# Encargo para Codex — S3b, protección de la diferencial de U103A

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
Lee los ficheros enteros. Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S3b.md`, que es tu contrato, y los documentos que manda leer.
2. Parte de tu trabajo de S3 (`comun/ch1_comun_s3.inc`, `ejecutar_s3.py`). **No lo modifiques**: S3b va en ficheros nuevos.
3. Escribe `ejecutar_s3b.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`.
4. Primero B0 y los dos controles de ruido de §1.3. Informa esos números antes de la campaña.
5. Pasa `--smoke` y después la campaña completa. Prioridad: B3, B2, B1, B4, B5, B6.
6. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño fuera de R_SER y de los diodos de §1.** Si algo falla, se informa con su valor medido y cuánto falta.
- **No elijas variante.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, variante, escala, POS, toma, polaridad, temperatura), y ese estado tiene que ser el real del circuito.
- El transitorio no pasa de ±4.5 V en la BNC (el ±40 V de S3 no convergía); los límites en saturación se miden con `.dc`.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- B0 y los controles de ruido;
- tabla S3b-C1…C6 por variante (A, B, C, D);
- en B3, por variante: diferencial pico de U103A y U103B, corriente del 4051 y de los diodos;
- ruido máximo por variante;
- offset de B6;
- dudas.
