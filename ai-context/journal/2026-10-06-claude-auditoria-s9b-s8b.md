# Auditoría S9-B y S8b — 6 oct 2026, Claude (Opus 5.5)

## S9-B (Codex, cerrado el 6 oct a las 02:00)
- Comprobado en un deck (mc7, dac_local) que VOA/VOB/VOFA/VOFB corregidos = originales + 2.986000 mV exactos. La orientación es `VOS IP IPR {VOS}` y XAMP entra por IPR, así que +IN efectivo = externo − VOS. Con el +2.986006 mV nativo, el offset total es −draw, uniforme ±3 mV. El razonamiento de signo de Codex es correcto.
- C9 recalculado desde resultados/s9b_op_corregido.csv: 483, 477, 483 y 477 de 500, y 471 conjunto. Los fallos de B son casi todos de recorrido negativo (14+3 en 5 mV/div, 23 en 50 mV/div; mínimo 4.33 div).
- A desde resultados/s9_k5op.csv, sin la fila nominal: 484, 488, 484 y 488 de 500; **conjunto 481/500 (96.2 %)**. Fallos de recorrido positivo.
- El intervalo de confianza del 95 % para 477/500 va aproximadamente de 93 % a 97 %, así que el «pasa por escala» de B es marginal.
- Recuperación máxima K6: A 1.41 µs (s9_k6rec.csv) y B 1.47 µs (acta); las dos ≤ 2 µs.
- Consumo por canal: A 62.7 mW y B 109.1 mW. Ruido peor: A 0.234 y B 0.286 %div.
- Veredicto: entrega coherente y reproducible. A domina en C9 conjunto, consumo y ruido. La decisión es de Keneth.

## S8b (sesión de Konnect, 5 oct, commits eb989e2 y 7381d0d)
- Netlist reexportada con kicad-cli 10: igual a s8_ch1.net salvo la fecha. verificar_s8.py da código 0.
- ERC reejecutado: 15 (7 power_pin_not_driven en #PWR001/004/006/007/009/019/040, 3 pin_not_driven y 5 isolated_pin_label). El informe lo explica bien.
- comprobar_textos_s8b.py: 0 solapes. Visualmente, en ch1_8_etapa_final.png, las etiquetas verticales CH1_VMID_LO y CH1_ROFF_MID cruzan textos de R131/R147 y R128, y el símbolo VREF_2V5 se pega a R130. El detector no compara etiquetas con campos. Es cosmético.
- Pendiente: cajetín (Keneth en KiCad), aceptar el ERC 15 y la unión con main. No se hizo push ni merge.
- 6 oct: Keneth eligió AD8039 para CH2/CH3; registrado en DECISIONS.

## Tabla de consumo G.3/G.4 rehecha (6 oct, Claude)
- `herramientas/calc_rieles.py`: el AFE pasa de 10 × 3.9 mA genéricos a 3 × (OPA810 3.7 + 4 × AD8039 1.0) = 23.1 mA por riel, más 3 × (OPA836 1.0 + VMID/DAC 0.2) mA en VDDM. Los relés pasan de 3 × 40 mA × 0.36 en BUS5 a 3 × 16 mA de mantenimiento en VDDM (LDO de 3.3 V tras BUS5).
- Resultado: M1 2.52 W y 6.6 h (antes 2.76 W y 6.0 h); M2 1.81 W y 9.2 h; M3 1.63 W y 10.2 h; M4 sin cambio; M5 2.04 W; M6 2.44 W. LM27762: 26/23 mA. BUS5: 153 mA.
- Corrección: el «≈ 0.16 W» de los relés (D-03 y el callout del 4 oct) era la potencia en el riel de 3.3 V. De la batería salen ≈ 0.28 W porque es un LDO tras el boost. Propuesta, sin decidir: mantenimiento desde el buck 3V3D, ≈ 0.18 W.
- Actualizados en el documento vivo: G.3 (tabla, nota, callout), G.4, RF-17, G.5, G.6 (≈ 0.11 W por canal + 0.09 W del relé), G.8, D-03 y la línea de meta.
