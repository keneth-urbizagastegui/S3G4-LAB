Completado. Acta y diario cerrados; 64 fuentes protegidas verificadas sin cambios.

Ficheros: [ACTA_S12b.md](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S12b.md>), [ejecutar_s12b.py](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12b.py>), [dmm_bloque2b.inc](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/comun/dmm_bloque2b.inc>), auxiliares, resultados CSV/JSON y [diario](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-08-codex-s12b.md>).

**1191/1191 simulaciones válidas**, diez trabajadores, límite 900 s/caso. Fases válidas: **51 min 00.8 s**; smoke 11/11 en 17.04 s; cuatro verificaciones adicionales en 326.43 s. Excluye desarrollo e intentos interrumpidos.

| Ensayo | Resultado |
|---|---|
| E1 | Cumple población virtual: p95 0.18071% |
| E2 | Falla presupuesto conservador: 4.18869 cuentas |
| E3 | Rieles cumplen; cuatro fallos de asentamiento, máximo 1.65612 cuentas |
| E4 | Cumple: recuperación ≤15.52 µs |
| E5 | Falla: margen mínimo 38.46° |
| E6 | Pendiente calificación de impulso: Rc alcanza 1111.43 V |
| E7 | Cumple: ruido ≤0.03595 cuentas |
| E8 | Falla modelo ESD: 22.03 mA frente a 5 mA |

**Fuga máxima tolerable:** 0.804 nA por entrada de buffer a 23 °C, condicionada al presupuesto y a duplicarse cada 10 °C.

Piezas finales: 6×1.5 MΩ, 910 kΩ, 100 kΩ; 3×100 pF/2 kV; 3×3.3 kΩ antipulso; 330 pF y 3 nF; 74HCT4051; OPA2192 dual nuevo para X0/X1; canal OPA2192 A; sección TMUX4053; 91 kΩ/10 kΩ. Referencias y pendientes están en el acta.

Dudas: pinza de entrada sin IV validada, corriente capacitiva incluida en E8, arco IEC aire no modelado, fugas/dispersión reales y curvas de impulso de Rc pendientes. La comprobación fina de ±50 V da 2.15 mA; no confirma el pico grueso de 10.31 mA. Auditoría independiente y prototipo pendientes.