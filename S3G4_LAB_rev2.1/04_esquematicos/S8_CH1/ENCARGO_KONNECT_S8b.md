# Encargo S8b — CH1 como esquema cableado, con símbolos y huellas propios

Para la sesión de Claude Code abierta en `S3G4_LAB_rev2.1/04_esquematicos/kicad/` (Konnect). Lo prepara la sesión principal de Claude, 4 oct 2026. Sigue a S8 (`INFORME_S8.md`, `AUDITORIA_CLAUDE_S8.md`).

**Pedido de Keneth:** «quiero que se vea como un esquemático conectado, no solo los componentes y netlabels». La hoja de S8 es correcta eléctricamente (`verificar_s8.py` da 0), pero cada pin lleva una etiqueta y no se ve el recorrido de la señal.

## Antes de empezar

1. Lee los `AGENTS.md` (el de la raíz y el de `kicad/`), `CH1_PIEZAS_Y_REDES.md` (la fuente, sin cambios de redes), `INFORME_S8.md` y `AUDITORIA_CLAUDE_S8.md`.
2. Rama **`ai/s8-ch1-esquema`** (ya existe; último commit `487b0d0`). `git status` limpio en `kicad/`. KiCad **cerrado** mientras Konnect escribe.
3. Comprueba qué herramientas de Konnect hay para **cables, uniones, símbolos de alimentación y cambio de símbolo**. **Si Konnect no puede trazar cables, para y avisa**: no simules el cableado con etiquetas.

## 1. Símbolos y huellas propios (ya están en la librería `s3g4`)

Los generó `lib/gen/gen_ch1_parts.py` (cotas en su cabecera):

| Ref | Cambiar a | Huella |
|---|---|---|
| K101 | símbolo `s3g4:TQ2SA-5V-Z` (sustituye a `Relay:G6H-2`) | `s3g4:Relay_Panasonic_TQ2SA_SMD` (viene en el símbolo) |
| SW101 | símbolo `s3g4:SS23H37L6` (sustituye a `Switch:SW_DP3T`) | `s3g4:SW_Slide_DP3T_XKB_SS23H37` (viene en el símbolo) |
| J101 | se queda `Connector:Conn_Coaxial` | `s3g4:BNC_Kinghelm_KH-BNC50-3511_Horizontal` |
| VC101 | se queda `Device:C_Trim` | `s3g4:C_Trimmer_SEHWA_STC3MA06_4.5x3.2mm` |

- Conserva la referencia, el valor y los campos (`LCSC`, `MPN`, `Nota`) de cada pieza.
- Quita la `Nota` de «símbolo provisional» de las cuatro.
- Los números de pin no cambian: K101 sigue la tabla del §2.2 y SW101 la del §2.3.

## 2. Redibujo cableado

**Regla de redes:** las redes y sus nombres **no cambian**. Cada red `CH1_*` conserva **al menos una etiqueta local** sobre su cable, para que se llame igual; `verificar_s8.py` tiene que seguir saliendo con 0.

**Cómo dibujar:**

- Hoja A2 apaisada. La señal va de izquierda a derecha y cada bloque se lee de izquierda a derecha.
- **Dentro de un bloque, todo con cables:** los pines se unen con cables, con un punto de unión en cada derivación en T. Nada de etiquetas pegadas a cada pin.
- **Entre bloques:** cable si están al lado y el cable queda corto y limpio. Si no, una etiqueta local en cada extremo con el nombre de la red.
- **Alimentaciones con símbolos de alimentación de KiCad** (`power:`), no con etiquetas globales: `AGND`, `GND`, `+AFE_4V9`, `-AFE_4V9`, `VDDA`, `VREF_2V5` y `+3V3`. El nombre de la red tiene que quedar idéntico; si el símbolo `power:` estándar no lo permite, usa uno con el Value cambiado y comprueba en la netlist que la red se llama igual.
- **Etiquetas globales** solo para lo que viene de otras hojas: `CH1_ADC`, `CH1_OFFSET_DAC`, `CH1_SENSEL_A/B/C`, `CH1_K_CTRL`, `CH1_CPL_A/B` y `RELAY_COM`.
- Cuadrícula de 1.27 mm. Sin cables que pasen por encima de pines, sin textos que se pisen y con los valores legibles junto a cada pieza.
- **Las parejas serie/paralelo del §2.10 se dibujan juntas**: en paralelo, una al lado de la otra entre los mismos dos nodos; en serie, una a continuación de la otra.

