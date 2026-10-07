# Encargo S10 — CH2 y CH3 como hojas cableadas en KiCad

Para la sesión de Claude Code abierta en `S3G4_LAB_rev2.1/04_esquematicos/kicad/` (Konnect). Lo prepara la sesión principal de Claude el 6 oct 2026. Sigue a S8b: CH1 está cableado, verificado y unido en `main`.

## Antes de empezar

1. Lee los `AGENTS.md` (el de la raíz y el de `kicad/`), `../S10_CH23/CH23_PIEZAS_Y_REDES.md` (la fuente) y, como referencia de estilo, `../S8_CH1/INFORME_S8b.md`.
2. Crea la rama **`ai/s10-ch23-esquema`** desde `main`. `git status` limpio en `kicad/`. KiCad **cerrado** mientras Konnect escribe.
3. Comprueba qué herramientas de Konnect hay para **crear una hoja jerárquica** (símbolo de hoja en la raíz y su archivo `.kicad_sch`) y para **copiar o duplicar** piezas de una hoja a otra.
   - Si Konnect no puede crear hojas, **para y avisa**. Keneth las crea en KiCad (*Colocar → Hoja jerárquica*: `CH2` → `ch2.kicad_sch` y `CH3` → `ch3.kicad_sch`, a la derecha de CH1 en la raíz, sin pines) y tú sigues dibujando dentro.
   - No edites ningún `.kicad_sch` a mano ni con scripts.

## 1. Qué dibujar

- **`ch2.kicad_sch` y `ch3.kicad_sch`:** cada una, una copia de la hoja de CH1 de la raíz con las reglas del §2 de la tabla: referencias 2xx/3xx, redes `CH2_*`/`CH3_*` y las mismas etiquetas globales renombradas. Los rieles, las masas y `RELAY_COM` no cambian.
- **El filtro, según el §3:** R_23/R_24 a 2.2 kΩ (C4190), R_48/R_49 a 150 Ω (C22808), R_25/R_26 a 1.1 kΩ (C22764). **R_38 y R_39 no se dibujan.** Los condensadores no cambian.
- Hoja A2 apaisada, con **la misma disposición que CH1**: los mismos bloques en el mismo sitio, cables, uniones y símbolos `power:`. Una etiqueta local en cada red `CHn_*`, y etiquetas globales solo para lo que viene de otras hojas. Si se puede copiar la geometría de CH1, mejor que redibujar.
- Textos según el §4 de la tabla (rótulos, nota «ABIERTO», cajetín si Konnect puede).
- **La raíz solo gana los dos símbolos de hoja.** No toques CH1: ni piezas, ni cables, ni textos.

## 2. Comprobaciones (las cuatro, con salida)

1. Exporta la netlist del proyecto a `../S10_CH23/s10_ch23.net` y ejecuta `python ../S10_CH23/verificar_ch23.py ../S10_CH23/s10_ch23.net`.
   - Tiene que salir con **código 0**: CH1 igual que en S8b (89 piezas) y CH2/CH3 con 87 piezas cada uno, sin diferencias.
   - El script deriva lo esperado de `../S8_CH1/s8_ch1.net`. No lo cambies para que pase. Si crees que el script está mal, anótalo.
2. Ejecuta `kicad-cli sch erc`.
   - En CH1 eran 15 violaciones (7 `power_pin_not_driven`, uno por riel; 3 `pin_not_driven` en S0–S2 del 4051; 5 `isolated_pin_label`).
   - Por cada canal nuevo se esperan como mucho 3 `pin_not_driven` y las globales sin pareja del tipo `isolated_pin_label`.
   - Cualquier otro tipo, o una red que se una entre canales por error, es un fallo.
3. Ejecuta `python ../S8_CH1/comprobar_textos_s8b.py` sobre cada hoja (adapta la ruta con un argumento si lo pide; no cambies su lógica) y **mira también las etiquetas frente a los textos de las piezas**. En S8b el detector no lo hacía y quedaron pisados CH1_VMID_LO, CH1_ROFF_MID y VREF_2V5 junto a R130.
4. Exporta `../S10_CH23/s10_ch2.pdf` y `s10_ch3.pdf` y una vista PNG de la hoja completa de cada canal en `../S10_CH23/vistas/`.

## 3. Reglas

- No cambies valores, redes ni referencias fuera de lo que dice la tabla. Las contradicciones se anotan.
- No uses `set_active_layer`. No toques el PCB.
- Commits pequeños en `ai/s10-ch23-esquema`, sin push.
- Al terminar:
  - escribe `../S10_CH23/INFORME_S10.md` con las herramientas usadas, los límites de Konnect, la salida de las cuatro comprobaciones y las dudas;
  - escribe un diario en `ai-context/journal/`.
