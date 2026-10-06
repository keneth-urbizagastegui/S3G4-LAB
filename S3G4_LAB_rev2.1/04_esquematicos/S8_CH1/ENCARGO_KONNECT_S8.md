# Encargo S8 — dibujar CH1 en KiCad con Konnect

Para una sesión de Claude Code abierta **en `S3G4_LAB_rev2.1/04_esquematicos/kicad/`**, que es donde se cargan las herramientas de Konnect (`.mcp.json` de esa carpeta). La preparó otra sesión de Claude el 4 oct 2026, que es la que audita.

## Antes de empezar

1. Lee `AGENTS.md` de la raíz y el de `kicad/`, `ai-context/START.md`, `ai-context/STATE.md` y, entero, `../S8_CH1/CH1_PIEZAS_Y_REDES.md`: **es la única fuente de piezas, valores, pines y nombres de red**. No saques nada de memoria ni del documento vivo directamente.
2. Comprueba que las herramientas de Konnect están cargadas. Si no lo están, para y dilo.
3. `git status` del proyecto KiCad limpio; crea la rama **`ai/s8-ch1-esquema`** desde `main`. Nunca trabajes en `main`.
4. KiCad abierto con el proyecto `s3g4`, el esquemático **guardado**; un solo actuador MCP (solo Konnect).
5. **La escritura de Konnect nunca se ha probado en KiCad 10.0.6.** Primero una prueba mínima: coloca una resistencia, cablea una etiqueta, guarda, ejecuta `kicad-cli sch erc` y comprueba que el fichero se abre bien. Si falla, para, deshaz con git y avisa. **No uses `set_active_layer`** (incidencia #610) y no toques el PCB ni el stackup.

## Qué dibujar

- **Una sola hoja plana** (`s3g4.kicad_sch`), sin hojas jerárquicas. Tamaño A3 o A2 apaisado, lo que quepa legible.
- La cadena de izquierda a derecha y en bloques con un rótulo de texto cada uno, en este orden:
  1. Entrada: J101, divisor ÷100 y rama ×1, réplica.
  2. Relé K101 (TQ2SA-5V-Z; la bobina tiene polaridad).
  3. Sujeción D101, acoplo SW101, C_AC, R_BIAS y R_PROT.
  4. Buffer U101.
  5. Escalera, VCHECK y U102.
  6. Ganancia U103 (A y B, con R_SER y BAV99).
  7. Filtro U105 (A y B).
  8. Etapa final U106, VMID y red del pin.
  9. Driver del relé (Q101, D104, R135, R136), junto a K101 o en un recuadro aparte.
- Etiquetas globales para todo lo del §1 de `CH1_PIEZAS_Y_REDES.md`. Etiquetas locales con los nombres `CH1_*` exactos para las redes propias (sin inventar otros).
- Referencias **exactamente** las de la tabla (R101…R149, C101…C126, D101…D104, Q101, U101…U106, K101, SW101, J101, VC101), incluidos el desacoplo y los pull-ups del §4 y las parejas serie/paralelo del §2.10 (cada pareja junta). Cada condensador de desacoplo se dibuja junto al CI que dice la tabla.
- Campos en cada pieza: `Value`, `Footprint`, `MPN` y `LCSC` cuando la tabla los dé; si no, déjalos vacíos (no busques códigos tú). C103 con el atributo DNP. C107 con el campo `Nota = seleccionar en prueba`.
- Lo abierto del §5 va como **texto en la hoja**, no como circuito inventado.

## Símbolos

- Usa los símbolos de las librerías estándar de KiCad 10 cuando exista el **número de pieza exacto** o uno con el mismo encapsulado y pinout. Comprueba siempre los números de pin del símbolo contra la tabla (los pinouts verificados citan página y tabla de la hoja).
- Unidades múltiples: AD8039 con sus unidades A, B y la de alimentación. 74HC4051 con la alimentación visible (VEE no es GND).
- Si una pieza no tiene símbolo adecuado (probable para el TQ2SA-5V-Z, SS23H37L6, trimmer SEHWA o BNC Kinghelm), usa un símbolo genérico de la librería estándar con el número de contactos correcto **y anota la pieza como «símbolo provisional»** en el informe. No crees símbolos en `lib/s3g4.kicad_sym` sin que Keneth lo pida.
- Huellas: sólo las que la tabla deja claras (1206, 0603 y los encapsulados de los CI). El resto, vacías y listadas.

## Comprobaciones al terminar (las tres, con la salida)

1. `kicad-cli sch erc` sobre `s3g4.kicad_sch`: informa los errores y avisos. Los que sean por bloques que todavía no existen (etiquetas globales sin origen, `power_in` sin fuente) se listan aparte; no los tapes con PWR_FLAG.
2. Exporta la netlist (`kicad-cli sch export netlist`) a `../S8_CH1/s8_ch1.net`.
3. Compara la netlist contra las tablas de `CH1_PIEZAS_Y_REDES.md` con un script en `../S8_CH1/verificar_s8.py`: cada pin de cada pieza en su red, sin redes de más ni de menos. **Los recuentos se calculan del fichero de tablas, no se escriben a mano.** El script sale con código 1 si hay diferencias.

## Reglas

- **No cambies valores ni topología.** Si algo de la tabla te parece mal o contradice una hoja de datos, anótalo y dibújalo tal cual.
- Las contradicciones se anotan, no se resuelven.
- Commits pequeños en `ai/s8-ch1-esquema`, sin push. No toques `ai-context/STATE.md` ni `DECISIONS.md`; escribe tu diario en `ai-context/journal/`.

## Entrega

En `../S8_CH1/INFORME_S8.md`:
- rama y commits;
- lista de símbolos usados (biblioteca:nombre) y cuáles son provisionales;
- huellas asignadas y vacías;
- resultado del ERC;
- salida de `verificar_s8.py` y su código de salida;
- dudas y contradicciones.

Después el auditor (Claude, en la sesión principal) revisa con `kicad-happy` (`analyze_schematic.py`) y con el script.
