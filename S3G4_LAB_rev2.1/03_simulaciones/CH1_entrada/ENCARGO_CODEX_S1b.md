# Encargo para Codex — S1b, trimmer, sonda corregida y C_EQ en prueba

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento:**
- CLI de la aplicación: `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0 desde el 3 oct; antes `…\be3fd7e5c1969ff6\…`). El CLI del PATH (0.154.0) rechaza `gpt-6.1-sol`.
- `-m gpt-6.1-sol`. Esfuerzo recomendado: `medium`. En S1, con `low`, la comprobación de convergencia se hizo en el caso que no la revelaba.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Python 3.12 en el PATH, con numpy y scipy. Usa rutas de Windows (C:\…), no /c/Users/….
Lee los ficheros enteros; no dependas de búsquedas por patrón sobre rutas con espacios.
Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, en `CH1_entrada/`, enteros:
   - `PLAN_SIMULACION_S1b.md`, que es tu contrato;
   - `PLAN_SIMULACION_S1.md`, que sigue vigente salvo lo que S1b cambia;
   - `ACTA_S1.md`;
   - `AUDITORIA_CLAUDE_S1.md`.
2. Parte de tu propio trabajo de S1 (`comun/ch1_comun.inc`, `ejecutar_s1.py`) como patrón. **No lo modifiques**: S1b va en ficheros nuevos.
3. Construye los entregables de §6 del plan. Prioridad si no llegas: E1b/E2b, E3b, E4A con los tres rangos, E4B.
4. Ejecuta `ejecutar_s1b.py`; informa el código de salida y cuántas simulaciones dieron error o advertencia.
5. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño para que algo pase.** Sólo se recalculan los derivados que el plan indica.
- **Las contradicciones se anotan, no se resuelven.** Van a la lista de dudas del acta.
- Cada `.meas` lleva en el nombre su estado (POS, CPL, rango del trimmer, campaña y caso), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario en `ai-context/journal/`. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida;
- tabla S1b-C1…C9 (valor y pasa/falla);
- rango de trimmer mínimo que cumple C6 y cuántos casos quedaron contra tope con cada rango;
- de la campaña B: ΔCin antes y después de seleccionar C_EQ;
- dudas.
