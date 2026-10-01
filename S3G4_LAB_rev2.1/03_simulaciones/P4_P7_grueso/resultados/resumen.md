# Resumen automatico P4/P7

- Simulaciones: 14
- Errores: 0
- Advertencias: 0

| Criterio | P4 | Estado | P7 | Estado |
|---|---|---|---|---|
| C1 | x1=0.9089 Mohm, d100=0.9991 Mohm | FALLA | fina=0.9998 Mohm, gruesa=0.9998 Mohm | PASA |
| C2 | x1=21.832 pF, d100=13.878 pF; delta=7.954 pF | FALLA | fina=18.609 pF, gruesa=18.609 pF; delta=0.000 pF | PASA |
| C3 | peor error=-1.190% | FALLA | peor error=-0.199% | PASA |
| C4 | peor planitud=9.419%, perdida1.5MHz=0.142 dB, pico=0.794 dB | FALLA | peor planitud=14.881%, perdida1.5MHz=1.429 dB, pico=3.203 dB | FALLA |
| C5 | 5mV/div=0.366%, 500mV/div=15.826% | FALLA | 5mV/div=22.276%, 500mV/div=0.091% | FALLA |
| C6 | 5mV/div=15.54uV (0.311%), 200mV/div=468.44uV (0.234%), 500mV/div=1533.04uV (0.307%) | PASA | 5mV/div=44.52uV (0.890%), 200mV/div=906.04uV (0.453%), 500mV/div=3573.66uV (0.715%) | PASA |
| C7 | THD=0.0000%, Zin_ef=999.01 kohm | PASA | THD=0.0154%, Zin_ef=738.57 kohm | FALLA |
| C8 | low: Rt=16.50V/0.82mW c/u, Rs-base=44.02V/19.38mW, VinAmp=5.98V; safe: Rt=16.50V/0.83mW c/u, Rs-base=0.00V/0.00mW, VinAmp=0.50V | FALLA | low: rtf=14.71V/0.65mW c/u, rtg=16.58V/0.41mW c/u, VinAmp=5.86V; safe: rtf=14.71V/0.65mW c/u, rtg=16.58V/0.41mW c/u, VinAmp=5.86V | FALLA |
| C9 | Iclamp_pk peor=3.48mA, VinAmp peor=6.09V | FALLA | Iclamp_pk peor=0.34mA, VinAmp peor=5.97V | FALLA |

## Ejecuciones

| Fichero | exit LTspice | Estado |
|---|---:|---|
| `P4_rele\T01_zin.asc` | 0 | OK |
| `P4_rele\T02_respuesta.asc` | 0 | OK |
| `P4_rele\T03_escalon.asc` | 0 | OK |
| `P4_rele\T04_ruido.asc` | 0 | OK |
| `P4_rele\T05_gran_senal.asc` | 0 | OK |
| `P4_rele\T06_supervivencia.asc` | 0 | OK |
| `P4_rele\T07_robustez.asc` | 0 | OK |
| `P7_sin_rele\T01_zin.asc` | 0 | OK |
| `P7_sin_rele\T02_respuesta.asc` | 0 | OK |
| `P7_sin_rele\T03_escalon.asc` | 0 | OK |
| `P7_sin_rele\T04_ruido.asc` | 0 | OK |
| `P7_sin_rele\T05_gran_senal.asc` | 0 | OK |
| `P7_sin_rele\T06_supervivencia.asc` | 0 | OK |
| `P7_sin_rele\T07_robustez.asc` | 0 | OK |

## Errores
- Ninguno.

## Advertencias
- Ninguna.
