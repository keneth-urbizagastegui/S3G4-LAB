# Encargo para Codex — S9, variante B con un modelo del LM6172 ajustado a la hoja

Continuación de S9. Claude, 4 oct 2026. **Decisión de Keneth (4 oct):** «hay que seguir lo que dice el datasheet». La variante B se simula con una **copia propia del macromodelo ajustada a la hoja de TI a ±5 V**, no con el modelo de National tal cual.

**Lanzamiento (lo hace Claude):** cuando termine la campaña de la variante A. Codex arranca en la raíz `S3G4 LAB`.

---

## Contexto

- Contrato: `PLAN_SIMULACION_S9.md` y `ENCARGO_CODEX_S9.md` (misma carpeta). Siguen vigentes salvo lo que cambia aquí.
- Tu puerta K0 detuvo B con razón (`resultados/s9_puerta_k0.json`). El modelo de National a ±4.9 V da un producto ganancia-ancho de banda de ≈ 150 MHz (×10 → 15.3 MHz) y 1.7 mA por amplificador. La hoja (tu tabla de `ACTA_S9.md`, SNOS792E) da, a ±5 V: **70 MHz de ancho unitario**, 130 MHz de −3 dB como seguidor, **2.2 mA por amplificador** (4.4 mA por dual), 11 nV/√Hz y 1 pA/√Hz.
- Abre tu diario (o continúa el de S9) al empezar.

## Qué hacer

1. **Copia ajustada** en `comun/lm6172_hoja.lib` (nunca en `Simulation_LTSpice/models/`), con el mismo orden de nodos (`+IN −IN V+ V− OUT`). Ajusta lo mínimo para que, a ±4.9 V, cumpla la tabla de ±5 V de la hoja:
   - producto ganancia-ancho de banda: **70 MHz ±15 %**, medido con ganancia ×10 (−3 dB en 7 MHz ±15 %);
   - seguidor: −3 dB entre 100 y 160 MHz, con pico ≤ 3 dB;
   - consumo: **2.2 mA ±15 %** por amplificador;
   - ruido: 11 nV/√Hz ±10 % entre 10 kHz y 1 MHz (puedes partir de tu copia de ruido) y 1 pA/√Hz;
   - sin cambiar el offset, la polarización ni la excursión de salida del modelo original. Comprueba que siguen dentro de la hoja: ±3 mV, ≤ 2.5 µA y +3.1/−3.1 V con 1 kΩ.
   - Documenta **qué tocaste y por qué** (por ejemplo, la capacidad de compensación interna o un polo añadido, y el escalado de la fuente de consumo) y deja intacta la topología de saturación y de entrada.
2. **K0 repetido con la copia**, con la tabla «hoja frente a modelo» completa. Si no logras cumplir los márgenes del punto 1 sin rehacer el modelo, para, anótalo y sigue con lo que quede de A.
3. **Campaña de B** con la copia: K1 (con los valores E96 del filtro elegidos para A, sin reoptimizar salvo que caiga fuera de 1.0 MHz ± 10 %), K2, K3, K5, K6, K7 y K8. K4 no hace falta, porque el driver del pin no cambia. Mismo Monte Carlo y misma semilla que A.
4. **Acta:** completa `ACTA_S9.md` con la columna B y una sección «Modelo del LM6172 ajustado a la hoja», con sus límites. La saturación y las protecciones (K6) siguen saliendo de la topología de National: dilo como limitación junto a cada resultado de K6.

## Reglas

Las de `ENCARGO_CODEX_S9.md`. Además: **no elijas variante** y no toques los resultados de A. No descargues nada. `--resume` y registros fuera de la carpeta vigilada.

## Respuesta final

- Ficheros nuevos o cambiados.
- K0: tabla hoja / modelo original / copia ajustada.
- Tabla S9-C1…C9 con A y B lado a lado.
- Limitaciones de la copia.
- Dudas.
