import numpy as np
SIZE=256; AP=30; F_REF=1000.0; AMP_RANGE=(0.8,1.2); SIG_RANGE=(1.5,4.0)
LHS_SEED=20261003; ANALYSIS_SEED=20261004
KAPPAS=(1,2,5,10,20); C_LEVELS=(0.0,0.6,1.0)
def lhs2(n=300,seed=LHS_SEED):
 rng=np.random.default_rng(seed); cols=[]
 for _ in range(2):
  u=(np.arange(n)+rng.random(n))/n; rng.shuffle(u); cols.append(u)
 return np.column_stack(cols)
def gaussian_source(F,sigma):
 y,x=np.mgrid[:SIZE,:SIZE]; c=SIZE//2
 g=np.exp(-((x-c)**2+(y-c)**2)/(2*sigma*sigma)); return F*g/g.sum()
def mask(r1,r2=None):
 y,x=np.ogrid[:SIZE,:SIZE]; c=SIZE//2; q=(x-c)**2+(y-c)**2
 return q<=r1*r1 if r2 is None else (q>=r1*r1)&(q<=r2*r2)
AM=mask(30); BM=mask(50,90)
def A(im): return float(im[AM].sum())
def B(im): return float(im[AM].sum()-im[BM].mean()*AM.sum())
def C(im):
 bg=im[BM]; rng=np.random.default_rng(20260814); best=float(np.median(bg)); score=-1; sd=float(np.std(bg))
 for _ in range(200):
  s=rng.choice(bg,30,replace=False); v=float(np.median(s)); sc=int(np.sum(np.abs(bg-v)<0.2*sd)) if sd>0 else len(bg)
  if sc>score: score=sc; best=v
 return float(im[AM].sum()-best*AM.sum())
def E(im):
 from scipy.optimize import least_squares
 c=SIZE//2; pad=34; x0,x1=c-pad,c+pad+1; patch=im[x0:x1,x0:x1]; yy,xx=np.mgrid[x0:x1,x0:x1]; mk=(xx-c)**2+(yy-c)**2<=AP**2
 bg0=float(np.median(patch[~mk])); amp0=max(float(patch.max())-bg0,1e-12)
 def fun(p):
  xc,yc,amp,sig,bg=p; g=np.exp(-((xx-xc)**2+(yy-yc)**2)/(2*sig**2)); return (bg+amp*g-patch)[mk]
 r=least_squares(fun,[c,c,amp0,3.,bg0],bounds=([x0,x0,0.,1.,-np.inf],[x1-1,x1-1,np.inf,20.,np.inf]),max_nfev=120)
 return float(2*np.pi*abs(r.x[2])*r.x[3]**2),bool(r.success),int(r.status),int(r.nfev)
def i2p(seed,level):
 rng=np.random.default_rng(seed); y,x=np.mgrid[:SIZE,:SIZE]; c=SIZE//2
 a=rng.uniform(0,2*np.pi); dist=rng.uniform(38,70); cx=c+dist*np.cos(a); cy=c+dist*np.sin(a)
 p=rng.uniform(0,2*np.pi); cp,sp=np.cos(p),np.sin(p); dx=x-cx; dy=y-cy; u=cp*dx+sp*dy; v=-sp*dx+cp*dy
 su=rng.uniform(5,12); sv=rng.uniform(1.5,3.5); return 0.02*F_REF*level*np.exp(-(u*u/(2*su*su)+v*v/(2*sv*sv)))
def neutral_field(seed):
 rng=np.random.default_rng(seed); y,x=np.mgrid[:SIZE,:SIZE]; z=rng.normal(0,1,(SIZE,SIZE)); grad=(x/(SIZE-1)-.5)*4.
 cr=np.zeros_like(z)
 for _ in range(8):
  yy=int(rng.integers(0,SIZE)); xx=int(rng.integers(0,SIZE)); cr[yy,xx]+=rng.uniform(5,15)
 return z+grad+cr
