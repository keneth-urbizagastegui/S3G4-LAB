S12d terminado. **E3/E5/E8 cumplen; E2 queda marginal y no permite confirmar cierre con margen.** Fuentes protegidas intactas.

Ficheros: [acta](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S12d.md>), [include](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/comun/dmm_bloque2d.inc>), [ejecutor](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12d.py>), [análisis](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/analizar_s12d.py>), [CSV](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/resultados/s12d_campaign.csv>) y [diario cerrado](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-08-codex-s12d.md>).

**234/234 casos válidos**, 10 trabajadores, 900 s/caso. Incluidos smoke y ocho repeticiones por nombres `.meas`: **242 lanzamientos, 26 min 15 s**. Con preparación: 256 lanzamientos y 29 min 09 s de fases medidas.

| Ensayo | Resultado |
|---|---|
| E1 | Heredado S12c: residuo p95 0.151%; no repetido |
| E2 | SPICE 3.92 cuentas; presupuesto 4.44 frente a 4: marginal de criterio/presupuesto |
| E3 | DC 0.42 cuentas; AC 0.13; pinza 40.1 µA: cumple |
| E4 | Heredado: recuperación ≤15.52 µs |
| E5 | Margen mínimo 43.6°: cumple ≥40° |
| E6 | Heredado: régimen cumple; calificación de impulso pendiente |
| E7 | Heredado: 0.036/0.027 cuentas rms |
| E8 | Pinza máxima 0.461 mA: cumple ≤5 mA |

**Fuga máxima tolerable conservadora:** ≈**0.50 nA por entrada de buffer a 23 °C**, con los supuestos del acta.

Piezas finales: 1 OPA4192; 1 74HCT4051; 1 sección TMUX4053; 6×1.5 MΩ, 910 kΩ, 100 kΩ; 91 kΩ/10 kΩ; 2×10 kΩ ante buffers; 3×3.3 kΩ antipulso; 3×100 pF C0G/2 kV; 330 pF C0G/≥100 V; 3 nF C0G/≥25 V. Referencias y condiciones en el acta.

Dudas: margen real de E2, fugas/derivas térmicas, acoplo del cuádruple, IV de pinzas, MPN y curvas de impulso pendientes. Auditoría independiente y ensayos físicos pendientes.