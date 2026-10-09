S13 terminado: **502/502 estados completos, sin errores de ejecución**. Smoke: 182.4 s; campaña: 1,252.1 s, con 10 reutilizados. Total definitivo: **23 min 54.5 s**, excluyendo depuración.

Ficheros en [DMM](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM>): `comun/dmm_bloque3.inc`, `ejecutar_s13.py`, `analizar_s13.py`, [ACTA_S13.md](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S13.md>) y `resultados/s13_*`. [Diario cerrado](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-08-codex-s13.md>); contexto sincronizado.

| Criterio | Resultado |
|---|---|
| C1 | Cumple continuo: R1 0.484 W/pieza, TVS 0.391 W, rieles 10.569 V. ESD: 358 V/pieza; pendiente rating de impulso. |
| C2 | Compliancia 97/100; fase mínima 74.45°; asiento cumple. Deriva de pasivos no garantizada. |
| C3 | Cierre 30.56 µs; apertura 0.30 µs; sin rebotes. Umbral calibrado pendiente de P41. |
| C4 | Cumple cálculo: 91.27 % garantizada; 78.12 % con proxy calibrado. |
| C5 | Pasan 4/18 combinaciones en corriente y 2/18 en ohmios. Fallos de 1 nA clasificados como marginales. |
| C6 | Cumple lógica simulada de P34 con umbral conservador de 16 cuentas. ADC ideal y fuente ordenada OFF; P33 excluida. |

Diodo adicional: **99.84 µA a 3.6 V** y **1.00194 mA a 0.65 V**.

Piezas: TLV2372, 2×BSS138, BSS84, 2×74HCT4051, 2×BAT54; R_k de 499 Ω, 4.99 kΩ, 49.9 kΩ, 420 kΩ y 1.7 MΩ; referencia 24.9/4.99 kΩ; compensación 1 kΩ + 1 nF; divisor PB14 2×10 kΩ. Cadena compartida: TQ2SA, 3×510 Ω, SMAJ12CA, R_S 2.7 kΩ, BAV199 y BZT52C5V6. Lista completa y MPN en el acta.

Dudas pendientes: fugas reales, curva de impulso/GDT, MPN BSS138, ADC/P41 y secuencia EN/INH. SWI1 dio Ron superior a la del estudio; queda documentado como limitación de modelo.