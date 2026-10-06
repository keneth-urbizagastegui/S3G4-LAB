"""Reduce native evidence to S9 tables, without substituting models/criteria."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json
import numpy as np
import ejecutar_s9 as s
ROOT=s.ROOT
def table(rows,fields):
    def value(v):
        if isinstance(v,float):return f'{v:.7g}'
        return str(v)
    return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+'\n'.join('| '+' | '.join(value(r.get(k,'')) for k in fields)+' |' for r in rows)+'\n'

def readable(text):
    fixes={'Código0':'Código 0','envoltorioLM6172':'envoltorio LM6172','copiaK3':'copia K3','Hoja±5V':'Hoja ±5 V: ','modeloLM6172':'modelo LM6172','a±5V':'a ±5 V','ruido blanco de hoja no curva1/f':'ruido blanco de hoja sin curva 1/f','offsetpropio3mV delmacro sumado alMC comoS7b':'offset propio del macro sumado al Monte Carlo como S7b (diagnóstico B excluido)','baseS7b frenteaS7c':'base S7b frente a S7c','U105 sin470Ω/BAV99 enbase peseal textoS9':'U105 sin 470 Ω/BAV99 en la base pese al texto S9','soncasos, no fraccionesdeplacas':'son casos, no fracciones de placas','No se eligevariante niremedio':'No se elige variante ni remedio','Todos losdetalles, advertencias yconcurrencia enACTA/diario':'Detalles, advertencias y concurrencia en acta y diario','Muestreo2.5ciclos':'Muestreo de 2.5 ciclos','yP2.5/P97.5':'y P2.5/P97.5','consumo1.70mA':'consumo 1.70 mA','macroseguidor182MHz frente130MHz':'seguidor del modelo: 182 MHz frente a 130 MHz','offsetmax3mV':'offset máximo 3 mV','diferencialabs±10V':'diferencial absoluto ±10 V','entradaabs±10mA':'entrada absoluta ±10 mA','sinGBW':'sin GBW','sin entrelazado':'sin entrelazado'}
    for old,new in fixes.items():text=text.replace(old,new)
    text=text.replace('entradaDC y E5b tambiénAC','sobrecarga continua en las posiciones de acoplamiento DC y AC de E5b')
    for old,new in {'gananciaDC':'ganancia DC','sobreestimaBW':'sobreestima el ancho de banda','yresetADC':'y reset del ADC','validada11.03684nV':'validada a 11.03684 nV','frente2.2mA':'frente a 2.2 mA','ruidoADC':'ruido del ADC','segúnS7b':'según S7b','porSHA256':'por SHA256','requiereCSV':'requiere CSV','registroJSON':'registro JSON','LosCSV':'Los CSV','porID':'por ID'}.items():text=text.replace(old,new)
    return text
def main():
    work=ROOT/'S9/campaign';data=json.loads((work/'s9_checkpoint.json').read_text());meta=json.loads((work/'s9_meta.json').read_text());rows=data['rows'];extras=data['extras'];out=ROOT/'resultados'
    criteria=[]
    def add(n,v,scope,rs,predicate,population=True):
        passed=sum(bool(predicate(r)) for r in rs);size=len(rs);fraction=passed/size if size else 0
        criteria.append(dict(criterion=f'S9-C{n}',variant=v,scope=scope,N=size,pass_count=passed,fraction=fraction,status='PASA' if size and fraction>=(.95 if population else 1.) else 'FALLA',population=population))
    for v in ['A']:
        for ix in [0,3,6,9]:
            ac=[r for r in rows if r['variant']==v and r['ix']==ix and r['test']=='K5AC'];op=[r for r in rows if r['variant']==v and r['ix']==ix and r['test']=='K5OP' and r['mc']>=0]
            add(1,v,f'{s.SCALES[ix]} V/div MC',ac,lambda r:.85e6<=r['minus3_Hz']<=1.15e6)
            add(2,v,f'{s.SCALES[ix]} V/div MC',ac,lambda r:r['peak_db']<=1)
            add(3,v,f'{s.SCALES[ix]} V/div MC',ac,lambda r:r['atten_2p47m_db']>=20)
            add(5,v,f'{s.SCALES[ix]} V/div MC',op,lambda r:abs(r['gain_error_pct'])<=5)
            add(9,v,f'{s.SCALES[ix]} V/div MC',op,lambda r:r['position_pass'])
        for ix in [0,6]:
            rr=[r for r in rows if r['variant']==v and r['ix']==ix and r['test']=='K5NOISE']
            add(4,v,f'{s.SCALES[ix]} V/div MC (100)',rr,lambda r:r['noise_pct_div']<=.5)
        nominal=[r for r in rows if r['variant']==v and r['test']=='K3'];add(4,v,'12 escalas nominales',nominal,lambda r:r['noise_pct_div']<=.5,False)
        sample=[r for r in rows if r['test']=='K4' and r['RSW']==825];add(6,v,'K4 compartido, P/Z/R, dos frecuencias',sample,lambda r:r['sfdr_db']>=60 and r['residual_rms_LSB']<=.5,False)
        prot=[r for r in rows if r['test']=='K6' and r['variant']==v];add(7,v,f'{len(prot)} barridos deterministas, rieles extremos',prot,lambda r:r['protection_pass'],False)
        recover=[r for r in rows if r['test']=='K6REC' and r['variant']==v and not r['bav199_conducts']];add(8,v,'recuperaciones nominales sin BAV199',recover,lambda r:r.get('recovery_us') is not None and r['recovery_us']<=1,False)
    criteria += [dict(criterion=f'S9-C{n}',variant='B',scope='Detenida por K0',N=0,pass_count=0,fraction='',status='NO EVALUADA',population=False) for n in range(1,10)]
    s.csv_write(out/'s9_criterios.csv',criteria,['criterion','variant','scope','N','pass_count','fraction','status','population'])
    nominal=[];nominal_sources=[]
    for v in ['A']:
        for ix in range(12):
            r=dict(next(r for r in rows if r['test']=='K1' and r['variant']==v and r['ix']==ix))
            for test in ['K2','K3']:
                r.update(next(r for r in rows if r['test']==test and r['variant']==v and r['ix']==ix))
            op=next(r for r in rows if r['test']=='K5OP' and r['variant']==v and r['ix']==ix and r['mc']<0)
            for key in ['gain_dc_signed','gain_nominal_signed','gain_error_pct','center_V','offset_uncal_V','position_plus_div','position_minus_div']:r[key]=op[key]
            nominal_sources.append(dict(variant=v,scale_V_div=s.SCALES[ix],K1=next(x['id'] for x in rows if x['test']=='K1' and x['variant']==v and x['ix']==ix),K2=next(x['id'] for x in rows if x['test']=='K2' and x['variant']==v and x['ix']==ix),K3=next(x['id'] for x in rows if x['test']=='K3' and x['variant']==v and x['ix']==ix),K5OP=op['id']))
            r.update(id=f's9_nominal_{v.lower()}_s{ix:02d}',test='NOMINAL_COMBINADO',kind='combined',amplitude_V='')
            nominal.append(r)
        cal=[dict(escala_V_div=r['scale_V_div'],rele=r['POS'],toma=r['tap'],ganancia_medida=r['gain_dc_signed'],ganancia_nominal=r['gain_nominal_signed'],signo=-1) for r in nominal if r['variant']==v]
        s.csv_write(out/f's9_tabla_calibracion_{v}.csv',cal,['escala_V_div','rele','toma','ganancia_medida','ganancia_nominal','signo'])
    s.csv_write(out/'s9_nominal.csv',nominal,s.FIELDS)
    s.csv_write(out/'s9_nominal_sources.csv',nominal_sources,['variant','scale_V_div','K1','K2','K3','K5OP'])
    stats=[]
    for v in ['A']:
        for ix in [0,3,6,9]:
            for metric,test in [('minus3_Hz','K5AC'),('peak_db','K5AC'),('atten_2p47m_db','K5AC'),('gain_dc_signed','K5OP'),('offset_uncal_V','K5OP'),('noise_pct_div','K5NOISE')]:
                rr=[r[metric] for r in rows if r['variant']==v and r['ix']==ix and r['test']==test and r['mc']>=0]
                if not rr:continue
                values=np.array(rr);a,b=np.percentile(values,[2.5,97.5]);stats.append(dict(variant=v,scale_V_div=s.SCALES[ix],metric=metric,N=len(rr),min=float(values.min()),p2p5=float(a),p97p5=float(b),max=float(values.max())))
    s.csv_write(out/'s9_estadisticas.csv',stats,['variant','scale_V_div','metric','N','min','p2p5','p97p5','max'])
    compact=[]
    for n in range(1,10):
        item=dict(criterio=f'S9-C{n}')
        for v in ['A','B']:
            if v=='B':
                item[v]='NO EVALUADA: detenida por K0 (modelo incompatible con hoja)'
                continue
            rr=[r for r in criteria if r['variant']==v and r['criterion']==f'S9-C{n}'];item[v]='; '.join(f'{r["scope"]}: {r["pass_count"]}/{r["N"]} ({100*r["fraction"]:.1f}%)' for r in rr)
            item[v]+=' — '+('PASA' if all(r['status']=='PASA' for r in rr) else 'FALLA')
        compact.append(item)
    criterion_table=table(compact,['criterio','A','B'])
    limits=[]
    for v in ['A']:
        for stage in s.old.STAGES:
            rr=[r for r in extras['limits'] if r['variant']==v and r['stage']==stage]
            field='pin_current_abs_max_A' if v=='B' and stage.startswith(('U103','U105')) else 'current_abs_max_A'
            limits.append(dict(variant=v,stage=stage,differential_V=max(r['differential_abs_max_V'] for r in rr),input_max_mA=1e3*max(max(r['plus_'+field],r['minus_'+field]) for r in rr)))
    s.csv_write(out/'s9_limites_resumen.csv',limits,['variant','stage','differential_V','input_max_mA'])
    consum=extras['consumption']
    # Consumption rows inherit actual case id; annotate variant without guessing model data.
    for r in consum:r['variant']='B' if '_b_' in r['id'] else 'A'
    s.csv_write(out/'s9_consumo.csv',consum,['id','variant','stage','kind','plus_A','minus_A','vdda_A','vref_A','dac_A','power_mW'])
    differences=[]
    for name,field,test in [('Ruido peor nominal (%div)','noise_pct_div','K3'),('Offset nominal 5mV/div (V)','offset_uncal_V','K5OP')]:
        rr={v:[r for r in rows if r['variant']==v and r['test']==test and (r['mc']<0) and (test!='K5OP' or r['ix']==0)] for v in ['A','B']}
        differences.append(dict(dato=name,A=max(r[field] for r in rr['A']),B='Detenida por K0'))
    for name,field in [('Consumo de canal simulado (mW)','power_mW'),('Corriente riel+ simulada (mA)','plus_A')]:
        factor=1e3 if field=='plus_A' else 1
        differences.append(dict(dato=name,A=next(r[field]*factor for r in consum if r['variant']=='A' and r['stage']=='TOTAL_CHANNEL'),B='Detenida por K0'))
    differences.append(dict(dato='Corriente por riel según hojas (mA)',A=3.7+4*1.,B=3.7+4*(4.4/2)))
    differences.append(dict(dato='Diferencial U103/U105 máximo (V)',A=max(r['differential_V'] for r in limits if r['variant']=='A' and r['stage'].startswith(('U103','U105'))),B='Detenida por K0'))
    s.csv_write(out/'s9_diferencias.csv',differences,['dato','A','B'])
    sampling=[r for r in rows if r['test']=='K4'];recovery=[r for r in rows if r['test']=='K6REC'];protection=[r for r in rows if r['test']=='K6']
    extra_info=[]
    for v in ['A']:
        pr=[r for r in protection if r['variant']==v];br=[r for r in extras['bav99'] if r['variant']==v]
        extra_info.append(dict(variant=v,adc_min_V=min(r['adc_min_V'] for r in pr),adc_max_V=max(r['adc_max_V'] for r in pr),mux_low_margin_V=min(r['mux_low_margin_V'] for r in pr),mux_high_margin_V=min(r['mux_high_margin_V'] for r in pr),mux_supply_max_V=max(r['mux_supply_max_V'] for r in pr),bav99_max_mA=1e3*max(r['current_abs_max_A'] for r in br)))
    history=[json.loads(x) for x in (work/'native_history.jsonl').read_text().splitlines()]
    accounting=dict(native_attempts_recorded=len(history),native_failed_attempts=sum(x['returncode']!=0 for x in history),native_parallel_elapsed_sum_s=sum(x['seconds'] for x in history),successful_logical_cases=meta['successful'],reference_native_runs=meta['simulations'],completed_session_elapsed_s=meta['seconds'],interrupted_attempts='Console y logs conservados; procesos interrumpidos antes de devolver registro no están en el contador de intentos terminados.')
    s.write(out/'s9_contabilidad.json',json.dumps(accounting,indent=2))
    summary=f'Código **{meta["returncode"]}**; **{meta["simulations"]} ejecuciones nativas de referencia**, **{meta["successful"]}/{meta["logical_cases"]} casos lógicos**, **{meta["seconds"]:.3f} s** de sesiones finalizadas de campaña (sin huellas iniciales ni sesiones interrumpidas), 10 trabajadores, semilla {s.SEED}. Histórico: {len(history)} intentos terminados registrados, {accounting["native_failed_attempts"]} fallidos de depuración; suma de tiempos de procesos paralelos {accounting["native_parallel_elapsed_sum_s"]:.3f} s, no tiempo de pared. Interrupciones en console/diario. Código 0 significa ejecución completa, no aprobación eléctrica. Cambios protegidos: {meta["protected_changed"]}.\n'
    guard=work/'guard_concurrencia_2026-10-04/s9_meta.json'
    if guard.exists():
        original=json.loads(guard.read_text())
        summary+=f'\nLa ejecución completa original devolvió código {original["returncode"]} tras {original["seconds"]:.3f} s: detectó modificaciones externas de STATE.md y DECISIONS.md, conservadas con huellas antes/después en `S9/campaign/guard_concurrencia_2026-10-04/`. CH1 y modelos permanecieron idénticos. El código actual corresponde a reanudación y revisión de una nueva ventana sin modificar esos archivos; se reutilizan los mismos resultados.\n'
    audit_path=work/'s9_auditoria_codex.json'
    if audit_path.exists():
        audit=json.loads(audit_path.read_text());summary+=f'\nAuditoría Codex: código {audit["returncode"]}, {audit["decks"]} decks y {audit["logical_cases"]} casos verificados; {len(audit["errors"])} errores. Auditoría externa de Claude pendiente.\n'
    report='\n\n## Campaña cerrada\n\n'+summary+'\n'+criterion_table
    report+='\nConcurrencia: las nuevas entradas de memoria sobre S8 (relé, economizador, C_AC, parejas serie/paralelo y orden AC–GND–DC) no se incorporan al modelo S9, cuyo contrato exige S7b literal. Las fracciones describen ese circuito contractual y su reparto de tolerancias; no certifican las nuevas realizaciones físicas de S8. Los seis escalones con fallo inicial por límite de iteraciones terminaron en el único reintento, con la recomendación nominal propia y itl4=1000; sus errores iniciales están en registros e historial.\n'
    report+='\nB se detiene por K0: el modelo antiguo no concuerda en ancho ni consumo con la hoja suministrada. Sus ensayos previos son diagnósticos y quedan fuera de esta campaña. C1/C2/C3/C5/C9: cuatro cohortes de las mismas 500 placas de A, no 2000 placas independientes. C4: primeras 100 placas en dos escalas, nominal en las 12. C6/C7/C8 son fracciones de casos deterministas y no estiman una fracción poblacional. Detalle por escala en `s9_criterios.csv`.\n'
    report+='\n## K1 nominal por escala\n\n'+table(nominal,['variant','scale_V_div','minus3_Hz','peak_db','atten_1p73m_db','atten_2p47m_db','gain_dc_signed','gd_min_ns','gd_max_ns','rebound_excess_db','rise_ns','overshoot_pct','noise_pct_div'])
    report+='\n## Monte Carlo\n\n'+table(stats,['variant','scale_V_div','metric','N','min','p2p5','p97p5','max'])
    noise_fields=['variant','scale_V_div','noise_pin_uV','noise_pct_div','noise_with_adc_low_pct','noise_with_adc_high_pct']
    report+='\n## K3: AFE y ADC\n\nRuido integrado de 1 Hz a 10 MHz. Se suma en cuadratura el ruido independiente del ADC de 0.40 y 0.61 mV rms. Las tres columnas de porcentaje se refieren a una división; C4 se evalúa sólo con el AFE.\n\n'+table(nominal,noise_fields)
    report+='\n## Muestreo, un ADC\n\n'+f'f_ADC=52MHz, f_s=52MHz/15={s.FS:.12g}Sa/s; t_s=2.5/52MHz={s.TS*1e9:.12g}ns; período={s.PERIOD*1e9:.12g}ns. N=1024, M impar más cercano a0.5/1MHz. R_SW inferida de S6, no medida: (2.5/60MHz)/(5pF×ln(2¹³))−100Ω={((2.5/60e6)/(5e-12*np.log(2**13))-100):.12g}Ω. C_pad5pF supuesto; C_S5pF, resetideal0/2.5V, flancos20ps. Se descartan256 muestras; se mide el límite izquierdo de cierre, sin mezclar reset. Referencia sin carga de la misma S4 en paralelo. LS error=a*v[n]+b*v[n−1]+c; sin entrelazado. FFT rectangular, sin cuantización/jitter/ruidoADC.\n\n'
    report+=table(sampling,['state','RSW','freq_Hz','M','sfdr_db','reference_sfdr_db','residual_rms_LSB','error_max_LSB','error_rms_LSB','gain_delta_db','phase_delta_deg','fundamental_pp_V','closing_time_error_ps'])
    report+='\nFondo de escala heredado de S6/S7: ±4 divisiones, 0.25 V/div; referencia sin carga de 2 Vpp centrada en 1.25 V. Es distinto del rango eléctrico total ADC de 0…2.5 V. Fuente: PLAN_SIMULACION_S3.md, Las 12 escalas; PLAN_SIMULACION_S7.md, J7; auditoría S6, amplitud 1 V. La amplitud y el centro de la fuente se calculan con AC y OP de la etapa real.\n'
    report+=f'\nLSB heredado de S6: 2.5/4096 = {s.old.a6.LSB*1e3:.12g} mV (12 bits). Medio LSB = {s.old.a6.LSB*1e3/2:.12g} mV; el factor ln(2¹³) corresponde al asentamiento a medio LSB, no a un ADC de 13 bits.\n'
    report+='\n## Protecciones en extremos\n\n'+table(limits,['variant','stage','differential_V','input_max_mA'])+'\n'+table(extra_info,['variant','adc_min_V','adc_max_V','mux_low_margin_V','mux_high_margin_V','mux_supply_max_V','bav99_max_mA'])
    corners=sorted({(r['rail_plus_set_V'],r['rail_minus_set_V']) for r in protection})
    report+=f'\nRieles fuente (positivo, magnitud del negativo), en V: {corners}. Barridos continuos de cero hasta ±40 V y ±100 V, con paso de 1 mV y posterior fusión de polaridades; E5b cubre las posiciones de acoplamiento DC y AC. Las sondas de corriente usan fuentes de 0 V. Los diagnósticos B miden la corriente real del pin a través de RINA/RINB, separada de la corriente de los BAV99 externos. No se ejecutaron ESD, apagado ni pruebas físicas.\n'
    report+='\n## Recuperación\n\n'+table(recovery,['variant','scale_V_div','amplitude_V','recovery_us','bav199_conducts','bav199_forward_max_V'])
    failures=[r for r in criteria if r['status']=='FALLA']
    report+='\n## Distancia a los criterios incumplidos\n\n'
    for r in failures:
        target=95 if r['population'] else 100
        report+=f'- {r["criterion"]}, {r["scope"]}: {100*r["fraction"]:.3f} %, faltan {max(0,target-100*r["fraction"]):.3f} puntos porcentuales para {target} % ({"placas" if r["population"] else "casos deterministas"}). '
        if r['criterion']=='S9-C8':
            values=[x['recovery_us'] for x in recovery if x.get('recovery_us') is not None and not x['bav199_conducts']]
            report+=f'Recuperación medida {min(values):.6g}…{max(values):.6g} µs frente a 1 µs. El resultado se movería al acortar la cola del filtro y/o la salida de saturación; no se cambia el ancho contractual ni se simula un remedio.'
        elif r['criterion']=='S9-C9':
            scale=float(r['scope'].split()[0]);values=[x for x in rows if x['test']=='K5OP' and x['mc']>=0 and x['scale_V_div']==scale]
            pp=min(x['position_plus_div'] for x in values);pn=min(x['position_minus_div'] for x in values)
            report+=f'Posición mínima positiva/negativa: {pp:.6g}/{pn:.6g} div; faltan {max(0,4.5-pp):.6g}/{max(0,4.5-pn):.6g} div frente a ±4.5. El resultado depende del offset efectivo y de la excursión disponible bajo el control DAC. Reducir ese offset o aumentar la posición utilizable movería el criterio; no se elige ni simula un cambio.'
        else:report+='Valores y extremos medidos en las tablas nominales, de Monte Carlo y de protecciones; no se simulan remedios.'
        report+='\n'
    report+='\n## Diferencias y consumo\n\n'+table(differences,['dato','A','B'])+'\n'+table(consum,['variant','stage','plus_A','minus_A','vdda_A','vref_A','dac_A','power_mW'])
    sheet=next(r for r in differences if r['dato']=='Corriente por riel según hojas (mA)')
    report+=f'\nConsumo por hojas: OPA810 3.7 mA, AD8039 1 mA/amplificador (revisión R3); LM6172 4.4 mA/dual a ±5 V, {4.4/2:.6g} mA/amplificador (p.7). Por riel: A {sheet["A"]:.6g} mA, B {sheet["B"]:.6g} mA; OPA836 ≈1 mA a 3.3 V, más VMID/DAC. Los modelos dan menos corriente que las hojas; no se corrige G.3 ni se certifica autonomía. No incluye relé, MCU, pérdidas de convertidores ni cargas de otros canales; las cargas 42/39 mA de RAILS heredadas no se suman al canal. B sólo tiene estimación por hoja, tras su detención K0.\n'
    report+='\nLas corrientes de las fuentes se conservan con signo; para consumo del riel negativo se usa su magnitud. La potencia se calcula con la tensión y la corriente firmadas de cada fuente.\n'
    report+='\n## Método y reproducibilidad\n\nUniformes independientes por componente segúnS7b §2; resistencias1%, divisor0.1%, C0G5%, pistas1/3pF50%, rieles2% independientes, VREF0.2%; fuentes de offset OPA810715µV/AD8039 yLM6172 3mV/OPA836400µV. Se conserva la realización física emparejada al cambiar escala/variante. Resistores del filtro usan el mismo factor, reescalado del nominalCH1 al E96 elegido. Componentes completos en `s9_mc_components.csv`. No se dispersan GBW/Ib/temperatura ni ruido intrínseco. EntradaBNC fuenteideal0Ω para ruido, integral1Hz…10MHz en pin. Se informa AFE y cuadratura con0.40/0.61mVrms delADC.\n\nGananciaDC se mide con `.op` independientes −0.01/0/+0.01div, DAC1.25V. Para posición, entrada0, DAC0.2/1.25/2.3V más1.24V para pendiente local sin recorte. Los extremos reales incluyen saturación; centroADC1.25V, ±4.5div requiere0.125…2.375V. Nunca se usa barridoDC en MC. Tiempo límite60s porOP,120sAC/ruido,600sprotecciones,900stransitorio, un reintento por caso. `.loadbias` sólo recomienda condiciones iniciales, se resuelve nuevamente el circuito; fallback deMC0S7b, conservado sin cambios. Reintento transitorio aumenta itl4, sin relajar explícitamente tolerancias ni cambiar estímulo. Advertencias nativas e intentos fallidos quedan registrados. Fuentes y modelos se protegen porSHA256; artefactos de ensayo previos por tamaño/mtime; logs/raw/db se excluyen, según contrato.\n\nReejecución: `python ejecutar_s9.py --preflight --optimize`; `python ejecutar_s9.py --smoke`; `python ejecutar_s9.py`; `python ejecutar_s9.py --resume`; `python informar_s9.py`. `S3G4_MODELS` admite ruta alternativa de sólo lectura. Diez trabajadores desde preflight. Resume requiereCSV completo, columnas fijadas y registroJSON; no infiere éxito sólo de existencia de log. LosCSV se ordenan porID y columnas declaradas.\n'
    # Keep the pre-campaign K0 extraction and contradictions; replace only own generated tail.
    report=report.split('\n## Método y reproducibilidad')[0]+f'''
## Método y reproducibilidad

LTspice 26.0.2, modelos locales, diez trabajadores. El reparto S7b §2 conserva uniformes independientes por componente: resistencias ±1 % (divisor ±0.1 %), C0G ±5 %, pistas de 1/3 pF ±50 %, rieles ±2 % independientes y VREF ±0.2 %. Offsets en serie con IN+: OPA810 ±715 µV, AD8039 ±3 mV y OPA836 ±400 µV. LM6172 ±3 mV sólo en los diagnósticos B previos. El offset propio de cada modelo permanece. No se dispersan GBW, polarización, temperatura ni ruido intrínseco.

La realización física se conserva al cambiar escala. Los resistores del filtro reutilizan el mismo factor de tolerancia, reescalado al E96 elegido. Componentes y factores en `s9_mc_components.csv`. K3 pone la BNC a masa con fuente ideal de 0 Ω e integra el ruido en el pin de 1 Hz a 10 MHz. El ruido ADC de 0.40/0.61 mV rms se añade en cuadratura.

Ganancia DC: tres puntos `.op` independientes, entrada −0.01/0/+0.01 división, DAC a 1.25 V. Posición: entrada cero, DAC a 0.2/2.3 V y 1.24 V para medir la pendiente local junto al punto de 1.25 V. Son seis puntos por caso. Los extremos reales incluyen saturación. Centro ADC 1.25 V; ±4.5 divisiones exige {1.25-4.5*.25:.12g}…{1.25+4.5*.25:.12g} V. La continua Monte Carlo no usa `.dc`.

Límites de tiempo: 60 s por OP, 120 s en AC/ruido, 600 s en protecciones y 900 s en transitorios; un reintento por caso. `.loadbias` recomienda condiciones iniciales y Newton resuelve de nuevo el circuito. Se usa la solución propia de placa/escala cuando existe; las recomendaciones S7b y su permutación de rama están documentadas arriba. El reintento A aumenta itl4 y usa su bias nominal propio, conservando estímulo y tolerancias. Los ensayos numéricos B permanecen como diagnóstico histórico.

CSV con columnas fijas y orden por ID; JSON durables por caso. `--resume` exige CSV completo, cabecera declarada y registro JSON. La tabla `s9_nominal.csv` se identifica como agregado, con los cuatro casos fuente por escala en `s9_nominal_sources.csv`. Calibración A usa ganancia DC con signo; B tiene CSV vacío y nota de no evaluación.

Fuentes/modelos protegidos por SHA256; artefactos previos por tamaño/mtime. Logs, raw, bases de datos y bytecode quedan fuera del guard. La concurrencia externa se conserva con huellas y metadatos originales; no se editan STATE ni DECISIONS. El auditor indexa los decks una sola vez y comprueba los seis estados OP, parámetros Monte Carlo, nombres de medidas, extremos de protección, fuente coherente, un ADC, apertura y cabeceras.

Reproducción desde CH23_entrada: `python preparar_s9.py`; `python k0_s9.py`; `python ejecutar_s9.py --preflight --optimize`; `python ejecutar_s9.py --smoke`; `python ejecutar_s9.py`; `python verificar_s9.py`; `python informar_s9.py`. Reanudación: `python ejecutar_s9.py --resume`. `S3G4_MODELS` admite otra ruta de la biblioteca local de sólo lectura. B se filtra por su resultado K0.
'''
    acta=(ROOT/'ACTA_S9.md').read_text();acta=acta.split('\n\n## Campaña cerrada')[0]
    acta=acta.replace('Documento abierto durante K0; resultados de campaña pendientes.','Campaña A cerrada; B detenida por K0.').replace('Pendientes de cierre tras preflight, smoke y campaña.','Resultados finales en la sección Campaña cerrada. Registros K0/preflight y diagnósticos históricos conservados en S9.')
    report=readable(report)
    s.write(ROOT/'ACTA_S9.md',acta+report)
    s.write(out/'s9_resumen.md',summary+'\n'+criterion_table)
    final='# Respuesta final — S9\n\nFicheros: `comun/ch23_comun_s9.inc`, envoltorioLM6172 y copia de ruido; `ejecutar_s9.py`, `preparar_s9.py`, `k0_s9.py`, `informar_s9.py`; decks/registros en `S9/`; `resultados/s9_*.csv`, calibraciónA/B, `ACTA_S9.md` y diario `ai-context/journal/2026-10-04-codex-s9.md`.\n\n'+summary+'\nE96: '+str(meta['filters'])+'; B no necesita reoptimización. K0: patillaje correcto, ruido nativo incompatible con hoja; copiaK3 validada11.03684nV/√Hz. Hoja±5V11nV/√Hz/1pA/√Hz, offsetmax3mV, diferencialabs±10V, entradaabs±10mA; macroseguidor182MHz frente130MHz y consumo1.70mA frente2.2mA/amplificador. Limitación predictiva deB explícita.\n\n'+criterion_table
    final+='\nK1 por escala (gananciaDC con signo):\n\n'+table(nominal,['variant','scale_V_div','minus3_Hz','peak_db','atten_1p73m_db','atten_2p47m_db','gain_dc_signed'])
    final+='\nMonte Carlo, mínimo/máximo yP2.5/P97.5:\n\n'+table(stats,['variant','scale_V_div','metric','N','min','p2p5','p97p5','max'])
    final+='\nMuestreo2.5ciclos:\n\n'+table(sampling,['state','RSW','freq_Hz','sfdr_db','residual_rms_LSB','error_max_LSB'])
    final+='\nK3: AFE y suma en cuadratura con ADC de 0.40/0.61 mV rms; porcentajes de división:\n\n'+table(nominal,noise_fields)
    final+='\nProtecciones en extremos:\n\n'+table(limits,['variant','stage','differential_V','input_max_mA'])+'\n'+table(extra_info,['variant','adc_min_V','adc_max_V','mux_supply_max_V','bav99_max_mA'])
    final+='\nConsumo y diferencias:\n\n'+table(differences,['dato','A','B'])
    eligible=[r['recovery_us'] for r in recovery if r.get('recovery_us') is not None and not r['bav199_conducts']]
    final+=f'\nC8: {min(eligible):.7g}…{max(eligible):.7g} µs frente a 1 µs; exceso de {min(eligible)-1:.7g}…{max(eligible)-1:.7g} µs. Acortar la cola del filtro o la salida de saturación movería el resultado; no se simularon remedios. Rieles fuente de K6, en V: {corners}.\n'
    final+='\nCriterios incumplidos: '+('; '.join(f'{r["criterion"]} {r["scope"]}: faltan {max(0,(95 if r["population"] else 100)-100*r["fraction"]):.3f} puntos porcentuales hasta {95 if r["population"] else 100} %' for r in failures) or 'ninguno')+'. Valores, distancia y dependencias sin simular remedios en ACTA_S9.md.\n'
    final+='\nDudas: modeloLM6172 antiguo sobreestimaBW y subestima consumo a±5V; ruido blanco de hoja no curva1/f; offsetpropio3mV delmacro sumado alMC comoS7b; baseS7b frenteaS7c; U105 sin470Ω/BAV99 enbase peseal textoS9; GBW/Ib/temperatura no dispersados; R_SW yresetADC supuestos. C6/C7/C8 soncasos, no fraccionesdeplacas. No se eligevariante niremedio. Todos losdetalles, advertencias yconcurrencia enACTA/diario.\n'
    final=final.replace('calibraciónA/B','calibración A; B no evaluada').replace('; B no necesita reoptimización.','; el preflight B usó los mismos valores, pero la campaña B se detiene por K0.').replace('Limitación predictiva deB explícita.','B detenida por la condición del punto 3 del encargo; no se califica su rendimiento. Los resultados B anteriores se conservan sólo como diagnóstico.')
    prefix='# Respuesta final — S9\n\nFicheros creados: `comun/ch23_comun_s9.inc`, `comun/lm6172_s9_ruido_hoja.lib`, `comun/lm6172_s9_sin_ruido_interno.lib`; `ejecutar_s9.py`, `preparar_s9.py`, `k0_s9.py`, `informar_s9.py`, `verificar_s9.py`; decks y registros en `S9/`; CSV/JSON en `resultados/`, calibración A y CSV B vacío con nota de no evaluación; `ACTA_S9.md` y `ai-context/journal/2026-10-04-codex-s9.md`.\n\n'
    prefix+=summary+f'\nFiltro A: RFILT1 = {meta["filters"]["A"][0]:.6g} Ω, RFILT2 = {meta["filters"]["A"][1]:.6g} Ω, E96. El preflight B usó los mismos valores; la campaña B se detuvo en K0.\n\n'
    prefix+='K0: orden +IN −IN V+ V− OUT confirmado en `LM6172/NS`. Hoja TI SNOS792E, pp.4/7/8: alimentación recomendada 5.5–36 V, diferencial absoluto ±10 V, entrada absoluta ±10 mA, offset máximo 3 mV, polarización máxima 2.5 µA a 25 °C; a ±5 V, salida típica +3.4/−3.3 V con 1 kΩ, ruido 11 nV/√Hz y 1 pA/√Hz, consumo típico 2.2 mA/amplificador. El modelo a ±4.9 V da offset 2.986 mV, polarización 1.219/1.200 µA, seguidor 181.984 MHz frente a 130 MHz de la hoja y consumo 1.698 mA/amplificador. ×10: 9.9971, −3 dB en 15.263 MHz. El ruido nativo de 6.587/51.496 nV/√Hz a 100 kHz/1 MHz no representa el ruido de entrada de la hoja; la copia propia blanca valida 11.03684 nV/√Hz en ambos puntos. Por el punto 3 del encargo, B queda detenida: sus pruebas previas son diagnóstico, excluido de las fracciones. Detalles de condiciones, máximos, estabilidad y margen en ACTA_S9.md.\n\n'
    final=prefix+criterion_table+final.split(criterion_table,1)[1]
    s.csv_write(out/'s9_tabla_calibracion_B.csv',[],['escala_V_div','rele','toma','ganancia_medida','ganancia_nominal','signo'])
    s.write(out/'s9_tabla_calibracion_B_NO_EVALUADA.md','B detenida por K0. CSV sin filas: no hay calibración aprobada ni campaña B.\n')
    s.write(ROOT/'RESPUESTA_FINAL_S9.md',readable(final))
    print(json.dumps(dict(criterios=compact,diferencias=differences,meta=meta),ensure_ascii=False))
if __name__=='__main__':main()
