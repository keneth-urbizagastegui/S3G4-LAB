# Simulaciones LTspice de la rev 2.1

Carpeta **separada a propósito** de `Simulation_LTSpice/`, que contiene las simulaciones de la rev 2.0 con sus actas. Nada de aquí modifica aquella carpeta ni la usa como línea base: la rev 2.0 es una referencia más.

| Carpeta | Qué decide | Estado |
|---|---|---|
| `P4_P7_grueso/` | Atenuador grueso: con relé (P4) o sin relé (P7) | Construida por Codex, auditada por Claude (`AUDITORIA_CLAUDE_P4_P7.md`). Por RF-07 queda P4; la corrección (P4b) se simuló en `CH1_entrada/` |
| `CH1_entrada/` | Canal rápido CH1 completo, de la BNC a PA0: S1–S2b entrada y protección, S3–S3b ganancia, S4 etapa final, S5 filtro, S6 muestreo, S7–S7c canal completo con Monte Carlo | Cerrado y auditado el 3–4 oct (`AUDITORIA_CLAUDE_S*.md`, `ACTA_S7c.md`, `REVISION_CLAUDE_CH1.md`). Base de CH2/CH3: `comun/ch1_comun_s7b.inc` |
| `DMM/` | DMM por bloques: S11.1–S11.4 (bloque 1, bornes y protección; más `REDISENO_BLOQUE1.md` y `GDT_SEGUIMIENTO.md`), S12–S12d (bloque 2, frontal de tensión; `ESTUDIO_BLOQUE2.md`) y S13 (bloque 3, ohmios, diodo y continuidad; `ESTUDIO_BLOQUE3.md`). S11a quedó aparcado. Prompts en `_registros_codex/` | Bloques 1–3 cerrados y auditados (7–8 oct; `AUDITORIA_CLAUDE_*.md`). Siguiente: bloque 4 (corriente). Las corridas `S1*/` se quedan en local; van a git los scripts, las actas y `resultados/` |
| `CH23_entrada/` | S9: CH2/CH3 a 1 MHz y un ADC a 3.47 MSa/s, con la AD8039 y el LM6172 como variante (queda la AD8039) | Cerrada (Codex, 6 oct; auditada por Claude en `ai-context/journal/2026-10-06-claude-auditoria-s9b-s8b.md`). Elegida la AD8039 (DECISIONS, 6 oct) |

Documentos de diseño que gobiernan estas simulaciones:

- `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` (documento vivo, secciones B–F) y `01_diseno/revision_entrada_ch1.html` (plan S0–S8).
- `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html` (P1–P6), `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html` (P7) y `S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html` (P8–P11).

`ejecutar_todo.py` usa rutas relativas: funciona desde cualquier ubicación de la carpeta.

Convenciones (las mismas que en la rev 2.0): LTspice 26 en modo lote (`-b`); cada ensayo `.asc` lleva dentro sus medidas `.meas`; cada carpeta cierra con un acta de resultados.

**Qué está en git (6 oct):** scripts (`*.py`), actas y encargos (`*.md`), modelos e includes de `comun/` y las tablas de `resultados/`. Las corridas (decks generados, `.raw`, `.log`, `.db` y consolas de `S*/` y `chequeo_claude/`) se quedan en local y se regeneran con los scripts; las reglas están en `.gitignore`.
