# CH1 — piezas y redes para el esquema (S8)

- Autor: Claude Code, 4 oct 2026. Fuente de verdad para dibujar CH1 en KiCad.
- **De dónde sale cada valor:** `ai-context/DECISIONS.md` (2–4 oct), `03_simulaciones/CH1_entrada/comun/ch1_comun_s7b.inc` y los `.inc` que incluye (S2b…S7), `ACTA_S7b.md`, `ACTA_S7c.md` y el documento vivo `01_diseno/rediseno_afe_rev21.html` (secciones A–F). Nada sale de memoria.
- Alcance: **solo la cadena de CH1**, del BNC al pin PA0, en **una hoja plana** (sin jerarquía; la jerarquía estilo OpenScope se hará al final). Rieles, VREF+, DAC, 74HCT595 y 74HC165 entran como **etiquetas globales**.
- Pinouts marcados **[VERIFICAR]**: comprobar contra la hoja de datos (carpeta `datasheet - componentes/`) antes de dar el símbolo por bueno. **[SIN HOJA]**: no hay PDF en el proyecto.

## 1. Etiquetas globales (vienen de otras hojas)

| Etiqueta | Qué es | Fuente |
|---|---|---|
| `+AFE_4V9` | Riel positivo del AFE, +4.90 V (LM27762) | DECISIONS 3 oct (R2) |
| `-AFE_4V9` | Riel negativo del AFE, −4.90 V | ídem |
| `VDDA` | 3.3 V analógico del G473 | sección E |
| `VREF_2V5` | VREF+ 2.5 V (REF3325) | sección E/F |
| `AGND` | Masa analógica. **La partición AGND/GND la decide Keneth al hacer la placa**; aquí solo se nombra | sección A (T3 → AGND) |
| `GND` | Masa digital (polo B del conmutador de acoplo) | sección A |
| `+3V3` | Lógica 3.3 V (pull-ups del polo B) | §4, aceptado 4 oct |
| `CH1_OFFSET_DAC` | DAC1 del G473 (PA4) con buffer | DECISIONS 3 oct (S4) |
| `CH1_ADC` | **PA0** (ADC1 + ADC2 entrelazados) | D-02 |
| `CH1_SENSEL_A`, `_B`, `_C` | Selección del 74HC4051, desde el 74HCT595 | sección C |
| `CH1_K_CTRL` | Mando del relé, desde el 74HCT595 | §2.9 |
| `RELAY_COM` | Nodo común de las bobinas de K101…K103: 5 V de arranque (P-MOSFET común, línea `RELAY_KICK` del 74HCT595) o ≈ 3.0 V de mantenimiento (3.3 V por un Schottky). **El circuito común va en otra hoja** | Keneth, 4 oct (opción C) |
| `CH1_CPL_A`, `CH1_CPL_B` | Lectura del acoplo (polo B) hacia el 74HC165 | sección A, propuesta |

## 2. Piezas

**Códigos LCSC de todas las piezas:** `CH1_BOM_precios.csv` (generado por `bom_ch1.py`, 4 oct). Allí manda el código; aquí, el valor y la red.

Los condensadores de pista que aparecen en las simulaciones (`CBNC`, `CX1`, `CTAP`, `CSEL_PAR`, `CPCB`, `C_GAIN`, `C_SUM`, `CPAD`, `C_COMMON`, `COFF_*`) son **parásitos modelados, no piezas**. No se dibujan.

### 2.1 Entrada, divisor ÷100 y rama ×1

