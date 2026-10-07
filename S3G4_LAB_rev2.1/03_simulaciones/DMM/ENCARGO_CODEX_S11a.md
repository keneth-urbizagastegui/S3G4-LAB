# Encargo para Codex — S11a, DMM: cadena de medida, fuente de ohmios P43 y dinámica

Pegar este texto como encargo. Codex arranca en la raíz `S3G4 LAB`.

**Lanzamiento (lo hace Claude):**
- CLI de la aplicación: `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\5ea220ae823df3d7\codex.exe` (0.160.1, 7 oct), `-m gpt-6.1-sol`, esfuerzo `medium`.
- Como proceso independiente (`Start-Process`), con el prompt por stdin desde un fichero y `-o` para la respuesta final.
- **Antes:** comprobar que Keneth ha dejado los modelos y las hojas del §2 del plan.

---

## Entorno (leer antes de nada)

```
Raíz del proyecto:  C:\Users\Keneth\Desktop\S3G4 LAB   (la ruta tiene un ESPACIO: entrecomilla siempre)
Carpeta de trabajo: C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM
Diseño (SÓLO LECTURA): ...\S3G4_LAB_rev2.1\01_diseno\dmm_rev21.html (sección H) y ...\herramientas\calc_dmm_h.py, calc_dmm_s11.py
Método de referencia (SÓLO LECTURA): ...\03_simulaciones\CH1_entrada (S6: modelo del ADC) y ...\CH23_entrada (S9)
LTspice 26:         C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe   (modo lote: -b "ruta Windows del .cir")
Biblioteca LTspice: C:\Users\Keneth\AppData\Local\LTspice\lib (standard.bjt/.dio/.mos en UTF-16; sub\ con LTC2057, ADR…)
Modelos (sólo lectura): C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\  (léete su LEEME.md entero)
Hojas de datos:      C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes\  y  ...\datasheet\ (stm32g473.pdf, rm0440)
Python 3.12 en el PATH, con numpy, scipy y pymupdf. Usa rutas de Windows (C:\…).
Lee los ficheros enteros. Si vas justo de tiempo o de cupo, entrega lo que tengas, ejecutado, y di qué falta.
Los números que se derivan se calculan (.param o Python); no escribas a mano totales ni valores derivados.
```

## Qué hacer

1. Lee `AGENTS.md`, `ai-context/START.md` y, enteros, `DMM/PLAN_SIMULACION_S11a.md` (tu contrato) y los documentos que manda leer.
2. **Abre tu diario en `ai-context/journal/` al empezar y ve completándolo.** En S4 y S7b te quedaste sin cupo, y el diario es lo que permite reanudar.
3. Haz **K0** antes que nada.
   - Si falta un modelo, usa el sustituto del §2 del plan y márcalo en cada resultado.
   - Si falta el del TLV2372, haz la variante B del driver y deja P43 preparada.
   - Comprueba el orden de pines de cada envoltorio con un seguidor en continua.
4. Escribe `comun/dmm_comun_s11.inc` y comprueba K1 en nominal. **Informa en el diario de los tres ejemplos de la sección H y del reparto del Monte Carlo (10 placas) antes de la campaña.**
5. Escribe `ejecutar_s11.py` **en paralelo, con 10 trabajadores, desde el principio**.
   - Con `--smoke`, `--resume` y `S3G4_MODELS`.
   - Monte Carlo con puntos `.op`, tiempo límite y un reintento.
   - Orden de columnas fijo en los CSV.
   - Los registros, fuera de la comprobación de ficheros protegidos.
   - El modelo del 74HC4051 es solo para transitorio: en continua, corre un transitorio hasta el régimen.
6. Pasa `--smoke` y después la campaña completa. Prioridad: K0, K1, K2, K3, K7, K4, K6, K5, K8, K11, K12, K10, K9, K13.
7. Escribe el acta y cierra el diario.

## Reglas

- **No cambies valores fuera de lo que el plan barre. No elijas variante ni remedios. No diseñes la escalera de P42**: en S11a es un 1N4007 más 0.2 V (§0 del plan).
- **Las contradicciones se anotan, no se resuelven.** Por ejemplo, un dato de la hoja que no cuadre con la sección H.
- Cada `.meas` lleva en el nombre su estado (prueba, función, rango, variante, placa, temperatura y estado previo del ADC), y ese estado tiene que ser el real del circuito.
- La calibración de cada placa se hace a 23 °C, y la evaluación a 18 y 28 °C con las constantes de esa misma placa.
- No toques `../CH1_entrada/`, `../CH23_entrada/`, `Simulation_LTSpice/models/`, `01_diseno/`, `STATE.md` ni `DECISIONS.md`; sí tu diario. No descargues nada.

## Respuesta final

Un resumen corto con:
- ficheros creados;
- código de salida, número de simulaciones y tiempo;
- K0: datos de cada hoja frente a su modelo, y qué sustitutos se usaron;
- los tres ejemplos de la sección H;
- tabla S11-C1…C14 con la fracción de placas, **elemento de paso A | B y driver A | B lado a lado**;
- la fuga máxima tolerable del 74HC4051 por rango (para D4);
- alterna: caída sin corregir a 20 kHz por rango y residuo tras P39;
- la rejilla R_ISO / C_FLT del driver con su error y su estabilidad;
- la tensión disponible y en vacío por rango, y el OPA2188 en el límite de su modo común;
- LED en la prueba de diodo, ruido, rechazo de la red, TRMS y consumo;
- dudas.
