"""Summarize S13 CSVs without changing preceding campaigns or design files."""
import csv,json,math
from pathlib import Path
from collections import defaultdict,Counter
HERE=Path(__file__).resolve().parent;R=HERE/'resultados'
def read(name):
 with (R/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def number(r,k,default=float('nan')):
 try:return float(r[k])
 except (ValueError,KeyError,TypeError):return default
def mx(rows,k):return max((number(r,k) for r in rows if math.isfinite(number(r,k))),default=float('nan'))
def mn(rows,k):return min((number(r,k) for r in rows if math.isfinite(number(r,k))),default=float('nan'))
def main():
 rows=read('s13_campaign.csv');good=[r for r in rows if r['status']=='ok'];groups=defaultdict(list)
 for r in good:groups[r['kind']].append(r)
 smoke=json.loads((R/'s13_smoke.json').read_text());campaign=json.loads((R/'s13_campaign.json').read_text())
 comp=groups['compliance'];phase=groups['phase'];starts=groups['startup'];thermal=groups['thermal'];esd=groups['esd'];fault=groups['fault60'];cont=groups['continuity'];leak=groups['leak'];ext=groups['external'];diode=groups['diode']
 # Compliance is the voltage retaining 99% of that plate's calibrated
 # low-voltage current. Separately report initial calibration error.
 import sys,numpy as np
 sys.path.insert(0,str(HERE/'estudio_bloque3/scripts'));import rawlt
 calibrated=[]
 for r in comp:
  _,d=rawlt.read(str(HERE/'S13'/(r['id']+'.raw')));vb=np.real(d['V(bor)']);ii=np.real(d['I(Vdut)'])+vb/10.01e6;i0=float(ii[0]);valid=ii>=.99*i0
  cv=float(vb[valid].max()) if np.any(valid) else 0.;vx=i0*(2000*10.01e6/(2000+10.01e6));margin=cv-vx
  calibrated.append(dict(id=r['id'],initial_current_A=i0,initial_error_pct=number(r,'initial_error_pct'),compliance_calibrated_V=cv,fs_actual_V=vx,margin_calibrated_V=margin,pass_margin=margin>=.3,force_ron_ohm=number(r,'force_ron_ohm')))
  r['margin_V']=str(margin)
 deriv=[]
 for k in range(5):
  rs=[r for r in thermal if int(r['k'])==k];ref=next((number(r,'current_A') for r in rs if int(r['temp'])==23),float('nan'))
  deriv.append(max((abs(number(r,'current_A')/ref-1)*1e6 for r in rs),default=float('nan')))
 lg=defaultdict(list)
 for r in leak:lg[(r['k'],r['lf23'],r['lb23'])].append(r)
 leaks=[]
 for key,rs in lg.items():
  ref=next((number(r,'current_A') for r in rs if int(r['temp'])==23),float('nan'));vref=next((number(r,'borne_final_V') for r in rs if int(r['temp'])==23),float('nan'));fs=2e6 if int(key[0])==3 else 20e6;pct=.002 if fs==2e6 else .01
  drift=max((abs(number(r,'current_A')/ref-1) for r in rs),default=float('nan'));allow=.25*(pct-.0006)
  # Supplemental inverse-divider amplification, after calibration at 23 C.
  rex=[number(r,'borne_final_V')/(ref-number(r,'borne_final_V')/10.01e6) for r in rs]
  amplified=max((abs(x/fs-1) for x in rex),default=float('nan'))
  leaks.append(dict(k=int(key[0]),lf23_nA=float(key[1])*1e9,lb23_nA=float(key[2])*1e9,current_drift_ppm=drift*1e6,allow_ppm=allow*1e6,ratio_pct=100*drift/allow,resistance_drift_pct=amplified*100,pass_current=drift<=allow,pass_resistance=amplified<=allow))
 import ejecutar_s11_4 as s4
 s4.writecsv(R/'s13_compliance_summary.csv',calibrated)
 measnotes=[]
 for r in rows:
  for line in (HERE/'S13'/(r['id']+'.log')).read_text(errors='replace').splitlines():
   if "FAIL'ed" in line:measnotes.append(dict(id=r['id'],note=line,classification='measurement_endpoint_rounding_RAW_complete'))
 if measnotes:s4.writecsv(R/'s13_measurement_notes.csv',measnotes)
 steady=[]
 for r in fault:
  d=s4.prev.raw(HERE/'S13'/(r['id']+'.raw'));t=np.abs(d['time']);mask=t>=t[-1]-5/60;tt=t[mask]
  def v(node):return np.asarray(d['v('+node+')'])[mask]
  def i(part):return np.asarray(d['i('+part+')'])[mask]
  def avg(y):return float(np.trapezoid(y,tt)/(tt[-1]-tt[0]))
  steady.append(dict(id=r['id'],window_start_s=float(tt[0]),d2p_continuous_peak_A=float(np.abs(i('d2p')).max()),d2n_continuous_peak_A=float(np.abs(i('d2n')).max()),tvs_continuous_avg_W=avg(v('n1')*i('btvs')),rs_continuous_avg_W=avg((v('n1')-v('n2'))**2/2700),dzp_continuous_avg_W=avg(-v('rp')*i('dzp')),dzn_continuous_avg_W=avg(v('rn')*i('dzn'))))
 s4.writecsv(R/'s13_c1_steady.csv',steady)
 s4.writecsv(R/'s13_leak_summary.csv',leaks)
 inl=read('s13_inl.csv');lines=[]
 for fs in sorted({number(r,'range_ohm') for r in inl}):
  rr=[r for r in inl if number(r,'range_ohm')==fs]
  vals={r['level']:number(r,'worst_pct') for r in rr};lines.append(f'| {fs:g} | {vals["typical"]:.2f} % | {vals["guaranteed"]:.2f} % | {vals["calibrated_proxy"]:.2f} % |')
 fail=[r for r in rows if r['status']!='ok'];s4.writecsv(R/'s13_errors.csv',fail) if fail else None
 npass=sum(number(r,'margin_V')>=.3 for r in comp);ical=sum(abs(number(r,'initial_error_pct'))<=1 for r in comp)
 pmmin=mn(phase,'pm_deg');start_ratio=max((number(r,'settle_s')/number(r,'limit_s') for r in starts),default=float('nan'))
 r1p=max((mx(fault,f'r1_{i}_Pavg_W') for i in (1,2,3)));r1v=max((mx(fault,f'r1_{i}_vpeak_V') for i in (1,2,3)))
 tvsp=mx(fault,'tvs_P_period_W');
 # Inherited audit key names vary by stimulus; include exact available data.
 stresskeys=sorted({k for r in fault+esd for k in r if any(x in k.lower() for x in ('tvs','rs_','zener','dzp','dzn','d2p','d2n','span'))})
 stress={k:mx(fault,k) for k in stresskeys if math.isfinite(mx(fault,k))}
 (R/'s13_stress_summary.json').write_text(json.dumps(stress,indent=2),encoding='utf-8')
 detection=[]
 p34_threshold=math.floor(min(abs(number(r,'x2_out_V'))/100e-6 for r in ext if abs(number(r,'voltage'))<=.02 and number(r,'gain')>1)-3-.5)
 for r in ext:
  signal=abs(number(r,'x2_out_V'))/100e-6
  applicable=number(r,'gain')>1 or abs(number(r,'voltage'))>=5
  detected=signal-3-.5>=p34_threshold if applicable else None
  detection.append(dict(voltage_V=number(r,'voltage'),gain=number(r,'gain'),x0_out_V=number(r,'x0_out_V'),x2_out_V=number(r,'x2_out_V'),counts=signal,threshold_counts=p34_threshold,detection_applicable=applicable,detected_noise3=detected))
 s4.writecsv(R/'s13_p34_summary.csv',detection)
 summary=dict(unique_cases=len(rows),completed=len(good),failed=len(fail),by_kind=dict(Counter(r['kind'] for r in rows)),wall_s=smoke['elapsed_s']+campaign['elapsed_s'],compliance_pass=npass,compliance_n=len(comp),calibration_pass=ical,pm_min_deg=pmmin,start_limit_ratio=start_ratio,model_thermal_endpoint_ppm=deriv,continuous_r1_W=r1p,continuous_r1_peak_V=r1v,bat_reverse_V=mx(esd+fault,'bat_reverse_V'),bss_vds_V=mx(esd+fault,'bss_vds_V'),span_V=mx(esd+fault,'span_max'),continuity_close_us=mx(cont,'close_s')*1e6,continuity_open_us=mx(cont,'open_s')*1e6,continuity_max_transitions=mx(cont,'transitions'),leak_pass=sum(r['pass_current'] for r in leaks),leak_n=len(leaks),inl_guaranteed_pct=mx([r for r in inl if r['level']=='guaranteed'],'worst_pct'),inl_calibrated_pct=mx([r for r in inl if r['level']=='calibrated_proxy'],'worst_pct'))
 summary.update(tvs_continuous_W=mx(steady,'tvs_continuous_avg_W'),rs_continuous_W=mx(steady,'rs_continuous_avg_W'),zener_continuous_W=max(mx(steady,'dzp_continuous_avg_W'),mx(steady,'dzn_continuous_avg_W')),clamp_continuous_peak_mA=1000*max(mx(steady,'d2p_continuous_peak_A'),mx(steady,'d2n_continuous_peak_A')),clamp_startup_peak_mA=1000*max(mx(fault,'d2p_peak_A'),mx(fault,'d2n_peak_A')),r1_esd_peak_V=max(mx(esd,f'r1_{i}_vpeak_V') for i in (1,2,3)))
 (R/'s13_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 text=f'''# ACTA S13 — DMM: ohmios, diodo y continuidad

8 oct 2026 · Codex · Contrato: PLAN_SIMULACION_S13.md; ESTUDIO_BLOQUE3.md íntegro, especialmente §9. Referencias: PLAN/ACTA S11.4, ACTA S12d y entorno ENCARGO_CODEX_S11_1.md.

## Alcance y reproducción

Confirmación de c1: relé TQ2SA → 3 × 510 Ω → N1 (SMAJ12CA, inyección aquí) → R_S 2.7 kΩ → sujeciones. P43: TLV2372, BSS138 de referencia/habilitación y BSS84 de paso, fuerza/sentido por dos 74HCT4051, compensación 1 kΩ + 1 nF; 2 MΩ con 420 kΩ y 20 MΩ con 1.7 MΩ. Diodo por X2 ×10.1, continuidad a 1 mA con un Schottky negativo en PB14. P33 excluida. No se cambiaron piezas ni archivos anteriores, 01_diseno, models, STATE o DECISIONS. No hubo descargas ni prueba física.

Desde la raíz (entrecomillar las rutas):

```powershell
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --preflight
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --smoke
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --resume
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/analizar_s13.py"
```

10 trabajadores, 900 s/caso; S3G4_MODELS y S3G4_LTSPICE admitidos. LTspice por argumentos independientes, sin shell. Resume exige coincidencia de firma del deck/ejecutor/include/dependencias S11. Archivos por caso en S13: cir, log, raw y json. El nombre largo de cada .meas expresa las variables de estado y, en C1, el estado completo heredado. Los filenames son cortos por el límite de ruta Windows.

## Simulaciones y tiempo

{len(rows)} estados únicos; {len(good)} completos y {len(fail)} errores. Smoke: {smoke['total']} casos, {smoke['elapsed_s']:.3f} s. Campaña: {campaign['total']} casos, {campaign['reused']} reutilizados, {campaign['elapsed_s']:.3f} s. Pared smoke+campaña: **{summary['wall_s']:.3f} s ({summary['wall_s']/60:.2f} min)**. Nuevos lanzamientos en campaña: {campaign['total']-campaign['reused']}. No se suman al tiempo definitivo la lectura, programación ni los preflights/smokes de depuración interrumpidos: no se conservó un registro íntegro de sus tiempos y lanzamientos, por lo que no se inventa un total histórico.

Distribución: {json.dumps(summary['by_kind'],ensure_ascii=False)}. C4 es cálculo numérico, no una simulación LTspice. C7 adicional responde a la prueba de diodo que aparece en §9 del estudio aunque el plan nombra C1–C6.

Completitud validada con el último tiempo del RAW; medidas de aceptación calculadas desde ese RAW. En {len(measnotes)} casos C3, el .meas FIND del borne exactamente al tiempo final falla por redondeo del último instante (320 µs); el RAW sí completa y conserva el valor final. Las medidas de cruce, apertura y rebotes se extraen de la traza, no de ese FIND. Se registra aparte en s13_measurement_notes.csv, sin presentarlo como fallo físico de continuidad ni como .meas exitoso.

## Tabla C1–C6

| Criterio | Resultado medido | Dictamen / alcance |
|---|---|---|
| C1, protección | R1 continua {r1p:.4f} W/pieza, pico {r1v:.2f} V; rieles {summary['span_V']:.4f} V; BAT54 inversa {summary['bat_reverse_V']:.3f} V; BSS84 {summary['bss_vds_V']:.3f} V | Cumple continuo; pulso condicionado al rating/curva del MPN. Modelo reducido de S11.4 |
| C2, P43 | Compliancia ≥0.3 V: {npass}/{len(comp)}; corriente inicial ±1 %: {ical}/{len(comp)}; PM mínimo {pmmin:.2f}°; peor asiento/límite {start_ratio:.3f} | Cumple rendimiento de compliancia ≥95 %, fase y asiento; {len(comp)-ical} errores iniciales marginales. Deriva de pasivos no garantizada; Ron/capacidades condicionados al modelo |
| C3, continuidad | Cierre {summary['continuity_close_us']:.3f} µs; apertura {summary['continuity_open_us']:.3f} µs; máximo {summary['continuity_max_transitions']:g} transiciones | Cumple dinámica sin rebotes; umbral calibrado condicionado a P41 |
| C4, INL | Máximo garantizado {summary['inl_guaranteed_pct']:.2f} %, proxy calibrado {summary['inl_calibrated_pct']:.2f} % | Cumple cálculo con INL de hoja; proxy 10 cuentas, no curva medida |
| C5, fugas | {summary['leak_pass']}/{summary['leak_n']} combinaciones pasan la deriva de corriente; {sum(r['pass_resistance'] for r in leaks)}/{len(leaks)} al invertir el divisor | Condicionado al prototipo. Fallos a 1 nA marginales de criterio; 10 nA incompatibles |
| C6, P34 | ±20 mV, ±5 V y ±60 V; X2 ×10.1 y ×1 | Cumple lógica modelada, umbral {p34_threshold} cuentas para ruido −3 y offset simulado; ADC ideal y fuente ordenada OFF. P33 excluida |

## C1: protección y esfuerzo

El generador, GDT y rieles son los de S11.4, sin rediseñar. Se retienen todos los estados T2 y T4 y se añade fuente a 1 mA en T4. El camino R1 se cambia exclusivamente al c1 contratado; R_S y las sujeciones permanecen intactos. Los valores del viejo audit de dos resistencias NO certifican las tres de c1: usar r1_1/r1_2/r1_3 del CSV. TVS, R_S, zéner y D2p/D2n mantienen sus claves de auditoría; máximos en resultados/s13_stress_summary.json.

Para continua/AC: potencia por R1 ≤1 W, tensión ≤200 V, TVS ≤0.5 W, corriente de sujeción continua ≤5 mA y separación de rieles ≤10.6 V. BAT54 ≤24 V inversos y BSS84 ≤40 V. TVS media continua: {summary['tvs_continuous_W']:.4f} W; R_S: {summary['rs_continuous_W']:.5f} W; zéner: {summary['zener_continuous_W']:.5f} W. Sujeción continua pico: {summary['clamp_continuous_peak_mA']:.4f} mA, frente al pico total de arranque {summary['clamp_startup_peak_mA']:.4f} mA. La ventana continua es el último intervalo de cinco ciclos de 60 Hz (también para DC); ambos valores se conservan en CSV. El pico de arranque no se presenta como corriente continua.

La ESD lleva R1 a {summary['r1_esd_peak_V']:.3f} V/pieza, por encima de 200 V si se aplica literalmente el límite de trabajo del §9. **C1 queda condicionado/no demostrado en pulso**: clasificar como falta de criterio/rating de impulso, sin afirmar destrucción. La potencia media sobre 50 µs NO es potencia continua. Falta la curva de impulso del HoCR2512 de 510 Ω. El GDT mantiene los supuestos de S11.4: arco 20 V, mantenimiento 10 mA, encendido/extinción 1 ns y extrapolación de cebado a frentes ESD. No prueba el retraso del GDT real ni supervivencia de PCB.

P43 completo en ESD falló numéricamente en xb2:D17 (timestep 1.25e-19 s a ~100 ns). Se conserva para C1 el modelo reducido de exposición validado en S11.4: fuente abstracta, diodo de cuerpo y capacidades de BSS84, BAT54 real de biblioteca. C2 sí usa los macromodelos completos. Esto es una **limitación de modelo**, no prueba de daño real.

## C2: qué se barrió y qué no se garantiza

100 placas Monte Carlo uniformes, semilla 1308: riel 4.8–5.0 V; R_ref/R_set ±0.1 %; Vos de cada TLV2372 ±4.5 mV; Vth BSS84 −0.8…−2.0 V; Ron nominal 60–130 Ω; capacidades explícitas ×0.5…1.5. Compliancia se busca con corriente ≥99 % de la corriente inicial de esa placa por barrido 0–4.5 V, resolución 10 mV, y se resta V_x a fondo con esa misma corriente. El CSV de campaña conserva también el umbral estricto contra corriente nominal; para compliancia tras calibrar usar s13_compliance_summary.csv. El error inicial ±1 % se evalúa aparte: un offset de ganancia no debe confundirse con pérdida de regulación. El fondo de 2 kΩ es el exigente; 200 Ω tiene el mismo suministro y menor V_x. No son 100 placas fabricadas ni intervalo estadístico de rendimiento garantizado.

80 esquinas AC (16 por cada una de las cinco corrientes). Ruptura/inyección de lazo y extracción del primer cruce de unidad según el estudio; el resto de parámetros nominales. No se exploró una esquina simultánea de todos los Vos en AC. 15 transitorios con 300/600/900 pF de TVS; arranque medido desde borne inicialmente a 0 V con rieles establecidos. No se acredita aquí encendido frío ni secuencia real EN/INH. 15 puntos térmicos de SPICE (18/23/28 °C); máximos respecto a 23 °C por rango: {', '.join(f'{x:.3f}' for x in deriv)} ppm.

**Ron de SWI1:** la biblioteca tiene una resistencia efectiva propia y no permite el mismo parámetro ideal de los decks de estudio. Se añade max(Ron−60,0) Ω y se publica force_ron_ohm en las filas DC. Por ello el barrido total no es exactamente 60–130 Ω y las capacidades internas SWI1 no varían con las capacidades explícitas. No se retoca la biblioteca ni se presenta este desajuste como dispersión del MPN: **limitación de modelo**.

El BSS138 usa un VDMOS genérico (Vth 1.3 V, Kp 1.3, capacidades explícitas) **supuesto**, no modelo garantizado del MPN. BSS84 y BAT54 conservan los modelos del estudio/biblioteca. Los BAV199 son del modelo local; TVS: avalancha lineal S11.4 y capacidad parametrizada; la fuga se inyecta en C5 en lugar de inventar extrapolación desde 12 V.

Deriva de pasivos/Vos del estudio: RSS de 125,177,20,4 ppm = {math.sqrt(125**2+177**2+20**2+4**2):.2f} ppm respecto a 23 °C. Peor caso lineal (125+250+20+4) = **399 ppm**, supera 300 ppm. El SPICE no incorpora TC real de las resistencias, referencia ni deriva garantizada de Vos: su deriva NO certifica esa especificación. **Criterio/método:** 217 ppm es una estimación RSS; con los límites individuales no hay garantía determinista de 300 ppm. No se cambian piezas.

## C3 y C6: lectura y lógica

Lectura basada en el deck run_cont.py: R_PROT 99 kΩ, 10 kΩ, OPAx192 de buffer, mux 70 Ω/28 pF, A ×10.1 y divisor 2×10 kΩ hasta PB14; un BAT54 negativo. COMP ideal, histéresis total 9 mV (HYST=1 típica), umbral 252.5 mV. Cierra 20/40 Ω y abre, TVS 300/600/900 pF. Las ventanas comienzan con DC establecido; maxstep 0.2 µs. La lectura X2 usa el divisor 9.91 MΩ/100 kΩ y buffer OPAx192; para C6 se simulan las rutas X0 y X2 por separado, sin reconstruir toda la red TMUX4053, cuyo efecto DC se idealiza.

El ±16 mV sin calibrar equivale a ±{.016/(.001*10.1/2):.3f} Ω. Para ≤±1.5 Ω tras P41 el residuo debe ser ≤7.575 mV en PB14. No hay calibración física ni se garantiza deriva/ruido real del COMP/DAC. La histéresis de hoja 4–16 mV tampoco queda probada por su típico 9 mV. Pendiente de prototipo; no se marca P41 realizada.

P34 usa X2: 20 mV → {20e-3*10.1*100000/10010000/100e-6:.3f} cuentas ideales. Un umbral literal de 20 mV puede perder ese caso con ruido −3 cuentas. La lectura positiva simulada resulta ligeramente menor por offset del OPAx192; el modelo de firmware calcula **{p34_threshold} cuentas** como umbral de aviso conservador: floor(menor señal simulada−3cuentas de ruido−0.5cuenta de redondeo). Esto puede avisar por debajo de 20 mV y no exige piezas; no se declara una modificación de firmware realizada. Para ±60 V, ×10.1 satura, lo que basta para avisar; ×1 permite leer ~±0.599 V sin saturación. X0 saturado no oculta la lectura independiente de X2. El estado ×1 a20 mV solo documenta lectura, no es la ruta de detección. resultados/s13_p34_summary.csv conserva cada estado. El ADC se idealiza en este modelo de lógica (cuentas de100 µV y ruido acotado); la INL local cerca de cero y la linealización real quedan pendientes. La fuente OFF se representa por BSS84 con puerta al riel y BAT54; el macromodelo TLV2372 deshabilitado no convergía en algunos DC extremos. La secuencia de habilitación real queda pendiente, sin modificar firmware.

## C4: presupuesto de INL

Barrido 10–100 % de cada rango, divisor de 10.01 MΩ, G=10.1 en 200 Ω y G=1 en el resto. INL diferencial: 5 V/4096 × 2.1/3.2 LSB =25.635/39.0625 cuentas de 100 µV. Ganancia de ohmios 600 ppm según el estudio; se descuenta de la tolerancia. Nivel calibrado: residuo supuesto de 10 cuentas; no se afirma que se haya medido o linealizado un ADC5.

| Rango Ω | Típica de hoja | Garantizada (≤100 %) | Proxy calibrado (≤85 %) |
|---|---|---|---|
{chr(10).join(lines)}

## C5: clasificación de fugas

3×3 combinaciones de 0.1/1/10 nA en fuerza y borne, dos rangos, 18/23/28 °C: 54 simulaciones. Ley de deriva ×2/10 °C, como el estudio. Se calibra a 23 °C y se compara deriva de corriente con 25 % de (tolerancia porcentual−600 ppm). Se conserva también la amplificación al invertir el divisor para convertir tensión a ohmios en s13_leak_summary.csv; no se oculta el efecto de la carga de 10.01 MΩ en 20 MΩ.

La suma de ambas fugas importa: no se comparan dos fugas de 1 nA como si fueran una sola. Los límites antiguos 0.85/1.14 nA del contrato corresponden a 1/0.2 µA; con 420 kΩ/1.7 MΩ las corrientes reales aumentan la tolerancia, pero no garantizan las fugas de hoja de los 4051. A 1 nA, falla marginal de criterio/prototipo; a 10 nA, error físico del supuesto inyectado. El modelo no demuestra que las piezas reales tengan 10 nA a baja tensión. No se propone ni aplica sustitución.

## Diodo (C7 adicional)

Silicio 0.65 V a 1 mA; LED 3.0/3.2 V y punto de compliancia 3.6 V a 100 µA, riel 4.8 V, lectura X2 ×10.1. DUT es tensión fija, como S11.4, no curva I/V de un LED seleccionado. Corriente medida en cada DUT y lectura en s13_campaign.csv. La corriente del DUT excluye la carga del divisor: no confundir I(R_k) con I_LED.

## Lista de piezas — contrato, no nueva selección

| Función | Pieza / valor | Cantidad / observación |
|---|---|---|
| Fuente y referencia | TLV2372IDR, C27204 | 1 dual |
| Paso | BSS84, C82079 (BSS84LT1G) | 1; modelo/hoja no garantizan ese MPN exacto |
| Referencia y habilitación | BSS138, C7420339 | 2; Vgs/Vth del MPN por confirmar |
| Fuerza/sentido | 74HCT4051, C87239 | 2; 5 canales usados +3 libres en cada uno |
| Rangos, 0.1 %,25 ppm/°C | 499 Ω;4.99 kΩ;49.9 kΩ;420 kΩ;1.7 MΩ | 5 valores; 1.7 MΩ =1.5 MΩ+200 kΩ; MPN de los dos últimos no definido por este encargo |
| Referencia, 0.1 % | 24.9 kΩ y4.99 kΩ | 2 |
| Referencia común | REF3325,2.5 V | Compartida; fuente ideal en estos decks |
| Compensación/control | 1 kΩ puerta;1 kΩ sentido;10 kΩ habilitación;1 nF C0G | 4 piezas; desacoplos según implementación, no definidos aquí |
| Bloqueo + PB14 | BAT54 (bloqueo y Schottky negativo) | 2 diodos |
| PB14 | 10 kΩ,1 % | 2, divisor ÷2 |
| Cadena c1 compartida con bloque1 | HoCR2512 510 Ω,2 W, C2912629 | 3; curva de impulso pendiente |
| Cadena compartida | TQ2SA,C46047; SMAJ12CA; R_S2.7 kΩ;2×BAV199;2×BZT52C5V6 | Piezas del contrato; sin sustitución |
| Lectura compartida, bloque2 | OPA4192;74HCT4051;TMUX4053;divisor6×1.5 MΩ+910 kΩ+100 kΩ | Ya definidos en S12d; no piezas nuevas de P43 |
| MCU compartido | STM32G473: COMP7/DAC2/PB14/ADC5 | Sin hardware nuevo para P34; P33 excluida |

## Dudas y pendientes

Fuga real y limpieza/guarda del prototipo; capacidad de TVS/cables y asiento real en 20 MΩ; curva ADC5/linealización; P41 y deriva COMP/DAC; BSS138/MPN; impulso de HoCR2512/GDT real; secuencia EN/INH y recuperación de alimentación. La tensión en vacío mayor que3.4 V permanece como contradicción documental del estudio: no se cambia 01_diseno. Las limitaciones de modelo/criterio se clasifican, sin perseguirlas ni cambiar piezas.

Diario: ai-context/journal/2026-10-08-codex-s13.md. STATE y DECISIONS se dejan intactos por instrucción expresa. La sincronización del contexto se ejecuta al cierre sobre las fuentes locales.
'''
 (HERE/'ACTA_S13.md').write_text(text,encoding='utf-8');print(json.dumps(summary,indent=2));print('stress',json.dumps(stress))
if __name__=='__main__':main()
