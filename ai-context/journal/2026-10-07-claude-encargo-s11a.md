# D8 aceptada y encargo S11a del DMM (7 oct 2026, ~11:00, Claude Opus 5.5)

## Pedido

Keneth: «de acuerdo con P43, escribe el encargo S11». P43 queda aceptada (D8) y está registrada en `DECISIONS.md`.

## Cambio

- **Encargo y plan nuevos** en `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
  - `ENCARGO_CODEX_S11a.md`;
  - `PLAN_SIMULACION_S11a.md`, con el formato de S9: §1 con todos los valores, K0–K13, criterios S11-C1…C14 (≥ 95 % de placas, tras calibrar a 23 °C y evaluando a 18/28 °C), entregables, lo que no es de Codex y cómo audito.
- **Variantes,** que Codex informa sin elegir:
  - elemento de paso de P43: bipolar (2N3904/2N3906) | MOSFET (2N7002/BSS84);
  - driver: TLV2372 | OPA365.
- `herramientas/calc_dmm_s11.py` (nuevo): estimaciones que el plan cita.
- **Sección H** (versión 4):
  - P43 aceptada;
  - la frase falsa sobre P42 («nada que se caliente») corregida;
  - en §6, la nota sobre la β del PNP;
  - en §11, los riesgos y el enlace al plan.
- **Hoja de especificaciones** (versión 4): nota 3 con P43 aceptada.
- Actualizados `03_simulaciones/LEEME.md`, `herramientas/LEEME.md`, ARTEFACTOS, STATE, el diario de retomada, el plan de referencias y la memoria.

## Hallazgos al escribir el plan (`calc_dmm_s11.py`)

- **P42 no limita la corriente.** Con tensión negativa en V/Ω, la fuente sigue entregando la corriente de su rango, y la escalera disipa I × V.
  - Con la red, en 200 Ω (10 mA): ≈ 1.65 W de pico por MMBTA92 (472 % de 0.35 W).
  - En 2 kΩ: 0.165 W (47 %). En los demás, casi nada.
  - Depende de que el firmware (P34) apague la fuente a tiempo.
  - H decía «nada que se caliente»: corregido.
- **El circuito de la escalera P42 no está definido.** H solo dice «resistencias de base que reparten la tensión».
  - Una escalera de PNP autopolarizada no pasa 10 mA con ≈ 0.8 V de caída (lo que supone `calc_dmm_h.py`) con un riel de 4.9 V. El 34401A lo hace con 12.9 V y una polarización aparte (Q211).
  - **Por eso S11 se parte:** S11a modela P42 con un 1N4007 + 0.2 V, y S11b (escalera, red 10 s y ESD) espera a que Claude diseñe el circuito.
- **PNP de paso:** su corriente de base no llega a Rx. Con β = 100 se pierde ≈ 1 % y deriva ≈ 300 ppm con ±5 °C (≈ 590 ppm con β = 50, que es plausible a 0.2 µA). Lo mismo pasa con el NPN de IREF. Variante MOSFET en S11a.
- **Tensión en vacío:** de 2 kΩ a 2 MΩ cae, por construcción, en el límite de modo común del OPA2188 (riel − 1.5 V), con cualquier riel. S11 mira la inversión de fase y la saturación.
- **Alterna en 200 mV y 2 V:** R_PROT (99 kΩ) con ≈ 40 pF en X0 da un polo en ≈ 40 kHz, −10.5 % a 20 kHz. Lo corrige P39; S11 mide el residuo y cuánto varía esa capacidad.
- **Muestreo:** la carga media del ADC5 a 200 kSa/s equivale a 1 MΩ. Con R_ISO = 3.3 kΩ son 3300 ppm de error lineal (calibrable); con 100 Ω, 100 ppm. Rejilla en K6.
- **Rechazo de la red:** a 60 ± 0.5 Hz, 41.5 dB con un ciclo; con 100 ms a 49.5 Hz, 39.9 dB (al límite). El criterio se aplica a 60 Hz.
- **Compensación del divisor:** 3 × 100 pF sobre los 3 MΩ (τ = 300 µs), 330 pF (−1 %) y 3.0 nF; con 3.3 kΩ de amortiguación en serie con cada 100 pF, el polo queda en 477 kHz.

## Pruebas

- `python calc_dmm_s11.py` da las cifras citadas.
- Etiquetas de H equilibradas.
- CLI de Codex comprobado: `…\OpenAI\Codex\bin\5ea220ae823df3d7\codex.exe`, 0.160.1. La ruta del encargo S9 (`8aaf…`) ya no existe.

## Pendientes

- **Modelos y hojas de TI.** Keneth debe dejar en el proyecto (o autorizar que Claude los baje) los modelos de OPA2188, TLV2372 y REF3325. Las hojas son las de esas tres piezas y las de MMBT3904/3906, 2N7002, BSS84, 1N4007W y DF10S. Sin el TLV2372 no se puede simular P43.
- Lanzar S11a y auditarlo.
- Diseñar el circuito de la escalera P42 y decidir cómo se apaga la fuente ante tensión externa: firmware P34, un comparador o menos corriente en continuidad. Después, escribir S11b.
