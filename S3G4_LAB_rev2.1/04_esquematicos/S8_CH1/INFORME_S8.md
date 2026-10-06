# Informe S8: CH1 dibujado en KiCad con Konnect

- Autor: Claude Code (sesión en `04_esquematicos/kicad/`), 4 oct 2026. Fuente única: `CH1_PIEZAS_Y_REDES.md`. Los códigos LCSC y los encapsulados salen de `CH1_BOM_precios.csv`.
- Herramientas: Konnect 0.12.1 y KiCad 10.0.6 (`kicad-cli`). KiCad no estaba abierto: Konnect escribió el fichero sin que hubiera un editor concurrente.
- El MCP `s3g4-context` no conectó en esta sesión, así que se leyeron los ficheros directamente.

## Rama y commits

Rama `ai/s8-ch1-esquema`, creada desde `main`, sin push.

- `b9f1be1`: fija el guardado trivial que KiCad 10 había dejado en `s3g4.kicad_pro` y `.kicad_sch` (había cambios sin commit en `main`) y excluye `.history/`.
- `36ccb06`: dibuja la cadena de CH1.
- `fa9dad8`: añade rótulos, notas, colocación de textos, netlist, ERC y `verificar_s8.py`.

La prueba mínima de escritura de Konnect se hizo antes de dibujar: R + etiqueta, ERC sin violaciones y netlist correcta. Se deshizo con git. No se usó `set_active_layer` y no se tocó el PCB.

## Hoja

`s3g4.kicad_sch` es una hoja plana A2 apaisada, organizada en dos bandas de izquierda a derecha:

- **Banda superior:** bloques 1 a 5 y el 9 (driver), este último en un recuadro bajo K101.
- **Banda inferior:** bloques 6 a 8 y el texto del §5 con las contradicciones.

Conexiones:

- Cada pin lleva una etiqueta, sin cables largos.
- Las redes `CH1_*` usan etiquetas locales.
- Las del §1 usan etiquetas globales.
- Cada pareja del §2.10 está en filas contiguas y cada desacoplo, junto a su CI.

En `s8_ch1.pdf` está la exportación de la hoja.

## Símbolos

| Pieza | Símbolo | Estado |
|---|---|---|
| R, C | `Device:R`, `Device:C` | estándar |
| U101 | `Amplifier_Operational:OPA810xDBV` | número de pieza exacto; pinout = tabla 5-1 |
| U102 | `74xx:74HC4051` | exacto; VEE visible (pin 7 a `-AFE_4V9`) |
| U103, U105 | `Amplifier_Operational:LM6172` (unidades A, B y alimentación) | sustituto con el mismo pinout SOIC-8 doble que el AD8039 (p. 1, fig. 3) |
| U106 | `Amplifier_Operational:ADA4807-1` | sustituto con el mismo pinout SOT-23-6 que el OPA836 (tabla 6-1, pin 5 = PD/~DISABLE) |
| D101 | `Diode:BAV99` (Value BAV199) | mismo pinout que el BAV199 (tabla 2: 1 = A1, 2 = K2, 3 = común); se comprobó con el dibujo del símbolo |
| D102, D103 | `Diode:BAV99` | exacto; pinout de la hoja **NO VERIFICADO** (no hay PDF en el proyecto) |
| Q101 | `Transistor_FET:2N7002` (1 G, 2 S, 3 D) | exacto; **NO VERIFICADO** con la hoja (no hay PDF) |
| D104 | `Diode:1N4148W` (1 K, 2 A) | exacto; **NO VERIFICADO** con la hoja |
| **K101** | `Relay:G6H-2` | **provisional**; numeración idéntica a la del TQ2SA (1+/10 bobina, 3-2-4 y 8-9-7, 5 y 6 sin función) |
| **SW101** | `Switch:SW_DP3T` | **provisional**; los números de pin siguen el §2.3, pero el dibujo pone el común en los pines 3/7 (en la pieza es 2/6). Hay una nota en la hoja |
| **J101** | `Connector:Conn_Coaxial` | **provisional** (centro = 1, cuerpo = 2) |
| **VC101** | `Device:C_Trim` | **provisional** |

No se creó ningún símbolo en `lib/s3g4.kicad_sym`. Cada pieza sustituta o provisional lleva el campo `Nota`.

## Huellas

