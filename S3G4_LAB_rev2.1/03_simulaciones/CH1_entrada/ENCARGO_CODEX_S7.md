# Encargo para Codex — S7, canal CH1 completo de la BNC a PA0 (acta final)

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

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S7.md`, que es tu contrato, y los documentos que manda leer.
2. **Abre tu diario en `ai-context/journal/` al empezar y ve completándolo.** En S4 te quedaste sin cupo antes de escribirlo.
3. Parte de tu trabajo de S2b–S6 (`comun/ch1_comun_s*.inc` y `ejecutar_s*.py`) y de los decks de auditoría `chequeo_claude/s3b/y_*_g_*.cir`. **No los modifiques**: S7 va en ficheros nuevos.
4. Primero escribe `comun/ch1_comun_s7.inc` y una comprobación rápida: J1 a 5 mV/div y 0.5 V/div, y el reposo de J9. Informa de esos números antes de la campaña.
5. Escribe `ejecutar_s7.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`. Orden de columnas fijo en los CSV. Los registros, fuera de la comprobación de ficheros protegidos.
6. Pasa `--smoke` y después la campaña completa. Prioridad: J1, J5, J4, J2, J3, J6, J8, J9, J7.
7. Escribe el acta y cierra el diario.

## Reglas

- **No cambies valores ni elijas remedios: es la integración de lo decidido.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, escala, caso de Monte Carlo, nivel, polaridad), y ese estado tiene que ser el real del circuito.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- tabla S7-C1…C9;
- por escala: −3 dB, ganancia en continua con signo, subida, ruido y atenuación a 4.5 MHz;
- Monte Carlo;
- límites de J5;
- consumo por etapa y por canal;
- dudas.
