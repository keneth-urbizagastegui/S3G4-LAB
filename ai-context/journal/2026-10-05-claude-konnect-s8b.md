# S8b: CH1 cableado, auditoría y acabado (Claude Code, 5 oct 2026, noche)

- **Cambio:** encargo `ENCARGO_KONNECT_S8b.md`. El redibujo cableado (símbolos propios, cables, uniones y símbolos `power:`) ya estaba en la rama `ai/s8-ch1-esquema` desde el 4 oct (commits aa9bdd8 y b9d4898, sin informe). Esta sesión lo auditó y lo completó: rótulos de bloque y nota del §5 restituidos, 92 solapes de texto resueltos con Konnect (`edit_schematic_component`, `add_schematic_text`), netlist, ERC, PDF y vistas regenerados. Sin push.
- **Evidencia:** `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/INFORME_S8b.md`, `s8_ch1.net`, `s8_ch1.pdf`, `erc_s8b.json/.rpt`, `vistas/` y el detector `comprobar_textos_s8b.py`.
- **Pruebas:**
  - `verificar_s8.py` sale con 0: 89 piezas, 229 pines y 56 redes, sin diferencias.
  - `comprobar_textos_s8b.py`: 0 solapes (antes 92).
  - ERC: 15 violaciones frente a 12 en S8. Las 3 de más son `power_pin_not_driven` en GND, +3V3 y VREF_2V5, que ahora aparecen sobre el símbolo `power:`. No se añadió PWR_FLAG.
- **Pendientes:**
  - Cajetín (título, empresa, revisión S8b, fecha, comentario): Konnect no tiene herramienta; lo rellena Keneth en KiCad.
  - Decidir si se acepta el ERC de 15 o hay PWR_FLAG en la hoja de alimentación.
  - Auditoría de Claude con kicad-happy y unir la rama con `main`.
- **Notas:**
  - En `edit_schematic_component`, la rotación de un campo es relativa al símbolo y con justificación «left» el ancla de un campo girado queda en el extremo derecho.
  - No se tocaron STATE ni DECISIONS.
