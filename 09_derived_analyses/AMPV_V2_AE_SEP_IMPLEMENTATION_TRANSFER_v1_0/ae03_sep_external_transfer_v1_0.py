import csv, json, math, sys
from pathlib import Path
import numpy as np
import sep

SIZE=256; AP=30; F_REF=1000.0
KAPPAS=(1,5,20); C_LEVELS=(0.0,0.6,1.0); LHS_SEED=20261003

def lhs2(n,seed=LHS_SEED):
    rng=np.random.default_rng(seed); cols=[]
    for _ in range(2):
        u=(np.arange(n)+rng.random(n))/n; rng.shuffle(u); cols.append(u)
    return np.column_stack(cols)

def gaussian_source(F,sigma):
    y,x=np.mgrid[:SIZE,:SIZE]; c=SIZE//2
    g=np.exp(-((x-c)**2+(y-c)**2)/(2*sigma*sigma))
    return np.ascontiguousarray(F*g/g.sum(),dtype=np.float64)

def i2p(seed,level=1.0):
    rng=np.random.default_rng(seed); y,x=np.mgrid[:SIZE,:SIZE]; c=SIZE//2
    a=rng.uniform(0,2*np.pi); dist=rng.uniform(38,70)
    cx=c+dist*np.cos(a); cy=c+dist*np.sin(a)
    p=rng.uniform(0,2*np.pi); cp,sp=np.cos(p),np.sin(p)
    dx=x-cx; dy=y-cy; u=cp*dx+sp*dy; v=-sp*dx+cp*dy
    su=rng.uniform(5,12); sv=rng.uniform(1.5,3.5)
    return 0.02*F_REF*level*np.exp(-(u*u/(2*su*su)+v*v/(2*sv*sv)))

def neutral_field(seed):
    rng=np.random.default_rng(seed); y,x=np.mgrid[:SIZE,:SIZE]
    z=rng.normal(0,1,(SIZE,SIZE)); grad=(x/(SIZE-1)-.5)*4.
    cr=np.zeros_like(z)
    for _ in range(8):
        yy=int(rng.integers(0,SIZE)); xx=int(rng.integers(0,SIZE)); cr[yy,xx]+=rng.uniform(5,15)
    return z+grad+cr

def run(n,outcsv):
    D=lhs2(n); rows=[]
    for sid in range(n):
        af=.8+D[sid,0]*.4; sig=1.5+D[sid,1]*2.5
        base=neutral_field(910000+sid); contam=base+i2p(920000+sid)
        for k in KAPPAS:
            F=F_REF*af*k; clean=gaussian_source(F,sig)
            for clev in C_LEVELS:
                im=np.ascontiguousarray(clean+clev*contam,dtype=np.float64)
                flux,fluxerr,flag=sep.sum_circle(im,[128.0],[128.0],30.0,bkgann=(50.0,90.0),subpix=0)
                v=float(flux[0]); fl=int(flag[0]); e=(v-F)/F
                rows.append((sid,k,clev,F,sig,v,float(fluxerr[0]),fl,e,abs(e),abs(e)>.5))
    cols=['sample_id','kappa_ref_target','C','F_true','sigma_psf','SEP_flux','SEP_fluxerr','SEP_flag','signed_error','absolute_error','vulnerable_tau_0_5']
    with open(outcsv,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(cols); w.writerows(rows)
    finite=all(math.isfinite(float(x)) for r in rows for x in (r[3],r[4],r[5],r[6],r[8],r[9]))
    summary={'rows':len(rows),'sample_ids':n,'expected_rows':n*9,'all_finite':finite,'nonzero_flags':sum(r[7]!=0 for r in rows),'sep_version':sep.__version__,'numpy_version':np.__version__}
    Path(str(outcsv)+'.summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    n=int(sys.argv[1]); run(n,sys.argv[2])
