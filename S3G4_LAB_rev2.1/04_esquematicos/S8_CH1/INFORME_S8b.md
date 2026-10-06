# Informe S8b — CH1 cableado, con símbolos y huellas propios

Sesión de Claude Code (Sonnet 5.5) sobre `04_esquematicos/kicad/`, rama `ai/s8-ch1-esquema`, 5 oct 2026. Encargo: `ENCARGO_KONNECT_S8b.md`.

**Resumen.** El redibujo cableado ya estaba en la rama cuando empecé: lo hizo una sesión anterior el 4 oct (commits `aa9bdd8` y `b9d4898`) y no dejó informe, vistas ni comprobaciones. Yo lo he auditado contra el encargo, he corregido lo que no cumplía (rótulos de bloque perdidos, 92 textos que se pisaban) y he hecho las tres comprobaciones y las vistas. **Una cosa no se ha podido hacer con Konnect: el cajetín** (ver «Dudas»).

## Commits (rama `ai/s8-ch1-esquema`, sin push)

| Commit | Contenido |
|---|---|
| `487b0d0`, `3ac0273` | (sesión anterior) símbolos y huellas propios de CH1, DNP de C103, C125/C126 a 25 V, huella del trimmer |
| `aa9bdd8` | (sesión anterior) CH1 redibujado con cables, uniones y símbolos de alimentación |
| `b9d4898` | (sesión anterior) desacoplos verticales junto a su CI, etapa final reordenada |
| `eb989e2` | rótulos de bloque restituidos y valores/referencias de los pasivos reubicados |
| (este) | resto de textos, netlist, PDF, vistas, ERC, informe y diario |

## Lo que encontré al auditar el redibujo

Cumplía: K101 = `s3g4:TQ2SA-5V-Z`, SW101 = `s3g4:SS23H37L6`, J101 y VC101 con sus huellas propias, sin la `Nota` de «provisional»; 296 cables, 81 uniones, 50 símbolos `power:` con los nombres de red del encargo, 10 etiquetas globales con 9 nombres (RELAY_COM dos veces, en K101 y en D104) y todas las redes `CH1_*` con una etiqueta local; todo en rejilla de 1.27 mm (0 símbolos o extremos de cable fuera).

No cumplía:

1. **Se habían perdido los rótulos de bloque y la nota del §5** («se conservan»): el `.kicad_sch` no tenía ningún texto. Los he vuelto a poner (bloques 1–9 y la nota «ABIERTO / CONTRADICCIONES»). De la nota quité lo que ya está resuelto: huella del TQ2SA, símbolos provisionales de K101/SW101, C125/C126 a 25 V y el DNP de C103.
2. **Textos que se pisan:** el detector nuevo `comprobar_textos_s8b.py` encontró **92 solapes** (referencia y valor de los pasivos verticales encima del cuerpo y entre sí, C101 con C102, desacoplos con el nombre del CI, valores de los CI cruzados por cables, etc.). Ahora hay **0**.

## Herramientas de Konnect y limitaciones

Usadas en esta sesión (no repetí el cableado; del redibujo anterior no tengo su registro de llamadas): `add_schematic_text`, `edit_schematic_component` con `field_placements` (≈50 llamadas), `batch_delete`, `add_wire` / `delete_schematic_wire`, `add_schematic_net_label` / `delete_schematic_net_label`, `get_schematic_layout`, `check_schematic_overlaps`. Para cables, uniones, símbolos de alimentación y cambio de símbolo Konnect tiene `add_wire`, `batch_add_wire`, `add_junction`, `add_power_symbol` y `replace_component`: no hizo falta simular el cableado con etiquetas.

Limitaciones:

- **No hay herramienta para el cajetín** (`title_block`). Es lo único del encargo que queda sin hacer.
- `field_placements` sólo mueve x, y, rotación y oculta; no cambia la justificación ni el tamaño de letra. La rotación de un campo es **relativa al símbolo** (un campo con 90° en un símbolo girado 90° se ve horizontal), y con justificación «left» el ancla de un campo girado queda en el extremo derecho. Lo descubrí al medir; la posición de cada campo la calculé con el SVG de `kicad-cli`.
- `render_schematic_png` sólo da la hoja entera. Las vistas por bloque salen del PDF de `kicad-cli` recortado con PyMuPDF (`kicad-cli` no exporta PNG).
- Textos largos de dos condensadores en paralelo (C101 ∥ C102, 20 mm de valor con 15 mm de paso) no caben en horizontal: sus **valores van en vertical** bajo los condensadores.

