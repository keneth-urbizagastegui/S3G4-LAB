# DMM — arquitectura (7 oct 2026, Claude Opus 5.5)

- Leídos: RD-01…RD-10, el reparto de pines del DMM en la rev 2.0 (MAPA_PINES_FIRMADO: PD13/PD14 ADC5 diferencial, PB14 OPAMP5/COMP7) y la revisión del G473. Del TIDA-01012 se leyó el resumen: ADS8885 externo, OPA333, REF3325, conmutadores de baja tensión detrás del divisor de 10 MΩ, corriente hasta 50 mA.
- Keneth eligió las cuatro opciones recomendadas: mux, deriva cero externo, aguantar la red unos segundos y los rangos propuestos. Registrado en DECISIONS.
- Búsqueda en LCSC de una pieza de deriva cero: el filtro paramétrico de pcbparts no se aplicó (devolvió LM358 y similares). La elección queda para la sección H.
- Escrito `01_diseno/dmm_arquitectura.md` (borrador).
