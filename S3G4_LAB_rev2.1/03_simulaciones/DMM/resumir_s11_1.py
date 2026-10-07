"""Summarize persisted evidence, never promote invalid extrapolation to a result."""
from pathlib import Path
import csv, json, math
from collections import Counter

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'resultados'

def load():
    with (RESULTS/'s11_1_campana_mixta.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for k,v in list(r.items()):
            if v in ('True','False'): r[k]=v=='True'
            elif v:
                try: r[k]=float(v)
                except ValueError: pass
            else: r[k]=None
        last=num(r,'observed_stop_s'); stop=num(r,'stop')
        exact=r.get('raw_complete')
        r['raw_endpoint_exact']=exact
        covered=last is not None and stop is not None and last>=stop-max(1e-9,stop*1e-7)
        r['raw_completion_reclassified']=covered!=exact
        r['raw_complete']=covered
        r['requested_stop_s']=stop
        r['raw_overrun_s']=max(last-stop,0) if last is not None and stop is not None else None
    return rows

def num(r,k):
    v=r.get(k)
    return v if isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) else None

def extreme(rows,keys,which=max):
    vals=[(num(r,k),r,k) for r in rows for k in keys if num(r,k) is not None]
    return which(vals,key=lambda x:x[0]) if vals else (None,None,None)

def fmt(x):
    return 'sin dato' if x is None else f'{x:.6g}'

