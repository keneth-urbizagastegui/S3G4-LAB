"""Report only recorded evidence; numerical completion is not electrical acceptance."""
from pathlib import Path
import csv, json, math, collections

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'resultados'

def number(r,k):
    try:
        v=float(r.get(k,''))
        return v if math.isfinite(v) else None
    except (ValueError,TypeError): return None

def peak(rows,key):
    pairs=[(number(r,key),r) for r in rows if number(r,key) is not None]
    return max(pairs,key=lambda x:x[0]) if pairs else (None,{})

def fmt(v): return 'sin medida válida' if v is None else f'{v:.9g}'

def main():
    path=RESULTS/'s11_1_campana_full.csv'
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    summary=json.loads(path.with_suffix('.json').read_text())
    with (RESULTS/'s11_1_smoke_full.csv').open(encoding='utf-8-sig',newline='') as f: smoke=list(csv.DictReader(f))
    complete=[r for r in rows if r['status']=='ok']
    energy=[]
    for r in rows:
        for key in r:
            if key.endswith('_energy_simulated_J') and number(r,key) is not None:
                part=key.removesuffix('_energy_simulated_J')
                valid=r.get('extrapolation_valid')=='True' and r['status']=='ok'
                energy.append(dict(id=r['id'],p=r['p'],rs=r['rs'],rcold=r.get('rcold'),part=part,
                    status=r['status'],observed_stop_s=r.get('observed_stop_s'),
                    simulated_J=r[key],extrapolated_J=r.get(part+'_energy_extrapolated_J','') if valid else '',
                    total_J=r.get(part+'_energy_total_estimate_J','') if valid else '',
                    extrapolation_valid=valid))
    ep=RESULTS/'s11_1_energias.csv'
    with ep.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['id','p','rs','rcold','part','status','observed_stop_s','simulated_J','extrapolated_J','total_J','extrapolation_valid']
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(energy)
    lines=['# ACTA S11.1 — DMM, bloque 1', '',
        'Codex, 7 octubre 2026. Campaña de simulación; no se conectó hardware. Estado: **no aceptado / validación incompleta**. Los fallos numéricos no prueban supervivencia ni fallo físico.', '',
        'Contrato: `PLAN_SIMULACION_S11_1.md`, incluido §3b, y `ENCARGO_CODEX_S11_1.md`. Leídos diario anterior, decisiones D1–D8/B2, documento DMM y método/acta S2b. Manda el plan actual frente al documento de diseño y la memoria histórica.', '',
        '## Ejecución y cobertura', '',
        f"Smoke final: {sum(r['status']=='ok' for r in smoke)}/{len(smoke)} casos terminados; ver `resultados/s11_1_smoke_full.json`. Campaña: {summary['total']} casos, {summary['ok']} terminados, {summary['elapsed_s']:.3f} s ({summary['elapsed_s']/60:.2f} min), diez trabajadores, límite {summary['timeout']} s por caso. Código de salida: {0 if summary['total']==summary['ok'] else 1}.", '',
        'Se usó `--resume`: resultados P1 de tensión compatibles y con firma original verificada se conservan. No se reutiliza el resultado eléctrico de P5 a 50 Hz para la red de 60 Hz. Las firmas incluyen código, netlist y modelos. Los intentos anteriores están en `resultados/intentos/` y `s11_1_intentos.jsonl`.', '',
        '| Prueba | ok | timeout | fallo numérico | error |', '|---|---:|---:|---:|---:|']
    for p in ('P3','P2','P4','P5','P1','P6','P7'):
        count=collections.Counter(r['status'] for r in rows if r['p']==p)
        lines.append(f"| {p} | {count['ok']} | {count['timeout']} | {count['numerical_failure']} | {count['error']} |")
    lines+=['','## P0 y páginas', '',
        'Se conserva `resultados/s11_1_p0.csv`. Páginas de los PDF locales (sin descargas):', '',
        '| Pieza | Página | Datos y límites relevantes |','|---|---:|---|',
        '| PTCTL4MR500SBE, ptctl.pdf | 1 | 50 Ω ±20 %; 600 Vrms/DC; 50 mA a 70 °C; disparo 140 mA a 25 °C; ≤1 s a 1 A; Imax 1 A a Vmax. Sin curva R(T), disparo o enfriamiento en pp. 1–3. |',
        '| SMAJ12CA | 2–3 | 400 W de pulso no repetitivo, 1 W continuo a TL=75 °C; VRWM 12 V; VBR 13.3–14.7 V a 1 mA; 19.9 V a 20.1 A; fuga ≤5 µA a 12 V, sin garantía a 4 V. |',
        '| BAV199 | 2–3 | 75 V DC/85 V repetitivo; IF 140 mA; 250 mW; IFSM 4 A/1 µs, 1 A/1 ms, 0.5 A/1 s; fuga ≤5 nA a 75 V/25 °C, sin garantía a 4 V. |',
        '| BSS84 | 2 | VDS 50 V, VGS 20 V, ID 130 mA, IDM 1.2 A, 300 mW en condiciones de montaje de la hoja. |',
        '| DF08S | 2 | 800 V, 1 A; IFSM 50 A en media onda de 8.3 ms; I²t 10.4 A²s para t<8.3 ms; VF≤1.1 V a 1 A por diodo. |',
        '| 74HC4051 | 5–6 | VCC−VEE absoluto 11 V; ISK 20 mA; ISW 25 mA; 100 mW por interruptor; alimentación recomendada 10 V. |',
        '| OPA2188 | 4 | Alimentación absoluta 40 V; entrada VS±0.5 V; corriente de entrada ±10 mA (C3: mitad). |',
        '| TQ2SA, C46047.pdf | 6 | Conmutación 125 Vac/220 Vdc y 2 A; aislamiento de contactos abiertos 1000 Vrms/1 min; suelta ≤4 ms sin diodo, frente a 3 ms del contrato. |',
        '| R, C, fusible, derivador | — | Sin MPN/hojas específicos: no se certifican ratings de tensión, potencia o energía por el formato 1206. |', '',
        '## Modelo de PTC', '',
        'θ es energía térmica normalizada, no temperatura. dθ/dt=P/Ecrit−θ/τ; G=Rcold·0.14², Ecrit=−G/ln(1−0.14²), τ=Ecrit/G. R=Rcold hasta θ=1; después R=Rcold·exp[ln(10⁶/Rcold)·limit((θ−1)/0.4,0,1)]. Disparo: θ=1. Casos Rcold=40 y 60 Ω. Se reproduce el punto 1 A/1 s y un umbral de equilibrio supuesto de 140 mA; la hoja no identifica una masa térmica. La resistencia caliente de 1 MΩ, la transición y la recuperación no están respaldadas por curvas.', '',
        f"Parámetros calculados: Ecrit/Rcold={summary['thermal']['Ecrit_per_ohm']:.12g} J/Ω, G/Rcold={summary['thermal']['G_per_ohm']:.12g} W/Ω, τ={summary['thermal']['tau']:.12g} s. C4 es orientativo incluso con convergencia.", '',
        '## Criterios: R_S lado a lado', '',
        '| Criterio | R_S=100 Ω | R_S=330 Ω |','|---|---|---|']
    for criterion in range(1,8):
        cells=[]
        for rs in ('100','330'):
            sub=[r for r in complete if r['rs']==rs]
            if criterion==1:
                v,_=peak([r for r in sub if r['p']=='P5'],'observed_dbr1_i2t_8p3ms')
                cells.append('No cumple DF08S: '+fmt(v)+' A²s en ≤8.3 ms frente a 5.2 A²s (50 %); resto sin certificar' if v is not None and v>5.2 else 'No validado; hojas de R/C/fusible ausentes y conmutación 230 Vac fuera del TQ2SA')
            elif criterion==2:
                sub=[r for r in rows if r['rs']==rs and r['p'] in ('P2','P3','P4')]
                v,_=peak(sub,'observed_span_max')
                cells.append(('Excursión registrada '+fmt(v)+' V >11 V; ' if v is not None and v>11 else '')+'no validado en exposición completa P2–P4')
            elif criterion==3:
                v,_=peak([r for r in sub if r['p']=='P5'],'observed_span_max')
                cells.append('No cumple: span '+fmt(v)+' V >11 V del mux; otras corrientes/ESD sin validar' if v is not None and v>11 else 'No validado en todos los estados')
            elif criterion==4:
                trip,_=peak([r for r in sub if r['p']=='P3' and float(r['opening'])>=100],'observed_trip_s')
                cells.append('Orientativo; no demuestra 10 s. Disparo: '+fmt(trip)+' s')
            elif criterion==5:
                leak=[r for r in sub if r['p']=='P1' and r['mode']=='leak']
                values=[]
                for source,limit in ((.2e-6,1000),(1e-6,200)):
                    errors=[(abs(number(r,'leak_tvs_final') or 0)+abs(number(r,'leak_bav_final') or 0))/source*1e6 for r in leak if abs(float(r['source'])-source)<1e-15 and number(r,'leak_tvs_final') is not None]
                    values.append(f'{max(errors):.6g} ppm (límite {limit})' if errors else f'sin resultado a {source:g} A')
                cells.append('; '.join(values)+'; fuga a 4 V no garantizada')
            elif criterion==6:
                diode=[r for r in sub if r['p']=='P1' and r['mode']=='diode' and number(r,'terminal_final') is not None]
                v=min((number(r,'terminal_final') for r in diode),default=None)
                current=min((number(r,'pass_final') for r in diode if number(r,'pass_final') is not None),default=None)
                cells.append('mín. '+fmt(v)+' V; corriente '+fmt(current)+' A; '+('≥3.5 V en casos terminados, cobertura por comprobar' if v is not None and v>=3.5 else 'no validado / bajo 3.5 V'))
            else: cells.append('No validado tras 10 s: ensayo auxiliar de 1 s + 1 s, sin estado extrapolado certificado')
        lines.append(f"| C{criterion} | {' | '.join(cells)} |")
    lines+=['','## Energía simulada y extrapolada', '',
        '`resultados/s11_1_energias.csv` separa energía integrada en el raw real, energía extrapolada y total. Para un prefijo abortado, el tiempo observado es el único intervalo de integración: no se le atribuyen 1 s ni 10 s. Las columnas de extrapolación/total quedan vacías si no se cumplen las condiciones de periodicidad.', '',
        'En tramos completos de red se usa la potencia de los últimos cinco ciclos (60 Hz), con comparación de dos y tres ciclos, cambio <5 % y deriva de riel <10 mV. La implementación exige RPTC≥0.99 MΩ para extrapolar un P3 sin apertura. Si la PTC se queda en la región de transición, este método no permite extrapolar. No se sustituye con Rfrío ni con una energía de un ciclo presentada como simulada.', '',
        f"Registros pieza/caso con energía integrada: {len(energy)}; con extrapolación habilitada: {sum(e['extrapolation_valid'] for e in energy)}.", '',
        '| Prueba | R_S | Pieza con mayor energía disipada observada | Energía simulada J | Extrapolada J | Intervalo s | Caso |', '|---|---:|---|---:|---:|---:|---|']
    for p in ('P3','P2','P4','P5','P1','P6','P7'):
        for rs in ('100','330'):
            es=[e for e in energy if e['p']==p and e['rs']==rs and e['status']=='ok']
            e=max(es,key=lambda x:float(x['simulated_J']),default=None)
            lines.append(f"| {p} | {rs} | {e['part'] if e else 'sin intervalo completo'} | {fmt(float(e['simulated_J'])) if e else '—'} | {e['extrapolated_J'] if e and e['extrapolated_J'] else 'no habilitada'} | {e['observed_stop_s'] if e else '—'} | `{e['id'] if e else '—'}` |")
    lines+=['','La pieza de mayor energía no es necesariamente la de menor margen: DF08S es crítico por I²t y el mux por alimentación/pines. No hay rating de energía para todas las piezas que permita ordenar el margen normalizado.', '',
        '## Rieles apagados y disparo', '',
        '| R_S | Diodo de cuerpo | Máximo span observado V | Estado de cobertura |','|---|---|---:|---|']
    for rs in ('100','330'):
        for body in ('0','1'):
            sub=[r for r in rows if r['p']=='P4' and r['rs']==rs and r['body']==body]
            v,r=peak(sub,'observed_span_max')
            lines.append(f"| {rs} | {body} | {fmt(v)} | {sum(x['status']=='ok' for x in sub)}/{len(sub)} completos; prefijos no certifican el máximo de 10 s |")
    for rs in ('100','330'):
        sub=[r for r in rows if r['p']=='P3' and r['rs']==rs and number(r,'observed_trip_s') is not None]
        lines.append(f"\nR_S={rs} Ω: tiempos de disparo observados {', '.join(fmt(number(r,'observed_trip_s'))+' s ('+r['status']+')' for r in sub) if sub else 'no disponibles'}.")
    lines+=['','## Supuestos, diferencias y pendientes', '',
        '- No se corrigió ningún valor de protección para obtener un aprobado. Solo se barre R_S y se aplican los extremos PTC ordenados. Los experimentos de uic, nodeset y regularización de rieles se descartaron; el circuito final conserva la implementación original de los rieles. Las pruebas de modelos parciales son diagnósticas y no sustituyen el modelo completo.',
        '- Transitorios de red: límite 1 s y paso máximo 50 µs; aún hay fallos antes del fin. No se implementó una interrupción dinámica exactamente en θ=1: si un caso termina, puede integrar hasta 1 s aunque haya disparado antes; no se presenta ese tiempo como tiempo hasta disparo. Hace falta resolver convergencia y ejecutar el tramo hasta el disparo y el régimen caliente antes de cerrar §3b.',
        '- P7 ejecuta un diagnóstico de retirada a 1 s y observación hasta 2 s, con referencia a su valor final. No representa el estado térmico/eléctrico tras los 10 s extrapolados; C7 queda sin validar. El enfriamiento real no puede deducirse de la hoja.',
        '- P6 usa la red simple contractual 150 pF/330 Ω, 10 µs totales y paso máximo 1 ns en todo el intervalo. A 8 kV se añade arco de 300 Ω (total 630 Ω), orientativo. No es el generador calibrado de dos ramas de S2b: no se certifica la forma IEC de corriente.',
        '- TVS: avalancha lineal por dos puntos máximos, y fuga lineal 5 µA/12 V. Esta extrapolación de fuga a 4 V es un supuesto, no una garantía de la hoja. BAV199 usa el modelo Nexperia; tampoco hay garantía específica de fuga a 4 V.',
        '- DF08S: ajuste VF=1.1 V a 1 A; extrapolación a cientos de amperios no validada. I²t se contrasta solo hasta 8.3 ms, sin extender la garantía a 10 ms; el fusible no abre en el modelo.',
        '- Modelo OPA2188: transferencia de TI con suministro copiado, entrada física ESD/capacidades añadida al circuito; no caracteriza daño ni comportamiento garantizado sin alimentación. No se interpreta convergencia como seguridad del componente.',
        '- El relé se abre 3 ms después de la orden por contrato; la hoja declara hasta 4 ms y no garantiza conmutación de 230 Vac. Esto queda abierto, sin simular un remedio.',
        '- No se modificaron firmware, PCB, modelos de fabricante, diseño, STATE.md o DECISIONS.md. La prohibición del contrato prevalece sobre el mantenimiento general de STATE.md. Se actualiza el mismo diario pedido por Keneth y se sincroniza el índice local.',
        '- Pendiente: resolver los fallos numéricos del circuito completo, la extrapolación térmica válida y el estado inicial de recuperación; auditar con Claude. El bloque no está aprobado ni cerrado eléctricamente.', '']
    (HERE/'ACTA_S11_1.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(total=summary['total'],ok=summary['ok'],elapsed_s=summary['elapsed_s'],status_counts=dict(collections.Counter(r['status'] for r in rows)),energy_rows=len(energy),valid_extrapolations=sum(e['extrapolation_valid'] for e in energy))))
    for rs in ('100','330'):
        sub=[r for r in complete if r['rs']==rs]
        print('RS',rs,'DF08 I2t8.3ms',peak(sub,'observed_dbr1_i2t_8p3ms')[0],'span',peak(sub,'observed_span_max')[0])

if __name__=='__main__': main()