| Ref | Valor | Detalle / LCSC | Pin → red |
|---|---|---|---|
| J101 | BNC | Kinghelm, C2837587 | centro → `CH1_BNC`; cuerpo → `AGND` (Keneth, 4 oct) |
| R101 (R1A) | 549 kΩ 0.1 % | 1206 | `CH1_BNC` – `CH1_DIV_MID` |
| R102 (R1B) | 549 kΩ 0.1 % | 1206 | `CH1_DIV_MID` – `CH1_TAP` |
| C101 (C1A) | 20 pF ±2 % C0G 250 V | C3845779 | `CH1_BNC` – `CH1_DIV_MID` |
| C102 (C1B) | 15 pF ±2 % C0G 250 V | C3836120 | `CH1_DIV_MID` – `CH1_TAP` |
| VC101 | trimmer 2–6 pF | SEHWA, C22468120 | `CH1_DIV_MID` – `CH1_TAP` |
| C103 | **DNP** 0603 | hueco de seguro (DECISIONS 4 oct) | `CH1_DIV_MID` – `CH1_TAP` |
| R103 (R2) | 11.0 kΩ 0.1 % | | `CH1_TAP` – `AGND` |
| C104 (Cb) | 1 nF ±1 % C0G | C507408 | `CH1_TAP` – `AGND` |
| C105 | 68 pF ±5 % C0G | | `CH1_TAP` – `AGND` |
| R104 (R_S1) | 49.9 kΩ | 1206 | `CH1_BNC` – `CH1_RS_MID` |
| R105 (R_S2) | 49.9 kΩ | 1206 | `CH1_RS_MID` – `CH1_X1` |
| C106 (C_S) | 1.2 nF C0G ≥ 200 V | | `CH1_BNC` – `CH1_X1` |
| R106 (R_EQ) | 10 MΩ | 1206 | `CH1_EQ` – `AGND` |
| C107 (C_EQ) | ≈ 8.7 pF C0G ≥ 200 V (8.2–9.1 pF) | **seleccionado en prueba**. Se compra 8.2 pF 1 kV (C54431614) como valor de partida y se cambia según la medida (S8, auditoría 4 oct) | `CH1_EQ` – `AGND` |

### 2.2 Relé del grueso (K101)

**TQ2SA-5V-Z** (Panasonic, **C22686**, SMD 14 × 9 mm; Keneth, 4 oct, sustituye al HFD27/005-S), DPDT monoestable, bobina de 5 V **con polaridad**. **Reposo (sin alimentar) = ÷100.** Pinout **verificado** con la hoja de la serie TQ (C46047.pdf, ASCTB14E, p. 10, esquema de «Single side stable», condición sin alimentar; el de la versión SA viene en vista superior, p. 11, con la misma numeración [VERIFICAR la huella con la p. 11]).

| Pin | Función | Red |
|---|---|---|
| 1 | bobina + | `RELAY_COM` (global) |
| 10 | bobina − | `CH1_K_COIL_N` (driver del §2.9) |
| 3 | polo 1, común | `CH1_SEL` |
| 2 | polo 1, NC (reposo, ÷100) | `CH1_TAP` |
| 4 | polo 1, NO (×1) | `CH1_X1` |
| 8 | polo 2, común | `CH1_X1` |
| 9 | polo 2, NC (reposo: réplica conectada) | `CH1_EQ` |
| 7 | polo 2, NO | sin conexión (marca no-connect) |
| 5, 6 | sin función en el monoestable | no-connect |

Fuente: el modelo de S7b (`FRONT_S7B`: `Rk1a100 TAP–SEL` y `Rk1b X1–EQ` cerrados con POS = 100).

### 2.3 Sujeción, acoplo y polarización

| Ref | Valor | Detalle / LCSC | Pin → red |
|---|---|---|---|
| D101 | BAV199 | C40919, par en serie SOT-23; **verificado**: BAV199.pdf, tabla 2 (1 = A1, 2 = K2, 3 = K1/A2) | ánodo de D1 → `-AFE_4V9`; punto común → `CH1_SEL`; cátodo de D2 → `+AFE_4V9` (en S7b: `DHP SEL→VP`, `DLP VN→SEL`) |
| SW101 | SS23H37L6 | C883267, 2 polos × 3 posiciones; ver la tabla de pines debajo | Polo A: común → `CH1_CPL_COM`; DC → `CH1_SEL`; AC → `CH1_AC`; GND → `AGND`. Polo B: común → `GND`; AC → `CH1_CPL_A`; DC → `CH1_CPL_B`; GND → no-connect |
| C108 (C_AC) | 1.8 nF C0G 50 V | 0603 (Keneth, 4 oct; S2/S2b: 5.75 V de peor caso = 11.5 %) | `CH1_SEL` – `CH1_AC` |
| R107 (R_BIAS) | 10 MΩ 1 % | | `CH1_CPL_COM` – `AGND` |
| R108 (R_PROT) | 1 kΩ | | `CH1_CPL_COM` – `CH1_BUF_INP` |

