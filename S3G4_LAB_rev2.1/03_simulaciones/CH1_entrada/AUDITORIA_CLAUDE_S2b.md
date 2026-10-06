# Auditoría de Claude — S2b, ESD realista, piezas de 200 V y capacidad del buffer

- Fecha: 2026-10-03.
- Auditor: Claude Code (Opus 5.5).
- Objeto: trabajo de Codex (CLI 0.160.0, `gpt-6.1-sol`, `medium`, sesión `01a100a9-a562-7e70-b2ac-38cc878a17c8`). Entregó `comun/ch1_comun_s2b.inc`, `S2b/`, `ejecutar_s2b.py`, `ACTA_S2b.md`, 14 CSV y su diario.
- Contrato: `PLAN_SIMULACION_S2b.md` §7.

## Veredicto

1. **Reproducible:** mi reejecución en una copia fuera del proyecto, con `S3G4_MODELS`, sale con código 0 y 120 simulaciones sin errores en 55 s. **Los 14 CSV son idénticos byte a byte.** La ruta configurable funciona.
2. **Capacidad del buffer sin doble cuenta:** CIN_BUF = 0 en el circuito y `C_SEL_EST` usa la capacidad de modo común de la hoja (CBUF_EST = 2.5 pF para el OPA810). ΔCin baja de 2.84 pF (S2) a **0.39 pF**.
3. **Generador ESD verificado sobre 2 Ω** (red de dos ramas: 150 pF / 330 Ω / 1.8 µH y 5 pF / 155 Ω / 180 nH), con pasos de 50 ps en los primeros 100 ns:

| Nivel | Pico (15/30 A ±15 %) | Subida (0.8 ns ±25 %) | I 30 ns (8/16 A ±30 %) | I 60 ns (4/8 A ±30 %) |
|---|---|---|---|---|
| 4 kV | 14.99 A ✓ | 0.805 ns ✓ | 7.93 A ✓ | 4.05 A ✓ |
| 8 kV | 29.97 A ✓ | 0.805 ns ✓ | 15.85 A ✓ | 8.09 A ✓ |

## ESD con la métrica correcta (I²t por diodo; rating 16 µA²s, criterio ≤ 8)

| Buffer | ±4 kV contacto (acordado) | +8 kV aire (acordado) | ±8 kV contacto (no exigido) |
|---|---|---|---|
| OPA810 | **3.41** ✓ (21 % del rating) | **6.97** ✓ (44 %) | 13.67 (85 %) |
| OPA828 | 3.59 ✓ | 7.32 ✓ | 14.38 (90 %) |

**El nivel acordado (±4 kV en contacto, ±8 kV en aire) se cumple con los BAV199**, sin protección adicional. Las cifras son de simulación: falta el ensayo IEC en placa. 8 kV en contacto queda cerca del rating y no estaba pedido.

## C3: el criterio era mío y estaba mal planteado

- Las dos hojas autorizan pasar del riel **si la corriente por los diodos ESD internos se limita a 10 mA**:
  - OPA828, nota (3) de los máximos absolutos: «Input terminals are diode-clamped to the power-supply rails. Current-limit input signals that can swing more than 0.5 V beyond the supply rails to 10 mA or less».
  - OPA810: lo mismo en su apartado de entradas («limiting current through the input ESD diodes when input common-mode voltages are greater than the supply voltages»).
- Medido:
  - en continuo (E5b), corriente de entrada de µA a 0.2 mA;
  - en ESD, 5.7 mA (OPA810) y 6.2 mA (OPA828);
  - todo **≤ 10 mA** gracias a R_PROT de 1 kΩ.
- Diferencial: OPA810 0.89 V en continuo y 4.4 V en ESD (límite ±7 V); OPA828 4.0 V (límite = toda la alimentación).
- **Con el criterio de corriente, C3 pasa** con los dos buffers. En S1–S2 lo planteé por tensión: queda corregido para las siguientes etapas.

## Lo demás

- **C1 y C2 pasan con OPA810.** R_EQ ve 99.0 V con un límite reducido de 100 V (1206). Queda al 99 %: hay que usar la 1206 de 200 V, nunca una 0805. C_EQ y C_S de 200 V, dentro.
- **Canal apagado:** Codex señala que el OPA810 sin alimentar supera en 0.6 V su diferencial «igual a la alimentación total» (nota 2 de su hoja). Sin alimentación, esa cifra no tiene sentido físico; lo que manda es la corriente por los diodos ESD: 1 V de la toma con R_PROT de 1 kΩ deja ~0.5 mA. **Se valida en placa** junto con el resto del canal apagado.

## La segunda fuente (OPA828)

- **Eléctricamente sirve:** diferencial y ESD bien, offset y rieles bien.
- **No es intercambiable con la misma lista de piezas:** su capacidad de entrada es mayor y la **Cin del canal sube a 31 pF**, por encima de los 30 pF de RF-08. Además, el error de ganancia es del 0.54 % (criterio ±0.5 %), aunque eso se corrige en la calibración.
- Además cambia el encapsulado (SOIC-8 o HVSSOP-8 frente a SOT-23-5).

Opciones, que decide Keneth:
1. **Ct de 2 × 12 pF para las dos fuentes.** Baja la Cin unos 4 pF (S1: 22.7 frente a 26.7 pF), así que las dos quedan dentro de 10–30 pF. Hay que volver a simular el recorrido del trimmer, porque con Ct menor la compensación es más sensible.
2. **OPA828 como alternativa con variante de piezas:** C_S, C_EQ y Cb distintos según el buffer montado, y huella doble. Más complicado de fabricar.
3. **OPA810 como fuente única** (RF-19 lo permite si no hay equivalente que cumpla) y el OPA828 sólo documentado.

## Dudas de Codex

| Duda | Juicio |
|---|---|
| Macromodelos apagados sin validar | Correcto: canal apagado en placa |
| Diferencial del OPA810 apagado | Ver arriba: manda la corriente por los diodos ESD |
| Faltan ratings de pulso de piezas concretas | Correcto: al elegir las resistencias 1206, pedir su curva de pulso |
| Falta el ensayo IEC físico | Correcto |
| El aire sólo se probó a +8 kV | Era lo que pedía el plan. Por simetría del circuito, −8 kV en aire debería dar lo mismo en el otro diodo; se puede añadir si hace falta |

## Estado de la entrada de CH1 tras S1–S2b

Con el OPA810, la entrada P4b cumple en simulación:
- RF-05, RF-07 y RF-08;
- el nivel de seguridad acordado: ±100 V sin daño, también apagado, y ESD de ±4 kV en contacto / ±8 kV en aire;
- piezas dentro de sus límites con R_EQ en 1206 y C_EQ y C_S de 200 V.

Pendiente de placa: canal apagado, ESD real y centrado del trimmer. Siguiente etapa del plan: **S3** (buffer, escalera y ganancia con amplificadores reales).
