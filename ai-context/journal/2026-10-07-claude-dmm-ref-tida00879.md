# Referencia del DMM 3/9: TIDA-00879 (7 oct 2026, Claude Opus 5.5)

- Leídos tidubm4.pdf (TIDUBM4A, 38 p) y el esquemático tidrmi4.pdf (hojas AFE y MCU a 200/130 ppp); la BOM tidrmi5.pdf para números de pieza.
- Topología igual que el 01012 (patas con TS5A3359, 100 MΩ siempre, TS3A24159 con fuerza y sentido), con estas diferencias:
  - R19 CRHV1206 10 MΩ; trimmers C33/C34 TZB4 de 4.5–20 pF;
  - puente J7 para 499 kΩ;
  - OPA333 ×3 (referencia, V−, I−);
  - borne rojo J6 = referencia (AVCC/2 = 1.2 V por R7 de 4.7 Ω), tensión por el negro J8, corriente por el azul J9;
  - SD24_B a 2 MHz/OSR 64 = 31.25 kSa/s, PGA ×16, 4096 muestras por lectura;
  - TPS62740 a 2.4 V con conmutador de carga para el AFE; 3 × AAA.
- Resultados leídos de las gráficas: 60 V −10…+4 mV; 60 mV −8…+12 µV; alterna en 6 V ±1 % hasta ≈ 2 kHz y +6 % a 4 kHz.
  - Las líneas verdes de TI dibujan ±(0.05 % + 5), no el 0.03 % de su tabla 1.
- Corrección registrada: su ADC es un ΣΔ de 24 bits, así que no es comparable con el SAR de 12 bits del G473.
