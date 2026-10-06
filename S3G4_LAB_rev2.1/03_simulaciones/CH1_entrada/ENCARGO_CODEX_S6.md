# Encargo para Codex — S6, ataque al ADC (muestreo entrelazado del G473)

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

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S6.md`, que es tu contrato, y los documentos que manda leer.
2. **Abre tu diario en `ai-context/journal/` al empezar y ve completándolo.** En S4 te quedaste sin cupo antes de escribirlo.
3. Parte de tu trabajo de S4 y S5 (`comun/ch1_comun_s4.inc`, `comun/ch1_comun_s5.inc`, `ejecutar_s5.py`). **No lo modifiques**: S6 va en ficheros nuevos.
4. Primero H0: deduce R_SW y comprueba la temporización de los interruptores. Informa de esos números antes de la campaña.
5. Escribe `ejecutar_s6.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`. Orden de columnas fijo en los CSV. Los registros, fuera de la comprobación de ficheros protegidos.
6. Pasa `--smoke` y después la campaña completa. Prioridad: H1, H2, H4, H3.
7. Escribe el acta y cierra el diario.

## Reglas

- **No cambies el circuito ni elijas remedios.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, R_SW, estado previo P/Z/R, frecuencia, nivel), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- R_SW deducida y temporización;
- tabla S6-C1…C5;
- error en continua y a 2 MHz (máximo y rms, por ADC), con la descomposición lineal / no lineal y la FFT;
- sensibilidad a R_SW y al estado previo;
- margen de fase;
- dudas.
