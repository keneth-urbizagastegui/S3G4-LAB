S12c ejecutado y documentado. **El diseño no queda conforme**, por E2 y E3; E6 sigue pendiente de calificación.

Ficheros: [include](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/comun/dmm_bloque2c.inc>), [ejecutor](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12c.py>), [acta completa](<C:/Users/Keneth/Desktop/S3G4 LAB/S3G4_LAB_rev2.1/03_simulaciones/DMM/ACTA_S12c.md>) y [diario cerrado](<C:/Users/Keneth/Desktop/S3G4 LAB/ai-context/journal/2026-10-08-codex-s12c.md>). También se generaron los tres scripts de análisis/verificación y `resultados/s12c_*`.

**Ejecución:** smoke 15/15 en 91.9 s; campaña 1215/1215 válidos en **30 min 46.5 s**, incluidas reparaciones. Trece comprobaciones adicionales: cuatro válidas y nueve agotaron 900 s; ventana solapada de unos 24 min 37 s. Diez trabajadores. Las 167 fuentes protegidas permanecen idénticas.

| Ensayo | Resultado | Dictamen |
|---|---|---|
| E1 | Residuo P95 conjunto 0.1507%; 50 Vrms nominal comprobado | Cumple |
| E2 | 20 V: presupuesto de offset 8.044 cuentas | No cumple en 20 V |
| E3 | Entrada del buffer 5.524 V; caso refinado 1.813 cuentas a 1.5 ms | No cumple |
| E4 | Sin valores válidos engañosos; recuperación 15.52 µs | Cumple |
| E5 | Margen mínimo 43.60° | Cumple |
| E6 | 3.3 kΩ: pico 1.112 kV y 2.321 µJ | Calificación pendiente |
| E7 | Ruido máximo 0.03595 cuentas rms | Cumple |
| E8 | Pinza máxima 2.998 mA frente a 5 mA | Cumple |

**Fuga máxima tolerable**, bajo los supuestos térmicos del acta:

| Rango | Máximo |
|---|---:|
| 200 mV, X0 | 0.804 nA; se mantiene el límite contractual de 0.6 nA |
| 2 V, X0 | 9.601 nA |
| 20 V, X2 | **0.866 nA agregados** |
| 50 V, X2 | 9.657 nA agregados |

En X2 manda el rango de 20 V; el supuesto de 1.85 nA supera su presupuesto.

Lista final de piezas:

- 6×1.5 MΩ Yageo RT1206BRD071M5L; 910 kΩ RT1206BRD07910KL; 100 kΩ RT1206BRD07100KL.
- 3×100 pF/2 kV CCTC TCC1206COG101J202FT; 3×3.3 kΩ antipulso, MPN pendiente.
- C0G 330 pF y 3.0 nF, MPN/rating pendientes.
- Nexperia 74HCT4051; un OPA2192 doble para buffer X0+A; una sección TMUX4053.
- 91 kΩ/10 kΩ, 0.1%, 25 ppm/°C: ganancia real **×10.1**.
- Frontera conservada: 3×33 kΩ, BAV199 y 100 Ω de X0, GDT+MOV. Rama X1 retirada solamente en S12c.

Dudas pendientes: espera de 20 V —los dos casos refinados cumplen a 3 ms—; modo común y acoplo del OPA2192 doble; fuga real; nueve refinamientos inconclusos; curvas de impulso, MPN y ensayo ΔR≤1%. El condensador de 330 pF alcanza 47.68 V y necesita rating confirmado.