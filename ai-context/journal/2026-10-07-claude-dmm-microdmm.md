# R3 Micro-DMM: anatomía (7 oct 2026, Claude Opus 5.5)

Sesión retomada con `2026-10-07-claude-retomar-referencias-dmm.md`. Referencia 5 de 9 del estudio del DMM.

## Cambio

- Página nueva `S3G4_LAB_rev2.1/02_referencias/dmm_microdmm.html`, publicada en https://claude.ai/artifact/VXTHBpRXxs9tDhqPwQFTb6 (versión 2).
- Scripts nuevos en `S3G4_LAB_rev2.1/herramientas/`: `calc_dmm_microdmm.py`, `draw_dmm_microdmm.py` (dibujos `puente` y `ohmios`, 0 solapes) y `build_dmm_microdmm.py`.
- Actualizados: `ARTEFACTOS.md`, `herramientas/LEEME.md`, la fila 5 de `06_plan/PLAN_REFERENCIAS_DMM.md`, `STATE.md` y el diario de retomada (5 de 9, P33–P34, el riesgo de lazos de masa y el siguiente paso).

## Evidencia

- Repositorio `research_and_tests/Micro-DMM/` (último commit 12 ago 2026). La fecha del último cambio de cada placa sale de `git log` por carpeta: la V4_next es del 11 dic 2025; Feather Redux y SimplifiedOpenLeadVoltmeter, de mayo–junio 2026; OpenLead_Headless_V3, de ago 2026.
- Netlists exportadas con `kicad-cli` 10 y leídas con `kinet.py`. El esquema de la V4_next se renderizó (PDF → PNG por zonas).
- **Puente en la V4_next:** R14 = 15 kΩ fijo y Q8 + R24 = 1 MΩ en paralelo, comprobado en la netlist y en el dibujo. Al abrir Q8 el puente no se rompe. En las placas posteriores está al revés (1 MΩ fijo, 15 kΩ conmutado).
- **Firmware:**
  - `OpenLeadDetect_Feather_Voltmeter` (ago 2026): ADS1015 a ±2.048 V, umbral 1.42 V; 1.262 V con las puntas cerradas y 1.706 V abiertas; espera de 4 ms en alterna.
  - `microDMM_RA4M1_XIAO_SMD_V5`: fórmulas de ohmios, rango en 400 Ω ± 5 %, 15 factores CF_A…CF_O, ahorro a los 5 s con las puntas al aire.
  - `BlinkyHawk_RA4M1`: umbrales por DIP, configuración en memoria con CRC y tres métodos de detección.
- **Hoja «Calibrations»:** errores sin calibrar de 3 placas, de −18 % a +44 % en 4.7 MΩ y dentro de ±1 % entre 330 Ω y 100 kΩ.
- **ADS1115 (SBAS444E p. 5):** Z_CM y Z_DIFF por fondo de escala; error de ganancia de 0.15 % como máximo.

## Cifras propias (calc_dmm_microdmm.py)

- La escala 69.95 del firmware coincide con 14.78 kΩ ∥ 710 kΩ (Z diferencial del ADS a ±0.256/0.512 V). A ±1.024 V o más, la lectura sale entre +1.45 % y +2.0 %. Deducción, NO VERIFICADO.
- La bajada efectiva de AIN1 en la prueba (≈ 490/465 kΩ) se deduce de los umbrales; la atribuyo a la fuga de D5 (NO VERIFICADO). La corriente por las puntas en la prueba es ≈ 1.26 µA.
- **Ohmímetro, rango alto:** S = (R + 22 kΩ)/22 kΩ vale 46 en 1 MΩ y 215 en 4.7 MΩ. La carga del ADS (≈ 6.9 MΩ) da −41 % en 4.7 MΩ, y 6 mV de error en la referencia dan −20 %.
- **P33:** tabla de tensiones de las variantes A y B, con corrientes máximas de 124 nA y 490 nA y τ de 0.1 ms en la toma y 2 ms con 100 pF de cable.

## Propuestas (sin aplicar; las decide Keneth en la síntesis)

- **P33** Cable abierto en tensión con resistencias definidas.
- **P34** En ohmios, detectar tensión externa y desconectar la fuente.
- Refuerza P26, P29 y P21, y confirma la sección H §4 y §6.

## Pruebas

- `chk_dmm.py draw_dmm_microdmm puente ohmios`: 0 y 0. Dibujos revisados a la vista con `render_svg.py`.
- La página en el navegador integrado: 16 secciones y 2 SVG, sin desbordamiento horizontal a 296 px (se añadió `code{overflow-wrap:anywhere}`). La plantilla del TIDA-01012 se regenera sin cambios.

## Pendientes

- Siguiente: R8 Martin + R4 EEWorld 77845; luego R5, R9 y la síntesis.
- Para la síntesis: elegir la variante de P33 (A o B) y su umbral; el tiempo de detección de P34 en S11; cómo avisar de los lazos de masa con USB (RD-05).