**Pines de SW101** (plano C883267.pdf, comprobado el 4 oct). El plano no numera los pines: la numeración es nuestra y la seguirán el símbolo y la huella. Cada polo es una fila de 4 pines a 0, 6, 10 y 14 mm. El de 6 mm es el **común**, y los de 0, 10 y 14 mm son las posiciones T1, T2 y T3. **Orden del panel (Keneth, 4 oct): T1 = AC, T2 = GND, T3 = DC**, con GND en el centro, como en los osciloscopios clásicos.

| Pin | Fila / posición | Polo A | Polo B |
|---|---|---|---|
| 1 / 5 | 0 mm · T1 = AC | `CH1_AC` | `CH1_CPL_A` |
| 2 / 6 | 6 mm · común | `CH1_CPL_COM` | `GND` |
| 3 / 7 | 10 mm · T2 = GND | `AGND` | no-connect |
| 4 / 8 | 14 mm · T3 = DC | `CH1_SEL` | `CH1_CPL_B` |
| MP ×4 | patas de anclaje | sin conexión eléctrica en el esquema (se decide en la placa) | |

La posición GND pone a masa la **entrada del buffer**, nunca la BNC (sección A). Tabla del polo B (sección A): AC → A = 0, B = 1; DC → A = 1, B = 0; GND → A = 1, B = 1 (se cumple con la tabla de pines de arriba).

### 2.4 Buffer (U101)

OPA810IDBVR, C2833513, SOT-23-5. Pinout DBV **verificado** (opa810.pdf SBOS799E, p. 3, tabla 5-1): 1 OUT, 2 V−, 3 IN+, 4 IN−, 5 V+. Ojo: `models/LEEME.md` avisa de que el **orden de nodos del modelo SPICE** no es el del encapsulado; aquí manda la hoja.

| Pin | Red |
|---|---|
| IN+ | `CH1_BUF_INP` |
| IN− y OUT | `CH1_BUF_OUT` (seguidor) |
| V+ / V− | `+AFE_4V9` / `-AFE_4V9` |

### 2.5 Escalera, VCHECK y multiplexor (U102)

| Ref | Valor | Pin → red |
|---|---|---|
| R109 + R137 (RL1) | 499 Ω → 1 kΩ ∥ 1 kΩ | `CH1_BUF_OUT` – `CH1_LAD1` (las dos) |
| R110 + R140 (RL2) | 249 Ω → 270 Ω ∥ 3.3 kΩ | `CH1_LAD1` – `CH1_LAD2` (las dos) |
| R111 (RL3) | 150 Ω 1 % | `CH1_LAD2` – `CH1_LAD3` |
| R112 (RL4) | 49.9 Ω 1 % | `CH1_LAD3` – `CH1_LAD4` |
| R113 + R143 (RL5) | 24.9 Ω → 49.9 Ω ∥ 49.9 Ω | `CH1_LAD4` – `CH1_LAD5` (las dos) |
| R114 + R144 (RL6) | 24.9 Ω → 49.9 Ω ∥ 49.9 Ω | `CH1_LAD5` – `AGND` (las dos) |
| R115 | 12.4 kΩ 0.1 % | `VREF_2V5` – `CH1_VCHECK` |
| R116 | 100 Ω 0.1 % | `CH1_VCHECK` – `AGND` |

