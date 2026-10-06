# Encargo para Codex — S9, CH2/CH3 a 1 MHz con la AD8039 y el LM6172 como variante

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):** CLI de la aplicación `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe`, `-m gpt-6.1-sol`, esfuerzo `medium`, como proceso independiente (`Start-Process`), prompt por stdin desde un fichero y `-o` para la respuesta final.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH23_entrada
Base de CH1 (SÓLO LECTURA): ...\03_simulaciones\CH1_entrada  (comun\ch1_comun_s7b.inc y lo que incluye)
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md; el LM6172 en models\LM6172\)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…).
Lee los ficheros enteros. Si vas justo de tiempo o de cupo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, `CH23_entrada/PLAN_SIMULACION_S9.md`, que es tu contrato, y los documentos que manda leer.
2. **Abre tu diario en `ai-context/journal/` al empezar y ve completándolo** (en S4 y S7b te quedaste sin cupo; el diario es lo que permite reanudar).
3. Extrae los datos de la hoja del LM6172 (§2 del plan) y haz **K0** antes de nada más. Si el orden de pines o el modelo no cuadran con la hoja, para la variante B, anótalo y sigue con A.
4. Escribe `comun/ch23_comun_s9.inc` y comprueba K1 nominal a 5 mV/div y 0.5 V/div en las dos variantes, y el reparto del Monte Carlo (10 casos). **Informa de esos números en el diario antes de la campaña.**
5. Escribe `ejecutar_s9.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke`, `--resume` y `S3G4_MODELS`. Monte Carlo en continua con puntos `.op`, tiempo límite y un reintento. Orden de columnas fijo en los CSV. Los registros, fuera de la comprobación de ficheros protegidos.
6. Pasa `--smoke` y después la campaña completa. Prioridad: K0, K1, K3, K4, K5, K6, K7, K2, K8.
7. Escribe el acta y cierra el diario.

## Reglas

- **No cambies valores fuera del §1 del plan, no elijas variante y no elijas remedios.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, variante, escala, caso de Monte Carlo, nivel, polaridad), y ese estado tiene que ser el real del circuito.
- No toques `../CH1_entrada/`, `Simulation_LTSpice/models/`, `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- K0: datos de la hoja del LM6172 frente al modelo;
- valores E96 elegidos para el filtro (y los de B si hubo que reoptimizar);
- tabla S9-C1…C9 con la fracción de placas, **A | B lado a lado**;
- K1 por escala (−3 dB, pico, atenuación a 1.73 y 2.47 MHz, ganancia con signo);
- Monte Carlo (mínimo, máximo y percentiles 2.5 / 97.5 % de −3 dB, pico, atenuación a 2.47 MHz, ruido y ganancia);
- muestreo de 2.5 ciclos;
- protecciones en los extremos de los rieles;
- consumo por variante;
- dudas.
