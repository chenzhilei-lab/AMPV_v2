# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import csv, hashlib, importlib.util, json, math, sys, time, traceback, shutil
import numpy as np

PROJECT = Path(r"D:\Papers\AMPV_V2")
EXP_ROOT = PROJECT / "04_EXPERIMENTS"
AUTH_ROOT = PROJECT / "05_PILOT" / "S4_AUTHORIZATION"
PROD_ROOT = PROJECT / "06_PRODUCTION"
AUDIT_ROOT = PROJECT / "12_AUDIT"

CANONICAL_ROOT = Path(r"D:\Papers\JATIS-Done-Backup\CLEAN_MASTER_20260927_073905\01_CANONICAL_PIPELINE\v1.0.0_FINAL")
CANONICAL_FILES = {
    "benchmark":"xv02_benchmark_canonical_v1_0_0.py",
    "interference":"compound_interference_v1_0_0.py",
    "forward":"xv02_forward_model_v1_0_0.py",
    "protocol":"CANONICAL_PROTOCOL_v1_0_0.md",
}

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def hash_array(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()

def derive_seed(master, *parts) -> int:
    s="|".join(map(str,(master,)+parts)).encode()
    return int.from_bytes(hashlib.sha256(s).digest()[:8],"big")%(2**32-1)

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

def lhs(n, seed=42, lo=.3, hi=5.0):
    g=np.random.default_rng(seed)
    u=(np.arange(n)+g.random(n))/n
    g.shuffle(u)
    return lo+u*(hi-lo)

def aperture_mask(n=256, r=30):
    y,x=np.ogrid[:n,:n]
    c=n//2
    return (x-c)**2+(y-c)**2<=r*r

def method_e_with_diag(b, img, rn):
    import scipy.optimize, scipy
    orig=scipy.optimize.least_squares
    box={}
    def wrap(*a,**k):
        z=orig(*a,**k); box["z"]=z; return z
    scipy.optimize.least_squares=wrap
    try:
        flux=float(b.method_e_psf_fitting(img,true_rn=rn))
    finally:
        scipy.optimize.least_squares=orig
    z=box.get("z")
    d={"scipy_version":scipy.__version__}
    if z is not None:
        for k in ["success","status","nfev","njev","cost","optimality","message"]:
            if hasattr(z,k):
                v=getattr(z,k)
                d[k]=v.item() if hasattr(v,"item") else str(v)
    return flux,d

def build_calibrations(b, methods, gain, cal_cfg):
    rg=np.logspace(np.log10(cal_cfg["lo"]),np.log10(cal_cfg["hi"]),cal_cfg["n_grid"])
    out={}
    for m in methods:
        fg=[
            float(b.METHODS[m](gain*b.generate_comet_image(float(rn)),true_rn=float(rn)))
            for rn in rg
        ]
        out[m]=(rg,np.asarray(fg))
    return out

def append_log(event, md_text):
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    mds=sorted(AUDIT_ROOT.glob("AMPV_V2_WORKLOG_LIVE_*.md"))
    jls=sorted(AUDIT_ROOT.glob("AMPV_V2_EVENT_LOG_LIVE_*.jsonl"))
    if not mds or not jls:
        print("WARNING log append skipped: no live baseline")
        return None,None
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md=AUDIT_ROOT/f"AMPV_V2_WORKLOG_LIVE_{stamp}.md"
    out_jl=AUDIT_ROOT/f"AMPV_V2_EVENT_LOG_LIVE_{stamp}.jsonl"
    shutil.copy2(mds[-1],out_md); shutil.copy2(jls[-1],out_jl)
    with out_jl.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,ensure_ascii=False,separators=(",",":"))+"\n")
    with out_md.open("a",encoding="utf-8") as f:
        f.write(md_text)
    return out_md,out_jl

