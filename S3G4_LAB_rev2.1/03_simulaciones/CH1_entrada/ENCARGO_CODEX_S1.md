# Encargo para Codex — S1, entrada pasiva P4b de CH1

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Modelo (probado el 2 oct con la cuenta de ChatGPT):** responden `gpt-6-astra`, `gpt-5.6-sol` y `gpt-5.6-terra`. Fallan con error 400 («not supported when using Codex with a ChatGPT account») `gpt-6.1-sol` (el de `~/.codex/config.toml`), `gpt-6-sol` y `gpt-6-luna`. Lanzar con `-m` explícito. **Corrección del 2 oct (noche):** el rechazo de `gpt-6.1-sol` venía del CLI viejo del PATH (`…\Programs\OpenAI\Codex\bin\codex.exe`, 0.154.0). El CLI de la aplicación (`C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0 desde el 3 oct; antes `…\be3fd7e5c1969ff6\…`), 0.159.0-alpha) sí lo acepta. S1 se lanzó con ese CLI, `gpt-6.1-sol` y esfuerzo `low`, por decisión de Keneth. Recomendado: `gpt-6-astra` con esfuerzo `medium`; alternativa probada en P4/P7: `gpt-5.6-sol` con `high`. Prueba de entorno OK: Python 3.12.10 con NumPy 2.4.6 y SciPy 1.17.1, LTspice en lote con `.cir`, MCP ltspice, pcbparts y s3g4-context, lectura del plan y escritura en `CH1_entrada/`.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe
                    Modo lote:  "…\LTspice.exe" -b "C:\…\E1_zin.cir"   → deja E1_zin.log al lado, con los .meas
Python 3.12 está en el PATH, con numpy. Python es nativo de Windows: usa rutas de Windows
(C:\…), NO rutas estilo /c/Users/… de Git Bash, o dará FileNotFoundError sobre ficheros que existen.
Lee los ficheros enteros; no dependas de búsquedas por patrón sobre rutas con espacios.
Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y **entero** `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/PLAN_SIMULACION_S1.md`. El plan es el contrato: circuito, valores, pruebas, criterios, entregables y lo que no es tuyo.
2. Lee `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md` y usa `P4_P7_grueso/` como patrón de estilo. **Sólo lectura.**
3. Construye los entregables de §6 del plan. Orden de prioridad por si no llegas: E1, E2, E3, E4.
4. Ejecuta `ejecutar_s1.py` y comprueba que todo corre sin error ni advertencia. Informa el código de salida.
5. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño para que algo pase.** Un criterio que falla se informa con su valor medido.
- **Las contradicciones se anotan, no se resuelven.** Si el plan choca con sus fuentes, contigo mismo o con la simulación, va a la lista de dudas del acta con lo que viste.
- Cada `.meas` lleva en el nombre el estado en que se midió (POS, CPL, CT1), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario en `ai-context/journal/`.
- No descargues nada de internet.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida de `ejecutar_s1.py`;
- tabla de S1-C1…S1-C5 por caso (valor medido y pasa/falla);
- de E4: peor caso de ΔCin y de la desviación a 1 MHz, y el parámetro que lo produce;
- la lista de dudas.
