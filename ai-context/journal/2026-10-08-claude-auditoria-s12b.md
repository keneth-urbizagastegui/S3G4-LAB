# 2026-10-08 — Claude (Opus) — auditoría de S12b (DMM bloque 2 con buffer)

- Cambio: `03_simulaciones/DMM/AUDITORIA_CLAUDE_S12b.md` y scripts en `DMM/chequeo_claude/s12b/`. Sin tocar archivos de Codex, STATE ni DECISIONS.
- Evidencia: smoke reejecutado de cero en `C:\s12b` (11/11, métricas idénticas); E3, E5 y E8 recalculados desde el `.raw`.
- Hallazgos:
  - E3 es un error estático (buffer X1 con 5.045 V por encima del modo común); ≤ 0.23 cuentas con fondo de 48 V.
  - E2: 83 % de la fuga supuesta de 0.85 nA × 99 kΩ en la entrada de X0; la tolerable es 0.80 nA.
  - E5: CD(ON) concentrada detrás de Ron; repartida da 42–43.6°.
  - E8: los 22 mA son capacitivos (3 ns); la pinza llega como máximo a 3.86 mA en los 148 casos.
  - E6: especificación propuesta para Rc (≥ 1.5 kV de impulso, ≥ 25 µJ).
- Pendientes (propuestas, no aceptadas): fondo de 50 V ≤ 48 V, criterios E2/E8 reescritos, repetición pequeña de E5, MPN de Rc.
