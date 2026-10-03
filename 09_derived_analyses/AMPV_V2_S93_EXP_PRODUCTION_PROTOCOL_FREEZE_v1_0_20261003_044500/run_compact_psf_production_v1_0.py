import time,json,hashlib,sys
from pathlib import Path
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import compact_psf_core_v1_0 as m
OUT=HERE/"PRODUCTION"; OUT.mkdir(exist_ok=True)
D=m.lhs2(300); rows=[]; t=time.time()
for sid in range(300):
 af=.8+D[sid,0]*.4; sig=1.5+D[sid,1]*2.5; base=m.neutral_field(910000+sid)
 for k in m.KAPPAS:
  F=m.F_REF*af*k; clean=m.gaussian_source(F,sig)
  for Clev in m.C_LEVELS:
   im=clean+Clev*(base+m.i2p(920000+sid,1.0))
   vals={"A":(m.A(im),True,1,0),"B":(m.B(im),True,1,0),"C":(m.C(im),True,1,0)}
   ev,ok,st,nf=m.E(im); vals["E"]=(ev,ok,st,nf)
   realized=m.A(clean)/(1.0*np.sqrt(m.AM.sum()))
   for w,(v,ok,st,nf) in vals.items():
    e=(v-F)/F
    rows.append(["COMPACT_PSF_PRIMARY",sid,k,Clev,w,F,sig,realized,v,e,abs(e),abs(e)>.5,ok,st,nf])
q=pd.DataFrame(rows,columns=["family_id","sample_id","kappa_ref_target","C","workflow_id","F_true","sigma_psf","realized_reference_contrast","F_est","signed_error","absolute_error","vulnerable_tau_0_5","optimizer_success","optimizer_status","optimizer_nfev"])
q.to_csv(OUT/"PRODUCTION_ROWS.csv",index=False)
sha=hashlib.sha256((OUT/"PRODUCTION_ROWS.csv").read_bytes()).hexdigest()
summary={"rows":len(q),"sample_ids":q.sample_id.nunique(),"cells":q.groupby(["kappa_ref_target","C","workflow_id"]).ngroups,"runtime_seconds":time.time()-t,"all_finite":bool(np.isfinite(q.select_dtypes(include=[np.number]).to_numpy()).all()),"E_non_success":int((~q[q.workflow_id=="E"].optimizer_success).sum()),"rows_sha256":sha}
(OUT/"RUN_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8"); print(json.dumps(summary,indent=2))