def verify_rows(rows, config, canonical_audit):
    checks=[]
    def ck(name, q, detail=""):
        checks.append({"name":name,"pass":bool(q),"detail":detail})
        print(("PASS" if q else "FAIL"),name,detail)
    klev=config["kappa_ref_levels"]; clev=config["contamination_levels"]
    methods=config["methods"]; N=config["N_per_cell"]
    expected=len(klev)*len(clev)*N*len(methods)
    ck("canonical unchanged", canonical_audit["all_unchanged"])
    ck("row count",len(rows)==expected,f"{len(rows)}/{expected}")

    # per-cell completeness and within-scene pairing
    for K in klev:
        for C in clev:
            cname=f"K{str(K).replace('.0','')}_C{str(C).replace('.','p')}"
            rr=[r for r in rows if r["cell"]==cname]
            ck(cname+" rows",len(rr)==N*len(methods),str(len(rr)))
            byid={}
            for r in rr: byid.setdefault(r["sample_id"],[]).append(r)
            ck(cname+" sample ids",len(byid)==N,str(len(byid)))
            badwf=0; badscene=0
            for i,q in byid.items():
                if set(r["workflow_id"] for r in q)!=set(methods): badwf+=1
                if len(set(r["scene_hash"] for r in q))!=1: badscene+=1
            ck(cname+" workflows complete",badwf==0,str(badwf))
            ck(cname+" scene match",badscene==0,str(badscene))

    # cross-cell pairing by sample_id: compare workflow A only
    cross_bad_rn=cross_bad_seed=cross_bad_struct=0
    for i in range(N):
        q=[r for r in rows if r["sample_id"]==i and r["workflow_id"]=="A"]
        if len(set(round(r["r_n_true"],14) for r in q))!=1: cross_bad_rn+=1
        if len(set((r["seed_i6"],r["seed_structured"]) for r in q))!=1: cross_bad_seed+=1
        if len(set(round(r["structured_rms_unscaled"],14) for r in q))!=1: cross_bad_struct+=1
    ck("cross-cell same rn",cross_bad_rn==0,str(cross_bad_rn))
    ck("cross-cell same seeds",cross_bad_seed==0,str(cross_bad_seed))
    ck("cross-cell same unscaled structured RMS",cross_bad_struct==0,str(cross_bad_struct))

    # C scaling
    for C in clev:
        q=[r for r in rows if r["workflow_id"]=="A" and abs(r["C"]-C)<1e-15]
        if C==0:
            ok=all(abs(r["structured_rms_scaled"])<1e-15 for r in q)
        else:
            ok=all(np.isclose(r["structured_rms_scaled"],C*r["structured_rms_unscaled"],
                              rtol=1e-12,atol=1e-15) for r in q)
        ck(f"C={C} scaling",ok)

    # gain consistency for same K
    for K in klev:
        q=[r for r in rows if r["workflow_id"]=="A" and abs(r["kappa_ref_target"]-K)<1e-15]
        ck(f"K={K} same source gain",len(set(round(r["source_gain"],15) for r in q))==1)

    E=[r for r in rows if r["workflow_id"]=="E"]
    good=[r for r in E if "exception" not in json.loads(r["diagnostics_json"])]
    ck("Method E >=95% nonexception",len(good)/len(E)>=.95,f"{len(good)}/{len(E)}")
    diag_ok=all(all(k in json.loads(r["diagnostics_json"]) for k in ["success","status","nfev","cost","optimality"]) for r in good)
    ck("Method E diagnostics",diag_ok)
    return checks, all(x["pass"] for x in checks)

def cell_summary(rows, config):
    out=[]
    for K in config["kappa_ref_levels"]:
        for C in config["contamination_levels"]:
            cname=f"K{str(K).replace('.0','')}_C{str(C).replace('.','p')}"
            for m in config["methods"]:
                q=[r for r in rows if r["cell"]==cname and r["workflow_id"]==m]
                valid=[r for r in q if r["valid"]]
                errs=np.array([r["absolute_error"] for r in valid],dtype=float) if valid else np.array([])
                signed=np.array([r["signed_error"] for r in valid],dtype=float) if valid else np.array([])
                out.append({
                    "cell":cname,"kappa_ref_target":K,"C":C,"workflow_id":m,
                    "n_total":len(q),"n_valid":len(valid),
                    "n_computational_failure":sum(r["failure_class"]=="COMPUTATIONAL_FAILURE" for r in q),
                    "n_vulnerable_tau_0_5":sum(bool(r["vulnerable_tau_0_5"]) for r in valid),
                    "vulnerability_rate_tau_0_5":float(np.mean([bool(r["vulnerable_tau_0_5"]) for r in valid])) if valid else None,
                    "median_absolute_error":float(np.median(errs)) if len(errs) else None,
                    "q25_absolute_error":float(np.percentile(errs,25)) if len(errs) else None,
                    "q75_absolute_error":float(np.percentile(errs,75)) if len(errs) else None,
                    "median_signed_error":float(np.median(signed)) if len(signed) else None,
                    "median_realized_kappa":float(np.median([r["kappa_sample_actual"] for r in q])) if q else None
                })
    return out