Tomas: 1, 1/2, 1/4, 1/10, 1/20 y 1/40 (sección C). **Contradicción anotada:** S7/S7b simularon VCHECK con 1 kΩ a masa (`R_VCHECK_S7`), no con el divisor 12.4 k / 100 Ω del documento vivo (propuesta R4). Se dibuja el divisor del documento; el ensayo de VCHECK queda pendiente.

U102: 74HC4051 (Nexperia), C9386, SOIC-16. Pinout **verificado** (74HC_HCT4051.pdf rev. 12, p. 4, tabla 2): 1 Y4, 2 Y6, 3 Z, 4 Y7, 5 Y5, 6 E̅, 7 VEE, 8 GND, 9 S2, 10 S1, 11 S0, 12 Y3, 13 Y0, 14 Y1, 15 Y2, 16 VCC.

| Pin | Red |
|---|---|
| Y0 | `CH1_BUF_OUT` (toma 1) |
| Y1…Y5 | `CH1_LAD1` … `CH1_LAD5` |
| Y6 | `AGND` (autocero) |
| Y7 | `CH1_VCHECK` |
| Z | `CH1_MUX_OUT` |
| S0 / S1 / S2 | `CH1_SENSEL_A` / `_B` / `_C` |
| E̅ | `AGND` (siempre habilitado) |
| VCC / VEE / GND | `+AFE_4V9` / `-AFE_4V9` / `AGND` |

Orden Y0…Y7 tomado de `CHANNEL_S7B` (`XMUX BO Y1 Y2 Y3 Y4 Y5 0 Y7 …`).

### 2.6 Ganancia ×50 (U103, AD8039 doble)

AD8039ARZ-REEL7, C96525, SOIC-8. Pinout **verificado** (AD8038_8039.pdf, p. 1, figura 3): 1 OUT A, 2 −IN A, 3 +IN A, 4 V−, 5 +IN B, 6 −IN B, 7 OUT B, 8 V+.

| Ref | Valor | Pin → red |
|---|---|---|
| R117 (R_SER A) | 470 Ω | `CH1_MUX_OUT` – `CH1_G1_INP` |
| D102 | BAV99, C2500 (**verificado**: C2500.pdf, tabla 2: 1 = A1, 2 = K2, 3 = K1/A2) | antiparalelo entre `CH1_G1_INP` y `CH1_G1_INN`: pines 1 y 2 → `CH1_G1_INP`, pin 3 (común) → `CH1_G1_INN` |
| R118 (RF1) | 1.00 kΩ 1 % | `CH1_G1_OUT` – `CH1_G1_INN` |
| R119 + R141 (RG1) | 249 Ω → 270 Ω ∥ 3.3 kΩ | `CH1_G1_INN` – `AGND` (las dos) |
| R120 (R_SER B) | 470 Ω | `CH1_G1_OUT` – `CH1_G2_INP` |
| D103 | BAV99, C2500 | entre `CH1_G2_INP` (pines 1 y 2) y `CH1_G2_INN` (pin 3) |
| R121 + R145 (RF2) | 2.26 kΩ → 2.2 kΩ + 68 Ω en serie | R121: `CH1_G2_OUT` – `CH1_RF2_MID`; R145: `CH1_RF2_MID` – `CH1_G2_INN` |
| R122 + R142 (RG2) | 249 Ω → 270 Ω ∥ 3.3 kΩ | `CH1_G2_INN` – `AGND` (las dos) |

U103A: +IN `CH1_G1_INP`, −IN `CH1_G1_INN`, OUT `CH1_G1_OUT` (×5.016). U103B: +IN `CH1_G2_INP`, −IN `CH1_G2_INN`, OUT `CH1_G2_OUT` (×10.08). V+ / V− → `+AFE_4V9` / `-AFE_4V9`.

### 2.7 Filtro anti-alias (U105, AD8039 doble, dos Sallen-Key de ganancia 1)

