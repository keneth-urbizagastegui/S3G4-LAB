# DMM de la rev 2.1 — arquitectura (borrador)

> **Superado el 7 oct por la sección H:** `01_diseno/dmm_rev21.html` (guía con valores) y `00_requisitos/especificaciones_dmm.html`. Se conserva como registro del primer paso. La sección H se revisó el mismo día con D1–D7 (`ai-context/DECISIONS.md`). Ya no valen la PTC de la fuente de ohmios, sustituida por P42, ni la medida de ohmios por razón, ahora P43 (propuesta).

- Autor: Claude Code, 7 oct 2026. Primer paso del DMM (PLAN, paso 1).
- Decisiones de Keneth del 7 oct: `ai-context/DECISIONS.md`, entrada «DMM: arquitectura».
- Requisitos: RD-01…RD-10 en `00_requisitos/requisitos_dmm_awg.html`.
- Referencias: TI TIDA-01012 (`research_and_tests/tidubv5b (1).pdf`), Micro-DMM (`research_and_tests/Micro-DMM/`), NI ELVIS II y la revisión del G473 (`02_referencias/g473_analogico.html`).
- **Borrador:** las cifras marcadas «a calcular» se fijan en la sección H del documento vivo y se comprueban en simulación (S11), con el mismo método que CH1.

## 1. Bloques

```
V/Ω ──R_PROT(alta tensión)──┬── divisor 10 MΩ: tomas ÷1 · ÷10 · ÷100 ──┐
                            │                                           ├─ 74HC4051 ─ deriva cero A (buffer) ─┐
                            └── fuente de ohmios: PTC + sujeción ───────┘   (÷1, ÷10, ÷100, COM=autocero,     │
                                 + resistencia de referencia por rango      Ω, diodo, I, VCM)                 ├─ ADC5 diferencial
A ──fusible 3.15 A rápido── derivador 0.1 Ω (Kelvin) ── COM                                                   │   (PD13 + / PD14 −)
                            └── diodos de potencia en paralelo ── deriva cero B (×10 / ×100) ─────────────────┘
COM = masa común del equipo (RD-05)
```

| Bloque | Qué hace | Decidido | Por fijar |
|---|---|---|---|
| Entrada V/Ω | Divisor de 10 MΩ en resistencias de alta tensión en serie, con tomas ÷1 / ÷10 / ÷100. La toma ÷1 pasa por R_PROT y una sujeción a los rieles | Divisor con tomas y mux (7 oct) | Valores, partición de la cadena, compensación para que sea plano hasta 20 kHz (RD-07) |
| Selección | 74HC4051 a ±4.9 V, la misma pieza que la escalera del osciloscopio. Elige la toma, COM (autocero), la señal de ohmios/diodo, la del derivador y VCM | Mux (7 oct) | Asignación de las 8 entradas; fugas del 4051 con 10 MΩ de fuente |
| Amplificador | Doble de deriva cero. A: buffer de alta impedancia (×1, y ×10 en 200 mV). B: ganancia ×10 / ×100 del derivador | Deriva cero externo (7 oct) | **Pieza** (barata en LCSC, deriva cero real, alimentación compatible) y su riel; ganancia conmutada |
| ADC | ADC5 en diferencial, sobremuestreo ×256 por hardware y ×4 en firmware (RD-03); referencia REF3325 compartida (VREF+) | RD-03 | Tensión de modo común (VCM) y fondo de escala útil; filtro anti-alias para AC (H-2) |
| Corriente | Derivador único de 0.1 Ω (≥ 1 W), fusible rápido de 3.15 A, diodos de potencia en paralelo con el derivador. Medida Kelvin respecto a COM | RD-06 | Fusible (pieza SMD o portafusibles); diodos; la caída en 2 A (0.2 V) |
| Ohmios, diodo y continuidad | Fuente desde 5 V con una resistencia de referencia por rango (método de razón: R = R_ref · V_x / (V_s − V_x)); diodo hasta 3.5 V con divisor ≈ ÷2 antes de PB14 (RD-08); PTC + sujeción para aguantar la red unos segundos | RD-08, RD-10 (7 oct) | Rangos de corriente, conmutación de R_ref, PTC concreto; continuidad con COMP7 (PB14) |
| Cable abierto (RD-09) | Pequeña corriente de prueba en la entrada | RD-09 | Valor y cómo se apaga en medida |

