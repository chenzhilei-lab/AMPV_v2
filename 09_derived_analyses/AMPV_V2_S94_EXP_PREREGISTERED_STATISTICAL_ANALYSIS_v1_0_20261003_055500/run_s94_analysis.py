import pandas as pd,numpy as np,json,hashlib,time
from pathlib import Path
SRC=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S93_EXP_PRODUCTION_PROTOCOL_FREEZE_v1_0_20261003_044500\PRODUCTION\PRODUCTION_ROWS.csv"); OUT=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S94_EXP_PREREGISTERED_STATISTICAL_ANALYSIS_v1_0_20261003_055500"); B=2000; SEED=20261004
q=pd.read_csv(SRC); rng=np.random.default_rng(SEED)
TAUS=[.25,.4,.5,.6,.75,1.0]; W=["A","B","C","E"]; K=[1,2,5,10,20]; CS=[0.,.6,1.]
def ci_med(x):
 x=np.asarray(x,float); n=len(x); z=np.empty(B)
 for i in range(B): z[i]=np.median(x[rng.integers(0,n,n)])
 return np.median(x),*np.quantile(z,[.025,.975])
def ci_mean01(x):
 x=np.asarray(x,float); n=len(x); z=np.empty(B)
 for i in range(B): z[i]=np.mean(x[rng.integers(0,n,n)])
 return np.mean(x),*np.quantile(z,[.025,.975])
cells=[]
for (k,c,w),g in q.groupby(["kappa_ref_target","C","workflow_id"]):
 ma,alo,ahi=ci_med(g.absolute_error); ms,slo,shi=ci_med(g.signed_error); vr,vlo,vhi=ci_mean01(g.absolute_error.to_numpy()>.5)
 cells.append([k,c,w,len(g),ma,alo,ahi,ms,slo,shi,vr,vlo,vhi])
pd.DataFrame(cells,columns=["kappa","C","workflow","N","median_abs","abs_lo","abs_hi","median_signed","signed_lo","signed_hi","vuln_tau_0_5","vuln_lo","vuln_hi"]).to_csv(OUT/"S94_CELL_SUMMARY.csv",index=False)
pairs=[]
for k in K:
 for c in CS:
  g=q[(q.kappa_ref_target==k)&(q.C==c)].pivot(index="sample_id",columns="workflow_id",values="absolute_error")
  for a,bb in [("A","B"),("A","C"),("A","E"),("B","C"),("B","E"),("C","E")]:
   m,lo,hi=ci_med((g[a]-g[bb]).to_numpy()); pairs.append([k,c,a,bb,m,lo,hi])
pd.DataFrame(pairs,columns=["kappa","C","workflow_left","workflow_right","median_paired_diff_left_minus_right","lo","hi"]).to_csv(OUT/"S94_WORKFLOW_PAIRED_CONTRASTS.csv",index=False)
cont=[]
for k in K:
 for w in W:
  g=q[(q.kappa_ref_target==k)&(q.workflow_id==w)].pivot(index="sample_id",columns="C",values="absolute_error")
  for high in [.6,1.]:
   m,lo,hi=ci_med((g[high]-g[0.]).to_numpy()); cont.append([k,w,high,m,lo,hi])
pd.DataFrame(cont,columns=["kappa","workflow","C_high","median_diff_high_minus_C0","lo","hi"]).to_csv(OUT/"S94_CONTAMINATION_CONTRASTS.csv",index=False)
adj=[]
for c in CS:
 for w in W:
  g=q[(q.C==c)&(q.workflow_id==w)].pivot(index="sample_id",columns="kappa_ref_target",values="absolute_error")
  for low,high in [(1,2),(2,5),(5,10),(10,20)]:
   m,lo,hi=ci_med((g[high]-g[low]).to_numpy()); adj.append([c,w,low,high,m,lo,hi])
pd.DataFrame(adj,columns=["C","workflow","kappa_low","kappa_high","median_diff_high_minus_low","lo","hi"]).to_csv(OUT/"S94_ADJACENT_KAPPA_CONTRASTS.csv",index=False)
ts=[]
for tau in TAUS:
 for (k,c,w),g in q.groupby(["kappa_ref_target","C","workflow_id"]):
  vr,lo,hi=ci_mean01(g.absolute_error.to_numpy()>tau); ts.append([tau,k,c,w,vr,lo,hi])
pd.DataFrame(ts,columns=["tau","kappa","C","workflow","vulnerability","lo","hi"]).to_csv(OUT/"S94_TAU_SENSITIVITY.csv",index=False)
pc=pd.DataFrame(cont,columns=["kappa","workflow","C_high","m","lo","hi"]); pa=pd.DataFrame(adj,columns=["C","workflow","kl","kh","m","lo","hi"]); pp=pd.DataFrame(pairs,columns=["kappa","C","a","b","m","lo","hi"])
summary={"stage":"S94-EXP","source_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),"bootstrap_B":B,"analysis_seed":SEED,"rows":len(q),"sample_ids":q.sample_id.nunique(),"cell_groups":len(cells),"workflow_paired_contrasts":len(pairs),"contamination_contrasts":len(cont),"adjacent_kappa_contrasts":len(adj),"tau_cells":len(ts),"contamination_ci_positive":int((pc.lo>0).sum()),"contamination_ci_negative":int((pc.hi<0).sum()),"contamination_ci_zero":int(((pc.lo<=0)&(pc.hi>=0)).sum()),"adjacent_kappa_ci_negative":int((pa.hi<0).sum()),"adjacent_kappa_ci_positive":int((pa.lo>0).sum()),"adjacent_kappa_ci_zero":int(((pa.lo<=0)&(pa.hi>=0)).sum()),"workflow_pair_ci_positive":int((pp.lo>0).sum()),"workflow_pair_ci_negative":int((pp.hi<0).sum()),"workflow_pair_ci_zero":int(((pp.lo<=0)&(pp.hi>=0)).sum())}
(OUT/"S94_RUN_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8"); print(json.dumps(summary,indent=2))
