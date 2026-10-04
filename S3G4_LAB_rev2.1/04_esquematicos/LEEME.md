# Esquemas de la rev 2.1

Aquí van los esquemas de la rev 2.1, junto con su netlist y su lista de materiales.

- `S8_CH1/` (4 oct): paquete para dibujar CH1 en una hoja plana. `CH1_PIEZAS_Y_REDES.md` es la fuente de piezas, pines y redes (pinouts verificados con las hojas de datos); `ENCARGO_KONNECT_S8.md`, el encargo para la sesión de Claude con Konnect; `bom_ch1.py` genera `CH1_BOM_precios.csv` (códigos LCSC y precios). La jerarquía de hojas se hará al final, al estilo del OpenScope.

- `kicad/`: proyecto KiCad 10.0.6 `s3g4`, creado el 30 sep 2026 y todavía **vacío**: esquemático sin hojas, PCB de 2 capas por defecto, sin contorno y con `s3g4.kicad_dru` sin reglas. Incluye las carpetas de librerías propias (`lib/`), el `.gitignore`, las reglas para IA (`AGENTS.md`) y el MCP de Konnect (`.mcp.json`, sólo disponible en sesiones de Claude abiertas en esa carpeta).
  - Antes de dibujar: stackup de 4 capas, contorno y clases de red del AFE con sus reglas DRC. Ver `../06_plan/PLAN.md`, paso 9.
  - Detalle del entorno y sus trampas: `ai-context/journal/2026-09-30-claude-entorno-kicad10-ia.md`.

- Los redibujos de estudio (canales del DSO112, WAVE2, OpenScope y black_scope, y las secciones B y C) están dentro de las páginas HTML. Se generan con los `draw_*.py` de `../herramientas/`.
- Los esquemas de la rev 2.0 siguen en `Schematics/` y en `docs/netlist_hoja*.py`, en la raíz del proyecto. Son referencia, no base: sus netlists tienen fallos sin corregir (`ai-context/journal/2026-09-18-claude-esbozo-hardware.md`).
