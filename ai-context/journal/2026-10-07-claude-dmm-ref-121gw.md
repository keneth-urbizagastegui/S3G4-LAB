# Referencia del DMM 4/9: EEVblog 121GW (7 oct 2026, Claude Opus 5.5)

- Esquema de 1 hoja (ene. 2018, archive.org), leído por zonas a 330–420 ppp; manual de 2025 (pp. 15–23 renderizadas para las tablas de especificación).
- Entrada V/Ω: PTC3 1.2 k + R16 1 k → MOV1 S05K575 a un nudo con MOV3 a AGND y MOV2 al camino R; FB4; R11 10 MΩ ±0.5 % con C13 6 pF en serie con R9 30 k.
  - Patas R13 1.11 M (C sin montar), R15 101 k (596 pF), R21 10 k (6.35 nF), R26 1 k (66 nF): τ ≈ 60/64/66 µs frente a 60 µs arriba. Emparejamiento deducido de la disposición.
- Camino R: PTC4 1.2 k + R17 1 k = 2.2 kΩ (diodo 3 V/1.4 mA y 15 V/7 mA, y LowZ).
- Corriente: R33 100 Ω, R43 1 Ω, 10 mΩ; F1/F2 HRC (el esquema dice 440 mA/1000 V; el manual, 400 mA/600 V con 10 kA); puente DF10S con +/− unidos; MAX4238 ×10 y 74HC4053.
- Aviso de fusible con TLC272 a través de 9.4 MΩ y pull-ups de 10 MΩ. AD8436 para el RMS; ADR3412; STM32L152.
- Error propio corregido durante el cálculo: los 7 mA del diodo de 15 V son la corriente de cortocircuito (fuente ≈ 15.4 V), no una fuente de 30 V.