| Ref | Valor | Pin → red |
|---|---|---|
| R123 + R148 | 1.11 kΩ → 1.1 kΩ + 10 Ω en serie | R123: `CH1_G2_OUT` – `CH1_F1_A`; R148: `CH1_F1_A` – `CH1_F1_MID` |
| R124 + R149 | 1.11 kΩ → 1.1 kΩ + 10 Ω en serie | R124: `CH1_F1_MID` – `CH1_F1_B`; R149: `CH1_F1_B` – `CH1_F1_INP` |
| C109 | 56 pF C0G | `CH1_F1_MID` – `CH1_F1_OUT` |
| C110 | 47 pF C0G | `CH1_F1_INP` – `AGND` |
| R125 + R138 | 499 Ω → 1 kΩ ∥ 1 kΩ | `CH1_F1_OUT` – `CH1_F2_MID` (las dos) |
| R126 + R139 | 499 Ω → 1 kΩ ∥ 1 kΩ | `CH1_F2_MID` – `CH1_F2_INP` (las dos) |
| C111 | 220 pF C0G | `CH1_F2_MID` – `CH1_FILT_OUT` |
| C112 | 56 pF C0G | `CH1_F2_INP` – `AGND` |

U105A: +IN `CH1_F1_INP`, −IN y OUT `CH1_F1_OUT`. U105B: +IN `CH1_F2_INP`, −IN y OUT `CH1_FILT_OUT`. V+ / V− → `+AFE_4V9` / `-AFE_4V9`. Fuente: `SK_S7B` y DECISIONS 3 oct (filtro intermedio reescalado).

### 2.8 Etapa final, VMID y red del pin (U106)

OPA836IDBVR, C111589, SOT-23-6, a 3.3 V. Pinout DBV **verificado** (opa836.pdf SLOS712J, p. 7, tabla 6-1): 1 OUT, 2 V−, 3 IN+, 4 IN−, 5 PD, 6 V+.

| Ref | Valor | Pin → red |
|---|---|---|
| R127 (R_IN) | 10.0 kΩ 1 % | `CH1_FILT_OUT` – `CH1_SUM` |
| R128 + R146 (R_OFF) | 8.06 kΩ → 7.5 kΩ + 560 Ω en serie | R128: `CH1_OFFSET_DAC` – `CH1_ROFF_MID`; R146: `CH1_ROFF_MID` – `CH1_SUM` (la de 560 Ω junto al nudo de suma) |
| R129 (R_F) | 10.0 kΩ 1 % | `CH1_DRV_OUT` – `CH1_SUM` |
| C113 (C_F) | 1 pF C0G | `CH1_DRV_OUT` – `CH1_SUM` |
| R130 | 10.0 kΩ 1 % | `VREF_2V5` – `CH1_VMID` |
| R131 + R147 | 5.23 kΩ → 5.1 kΩ + 120 Ω en serie | R131: `CH1_VMID` – `CH1_VMID_LO`; R147: `CH1_VMID_LO` – `AGND` |
| C114 | 1 µF | `CH1_VMID` – `AGND` |
| R132 (R_ADC) | 68 Ω | `CH1_DRV_OUT` – `CH1_ADC` |
| C115 (C_ADC) | 470 pF C0G | `CH1_ADC` – `AGND` |

U106: IN+ `CH1_VMID`, IN− `CH1_SUM`, OUT `CH1_DRV_OUT`, V+ `VDDA`, V− `AGND`, **PD → `VDDA`** (tabla 6-1: alto = funcionamiento normal; «PIN MUST BE DRIVEN»).

### 2.9 Driver del relé (Keneth, 4 oct: economizador de dos tensiones, opción C)

