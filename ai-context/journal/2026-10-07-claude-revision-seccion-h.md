# Revisión de la sección H del DMM con D1–D7 (7 oct 2026, ~10:20, Claude Opus 5.5)

Paso 9 de `S3G4_LAB_rev2.1/06_plan/PLAN_REFERENCIAS_DMM.md`.

## Pedido

Keneth: «de acuerdo con D1–D7, revisa la sección H, sin huella del ads1115 confiemos en el stm32». Acepta las siete recomendaciones de la síntesis. En D1 quita la huella sin montar del ADS1115: solo el ADC5 y la linealización al fabricar. Registrado en `DECISIONS.md` (7 oct).

## Cambio

- `S3G4_LAB_rev2.1/01_diseno/dmm_rev21.html` (sección H, HTML a mano) revisada → https://claude.ai/artifact/4iveEdvtCBTvhQj9jHjsvY, versión 3.
  - Cabecera y recuadro «Qué cambió en esta revisión».
  - §1: INL de 26–39 cuentas y una sola linealización en el rango de 2 V.
  - §2: tabla nueva, con la exactitud en dos niveles, ≥ 40 dB de rechazo a 60 Hz/100 ms (P40), y la calibración y la autoprueba.
  - §3: diagrama y bloques:
    - fuente de corriente P43 y bloqueo P42 en lugar de la PTC;
    - fusible cerámico;
    - X5 = aviso de fusible (P32), X6 libre y X7 autoprueba (P41);
    - C0G fijos con corrección por firmware (P18, P39);
    - asiento del autocero (P38), fugas del 4051 (D4) e Ib máx. del OPA2188;
    - RC del driver con la carga de muestreo (P20);
    - sin descargadores ni varistores (P23).
  - §5: puente DF10S, fusible HRC ≥ 35 A a 250 V y punto estrella (P27).
  - §6: reescrito con P43 (propuesta, D8), P42, diodo a 1 mA, continuidad, cable abierto (P33) y aviso de red (P34).
  - §7: tabla de protección actualizada.
  - §8: presupuesto con el método de ADI (579–630 ppm), tabla de cuentas y especificación en dos niveles (D5).
  - §9: recursos.
  - §10 nuevo: firmware y calibración, con 6 pasos al fabricar.
  - §11: S11 y lo abierto.
- `S3G4_LAB_rev2.1/00_requisitos/especificaciones_dmm.html` reescrita con las mismas cifras → https://claude.ai/artifact/9wuyJcNBxPcee2dNuThttm, versión 3.
  - Dos niveles de exactitud, corrientes de P43 y diodo a 1 mA hasta ≈ 3.3 V.
  - P42, fusible cerámico y aviso de fusible abierto, autoprueba, «sin ADC externo, ni huella (D1)» y 7 notas.
- `herramientas/calc_dmm_h.py` (nuevo). Calcula:
  - la fuente P43: corrientes, tensión disponible, diodo, continuidad y deriva;
  - el error de la razón por la INL;
  - la ganancia de ohmios;
  - la comprobación de la especificación de ohmios en cada rango.
- Nota en `01_diseno/dmm_arquitectura.md`. Actualizados `DECISIONS.md`, STATE, el diario de retomada, ARTEFACTOS, `herramientas/LEEME.md`, el plan y la memoria `referencias-dmm`.

## Hallazgos

- **La razón de ohmios de H no cumple ±(0.2 % + 10).** La corriente también se medía con el ADC5 (V_alto − V_bajo de R_ref, ÷4), así que la INL entra en % de lectura: 0.62 % típ., 0.94 % máx. y 0.24 % aun linealizada. Se propone **P43**: una fuente de corriente ratiométrica a VREF, como la del 34401A.
  - IREF = VREF/R1 (24.9 kΩ) baja por R2 (4.99 kΩ) → 501 mV bajo el riel de +4.9 V.
  - Un TLV2372 (C27204, 0.35 USD) copia esa caída en R_rango (50 Ω…2.49 MΩ, 0.1 %), con 2 × 74HC4051 en fuerza y sentido, PNP de paso y P42.
  - Corrientes de 10 mA … 0.2 µA. Tensión disponible de 2.40 V (200 Ω, margen 0.39 V) a 3.40 V. Diodo a 1 mA hasta 3.30 V.
  - Deriva de la corriente ±5 °C: 280 ppm. Ganancia de ohmios: 625 ppm.
- **20 MΩ a 0.2 µA, no a 0.1 µA** (encontrado al cerrar la revisión). El divisor de 10 MΩ en paralelo aplana V_x(Rx), así que cerca del fondo una cuenta del ADC son 4.4 kΩ.
  - Con 0.1 µA, la INL máxima da 1.52 veces la tolerancia garantizada ±(1 % + 40); con 0.2 µA, 0.76.
  - La fuga del mux pasa a 0.5 % de la corriente por nA, y la Ib máx. del OPA2188 a 0.42 %. Las dos se calibran.
  - En vacío, 2.0 V en 20 MΩ. El cable abierto y la autoprueba usan esa misma fuente.
- **Comprobación por rango** (10–100 % del rango, suma lineal tras la ganancia): el error usa del 76 al 95 % de la tolerancia en el nivel garantizado y del 25 al 81 % en el calibrado. Lo más justo está en 2 MΩ al 10 % del rango (0.95).

## Pruebas

- Etiquetas HTML equilibradas en H.
- SVG renderizados por separado (PyMuPDF) y en el navegador: ningún texto se sale de su caja ni se solapa más de 3 px. De paso se corrigieron tres textos que ya venían de antes: «3.15 A cerámico», «74HC4051»/«X0» y «Kelvin…»/«→ X4».
- Hoja de especificaciones a 375 px de ancho: sin desbordamiento horizontal.
- `python calc_dmm_h.py` reproduce todas las cifras citadas.

## Pendientes

- **D8 (Keneth):** aprobar P43. Si no se aprueba, los ohmios vuelven a la razón con buffer (P25), con ≈ 0.6 % sin linealizar.
- Después, escribir el encargo S11 para Codex con la lista de §11 de H.
- Abiertos en H §11: pieza del fusible y su portafusibles, el driver diferencial y el interruptor de carga del DMM.
- RD-08 pide ~3.5 V en diodo; con 1 mA quedan ≈ 3.3 V. S11 lo comprueba.
