# 2026-10-04 — Claude Code: cómo retomar tras cerrar CH1 (S8 y S9)

Resumen para el chat siguiente. El detalle de la sesión está en `2026-10-03-claude-s3-u103.md` (del 3 oct a la madrugada del 4).

## Dónde estamos

- **CH1 (canal rápido) está cerrado en simulación:** S0–S7c, todo auditado (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_*.md`, `ACTA_S7c.md`, `REVISION_CLAUDE_CH1.md`).
- **Resultado:**
  - 2.0 MHz a −3 dB en las 12 escalas; 21.7 dB a 4.5 MHz (alias); subida de 182 ns; ruido de 0.25–0.32 % div (0.41–0.45 % con el ADC);
  - protegido con ±100 V y ESD de ±4/±8 kV;
  - en el Monte Carlo de 500 placas con tolerancias reales, todos los criterios en ≥ 95 % (casi todos al 100 %), y el trimmer en el 100 % con las tolerancias nuevas.
- **Documento vivo actualizado** (versión 16, https://claude.ai/artifact/YLrJwmm5Cz6w864dUYsrBT): C.6 con los valores finales; nuevas secciones **D** (filtro), **E** (etapa final y offset) y **F** (driver del ADC); G con el consumo real, los rieles de ±4.9 V, la regla de encendido y la propuesta del jack.
- **Criterio permanente de Keneth (DECISIONS 3 oct):** «no quiero la perfección, quiero que funcione»: tolerancias reales, ≥ 95 % de placas, criterios funcionales y componentes con margen (≤ 80 % de tensión, ≤ 50 % de potencia y corriente).

## Cadena final de CH1 (fuente de verdad: `DECISIONS.md` del 3–4 oct y `comun/ch1_comun_s7b.inc`)

| Bloque | Piezas |
|---|---|
| Entrada | BNC Kinghelm C2837587; acoplo SS23H37L6 (C883267); relé HFD27/005-S (C23911), monoestable DPDT, reposo en ÷100 |
| Divisor ÷100 | R1A/R1B 2 × 549 kΩ 0.1 % 1206; **C1A 20 pF ±2 % 250 V (C3845779)**; **C1B 15 pF ±2 % 250 V (C3836120) ∥ trimmer SEHWA 2–6 pF (C22468120) ∥ hueco DNP 0603**; R2 11.0 kΩ 0.1 %; **Cb 1 nF ±1 % (C507408) + 68 pF ±5 %** |
| Rama ×1 | R_S 2 × 49.9 kΩ 1206; **C_S 1.2 nF C0G ≥ 200 V**; réplica R_EQ 10 MΩ 1206 ∥ **C_EQ ≈ 8.7 pF ≥ 200 V** (seleccionado en prueba) |
| Protección | BAV199 (C40919) a los rieles; TVS de riel por elegir; C_AC 1.8 nF; R_BIAS 10 MΩ; R_PROT 1 kΩ |
| Buffer | U101 OPA810 (C2833513) |
| Escalera | RL 499 / 249 / 150 / 49.9 / 24.9 / 24.9 Ω; U102 74HC4051 (C9386); Y6 = GND; **Y7 = VCHECK (12.4 kΩ / 100 Ω 0.1 % desde VREF+)** |
| Ganancia | U103 AD8039 (C96525): 1.00 k / 249 Ω (×5.016) y 2.26 k / 249 Ω (×10.08); **470 Ω + BAV99 (C2500)** en IN+ de cada etapa |
| Filtro | U105 AD8039: Sallen-Key 1.11 kΩ / 56 pF / 47 pF y 499 Ω / 220 pF / 56 pF |
| Etapa final | U106 OPA836 (C111589) a 3.3 V: R_IN = R_F = 10.0 kΩ, C_F 1 pF, R_OFF 8.06 kΩ desde el DAC (PA4/PA5/PA6); VMID: 10.0 k / 5.23 k desde VREF+ + 1 µF |
| Pin | 68 Ω + 470 pF C0G → PA0 (ADC1 + ADC2 entrelazados) |
| Rieles | **±4.90 V** (LM27762 reajustado); VDDA 3.3 V; VREF+ 2.5 V (REF3325) |
| Control | 2 × 74HCT595: 3 líneas del 4051 + relé por canal |

## Lo siguiente

1. **S8, esquema de CH1 en KiCad:**
   - el proyecto está en `S3G4_LAB_rev2.1/04_esquematicos/kicad/` (con su `AGENTS.md`); herramientas y trampas en la memoria «entorno-kicad10-ia» de Claude;
   - hoja jerárquica de CH1: entrada (A/B/C.2), ganancia (C), filtro + final + pin (D/E/F);
   - valores y nombres de red **del acta y de `ch1_comun_s7b.inc`, nunca de memoria**;
   - reglas de placa (4 capas, contorno y clases de red) las escribe Keneth (PLAN, paso 9).
2. **S9, CH2/CH3 a 1 MHz:**
   - copia de CH1 con el filtro escalado (R ≈ 2.49 kΩ y ≈ 1.10 kΩ, mismos C; reajustar en simulación a 1.0 MHz);
   - muestreo de 2.5 ciclos (48 ns, un solo ADC a 3.47 MSa/s);
   - Monte Carlo con el criterio de tolerancias;
   - abierto: el disparo de CH2/CH3 (PE9/PE15 no llegan a ningún comparador).
3. **Abiertos menores:**
   - rehacer G.3/G.4 con 23 mA por riel;
   - resistencias del LM27762 para ±4.9 V;
   - reservar PA4–PA6 en el mapa de pines;
   - economizador del relé;
   - TVS de riel;
   - medir en el prototipo el estado del condensador de muestreo del ADC y el glitch del 4051 (`REVISION_CLAUDE_CH1.md` §5).

## Cómo trabajar con Codex (lecciones de esta sesión)

- CLI: `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe`, `-m gpt-6.1-sol -c model_reasoning_effort=medium`, con `Start-Process`, prompt por stdin y `-o`. Vigilar el fichero `-o` y el PID con Monitor (se renueva cada 30 min).
- **Cupo de ChatGPT:** Codex se quedó sin cupo dos veces (S4 a las 18:34 y S7b a las 23:06; se renueva a una hora fija que da el error). Pedirle que **abra su diario al empezar** y que su script admita `--resume`. Si se corta, relanzar con un prompt de reanudación que apunte a su diario y a una nota de Claude.
- **Convergencia:** los barridos `.dc` con placas de Monte Carlo se colgaron; Codex lo resolvió con puntos `.op`, tiempo límite y reintento. Pedirlo desde el principio en planes con Monte Carlo en continua.
- **Registros fuera de la carpeta vigilada:** el script marca código 1 si cambia un fichero protegido.
- **Auditoría de los criterios:** varios «fallos» venían de criterios mal planteados por Claude (E14 de S3, F5 de S4, E18 de S6). Revisar que el estímulo llegue al caso que se quiere ver.
- **Macromodelos:** el AD8038 de LTspice da el doble de ruido que la hoja (copia corregida `AD8038_ltspice_ruido_hoja.sub`); el OPA810 da 1.9 mA de reposo frente a 3.7 de la hoja; el OPA836 de TI no trae los diodos entre entradas.

## Memoria compartida

- `tools/ai-context/sync.mjs` admite `excludeDirs` y `excludeFiles`; el límite es de 400 fuentes. El índice excluye `ENCARGO_CODEX_*`, `RESPUESTA_FINAL_*`, `*_resumen.md` y las carpetas de salida de simulación (`ai-context/SOURCES.md`). 198 fuentes a 4 oct.
EOF
## Reproducción de muestra (hecha el 4 oct, 03:00)

- S7 `--quick`: valores idénticos bit a bit (J1 en 5 mV y 0.5 V/div y J9).
- S7b `--smoke`: 15/15 CSV con los mismos valores (diferencia ≤ 7·10⁻¹⁶).
- Anotado en `AUDITORIA_CLAUDE_S7.md` y `AUDITORIA_CLAUDE_S7b.md`. Las campañas completas no se reejecutaron (38 min y 2 h).
