# Encargo para Codex — simulación P4 frente a P7

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\P4_P7_grueso
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe
                    Modo lote:  "…\LTspice.exe" -b "C:\…\T01_zin.asc"   → deja T01_zin.log al lado, con los .meas
Python 3.12 está en el PATH, con numpy. Python es nativo de Windows: usa rutas de Windows
(C:\…), NO rutas estilo /c/Users/… de Git Bash, o dará FileNotFoundError sobre ficheros que existen.
Lee los ficheros enteros; no dependas de búsquedas por patrón sobre rutas con espacios.
Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y **entero** `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/PLAN_SIMULACION.md`. El plan es el contrato: valores, ensayos, criterios, entregables y lo que no es tuyo.
2. Mira un ensayo de la rev 2.0 como patrón de estilo, por ejemplo `Simulation_LTSpice/Oscilloscope/04b_atenuador_comp.asc` y el acta `Simulation_LTSpice/Oscilloscope/ACTA_RESULTADOS_CANAL_OSCILOSCOPIO.md`. **Sólo lectura: no modifiques nada en `Simulation_LTSpice/`.**
3. Construye los entregables de §7 del plan, en este orden de prioridad por si no llegas: T04 (ruido), T06 (supervivencia), T05 (señales grandes), T02, T03, T01 y T07.
4. Ejecuta `ejecutar_todo.py` y comprueba que todos los `.asc` corren sin error ni advertencia. Informa el código de salida.
5. Escribe el acta y tu diario.

## Reglas

- **No elijas entre P4 y P7** ni lo recomiendes: mide y describe.
- **No cambies valores de diseño para que algo pase.** Un criterio que falla se informa con su valor medido.
- **Las contradicciones se anotan, no se resuelven.** Si el plan choca con sus fuentes, contigo mismo o con lo que da la simulación, va a la lista de dudas del acta con lo que viste.
- Cada `.meas` lleva en el nombre el estado en que se midió (diseño, escala o posición, fuente), y ese estado tiene que ser el real del circuito en ese ensayo.
- En potencia, el criterio incluye la reducción (≤ 60 % de la nominal en continuo), no sólo «no se quema».
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario en `ai-context/journal/`.
- No descargues nada de internet.

## Respuesta final

Un resumen corto con: ficheros creados, código de salida de `ejecutar_todo.py`, tabla de criterios C1–C9 por diseño (valor medido y pasa/falla), las discrepancias de más del 30 % con los valores de referencia de T04, y la lista de dudas.
