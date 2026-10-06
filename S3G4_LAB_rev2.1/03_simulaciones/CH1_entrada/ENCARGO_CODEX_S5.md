# Encargo para Codex — S5, filtro anti-alias de CH1 (U105, AD8039 doble)

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):** CLI de la aplicación `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0), `-m gpt-6.1-sol`, esfuerzo `medium`, como proceso independiente (`Start-Process`), prompt por stdin desde un fichero y `-o` para la respuesta final.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…).
Lee los ficheros enteros. Si vas justo de tiempo o de cupo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S5.md`, que es tu contrato, y los documentos que manda leer.
2. **Abre tu diario en `ai-context/journal/` al empezar y ve completándolo.** En S4 te quedaste sin cupo antes de escribirlo.
3. Parte de tu trabajo de S4 (`comun/ch1_comun_s4.inc`, `ejecutar_s4.py`). **No lo modifiques**: S5 va en ficheros nuevos.
4. `sintesis_s5.py`: repite el cálculo de §2 del plan, sintetiza los tres candidatos en E96/E12 y comprueba cada sección aislada. Informa de la tabla antes de la campaña.
5. Escribe `ejecutar_s5.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`. Orden de columnas fijo en los CSV. Los registros, fuera de la comprobación de ficheros protegidos.
6. Pasa `--smoke` y después la campaña completa. Prioridad: G1, G2, G3, G5, G6, G4.
7. Escribe el acta y cierra el diario.

## Reglas

- **No cambies S1–S4 ni los polos fijos. No elijas candidato.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, candidato, escala, caso de Monte Carlo, polaridad), y ese estado tiene que ser el real del circuito.
- En transitorio, la BNC no pasa de ±4.5 V.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- tabla de componentes;
- tabla S5-C1…C8 por candidato;
- tabla comparativa: −3 dB, atenuación a 3.25, 4.5 y 6.5 MHz, sobreimpulso, subida, ruido y Monte Carlo;
- dudas.