| Ref | Valor | Detalle / LCSC | Pin → red |
|---|---|---|---|
| Q101 | 2N7002 | C8545, SOT-23 (Id 115 mA: 28 mA de bobina = 24 %) | D → `CH1_K_COIL_N`; G → `CH1_K_GATE`; S → `GND` |
| D104 | 1N4148W | C81598, SOD-123 (150 mA, 75 V) | ánodo → `CH1_K_COIL_N`; cátodo → `RELAY_COM` |
| R135 | 100 Ω | 0603 (C22775), serie de puerta | `CH1_K_CTRL` – `CH1_K_GATE` |
| R136 | 100 kΩ | 0603 (C25803): puerta a masa, el relé queda en reposo (÷100) mientras el 74HCT595 no esté gobernado | `CH1_K_GATE` – `GND` |

- La corriente de la bobina vuelve por **`GND`, no por `AGND`**.
- Pinout SOT-23 del 2N7002 (1 G, 2 S, 3 D), **verificado** con C8545.pdf, p. 1; R_DS(on) ≤ 7 Ω con 5 V. 1N4148W: pin 1 = cátodo, pin 2 = ánodo (**verificado**: C81598.pdf).
- Bobina del TQ2SA-5V (hoja, p. 5): 178 Ω, 28.1 mA y 140 mW a 5 V; cierre ≤ 75 %, suelta ≥ 10 %. Arranque: ≈ 4.80 V (96 %). Mantenimiento: 3.3 V − ~0.3 V (Schottky) − 16 mA × 7.5 Ω ≈ 2.88 V (58 %) ≈ 46 mW. La hoja no da un mínimo de mantenimiento; las curvas de referencia (p. 7) sitúan la suelta en ≤ ~40 %, +~10 puntos a 70 °C. **Comprobar en el prototipo** bajando la tensión hasta que suelte.
- Ojo: el HFD27 se descartó porque su hoja (p. 22, nota 4) pide un mantenimiento ≥ 60 % y este esquema le daba ≈ 56 %.

### 2.10 Combinaciones serie/paralelo (Keneth, 4 oct)

Para reproducir los valores simulados con piezas *basic* de JLCPCB (sin cargo por referencia) y obtener el 1.11 kΩ, que no existe. Error frente al valor simulado ≤ 0.35 %, dentro del ±1 % del Monte Carlo de S7b: no hace falta volver a simular. Cada pareja se dibuja y se coloca **junta**; las redes intermedias (`CH1_RF2_MID`, `CH1_ROFF_MID`, `CH1_VMID_LO`, `CH1_F1_A`, `CH1_F1_B`) son locales y cortas.

| Valor simulado | Pareja | Combinación | Resultado | Códigos |
|---|---|---|---|---|
| 499 Ω | R109/R137, R125/R138, R126/R139 | 1 kΩ ∥ 1 kΩ | 500.0 Ω (+0.20 %) | C21190 |
| 249 Ω | R110/R140, R119/R141, R122/R142 | 270 Ω ∥ 3.3 kΩ | 249.6 Ω (+0.23 %) | C22966 + C22978 |
| 24.9 Ω | R113/R143, R114/R144 | 49.9 Ω ∥ 49.9 Ω | 24.95 Ω (+0.20 %) | C23185 |
| 2.26 kΩ | R121/R145 | 2.2 kΩ + 68 Ω | 2.268 kΩ (+0.35 %) | C4190 + C27592 |
| 8.06 kΩ | R128/R146 | 7.5 kΩ + 560 Ω | 8.060 kΩ (0.00 %) | C23234 + C23204 |
| 5.23 kΩ | R131/R147 | 5.1 kΩ + 120 Ω | 5.220 kΩ (−0.19 %) | C23186 + C22787 |
| 1.11 kΩ | R123/R148, R124/R149 | 1.1 kΩ + 10 Ω | 1.110 kΩ (0.00 %) | C22764 + C22859 |

No se usan combinaciones en el divisor ÷100, en la réplica ni en VCHECK (alta impedancia o precisión del 0.1 %).

## 3. Cuenta