def main():
    print("="*100)
    print("AMPV V2 S5 PRODUCTION RUNNER v1.0")
    print("="*100)

    # Discover latest authorization
    auth_dirs=sorted(AUTH_ROOT.glob("S4_PRODUCTION_AUTHORIZATION_*"))
    if not auth_dirs:
        raise SystemExit("BLOCKED: no S4 production authorization found")
    auth_dir=auth_dirs[-1]
    auth_path=auth_dir/"S4_PRODUCTION_AUTHORIZATION.json"
    if not auth_path.exists():
        raise SystemExit("BLOCKED: authorization JSON missing")
    auth=json.loads(auth_path.read_text(encoding="utf-8"))
    if auth.get("production_authorized") is not True or auth.get("status")!="AUTHORIZED":
        raise SystemExit("BLOCKED: latest authorization is not AUTHORIZED")

    # Freeze config must be exactly the authorized snapshot hash
    freeze=Path(auth["freeze_dir"])
    cfg_path=freeze/"S4_PRODUCTION_GRID_v1_0.json"
    if not cfg_path.exists():
        raise SystemExit("BLOCKED: frozen production config missing")
    cfg_sha=sha256_file(cfg_path)
    if cfg_sha != auth["freeze_config_sha256"]:
        raise SystemExit("BLOCKED: frozen config SHA256 no longer matches authorization")
    C=json.loads(cfg_path.read_text(encoding="utf-8"))

    # Exact authorized design
    if C["kappa_ref_levels"] != [1.0,2.0,5.0,10.0,20.0]: raise SystemExit("BLOCKED: kappa grid changed")
    if C["contamination_levels"] != [0.0,0.6,1.0]: raise SystemExit("BLOCKED: contamination grid changed")
    if C["N_per_cell"] != 300: raise SystemExit("BLOCKED: N changed")
    if C["methods"] != ["A","B","C","D","E"]: raise SystemExit("BLOCKED: methods changed")
    sp=C["seed_policy"]
    if sp["seed_namespace"]!="AMPV_PRODUCTION_v1_0": raise SystemExit("BLOCKED: seed namespace changed")
    if sp["fidelity"]!="F0" or sp["task_family"]!="COMET_LIKE_PRIMARY": raise SystemExit("BLOCKED: design identity changed")

    # Canonical hash authorization check BEFORE run
    files={k:CANONICAL_ROOT/v for k,v in CANONICAL_FILES.items()}
    for k,p in files.items():
        if not p.exists(): raise SystemExit(f"BLOCKED: canonical file missing: {p}")
    current_hashes={p.name:sha256_file(p) for p in files.values()}
    if current_hashes != auth["canonical_hashes_at_authorization"]:
        print("AUTHORIZED:",json.dumps(auth["canonical_hashes_at_authorization"],indent=2))
        print("CURRENT:",json.dumps(current_hashes,indent=2))
        raise SystemExit("BLOCKED: canonical hashes changed since authorization")
    before=current_hashes.copy()

    # Output path is fixed under AMPV V2 root
    PROD_ROOT.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    out=PROD_ROOT/f"AMPV_V2_PRODUCTION_{stamp}"
    out.mkdir(parents=True,exist_ok=False)

    start_time=datetime.now().astimezone()
    run_manifest={
        "project":"AMPV V2","stage":"V2-S5 Production","version":"v1.0",
        "status":"RUNNING","started_at":start_time.isoformat(timespec="seconds"),
        "authorization_dir":str(auth_dir),"authorization_sha256":sha256_file(auth_path),
        "freeze_dir":str(freeze),"freeze_config_sha256":cfg_sha,
        "output_dir":str(out),"canonical_hashes_before":before,
        "production_authorized":True,"server_used":False
    }
    (out/"RUN_MANIFEST.json").write_text(json.dumps(run_manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    shutil.copy2(auth_path,out/"PRODUCTION_AUTHORIZATION_SNAPSHOT.json")
    shutil.copy2(cfg_path,out/"PRODUCTION_CONFIG_SNAPSHOT.json")

    # Start log event
    start_event={
        "event_id":f"V2-S5-PRODUCTION-START-{stamp}",
        "date":start_time.date().isoformat(),"project":"AMPV V2","stage":"V2-S5 Production",
        "status":"STARTED","evidence_status":"LIVE-EXECUTION",
        "paths":{"output_dir":str(out),"authorization_dir":str(auth_dir),"freeze_dir":str(freeze)},
        "results":["Authorized frozen design accepted.","Canonical hashes match authorization."],
        "canonical_modified":False,"production_authorized":True,"server_used":False
    }
    append_log(start_event,f"""

---

## LIVE APPEND — {start_time.isoformat(timespec='seconds')} — V2-S5 Production START

- output: `{out}`
- authorization: `{auth_dir}`
- freeze: `{freeze}`
- canonical hash gate: **PASS**
- production authorized: **YES**
- server used: **NO**
- status: `STARTED`
""")

    try:
        sys.path.insert(0,str(CANONICAL_ROOT))
        b=load_module("xv02_benchmark_canonical_v1_0_0",files["benchmark"])
        reg={x.name:x for x in b.REGIMES}[C["reference_regime"]]
        ap=aperture_mask(b.DEFAULT_SIZE,C["reference_aperture_radius_px"])
        nref=int(ap.sum())
        sigma=float(reg.i6_readout_noise)/1.5
        fref=float(b.generate_comet_image(C["reference_rn_km"])[ap].sum())
        den=sigma*math.sqrt(nref)

        methods=C["methods"]; N=C["N_per_cell"]; tau=C["tau"]
        rns=lhs(N,**C["rn_design"])
        gain_by_k={}; cal_by_k={}
        for K in C["kappa_ref_levels"]:
            gain=K*den/fref
            gain_by_k[str(K)]=gain
            print(f"Building calibration K={K} gain={gain:.12g}")
            cal_by_k[str(K)]=build_calibrations(b,methods,gain,C["calibration"])

        master=sp["master_seed"]; namespace=sp["seed_namespace"]
        rows=[]; scene_times=[]
        total_scenes=len(C["kappa_ref_levels"])*len(C["contamination_levels"])*N
        scene_counter=0

        for K in C["kappa_ref_levels"]:
            gain=gain_by_k[str(K)]
            for cc in C["contamination_levels"]:
                cname=f"K{str(K).replace('.0','')}_C{str(cc).replace('.','p')}"
                print("\nCELL",cname,"K",K,"C",cc)
                for i in range(N):
                    ts=time.perf_counter()
                    rn=float(rns[i])
                    clean=gain*b.generate_comet_image(rn)
                    clean_flux=float(clean[ap].sum())
                    kactual=clean_flux/den

                    # Common random numbers across ALL production cells.
                    si6=derive_seed(master,namespace,sp["fidelity"],sp["task_family"],i,"I6")
                    sst=derive_seed(master,namespace,sp["fidelity"],sp["task_family"],i,"I1_I5")
                    ni=b.CompoundInterferenceGenerator(reg,gain=1.0,enabled_components=("I6",)).generate(seed=si6)
                    su=b.CompoundInterferenceGenerator(reg,gain=1.0,enabled_components=("I1","I2","I3","I4","I5")).generate(seed=sst)
                    ss=cc*su
                    scene=clean+ni+ss
                    scene_hash=hash_array(scene)
                    diag0={
                        "i6_rms":float(np.sqrt(np.mean(ni**2))),
                        "structured_rms_unscaled":float(np.sqrt(np.mean(su**2))),
                        "structured_rms_scaled":float(np.sqrt(np.mean(ss**2)))
                    }

                    for m in methods:
                        t=time.perf_counter()
                        diag={}; raw=est=None; fail=None
                        try:
                            if m=="E":
                                raw,diag=method_e_with_diag(b,scene,rn)
                            else:
                                raw=float(b.METHODS[m](scene,true_rn=rn))
                            rg,fg=cal_by_k[str(K)][m]
                            est=float(b.flux_to_r_n(raw,rg,fg))
                        except Exception as e:
                            diag["exception"]=repr(e)
                            fail="COMPUTATIONAL_FAILURE"
                        runtime=time.perf_counter()-t
                        if fail:
                            valid=False; signed=absolute=vulnerable=None
                        else:
                            signed=(est-rn)/rn
                            absolute=abs(signed)
                            vulnerable=absolute>tau
                            valid=True
                            fail="VALID_POOR" if vulnerable else "VALID_GOOD"

                        rows.append(dict(
                            production_version="AMPV_PRODUCTION_v1_0",
                            fidelity=sp["fidelity"],
                            task_family=sp["task_family"],
                            seed_namespace=namespace,
                            cell=cname,C=cc,kappa_ref_target=K,kappa_sample_actual=kactual,
                            source_gain=gain,sample_id=i,r_n_true=rn,clean_aperture_flux=clean_flux,
                            seed_i6=si6,seed_structured=sst,scene_hash=scene_hash,
                            workflow_id=m,workflow_info_class="ORACLE_DIAGNOSTIC" if m=="D" else "BLIND",
                            raw_flux=raw,r_n_est=est,signed_error=signed,absolute_error=absolute,
                            vulnerable_tau_0_5=vulnerable,valid=valid,failure_class=fail,
                            runtime_sec=runtime,diagnostics_json=json.dumps(diag,ensure_ascii=False),**diag0
                        ))
                    scene_times.append(time.perf_counter()-ts)
                    scene_counter+=1
                    if i==0 or (i+1)%50==0 or i+1==N:
                        print(f"  {cname} {i+1}/{N} | overall {scene_counter}/{total_scenes} | rn={rn:.4f} | Ksample={kactual:.3f}")

        # Write raw production evidence
        fields=list(rows[0].keys())
        with (out/"PRODUCTION_ROWS.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
        (out/"PRODUCTION_ROWS.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")

        st=np.asarray(scene_times,dtype=float)
        runtime_report={
            "matched_scenes":len(scene_times),
            "median_sec_per_scene":float(np.median(st)),
            "p95_sec_per_scene":float(np.percentile(st,95)),
            "total_runtime_sec_scene_loop":float(np.sum(st)),
            "total_runtime_min_scene_loop":float(np.sum(st)/60),
            "server_recommended_12h_rule":False
        }
        (out/"PRODUCTION_RUNTIME_REPORT.json").write_text(json.dumps(runtime_report,indent=2),encoding="utf-8")

        # Canonical unchanged
        after={p.name:sha256_file(p) for p in files.values()}
        canaudit={"before":before,"after":after,"all_unchanged":before==after}
        (out/"PRODUCTION_CANONICAL_HASH_AUDIT.json").write_text(json.dumps(canaudit,indent=2),encoding="utf-8")

        # Verification
        print("\n"+"="*100)
        print("PRODUCTION VERIFICATION")
        print("="*100)
        checks, all_pass=verify_rows(rows,C,canaudit)
        (out/"PRODUCTION_VERIFICATION.json").write_text(json.dumps({"checks":checks,"all_pass":all_pass},indent=2),encoding="utf-8")

        summary=cell_summary(rows,C)
        (out/"PRODUCTION_CELL_WORKFLOW_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
        with (out/"PRODUCTION_CELL_WORKFLOW_SUMMARY.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

        # Finish manifest + hashes
        end_time=datetime.now().astimezone()
        run_manifest.update({
            "status":"PASS" if all_pass else "FAILED_VERIFICATION",
            "finished_at":end_time.isoformat(timespec="seconds"),
            "canonical_hashes_after":after,
            "canonical_unchanged":before==after,
            "expected_rows":22500,"actual_rows":len(rows),
            "verification_pass":all_pass,
            "runtime_report":runtime_report
        })
        (out/"RUN_MANIFEST.json").write_text(json.dumps(run_manifest,indent=2,ensure_ascii=False),encoding="utf-8")

        sums=[]
        for p in sorted(out.glob("*")):
            if p.is_file() and p.name!="SHA256SUMS.txt":
                sums.append(f"{sha256_file(p)}  {p.name}")
        (out/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")

        event={
            "event_id":f"V2-S5-PRODUCTION-END-{stamp}",
            "date":end_time.date().isoformat(),"project":"AMPV V2","stage":"V2-S5 Production",
            "status":"PASS" if all_pass else "FAILED_VERIFICATION","evidence_status":"LIVE-EXECUTION",
            "paths":{"output_dir":str(out),"authorization_dir":str(auth_dir),"freeze_dir":str(freeze)},
            "results":[
                f"Rows={len(rows)}/22500",
                f"Matched scenes={len(scene_times)}/4500",
                f"Verification all_pass={all_pass}",
                f"Canonical unchanged={before==after}",
                f"Scene-loop runtime={runtime_report['total_runtime_min_scene_loop']:.3f} min"
            ],
            "decision":"Accept production run as candidate canonical V2 production evidence; proceed to numerical ledger/audit." if all_pass else "Do not promote; inspect failed verification.",
            "canonical_modified":False,"production_authorized":True,"server_used":False
        }
        wm=f"""

---

## LIVE APPEND — {end_time.isoformat(timespec='seconds')} — V2-S5 Production END

**Status:** `{'PASS' if all_pass else 'FAILED_VERIFICATION'}`

- output: `{out}`
- rows: `{len(rows)}/22500`
- matched scenes: `{len(scene_times)}/4500`
- verification: **{'PASS' if all_pass else 'FAIL'}**
- canonical unchanged: **{'YES' if before==after else 'NO'}**
- scene-loop runtime: `{runtime_report['total_runtime_min_scene_loop']:.3f} min`
- production authorized: **YES**
- server used: **NO**

**Decision:** {'Candidate V2 production evidence accepted for numerical-ledger audit; not yet labeled canonical until that audit passes.' if all_pass else 'Do not promote this run.'}
"""
        logmd,logjl=append_log(event,wm)
        print()
        print("="*100)
        print("AMPV V2 PRODUCTION", "PASS" if all_pass else "FAILED VERIFICATION")
        print("OUTPUT:",out)
        print("ROWS:",len(rows))
        print("MATCHED SCENES:",len(scene_times))
        print("CANONICAL UNCHANGED:",before==after)
        print("PRODUCTION AUTHORIZED: YES")
        print("SERVER USED: NO")
        if logmd: print("WORKLOG:",logmd)
        if logjl: print("EVENTLOG:",logjl)
        print("="*100)
        raise SystemExit(0 if all_pass else 6)

    except BaseException as e:
        if isinstance(e,SystemExit):
            raise
        fail_time=datetime.now().astimezone()
        tb=traceback.format_exc()
        (out/"PRODUCTION_EXCEPTION.txt").write_text(tb,encoding="utf-8")
        run_manifest.update({"status":"FAILED_EXECUTION","finished_at":fail_time.isoformat(timespec="seconds"),"exception":repr(e)})
        (out/"RUN_MANIFEST.json").write_text(json.dumps(run_manifest,indent=2,ensure_ascii=False),encoding="utf-8")
        event={
            "event_id":f"V2-S5-PRODUCTION-FAIL-{stamp}",
            "date":fail_time.date().isoformat(),"project":"AMPV V2","stage":"V2-S5 Production",
            "status":"FAILED_EXECUTION","evidence_status":"LIVE-EXECUTION",
            "paths":{"output_dir":str(out)},"results":[repr(e)],
            "decision":"Retain failed output; do not promote. Diagnose and rerun only after documented correction.",
            "canonical_modified":False,"production_authorized":True,"server_used":False
        }
        append_log(event,f"""

---

## LIVE APPEND — {fail_time.isoformat(timespec='seconds')} — V2-S5 Production FAILURE

- output: `{out}`
- status: `FAILED_EXECUTION`
- exception: `{repr(e)}`
- scientific use: **NO**
- retain failed run: **YES**
""")
        print(tb)
        raise SystemExit(7)

if __name__=="__main__":
    main()
