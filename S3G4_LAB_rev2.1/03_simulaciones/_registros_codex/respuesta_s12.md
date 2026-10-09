S12 ejecutado y documentado; **no queda conforme**. No cambié piezas ni archivos excluidos.

Ficheros: [acta](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S12.md>), [frontal](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/comun/dmm_bloque2.inc>), [ejecutor](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12.py>), [complemento E6](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12_e6_actual.py>) y [diario cerrado](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-08-codex-s12.md>). Decks/logs/RAW en `S12/`; CSV en `resultados/s12_*.csv`.

**Campañas:** 1075 casos válidos —1073 ejecuciones nuevas y 2 reutilizadas—. Principal: **16 min 16 s**; complemento: **4 min 28 s**, solapados. Smoke: 11/11 casos.

**OPA2192:** orden `IN+ IN− VCC VEE OUT` confirmado con seguidor. Ib: **5.06 pA**, frente a 5 pA típico; a 4 V sube a 24.85 pA. Cruce de unidad: **9.62 MHz**, frente a 10 MHz típico. Sigue correctamente hasta 4.5 V, dentro del modo común de hoja.

| Criterio | Resultado |
|---|---|
| E1 | Cumple AC pequeño: p95 conjunto **0.208 %**; **0.271 %** con calibración al 0.1 %. |
| E2 | **Falla 200 mV:** 4.008 cuentas nominales; 4.552 en presupuesto conservador. |
| E3 | **Falla X1/X2:** colas incorrectas, 2.793/4.879 V. X0 cumple. |
| E4 | Cumple el modelo: recuperación **18.7/22.6 µs**, sin valores engañosos bajo el umbral supuesto. |
| E5 | **Falla corner:** margen **40.46°**; recuperación ≤11.45 µs. |
| E6 | **Falla cadena vigente:** **558.1 V** por 1.5 MΩ frente a 400 V de sobrecarga. |
| E7 | Cumple: **0.0271/0.00450 cuentas rms**, incluyendo autocero independiente. |

Fuga máxima presupuestada **a 23 °C**, condicionada a las hipótesis térmicas:

| Rango | Máxima |
|---|---:|
| 200 mV | 0.866 nA |
| 2 V | 9.657 nA |
| 20 V | 1.046 nA |
| 50 V | 9.657 nA |

Dudas principales: fidelidad de `SWI1` y canales no seleccionados, Ron/capacidad del TMUX, fuga/Ib reales y pulso del GDT. El contrato reutiliza GDT solo; la cadena aprobada lleva MOV. Ambas quedaron separadas en el acta. Los resultados condicionales no certifican ≥95 % de fabricación.