import numpy as np, json, hashlib
from pathlib import Path
OUT=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S91_EXP_ISOLATED_IMPLEMENTATION_v1_0_20261003_034000")
SIZE=256; AP=30; LHS_SEED=20261003
F_REF=1000.0
# Frozen intrinsic amplitude factor: narrow range prevents duplication of kappa stress axis.
AMP_RANGE=(0.8,1.2)
SIG_RANGE=(1.5,4.0)
def gaussian_source(F,sigma,size=SIZE):
 y,x=np.mgrid[:size,:size]; c=size//2
 g=np.exp(-((x-c)**2+(y-c)**2)/(2*sigma*sigma))
 return F*g/g.sum()
def aperture_mask(r):
 y,x=np.ogrid[:SIZE,:SIZE]; c=SIZE//2
 return (x-c)**2+(y-c)**2<=r*r
def annulus_mask(a,b):
 y,x=np.ogrid[:SIZE,:SIZE]; c=SIZE//2; q=(x-c)**2+(y-c)**2
 return (q>=a*a)&(q<=b*b)
AM=aperture_mask(30); BM=annulus_mask(50,90)
def A(im): return float(im[AM].sum())
def B(im): return float(im[AM].sum()-im[BM].mean()*AM.sum())
def C(im):
 bg=im[BM]; rng=np.random.default_rng(20260814); best=float(np.median(bg)); score=-1
 sd=float(np.std(bg))
 for _ in range(200):
  s=rng.choice(bg,30,replace=False); v=float(np.median(s))
  sc=int(np.sum(np.abs(bg-v)<0.2*sd)) if sd>0 else len(bg)
  if sc>score: score=sc; best=v
 return float(im[AM].sum()-best*AM.sum())
def E(im):
 from scipy.optimize import least_squares
 c=SIZE//2; pad=34; x0,x1=c-pad,c+pad+1; y0,y1=x0,x1
 patch=im[y0:y1,x0:x1]; yy,xx=np.mgrid[y0:y1,x0:x1]; mask=(xx-c)**2+(yy-c)**2<=AP**2
 bg0=float(np.median(patch[~mask])); amp0=max(float(patch.max())-bg0,1e-12)
 def fun(p):
  xc,yc,amp,sig,bg=p; g=np.exp(-((xx-xc)**2+(yy-yc)**2)/(2*sig**2)); return (bg+amp*g-patch)[mask]
 r=least_squares(fun,[c,c,amp0,3.,bg0],bounds=([x0,y0,0.,1.,-np.inf],[x1-1,y1-1,np.inf,20.,np.inf]),max_nfev=120)
 return float(2*np.pi*abs(r.x[2])*r.x[3]**2), bool(r.success), int(r.status)
# I2P: task-neutral asymmetric elongated residual, fixed reference scale.
# Geometry frozen before contaminated outcome generation.
def i2p(seed, level=1.0):
 rng=np.random.default_rng(seed); y,x=np.mgrid[:SIZE,:SIZE]; c=SIZE//2
 angle=rng.uniform(0,2*np.pi); dist=rng.uniform(38,70); cx=c+dist*np.cos(angle); cy=c+dist*np.sin(angle)
 phi=rng.uniform(0,2*np.pi); cp,sp=np.cos(phi),np.sin(phi)
 dx=x-cx; dy=y-cy; u=cp*dx+sp*dy; v=-sp*dx+cp*dy
 su=rng.uniform(5,12); sv=rng.uniform(1.5,3.5)
 peak=0.02*F_REF*level
 return peak*np.exp(-(u*u/(2*su*su)+v*v/(2*sv*sv)))
# 2D LHS design, deterministic.
def lhs2(n=300,seed=LHS_SEED):
 rng=np.random.default_rng(seed); cols=[]
 for _ in range(2):
  u=(np.arange(n)+rng.random(n))/n; rng.shuffle(u); cols.append(u)
 return np.column_stack(cols)
D=lhs2(); amp=AMP_RANGE[0]+D[:,0]*(AMP_RANGE[1]-AMP_RANGE[0]); sig=SIG_RANGE[0]+D[:,1]*(SIG_RANGE[1]-SIG_RANGE[0])
np.savetxt(OUT/"S91_BASE_DESIGN.csv",np.column_stack([np.arange(300),amp,sig]),delimiter=",",header="sample_id,intrinsic_amplitude_factor,sigma_psf",comments="")
# clean-domain audit: deliberately not scientific stress outcomes
rows=[]
for F in [800.,1000.,1200.]:
 for s in np.linspace(1.5,4.0,11):
  im=gaussian_source(F,float(s)); vals={"A":A(im),"B":B(im),"C":C(im)}; ev,ok,st=E(im); vals["E"]=ev
  for w,v in vals.items(): rows.append((F,s,w,v,(v-F)/F))
import pandas as pd
q=pd.DataFrame(rows,columns=["F_true","sigma_psf","workflow","F_est","signed_rel_error"]); q.to_csv(OUT/"S91_CLEAN_DOMAIN_AUDIT.csv",index=False)
# determinism checks for forward source, design and I2P only
checks={}
for name,a1,a2 in [
 ("source",gaussian_source(1000,2.5),gaussian_source(1000,2.5)),
 ("i2p",i2p(12345,.6),i2p(12345,.6))]:
 checks[name]=bool(np.array_equal(a1,a2))
checks["lhs"]=bool(np.array_equal(lhs2(),lhs2()))
summ=q.groupby("workflow").signed_rel_error.agg(["min","max",lambda x:float(np.max(np.abs(x)))]).reset_index()
summ.columns=["workflow","min_signed_rel_error","max_signed_rel_error","max_abs_rel_error"]
summ.to_csv(OUT/"S91_CLEAN_SUMMARY.csv",index=False)
meta={"status":"PASS" if all(checks.values()) else "FAIL","scientific_outcomes_generated":False,"F_REF":F_REF,"intrinsic_amplitude_range":AMP_RANGE,"sigma_range":SIG_RANGE,"lhs_seed":LHS_SEED,"I2P":{"center_distance_px":[38,70],"sigma_major_px":[5,12],"sigma_minor_px":[1.5,3.5],"peak_scale":"0.02*F_REF*level","depends_on_sample_truth":False},"determinism":checks}
(OUT/"S91_SMOKE_SUMMARY.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
print(json.dumps(meta,indent=2)); print(summ.to_string(index=False))
