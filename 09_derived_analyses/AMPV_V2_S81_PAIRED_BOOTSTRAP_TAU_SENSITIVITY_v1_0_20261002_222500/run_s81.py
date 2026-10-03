import pandas as pd, numpy as np, json, os
SRC=r"F:\AMPV_V2\07_CANONICAL_OUTPUTS\AMPV_V2_CANONICAL_RELEASE_20261002_074007\01_PRODUCTION\PRODUCTION_ROWS.csv"
OUT=r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S81_PAIRED_BOOTSTRAP_TAU_SENSITIVITY_v1_0_20261002_222500"
SEED=20261002; B=2000
df=pd.read_csv(SRC,encoding="utf-8-sig")
assert len(df)==22500 and df.sample_id.nunique()==300
assert df.groupby(["kappa_ref_target","C","workflow_id"]).size().eq(300).all()
rng=np.random.default_rng(SEED); ids=np.sort(df.sample_id.unique())
# exact reconciliation
summ=df.groupby(["kappa_ref_target","C","workflow_id"]).agg(n=("absolute_error","size"),median_abs=("absolute_error","median"),median_signed=("signed_error","median"),vuln=("vulnerable_tau_0_5","mean")).reset_index()
summ.to_csv(os.path.join(OUT,"S81_RECONCILED_POINT_ESTIMATES.csv"),index=False)
# cluster bootstrap 75 groups, resample IDs as whole clusters
keys=list(df.groupby(["kappa_ref_target","C","workflow_id"]).groups)
store={k:[] for k in keys}
for b in range(B):
    draw=rng.choice(ids,size=len(ids),replace=True)
    parts=[df[df.sample_id.eq(i)] for i in draw]
    x=pd.concat(parts,ignore_index=True)
    g=x.groupby(["kappa_ref_target","C","workflow_id"])
    for k,z in g:
        store[k].append((z.absolute_error.median(),z.signed_error.median(),z.vulnerable_tau_0_5.mean()))
rows=[]
for k,v in store.items():
    a=np.asarray(v,float)
    rows.append((*k,*np.quantile(a[:,0],[.025,.975]),*np.quantile(a[:,1],[.025,.975]),*np.quantile(a[:,2],[.025,.975])))
pd.DataFrame(rows,columns=["kappa_ref_target","C","workflow_id","median_abs_lo","median_abs_hi","median_signed_lo","median_signed_hi","vuln_lo","vuln_hi"]).to_csv(os.path.join(OUT,"S81_CLUSTER_BOOTSTRAP_95CI.csv"),index=False)
# tau sensitivity
taus=[.25,.4,.5,.6,.75,1.0]; rr=[]
for t in taus:
    q=df.assign(v=df.absolute_error>t).groupby(["kappa_ref_target","C","workflow_id"]).v.mean().reset_index()
    for _,r in q.iterrows(): rr.append((t,r.kappa_ref_target,r.C,r.workflow_id,r.v))
pd.DataFrame(rr,columns=["tau","kappa_ref_target","C","workflow_id","vulnerability_rate"]).to_csv(os.path.join(OUT,"S81_TAU_SENSITIVITY.csv"),index=False)
# boundary <=5%
q=pd.DataFrame(rr,columns=["tau","kappa_ref_target","C","workflow_id","vulnerability_rate"]); br=[]
for (t,c,w),z in q.groupby(["tau","C","workflow_id"]):
    ok=z[z.vulnerability_rate<=.05].sort_values("kappa_ref_target")
    br.append((t,c,w,None if ok.empty else float(ok.iloc[0].kappa_ref_target)))
pd.DataFrame(br,columns=["tau","C","workflow_id","lowest_tested_kappa_at_vuln_le_5pct"]).to_csv(os.path.join(OUT,"S81_TAU_BOUNDARIES.csv"),index=False)
# E status sensitivity
e=df[df.workflow_id.eq("E")].copy()
e["opt_success"]=e.diagnostics_json.str.contains('"success": "True"',regex=False)
bad=e[~e.opt_success]
bad.to_csv(os.path.join(OUT,"S81_WORKFLOW_E_NON_SUCCESS_ROWS.csv"),index=False)
inc=e.groupby(["kappa_ref_target","C"]).absolute_error.median(); exc=e[e.opt_success].groupby(["kappa_ref_target","C"]).absolute_error.median()
es=pd.concat([inc.rename("inclusive_median_abs"),exc.rename("exclude_non_success_median_abs")],axis=1).reset_index(); es["delta"]=es.exclude_non_success_median_abs-es.inclusive_median_abs
es.to_csv(os.path.join(OUT,"S81_WORKFLOW_E_STATUS_SENSITIVITY.csv"),index=False)
json.dump({"rows":len(df),"sample_ids":int(df.sample_id.nunique()),"bootstrap_B":B,"seed":SEED,"E_non_success":int(len(bad)),"max_abs_E_median_delta":float(es.delta.abs().max())},open(os.path.join(OUT,"S81_RUN_SUMMARY.json"),"w"),indent=2)
print("PASS",len(df),df.sample_id.nunique(),"Ebad",len(bad),"maxEdelta",es.delta.abs().max())
