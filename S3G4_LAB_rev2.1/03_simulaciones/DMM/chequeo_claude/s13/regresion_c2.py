"""Auditoria Claude S13: que explica error inicial y margen de compliancia en las 100 placas C2."""
import sys,csv,numpy as np
D=sys.argv[1]
c={r['id']:r for r in csv.DictReader(open(D+'/resultados/s13_campaign.csv',encoding='utf-8-sig')) if r['kind']=='compliance'}
s={r['id']:r for r in csv.DictReader(open(D+'/resultados/s13_compliance_summary.csv',encoding='utf-8-sig'))}
ids=sorted(c);f=lambda k,src=c:np.array([float(src[i][k]) for i in ids])
err=f('initial_error_pct');mar=f('margin_calibrated_V',s);ron=f('force_ron_ohm',s)
X=np.c_[np.ones(100),f('vosa'),f('vosb'),f('rail'),ron,f('vto'),f('rref'),f('rset')];names='1 vosa vosb rail ron_mux vto rref rset'.split()
for y,lab in ((err,'error inicial %'),(mar,'margen calibrado V')):
    b,*_=np.linalg.lstsq(X,y,rcond=None);r2=1-np.sum((y-X@b)**2)/np.sum((y-y.mean())**2)
    # contribucion: coef * desviacion tipica
    print(lab,'R2=%.3f'%r2,{n:round(float(b[j]*X[:,j].std()),4) for j,n in enumerate(names) if j})
print('Ron_mux - Ron_nominal: min %.1f max %.1f ohm'%((ron-f('ron')).min(),(ron-f('ron')).max()))
print('margen si Ron_mux = Ron nominal: min %.3f V, fallos %d'%((mar+1e-3*(ron-f('ron'))).min(),int(((mar+1e-3*(ron-f('ron')))<.3).sum())))
print('placas que fallan algun criterio:',sorted({i[-4:] for i in ids if abs(float(c[i]['initial_error_pct']))>1 or float(s[i]['margin_calibrated_V'])<.3}))
