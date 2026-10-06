# Encargo para Codex — S2, protección y abusos de la entrada P4b de CH1

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):**
- CLI de la aplicación: `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0). El CLI del PATH (0.154.0) rechaza `gpt-6.1-sol`.
- `-m gpt-6.1-sol`, esfuerzo `medium`.
- Como proceso independiente (`Start-Process`), no como tarea en segundo plano de Claude Code: esas se cortan a la hora.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\  (opa810.pdf, AD8065_8066 (1).pdf, BAV199.pdf)
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…), no /c/Users/….
Lee los ficheros enteros; no dependas de búsquedas por patrón sobre rutas con espacios.
Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros:
   - en `CH1_entrada/`: `PLAN_SIMULACION_S2.md`, que es tu contrato, y los documentos que manda leer (planes, actas y auditorías de S1 y S1b);
   - `Simulation_LTSpice/models/LEEME.md`.
2. Parte de tu propio trabajo de S1b (`comun/ch1_comun_s1b.inc`, `ejecutar_s1b.py`) como patrón. **No lo modifiques**: S2 va en ficheros nuevos.
3. Construye los entregables de §6. `ejecutar_s2.py` es **paralelo desde el principio** (10 trabajadores) y tiene modo `--smoke`; pásalo primero.
4. Prioridad si no llegas: E0, E5, E6, E7, E9, E10, E8, segunda fuente.
5. Ejecuta la campaña completa; informa el código de salida, cuántas simulaciones dieron error o advertencia, y el tiempo.
6. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño para que algo pase.** Si una pieza se queda corta, se informa con su valor medido.
- **Las contradicciones se anotan, no se resuelven.** Si la hoja de una pieza contradice el plan, usa la hoja y anótalo.
- Cada `.meas` lleva en el nombre su estado (prueba, POS, CPL, polaridad, variante, buffer), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario en `ai-context/journal/`. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- tabla S2-C1…C8 (valor y pasa/falla);
- tiempos de E8;
- diferencias de la segunda fuente;
- piezas que se quedan cortas, si alguna;
- dudas.
