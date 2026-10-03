import csv,json,hashlib,sys
from pathlib import Path
import numpy as np
IN=Path(sys.argv[1]); OUT=Path(sys.argv[2]); B=2000; SEED=20261004
rows=list(csv.DictReader(IN.open(encoding='utf-8')))
for r in rows:
 for k in ['kappa_ref_target','C','F_true','SEP_flux','signed_error','absolute_error']:
  r[k]=float(r[k])
 r['sample_id']=int(r['sample_id']); r['vulnerable_tau_0_5']=r['vulnerable_tau_0_5'].lower()=='true'
ids=sorted({r['sample_id'] for r in rows}); rng=np.random.default_rng(SEED)
by={(r['sample_id'],r['kappa_ref_target'],r['C']):r for r in rows}
def boot(vals):
 vals=np.asarray(vals,float); n=len(vals); meds=np.empty(B)
 for b in range(B): meds[b]=np.median(vals[rng.integers(0,n,n)])
 return float(np.median(vals)),float(np.percentile(meds,2.5)),float(np.percentile(meds,97.5))
cell=[]
for k in (1.,5.,20.):
 for c in (0.,.6,1.):
  ae=[by[(i,k,c)]['absolute_error'] for i in ids]; vr=[float(by[(i,k,c)]['vulnerable_tau_0_5']) for i in ids]
  m,lo,hi=boot(ae); vm,vlo,vhi=boot(vr); cell.append([k,c,m,lo,hi,float(np.mean(vr)),vlo,vhi])
cont=[]
for k in (1.,5.,20.):
 for ch in (.6,1.):
  vals=[by[(i,k,ch)]['absolute_error']-by[(i,k,0.)]['absolute_error'] for i in ids]
  m,lo,hi=boot(vals); cont.append([k,ch,m,lo,hi])
kap=[]
for c in (0.,.6,1.):
 for kl,kh in ((1.,5.),(5.,20.)):
  vals=[by[(i,kh,c)]['absolute_error']-by[(i,kl,c)]['absolute_error'] for i in ids]
  m,lo,hi=boot(vals); kap.append([c,kl,kh,m,lo,hi])
def write(name,head,data):
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(head);w.writerows(data)
OUT.mkdir(exist_ok=True)
write('AE04_CELL_SUMMARY.csv',['kappa','C','median_abs_error','lo','hi','vulnerable_fraction','vuln_lo','vuln_hi'],cell)
write('AE04_CONTAMINATION_CONTRASTS.csv',['kappa','C_high','median_diff_high_minus_C0','lo','hi'],cont)
write('AE04_KAPPA_CONTRASTS.csv',['C','kappa_low','kappa_high','median_diff_high_minus_low','lo','hi'],kap)
s={'B':B,'seed':SEED,'cells':len(cell),'contamination_contrasts':len(cont),'contamination_ci_above_zero':sum(x[3]>0 for x in cont),'kappa_contrasts':len(kap),'kappa_ci_below_zero':sum(x[5]<0 for x in kap),'input_sha256':hashlib.sha256(IN.read_bytes()).hexdigest()}
(OUT/'AE04_SUMMARY_v1_1.json').write_text(json.dumps(s,indent=2),encoding='utf-8');print(json.dumps(s,indent=2))

