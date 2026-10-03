import pandas as pd, numpy as np, json, os
SRC=r"F:\AMPV_V2\07_CANONICAL_OUTPUTS\AMPV_V2_CANONICAL_RELEASE_20261002_074007\01_PRODUCTION\PRODUCTION_ROWS.csv"; OUT=r"F:\\AMPV_V2\\12_DERIVED_ANALYSES\\AMPV_V2_S81_PAIRED_BOOTSTRAP_TAU_SENSITIVITY_v1_1_20261002_223500"
SEED=20261002; B=2000; rng=np.random.default_rng(SEED)
df=pd.read_csv(SRC,encoding="utf-8-sig").sort_values(["sample_id","kappa_ref_target","C","workflow_id"]).reset_index(drop=True)
ids=np.sort(df.sample_id.unique()); assert len(df)==22500 and len(ids)==300
keys=sorted(df[["kappa_ref_target","C","workflow_id"]].drop_duplicates().itertuples(index=False,name=None))
# point reconciliation
pt=df.groupby(["kappa_ref_target","C","workflow_id"]).agg(n=("absolute_error","size"),median_abs=("absolute_error","median"),median_signed=("signed_error","median"),vuln=("vulnerable_tau_0_5","mean")).reset_index(); assert pt.n.eq(300).all(); pt.to_csv(OUT+"\\S81_RECONCILED_POINT_ESTIMATES.csv",index=False)
# arrays shape [sample,cell,workflow] through keyed pivot; bootstrap sample axis only
def cube(col):
 p=df.pivot_table(index="sample_id",columns=["kappa_ref_target","C","workflow_id"],values=col,aggfunc="first").reindex(index=ids,columns=pd.MultiIndex.from_tuples(keys))
 assert not p.isna().any().any(); return p.to_numpy()
A=cube("absolute_error"); S=cube("signed_error"); V=cube("vulnerable_tau_0_5").astype(float)
boot=np.empty((B,len(keys),3))
for b in range(B):
 ix=rng.integers(0,len(ids),len(ids)); boot[b,:,0]=np.median(A[ix,:],axis=0); boot[b,:,1]=np.median(S[ix,:],axis=0); boot[b,:,2]=np.mean(V[ix,:],axis=0)
lo=np.quantile(boot,.025,axis=0); hi=np.quantile(boot,.975,axis=0)
ci=pd.DataFrame(keys,columns=["kappa_ref_target","C","workflow_id"])
for j,n in enumerate(["median_abs","median_signed","vuln"]): ci[n+"_lo"]=lo[:,j]; ci[n+"_hi"]=hi[:,j]
ci.to_csv(OUT+"\\S81_CLUSTER_BOOTSTRAP_95CI.csv",index=False)
# tau sensitivity and boundaries
rr=[]
for t in [.25,.4,.5,.6,.75,1.0]:
 q=df.assign(v=df.absolute_error>t).groupby(["kappa_ref_target","C","workflow_id"]).v.mean().reset_index()
 for r in q.itertuples(index=False): rr.append((t,r.kappa_ref_target,r.C,r.workflow_id,r.v))
q=pd.DataFrame(rr,columns=["tau","kappa_ref_target","C","workflow_id","vulnerability_rate"]); q.to_csv(OUT+"\\S81_TAU_SENSITIVITY.csv",index=False)
br=[]
for (t,c,w),z in q.groupby(["tau","C","workflow_id"]):
 ok=z[z.vulnerability_rate<=.05].sort_values("kappa_ref_target"); br.append((t,c,w,np.nan if ok.empty else ok.iloc[0].kappa_ref_target))
pd.DataFrame(br,columns=["tau","C","workflow_id","lowest_tested_kappa_at_vuln_le_5pct"]).to_csv(OUT+"\\S81_TAU_BOUNDARIES.csv",index=False)
# paired blind workflow contrasts
blind=["A","B","C","E"]; pc=[]
for k in [1.,2.,5.,10.,20.]:
 for c in [0.,.6,1.]:
  z=df[(df.kappa_ref_target==k)&(df.C==c)].pivot(index="sample_id",columns="workflow_id",values="absolute_error")
  for i in range(len(blind)):
   for j in range(i+1,len(blind)):
    x=(z[blind[i]]-z[blind[j]]).to_numpy(); vals=np.empty(B)
    for b in range(B): vals[b]=np.median(x[rng.integers(0,len(x),len(x))])
    pc.append((k,c,blind[i],blind[j],np.median(x),*np.quantile(vals,[.025,.975])))
pd.DataFrame(pc,columns=["kappa_ref_target","C","workflow_1","workflow_2","median_paired_diff_abs","ci_lo","ci_hi"]).to_csv(OUT+"\\S81_PAIRED_WORKFLOW_CONTRASTS.csv",index=False)
# E sensitivity
e=df[df.workflow_id=="E"].copy(); e["opt_success"]=e.diagnostics_json.str.contains('"success": "True"',regex=False); bad=e[~e.opt_success]; bad.to_csv(OUT+"\\S81_WORKFLOW_E_NON_SUCCESS_ROWS.csv",index=False)
inc=e.groupby(["kappa_ref_target","C"]).absolute_error.median(); exc=e[e.opt_success].groupby(["kappa_ref_target","C"]).absolute_error.median(); es=pd.concat([inc.rename("inclusive"),exc.rename("excluded")],axis=1).reset_index(); es["delta"]=es.excluded-es.inclusive; es.to_csv(OUT+"\\S81_WORKFLOW_E_STATUS_SENSITIVITY.csv",index=False)
json.dump({"status":"PASS","rows":len(df),"sample_ids":len(ids),"groups":len(keys),"bootstrap_B":B,"seed":SEED,"E_non_success":len(bad),"max_abs_E_median_delta":float(es.delta.abs().max())},open(OUT+"\\S81_RUN_SUMMARY.json","w"),indent=2)
print("PASS rows",len(df),"ids",len(ids),"groups",len(keys),"Ebad",len(bad),"maxEdelta",es.delta.abs().max())
