# Plan de simulación P4 (relé) frente a P7 (sin relé)

- Fecha: 2026-09-23, noche. Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: preparar la simulación en LTspice de P4 frente a P7, en una carpeta **separada** de las simulaciones existentes, y planificarla en detalle porque la construirá **Codex (GPT-6-Sol, esfuerzo medium)**; Claude audita su trabajo.
- *Corrección posterior:* GPT-6-Sol devuelve HTTP 400 con la cuenta de ChatGPT. Keneth eligió **gpt-5.6-sol**, esfuerzo medium, y con ese modelo se lanzó (tarea `task-muenuphs-puqefo`).

## Cambio

- Nueva carpeta `Simulation_LTSpice_rev21/` (separada de `Simulation_LTSpice/`, que es de la rev 2.0), con `LEEME.md`.
- `Simulation_LTSpice_rev21/P4_P7_grueso/PLAN_SIMULACION.md`: los dos diseños con valores y derivaciones, tramo común, parámetros y barridos, siete ensayos (T01 Zin/Cin, T02 respuesta, T03 escalón, T04 ruido, T05 señales grandes y rodilla de P7, T06 supervivencia 50 V y 250 Vrms, T07 robustez), criterios C1–C9, entregables, límites y cómo se auditará.
- `ENCARGO_CODEX.md`: texto para pegar a Codex, con el bloque de entorno (ruta de LTspice, rutas de Windows para Python, espacio en la ruta).
- Subcarpetas vacías: `comun/`, `P4_rele/`, `P7_sin_rele/`, `resultados/`.
- No se ejecutó ninguna simulación todavía. No se tocó `Simulation_LTSpice/`.

## Valores de referencia que la auditoría contrastará

Ruido referido a la entrada (1 polo a 1.5 MHz, amplificadores de 7 nV/√Hz): P4 ≈ 15 µV (5 mV/div), 0.43 mV (200 mV/div), 1.5 mV (500 mV/div); P7 ≈ 42 µV, 0.86 mV, 3.1 mV. Rodilla de P7 esperada en ±11.2 V en la BNC.

## Pendientes

1. Lanzar el encargo a Codex (Keneth decide si lo lanza él o Claude con el plugin).
2. Auditar el resultado según §9 del plan y registrar la decisión P4/P7 cuando Keneth la tome.
