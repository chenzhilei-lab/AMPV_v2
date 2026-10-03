import pandas as pd, numpy as np, json, hashlib
from pathlib import Path
SRC=Path(r"F:\AMPV_V2\07_CANONICAL_OUTPUTS\AMPV_V2_CANONICAL_RELEASE_20261002_074007\01_PRODUCTION\PRODUCTION_ROWS.csv")
OUT=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S88_MISSING_PAIRED_CONTRASTS_v1_0_20261003_015000")
SEED=20261002; B=2000
df=pd.read_csv(SRC,encoding="utf-8-sig").sort_values(["sample_id","kappa_ref_target","C","workflow_id"]).reset_index(drop=True)
ids=np.sort(df.sample_id.unique())
assert len(df)==22500 and len(ids)==300
assert df.groupby(["kappa_ref_target","C","workflow_id"]).size().eq(300).all()
def med_ci(x, rng):
 x=np.asarray(x,float); point=float(np.median(x)); vals=np.empty(B)
 for b in range(B):
  ix=rng.integers(0,len(x),len(x)); vals[b]=np.median(x[ix])
 lo,hi=np.quantile(vals,[.025,.975]); return point,float(lo),float(hi)
# Use independent deterministic RNG streams per analysis family, rooted in frozen S81 seed.
rngC=np.random.default_rng(SEED+88_001)
rngD=np.random.default_rng(SEED+88_002)
rowsC=[]
for k in [1.,2.,5.,10.,20.]:
 for w in ["A","B","C","D","E"]:
  z=df[(df.kappa_ref_target==k)&(df.workflow_id==w)].pivot(index="sample_id",columns="C",values="absolute_error").reindex(ids)
  assert list(z.columns)==[0.0,0.6,1.0] and not z.isna().any().any()
  for c1,c0 in [(0.6,0.0),(1.0,0.0)]:
   x=(z[c1]-z[c0]).to_numpy(); point,lo,hi=med_ci(x,rngC)
   rowsC.append((k,w,c1,c0,point,lo,hi,int((x>0).sum()),int((x<0).sum()),int((x==0).sum())))
C=pd.DataFrame(rowsC,columns=["kappa_ref_target","workflow_id","C_high","C_base","median_paired_diff_abs","ci_lo","ci_hi","n_positive","n_negative","n_zero"])
C.to_csv(OUT/"S88_PAIRED_CONTAMINATION_CONTRASTS.csv",index=False)
rowsD=[]
for c in [0.,0.6,1.0]:
 for w in ["A","B","C","D","E"]:
  z=df[(df.C==c)&(df.workflow_id==w)].pivot(index="sample_id",columns="kappa_ref_target",values="absolute_error").reindex(ids)
  assert list(z.columns)==[1.0,2.0,5.0,10.0,20.0] and not z.isna().any().any()
  for k0,k1 in [(1.,2.),(2.,5.),(5.,10.),(10.,20.)]:
   # high-kappa minus low-kappa: negative means error improves as reference contrast increases.
   x=(z[k1]-z[k0]).to_numpy(); point,lo,hi=med_ci(x,rngD)
   rowsD.append((c,w,k0,k1,point,lo,hi,int((x>0).sum()),int((x<0).sum()),int((x==0).sum())))
D=pd.DataFrame(rowsD,columns=["C","workflow_id","kappa_low","kappa_high","median_paired_diff_abs","ci_lo","ci_hi","n_positive","n_negative","n_zero"])
D.to_csv(OUT/"S88_PAIRED_ADJACENT_KAPPA_CONTRASTS.csv",index=False)
def cls(r):
 return "positive" if r.ci_lo>0 else ("negative" if r.ci_hi<0 else "includes_zero")
C["ci_sign"]=[cls(r) for r in C.itertuples()]
D["ci_sign"]=[cls(r) for r in D.itertuples()]
summary={
 "status":"PASS","source":str(SRC),"source_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
 "rows":len(df),"sample_ids":len(ids),"bootstrap_B":B,"root_seed":SEED,
 "contamination_rng_seed":SEED+88001,"adjacent_kappa_rng_seed":SEED+88002,
 "contamination_contrasts":len(C),"contamination_ci_positive":int((C.ci_sign=="positive").sum()),"contamination_ci_negative":int((C.ci_sign=="negative").sum()),"contamination_ci_includes_zero":int((C.ci_sign=="includes_zero").sum()),
 "adjacent_kappa_contrasts":len(D),"adjacent_kappa_ci_positive":int((D.ci_sign=="positive").sum()),"adjacent_kappa_ci_negative":int((D.ci_sign=="negative").sum()),"adjacent_kappa_ci_includes_zero":int((D.ci_sign=="includes_zero").sum())
}
json.dump(summary,open(OUT/"S88_RUN_SUMMARY.json","w"),indent=2)
print(json.dumps(summary,indent=2))
print("\nCONTAMINATION\n",C.to_string(index=False))
print("\nADJ_KAPPA\n",D.to_string(index=False))
