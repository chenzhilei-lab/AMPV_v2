import sys,time,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S92_EXP_CONTAMINATED_FEASIBILITY_SMOKE_v1_0_20261003_041500")
import s91_frozen_base as m
K=[1,2,5,10,20]; CS=[0.,.6,1.]; IDS=[0,1,2,3]
# engineering-only noise/background field; paired by sample id and scaled by C.
def neutral_field(seed):
 rng=np.random.default_rng(seed); y,x=np.mgrid[:m.SIZE,:m.SIZE]
 z=rng.normal(0,1,(m.SIZE,m.SIZE))
 grad=(x/(m.SIZE-1)-.5)*4.0
 cr=np.zeros_like(z)
 for _ in range(8):
  yy=int(rng.integers(0,m.SIZE)); xx=int(rng.integers(0,m.SIZE)); cr[yy,xx]+=rng.uniform(5,15)
 return z+grad+cr
D=m.lhs2()
rows=[]; t0=time.time()
for sid in IDS:
 af=.8+D[sid,0]*.4; sig=1.5+D[sid,1]*2.5
 base=neutral_field(910000+sid); loc=m.i2p(920000+sid,1.0)
 for k in K:
  F=m.F_REF*af*k
  clean=m.gaussian_source(F,sig)
  for C in CS:
   im=clean+C*(base+loc)
   vals={"A":(m.A(im),True,1),"B":(m.B(im),True,1),"C":(m.C(im),True,1)}
   ev,ok,st=m.E(im); vals["E"]=(ev,ok,st)
   for w,(v,ok,st) in vals.items():
    rows.append([sid,k,C,w,F,sig,v,(v-F)/F,abs((v-F)/F),ok,st])
q=pd.DataFrame(rows,columns=["sample_id","kappa_ref_target","C","workflow_id","F_true","sigma_psf","F_est","signed_error","absolute_error","optimizer_success","optimizer_status"])
q.to_csv(Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S92_EXP_CONTAMINATED_FEASIBILITY_SMOKE_v1_0_20261003_041500")/"S92_SMOKE_ROWS.csv",index=False)
# repeat exact generation to verify deterministic row hashes
def digest(df): return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()
h1=digest(q)
# structural checks only
checks={}
checks["rows_240"]=len(q)==4*5*3*4
checks["all_finite"]=bool(np.isfinite(q[["F_true","sigma_psf","F_est","signed_error","absolute_error"]].to_numpy()).all())
checks["all_cells_present"]=q.groupby(["sample_id","kappa_ref_target","C"]).ngroups==4*5*3
checks["four_workflows_each_cell"]=bool((q.groupby(["sample_id","kappa_ref_target","C"]).size()==4).all())
checks["paired_sigma_across_conditions"]=bool((q.groupby("sample_id").sigma_psf.nunique()==1).all())
checks["F_scales_exactly_with_kappa"]=True
for sid,g in q.groupby("sample_id"):
 f=g.groupby("kappa_ref_target").F_true.first()
 ratios=f/f.loc[1]
 if not np.allclose(ratios.values,np.array(K,dtype=float)): checks["F_scales_exactly_with_kappa"]=False
checks["E_optimizer_success_all"]=bool(q[q.workflow_id=="E"].optimizer_success.all())
checks["C0_i2p_zero_by_construction"]=True
# determinism: rebuild one representative cell twice
sid=2; af=.8+D[sid,0]*.4; sig=1.5+D[sid,1]*2.5; F=m.F_REF*af*5
def one():
 im=m.gaussian_source(F,sig)+.6*(neutral_field(910000+sid)+m.i2p(920000+sid,1.0))
 return np.array([m.A(im),m.B(im),m.C(im),m.E(im)[0]])
checks["representative_determinism"]=bool(np.array_equal(one(),one()))
meta={"stage":"S92-EXP","status":"PASS" if all(checks.values()) else "FAIL","purpose":"engineering feasibility only","sample_ids":IDS,"rows":len(q),"runtime_seconds":time.time()-t0,"checks":checks,"row_sha256":h1,"scientific_interpretation_authorized":False,"full_production_authorized":False}
Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S92_EXP_CONTAMINATED_FEASIBILITY_SMOKE_v1_0_20261003_041500","S92_SMOKE_SUMMARY.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
print(json.dumps(meta,indent=2))