## Comprobaciones (con salida)

1. **`python ../S8_CH1/verificar_s8.py`** tras exportar `s8_ch1.net`: **código 0**. «Esperado: 89 piezas (76 de dos terminales), 229 pines, 56 redes (40 propias de CH1, 16 globales), 4 no-connect. Netlist: 89 piezas, 56 redes. Sin diferencias: cada pin de cada pieza está en la red que da la tabla.»
2. **`kicad-cli sch erc`:** **15 violaciones frente a 12 en S8** (`erc_s8b.json`, `erc_s8b.rpt`). Cuenta no cumplida, con la causa:

   | Tipo | S8 | S8b |
   |---|---|---|
   | `isolated_pin_label` (globales de otras hojas con un solo pin) | 5 | 5 |
   | `pin_not_driven` (U102 S0–S2, vienen de `CH1_SENSEL_*`) | 3 | 3 |
   | `power_pin_not_driven` | 4 | **7** |

   Las 7 son una por riel (AGND, GND, +AFE_4V9, −AFE_4V9, +3V3, VREF_2V5, VDDA), ahora anotadas sobre el símbolo `power:` porque su pin es de entrada de alimentación y ninguna salida de esta hoja alimenta el riel. En S8 GND, +3V3 y VREF_2V5 no daban error porque sólo tocaban pines pasivos. Es la **misma clase** de aviso y desaparece cuando la hoja de alimentación aporte la salida del regulador; no añadí `PWR_FLAG`, como pide el encargo.
3. **Textos:** `python comprobar_textos_s8b.py` → «483 textos, 296 cables, 0 solapes».
4. **`s8_ch1.pdf`** regenerado y vistas en `vistas/` (abajo). Comprobación extra: `check_schematic_overlaps` da 6 coincidencias de cajas (cuatro símbolos `power:` que tocan por diseño el extremo de su resistencia o el CI, y C116 / AGND contra la caja de U101, que sólo es la caja, no el triángulo).

## Vistas (`S8_CH1/vistas/`, 300 dpi salvo la hoja)

`ch1_hoja_completa.png`, `ch1_1_entrada.png`, `ch1_2_rele_y_driver.png`, `ch1_3_sujecion_y_acoplo.png`, `ch1_4_buffer.png`, `ch1_5_escalera.png`, `ch1_6_ganancia.png`, `ch1_7_filtro.png`, `ch1_8_etapa_final.png`, `ch1_9_notas_abiertas.png`.

## Dudas

1. **Cajetín sin hacer.** Hay que rellenarlo en KiCad (*Archivo → Configuración de página*): Título «CH1 — canal rápido (AFE rev 2.1)», Empresa «S3G4 LAB», Revisión «S8b», Fecha la del día, Comentario 1 «Fuente: S8_CH1/CH1_PIEZAS_Y_REDES.md». No lo escribí a mano en el `.kicad_sch` por la regla del proyecto. La hoja es A2 apaisada.
2. **ERC 15 en vez de ≤ 12** (arriba). ¿Se acepta, o se prefiere un `PWR_FLAG` en la hoja de alimentación cuando exista?
3. **Los nombres de símbolo `LM6172` y `ADA4807-1`** de U103/U105 y U106 son el pinout de la librería (con `Nota` que lo aclara), no la pieza real: AD8039 y OPA836. Viene de S8; lo dejo.
4. **Trimmer SEHWA:** sigue sin identificarse el rotor en la hoja (pendiente heredado).
5. Los cuatro textos de C101/C102 en vertical y el AGND de C116 pegado al triángulo de U101 son lo más apretado de la hoja; legibles, pero si se prefiere más aire habría que mover piezas (y hacer cables nuevos), lo que no se hizo.
