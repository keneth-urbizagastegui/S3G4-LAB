"""Native LTspice S6; ten workers from H0; fixed protected S1-S5.

python ejecutar_s6.py --smoke; python ejecutar_s6.py
S3G4_MODELS overrides the read-only manufacturer model directory.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s4 as s4
import analisis_s6 as a6

ROOT=Path(__file__).resolve().parent
MODELS,LT=s4.MODELS,s4.LT
PROJECT=MODELS.parents[1]
STATES={'P':0,'Z':1,'R':2}
RSWS=[400,825,1500]
TARGETS=[.5e6,1e6,2e6]
OUT=ROOT/'resultados'
BASE_FIELDS=['id','test','RSW_Ohm','state','target_Hz','freq_Hz','M','level_V','source_dc_V','source_amp_V','section','probe']
METRIC_FIELDS=BASE_FIELDS+['adc','samples','reference_mean_V','error_max_mV','error_rms_mV','error_max_LSB','error_rms_LSB','error_mean_mV','a','b','c_V','residual_rms_mV','residual_max_mV','residual_rms_LSB','residual_max_LSB','gain_delta_db','phase_delta_deg','block_rms_delta_mV']
FFT_FIELDS=BASE_FIELDS+['sequence','sfdr_db','sfdr_bin','thd_pct','interleave_dbc','interleave_bin','fundamental_pp_V','mean_V']
SAMPLE_FIELDS=['id','n','adc','time_s','sample_V','reference_V','error_V','track_left_time_s','track_left_clock_V','closing_clock_time_s','closing_time_error_ps']
BIN_FIELDS=['id','sequence','bin','freq_Hz','amplitude_V']
LOOP_FIELDS=BASE_FIELDS+['crossover_Hz','phase_margin_deg','loop_current_ratio_abs','tian_crossover_Hz','tian_phase_margin_deg','tian_voltage_pm_delta_deg']

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')

def csv_write(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='raise');w.writeheader()
        w.writerows(sorted(rows,key=lambda r:(r.get('id',''),str(r.get('sequence','')),r.get('adc',0),r.get('n',r.get('bin',0)))))

def num(x):return s4.number(x)

def case(test,rsw=825,state='P',target=0,level=1.25,section='NA',probe='NA'):
    m,f=a6.coherent(target) if target else (0,0.)
    c=dict(test=test,RSW_Ohm=rsw,state=state,target_Hz=target,freq_Hz=f,M=m,level_V=level,
           source_dc_V=0.,source_amp_V=0.,section=section,probe=probe)
    c['id']=f'{test}_rsw{num(rsw)}_{state}_f{num(f)}_level{num(level)}_{section}_{probe}'.lower()
    if test in ['H0DC','H0AC','H4']:
        c['level_V']='NA'
        c['id']=c['id'].replace('level'+num(level),'levelna')
        c['RSW_Ohm']='NA';c['state']='NA'
        c['id']=c['id'].replace('rsw'+num(rsw)+'_'+state.lower(),'rswna_na')
    return c

def header(c):
    return [f'* {c["id"]}: real circuit state, no changed component values',
            f'.include "{ROOT/"comun/ch1_comun_s6.inc"}"',
            f'.include "{MODELS/"OPA836/opa836_a.lib"}"',
            f'.include "{MODELS/"AD8039/AD8038_ltspice.sub"}"',
            '.param BUFFER_KIND=810','.temp 25',
            '.options numdgt=15 plotwinsize=0 threads=1',
            '.options method=gear solver=alt reltol=1e-5 abstol=1e-12 gminsteps=0',
            'VDD VDDA 0 3.3','VREF REF 0 2.5','VDAC DAC 0 1.25','VP VP 0 5','VN VN 0 -5']

def meas(c,mode,name,expr):return f'.meas {mode} {c["id"]}_{name} {expr}'

def net(c,dt=.5e-9):
    l=header(c);test=c['test']
    if test=='H0TIMING':
        l+=['VINPUT PIN 0 1.25',f'XADC PIN CS1 CS2 CLK1 CLK2 RESET1 RESET2 ADC_S6 RSW={c["RSW_Ohm"]} STATE={STATES[c["state"]]}',
            '.save V(CLK1) V(CLK2) V(RESET1) V(RESET2) V(CS1) V(CS2)',
            meas(c,'TRAN','adc1_width','TRIG V(CLK1) VAL=0.5 RISE=1 TARG V(CLK1) VAL=0.5 FALL=1'),
            meas(c,'TRAN','adc1_period','TRIG V(CLK1) VAL=0.5 RISE=1 TARG V(CLK1) VAL=0.5 RISE=2'),
            meas(c,'TRAN','adc12_shift','TRIG V(CLK1) VAL=0.5 RISE=1 TARG V(CLK2) VAL=0.5 RISE=1'),
            '.tran 0 2u 0 .5n']
    elif test=='H4':
        if c['section']=='OPA836':
            l += [f'XLOAD INPUT PIN VDDA REF DAC STAGE_S6 LV={int(c["probe"]=="V")} LI={int(c["probe"]=="I")}',
                  'VI INPUT 0 0',
                  'BRET RET 0 V=V(XLOAD:SUM)','BINJ INJ 0 V=V(XLOAD:IM)',
                  '.save V(RET) V(INJ) I(XLOAD:VIM)']
        else:
            j=int(c['section'][-1]);ra,cf,cg=(1110,56e-12,47e-12) if j==1 else (499,220e-12,56e-12)
            # Break selected amplifier OUTPUT: both negative unity feedback and
            # positive C1 Sallen-Key feedback belong to the measured loop.
            # Breaking only IN- leaves a positive loop with RHP poles open.
            l+=['VI INPUT 0 0']
            for k in [1,2]:
                r,cfk,cgk=(1110,56e-12,47e-12) if k==1 else (499,220e-12,56e-12)
                incoming='INPUT' if k==1 else 'OA'
                outgoing='OA' if k==1 else 'FILTEROUT'
                l += [f'R{k}A {incoming} M{k} {r}',f'R{k}B M{k} P{k} {r}',
                      f'C{k}A M{k} {outgoing} {cfk:.17g}',f'C{k}B P{k} 0 {cgk:.17g}',f'C{k}PCB P{k} 0 1p',
                      f'VFB{k} AMP_OUT{k} {outgoing} DC 0 AC {int(k==j and c["probe"]=="V")}',
                      f'ITEST{k} 0 {outgoing} DC 0 AC {int(k==j and c["probe"]=="I")}',
                      f'XAMP{k} P{k} {outgoing} VP VN AMP_OUT{k} AD8038']
            l+=['XLOAD FILTEROUT PIN VDDA REF DAC STAGE_S6',
                f'BRET RET 0 V=V(AMP_OUT{j})',f'BINJ INJ 0 V=V({"OA" if j==1 else "FILTEROUT"})',
                f'.save V(RET) V(INJ) I(VFB{j})']
        l += [meas(c,'AC','return_1k','FIND mag(V(RET)/V(INJ)) AT=1k'),'.ac dec 500 1k 1G']
    else:
        filtered=test in ['H3','H0AC'] and c['section']=='TR'
        l+=['XREF INPUTREF REFERENCE VDDA REF DAC STAGE_S6']
        if filtered:
            l+=['XFILTREF SOURCE INPUTREF VP VN FILTER_TR_S6']
        else:l+=['VLINKREF SOURCE INPUTREF 0']
        if test=='H0DC':
            l+=['VI SOURCE 0 0','.save V(REFERENCE) V(SOURCE)',
                meas(c,'DC','center','FIND V(REFERENCE) AT=0'),'.dc VI -0.1 0.1 0.1']
        elif test=='H0AC':
            l+=['VI SOURCE 0 0 AC 1','.save V(REFERENCE) V(SOURCE)',
                meas(c,'AC','gain','FIND mag(V(REFERENCE)) AT='+format(c['freq_Hz'],'.17g')),
                f'.ac lin 3 {c["freq_Hz"]*.999:.17g} {c["freq_Hz"]*1.001:.17g}']
        else:
            l+=['XLOAD INPUTLOAD PIN VDDA REF DAC STAGE_S6']
            l+=['XFILTLOAD SOURCE INPUTLOAD VP VN FILTER_TR_S6'] if filtered else ['VLINKLOAD SOURCE INPUTLOAD 0']
            source=f'{c["source_dc_V"]:.17g}'
            if test!='H1':source=f'SINE({c["source_dc_V"]:.17g} {c["source_amp_V"]:.17g} {c["freq_Hz"]:.17g})'
            l += [f'VI SOURCE 0 {source}',f'XADC PIN CS1 CS2 CLK1 CLK2 RESET1 RESET2 ADC_S6 RSW={c["RSW_Ohm"]} STATE={STATES[c["state"]]}',
                  '.save V(PIN) V(REFERENCE) V(CS1) V(CS2) V(CLK1) V(CLK2) V(SOURCE)',
                  meas(c,'TRAN','reference_mean','AVG V(REFERENCE) FROM=20u TO=30u')]
            # Two previous samples available for regression; sample at exact end.
            count=64 if test=='H1' else a6.N
            stop=a6.START+a6.TS+(a6.FIRST+count)*1/a6.FS
            l += [f'.tran 0 {stop:.17g} 0 {dt:.17g}']
    return '\n'.join(l+['.end'])+'\n'

def protected():
    files=[p for p in ROOT.rglob('*') if p.is_file() and not p.is_relative_to(ROOT/'S6') and
           not p.name.startswith('s6_') and p.name not in ['ejecutar_s6.py','analisis_s6.py','verificar_s6.py','ch1_comun_s6.inc','ACTA_S6.md','RESPUESTA_FINAL_S6.md']
           and p.suffix.lower() not in ['.raw','.log','.db'] and '__pycache__' not in p.parts]
    files += [p for p in MODELS.rglob('*') if p.is_file()]
    files += [PROJECT/'ai-context'/p for p in ['STATE.md','DECISIONS.md']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}

def simulate(c,work,dt=.5e-9):
    path=work/(c['id']+'.cir');deck=net(c,dt);write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    record=dict(id=c['id'],returncode=0,errors=[],warnings=[])
    data={}
    try:
        proc=subprocess.run([str(LT),'-b',str(path)],cwd=work,capture_output=True,timeout=7200)
        vals,errors,warnings,_=s4.s3.prior.old.read_log(path.with_suffix('.log'))
        # LTspice TRIG/TARG emits name=value, unlike FIND/AVG name:...=value.
        logtext=path.with_suffix('.log').read_text(encoding='utf-8',errors='replace')
        vals.update({m[1].lower():float(m[2]) for m in re.finditer(r'^([\w]+)=([+\-\d.eE]+)\s',logtext,re.M)})
        expected={x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        if expected-set(vals):errors.append('Missing measures: '+str(sorted(expected-set(vals))))
        record.update(returncode=proc.returncode,errors=errors,warnings=warnings)
        if proc.returncode or errors:return data,record
        raw=s4.s3.raw_read(path.with_suffix('.raw'))
        if c['test']=='H0DC':
            x=raw['v(source)'];y=raw['v(reference)'];g,center=np.polyfit(x,y,1)
            data=dict(c,dc_gain=float(g),center_V=float(center))
        elif c['test']=='H0AC':
            data=dict(c,gain=float(abs(raw['v(reference)'][1])))
        elif c['test']=='H0TIMING':
            edges=[]
            for adc in [1,2]:
                v=raw[f'v(clk{adc})'];t=raw['time'];inds=np.flatnonzero((v[:-1]-.5)*(v[1:]-.5)<0)
                for i in inds:
                    when=float(t[i]+(.5-v[i])*(t[i+1]-t[i])/(v[i+1]-v[i]))
                    edges.append(dict(adc=adc,edge='rise' if v[i+1]>v[i] else 'fall',time_s=when))
            data=dict(c,edges=sorted(edges,key=lambda e:e['time_s']),**{k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        elif c['test']=='H4':
            key='i(xload:vim)' if c['section']=='OPA836' else 'i(vfb'+c['section'][-1]+')'
            data=dict(c,raw=raw,probe_current=raw[key])
        else:
            metrics,samples,fft,bins=a6.analyze(raw,c)
            data=dict(c,metrics=metrics,samples=samples,fft=fft,bins=bins)
    except Exception as exc:record['errors'].append(repr(exc))
    if not record['errors'] and not record['returncode']:
        for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    return data,record

def execute(cases,work,dt=.5e-9):
    data=[];records=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures={pool.submit(simulate,c,work,dt):c for c in cases}
        for future in as_completed(futures):
            c=futures[future];d,r=future.result();records.append(r)
            if d:data.append(d)
            print('DONE',c['id'],'ERROR '+str(r['errors']) if r['errors'] or r['returncode'] else 'OK',flush=True)
    return sorted(data,key=lambda c:c['id']),sorted(records,key=lambda c:c['id'])

def loop_analysis(data):
    result=[];traces=[]
    for section in ['OPA836','U105A1','U105B2']:
        v=next(d for d in data if d['section']==section and d['probe']=='V')
        i=next(d for d in data if d['section']==section and d['probe']=='I')
        crossings,tv=a6.loop_metrics(v['raw']);f=v['raw']['frequency']
        # Middlebrook two-injection (Tian return ratio). Current signs are
        # upstream-to-downstream VIM/VFB and ground-to-downstream ITEST.
        ti=-i['probe_current']/(i['probe_current']+1)
        tt=(tv*ti-1)/(tv+ti+2)
        fake={'frequency':f,'v(ret)':-tt,'v(inj)':np.ones(len(f))}
        exact,_=a6.loop_metrics(fake)
        for r in crossings:
            e=min(exact,key=lambda z:abs(np.log(z['crossover_Hz']/r['crossover_Hz'])))
            result.append({k:v[k] for k in BASE_FIELDS}|r|dict(loop_current_ratio_abs=float(np.interp(np.log(r['crossover_Hz']),np.log(f),abs(ti))),
                tian_crossover_Hz=e['crossover_Hz'],tian_phase_margin_deg=e['phase_margin_deg'],
                tian_voltage_pm_delta_deg=e['phase_margin_deg']-r['phase_margin_deg']))
        traces += [dict(section=section,freq_Hz=float(ff),tv_real=float(vv.real),tv_imag=float(vv.imag),ti_real=float(ii.real),ti_imag=float(ii.imag),tian_real=float(z.real),tian_imag=float(z.imag)) for ff,vv,ii,z in zip(f,tv,ti,tt)]
    return result,traces

def criteria(metrics,fft,loops,complete):
    result=[]
    p=[r for r in metrics if r['state']=='P' and r['RSW_Ohm']==825]
    h1=[r for r in p if r['test']=='H1'];h2=[r for r in p if r['test']=='H2' and r['target_Hz']==2e6]
    h23=h2+[r for r in p if r['test']=='H3']
    sf=[r['sfdr_db'] for r in fft if r['state']=='P' and r['RSW_Ohm']==825 and r['target_Hz']==2e6 and r['sequence']=='loaded']
    tests=[(1,max([r['error_max_LSB'] for r in h1],default=np.inf),.5,'LSB',len(h1)==6),
           (2,max([r['error_max_LSB'] for r in h2],default=np.inf),.5,'LSB',len(h2)==2),
           (3,max([r['residual_rms_LSB'] for r in h23],default=np.inf),.5,'LSB rms',len(h23)==4 and len(sf)==2),
           (4,max([abs(r['gain_delta_db']) for r in h2],default=np.inf),.1,'dB',len(h2)==2)]
    for n,value,limit,unit,coverage in tests:
        ok=value<=limit
        desc=f'{value:.9g} {unit} <= {limit}'
        if n==3:
            worst=min(sf,default=-np.inf);ok=ok and worst>=66;desc+=f'; SFDR min {worst:.9g} dB >= 66'
        result.append(dict(criterion=f'S6-C{n}',status=('PASA' if ok else 'FALLA') if coverage and complete else 'PARCIAL',value=desc))
    opa=[r for r in loops if r['section']=='OPA836'];pm=min([r['tian_phase_margin_deg'] for r in opa],default=-np.inf)
    result.append(dict(criterion='S6-C5',status=('PASA' if pm>=45 else 'FALLA') if opa and complete else 'PARCIAL',value=f'{pm:.9g} deg >= 45'))
    return result

METHOD='''
## Circuito, modelo y límites

Fuentes: PLAN/ENCARGO S6 completos; PLAN/ACTA/AUDITORIA S5 completos;
AUDITORIA S4 completa; DECISIONS del 3 oct; revisión de entrada §6 E18;
g473_analogico §§2–3; canal_rapido bloque ⑨; modelos/LEEME; fuentes
ch1_comun_s4.inc, ch1_comun_s5.inc y ejecutar_s5.py. No se han descargado
modelos ni modificado las fuentes anteriores. No es prueba física.

S4 cerrado: RIN/RF 10k, ROFF8.06k, CF1p, CSUM1p, OPA836 a3.3V,
PD aVDDA; DESD_OPA836 de S4, M1 10k/5.23k+1u por copia; DAC1.25V;
68ohm/470p hasta pin. Los 5p estáticos de S4 se identifican ahora como
Cpad=5p supuesto (pad+pista), y cada ADC tiene Cs=5p conmutado aparte.
H1/H2 parten de fuente ideal en entrada S4. H3 usa únicamente el TR
reescalado contractual, dos AD8038 de LTspice representan AD8039 a±5V,
incluyendo pista1p por entrada. No se añade la cadena S1–S3 ni su carga
sustituta, porque H3 empieza en entrada del filtro y no es S7.

RSW estimado de límite RC de tabla62, no un parámetro publicado ni medido:
(2.5/60MHz)/(5p*ln(2^13))-100ohm. Barrido400/825/1500ohm contractual.
Switch muestreo Ron=RSW, Roff1e15, umbral0.5V; sin inyección de carga,
clock feedthrough, ruido, cuantización ni mismatch entre ADC. Reset ideal
Ron1m durante conversión en Z/R, a0/2.5V. P conserva su propio Cs;
ambos resets apagados en P. El estado inicial DC se establece por Roff;
se descartan256 muestras combinadas antes de analizar. H1 tiene32
muestras por ADC; H2/H3 512 por ADC. Bloques RMS permiten revisar régimen.
Flancos20ps son regularización numérica; umbral exactamente en apertura
y cierre contractuales. Muestreo como límite izquierdo en el umbral
descendente: extrapolación de dos puntos de tracking anteriores al cierre.
Z/R tiene constante de reset5fs: interpolar atravesando el reset falsea la
muestra. El CSV conserva último tiempo/clock de tracking y cruce real
para auditar el límite izquierdo; referencia interpolada al mismo instante.

Referencia: misma S4, M1, ideal source y, en H3, filtro completo, en
paralelo, con68/470p+Cpad y sin switches/Cs. Error=Cs-referencia al mismo
instante, no Cs-pin cargado. LSB=2.5/4096V. H0 DC y AC calculan offset y
amplitud de fuente para niveles deseados y2Vpp en la referencia sin carga;
se informa amplitud/centro real, no se altera ninguna pieza para centrar.
Esto es calibración del estímulo ideal, no compensación del error ADC.

Coherencia:1024 muestras, M impar más cercano a0.5/1/2MHz, frecuencia
M*6.5MHz/1024. Por ello '2MHz' no es exactamente2MHz: se informa la
frecuencia real. FFT rectangular sin ventana ni cuantización; SFDR excluye
DC y fundamental y busca todo el resto hasta Nyquist. THD armónicos2–9,
plegados por alias y con bins únicos; espurio fs/2-fin explícito. El umbral
66dB viene del contrato, mientras documento G473 cita66.9dB single y63.2dB
multi; SFDR determinista no certifica el SNR real del ADC.

Descomposición por ADC: LS sobre error=a*v[n]+b*v[n-2]+c, usando referencia
sin carga. Dos muestras anteriores se simulan antes de la FFT; no wrap
artificial. Parte lineal H=1+a+b*exp(-j*2*pi*f*2/fs); ganancia20log|H| y
faseangle(H). Residuo=error-modelo LS. Se incluyen muestras y bins para
recalcularlo, sin ocultar error absoluto bajo una calibración.

H4: OPA836 inyección Middlebrook en entrada inversora, fuente DC0
entre retorno y entrada; U105 en SALIDA del amplificador, para incluir
las dos rutas de feedback (negativa unidad y positiva C1 Sallen-Key).
Ensayo independiente de corriente con tensión AC0, manteniendo puntoDC
y todas las cargas. Romper sólo IN- de SK deja un lazo positivo cerrado
con polos RHP y un margen ambiguo; no se usa esa primera prueba.
Tv=-Vret/Vinj; Ti=-Iprobe/(Iprobe+Itest), Itest=1A AC, orientación probe
retorno→entrada e Itest masa→entrada. Retorno general Tian/Middlebrook
T=(Tv*Ti-1)/(Tv+Ti+2); fase desenrollada desde0°, todos los cruces
descendentes0dB; PM=180°+fase(T). Se informa también la aproximación Tv
y su diferencia. No se declara PM de sistema periódico con switches:
carga H4 es la fija68ohm+470p+Cpad exigida. U105A conserva secciónB yS4
como carga; U105B conservaS4; fuente ideal en entradaTR. No hay fuenteAC
de señal concurrente. PuntoDC obtenido por macro real, diodos deS4 presentes.

Contradicciones conservadas: guía dice68ohm<=100ohm pero eso sólo compara
resistencia externa estática, no prueba seguimiento durante67ns; S6 lo
mide. E18 exigíaerror absoluto<=0.5LSB; C3/C4 distinguen linealidad y
ganancia, sin sustituir C2. RSW/estado previo/Cpad son suposiciones, no
caracterización de silicio. VREF/DAC ideales no incluyen sus ruido/drift.
No se decide remedio ni se diseñaS7. R_ADC, C_ADC y ciclos de muestreo
podrían mover el error; no se han simulado valores alternativos.

## Reejecución

python ejecutar_s6.py --smoke
python ejecutar_s6.py
En copia de CH1_entrada: S3G4_MODELS=ruta_original_de_modelos.
Diez trabajadores desdeH0, columnasCSV explícitas, filas ordenadas;
.cir/.log conservados enS6 y excluidos de huellas operativas; raw
exitosos eliminados por ser regenerables. HashesS1–S5/modelos/STATE/
DECISIONS antes/después. Código0 significa ejecución completa.
'''

def report(all_data,records,run,calibration,timing,looprows,looptraces):
    prefix='s6_smoke' if run['smoke'] else 's6'
    metrics=[r for d in all_data for r in d.get('metrics',[])];samples=[r for d in all_data for r in d.get('samples',[])]
    fft=[r for d in all_data for r in d.get('fft',[])];bins=[r for d in all_data for r in d.get('bins',[])]
    crit=criteria(metrics,fft,looprows,not run['smoke'] and run['exit_code']==0)
    for test in ['H1','H2','H3']:csv_write(OUT/f'{prefix}_{test.lower()}.csv',[r for r in metrics if r['test']==test],METRIC_FIELDS)
    csv_write(OUT/f'{prefix}_muestras.csv',samples,SAMPLE_FIELDS);csv_write(OUT/f'{prefix}_fft.csv',fft,FFT_FIELDS)
    csv_write(OUT/f'{prefix}_fft_bins.csv',bins,BIN_FIELDS);csv_write(OUT/f'{prefix}_h4.csv',looprows,LOOP_FIELDS)
    csv_write(OUT/f'{prefix}_lazo.csv',looptraces,['section','freq_Hz','tv_real','tv_imag','ti_real','ti_imag','tian_real','tian_imag'])
    csv_write(OUT/f'{prefix}_criterios.csv',crit,['criterion','status','value'])
    csv_write(OUT/f'{prefix}_h0_flancos.csv',timing.get('edges',[]),['adc','edge','time_s'])
    csv_write(OUT/f'{prefix}_calibracion.csv',calibration,BASE_FIELDS+['dc_gain','center_V','gain'])
    write(OUT/f'{prefix}_ejecucion.json',json.dumps(run,ensure_ascii=False,indent=2))
    tab=s4.table
    text=f'# ACTA S6 — ADC entrelazado CH1\n\nCódigo {run["exit_code"]}; {run["simulations"]} simulaciones; {run["elapsed_seconds"]:.3f}s; diez trabajadores. Errores {run["errors"]}; advertencias {run["warnings"]}.\n\n'
    text+=f'RSW deducida={run["RSW_deduced_Ohm"]:.12g}ohm; ventana={timing.get("adc1_width",float("nan"))*1e9:.12g}ns; período={timing.get("adc1_period",float("nan"))*1e9:.12g}ns; desfase={timing.get("adc12_shift",float("nan"))*1e9:.12g}ns.\n\n'
    text+=tab(crit,['criterion','status','value'])+'\n\n'
    nominal=[r for r in metrics if r['RSW_Ohm']==825 and r['state']=='P' and (r['test']!='H2' or r['target_Hz']==2e6)]
    text+='## Continua y seno nominal\n\n'+tab(nominal,['test','freq_Hz','level_V','adc','error_max_mV','error_rms_mV','error_max_LSB','error_rms_LSB','residual_rms_mV','residual_max_mV','gain_delta_db','phase_delta_deg'])+'\n\n'
    text+='## FFT nominal, con y sin carga\n\n'+tab([r for r in fft if r['RSW_Ohm']==825 and r['state']=='P'],['test','freq_Hz','sequence','sfdr_db','thd_pct','interleave_dbc','fundamental_pp_V','mean_V'])+'\n\n'
    text+='## Sensibilidad completa\n\n'+tab(metrics,['test','RSW_Ohm','state','freq_Hz','level_V','adc','error_max_mV','error_rms_mV','residual_rms_mV','gain_delta_db','phase_delta_deg','block_rms_delta_mV'])+'\n\n'
    text+='## Lazo\n\n'+tab(looprows,['section','crossover_Hz','phase_margin_deg','loop_current_ratio_abs','tian_crossover_Hz','tian_phase_margin_deg','tian_voltage_pm_delta_deg'])+'\n\n'
    text+=f'Protegidos={run["protected_files"]}; cambios={run["protected_changed"]}.\n'+METHOD
    write(OUT/f'{prefix}_resumen.md',text)
    if not run['smoke']:write(ROOT/'ACTA_S6.md',text)
    print(tab(crit,['criterion','status','value']),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--h0',action='store_true')
    args=parser.parse_args();start=time.perf_counter();before=protected()
    work=ROOT/'S6'/('smoke' if args.smoke else 'h0' if args.h0 else 'generados');work.mkdir(parents=True,exist_ok=True)
    controls=[case('H0DC'),case('H0TIMING')]+[case('H0AC',target=f) for f in TARGETS]+[case('H0AC',target=2e6,section='TR')]
    print('S6 workers=10; H0 first',flush=True)
    cal,records=execute(controls,work)
    rdeduced=(2.5/60e6)/(5e-12*np.log(2**13))-100
    timing=next((d for d in cal if d['test']=='H0TIMING'),{})
    print('H0 RSW',rdeduced,'timing', {k:v for k,v in timing.items() if k.startswith('adc')},flush=True)
    good=len(cal)==len(controls) and all(abs(timing.get(k,0)-target)<1e-12 for k,target in [('adc1_width',a6.TS),('adc1_period',a6.PERIOD),('adc12_shift',a6.SHIFT)])
    all_data=[];loops=[];looptraces=[]
    if good and not args.h0:
        dc=next(d for d in cal if d['test']=='H0DC')
        for test in ['H1','H2','H4','H3']:
            jobs=[]
            if test=='H1':jobs=[case(test,rsw,st,level=l) for rsw in ([825] if args.smoke else RSWS) for st in STATES for l in [.25,1.25,2.25]]
            elif test=='H2':jobs=[case(test,rsw,st,target=f) for rsw in ([825] if args.smoke else RSWS) for st in STATES for f in ([2e6] if args.smoke else TARGETS)]
            elif test=='H4':jobs=[case(test,section=s,probe=p) for s in ['OPA836','U105A1','U105B2'] for p in ['V','I']]
            else:jobs=[case('H3',target=2e6,section='TR')]
            for c in jobs:
                c['source_dc_V']=0. if test=='H4' else (c['level_V']-dc['center_V'])/dc['dc_gain']
                if test in ['H2','H3']:
                    ac=next(d for d in cal if d['test']=='H0AC' and d['target_Hz']==c['target_Hz'] and d['section']==c['section'])
                    c['source_amp_V']=1/ac['gain']
                if test=='H4':c['source_dc_V']=0.
            print('STAGE',test,len(jobs),flush=True);dd,rr=execute(jobs,work);records+=rr
            if test=='H4' and len(dd)==len(jobs):
                try:loops,looptraces=loop_analysis(dd)
                except Exception as e:records.append(dict(id='h4_analysis',returncode=1,errors=[repr(e)],warnings=[]))
            else:all_data+=dd
            if len(dd)!=len(jobs):break
    # Only remove obsolete generated decks in this resolved S6 work area.
    if not work.resolve().is_relative_to((ROOT/'S6').resolve()):raise ValueError('Work outside S6')
    active={r['id'] for r in records}
    for path in work.glob('*.cir'):
        if path.stem not in active:
            for ext in ['.cir','.log','.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    changed=[p for p,h in before.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records)
    expected=len(controls)+(0 if args.h0 else (9+3 if args.smoke else 27+27)+6+1)
    run=dict(exit_code=int(bool(errors or changed or not good or len(records)!=expected)),simulations=len(records),expected_simulations=expected,
        errors=errors,warnings=sum(bool(r['warnings']) for r in records),elapsed_seconds=time.perf_counter()-start,workers=10,
        smoke=args.smoke,h0_only=args.h0,RSW_deduced_Ohm=float(rdeduced),protected_files=len(before),protected_changed=changed,records=sorted(records,key=lambda r:r['id']))
    # h0 gets its own prefix through dedicated persisted manifest, no full acta.
    if args.h0:
        csv_write(OUT/'s6_h0_flancos.csv',timing.get('edges',[]),['adc','edge','time_s'])
        write(OUT/'s6_h0_ejecucion.json',json.dumps(run,indent=2))
    else:report(all_data,records,run,[{k:v for k,v in c.items() if k!='edges'} for c in cal if c['test']!='H0TIMING'],timing,loops,looptraces)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return run['exit_code']

if __name__=='__main__':raise SystemExit(main())
