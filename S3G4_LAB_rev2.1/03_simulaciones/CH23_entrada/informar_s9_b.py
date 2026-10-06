"""Derived S9-B tables; append current comparison, preserving historical A acta."""
import sys
sys.dont_write_bytecode=True
import csv,json,time
from pathlib import Path
import numpy as np
import ejecutar_s9_b as b
from informar_s9 import table
s=b.s;ROOT=b.ROOT;OUT=ROOT/'resultados'

def main():
    work=ROOT/'S9/B_hoja/campaign'
    d=json.loads((work/'s9b_checkpoint.json').read_text());meta=json.loads((work/'s9b_meta.json').read_text())
    if meta['successful']!=meta['logical_cases']:raise RuntimeError('Campaign incomplete')
    rows=d['rows'];extra=d['extras'];arows=json.loads((ROOT/'S9/campaign/s9_checkpoint.json').read_text())['rows']
    corrected_work=ROOT/'S9/B_hoja/op_corregido'
    corrected=json.loads((corrected_work/'s9b_op_corregido_checkpoint.json').read_text())['rows']
    corrected_meta=json.loads((corrected_work/'s9b_op_corregido_meta.json').read_text())
    corrected_audit=json.loads((corrected_work/'s9b_op_corregido_auditoria.json').read_text())
    if (len(corrected)!=2000 or corrected_meta['successful']!=2000
            or corrected_meta['returncode'] or corrected_meta['protected_changed']
            or corrected_audit['returncode']):
        raise RuntimeError('Corrected OP campaign incomplete or not audited')
    corrected_history=[json.loads(line) for line in (corrected_work/'native_history.jsonl').read_text().splitlines() if line.strip()]
    corrected_accounting=dict(reference_simulations=corrected_meta['simulations'],
                              native_attempts=len(corrected_history),
                              failed_native_attempts=sum(record['returncode']!=0 for record in corrected_history),
                              successful_logical_cases=corrected_meta['successful'],
                              explanation='Native history includes timed-out and repeated points; reference count comes from final successful case records.')
    s.write(OUT/'s9b_op_corregido_contabilidad.json',json.dumps(corrected_accounting,indent=2))
    criteria=[]
    def add(n,scope,rs,predicate,pop=True):
        ok=sum(bool(predicate(r)) for r in rs);N=len(rs);frac=ok/N if N else 0
        criteria.append(dict(criterion=f'S9-C{n}',variant='B',scope=scope,N=N,pass_count=ok,fraction=frac,status='PASA' if N and frac>=(.95 if pop else 1) else 'FALLA',population=pop))
    for ix in [0,3,6,9]:
        ac=[r for r in rows if r['ix']==ix and r['test']=='K5AC']
        op=[r for r in rows if r['ix']==ix and r['test']=='K5OP' and r['mc']>=0]
        scope=f'{s.SCALES[ix]} V/div MC'
        add(1,scope,ac,lambda r:.85e6<=r['minus3_Hz']<=1.15e6)
        add(2,scope,ac,lambda r:r['peak_db']<=1)
        add(3,scope,ac,lambda r:r['atten_2p47m_db']>=20)
        add(5,scope,op,lambda r:abs(r['gain_error_pct'])<=5)
        add(9,scope,op,lambda r:r['position_pass'])
    for ix in [0,6]:add(4,f'{s.SCALES[ix]} V/div MC (100)',[r for r in rows if r['ix']==ix and r['test']=='K5NOISE'],lambda r:r['noise_pct_div']<=.5)
    add(4,'12 escalas nominales',[r for r in rows if r['test']=='K3'],lambda r:r['noise_pct_div']<=.5,False)
    add(6,'K4 compartido de A; no reejecutado',[r for r in arows if r['test']=='K4' and r['RSW']==825],lambda r:r['sfdr_db']>=60 and r['residual_rms_LSB']<=.5,False)
    prot=[r for r in rows if r['test']=='K6'];rec=[r for r in rows if r['test']=='K6REC']
    add(7,'36 barridos deterministas, rieles extremos',prot,lambda r:r['protection_pass'],False)
    add(8,'recuperaciones sin BAV199; límite vigente 2 µs',[r for r in rec if not r['bav199_conducts']],lambda r:r.get('recovery_us') is not None and r['recovery_us']<=2,False)
    s.csv_write(OUT/'s9b_criterios.csv',criteria,['criterion','variant','scope','N','pass_count','fraction','status','population'])
    corrected_criteria=[]
    for r in criteria:
        item=dict(r)
        if r['criterion'] in ['S9-C5','S9-C9']:
            ix=next(i for i in [0,3,6,9] if r['scope']==f'{s.SCALES[i]} V/div MC')
            cohort=[x for x in corrected if x['ix']==ix]
            ok=sum(abs(x['gain_error_pct'])<=5 if r['criterion']=='S9-C5' else x['position_pass'] for x in cohort)
            item.update(N=len(cohort),pass_count=ok,fraction=ok/len(cohort),status='PASA' if ok/len(cohort)>=.95 else 'FALLA')
        corrected_criteria.append(item)
    s.csv_write(OUT/'s9b_criterios_op_corregido.csv',corrected_criteria,['criterion','variant','scope','N','pass_count','fraction','status','population'])
    ac=[r for r in csv.DictReader((OUT/'s9_criterios.csv').open()) if r['variant']=='A']
    # Reevaluate stored A measurements in memory only; never rewrite A deliverables.
    arec=[r for r in arows if r['test']=='K6REC' and not r['bav199_conducts']]
    for r in ac:
        if r['criterion']=='S9-C8':
            N=len(arec);ok=sum(x.get('recovery_us') is not None and x['recovery_us']<=2 for x in arec)
            r.update(scope='recuperaciones sin BAV199; límite vigente 2 µs',N=N,pass_count=ok,fraction=ok/N if N else 0,status='PASA' if N and ok==N else 'FALLA')
    compact=[]
    for n in range(1,10):
        item=dict(criterio=f'S9-C{n}')
        for v,cr in [('A',ac),('B_original',criteria),('B_corregida',corrected_criteria)]:
            rr=[r for r in cr if r['criterion']==item['criterio']]
            item[v]='; '.join(f'{r["scope"]}: {r["pass_count"]}/{r["N"]} ({100*float(r["fraction"]):.1f}%)' for r in rr)+' — '+('PASA' if all(r['status']=='PASA' for r in rr) else 'FALLA')
            if v.startswith('B') and n in [7,8]:item[v]+=' (LM6172: topología de saturación/protección National; sin validación contra silicio)'
        compact.append(item)
    nominal=[];sources=[]
    for ix in range(12):
        rr={test:next(r for r in rows if r['test']==test and r['ix']==ix and r['mc']<0) for test in ['K1','K2','K3','K5OP']}
        row=dict(rr['K1']);row.update(rr['K2']);row.update(rr['K3'])
        for k in ['gain_dc_signed','gain_nominal_signed','gain_error_pct','center_V','offset_uncal_V','position_plus_div','position_minus_div']:row[k]=rr['K5OP'][k]
        row.update(id=f's9b_nominal_b_s{ix:02d}',test='NOMINAL_COMBINADO',kind='combined',amplitude_V='');nominal.append(row)
        sources.append(dict(variant='B',scale_V_div=s.SCALES[ix],**{t:rr[t]['id'] for t in rr}))
    s.csv_write(OUT/'s9b_nominal.csv',nominal,s.FIELDS)
    s.csv_write(OUT/'s9b_nominal_sources.csv',sources,['variant','scale_V_div','K1','K2','K3','K5OP'])
    cal=[dict(escala_V_div=r['scale_V_div'],rele=r['POS'],toma=r['tap'],ganancia_medida=r['gain_dc_signed'],ganancia_nominal=r['gain_nominal_signed'],signo=-1) for r in nominal]
    # This previously empty B deliverable is explicitly requested; A remains unchanged.
    s.csv_write(OUT/'s9_tabla_calibracion_B.csv',cal,['escala_V_div','rele','toma','ganancia_medida','ganancia_nominal','signo'])
    stats=[]
    for ix in [0,3,6,9]:
        for metric,test in [('minus3_Hz','K5AC'),('peak_db','K5AC'),('atten_2p47m_db','K5AC'),('gain_dc_signed','K5OP'),('offset_uncal_V','K5OP'),('noise_pct_div','K5NOISE')]:
            vals=np.array([r[metric] for r in rows if r['ix']==ix and r['test']==test and r['mc']>=0])
            if not len(vals):continue
            lo,hi=np.percentile(vals,[2.5,97.5]);stats.append(dict(variant='B',scale_V_div=s.SCALES[ix],metric=metric,N=len(vals),min=float(vals.min()),p2p5=float(lo),p97p5=float(hi),max=float(vals.max())))
    s.csv_write(OUT/'s9b_estadisticas.csv',stats,['variant','scale_V_div','metric','N','min','p2p5','p97p5','max'])
    corrected_stats=[]
    for ix in [0,3,6,9]:
        for metric in ['gain_dc_signed','gain_error_pct','offset_uncal_V','dac_center_V','position_plus_div','position_minus_div']:
            vals=np.array([r[metric] for r in corrected if r['ix']==ix])
            lo,hi=np.percentile(vals,[2.5,97.5])
            corrected_stats.append(dict(variant='B_OP_CORREGIDA',scale_V_div=s.SCALES[ix],metric=metric,N=len(vals),min=float(vals.min()),p2p5=float(lo),p97p5=float(hi),max=float(vals.max())))
    s.csv_write(OUT/'s9b_estadisticas_op_corregido.csv',corrected_stats,['variant','scale_V_div','metric','N','min','p2p5','p97p5','max'])
    offset_summary=[]
    for ix in [0,3,6,9]:
        rr=[r for r in rows if r['ix']==ix and r['test']=='K5OP' and r['mc']>=0]
        offset_summary.append(dict(scale_V_div=s.SCALES[ix],N=len(rr),center_compensable=sum(r['offset_compensable'] for r in rr),position_pass=sum(r['position_pass'] for r in rr),dac_center_min_V=min(r['dac_center_V'] for r in rr),dac_center_max_V=max(r['dac_center_V'] for r in rr),position_plus_min_div=min(r['position_plus_div'] for r in rr),position_minus_min_div=min(r['position_minus_div'] for r in rr)))
    s.csv_write(OUT/'s9b_offset_resumen.csv',offset_summary,list(offset_summary[0]))
    offset_comparison=[]
    for original_row in offset_summary:
        ix=next(i for i in [0,3,6,9] if s.SCALES[i]==original_row['scale_V_div'])
        rr=[r for r in corrected if r['ix']==ix]
        corrected_row=dict(scale_V_div=s.SCALES[ix],N=len(rr),center_compensable=sum(r['offset_compensable'] for r in rr),position_pass=sum(r['position_pass'] for r in rr),dac_center_min_V=min(r['dac_center_V'] for r in rr),dac_center_max_V=max(r['dac_center_V'] for r in rr),position_plus_min_div=min(r['position_plus_div'] for r in rr),position_minus_min_div=min(r['position_minus_div'] for r in rr))
        for version,r in [('original_sesgada',original_row),('corregida_contractual',corrected_row)]:
            offset_comparison.append(dict(version=version,**r,position_fraction=r['position_pass']/r['N'],gain_pass=sum(abs(x['gain_error_pct'])<=5 for x in (rows if version=='original_sesgada' else corrected) if x['test']=='K5OP' and x['ix']==ix and x['mc']>=0)))
    s.csv_write(OUT/'s9b_offset_comparacion.csv',offset_comparison,list(offset_comparison[0]))
    # Static inspection only: AD8038 has no input VOS source or unequal input terms.
    admodel=s.MODELS/'AD8039/AD8038_ltspice.sub'
    adtext=admodel.read_text()
    for required in ['B1 N003 0 I=1m*dnlim(uplim(V(2)', 'B2 0 N003 I=1m*dnlim(uplim(V(1)', '100n*V(2)', '100n*V(1)']:
        if required not in adtext:raise RuntimeError('AD8038 static offset evidence changed')
    ad_offset=dict(model=str(admodel),method='Static algebraic inspection; no simulation',intrinsic_input_offset_mV=0,conditions='Equal inputs, symmetric supplies and matched ideal model branches; numerical/common-mode errors not independently measured',same_double_counting=False,explanation='B1/B2 use identical functions with opposite current directions; no fixed VOS source. Independent MC +/-3 mV is not added to a preexisting fixed 3 mV offset in this model. Other stages and nonsymmetric-supply effects not requalified.')
    s.write(OUT/'s9b_offset_ad8038_inspeccion.json',json.dumps(ad_offset,indent=2))
    limitation='LM6172: saturación/protecciones heredadas de National; no validadas contra silicio.'
    limits=[]
    for stage in s.old.STAGES:
        rr=[r for r in extra['limits'] if r['stage']==stage]
        field='pin_current_abs_max_A' if stage.startswith(('U103','U105')) else 'current_abs_max_A'
        limits.append(dict(stage=stage,differential_V=max(r['differential_abs_max_V'] for r in rr),input_max_mA=1e3*max(max(r['plus_'+field],r['minus_'+field]) for r in rr),limitacion=limitation))
    info=[dict(adc_min_V=min(r['adc_min_V'] for r in prot),adc_max_V=max(r['adc_max_V'] for r in prot),mux_low_margin_V=min(r['mux_low_margin_V'] for r in prot),mux_high_margin_V=min(r['mux_high_margin_V'] for r in prot),mux_supply_max_V=max(r['mux_supply_max_V'] for r in prot),bav99_max_mA=1e3*max(r['current_abs_max_A'] for r in extra['bav99']),limitacion=limitation)]
    for r in rec:r['limitacion']=limitation
    s.csv_write(OUT/'s9b_limites_resumen.csv',limits,list(limits[0]))
    s.csv_write(OUT/'s9b_protecciones_resumen.csv',info,list(info[0]))
    s.csv_write(OUT/'s9b_recuperacion_resumen.csv',rec,s.FIELDS+['limitacion'])
    consum=extra['consumption']
    original=json.loads((OUT/'s9_k0.json').read_text());gate=json.loads((OUT/'s9b_puerta_k0.json').read_text());adj=gate['rows']
    oldop=next(r for r in original if r['mode']=='op' and r['vin']==0 and r['rail']==4.9 and 'gmin12' not in r['id'])
    def find(rs,mode,gain=1):return next(r for r in rs if r['mode']==mode and r['gain']==gain)
    ko=[dict(dato='GBW inferido de ×10 (MHz)',hoja='70 ±15%',original=find(original,'ac',10)['minus3_Hz']*10/1e6,copia=find(adj,'ac',10)['minus3_Hz']*10/1e6),
        dict(dato='−3 dB ×10 (MHz)',hoja='7 ±15%',original=find(original,'ac',10)['minus3_Hz']/1e6,copia=find(adj,'ac',10)['minus3_Hz']/1e6),
        dict(dato='−3 dB seguidor (MHz)',hoja='130; margen100…160',original=find(original,'ac')['minus3_Hz']/1e6,copia=find(adj,'ac')['minus3_Hz']/1e6),
        dict(dato='Pico seguidor (dB)',hoja='≤3 (encargo)',original=find(original,'ac')['peak_db'],copia=find(adj,'ac')['peak_db']),
        dict(dato='Consumo +/− (mA por amplificador)',hoja='2.2 ±15%',original=f'{oldop["supply_plus_A"]*1e3:.6f}/{oldop["supply_minus_A"]*1e3:.6f}',copia=f'{adj[0]["supply_plus_A"]*1e3:.6f}/{adj[0]["supply_minus_A"]*1e3:.6f}'),
        dict(dato='Ruido100k/1MHz (nV/√Hz)',hoja='11 ±10%',original=f'{find(original,"noise")["en100k_nV"]:.6f}/{find(original,"noise")["en1m_nV"]:.6f}',copia=f'{find(adj,"noise")["en100k_nV"]:.6f}/{find(adj,"noise")["en1m_nV"]:.6f}'),
        dict(dato='Ruido corriente +/− (pA/√Hz)',hoja='1',original='No caracterizado por fabricante',copia=f'{gate["measured_current_noise_pA"]:.6f}/{gate["measured_minus_current_noise_pA"]:.6f}'),
        dict(dato='Offset (mV)',hoja='±3 a25°C',original=oldop['out_V']*1e3,copia=adj[0]['out_V']*1e3),
        dict(dato='Ib +/− (µA)',hoja='≤2.5 a25°C',original=f'{oldop["ip_A"]*1e6:.6f}/{oldop["im_A"]*1e6:.6f}',copia=f'{adj[0]["ip_A"]*1e6:.6f}/{adj[0]["im_A"]*1e6:.6f}'),
        dict(dato='Excursión1kΩ a±5V (V)',hoja='≥+3.1/≤−3.1',original=f'{next(r for r in original if r["vin"]==4)["out_V"]:.6f}/{next(r for r in original if r["vin"]==-4)["out_V"]:.6f}',copia=f'{adj[3]["out_V"]:.6f}/{adj[4]["out_V"]:.6f}')]
    ko += [
        dict(dato='Excursión 1 kΩ a ±4.9 V (V)',hoja='mismo margen del encargo',original='No repetido',copia=f'{adj[10]["out_V"]:.6f}/{adj[11]["out_V"]:.6f}'),
        dict(dato='Alimentación recomendada, V totales',hoja='5.5–36; p.4 §5.3',original='Validado a 9.8 y 30 V en K0 histórico',copia='Validado a 9.8/10 V; sin barrido completo'),
        dict(dato='Alimentación absoluta, V totales',hoja='36; p.4 §5.1',original='Sin modelo de daño',copia='9.8 nominal / 10.0 extremo; límite de margen 80%×36'),
        dict(dato='Diferencial absoluto, V',hoja='±10; p.4 §5.1',original='Sin certificación de daño',copia='K6 medido; margen ≤80%×10; saturación National'),
        dict(dato='Corriente de entrada absoluta, mA',hoja='±10; p.4 §5.1',original='Sin certificación de daño',copia='K6 medido; margen ≤50%×10; entrada National'),
        dict(dato='Offset / Ib en temperatura',hoja='±4 mV / ≤3.5 µA a −40…85 °C; p.7 §5.6',original='No validado en temperatura',copia='No validado en temperatura; límites K0 a 25 °C'),
        dict(dato='Estabilidad ganancia 1 / carga capacitiva',hoja='Unidad estable; evaluar aislamiento 50 Ω; pp.23–24',original='Seguidor con 1 kΩ, sin barrido capacitivo',copia='Seguidor con 1 kΩ; carga capacitiva no certificada; sin añadir remedio'),
        dict(dato='Compensación de evaluación',hoja='2 pF feedback y retorno 1 kΩ; pp.24–25',original='No añadido a canal',copia='No añadido a canal; compensación interna C1 ajustada')]
    s.csv_write(OUT/'s9b_k0_comparacion.csv',ko,['dato','hoja','original','copia'])
    history=[json.loads(x) for x in (work/'native_history.jsonl').read_text().splitlines()]
    birth=getattr(work.stat(),'st_birthtime',work.stat().st_ctime)
    wall=time.time()-birth
    accounting=dict(meta,native_attempts=len(history),native_failed_attempts=sum(r['returncode']!=0 for r in history),native_parallel_elapsed_sum_s=sum(r['seconds'] for r in history),wall_since_campaign_directory_s=wall,interrupted_attempts='Own Python23944 and10LTspice interrupted; before final native records; details in journal/console')
    s.write(OUT/'s9b_contabilidad.json',json.dumps(accounting,indent=2))
    summary=f'B: código {meta["returncode"]}; {meta["successful"]}/{meta["logical_cases"]} casos, {meta["simulations"]} ejecuciones nativas de referencia, {meta["seconds"]:.3f} s de la última reanudación registrada (no el total de todas las sesiones históricas). Tiempo desde la creación de la carpeta de campaña, incluyendo pausa/reanudación y comprobación: {wall:.3f} s. Histórico: {len(history)} intentos terminados, {accounting["native_failed_attempts"]} fallidos; los interrumpidos sin registro final se conservan en consola/diario. Diez trabajadores; semilla {meta["seed"]}. Protegidos sin cambios: {not bool(meta["protected_changed"])}. Código de ejecución no equivale a aprobación eléctrica. A no se repitió. K4 se reutiliza porque el driver/pin no cambia.'
    if meta['protected_changed']:
        summary+=' Cambios detectados por el guard de esta reanudación: '+', '.join(meta['protected_changed'])+'. STATE.md fue editado externamente a20:41:07−05:00, añadiendo el punto de retomada de Claude para el5oct; Codex no escribió STATE durante la campaña. En la sesión anterior se había observado también DECISIONS.md a16:21:44−05:00 (C8≤2µs); ese cambio histórico consta en el diario. Se conserva el código1 y las huellas originales, sin convertir este control en un fallo eléctrico ni repetir simulaciones.'
    modeltext='Copia local `comun/lm6172_hoja.lib`, no validada por TI. C1 cambia de 100 a 200 pF para reducir la banda ×10; GPWR pasa de 0.0014 a 0.001913 para ajustar el consumo. No se añaden polos ni se rehace el núcleo. Resistencias internas noiseless y fuente blanca de 11 nV/√Hz. Para corriente, fuentes externas independientes de 0.774425 pA/√Hz se suman en cuadratura al residual de National para obtener aproximadamente 1 pA/√Hz total, comprobado con 100 kΩ noiseless en cada entrada a 10 kHz. RINP/RINM = 27454.902706 Ω; GINP/GINM = 1/R. Offset, Ib, entrada y salida/sujeciones quedan intactos. Orden de nodos: +IN, −IN, V+, V−, OUT. Hoja local TI SNOS792E, pp. 4, 7 y 8; tolerancias del encargo a ±4.9 V y pruebas de excursión a ±5 V. El seguidor queda en el extremo bajo permitido (101 MHz frente a 130 MHz típico). Este ajuste no valida otras tensiones, temperaturas, slew rate ni cargas capacitivas. Sin curva 1/f ni dispersión de GBW, Ib o ruido; MC ±3 mV en serie conserva también el offset nativo de casi +3 mV, con posible sesgo y doble contabilización.'
    differences=[]
    ano=list(csv.DictReader((OUT/'s9_nominal.csv').open()));acns=list(csv.DictReader((OUT/'s9_consumo.csv').open()))
    btot=next(r for r in consum if r['stage']=='TOTAL_CHANNEL');atot=next(r for r in acns if r['stage']=='TOTAL_CHANNEL')
    differences.append(dict(dato='Ruido peor nominal (%div)',A=max(float(r['noise_pct_div']) for r in ano),B=max(r['noise_pct_div'] for r in nominal)))
    differences.append(dict(dato='Offset5mV/div (V)',A=float(ano[0]['offset_uncal_V']),B=nominal[0]['offset_uncal_V']))
    differences.append(dict(dato='Consumo canal (mW simulado)',A=float(atot['power_mW']),B=btot['power_mW']))
    differences.append(dict(dato='Corriente riel+ (mA simulado)',A=float(atot['plus_A'])*1e3,B=btot['plus_A']*1e3))
    differences.append(dict(dato='Corriente por riel según hojas(mA)',A=3.7+4,B=3.7+4*2.2))
    alim=list(csv.DictReader((OUT/'s9_limites_resumen.csv').open()))
    differences.append(dict(dato='DiferencialmáximoU103/U105 (V)',A=max(float(r['differential_V']) for r in alim if r['stage'].startswith(('U103','U105'))),B=max(r['differential_V'] for r in limits if r['stage'].startswith(('U103','U105')))))
    s.csv_write(OUT/'s9b_diferencias.csv',differences,['dato','A','B'])
    modeltext=modeltext.replace('con posible sesgo y doble contabilización','con sesgo y doble contabilización en la versión original')
    correction='Corrección ordenada en la reanudación: SOLO las cuatro cohortes MC OP se repiten para desplazar −2.986 mV el offset efectivo del LM6172. **Conversión de signo del banco:** VOSA IPA IPAR {VOA}, VOSB IPB IPBR {VOB} y VOS IP IPR {VOS} restan el parámetro a IN+. Por eso los parámetros VOA/VOB/VOFA/VOFB se incrementan +2.986 mV: offset efectivo = +2.986006 mV − (draw +2.986 mV). Restar 2.986 mV al parámetro SPICE duplicaría el sesgo, en vez de cancelarlo. No se toca el modelo. El total original es uniforme aproximadamente en [−0.014,+5.986] mV, frente al total corregido [−3,+3] mV (residual del redondeo K0 ≈6 nV). **La distribución corregida cumple el contrato de offset** de SNOS792E p.7; esto no equivale a aprobar C9. Las columnas B_original/B_corregida comparten las demás pruebas, que no se repiten por esta corrección.'
    report='\n\n## Continuación S9-B — resultado vigente de la copia ajustada\n\n'+summary+'\n\n### Modelo del LM6172 ajustado a la hoja\n\n'+modeltext+'\n\n'+table(ko,['dato','hoja','original','copia'])
    report+='\nLa detención de B narrada antes corresponde al modelo original y a la campaña A histórica. Este apartado completa B por el nuevo encargo; no sustituye ni altera resultados de A. Filtro E96 común: RFILT1=2370Ω, RFILT2=1100Ω; B nominal dentro1MHz±10%, sin reoptimización.\n\n'+table(compact,['criterio','A','B_original','B_corregida'])
    report+='\n'+correction+'\n'
    report+='\nC8 vigente: ≤2 µs según ai-context/DECISIONS.md, entrada S9 del4 octubre (decisión de Keneth registrada por Claude durante la campaña). PLAN_SIMULACION_S9.md y el acta histórica mantienen ≤1 µs: se señala esa discrepancia y se conserva la evidencia histórica de A sin reescribir sus CSV. La tabla vigente reevalúa las medidas guardadas de A y B frente a2 µs; los tiempos medidos no cambian.\n'
    report+='\nC1/C2/C3/C5/C9: cuatro escalas emparejadas de las mismas 500 placas; C4 usa las primeras 100 de esas placas. C6/C7/C8 son casos deterministas, no fracciones de fabricación. K6 hereda la saturación/protecciones de National y no certifica límites de daño.\n'
    paired={mc:[r for r in corrected if r['mc']==mc] for mc in sorted({r['mc'] for r in corrected})}
    joint_ok=sum(len(rs)==4 and all(r['position_pass'] for r in rs) for rs in paired.values())
    joint=dict(boards=len(paired),all_four_scales_pass=joint_ok,fraction=joint_ok/len(paired),
               scope='Derived intersection of C9 on the same boards; distinct from the per-scale contractual fractions')
    s.write(OUT/'s9b_c9_conjunto.json',json.dumps(joint,indent=2))
    report+=f'\n**Comprobación conjunta de C9:** {joint_ok}/{len(paired)} de las mismas placas cumplen el recorrido en las cuatro escalas simultáneamente ({100*joint["fraction"]:.1f} %). Las fracciones contractuales por escala pasan, pero esta intersección queda por debajo del 95 %. No se puede afirmar un rendimiento conjunto ≥95 % para todas las escalas de una placa. Evidencia: resultados/s9b_c9_conjunto.json; pendiente de valoración de Claude/Keneth, sin adoptar variante ni remedio.\n'
    sampling=[r for r in arows if r['test']=='K4' and r['RSW']==825]
    report+=f'\nK4 reutilizado de A, seis casos a R_SW=825 Ω: SFDR mínimo {min(r["sfdr_db"] for r in sampling):.6f} dB y residuo no lineal máximo {max(r["residual_rms_LSB"] for r in sampling):.9f} LSB rms. ADC único, f_ADC=52 MHz, muestreo=52 MHz/15=3.466667 MS/s, adquisición=2.5/52 MHz=48.076923 ns y N=1024. Frecuencias coherentes: M=147 (497656.25 Hz) y M=295 (998697.916667 Hz), estados P/Z/R. ADC ideal sin cuantización, jitter ni ruido; R_SW y C_pad=5 pF son hipótesis del banco, no mediciones. No se reejecuta K4.\n'
    report+='\n### K1/K2 nominal B por escala\n\n'+table(nominal,['scale_V_div','minus3_Hz','peak_db','atten_1p73m_db','atten_2p47m_db','gain_dc_signed','gd_min_ns','gd_max_ns','rebound_excess_db','rise_ns','overshoot_pct'])
    report+='\n### K3 B: AFE y ADC\n\n'+table(nominal,['scale_V_div','noise_pin_uV','noise_pct_div','noise_with_adc_low_pct','noise_with_adc_high_pct'])
    report+='\n### Monte Carlo B\n\n'+table(stats,['scale_V_div','metric','N','min','p2p5','p97p5','max'])
    report+='\n### K7: centrado y posición restante\n\nLa compensación del centro y el recorrido de ±4.5 divisiones se contabilizan por separado. Los puntos incluyen la polarización real del núcleo LM6172 a través de las resistencias de ganancia y filtro.\n\n'+table(offset_summary,list(offset_summary[0]))
    report+='\n### K7/C9 — ambas distribuciones OP emparejadas\n\n'+table(offset_comparison,list(offset_comparison[0]))
    report+='\nEstadísticas OP corregidas (extremos e intervalo central 95 %):\n\n'+table(corrected_stats,['scale_V_div','metric','N','min','p2p5','p97p5','max'])
    report+=f'\nRepetición corregida: {corrected_meta["successful"]}/{corrected_meta["logical_cases"]} casos (500 placas × cuatro escalas), {corrected_meta["simulations"]} OP nativos de referencia, código {corrected_meta["returncode"]}; tiempo de esta reanudación {corrected_meta["seconds"]:.3f} s. Auditoría: {corrected_audit["decks"]} decks, cero errores; sólo difieren cuatro fuentes MC y la ruta de la recomendación Newton. Detalle en resultados/s9b_op_corregido.csv y S9/B_hoja/op_corregido/.\n'
    report+=f'\nContabilidad OP corregida: {corrected_accounting["native_attempts"]} intentos nativos registrados, {corrected_accounting["failed_native_attempts"]} intentos fallidos (incluidos tiempos límite y reintentos). No confundirlos con casos eléctricos fallidos ni con los puntos de referencia de los casos terminados. Evidencia: resultados/s9b_op_corregido_contabilidad.json y S9/B_hoja/op_corregido/native_history.jsonl.\n'
    report+='\nAD8038 de A, comprobación algebraica sin simular: offset diferencial propio nominal **0 mV** bajo alimentación simétrica. B1 y B2 son funciones idénticas de IN− e IN+ con sentidos opuestos; no hay fuente VOS fija. Por tanto A no suma ±3 mV a un offset fijo propio de casi +3 mV como B. No se revalida aquí el error por modo común/rieles desiguales ni otros amplificadores. Fuente: Simulation_LTSpice/models/AD8039/AD8038_ltspice.sub, B1/B2 y ramas simétricas; evidencia en resultados/s9b_offset_ad8038_inspeccion.json. A permanece intacta.\n'
    report+='\n### K6 B — límites y recuperación\n\n'+table(limits,list(limits[0]))+'\n'+table(info,list(info[0]))+'\n'+table(rec,['scale_V_div','amplitude_V','recovery_us','bav199_conducts','limitacion'])
    report+='\nBarridos de ±40 V en cinco escalas y ±100 V en POS 1/100 con acoplo DC/AC; fuentes de 4.80/5.00 V en las cuatro combinaciones, paso de 1 mV. Márgenes: diferencial LM ≤80 % de 10 V, corriente de pin ≤50 % de 10 mA y alimentación ≤80 % de 36 V. Los BAV99 se informan separados de la corriente de pin. No se repiten ESD ni ensayos físicos. Cada resultado K6 conserva la limitación de National.\n'
    report+='\n### Diferencias y K8\n\n'+table(differences,['dato','A','B'])+'\n'+table(consum,['stage','plus_A','minus_A','vdda_A','vref_A','dac_A','power_mW'])
    report+=f'\nConsumo de hoja B: OPA810 a 3.7 mA + cuatro LM6172 a 2.2 mA = {3.7+4*2.2:.1f} mA/riel; OPA836 ≈1 mA en 3.3 V, más VMID/DAC. El modelo OPA810 conserva su consumo inferior al de hoja. No incluye relé, MCU ni convertidores.\n'
    report+='\n### Criterios fallidos y dudas\n\n'
    for r in corrected_criteria:
        if r['status']=='FALLA':report+=f'- {r["criterion"]}, {r["scope"]}: {r["pass_count"]}/{r["N"]}; faltan {max(0,(.95 if r["population"] else 1)-r["fraction"])*100:.3f} puntos porcentuales.\n'
    report+='\nNo se elige variante ni remedio. C8 depende de la cola del filtro y la salida de saturación; C9, del offset efectivo y la excursión bajo control DAC. No se simulan cambios. Persisten las contradicciones de la base literal S7b frente a S7c y U105 sin 470 Ω/BAV99, y el disparo de CH2/CH3 fuera de S9. Se conserva el Monte Carlo contractual sin dispersión de GBW/Ib/temperatura. Auditoría externa de Claude pendiente.\n'
    report+='\nReproducción de B desde CH23_entrada: `python k0_s9_b.py`; `python ejecutar_s9_b.py --preflight --resume`; `python ejecutar_s9_b.py --smoke --resume`; `python ejecutar_s9_b.py --resume`; `python verificar_s9_b.py`; `python informar_s9_b.py`. No ejecutar los scripts originales para regenerar A. `S3G4_MODELS` sigue admitiendo otra ubicación de los modelos originales de sólo lectura. Los registros de consola están en TEMP y los registros nativos fuera de los archivos protegidos. Diagnósticos numéricos en `comprobar_numerica_s9_b.py` y `resultados/s9b_numerica*.json`, excluidos de las fracciones.\n'
    report+='\nAntes de informar, reproducir sólo OP corregidas con `python ejecutar_s9_b_op_corregido.py --resume` y auditarlas con `python verificar_s9_b_op_corregido.py`. La columna corregida no contiene nuevas AC/ruido/K6/K2/K8.\n'
    report+='\nEntorno de la retomada: Python 3.12.10 con NumPy y SciPy, ejecutable C:/Users/Keneth/AppData/Local/Programs/Python/Python312/python.exe, y LTspice local. La pausa se retomó con `finalizar_s9_b.py --resume-after-smoke`: auditó/comparó el smoke ya terminado y continuó sólo OP corregidas, auditoría e informe. Los primeros intentos en el entorno restringido fallaron por acceso al Python/SciPy; no fueron fallos de circuito ni lanzaron OP.\n'
    auditpath=work/'s9b_auditoria_codex.json'
    if auditpath.exists():report+='\nAuditoríaCodex: '+json.dumps(json.loads(auditpath.read_text()),ensure_ascii=False)+'\n'
    # Reread shared acta immediately before small appended change; never regenerate A.
    acta=ROOT/'ACTA_S9.md';old=acta.read_text(encoding='utf-8')
    begin='<!-- S9_B_CODEX_BEGIN -->';end='<!-- S9_B_CODEX_END -->'
    block=begin+report+'\n'+end
    if begin in old:
        before,rest=old.split(begin,1)
        if end not in rest:raise RuntimeError('Unclosed B block; preserve shared acta for review')
        _,after=rest.split(end,1)
        new=before+block+after
    else:new=old+'\n\n'+block+'\n'
    s.write(acta,new)
    final='# Respuesta final S9-B\n\nFicheros nuevos o cambiados en S9-B y su retomada: comun/lm6172_hoja.lib; k0_s9_b.py; ejecutar_s9_b.py; ejecutar_s9_b_op_corregido.py; verificar_s9_b.py; verificar_s9_b_op_corregido.py; finalizar_s9_b.py; informar_s9_b.py; comprobar_numerica_s9_b.py; comprobar_op_s9_b.py; S9/B_hoja/; resultados/s9b_*; resultados/s9_tabla_calibracion_B.csv; ACTA_S9.md (sólo bloque B); diarios Codex de S9 y memoria STATE al cierre.\n\n'+report
    final+='\nC8 de la tabla vigente usa2 µs por la decisión de Keneth registrada por Claude el4 octubre en ai-context/DECISIONS.md. El plan y los resultados históricos de A conservan1 µs; sus medidas se reevalúan aquí sin reescribir A.\n'
    final+=f'\nK4 reutilizado de A: seis casos a R_SW=825 Ω, SFDR mínimo {min(r["sfdr_db"] for r in sampling):.6f} dB, residuo máximo {max(r["residual_rms_LSB"] for r in sampling):.9f} LSB rms; f_ADC=52 MHz, muestreo=52 MHz/15, adquisición=48.076923 ns, N=1024, M=147/295. ADC ideal, R_SW/C_pad supuestos. No se repite.\n'
    s.write(ROOT/'RESPUESTA_FINAL_S9_B.md',final)
    print(summary)
    print(table(compact,['criterio','A','B_original','B_corregida']))
if __name__=='__main__':main()
