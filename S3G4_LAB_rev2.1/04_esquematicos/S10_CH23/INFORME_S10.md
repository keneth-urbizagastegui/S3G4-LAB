# Informe S10 — CH2 y CH3 en KiCad

- Autor: Claude Code (Sonnet 5.5, Konnect), 6 oct 2026. Rama `ai/s10-ch23-esquema`, sin push.
- Resultado: `ch2.kicad_sch` y `ch3.kicad_sch` dibujadas (87 piezas cada una, A2 apaisada, misma disposición que CH1), colgadas de la raíz con dos símbolos de hoja (`CH2`, `CH3`, sin pines). CH1 no se tocó. Antes de empezar se commiteó tal cual el estado de la raíz guardado por Keneth (88151ab), por su decisión.

## Herramientas usadas y límites de Konnect

- Usadas: `add_hierarchical_sheet`, `batch_place_components`, `batch_add_wire`, `batch_add_junction`, etiquetas/`add_no_connect`, `add_component_annotation`, `edit_schematic_component` (referencias, valores, posiciones de texto), `batch_delete`, `add_schematic_text`, `render_schematic_png`; `kicad-cli` para netlist, ERC y PDF.
- **No hay copiar/pegar entre hojas.** Cada hoja se reconstruyó pieza a pieza y cable a cable desde la geometría de CH1.
- **Campos personalizados (LCSC, MPN, Nota):** `batch_edit_schematic_components` no los crea; se añadieron uno a uno con `add_component_annotation`.
- **Rutas de instancia:** `duplicate_sheet`/`add_hierarchical_sheet` sobre un archivo existente añaden rutas en vez de sustituir, y Konnect rechaza colocar piezas si el hijo no tiene exactamente la ruta actual. `ch3` se regeneró desde una hoja en blanco (ruta única). **`ch2` conserva una ruta obsoleta (5888b09f…)**: KiCad la limpia al abrir y guardar.
- `add_power_symbol` solo vale para símbolos estándar; AGND, ±AFE_4V9 y VREF_2V5 se colocaron con `batch_place_components` (`power:GNDA`, `-5V`, `+5V`, `+2V5`) y Value = nombre de red, como en CH1.
- `batch_edit` con `fields.Reference` no actualiza `instances` (archivo «stale»): se usó `edit_schematic_component(new_reference)`.
- Los `#PWR` se renumeraron (ch2 201–250, ch3 301–350) porque duplicados entre hojas dan avisos de anotación.
- No hay herramienta para mover o editar textos: el título del bloque 8 se borró y se volvió a añadir (x=312). El **cajetín no se pudo rellenar**: lo hace Keneth en KiCad (título «CH2 — canal lento (AFE rev 2.1)» / «CH3 — …», empresa «S3G4 LAB», revisión «S10», comentario «Fuente: S10_CH23/CH23_PIEZAS_Y_REDES.md»).

## Comprobaciones

1. **Netlist** → `s10_ch23.net`; `verificar_ch23.py`: CH1 89 piezas, CH2 87, CH3 87, 56 redes cada una, **0 diferencias, código 0**. R_38/R_39 no dibujadas; R223/224 = 2.2 k (C4190), R248/249 = 150 (C22808), R225/226 = 1.1 k (C22764), y lo mismo en 3xx.
2. **ERC** (`erc_s10.json`): 31 = 7 `power_pin_not_driven` (rieles compartidos) + 9 `pin_not_driven` (3 por canal) + 15 `isolated_pin_label` (5 por canal). Ningún otro tipo; sin aviso de anotación.
3. **Textos** (`comprobar_textos_s8b.py`): s3g4 0, ch2 0 y ch3 0 solapes (tras copiar las posiciones de Reference/Value de CH1 y reubicar el bloque 8 y dos AGND). Revisión visual de etiquetas frente a textos de pieza hecha sobre el PNG de ch3: sin pisados evidentes a esa escala; conviene un repaso en KiCad.
4. **Exportaciones:** `s10_ch2.pdf`, `s10_ch3.pdf`, `vistas/ch2_completa.png`, `vistas/ch3_completa.png`.

## Dudas / contradicciones anotadas

- RFILT1 = 2.35 kΩ (2.2 k + 150) frente a 2.37 kΩ simulado (−0.84 %), ya aceptado en la tabla.
- C207/C307: la tabla da ≈ 8.7 pF; la BOM (`CH1_BOM_preclos.csv`) da 8.2 pF (C54431614). Se dibujó la tabla; se selecciona en prueba.
- VCHECK: divisor 12.4 k / 100 Ω como en CH1, según la nota de contradicciones de CH1.
- ABIERTO: ADC3/ADC4 sin pin, canal del DAC de offset, disparo PE9/PE15.
- Símbolos de biblioteca: LM6172 para AD8039 (campo Value AD8039ARZ-REEL7), ADA4807 para OPA836, BAV99 para BAV199.
- Pendiente: Keneth abre y guarda ch2/ch3 en KiCad, rellena cajetín; auditoría de Claude (sesión principal).
