# Plan de la rev 2.1 — lo que haremos

Estado a 24 sep 2026. El estado compartido y oficial está en `ai-context/STATE.md`; esta lista lo ordena para trabajar.

## Hecho

- Anatomías de cinco referencias (DSO112, WAVE2, OpenScope MZ, black_scope) y revisión analógica del G473.
- Requisitos funcionales:
  - Osciloscopio: RF-01…RF-19.
  - DMM: RD-01…RD-10. Sólo baja tensión, sin medir la red.
  - AWG: RG-01…RG-08.
- Simulación P4/P7 construida por Codex y auditada. Por RF-07, el grueso es P4, con relé.
- Sección G (rieles): arquitectura y presupuesto. Con 5000 mAh, 6.0 h en el peor caso.

## Siguiente, en este orden

1. **Rieles (sección G.8):** elegir en LCSC (RF-19):
   - un cargador que no deje subir VSYS de ~4.4 V;
   - el boost de 5.3 V y el buck de 3.3 V;
   - el convertidor de ±6.5 V del AWG;
   - el driver de la retroiluminación y los interruptores de carga.
2. **Corregir P4 para RF-08:**
   - R_BIAS delante del relé.
   - Rt + Rb para que el paralelo dé 1 MΩ.
   - Capacidad igualada con el segundo polo del relé.
   - Resistencia serie antes del buffer.
   - Sujeción segura con el canal apagado.

   Luego, un nuevo encargo de simulación con T07 completo.
3. **Sección D, filtro anti-alias:** CH1 a 2 MHz, de orden alto (RF-03); CH2 y CH3 a 1.5 MHz.
4. **Sección E, offset:** ±5 divisiones (RF-14), con PWM o DAC en sample-and-hold (P6, P15).
5. **Sección F:** driver del ADC con R_AIN ≤ 100 Ω, REF3325 (P9) y reloj del ADC (P13).
6. **DMM:**
   - 60 V en continua o 30 Vrms, 2 A y 4½ dígitos.
   - Prueba de diodo de 3.5 V.
   - Protección frente a errores (RD-10).
7. **AWG:** etapa de salida de ±5 V con 50 mA, filtro de reconstrucción de 2 MHz y protección de ±15 V.
8. **Mapa de pines para 3 canales (D-02),** con disparo de CH2 y CH3 por watchdog (P11, P12).
9. **Esquemas de la rev 2.1** en `04_esquematicos/`.

## Decisiones abiertas (de Keneth)

- ¿Sigue el tope RE-01 de 120 USD?
- ¿Grueso ÷20 o ÷100 (P1)?
- P8 (etapa final única) y P13 (CPU a 104 MHz con el ADC síncrono).
- ¿Cuánto debe aguantar el DMM si se conecta a la red por error (RD-10)?
- Propuestas P1–P16: todas siguen sin aplicar salvo lo que recogen D-xx, RF, RD y RG.
