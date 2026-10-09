**S11.2 terminado: no aprobado.** Acta y diario cerrados; memoria sincronizada. Los archivos protegidos permanecen intactos.

Creados: [ACTA_S11_2.md](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S11_2.md>), [ejecutar_s11_2.py](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s11_2.py>), [dmm_bloque1_o2.inc](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/comun/dmm_bloque1_o2.inc>), modelo BSS126, documento Q0, tres auxiliares, instrucciones de reproducción, decks/logs/CSV y [diario](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-07-codex-s11-2.md>).

**Campaña:** 498 casos en **42 min 43 s**: 486 terminados y 12 Q7 en timeout de 300 s. Además, Q0: 12/12 en 2.72 s; auditoría de apertura: 53/53 en 156.41 s.

**Q0:** BSS126, pp.1–2: límites, IDSS y Rth; p.3: capacidades/diodo; pp.4–6: SOA y curvas térmicas. IDSS sólo tiene mínimo de 7 mA, sin máximo. **R_LIM=700 Ω se usó como diagnóstico; no hay una selección garantizable.** Los 21 mA son sensibilidad, no máximo de IDSS.

| Criterio | Resultado | Evidencia principal |
|---|---|---|
| C1 | Falla | Potencia, unión y tensiones ESD excedidas |
| C2 | Falla | Inyección hasta 5.884 mA frente a 3 mA; span 11.174 V |
| C3 | Falla | Clamp HC hasta 432 mA |
| C4 | Falla | No demuestra supervivencia a red durante 10 s |
| C5 | Informativo | BAV199: 3 pA típicos/5 nA máximos por diodo a 75 V |
| C6 | Falla | 3.374–3.577 V a 100 µA; 1.271–1.523 V a 1 mA |
| C7 | Sin certificar | Los 12 casos agotan el plazo |
| C8 | Falla por pico | 423.592 A frente al margen de 100 A |

**BSS126 en Q3:** corriente límite **1.307–2.569 mA**, potencia máxima por FET **0.263 W**, unión estimada máxima **135.66 °C**, frente a 120 °C. La tabla completa de extremos está en el acta; la estimación térmica no realimenta eléctricamente el modelo.

**Borne A:** las 162 aperturas quedan registradas entre **20.3 µs y 4.014 ms**; corriente posterior ≤0.651 nA. El GBU808 alcanza **423.592 A y 10.930 A²s**: falla por pico, aunque pasa el margen de I²t dentro del modelo de arco supuesto.

**ESD sin TVS:** hasta **VDS=2897.9 V y VGS=1592.0 V**, muy por encima de 600/20 V absolutos. O2 no queda validado; no se añadieron piezas.

Dudas abiertas: IDSS máximo y modelo garantizado, hojas del zéner/resistencias/derivador, arco real del fusible, discrepancia de ratings GBU808, conmutación del relé a 230 Vac y recuperación física tras calentamiento o daño.