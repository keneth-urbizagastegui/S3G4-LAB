# Requisitos del DMM y del AWG

- Fecha: 2026-09-23, noche.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «sí, haz el cuestionario de requisitos del DMM y del AWG», a continuación del del osciloscopio.

## Método

Dos rondas de preguntas para el DMM y dos para el AWG. Cada pregunta citaba lo que ya había:
- El mapa de pines firmado.
- El firmware del banco: DMM de la etapa J1 y SCPI del AWG de la etapa I3.
- La rev 2.0: cuatro bornes en el DMM y dos rangos de amplitud en el generador.
- La revisión del G473.
- Los requisitos RF del osciloscopio.
- Las referencias: NI ELVIS II, OpenScope y Micro-DMM.

Del ELVIS II se leyó su hoja de especificaciones (`research_and_tests/NI ELVIS II Series.pdf`) y el apéndice A del manual (`ELVIS II.pdf`):
- Derivador de 0.1 Ω, 2 A en continua, 500 mA o 2 A en alterna, y caída menor de 0.6 V.
- Fusible rápido de 3.15 A a 250 V.
- Alterna de 40 Hz a 20 kHz en tensión y de 40 Hz a 5 kHz en corriente.
- 5½ dígitos y 11 MΩ de entrada.
- DMM aislado, pero sólo CAT I de 60 V.

## Respuestas de Keneth

- **Funciones del DMM:** tensión, ohmios, diodo y continuidad, más corriente continua y alterna, con «3 bornes V/Ω, común y A, como el ELVIS».
- **Resolución:** 20 000 cuentas.
- **Categoría:** CAT II 600 V.
- **Aislamiento:** sin aislar, con enclavamiento.
- **Corriente:** hasta 2 A, como el ELVIS.
- **Alterna:** de 40 Hz a 20 kHz.
- **Prueba de diodo:** ~3.5 V.
- **Ayudas:** autorango, relativo, mín/máx y retención, registro en el tiempo y detección de cable abierto.
- **AWG:** dos canales, 1 MHz en todas las formas, ±5 V en vacío con dos rangos, y 50 Ω con ±50 mA, protegida.
- **Formas:** las básicas. Keneth preguntó si añadir más después afecta al hardware. Respuesta: no, son firmware sobre el mismo DAC y el mismo filtro, salvo pulsos de flanco muy rápido.
- **Arbitraria:** 4096 puntos.
- **Fuentes de continua:** no hacen falta aparte.
- **Sincronismo:** interno.

## Cambio

- Nuevo `docs/requisitos_dmm_awg.html` (https://claude.ai/artifact/5TwLhVKhkoYHuPQXJq9y2n), generado con `docs/rediseno_afe_gen/build_requisitos_dmm_awg.py`. Lleva RD-01…RD-10, RG-01…RG-08, sus consecuencias y lo que queda abierto.
- `docs/requisitos_osciloscopio.html`, versión 2: el apartado de pendientes enlaza con los nuevos requisitos.
- `DECISIONS.md`, `STATE.md`, `index.json` y la memoria de Claude, actualizados.

## Consecuencias principales

- **4½ dígitos:** el ADC5 en diferencial (~10.9 bits) con ×1024 da ~61 000 niveles. Hace falta una referencia externa tipo REF3325, divisores del 0.1 % y la calibración P10.
- **Sin aislar (RD-05):** el firmware tiene que detectar el USB (VBUS) y el osciloscopio activo. No sustituye al aislamiento: el riesgo residual queda aceptado.
- **Corriente (RD-06):** derivador de 0.1 Ω (200 mV y 0.4 W a 2 A) y amplificador de deriva cero para los rangos bajos.
- **Prueba de diodo de 3.5 V:** fuente de corriente en 5 V y sujeción antes de PB14 (P14).
- **AWG:** DAC3 → OPAMP en alta velocidad → filtro de ~2 MHz → etapa de salida.
  - ±5 V con 50 mA pide subir un poco los rieles o aceptar ±4.5 V.
  - Aguantar ±15 V desde fuera pide PTC y sujeción.
  - La RAM queda en 48 KiB para el osciloscopio más 16 KiB para la arbitraria, de 128 KiB.

## Pendientes

1. Rangos concretos del DMM y banda de la corriente alterna.
2. Rieles del AWG y presupuesto de energía con las tres funciones activas (RF-17).
3. Diseño del enclavamiento y texto de seguridad.
