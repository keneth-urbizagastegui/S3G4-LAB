# Encargo para Codex — S4, etapa final a 3.3 V con offset (OPA836)

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):** CLI de la aplicación `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0), `-m gpt-6.1-sol`, esfuerzo `medium`, como proceso independiente (`Start-Process`), prompt por stdin desde un fichero y `-o` para la respuesta final.

La §0 de `PLAN_SIMULACION_S4.md` está cumplida (3 oct): modelo del OPA836 en `Simulation_LTSpice/models/OPA836/opa836_a.lib`, **con 6 nodos** (IN+ IN− OUT VCC VEE Vnot_pd), comprobado por Claude. Ojo: hay que añadir C_F como variante y los diodos de entrada como suposición de modelado (§2.3).

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\CH1_entrada
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md: orden de nodos)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\   (opa836.pdf, AD8038_8039.pdf, 74HC_HCT4051.pdf)
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…).
Lee los ficheros enteros. Si vas justo de tiempo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, en `CH1_entrada/`: `PLAN_SIMULACION_S4.md`, que es tu contrato, y los documentos que manda leer.
2. Parte de tu trabajo de S3b (`comun/ch1_comun_s3b.inc`, `ejecutar_s3b.py`) y de los decks de auditoría `chequeo_claude/s3b/y_*_g_*.cir` (protección final de U103). **No los modifiques**: S4 va en ficheros nuevos.
3. Escribe `ejecutar_s4.py` **en paralelo, con 10 trabajadores, desde el principio**, con `--smoke` y `S3G4_MODELS`.
4. Primero una comprobación aislada del OPA836 (seguidor y S4 sola: −3 dB, excursión a 3.3 V, diferencial con V_in = ±3.9 V) y de la ecuación de §2. Informa esos números antes de la campaña.
5. Pasa `--smoke` y después la campaña completa. Prioridad: F1, F7, F0, F2, F3, F4, F6, F5.
6. Escribe el acta y tu diario.

## Reglas

- **No cambies valores de diseño ni añadas protecciones.** Si algo falla, se informa con su valor medido y cuánto falta.
- **No elijas variante de VMID ni de C_F.**
- **Las contradicciones se anotan, no se resuelven.**
- Cada `.meas` lleva en el nombre su estado (prueba, variante M1/M2, escala, V_in, V_DAC, polaridad, VDDA), y ese estado tiene que ser el real del circuito.
- Los límites en saturación se miden con `.dc`; en transitorio, la BNC no pasa de ±4.5 V.
- No toques `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- la comprobación aislada;
- tabla S4-C1…C8 por variante;
- la ecuación medida (ganancia, centro y rango de offset);
- los extremos del pin del ADC y de la entrada del OPA836 en F1 y F7;
- el ruido máximo del canal completo;
- dudas.
