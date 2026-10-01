# Esbozo de hardware para pasar a Altium

- Fecha: 2026-09-18, 18:30 hora local.
- Agente: Claude Code (Opus 5).
- Pedido: esbozo del hardware con los componentes elegidos para la integración del front-end: diagrama de bloques, esquema de cada bloque y conexión general entre hojas, legible y sin amontonar, como guía para dibujar en Altium.
- Fuentes: `docs/netlist_hoja00…10.py` (datos importados, no transcritos a mano), `docs/MAPA_PINES_FIRMADO.md`, `docs/S3G4-AFE_v1.0_frontend_analogico.html` §17–§20b.
- Cambio:
  - Nuevo `docs/esbozo_hardware_s3g4.html`, publicado también como artifact privado: https://claude.ai/artifact/N2QCUrWegFApQ51QXQWM1u
  - Generador reproducible en `docs/esbozo_hardware_gen/`: `dump.py` → `netlists.json`, luego `build.py <salida>`. `check.py` busca textos que se solapan o cruzan cables.
  - Las listas de componentes y los netlists de la página salen directamente de los `.py`.
- Evidencia: `check.py` da 0 solapes en las 14 figuras. No hubo revisión visual en navegador: el panel sólo muestra instantáneas reducidas de archivos locales.
- Hallazgos en los netlists. Ningún `.py` fue modificado; hay que decidir cada corrección:
  1. `R1004_HDR` (hoja 10) une `NET_VDDA` con `NET_VCC_P5`: sería un cortocircuito de 3.3 V a 5 V.
  2. Las bobinas de los relés van de `CTRL_*` (salida del TPL7407, que sólo hunde corriente) a `GND_RELAY` en las hojas 04, 05 y 08, así que nunca se energizan.
  3. `U1002` usa 8 canales, pero el TPL7407L tiene 7.
  4. Los 74HC595 a 3.3 V gobiernan CD405x con VDD = 5 V; V_IH es 3.5 V. Falta verificarlo.
  5. `SR_*`, `I2C_*` y `RST_GPIO` no tienen pin del MCU en el mapa firmado ni en `CABLEADO_TOP`.
  6. DUDA-00-01 (origen de la guarda) sigue provisional.
  7. La hoja 01 no tiene netlist de componentes.
- Pendiente: que el usuario confirme las correcciones 1 a 5 antes de dibujar las hojas 04, 05, 08 y 10 en Altium. El punto 5 reabre el mapa firmado.
- Producto: no se tocó firmware, `.ioc`, PCB ni el proyecto de Altium.
