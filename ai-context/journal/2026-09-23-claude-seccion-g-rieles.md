# Sección G — alimentación y rieles, y seguridad del DMM

- Fecha: 2026-09-23, noche.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: confirmar RD-07 a 20 kHz también en corriente y «seguir con los rieles». A mitad de la tarea preguntó si era más seguro usar el osciloscopio con el AWG y el DMM por separado, porque el osciloscopio es de un solo extremo y el DMM diferencial. Planteó el riesgo de unir el COM del DMM con la masa del osciloscopio y el retorno por el USB conectado a un PC.

## Fuentes

- Presupuesto de potencia de la rev 2.0: `docs/S3G4-AFE_v1.0_frontend_analogico.html` §06.5 y §12, y la tabla de cargas de `docs/netlist_hoja01.py`.
  - Total de 2.18 W y 7.2 h con 5000 mAh.
  - ESP32-S3 a 120 mA; pantalla a 150 mA; 12 OPA1656 a 3.9 mA; generador de 20 + 32 mA por riel.
  - Boost de 5 V → LM27762.
- `datasheet/esp32-s3.pdf`, tabla 5-7: TX de 283–340 mA de pico y RX de 88–91 mA.
- Hoja de la ER-TFT035IPS-6 (en `research_and_tests/black_scope/doc/datasheet/`): retroiluminación de 6 LED, 120 mA a 3.2 V.
- `datasheet/lm27762.pdf`:
  - Entrada de 2.7–5.5 V; salidas de 1.5 a 5 V y de −1.5 a −5 V; 250 mA por salida.
  - Consumo en vacío de 390 µA; 0.5 µA apagado; conmutación a 2 MHz.
  - Resistencia de la bomba de 2.5 Ω; caída del LDO de 30–45 mV.
  - **No sube la tensión:** con batería directa no llega a ±5 V.

## Respuesta a la pregunta de seguridad

- En el diseño sin aislar hay una sola masa: el blindaje de las BNC, la masa del AWG, el COM del DMM y el USB, y a través de él el PC.
- Que el DMM sea «diferencial» (resta en el ADC5) no lo aísla.
- Riesgos:
  - Corto entre el COM y la pinza del osciloscopio si van a puntos distintos.
  - Fase a tierra por el USB de un PC con toma de tierra.
  - Aunque todo esté desconectado, un COM en la fase deja con tensión el metal de las BNC y del USB-C.
- El enclavamiento por firmware de RD-05 no evita ese último caso.
- El osciloscopio con el AWG juntos es la práctica normal y segura, con la pinza de masa en la masa del circuito.

## Decisiones de Keneth

1. **El DMM sólo mide baja tensión** (60 V en continua o 30 Vrms, CAT I, como el ELVIS), con masa común. Revisa D-06 y sustituye a RD-04, RD-05 y RD-10.
2. **AWG con su propio convertidor de ±6.5 V.** Compartiendo la bomba, ésta caía a −4.95 V con 100 mA y el LDO de −5.0 V del AFE dejaba de regular.
3. **Batería de 5000 mAh.**
4. **Relés monoestables con economizador.**

## Cambio

- **`docs/rediseno_afe_rev21.html`** (versión 9 del artifact):
  - Nueva sección G con el árbol en Mermaid, el cálculo explicado, la tabla de cargas del peor caso, la autonomía por modo, la comprobación de rieles, el apagado por bloques (RF-18), la masa común y lo que falta.
  - D-03 pasa a monoestable con economizador; D-06 queda revisada en su parte del DMM.
  - Se actualizaron las secciones pendientes y la línea del relé en la BOM.
- **Páginas de requisitos:**
  - `docs/requisitos_dmm_awg.html` (versión 2): RD-04, RD-05, RD-06 y RD-10 revisados; RD-07 confirmado.
  - `docs/requisitos_osciloscopio.html` (versión 3): RF-06, RF-16 y el triángulo.
- **Scripts nuevos:** `docs/rediseno_afe_gen/calc_rieles.py` (presupuesto) y `seccion_g.py` (parche de una vez).

## Números (calc_rieles.py)

- **Peor caso de RF-17:** todo activo, WiFi, pantalla, AWG sobre 50 Ω y 3 relés en ×1. Consume 2.76 W: **6.0 h**, y 4.8 h con la celda envejecida al 80 %.
- **Uso típico:** 2.07 W, 8.1 h.
- **Otros modos:**
  - Sólo osciloscopio: 1.89 W, 8.8 h.
  - Sólo DMM: 1.22 W, 13.6 h.
  - Sin pantalla: 2.28 W, 7.3 h.
  - Con P13: 2.68 W, 6.2 h.
- **Rieles:**
  - LM27762: 42 mA en +5 V y 39 mA en −5 V, de 250 mA.
  - La bomba queda en −5.20 V sin el AWG.
  - BUS5 lleva 193 mA; el boost toma ~0.38 A de la celda a 3.0 V.

## Pendientes

1. Elegir en LCSC el cargador, el boost, el buck, el convertidor del AWG, el driver de la retroiluminación y los interruptores de carga. El cargador debe ser una variante que no deje subir VSYS por encima de ~4.4 V.
2. Confirmar el factor de 1.3 del lado negativo del LM27762 con su curva, y el consumo de los amplificadores elegidos.
3. Sujeción segura con canales apagados: a masa o a un riel vivo. Se decide junto con la corrección de P4.
4. Protección del DMM frente a una conexión accidental a la red (RD-10).