**Disposición por bloque.** Es una guía, no una plantilla exacta:

1. **Entrada.** J101 a la izquierda; su centro alimenta un nodo `CH1_BNC` del que salen dos ramas:
   - el **divisor**: R101 ∥ C101 en horizontal, luego R102 ∥ C102 ∥ VC101 ∥ C103 hasta el nodo `CH1_TAP`, y de `CH1_TAP` a masa R103 ∥ C104 ∥ C105 en vertical;
   - la **rama ×1**, debajo: R104 – R105 en serie, con C106 en paralelo con las dos, hasta `CH1_X1`.

   La malla de J101 va a `AGND`.
2. **Relé K101.** `CH1_TAP` entra por NC (2), `CH1_X1` por NO (4) y COM2 (8), y la réplica R106 ∥ C107 cuelga de NC2 (9) hacia `AGND`. COM1 (3) sale como `CH1_SEL`. El driver (Q101, D104, R135, R136) va justo debajo de la bobina.
3. **Nodo `CH1_SEL`.**
   - D101 en vertical hacia `+AFE_4V9` y `-AFE_4V9`.
   - SW101: polo A con T1 (`CH1_AC`), T2 (`AGND`) y T3 (`CH1_SEL`), y C108 entre `CH1_SEL` y `CH1_AC`. Su COM es `CH1_CPL_COM`.
   - R107 a `AGND` y R108 hacia el buffer.
   - El polo B, con sus pull-ups R133/R134, aparte, debajo.
4. **Buffer U101** como seguidor: la salida realimentada a IN− con un cable y el desacoplo pegado a sus pines de alimentación.
5. **Escalera.** Cadena vertical desde `CH1_BUF_OUT` hasta `AGND`, con las tomas `CH1_LAD1…5` por cable a las entradas Y1…Y5 de U102. Y0 desde `CH1_BUF_OUT`, Y6 a `AGND` y Y7 desde el divisor VCHECK (R115/R116).
6. **Ganancia.** U103A y U103B como no inversores. R_SER (470 Ω) en la entrada +, D102/D103 entre las entradas, RF de la salida a IN− y RG de IN− a `AGND`.
7. **Filtro.** Dos Sallen-Key de ganancia 1, dibujados de la forma estándar: R – R en serie hacia IN+, C de la unión a la salida y C de IN+ a masa.
8. **Etapa final.** U106 como sumadora inversora: R_IN y R_OFF hacia `CH1_SUM`, R_F ∥ C_F de la salida a `CH1_SUM`, VMID con su divisor y su condensador en IN+, y salida → R132 → `CH1_ADC` con C115 a masa.
9. El **desacoplo** de cada CI, junto a sus pines de alimentación.

**Cajetín:**
- Título «CH1 — canal rápido (AFE rev 2.1)».
- Empresa «S3G4 LAB».
- Revisión «S8b».
- Fecha.
- Comentario «Fuente: S8_CH1/CH1_PIEZAS_Y_REDES.md».

Los rótulos de bloque y la nota del §5 se conservan.

## 3. Comprobaciones (las tres, con salida)

1. `python ../S8_CH1/verificar_s8.py` después de exportar la netlist a `../S8_CH1/s8_ch1.net`: **código 0**, con las mismas 89 piezas, 229 pines y 56 redes.
2. `kicad-cli sch erc`: no puede aparecer **ninguna violación nueva** respecto a las 12 de S8. Puede bajar si los símbolos de alimentación resuelven alguna, pero no añadas PWR_FLAG. Anota cualquier cambio.
3. Exporta `../S8_CH1/s8_ch1.pdf` y una PNG de cada bloque a `../S8_CH1/vistas/`, para que el auditor compruebe la legibilidad.

## Reglas

- **No cambies valores, redes ni referencias.** Las contradicciones se anotan.
- No edites el `.kicad_sch` a mano. No uses `set_active_layer`. No toques el PCB.
- Commits pequeños en `ai/s8-ch1-esquema`, sin push. No toques `STATE.md` ni `DECISIONS.md`; escribe tu diario.

## Entrega

`../S8_CH1/INFORME_S8b.md` con:
- los commits;
- qué herramientas de Konnect usaste y sus limitaciones;
- el resultado de `verificar_s8.py` y el ERC;
- la lista de vistas;
- dudas.
