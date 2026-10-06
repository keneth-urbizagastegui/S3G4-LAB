# Auditoría de Claude — S8, esquema de CH1

- 4 oct 2026. Audita la sesión principal de Claude; dibujó la sesión de Konnect (`INFORME_S8.md`). Rama `ai/s8-ch1-esquema`: commits `b9f1be1`…`192fa03`, sin push.
- Fuente de verdad: `CH1_PIEZAS_Y_REDES.md`.

## Veredicto

**El esquema es eléctricamente correcto respecto a la fuente.** Cada pin de las 89 piezas está en su red. Los avisos del ERC y del analizador se deben a que las otras hojas todavía no existen. Antes de unir con `main` quedan dos cambios de valor (C125/C126) y el DNP de C103.

## Qué se comprobó, de forma independiente

1. **Reproducción.** `kicad-cli sch export netlist` desde el `.kicad_sch` de la rama da la misma netlist que la entregada (`s8_ch1.net`), salvo la fecha. `kicad-cli sch erc`: las mismas 12 violaciones.
2. **Pin a pin, con un analizador propio de la netlist (sin usar `verificar_s8.py`)** contra las tablas de la fuente y las hojas de datos:
   - **CI:** U101 (OPA810 DBV), los 16 pines de U102 (Y0…Y7, Z, S0…S2, E̅, VEE, VCC), U103/U105 (SOIC-8 doble; U105 en seguidor) y U106 (con PD a VDDA).
   - **Relé, conmutador y diodos:** K101 con 1 → `RELAY_COM`, 10 → `CH1_K_COIL_N` y los contactos 3-2-4/8-9-7; SW101 en AC–GND–DC (pines 1–8 según §2.3); D101 a ±4.9 V con el común en `CH1_SEL`; D102/D103 antiparalelo; D104 con el cátodo a `RELAY_COM`.
   - **Resto:** Q101 (G-S-D), J101, VC101 y las parejas serie del §2.10 con sus redes intermedias.
3. **Desacoplo:** C116–C126 en los rieles que dice el §4, incluido el negativo.
4. **kicad-happy `analyze_schematic.py`:** 89 piezas y 60 redes (56 más 4 sin conexión). Sus avisos:
   - 5 errores, todos esperables: 4 PP-001 (los pines V− no tienen camino a un riel con fuente, porque `-AFE_4V9` aún no tiene fuente) y 1 SS-001 (cobertura de MPN; las piezas llevan el campo `LCSC`, que es lo que usa JLCPCB).
   - 8 avisos: rieles sin fuente (RS-001) y `CH1_SENSEL_A/B/C` con un solo pin (NT-001). Desaparecen al dibujar las hojas de alimentación y de control.
   - El analizador ya ve C103 como DNP.

## Lo que queda

| # | Qué | Quién |
|---|---|---|
| 1 | **C125/C126 a 25 V** (C15850). La fuente decía 16 V y la lista de materiales 25 V; corregida la fuente hoy. Cambiar el valor en la hoja | Keneth en la GUI o la próxima sesión de Konnect |
| 2 | **C107**: corregida la fuente («≈ 8.7 pF, se compra 8.2 pF de partida»); el valor dibujado (8.7 pF) es válido | — |
| 3 | **C103 DNP**: marcar el atributo en la GUI. kicad-happy ya lo trata como DNP, pero la lista de JLCPCB necesita el atributo | Keneth en la GUI |
| 4 | **Símbolos y huellas propios** de K101 (TQ2SA, hoja p. 11), SW101 (plano C883267), J101 y VC101. El SW_DP3T provisional dibuja el común en 3/7, aunque los números de pin son los buenos | Siguiente tarea de esquema |
| 5 | **Pinouts sin hoja:** 2N7002, BAV99 y 1N4148W (los habituales de KiCad) | Bajar sus hojas |
| 6 | **Legibilidad:** la hoja conecta todo por etiquetas, sin cables. Es correcta, pero no se ve el recorrido de la señal. Al pasar a la jerarquía estilo OpenScope conviene cablear cada bloque | Al hacer la jerarquía |
| 7 | **Cajetín vacío** (sin título, revisión ni fecha) | Con la jerarquía |
| 8 | **Unir con `main`:** el último commit de la rama incluye cambios de `ai-context/index.json` de otra sesión. Son de Claude (los tres HTML añadidos al índice); no hay conflicto | Keneth decide cuándo |
