# Encargo para Codex — S2b, ESD realista, piezas de 200 V y capacidad del buffer

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):** CLI de la aplicación `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0), `-m gpt-6.1-sol`, esfuerzo `medium`, como proceso independiente (`Start-Process`).

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

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S2b.md`, que es tu contrato, y los documentos que manda leer.
2. Parte de tu trabajo de S2 (`comun/ch1_comun_s2.inc`, `ejecutar_s2.py`). **No lo modifiques**: S2b va en ficheros nuevos.
3. Construye primero el generador de ESD y verifícalo sobre 2 Ω (E7a). Sin eso, E7b y E7c no valen.
4. Pasa `--smoke` y después la campaña completa. Prioridad: E7a, E0b, E5b, E7b, E7c, segunda fuente si hay modelo.
5. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño para que algo pase.** Si algo falla, se informa con su valor medido.
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, POS, CPL, nivel, contacto o aire, alimentación, variante), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- la verificación del generador (cuatro puntos a 4 y 8 kV);
- tabla S2b-C1…C5;
- I²t por diodo a ±4 kV, a ±8 kV en contacto y a 8 kV en aire;
- si hubo segunda fuente;
- dudas.
