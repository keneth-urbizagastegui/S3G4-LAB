# Referencia del DMM 2/9: HydraMeter 0.4 (7 oct 2026, Claude Opus 5.5)

- Keneth autorizó bajar el 34401A. La URL /us/ de keysight.com devolvió su web impresa en PDF (27 p); la /mu/ dio el Service Guide real (167 p, 2022). Guardado en `research_and_tests/Agilent_34401A/34401A_Service_Guide.pdf`.
- HydraMeter: netlist exportada con kicad-cli 10 desde los .kicad_sch (KiCad 8) y leída con un parser propio (scratchpad/kinet.py). El PDF del proyecto son imágenes sin texto.
  - Bitácora de hackaday de 2023, anterior a la v0.4: allí la entrada tenía diez resistencias y había un SSR. Manda la netlist.
  - Firmware leído: calibration.h, configuración del MCP3461R, autorango, ohmios y alterna.
- Hallazgos:
  - Arriba 1 MΩ (2 × 100 k + 2 × 400 k THT), con MOV 230 Vrms y GDT 75 V al borne COM y MOV 3.3 V en la toma.
  - Patas R12 9.1 M (fija), R13 100 k y R14 6.8 k con NL7WB66. Zin de 10.1 / 1.10 / 1.01 MΩ.
  - **Compensación nominal mal en ÷1.11: −9.4 % desde ≈ 530 Hz**, con los 70 pF de RT1 según el autor y sin contar RT3.
  - Ohmios: 9.5 V aislados, 4 R de rango con P-MOS, LMC7101 + P-MOS para medir la corriente, Q1 seguidor que limita la tensión del DUT; D1, F3 y R25 fuera de la medida; interruptor del panel.
  - Derivadores 10 mΩ (4 pines, COM en el pin de sentido), 0.33 Ω y 100 Ω, con 1N4007 en antiparalelo.
  - Firmware: tablas de calibración de 3 a 15 puntos. La alterna lleva un factor ×2 sin explicar; la corrección de ohmios por la entrada en paralelo está comentada.
- Redibujos con 0 solapes, revisados a la vista. Página publicada.
