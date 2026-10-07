# DMM — arquitectura (7 oct 2026, Claude Opus 5.5)

- Leídos: RD-01…RD-10, el reparto de pines del DMM en la rev 2.0 (MAPA_PINES_FIRMADO: PD13/PD14 ADC5 diferencial, PB14 OPAMP5/COMP7) y la revisión del G473. Del TIDA-01012 se leyó el resumen: ADS8885 externo, OPA333, REF3325, conmutadores de baja tensión detrás del divisor de 10 MΩ, corriente hasta 50 mA.
- Keneth eligió las cuatro opciones recomendadas: mux, deriva cero externo, aguantar la red unos segundos y los rangos propuestos. Registrado en DECISIONS.
- Búsqueda en LCSC de una pieza de deriva cero: el filtro paramétrico de pcbparts no se aplicó (devolvió LM358 y similares). La elección queda para la sección H.
- Escrito `01_diseno/dmm_arquitectura.md` (borrador).

## Sección H (7 oct, más tarde)
- Pedido de Keneth: hacerlo como el osciloscopio, con camino de la señal, bloques, diagramas y especificaciones.
- Escritos y publicados `01_diseno/dmm_rev21.html` (artefacto 4iveEdvtCBTvhQj9jHjsvY) y `00_requisitos/especificaciones_dmm.html` (9wuyJcNBxPcee2dNuThttm).
- Pieza elegida por Claude, propuesta: OPA2188AIDR (LCSC C17271, 1.18 USD, stock 7115, ±2…±18 V, 6 µV, 8.8 nV/√Hz). Descartadas por coste o stock: OPA2187 (2.3 USD), ADA4522-2 (3.9 USD) y TLV2186 (38 nV/√Hz, stock 553).
- Detalle de diseño: ±19 999 cuentas = ±2 V diferenciales en el ADC5, por eso el driver es diferencial. RD-03 da unos 82 µV por nivel con ×1024, así que hay un margen de 1.2×. Es justo; S11 debe comprobarlo.
- Todas las cifras son de diseño, sin simular.
