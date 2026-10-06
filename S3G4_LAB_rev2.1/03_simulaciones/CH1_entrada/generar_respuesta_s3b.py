"""Generate the requested compact final response from measured CSVs only."""
import sys
sys.dont_write_bytecode=True
import csv
import json
from pathlib import Path
import ejecutar_s3b as s

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'resultados'


def read(name):
    with (OUT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def main():
    run=json.loads((OUT/'s3b_ejecucion.json').read_text(encoding='utf-8'))
    rows=read('s3b_resultados.csv');crit=read('s3b_criterios.csv')
    text='# Respuesta final S3b\n\n'
    text+='Creado: `comun/ch1_comun_s3b.inc`, `ejecutar_s3b.py`, `S3b/` (.cir y .log), '
    text+='`resultados/s3b_*` (CSV, JSON, resumen y registros), `ACTA_S3b.md`, este resumen y '
    text+='`ai-context/journal/2026-10-03-1619-codex-s3b.md`. '
    text+='Auxiliares: `generar_respuesta_s3b.py` y `verificar_reproduccion_s3b.py`.\n\n'
    text+=f'Campaña completa: **código {run["exit_code"]}, {run["simulations"]} simulaciones, {run["elapsed_seconds"]:.3f} s**, diez trabajadores; '
    text+=f'{run["errors"]} errores y {run["warnings"]} advertencias. '
    for name,label in [('s3b_controls_ejecucion.json','Controles previos'),('s3b_smoke_ejecucion.json','Smoke')]:
        r=json.loads((OUT/name).read_text(encoding='utf-8'))
        text+=f'{label}: código {r["exit_code"]}, {r["simulations"]} simulaciones, {r["elapsed_seconds"]:.3f} s. '
    text+='El código informa ejecución; las fallas eléctricas son resultados válidos.\n\n'
    b0=[]
    for r in rows:
        if r['test']=='B0':b0.append(dict(variante=r['variant'],ganancia_DC=f'{float(r["gain_dc"]):.6f}',corte_MHz=f'{float(r["minus3_Hz"])/1e6:.3f}',pico_dB=f'{float(r["peak_db"]):.3f}'))
    text+='B0 (U103A aislada):\n\n'+s.table(b0,list(b0[0]))+'\n\n'
    controls=[r for r in rows if r['test']=='B2' and r['variant']=='NONE']
    text+='Control de ruido sin protección: '+', '.join(f'{r["noise_model"]}: **{float(r["noise_315m_pct_div"]):.6f} % div**' for r in controls)+'.\n\n'
    grid=[];limits=[]
    for v in 'ABCD':
        grid.append(dict(variante=v,**{f'C{i}':next(r['status'] for r in crit if r['variant']==v and r['criterion']==f'S3b-C{i}') for i in range(1,7)}))
        dc=[r for r in rows if r['test']=='B3' and r['variant']==v]
        noise=max(float(r['noise_315m_pct_div']) for r in rows if r['test']=='B2' and r['variant']==v)
        limits.append(dict(variante=v,dif_U103A_V=f'{max(float(r["u103a_differential_peak_V"]) for r in dc):.6f}',
            dif_U103B_V=f'{max(float(r["u103b_differential_peak_V"]) for r in dc):.6f}',
            I_4051_mA=f'{max(float(r["switch_current_peak_A"]) for r in dc)*1e3:.6f}',
            I_Dp_mA=f'{max(float(r["diode_p_current_peak_A"]) for r in dc)*1e3:.6f}',
            I_Dn_mA=f'{max(float(r["diode_n_current_peak_A"]) for r in dc)*1e3:.6f}',
            I_OPA810_mA=f'{max(float(r["opa810_current_peak_A"]) for r in dc)*1e3:.6f}',
            ruido_max_pct_div=f'{noise:.6f}'))
    text+='Criterios S3b-C1…C6:\n\n'+s.table(grid,list(grid[0]))+'\n\n'
    passed=[v for v in 'ABCD' if all(r['status']=='PASA' for r in crit if r['variant']==v)]
    text+='Pasan todo: '+(', '.join(passed) if passed else '**ninguna variante**')+'. No se elige variante.\n\n'
    excess=[]
    for v in 'ABCD':
        iso=next(r for r in rows if r['test']=='B0' and r['variant']==v)
        ac=[r for r in rows if r['test']=='B1' and r['variant']==v]
        rec=max(float(r['recovery_s']) for r in rows if r['test']=='B4' and r['variant']==v)
        excess.append(dict(variante=v,pico_B1_dB=f'{max(float(r["s3_peak_db"]) for r in ac):.6f}',
            exceso_C4_B0_dB=f'{max(0,float(iso["peak_db"])-.5):.6f}',
            recuperacion_us=f'{rec*1e6:.6f}',exceso_C5_us=f'{max(0,rec*1e6-1):.6f}'))
    text+='Fallas cuantificadas (C4 exige también B0):\n\n'+s.table(excess,list(excess[0]))+'\n\n'
    text+='B3: máximos sobre ambas escalas y todo el barrido; ruido máximo en las 12 escalas:\n\n'+s.table(limits,list(limits[0]))+'\n\n'
    offsets=[]
    for v in 'ABCD':
        vals={'variante':v}
        for ix,label in [(0,'5mV'),(5,'200mV')]:
            for t in [25,70]:
                r=next(r for r in rows if r['test']=='B6' and r['variant']==v and int(r['ix'])==ix and int(r['temp_C'])==t)
                vals[f'{label}_{t}C_div']=f'{float(r["added_offset_div"]):.8g}'
        offsets.append(vals)
    text+='B6: offset **añadido frente a S3**, en divisiones:\n\n'+s.table(offsets,list(offsets[0]))+'\n\n'
    text+='Dudas: C2 de A/B es condicional por falta de hoja local BAT54S Vishay; el modelo declara Iave=300 mA. '
    text+='El AD8038 no modela Ib real ni deriva, y los pares de diodos no modelan desajuste; el pequeño B6 no garantiza offset de placa. '
    text+='B0 usa la carga aislada de S3 (1 kΩ ∥ 10 pF); B1 conserva la cadena real, por eso se informan por separado. '
    text+='Se mantienen las contradicciones documentales y los valores derivados de S2b; sin compensaciones nuevas, selección de variante, descargas ni ensayos físicos. '
    text+=f'Archivos protegidos comprobados: {run["protected_files"]}; cambios: {run["protected_changed"]}.\n'
    replay=OUT/'s3b_reproducibilidad.json'
    if replay.exists():
        r=json.loads(replay.read_text(encoding='utf-8'))
        text+=f'\nReejecución en ruta corta con S3G4_MODELS: código {r["exit_code"]}, {r["simulations"]} simulaciones, {r["elapsed_seconds"]:.3f} s; '
        text+=f'**{r["csv_identical"]}/{r["csv_count"]} CSV idénticos byte a byte**.\n'
    s.write(ROOT/'RESPUESTA_FINAL_S3b.md',text)
    print(text)


if __name__=='__main__':main()
