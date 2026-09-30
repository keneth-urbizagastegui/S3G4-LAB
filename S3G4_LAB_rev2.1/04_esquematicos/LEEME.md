# Esquemas de la rev 2.1

Aquí irán los esquemas de la rev 2.1, junto con su netlist y su lista de materiales.

- `kicad/`: esqueleto del proyecto KiCad 10 (carpetas de librerías, `.gitignore`, reglas para IA en `AGENTS.md`, `s3g4.kicad_dru` vacío). Todavía no contiene `.kicad_pro`/`.kicad_sch`/`.kicad_pcb`: se crean con *Archivo → Nuevo proyecto* dentro de esa carpeta, con nombre `s3g4`.

- Los redibujos de estudio (canales del DSO112, WAVE2, OpenScope y black_scope, y las secciones B y C) están dentro de las páginas HTML. Se generan con los `draw_*.py` de `../herramientas/`.
- Los esquemas de la rev 2.0 siguen en `Schematics/` y en `docs/netlist_hoja*.py`, en la raíz del proyecto.
