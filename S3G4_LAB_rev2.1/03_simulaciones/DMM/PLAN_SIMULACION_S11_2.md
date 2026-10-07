# Plan de simulación S11.2 — DMM, bloque 1 rediseñado: O2 y borne A con GBU808

- Autor: Claude Code (auditor), 7 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus).
- Continúa S11.1. **Lee antes, enteros:**
  - `PLAN_SIMULACION_S11_1.md`, incluidos los §3b y §3c, que siguen vigentes salvo lo que cambia aquí;
  - `ACTA_S11_1.md`, `AUDITORIA_CLAUDE_S11_1.md` y `REDISENO_BLOQUE1.md` (sobre todo §2.3, §5 y §7);
  - en `ai-context/DECISIONS.md`, la entrada del 7 oct «rediseño tras S11.1».
- Reutiliza tu ejecutor, tu modelo reducido y los scripts del rediseño (`rediseno_bloque1/`).

## 1. Qué cambia respecto a S11.1 (decisión de Keneth)

1. **Camino de ohmios, opción O2.** Es el circuito del §2.3 de `REDISENO_BLOQUE1.md`:
   - V/Ω → relé TQ2SA → **limitador bidireccional de deplexión** con 2 × **BSS126** (Infineon), puertas cruzadas y una sola resistencia R_LIM → N1 → R_S de 47 Ω → N2;
   - en N2: un BAV199 al riel positivo y otro de COM a N2;
   - zéner BZT52C5V6 de rp a COM y de COM a rn, como sumidero;
   - un diodo de bloqueo en serie con el BSS84 de la fuente, para su diodo de cuerpo;
   - **sin PTC ni TVS.**
   - **R_LIM:** elígela con la hoja del BSS126 de forma que la corriente límite sea ≥ 1.3 mA en el peor caso bajo y ≤ 2.4 mA en el peor caso alto (50 % de la potencia del SOT-23 con la red). Si ninguna R cumple las dos cosas con la dispersión de la hoja, **dilo y no la fuerces**.
2. **Prueba de diodo como el ELVIS:** silicio a 1 mA y LED a 100 µA (la fuente P43 tiene esa corriente en el rango de 20 kΩ).
3. **Borne A:**
   - **GBU808** (`GBU808.pdf`) en lugar del DF08S;
   - fusible **Littelfuse 0216, 3.15 A** (`Littelfuse-Fuse-216-Datasheet.pdf`): I²t de fusión, curva tiempo-corriente y poder de corte de su hoja;
   - **R_B = 10 kΩ** en serie con la entrada de B.
4. **Hojas nuevas:** `infineon-bss126-datasheet-en.pdf`, `GBU808.pdf` y `Littelfuse-Fuse-216-Datasheet.pdf`. Si Infineon no da modelo SPICE del BSS126 en el proyecto, construye uno a partir de la hoja (IDSS, V_GS(off) mín./típ./máx., R_DS(on), capacidades, BV_DSS y su variación con la temperatura). Cita la página de cada dato. **No descargues nada.**

## 2. Pruebas

Pruebas del S11.1, con los casos limitados a O2:

| # | Qué |
|---|---|
| Q0 | Datos de las tres hojas nuevas, con su página. El modelo del BSS126 frente a la hoja: I_D–V_GS en los extremos, V_p y R_on. R_LIM elegida y por qué |
| Q1 | Medida normal: diodo a 1 mA y a 100 µA (tensión disponible); fuga en N1/N2 con la hoja del 4051 (p. 9) y **sin el canal 6 sobre N2**; error añadido a 0.2 µA y 1 µA |
| Q3 | Red de 230 Vrms, 60 Hz, en ohmios, con el relé cerrado **y sin abrir nunca**, durante 10 s completos si el limitador lo permite (ya no hay PTC térmica; con el límite de corriente constante, el régimen periódico se extrapola como en el §3b). Fase 0° y 90°. Extremos del BSS126 (IDSS y V_p mín./máx.) a 0, 25 y 70 °C. Informa de: corriente límite, V_DS, potencia y temperatura de unión de cada FET, corriente a cada riel, tensión entre rieles, corriente por los BAV199 y los zéner, y la corriente que cortaría el relé |
| Q4 | Lo mismo con el DMM apagado (los dos casos de diodo de cuerpo del interruptor de carga) |
| Q5 | Borne A con la red a 0.5, 1 y 2 Ω, **con apertura del fusible** según la I²t y la curva de su hoja (factor de arco k = 1, 2 y 3). Para el GBU808: pico e I²t frente a su hoja; para el derivador, energía; tensión en la entrada de B tras R_B |
| Q6 | ESD ±4 kV (contacto) y ±8 kV (aire) en V/Ω, en modo ohmios y en modo tensión, y en A. Mira si O2 aguanta sin la TVS. Si no aguanta, informa de cuánto falta; **no añadas piezas** |
| Q7 | Recuperación tras Q3: tiempo hasta que N2 vuelve a 1 cuenta |

## 3. Criterios (los de S11.1, con estos cambios)

| # | Criterio |
|---|---|
| C1 | Cada pieza ≤ 80 % de su tensión y ≤ 50 % de su potencia, energía o I²t (de su hoja), en Q3–Q6. Para los FET, la temperatura de unión ≤ 80 % de su máximo con la potencia de 10 s y la R_th de la hoja |
| C2 | Tensión entre rieles ≤ 11 V; corriente hacia los rieles ≤ la carga del riel |
| C3 | Pines de los circuitos integrados dentro de sus máximos, con corrientes ≤ 50 % |
| C4 | Con la red en ohmios y el relé sin abrir nunca, todo sobrevive 10 s **sin firmware** |
| C5 | **Cambiado por decisión del rediseño:** informar de la fuga típica y máxima según las hojas en N1/N2 (sin el canal 6). El criterio de prototipo es típica ≤ 20 pA; aquí se informa, sin aprobar ni suspender |
| C6 | Diodo: ≥ 3.5 V disponibles a 100 µA; a 1 mA, informar |
| C7 | Recuperación ≤ 1 s tras retirar la red |
| C8 | Borne A: el GBU808 ≤ 50 % de su I²t y de su IFSM con el fusible abriendo, para k = 1–3 y la red a 0.5–2 Ω |

Fallar es un resultado válido: informa del valor y de lo que lo movería, sin simular remedios ni añadir piezas.

## 4. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque1_o2.inc` y el modelo del BSS126 con sus páginas;
- `S11_2/` y `ejecutar_s11_2.py`: 10 trabajadores, `--smoke`, `--resume`, `S3G4_MODELS` y 300 s por caso; el modelo reducido de S11.1 en Q3–Q7;
- `resultados/s11_2_*.csv`;
- `ACTA_S11_2.md`, con la tabla C1–C8, la R_LIM elegida, la tabla del BSS126 en sus extremos y la del borne A;
- tu diario en `ai-context/journal/`, abierto al empezar.

## 5. Lo que NO es tuyo

No cambies piezas ni topología salvo R_LIM. No añadas TVS ni otras protecciones. No toques los archivos de S11.1 (cópialos si los necesitas), `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 6. Cómo voy a auditar

1. `--smoke` reejecutado en una ruta corta.
2. El modelo del BSS126 frente a la hoja, con sus páginas.
3. Que en Q3 el relé está cerrado los 10 s.
4. Que en Q5 el fusible abre según su hoja.
5. Las energías y las temperaturas de unión, comprobadas a mano en un caso.
