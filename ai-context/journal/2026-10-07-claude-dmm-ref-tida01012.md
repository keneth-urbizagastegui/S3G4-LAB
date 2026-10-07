# Referencia del DMM 1/8: TIDA-01012 (7 oct 2026, Claude Opus 5.5)

- Keneth autorizó las descargas e incluir R6–R8.
  - TIDA-00879: tidubm4, tidrmi4, tidrmi5 y tidrmi7, en `research_and_tests/TIDA-00879/`.
  - 121GW: eevblog.com da 502 en download.php?id=11618, así que el esquemático se sacó de web.archive.org (2024id_; enero de 2018, 1 hoja). El manual de marzo de 2025 viene de eevblog.
  - Martin: `git clone` de MartinD-CZ/STM32F1-open-source-multimeter. Es la rev 1.5 con **STM32F373**, no F1.
- TIDA-01012: leída la guía (pp. 2–5, 24–54, 62–71) y la hoja 3 del esquemático por zonas.
  - Hallazgos clave: R16 de 10 MΩ fija y un SP3T TS5A3359 que elige la pata baja a COM. La toma vale ±50 mV en todos los rangos.
  - R17 de 499 kΩ (S2 manual) para 50 mV. R9 de 100 MΩ siempre.
  - **COM = IN_N = 1P35V_REF**: instrumento flotante a 2.7 V.
  - Derivadores con fuerza y sentido (TS3A24159), PTC de 0.2 A, OPA2313 + THS4531 (×44.2), ADS8885, REF3325 + RC de 3.4 Hz + OPA313 con RISO.
  - **Sin ohmios y sin protección de tensión.**
- Cálculos en calc_dmm_tida01012.py; 3 redibujos con 0 solapes (chk_dmm.py nuevo) revisados a la vista.
- Correcciones registradas en la página: el OPA333 solo sigue VCM; la conmutación es en las patas bajas, no en las tomas.
- Riesgo para la síntesis: en H una cuenta vale ≈ 1/12 de LSB del ADC5. En el TIDA vale 2.3 LSB de 18 bits.