- **Asignadas (KiCad estándar):**
  - `R_1206`: R101, R102, R104, R105 y R106.
  - `C_1206`: C106 y C107.
  - `R_0805`: R103.
  - `C_0805`: C102, C125 y C126.
  - `R_0402`: R115 y R116.
  - `C_0402`: C116…C124.
  - 0603: el resto de R y C, incluido C103.
  - `SOT-23-5`: U101.
  - `SOT-23-6`: U106.
  - `SOIC-8`: U103 y U105.
  - `SOIC-16`: U102.
  - `SOT-23`: D101, D102, D103 y Q101.
  - `D_SOD-123`: D104.
- **Vacías:** J101, VC101, K101 y SW101.

Los encapsulados de R103, C102, R115 y R116 vienen de la BOM; la tabla .md no los da.

## Campos

- `LCSC` está en todas las piezas salvo C103 (DNP, sin código).
- `MPN` solo aparece donde la tabla o la BOM lo dan.
- C107 lleva `Nota = seleccionar en prueba`.
- **C103 no tiene el atributo DNP:** Konnect 0.12.1 no lo expone y el `.kicad_sch` no se edita a mano. Lleva Value «DNP» y una nota. **Pendiente: marcar DNP en la GUI.**

## ERC (`kicad-cli sch erc`, `erc_s8.rpt`)

Da 12 violaciones (7 errores y 5 avisos), **todas por bloques que aún no existen**. No se ha añadido ningún PWR_FLAG.

- `power_pin_not_driven` ×4: los rieles `+AFE_4V9` (U101.5), `-AFE_4V9` (U101.2), `AGND` (U102.8) y `VDDA` (U106.6) no tienen fuente en esta hoja.
- `pin_not_driven` ×3: U102 S0/S1/S2 (`CH1_SENSEL_A/B/C` vienen del 74HCT595, que está en otra hoja).
- `isolated_pin_label` ×5: las globales `CH1_K_CTRL`, `CH1_OFFSET_DAC` y `CH1_SENSEL_A/B/C` tienen un solo pin en esta hoja.

No hay errores de cableado ni de pines sin conectar.

## Netlist y verificación

- `kicad-cli sch export netlist` genera `s8_ch1.net`.
- `python verificar_s8.py` sale con **código 0**:

```
Esperado según la tabla: 89 piezas (76 de dos terminales), 229 pines, 56 redes (40 propias de CH1, 16 globales), 4 no-connect
Netlist: 89 piezas, 56 redes
Sin diferencias: cada pin de cada pieza está en la red que da la tabla.
```

Qué hace el script:

- Calcula lo esperado a partir de las tablas del .md (pinouts incluidos).
- Comprueba que la fila resumen de SW101 cuadra con su tabla de pines y que el §3 coincide con las tablas.
- Compara el LCSC con el CSV.
- Las únicas suposiciones de numeración que no salen del .md son J101 (centro = 1) y D104 (cátodo = 1); el script las imprime.
- Prueba negativa: al renombrar una red o cambiar un pin en una copia de la netlist, sale con 1 y lista las diferencias.

## Dudas y contradicciones (anotadas; no se cambió nada)

1. **VCHECK:** S7/S7b simularon 1 kΩ a masa; se dibuja el divisor 12.4 k / 100 Ω (ya anotado en el .md).
2. **C107:** el .md dice ≈ 8.7 pF ≥ 200 V; la BOM da 8.2 pF 1 kV (C54431614). Se dibujó 8.7 pF con ese código.
3. **C125/C126:** el .md (§4) dice 16 V; la BOM, 25 V (C15850).
4. **Encapsulados:** R103 y C102 son 0805, y R115 y R116 son 0402, según la BOM; el .md no lo dice.
5. **Hojas que faltan:** no hay hoja de 2N7002, BAV99 ni 1N4148W en el proyecto; sus pinouts siguen el estándar de KiCad.
6. **K101:** sus pines 5 y 6 son `no_connect` ocultos en el símbolo G6H-2, así que no llevan marca X visible. El pin 7 sí la lleva.

## Pendiente

- Marcar C103 como DNP en KiCad.
- Crear los símbolos y huellas propios de K101, SW101, J101 y VC101 cuando Keneth lo pida.
- Verificar los pinouts del 2N7002 y del BAV99/1N4148W con sus hojas.
- Auditoría con kicad-happy.
