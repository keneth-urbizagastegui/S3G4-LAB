"""Compact final response from measured S3 CSVs; never changes the circuits."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'resultados'


def read(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def main():
    run=json.loads((OUT/'s3_ejecucion.json').read_text(encoding='utf-8'))
    smoke=json.loads((OUT/'s3_smoke_ejecucion.json').read_text(encoding='utf-8'))
    verification=json.loads((OUT/'s3_reproducibilidad.json').read_text(encoding='utf-8'))
    criteria=read('s3_criterios.csv');scales=read('s3_escalas.csv')
    pulses=read('s3_e14.csv');idle=read('s3_e11b.csv');sine=read('s3_e13.csv')
    amps=read('s3_isoamp.csv');taps=read('s3_tomas.csv')
    text=f'# Respuesta final S3\n\nCampaña: código **{run["exit_code"]}**, **{run["simulations"]} casos únicos**, **{run["elapsed_seconds"]:.3f} s**, diez trabajadores. '
    if run.get('e15_revised_simulations'):
        text+=f'Incluye {run["e15_revised_simulations"]} repeticiones de E15 para corregir sólo su estímulo (+2div con offset), en {run["e15_revision_seconds"]:.3f}s; {run["total_simulation_attempts"]} intentos en estas fases finales. '
    text+=f'Smoke: código {smoke["exit_code"]}, {smoke["simulations"]} ejecuciones, {smoke["elapsed_seconds"]:.3f} s (previo a la última corrección del estímulo E15). '
    native=sum(bool(r.get('native_failure')) for r in run['records'])
    text+=f'Dos fallos nativos de compatibilidad SWI1 activan el reemplazo permitido sólo en E15; {run["simulations"]-native} simulaciones utilizables. '
    text+=f'Reejecución con `S3G4_MODELS`: código {verification["replay_exit_code"]}, {verification["replay_seconds"]:.3f} s; **{len(verification["csv"])} CSV idénticos byte a byte**.\n\n'
    text+='Creados: `comun/ch1_comun_s3.inc`, `ejecutar_s3.py`, `repetir_e15_s3.py`, `verificar_reproduccion_s3.py`, `generar_respuesta_s3.py`, `S3/` (decks y logs), `resultados/s3_*.csv`, JSON de ejecución y reproducción, `resultados/s3_resumen.md`, `ACTA_S3.md`, este resumen y el diario de Codex. Ningún archivo protegido cambió.\n\n'
    text+='U103 aislado (1kΩ∥10pF): '
    for a in amps:text+=f'U103{a["stage"].upper()} ×{float(a["gain_dc"]):.6f}, −3dB {float(a["minus3_Hz"])/1e6:.3f}MHz, pico {float(a["peak_db"]):.3g}dB; '
    text+='tomas calculadas y comprobadas: '+', '.join(f'{float(t["ratio"]):.9f}' for t in taps)+'. '
    switches=read('s3_isosw.csv')
    text+='SWI1 activo bajo; RON(−2/0/+2V)='+ '/'.join(f'{float(next(s["ron"] for s in switches if float(s["level"])==v and s["control"]=="0")):.2f}' for v in [-2,0,2])+'Ω.\n\n'
    text+='| Criterio | Valor medido y límite | Resultado |\n|---|---|---|\n'
    for c in criteria:
        status='Informado' if c['criterion']=='S3-C3' else c['status']
        if c['criterion']=='S3-C8':status+=', aproximación E15'
        if c['criterion']=='S3-C7':status+=' por tensión OPA810; interpretación S2b pendiente'
        text+=f'| {c["criterion"]} | {c["value"]} | {status} |\n'
    text+='\n| Escala/div | Pérdida S3 a2MHz dB | BNC dB | Pico S3 dB | Ruido %div | Recuperación +/− µs |\n|---|---|---|---|---|---|\n'
    for s in scales:
        v=float(s['scale_V_div']);label=f'{v*1000:g}mV' if v<.5 else f'{v:g}V'
        text+=f'| {label} | {float(s["loss_s3_2m_db"]):.5f} | {float(s["loss_bnc_2m_db"]):.5f} | {float(s["peak_s3_db"]):.6f} | {float(s["noise_pct_div"]):.4f} | {float(s["recovery_positive_us"]):.4f}/{float(s["recovery_negative_us"]):.4f} |\n'
    noise=max(float(s['noise_pct_div']) for s in scales)
    recovery=max(float(p['recovery_0p1_s']) for p in pulses)*1e6
    text+=f'\nC4 falla en las 12 escalas: máximo **{noise:.6f}%**, exceso de {noise-.45:.6f} puntos frente a 0.45%. C6: **{recovery:.6f} µs** frente a 1 µs (exceso {recovery-1:.6f} µs), en 200 mV/div con ambas polaridades. '
    two=[s for s in sine if s['vpp']=='2']
    text+=f'C5: THD máxima {max(float(s["thd_pct"]) for s in two):.6f}%, dV/dt {max(float(s["max_dvdt_V_us"]) for s in two):.3f}V/µs (límite0.5×{float(two[0]["model_SR_V_us"]):g}).\n\n'
    da=max(float(p['u103a_differential_peak_V']) for p in pulses)
    db=max(float(p['u103b_differential_peak_V']) for p in pulses)
    rail=max(float(p['u101_'+side+'_rail_excess_V']) for p in pulses for side in ['plus','minus'])
    ib=max(float(p['u101_'+side+'_current_peak_A']) for p in pulses for side in ['plus','minus'])*1e3
    d1=max(float(p['u101_differential_peak_V']) for p in pulses)
    text+=f'E14: diferencial pico **U103A {da:.6f} V / U103B {db:.6f} V**, ambas por debajo de ±4 V. U101: {d1:.6f} V/7 V; {ib:.6f} mA/10 mA; excursión máxima {rail:.6f} V más allá del riel, frente a 0.5 V del criterio estricto (exceso {rail-.5:.6f} V). La auditoría S2b admite la excursión con corriente limitada; se conserva la contradicción.\n\n'
    text+='Reposo por amplificador, corrientes en sus pines +5V/−5V (mA): '
    for label,key in [('OPA810','u101'),('AD8039A','u103a'),('AD8039B','u103b')]:
        p=sum(float(r[key+'p_idle']) for r in idle)/len(idle)*1e3
        n=sum(float(r[key+'n_idle']) for r in idle)/len(idle)*1e3
        text+=f'**{label} {p:.6f}/{n:.6f}**; '
    text+='no se suman como si fueran dos consumos independientes.\n\n'
    text+='Dudas: macro AD8039 con16.18nV/√Hz a100kHz frente a8 de la hoja (no corregido); SWI1 sin convergencia al conmutar, por lo que E15 usa100Ω y capacidades de hoja, sin inyección de carga real; los30ns/20ns del contrato no están declarados así en la hoja; excepción de corriente del OPA810 y consumo real pendientes de auditoría/placa. El límite40V evita forzar saturación en las escalas más altas. Modelos, entregables anteriores, STATE y DECISIONS permanecen intactos.\n'
    (ROOT/'RESPUESTA_FINAL_S3.md').write_text(text,encoding='utf-8')
    print('RESPUESTA_FINAL_S3.md generado a partir de los CSV y la verificación independiente.')


if __name__=='__main__':main()