def csvout(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def main():
    rows=load(); ok=[r for r in rows if r['status']=='ok' and r.get('raw_complete')]
    csvout(RESULTS/'s11_1_campana_auditada.csv',rows)
    summary=json.loads((RESULTS/'s11_1_campana_mixta.json').read_text())
    smoke=json.loads((RESULTS/'s11_1_smoke_mixta.json').read_text())
    energies=[]; charged=[]; pins=[]
    for r in ok:
        if r['macro']!='reduced': continue
        for family,nodes,limit in (('HC4051',('x0','x1','x2','shunt','x5','n2','mux'),.01),('OPA2188',('mux',),.005)):
            for node in nodes:
                excess=num(r,node+'_excess')
                if excess is None: continue
                # Each simplified diode: I=max(deltaV-.5,0)/1ohm.
                peak=max(excess-.5,0)
                pins.append(dict(id=r['id'],p=r['p'],rs=r['rs'],family=family,node=node,
                    rail_excess_V=excess,peak_per_pin_A=peak,criterion_half_limit_A=limit,
                    current_pass_model=peak<=limit,method='derived from exact reduced diode IV; Ron=1ohm, Vf=.5V; either rail peak, no simultaneous sum'))
        pp=[x['peak_per_pin_A'] for x in pins if x['id']==r['id']]
        r['reduced_pin_peak_A']=max(pp,default=0)
    csvout(RESULTS/'s11_1_pines_reducidos.csv',pins)
    for r in rows:
        parts=[k[:-len('_energy_simulated_J')] for k in r if k.endswith('_energy_simulated_J') and num(r,k) is not None]
        for part in parts:
            valid=r.get('extrapolation_valid') is True and r['status']=='ok'
            energies.append(dict(id=r['id'],p=r['p'],rs=r['rs'],status=r['status'],part=part,
                simulated_duration_s=r.get('observed_stop_s'),simulated_J=r[part+'_energy_simulated_J'],
                peak_voltage_V=r.get('observed_'+part+'_v'),peak_power_W=r.get('observed_'+part+'_peak_W'),
                mean_simulated_W=r[part+'_energy_simulated_J']/r['observed_stop_s'] if num(r,'observed_stop_s') else None,
                extrapolated_duration_s=r.get('energy_extrapolated_duration_s'),
                extrapolated_J=r.get(part+'_energy_extrapolated_J') if valid else None,
                total_estimate_J=r.get(part+'_energy_total_estimate_J') if valid else None,
                rejected_extrapolation_J=r.get(part+'_energy_extrapolated_J') if not valid else None,
                extrapolation_valid=valid,basis=r.get('extrapolation_basis')))
        if parts:
            part=max(parts,key=lambda p:r[p+'_energy_simulated_J'])
            charged.append(dict(id=r['id'],p=r['p'],rs=r['rs'],status=r['status'],
                ranking='maximum simulated dissipated energy among recorded external parts',part=part,
                simulated_J=r[part+'_energy_simulated_J'],peak_W=r.get('observed_'+part+'_peak_W'),
                caveat='excludes IC internal dissipation, fuse and DF08S diode dissipation; not margin ranking'))
    csvout(RESULTS/'s11_1_energias.csv',energies)
    csvout(RESULTS/'s11_1_pieza_mas_cargada.csv',charged)
    df=[]
    for grid in (.5,1,2):
        for rs in (100,330):
            group=[r for r in ok if r['p']=='P5' and r['fuse']==1 and r['grid']==grid and r['rs']==rs]
            peak=extreme(group,[f'observed_dbr{i}_peak' for i in range(1,5)])[0]
            i2t=extreme(group,[f'observed_dbr{i}_i2t_8p3ms' for i in range(1,5)])[0]
            full=extreme(group,[f'observed_dbr{i}_i2t' for i in range(1,5)])[0]
            shunt=extreme(group,['rshunt_energy_simulated_J'])[0]
            shuntv=extreme(group,['observed_rshunt_v'])[0]
            df.append(dict(grid_ohm=grid,rs_ohm=rs,completed=len(group),peak_A=peak,
                peak_over_50A=peak/50 if peak is not None else None,i2t_8p3ms_A2s=i2t,
                i2t_over_10p4=i2t/10.4 if i2t is not None else None,i2t_10ms_A2s=full,
                shunt_simulated_J=shunt,shunt_i2t_10ms_A2s=shunt/.1 if shunt is not None else None,
                entry_B_peak_V=shuntv,extrapolated_J=0))
    csvout(RESULTS/'s11_1_df08s.csv',df)
    lines=['# Acta S11.1 — DMM bloque 1', '',
        '7 octubre 2026 · Codex · segunda reanudación, contrato PLAN_SIMULACION_S11_1.md §3b–§3c.', '',
        '**Bloque no aprobado.** La finalización numérica no acredita supervivencia. No se cambiaron piezas ni se simularon remedios.', '',
        '## Ejecución', '',
        f'Preflight P3: 1/1 ok en 38.044 s. Smoke inicial: 14/14 ok en 67.573 s; smoke tras corregir la carga externa apagada: 14/14 ok en 42.689 s; último smoke de estados con resume: {smoke["ok"]}/{smoke["total"]} ok en {smoke["elapsed_s"]:.3f} s, todos conservados por firma. Campaña final con resume: {summary["total"]} casos, {summary["ok"]} ok, {summary["elapsed_s"]:.3f} s de pared, diez trabajadores y límite 300 s/caso. `S3G4_MODELS`, `--resume`; prioridad P3, P2, P4, P5, P1, P6, P7. No se reintentaron los casos fallidos con otros ajustes.', '',
        f'El primer tramo de campaña se detuvo a los aproximadamente 2102 s para corregir Riqother en P4. El segundo se detuvo tras aproximadamente 1006 s adicionales al detectar que P1 diodo/fuga abría el relé a los 3 ms. P1 diodo/fuga ahora mantiene el relé cerrado, con nuevas firmas; los intentos con DUT desconectado quedan excluidos de C5/C6. Se conservan por firma exacta los ok no afectados, y se repiten las pruebas corregidas. Como resume solo conserva ok, cuatro P1 de tensión agotados previamente a 300 s se repiten sin cambiar ajustes. Tiempo aproximado de campaña acumulado: {3108+summary["elapsed_s"]:.3f} s, más preflight y smoke. Código de salida final: {0 if summary["ok"]==summary["total"] else 1}.', '',
        'Revisión raw: 34 P1 ok terminan entre 0.10 y 8.72 µs después del stop solicitado. El lector anterior confundía igualdad exacta con cobertura y daba raw_complete=False. `s11_1_campana_auditada.csv` corrige cobertura (último punto ≥ stop), conserva raw_endpoint_exact y no modifica ninguna medida. Las medidas finales de LTspice corresponden al tiempo solicitado; las energías auditadas integran el intervalo observado real, incluido ese pequeño excedente, identificado por raw_overrun_s. No hubo resimulación por esta corrección.', '',
        '| Prueba | Casos | Estado |', '|---|---:|---|']
    for p in ('P3','P2','P4','P5','P1','P6','P7'):
        group=[r for r in rows if r['p']==p]
        lines.append(f'| {p} | {len(group)} | {dict(Counter(r["status"] for r in group))} |')
    lines+=['', '## P0 y modelos', '',
        'Tabla completa: `resultados/s11_1_p0.csv`. Páginas de los PDF locales, sin descargas.', '',
        '| Pieza | Hoja/página | Límites relevantes |', '|---|---|---|',
        '| PTCTL4MR500SBE | ptctl.pdf p.1 | 50 Ω ±20 %; 600 Vrms/DC; mantenimiento 50 mA a 70 °C; disparo 140 mA a 25 °C; máximo 1 s a 1 A; Imax 1 A |',
        '| SMAJ12CA | SMAJ12CA.pdf pp.2–3 | 400 W no repetitivo, 1 W continuo a TL=75 °C; 12 V standoff; 13.3–14.7 V a 1 mA; 19.9 V a 20.1 A; 5 µA máx a 12 V |',
        '| BAV199 | BAV199.pdf pp.2–3 | 75 V DC/85 V repetitivo; 140 mA; 250 mW; 4 A/1 µs, 1 A/1 ms; fuga 5 nA a 75 V/25 °C |',
        '| DF08S | DF08S.pdf p.2 | 800 V, 1 A, 50 A/8.3 ms media senoide; I²t 10.4 A²s solo t<8.3 ms; VF 1.1 V a 1 A por diodo |',
        '| BSS84 | BSS84.pdf p.2 | VDS −50 V, VGS ±20 V, ID −130 mA, IDM −1.2 A, 300 mW; Ciss/Coss/Crss 24.6/4.7/2.8 pF típicos |',
        '| TQ2SA | C46047.pdf p.6 | Conmutación 125 Vac/220 Vdc, 2 A; aislamiento abierto 1000 Vrms/1 min; suelta máx 4 ms sin diodo |',
        '| OPA2188 | opa2188.pdf pp.4–6 | 40 V alimentación; entrada riel ±0.5 V y ±10 mA; 9.5 pF común, 6 pF diferencial; 415 µA/canal típico |',
        '| TLV2372 | tlv2372.pdf pp.8,11,13 | 16.5 V alimentación; entrada riel ±0.2 V y ±10 mA; 8 pF común; 550 µA/canal a 5 V, 750 µA a 15 V |',
        '| 74HC4051 | 74HC_HCT4051.pdf pp.1,5,9–10 | Límite contractual span 11 V; clamp ±20 mA, canal ±25 mA; Ron 60 Ω típico a 9 V; consumo 16 µA máx a 10 V/25 °C; Yn 5 pF, Z 25 pF |', '',
        'No hay fuga garantizada de TVS/BAV199 a 4 V ni curvas térmicas de la PTC. Faltan MPN y ratings de resistencias, capacitores, fusible y derivador: un encapsulado no certifica energía de pulso. El límite contractual span del 4051 no debe confundirse con su tabla VCC referida a GND; también se informa su rango recomendado de 10 V.', '',
        'Modelo PTC: θ normalizada, dθ/dt=P/Ecrit−θ/τ; G=Rcold·0.14², Ecrit=−G/ln(1−0.14²), τ=50.518759 s. R=Rcold hasta θ=1 y crecimiento exponencial a 1 MΩ entre θ=1 y 1.4. Para 40/60 Ω: Ecrit=39.606707/59.410060 J y G=0.784/1.176 W. θ=1 se llama disparo. El punto 1 A/1 s se reproduce, pero el umbral asintótico de 140 mA, Rcaliente y enfriamiento son supuestos; no se identificó masa térmica física ni temperatura. C4 es orientativo.', '',
        'P2–P7 usan `comun/dmm_reducido_s11_1.inc`: protección y capacidad de entradas, canal seleccionado resistivo y consumo equivalente. Los límites de corriente se evalúan, no recortan la corriente. Ron de los diodos internos=1 Ω es aproximado, sin curva IV publicada; TLV usa 550 µA/canal a 9.8 V como aproximación. Encendido, la suma de resistencias de consumo equivale a 3 mA a 9.8 V, sin doble cuenta. Apagado, el generador elimina la carga residual externa Riqother y mantiene solo las resistencias equivalentes de IC (1.946 mA a 9.8 V); su comportamiento apagado/inversamente alimentado no está validado. P43 se conserva como fuente abstracta con cumplimiento, terminales de sentido TLV en ms/msource; no representa el lazo completo ni sus referencias. BSS84 conserva capacitancias y diodo intrínseco: su hoja no especifica diodos de puerta a rieles y no se inventan. P1 conserva la implementación completa previa del OPA/4051 y BSS84; el lazo P43 anterior también era abstracto, no un macromodelo TLV2372 completo.', '',
        '## Criterios (100 Ω | 330 Ω)', '',
        '| Criterio | R_S = 100 Ω | R_S = 330 Ω |', '|---|---|---|']
    cells={}
    for rs in (100,330):
        rr=[r for r in ok if r['rs']==rs]
        fault=[r for r in rr if r['p'] in ('P2','P3','P4','P5')]
        c2=[r for r in fault if r['p'] in ('P2','P3','P4')]
        c3=[r for r in rr if r['p'] in ('P1','P2','P3','P4','P5','P6')]
        span=extreme(c2,['observed_span_max'])[0]
        span3=extreme(c3,['observed_span_max'])[0]
        inj=extreme(c2,['injp_peak','injn_peak'])[0]
        pin=extreme(c2,['reduced_pin_peak_A'])[0]
        excess=extreme(c3,['mux_excess','x0_excess','x1_excess','x2_excess','n2_excess','x5_excess','shunt_excess'])[0]
        passv=extreme(c3,['observed_pass_vds'])[0]
        passi=extreme(fault,['observed_vsense_peak','pass_peak'])[0]
        leak=[r for r in rr if r['p']=='P1' and r['mode']=='leak']
        errs={}; leak_coverage={}
        for source in (.2e-6,1e-6):
            e=[(abs(num(r,'leak_tvs_final') or 0)+abs(num(r,'leak_bav_final') or 0))/source*1e6 for r in leak if r['source']==source and num(r,'leak_tvs_final') is not None and num(r,'leak_bav_final') is not None]
            errs[source]=max(e) if e else None
            leak_coverage[source]=len(e)
        diode=[r for r in rr if r['p']=='P1' and r['mode']=='diode']
        available=extreme(diode,['terminal_final'],min)[0]
        actualsource=extreme(diode,['pass_final'],min)[0]
        recovery=extreme([r for r in rr if r['p']=='P7'],['x0_recovery_s','n2_recovery_s'])[0]
        trip=extreme([r for r in rr if r['p']=='P3'],['observed_trip_s'])[0]
        cells[rs]=[
            'FALLA: DF08S I²t >5.2 A²s (50 % de 10.4); también supera 50 A. Conmutación de relé a 230 Vac sobre 125 Vac. Márgenes R/C/fusible/derivador no verificables.',
            f'{"FALLA" if span is not None and span>11 or inj is not None and inj>.003 or pin is not None and pin>.003 else "NO CERTIFICADO"}: span {fmt(span)} V; inyección externa pico {fmt(inj)} A y clamp interno por pin máx {fmt(pin)} A vs 0.003 A. No se suman máximos de instantes distintos.',
            f'{"FALLA" if span3 is not None and span3>16.5 or excess is not None and excess>.5 or passi is not None and passi>.065 else "NO CERTIFICADO"}: span máx P1–P6 {fmt(span3)} V; exceso máximo de pines observados {fmt(excess)} V; VDS BSS84 {fmt(passv)} V; corriente de paso en red {fmt(passi)} A (límite continuo C3 0.065 A). Picos internos derivados de IV simplificada en CSV por pin, sin certificar curva de hoja.',
            f'ORIENTATIVO / NO CERTIFICADO: disparo máximo observado {fmt(trip)} s; faltan curva térmica y 10 s simulados/estado caliente validado.',
            f'{"FALLA MODELO" if errs[.2e-6] is not None and errs[.2e-6]>1000 or errs[1e-6] is not None and errs[1e-6]>200 else "NO CERTIFICADO"}: fuga modelada TVS+BAV N2 {fmt(errs[.2e-6])} ppm a 0.2 µA (lím.1000; {leak_coverage[.2e-6]}/6 completos), {fmt(errs[1e-6])} ppm a 1 µA (lím.200; {leak_coverage[1e-6]}/6 completos); sin garantía de fuga a 4 V.',
            f'{"FALLA" if available is not None and available<3.5 else "PASA TENSIÓN EN CASOS COMPLETOS / NO CERTIFICADO" if available is not None else "SIN DATO"}: tensión mínima {fmt(available)} V (lím.3.5 V), corriente fuente mínima {fmt(actualsource)} A, solicitada 1 mA; {len(diode)}/6 completos. Fuente abstracta y corriente no exactamente 1 mA; no garantiza C6 a 1 mA exacto.',
            f'NO CERTIFICADO: recuperación auxiliar máx {fmt(recovery)} s; P7 retira red a 1 s y observa hasta 2 s; no parte del estado tras 10 s ni del enfriamiento de hoja.'
        ]
    for i in range(7): lines.append(f'| S11.1-C{i+1} | {cells[100][i]} | {cells[330][i]} |')
    lines+=['', '## P5 — DF08S por diodo', '',
        'Peor caso entre fase cero/pico, riel nominal/±2 % y los cuatro diodos. Pico e I²t pueden corresponder a casos distintos. Fusible cerrado durante 10 ms; su apertura no se simula. Valores de modelo, ajustado a 1 A: la extrapolación IV a cientos de amperios no está validada. Comparación con máximos de hoja, sin confundirlos con el criterio más estricto del 50 %. No se extrapola energía en este ensayo.', '',
        '| Z red Ω | R_S Ω | Pico A / 50 A | I²t hasta 8.3 ms A²s / 10.4 | I²t 10 ms A²s (informativo) | E derivador simulada J | Pico entrada B V |', '|---:|---:|---:|---:|---:|---:|---:|']
    for r in df:
        lines.append(f'| {r["grid_ohm"]} | {r["rs_ohm"]} | {fmt(r["peak_A"])} / {fmt(r["peak_over_50A"])}× | {fmt(r["i2t_8p3ms_A2s"])} / {fmt(r["i2t_over_10p4"])}× | {fmt(r["i2t_10ms_A2s"])} | {fmt(r["shunt_simulated_J"])} | {fmt(r["entry_B_peak_V"])} |')
    lines+=['', 'I²t del derivador en 10 ms = E_simulada/0.100 Ω; valores en `s11_1_df08s.csv`. Su hoja y rating de pulso no están disponibles, por lo que no se certifica el margen del derivador.', '']
    lines+=['', '| P5 fusible abierto | Pico X5 V | Mínimo X5 V | Pico corriente por Rwarn A |', '|---:|---:|---:|---:|']
    for rs in (100,330):
        rr=[r for r in ok if r['p']=='P5' and r['fuse']==0 and r['rs']==rs]
        v=extreme(rr,['observed_rwarn_v'])[0]
        lines.append(f'| R_S={rs} Ω | {fmt(extreme(rr,["observed_x5_max"])[0])} | {fmt(extreme(rr,["observed_x5_min"],min)[0])} | {fmt(v/1e7 if v is not None else None)} |')
    lines+=['', '## Rieles con DMM apagado', '',
        '| Diodo cuerpo | R_S Ω | Máximo rp V | Mínimo rn V | Máximo span V / 11 V |', '|---|---:|---:|---:|---:|']
    for body in (0,1):
        for rs in (100,330):
            rr=[r for r in ok if r['p']=='P4' and r['rs']==rs and r['body']==body]
            lines.append(f'| {body} | {rs} | {fmt(extreme(rr,["observed_rp_max"])[0])} | {fmt(extreme(rr,["observed_rn_min"],min)[0])} | {fmt(extreme(rr,["observed_span_max"])[0])} / 11 |')
    lines+=['', '## P3 — disparo y energía de TVS', '',
        '| R_S Ω | PTC Ω | Apertura ordenada s | Casos ok | Disparo mín/máx s | E TVS semiciclo máx J | E TVS simulada máx J | E TVS extrapolada válida máx J | Extrapolaciones válidas |', '|---:|---:|---|---:|---|---:|---:|---:|---:|']
    for rs in (100,330):
        for rcold in (40,60):
            for opening in (.02,.1,100):
                rr=[r for r in ok if r['p']=='P3' and r['rs']==rs and r['rcold']==rcold and r['opening']==opening]
                valid=[r for r in rr if r.get('extrapolation_valid') is True]
                lines.append(f'| {rs} | {rcold} | {"nunca" if opening==100 else opening} | {len(rr)} | {fmt(extreme(rr,["observed_trip_s"],min)[0])} / {fmt(extreme(rr,["observed_trip_s"])[0])} | {fmt(extreme(rr,["observed_tvs_semicycle_max_J"])[0])} | {fmt(extreme(rr,["tvs_energy_simulated_J"])[0])} | {fmt(extreme(valid,["tvs_energy_extrapolated_J"])[0])} | {len(valid)}/{len(rr)} |')
    lines+=['', '| R_S Ω | Corriente PTC pico A | Corriente R_S pico A | BAV199 N2 pico por diodo A | TVS pico W |', '|---:|---:|---:|---:|---:|']
    for rs in (100,330):
        rr=[r for r in ok if r['p']=='P3' and r['rs']==rs]
        vr=extreme(rr,['observed_rs_v'])[0]
        lines.append(f'| {rs} | {fmt(extreme(rr,["observed_vptc_peak"])[0])} | {fmt(vr/rs if vr is not None else None)} | {fmt(extreme(rr,["observed_d2p_peak","observed_d2n_peak"])[0])} | {fmt(extreme(rr,["observed_tvs_peak_W"])[0])} |')
    lines+=['', '## Energía simulada y extrapolada', '',
        '`s11_1_energias.csv` separa para cada caso/pieza el tiempo real y la energía integrada, la estimación de los segundos restantes y el total. Una extrapolación rechazada se conserva en columna separada, sin promoverla a resultado. Los extremos de tablas no se suman entre sí: pueden pertenecer a casos diferentes.', '',
        'LTspice corrió como máximo 1 s en red y 10 µs en ESD (paso 1 ns). Desviación pendiente respecto de §3b: el ejecutor no corta dinámicamente al primer θ=1; sigue hasta 1 s, por lo que puede incluir calentamiento/enfriamiento y no debe describirse como tramo terminado exactamente al disparo. Python extrapola desde los últimos cinco ciclos solo si el raw terminó, la variación de potencia es <5 %, deriva de riel <10 mV y, con relé sin abrir, RPTC final ≥0.99 MΩ. No se ejecutó un régimen caliente separado: si esa condición no se alcanza se rechaza la extrapolación, y no hay validación de supervivencia durante 10 s.', '',
        '| Prueba | R_S Ω | Pieza de mayor energía simulada registrada | Energía J |', '|---|---:|---|---:|']
    for p in ('P3','P2','P4','P5','P1','P6','P7'):
        for rs in (100,330):
            cc=[r for r in charged if r['p']==p and r['rs']==rs and r['status']=='ok']
            r=max(cc,key=lambda r:r['simulated_J']) if cc else None
            lines.append(f'| {p} | {rs} | {r["part"] if r else "sin dato"} | {fmt(r["simulated_J"] if r else None)} |')
    lines+=['', 'Esta clasificación no es el menor margen frente a hoja: no hay límites de energía de todas las piezas. El CSV por caso identifica la pieza más cargada entre las registradas; excluye disipación interna de integrados, fusible y diodos DF08S.', '',
        '## Dudas, desviaciones y pendientes', '',
        '- PTC y TVS sin dato garantizado de fuga a 4 V; modelo térmico no físico único. C4 no certificable.',
        '- Relé contractual suelta 3 ms; hoja máximo 4 ms sin diodo. Conmutación a 230 Vac no respaldada por el rating 125 Vac. No se ajustaron estos valores para ocultar la contradicción.',
        '- El modelo reducido no caracteriza latch-up, avería, alimentación inversa, transferencia ni lazo TLV. El total de inyección de las medidas heredadas solo suma BAV externos. `s11_1_pines_reducidos.csv` deduce picos por pin HC/OPA de Vexceso y su IV lineal; estos picos no se suman entre sí ni sustituyen una medida simultánea por riel. No certifica C3 aunque el transitorio termine.',
        '- ESD es la red simple 150 pF/330 Ω del contrato (8 kV con 300 Ω de arco adicionales); no es el generador RLC calibrado sobre 2 Ω de S2b. Los picos orientan y no certifican IEC.',
        '- P7 no satisface la exposición previa de 10 s ni enfriamiento de hoja; sus tiempos auxiliares no son C7.',
        '- No hay elección de R_S ni remedios. Claude revisa aparte el borne A. No se tocaron STATE.md, DECISIONS.md, diseño, modelos del fabricante ni otros canales.', '',
        '## Archivos y trazabilidad', '',
        '`ejecutar_s11_1.py`, `leer_raw_s11_1.py`, `resumir_s11_1.py`, `comun/dmm_bloque1.inc`, `comun/dmm_reducido_s11_1.inc`; decks/logs/JSON en `S11_1/`; CSV/JSON y logs `segundo_*` en `resultados/`; diario `ai-context/journal/2026-10-07-codex-s11-1.md`. Los raw se eliminan tras extraer integrales para limitar disco; `--keep-raw` permite conservarlos. Firmas actuales del deck, include y bibliotecas; no se recuperan resultados legado.'
    ]
    content='\n'.join(lines)+'\n'
    # stdout is suitable for review; persist final acta with native apply_patch.
    print(content)

if __name__=='__main__': main()