- Redes propias de CH1: `CH1_BNC`, `CH1_DIV_MID`, `CH1_TAP`, `CH1_RS_MID`, `CH1_X1`, `CH1_EQ`, `CH1_SEL`, `CH1_AC`, `CH1_CPL_COM`, `CH1_BUF_INP`, `CH1_BUF_OUT`, `CH1_LAD1`…`CH1_LAD5`, `CH1_VCHECK`, `CH1_MUX_OUT`, `CH1_G1_INP`, `CH1_G1_INN`, `CH1_G1_OUT`, `CH1_G2_INP`, `CH1_G2_INN`, `CH1_G2_OUT`, `CH1_F1_MID`, `CH1_F1_INP`, `CH1_F1_OUT`, `CH1_F2_MID`, `CH1_F2_INP`, `CH1_FILT_OUT`, `CH1_SUM`, `CH1_VMID`, `CH1_DRV_OUT`, `CH1_K_COIL_N`, `CH1_K_GATE`, `CH1_RF2_MID`, `CH1_ROFF_MID`, `CH1_VMID_LO`, `CH1_F1_A`, `CH1_F1_B`, más las globales del §1.
- El auditor contará piezas y redes **a partir de esta tabla** (no con un número escrito aquí).

## 4. Desacoplo y pull-ups (propuesta de Claude, **aceptada por Keneth el 4 oct**)

No se simularon; los modelos no los necesitan.

| Ref | Valor | Detalle | Pin → red |
|---|---|---|---|
| C116 | 100 nF X7R 16 V | 0402, junto a U101 V+ | `+AFE_4V9` – `AGND` |
| C117 | 100 nF X7R 16 V | 0402, junto a U101 V− | `-AFE_4V9` – `AGND` |
| C118 | 100 nF X7R 16 V | 0402, junto a U102 VCC | `+AFE_4V9` – `AGND` |
| C119 | 100 nF X7R 16 V | 0402, junto a U102 VEE | `-AFE_4V9` – `AGND` |
| C120 | 100 nF X7R 16 V | 0402, junto a U103 V+ | `+AFE_4V9` – `AGND` |
| C121 | 100 nF X7R 16 V | 0402, junto a U103 V− | `-AFE_4V9` – `AGND` |
| C122 | 100 nF X7R 16 V | 0402, junto a U105 V+ | `+AFE_4V9` – `AGND` |
| C123 | 100 nF X7R 16 V | 0402, junto a U105 V− | `-AFE_4V9` – `AGND` |
| C124 | 100 nF X7R 16 V | 0402, junto a U106 V+ | `VDDA` – `AGND` |
| C125 | 10 µF X5R 25 V | 0805 (C15850, basic), depósito del canal | `+AFE_4V9` – `AGND` |
| C126 | 10 µF X5R 25 V | 0805 (C15850, basic), depósito del canal | `-AFE_4V9` – `AGND` |
| R133 | 10 kΩ 1 % | pull-up del polo B | `+3V3` – `CH1_CPL_A` |
| R134 | 10 kΩ 1 % | pull-up del polo B | `+3V3` – `CH1_CPL_B` |

16 V como mínimo para no pasar del 80 % con ±4.9 V (los 10 µF van a 25 V porque la pieza basic es de 25 V: más margen y menos pérdida por tensión continua) y limitar la pérdida de capacidad por tensión continua de las X5R/X7R. Sigue abierto si el 74HC165 que lee `CH1_CPL_A/B` cuelga del STM32 o del ESP32 (sección A); no afecta a esta hoja.

## 5. Abierto (no dibujar inventado: dejar un texto en la hoja)

- **Circuito común del economizador** (P-MOSFET de arranque, Schottky desde 3.3 V, línea `RELAY_KICK`): va en la hoja de control/alimentación, no en la de CH1.
- **Huella del TQ2SA:** comprobarla contra la p. 11 de la hoja (vista superior, patrón de pads SA).
- **TVS de riel:** es de la hoja de alimentación, no de CH1.
- El 74HC165 que lee `CH1_CPL_A/B` cuelga del **STM32**, en el bus de los 74HCT595 (Keneth, 4 oct). No cambia esta hoja.
