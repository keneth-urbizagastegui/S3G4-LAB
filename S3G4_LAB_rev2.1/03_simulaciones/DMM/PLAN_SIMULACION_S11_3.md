# Plan de simulación S11.3 — DMM, bloque 1: simulación de cierre (O4, 60 V en ohmios)

- Autor: Claude Code (auditor), 7 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- Cierra el bloque 1. **Lee antes:**
  - `PLAN_SIMULACION_S11_1.md` (con §3b y §3c) y `PLAN_SIMULACION_S11_2.md`, que siguen vigentes salvo lo que cambia aquí;
  - `AUDITORIA_CLAUDE_S11_2.md` y `REDISENO_BLOQUE1.md` (§2.5 y §3.3);
  - en `ai-context/DECISIONS.md`, la entrada del 7 oct «RD-10 relajado en modo ohmios».
- Reutiliza el ejecutor y el modelo reducido de S11.2, y los datos de las hojas que ya leíste. No repitas Q0.

## 1. Circuito final del bloque 1

1. **V/Ω en tensión:** como S11.1, más **R_X1 = 100 Ω** en serie entre la toma ÷10 y el pin X1 del 74HC4051 (auditoría de S11.2: la ESD metía 432 mA por la compensación del divisor). Pon también 100 Ω en X2 y en X0 si la ESD lo pide; **informa, no lo decidas**.
2. **V/Ω en ohmios (O4):**
   - V/Ω → relé TQ2SA → 2 × 1.10 kΩ en 2512 (2.2 kΩ) → N1, con la **SMAJ12CA** a COM → R_S de 3.3 kΩ → N2;
   - en N2: un BAV199 a cada riel y un diodo de bloqueo en serie con el BSS84 de la fuente;
   - zéner BZT52C5V6 de sumidero de rp a COM y de COM a rn;
   - sin PTC ni BSS126.
3. **Borne A:** Littelfuse 0216 de 3.15 A (apertura según su hoja, k = 1, 2 y 3), GBU808 en paralelo con el derivador de 0.1 Ω, R_B = 10 kΩ hacia la entrada de B y X5 por 10 MΩ.
4. **Rieles:** como en S11.2, con zéner y los dos casos de diodo de cuerpo con el DMM apagado.

## 2. Pruebas

| # | Qué |
|---|---|
| R1 | Medida normal: diodo a 1 mA y a 100 µA (tensión disponible y corriente real; el rediseño estimaba 0.6 mA en silicio); fuga en N1/N2 a 0.2 µA y 1 µA (informativa); ±50 V DC y 50 Vrms en tensión |
| R2 | **Red de 230 Vrms, 60 Hz, 10 s en modo tensión** (relé abierto), con el DMM encendido y apagado |
| R3 | **60 V DC (±) y 60 Vrms durante 10 s en modo ohmios** (relé cerrado, sin abrirse), en cada rango de la fuente (1 mA, 100 µA y 0.2 µA) y con la fuente apagada; DMM encendido y apagado |
| R3b | Solo informativo: 230 Vrms en ohmios durante 100 ms. ¿Qué pieza se rompe primero y en cuánto tiempo? Sirve para el aviso en pantalla, no tiene criterio |
| R5 | Borne A con la red a 0.5, 1 y 2 Ω y el fusible abriendo (repite el de S11.2 con el circuito final) |
| R6 | ESD ±4 kV (contacto) y ±8 kV (aire) en V/Ω, en modo tensión y en modo ohmios, y en A, con R_X1 |
| R7 | Recuperación tras R2 y R3, observando como máximo 2 s después de retirar la tensión (si no cabe, extrapola y dilo) |

## 3. Criterios

| # | Criterio | Pruebas |
|---|---|---|
| C1 | Cada pieza ≤ 80 % de su tensión y ≤ 50 % de su potencia, energía o I²t (según su hoja) | R2, R3, R5, R6 |
| C2 | Tensión entre rieles ≤ 11 V, con el DMM encendido y apagado | R2, R3, R6 |
| C3 | Pines de los circuitos integrados dentro de sus máximos, con corrientes ≤ 50 % | R1–R6 |
| C4 | En modo ohmios, 60 V durante 10 s sin daño y sin firmware | R3 |
| C5 | Fuga: informativa (se mide en el prototipo) | R1 |
| C6 | Diodo: ≥ 3.5 V a 100 µA; a 1 mA, informar de la tensión y de la corriente real | R1 |
| C7 | Recuperación ≤ 1 s | R7 |
| C8 | GBU808 ≤ 50 % de su I²t con el fusible abriendo; la IFSM de 8.3 ms no se aplica a pulsos de menos de 1 ms (auditoría de S11.2) | R5 |

Fallar es un resultado válido: informa del valor y de lo que lo movería. Puedes probar R_X0/R_X2, pero no otras piezas ni otros remedios.

## 4. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque1_o4.inc`;
- `S11_3/` y `ejecutar_s11_3.py`: 10 trabajadores, `--smoke`, `--resume`, `S3G4_MODELS` y 300 s por caso;
- `resultados/s11_3_*.csv`;
- `ACTA_S11_3.md`, con la tabla C1–C8, la pieza más cargada de cada prueba y la lista de piezas final del bloque 1;
- tu diario en `ai-context/journal/`.

## 5. Lo que NO es tuyo

No cambies piezas ni topología salvo R_X0/R_X2. No toques los archivos de S11.1 ni de S11.2, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
