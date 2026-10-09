# Retomar el DMM por bloques (8 oct 2026, Claude Opus 5.5)

Punto de retomada para un chat nuevo. Resume lo hecho entre el 7 y el 8 oct después de la síntesis de referencias; la crónica completa está en `STATE.md` y en los diarios del 7 y el 8 oct.

## Método acordado con Keneth

- **El DMM se diseña por bloques:**
  1. bornes y protección;
  2. frontal de tensión;
  3. ohmios, diodo y continuidad;
  4. corriente;
  5. driver diferencial y ADC5.
- **Cada bloque sigue cuatro pasos:**
  1. un **estudio previo** (Sonnet 5.5, esfuerzo alto) con opciones y una tabla de decisiones;
  2. **Keneth decide**;
  3. **una simulación con Codex** (gpt-6.1-sol, esfuerzo low; plan `PLAN_SIMULACION_*.md`);
  4. **una auditoría** (Opus 5.5, esfuerzo medio; `AUDITORIA_CLAUDE_*.md`), y se cierra el bloque.
- **Reparto de modelos** (memoria `sonnet-para-construir`): Opus medio audita, Codex construye y Sonnet alto se encarga de los estudios, las simulaciones pequeñas y KiCad/Konnect.
- **Criterio de Keneth** (DECISIONS del 8 oct; memoria `criterio-tolerancias-keneth`):
  - que funcione con margen, sin complicar;
  - los criterios se fijan con margen realista;
  - los fallos marginales de modelo o de criterio se clasifican y no se persiguen;
  - lo que solo se mide en banco queda para el prototipo.
- **Cómo se lanza Codex:**
  - CLI `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe` (0.162.0-alpha.2; la carpeta cambia con las actualizaciones, así que hay que buscarla antes de lanzar);
  - `exec -m gpt-6.1-sol -c model_reasoning_effort="low" --dangerously-bypass-approvals-and-sandbox -C <raíz> -o <respuesta> -`;
  - con `Start-Process`, el prompt por stdin desde `03_simulaciones/_registros_codex/prompt_*.txt` y un Monitor que vigila el PID;
  - los registros (`*.log`) se quedan en local.
- **Las corridas** (`DMM/S1*/`, .raw) se quedan en local (.gitignore). Van a git los scripts, las actas, los prompts y `resultados/`.

## Estado de los bloques

| Bloque | Estado | Simulaciones | Piezas clave |
|---|---|---|---|
| 1 · Bornes y protección | **Cerrado** | S11.1–S11.4 y el estudio del GDT | Tensión: R_PROT 3 × 33 kΩ antipulso, divisor de 10 MΩ, GDT SMD4532-600NF + varistor 14D431K. Ohmios (60 V, como el ELVIS): relé TQ2SA, 3 × 510 Ω (cambiado en el bloque 3), SMAJ12CA, R_S 2.7 kΩ, BAV199 y zéner, BAT54. A: Littelfuse 0216 3.15 A, GBU808 y 10 kΩ hacia B. Bornes Amass 24.245.1/.2 |
| 2 · Frontal de tensión | **Cerrado** | Estudio, S12, S12b, S12c y S12d | **OPA4192** (buffers de X0 y X2 y amplificador A); **sin toma ÷10** (el rango de 20 V va por ÷100 ×10); divisor de 6 × 1.5 MΩ + 910 kΩ + 100 kΩ (Yageo RT1206 al 0.1 %); 74HCT4051; TMUX4053 con 91 k/10 k; 10 kΩ delante de los buffers; compensación en C0G con 3.3 kΩ antipulso; alterna corregida por firmware |
| 3 · Ohmios, diodo y continuidad | **Cerrado** | Estudio y S13 | La fuente P43 **inyecta en N1** (c1); BSS84 de paso; TLV2372 + BSS138; compensación de 1 kΩ + 1 nF; R_k de 499 Ω / 4.99 k / 49.9 k / 420 k / 1.7 MΩ (1 mA … 0.30 µA); diodo por X2 ×10.1 (LED a 100 µA, silicio a 1 mA); continuidad a 1 mA en 31 µs; **sin P33** |
| 4 · Corriente | **Siguiente** | — | La sección H: derivador de 0.1 Ω Kelvin y amplificador B ×10. Ojo: B debe ir ahora en el OPA4192 o en otra pieza |
| 5 · Driver y ADC5 | Pendiente | — | Idea de Keneth: usar dos OPAMP internos del G473 como driver (su entrada de 0–3.3 V cabe ahí); validar las conexiones, el ruido y OPAMP5, que está reservado para la continuidad |

## Pendientes antes de fabricar (no impiden seguir)

- **MPN antipulso:** R_PROT, las 510 Ω (HoCR2512), las 3.3 kΩ de la compensación (≥ 1.5 kV a 1.2/50 µs, ≥ 25 µJ, ΔR ≤ 1 %), el BSS138, la hoja del fabricante del GDT y el interruptor de carga del DMM.
- **Prototipo:**
  - ESD IEC 61000-4-2 y red a 230/253 Vrms;
  - fuga en X0 ≤ 0.5–0.6 nA (deriva del offset de 18 a 28 °C ≤ 4 cuentas en 200 mV y 20 V);
  - fuga de los 4051 de la fuente ≤ 1 nA (si no, TMUX1208);
  - compliancia a 1 mA ≥ V_x + 0.25 V;
  - escalón ×1/×10 (margen ≥ 40°);
  - INL real del ADC5.
- **Firmware:**
  - espera del autocero: 3 ms en X2 y 0.1 ms en X0;
  - 50 ms en 20 MΩ;
  - P34 leyendo X2 con la fuente apagada;
  - corrección de alterna calibrada a 100 Hz, 1 kHz y 20 kHz.

## Documentos

- `01_diseno/dmm_bloque1.html` (artefacto WuPMtdkmWQVFsjsLy4jSzz): esbozo del bloque 1. Todavía no recoge el cambio a 3 × 510 Ω del bloque 3.
- `01_diseno/dmm_rev21.html` (sección H, artefacto 4iveEdvtCBTvhQj9jHjsvY): su aviso inicial resume qué queda superado por los bloques 1–3. El cuerpo es el diseño de partida: **no usarlo como diseño vigente** de esas partes.
- `00_requisitos/especificaciones_dmm.html` (artefacto 9wuyJcNBxPcee2dNuThttm): actualizada el 8 oct con lo que cambiaron los bloques 1–3.
- Simulaciones y estudios: `03_simulaciones/DMM/`:
  - ESTUDIO_BLOQUE2/3;
  - REDISENO_BLOQUE1;
  - GDT_SEGUIMIENTO;
  - planes, actas y auditorías S11.1–S13.

## Siguiente

**Bloque 4 (corriente)** con el mismo método: primero el estudio con Sonnet (derivador, Kelvin y punto estrella, amplificador B, protección GBU808/fusible, ganancias 200 mA / 2 A, autocalentamiento) y después las decisiones de Keneth.