## 2. Rangos aceptados (7 oct)

| Función | Rangos | Comentario |
|---|---|---|
| Tensión DC | 200 mV · 2 V · 20 V · 50 V | 20 000 cuentas; 10 µV por cuenta en 200 mV; el rango alto se recorta a 50 V |
| Tensión AC (TRMS, 40 Hz–20 kHz) | 200 mV · 2 V · 20 V · 50 Vrms | TRMS por firmware (etapa J1 del banco) |
| Resistencia | 200 Ω · 2 kΩ · 20 kΩ · 200 kΩ · 2 MΩ · 20 MΩ | método de razón; 20 MΩ en paralelo con la entrada a calcular |
| Corriente DC y AC | 200 mA · 2 A | 0.1 Ω: 20 mV y 200 mV a fondo; 200 mA pide 1 µV por cuenta (deriva cero + autocero) |
| Diodo · continuidad | hasta ≈ 3.5 V · umbral con zumbador | PB14 por divisor ≈ ÷2 (RD-08) |

## 3. Lista de reserva de recursos del G473 (para el mapa de pines)

Lo que el DMM da por supuesto. Se revisará contra el osciloscopio y el AWG en el paso 3 del PLAN.

| Recurso | Uso | Origen |
|---|---|---|
| ADC5, canal 10 diferencial (PD13 +, PD14 −) | Medida de tensión, corriente y ohmios | Mapa firmado rev 2.0; RD-03 |
| OPAMP5 (VINP0 = PB14, salida interna a ADC5_IN3) | Ohmios, diodo y continuidad | Mapa firmado rev 2.0 |
| COMP7 (INP = PB14, INM = DAC2_CH1) | Continuidad sin CPU (zumbador) | Mapa firmado rev 2.0 |
| DAC2_CH1 | Umbral de continuidad | ídem |
| VREF+ (REF3325, 2.5 V) | Referencia del ADC5 | P9, compartida con el osciloscopio |
| 3–4 líneas digitales | Selección del 4051 del DMM y de la ganancia | Pueden salir del 74HCT595 del AFE |
| 1 salida para el zumbador | Continuidad | — |

## 4. Abierto

1. **Pieza de deriva cero:** las habituales (OPA2333, TLV2333 y similares) son de 5.5 V como máximo, así que no van en ±4.9 V. Hay que decidir su riel (3.3 V con VCM, o una pieza de mayor tensión) y cómo llega la señal bipolar al ADC5 diferencial. El TIDA-01012 lo resuelve con VCM y un driver diferencial.
2. **Interruptor de carga propio del DMM** (RF-18, G.6): con su propio riel desde el punto 1 puede salir casi solo.
3. **Supervivencia a la red (≈ 10 s, 230 Vrms):** potencia y tensión de las resistencias del divisor, el PTC de la fuente de ohmios y la energía de la sujeción.
4. **Distancias en placa** para 71 Vpk continuos y 325 Vpk durante unos segundos en V/Ω.

## 5. Siguientes pasos

1. Claude: sección H del documento vivo con los valores (divisor, compensación, amplificador y riel, fuente de ohmios, derivador y fusible, presupuesto de errores para 20 000 cuentas), y la pieza de deriva cero elegida en LCSC. Keneth decide lo que quede abierto.
2. Codex: simulación S11 del DMM (precisión DC por rango, respuesta AC hasta 20 kHz, ohmios, corriente, red durante 10 s y fugas del 4051), con auditoría de Claude.
3. Paso al esquema (hoja `dmm.kicad_sch`).
