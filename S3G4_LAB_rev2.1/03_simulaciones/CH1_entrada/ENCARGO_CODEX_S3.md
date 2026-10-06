# Encargo para Codex — S3, buffer, escalera, 74HC4051 y ganancia ×5 · ×10 con AD8039

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):** CLI de la aplicación `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0), `-m gpt-6.1-sol`, esfuerzo `medium`, como proceso independiente (`Start-Process`), prompt por stdin desde este fichero y `-o` para la respuesta final.

La §0 de `PLAN_SIMULACION_S3.md` está cumplida (3 oct): modelos del AD8039 y del 74HC4051 en el proyecto, comprobados por Claude, y tabla §2.2 completa.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md: orden de nodos)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…).
Lee los ficheros enteros. Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S3.md`, que es tu contrato, y los documentos que manda leer.
2. Parte de tu trabajo de S2b (`comun/ch1_comun_s2b.inc`, `ejecutar_s2b.py`). **No lo modifiques**: S3 va en ficheros nuevos, y `ch1_comun_s3.inc` incluye el de S2b.
3. Escribe `ejecutar_s3.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`.
4. Primero tres comprobaciones aisladas, y sus números antes de la campaña:
   - U103 con la red de §1 a ±5 V: ganancia en continua, −3 dB y pico. Las cifras de Claude están en la §0 del plan y en `chequeo_claude/s3_*.cir` (léelos; no los modifiques);
   - relación de cada toma de la escalera;
   - RON de una instancia de `SWI1` en 0 V y ±2 V, y la polaridad de su control.
5. Pasa `--smoke` y después la campaña completa. Prioridad: E11, E12, E14, E13, E11b, E15.
6. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño para que algo pase.** Si algo falla, se informa con su valor medido y cuánto falta.
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, escala, POS, toma, CPL, RON, polaridad), y ese estado tiene que ser el real del circuito.
- El ruido es el `inoise` de LTspice referido a la fuente de la BNC; la integral se hace en Python sobre los puntos de la simulación.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- la comprobación aislada de U103 y de las tomas;
- tabla S3-C1…C8;
- por escala: pérdida a 2 MHz, pico, ruido en % de división y recuperación de E14;
- diferencial de entrada pico de U103A y U103B en E14 frente al límite de la hoja;
- corriente de reposo por amplificador;
- dudas.
