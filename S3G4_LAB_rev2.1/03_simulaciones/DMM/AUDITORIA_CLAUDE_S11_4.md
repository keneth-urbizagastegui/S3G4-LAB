# Auditoría de S11.4 (DMM, bloque 1, confirmación final)

- Auditor: Claude Code, 7 oct 2026. Ejecutó: Codex. Contrato: `PLAN_SIMULACION_S11_4.md`.
- Copia de trabajo: `C:\s114\a\b\DMM`. Hacen falta dos niveles de carpeta por `HERE.parents[2]` en `ejecutar_s11_2.py`. Los decks derivados están en `C:\s114\nofire` y `C:\s114\enc`; LTspice falla en silencio con los nombres largos de Codex dentro de esa ruta, así que los he renombrado (`n1…n8`, `map.txt`).
- No he tocado ningún archivo de Codex, ni `STATE.md`, `DECISIONS.md`, modelos u hojas. No he descargado nada.
- Mis scripts, en `DMM/chequeo_claude/s11_4/`:
  - `comparar_smoke.py`: compara mi smoke con el de Codex, columna a columna;
  - `pulso_esd.py`: lector `.raw` propio; mide la duración y la energía del pulso en Rprot1 y Rohm1, la tensión en el relé y la corriente por RX0/RX1;
  - `d5_raw.py`: recalcula D5 desde el barrido T1;
  - `envolvente_sin_gdt.py`: genera los decks T2 con el GDT sin cebar;
  - `encendido_t5.py`: genera el deck T5 apagado que se enciende en t = 12 s.

## 1. Reejecución y recálculo

- `--smoke --keep-raw`: 9/9 `ok` en 294 s. Los 9 casos coinciden con `s11_4_smoke.csv` de Codex en **todas** las columnas numéricas. Ninguna difiere en más de 1e-9 relativo. **Es reproducible.**
- Recalculado desde el `.raw` con mi lector:

| Caso | Magnitud | Claude (`.raw`) | Codex (CSV) |
|---|---|---|---|
| T2, +4 kV contacto, modo V, GDC = 420 V, riel −2 % | V/Ω pico; Rprot1; Rohm1; relé abierto | 1059.30; 353.03; 514.86; 38.33 V | 1059.30; 353.03; 514.86; 38.33 V |
| T2, +8 kV aire, modo V, **GDC = 780 V** (cebado máximo) | ídem | 1052.75; 350.82; 512.14; 37.69 V | 1052.75; 350.82; 512.14; 37.69 V |
| T2, −4 kV contacto, ohmios, GDC = 420 V | V/Ω pico; Rprot1; Rohm1 | 1038.76; 347.65; 511.95 V | 1038.76; 347.65; 511.95 V |
| T1 / D5, 100 µA, riel −2 % | V máx. con I_fuente ≥ 99 µA; I_DUT a 3.5 V | **3.606262 V**; 98.085 µA | 3.606262 V; 98.084527 µA |

Los resultados del acta están bien extraídos. Lo que discuto abajo es qué significan.

## 2. Modelo del GDT: ceba en la ESD y no con la red, pero de forma demasiado optimista

Lo que está bien:
- El cebado en continua (420/780 V) y el de impulso (1 kV a 100 V/µs) están bien puestos.
- El umbral depende de dV/dt: vale 420 V a frecuencia de red y 1000 V en la ESD.
- El arco es de 20 V + 1 Ω. Se mantiene por encima de 10 mA y se extingue por debajo.
- **Con la red no ceba:** en T3, 325.27 V frente al umbral de continua de 420 V. Estado 0 y arco 0 A en 18/18 casos.
- **En la ESD sí ceba:** en mis tres casos, el estado pasa de 0.5 a los 0.75–0.91 ns del frente.

Lo que no representa la realidad:
1. **El frente del generador es un escalón ideal.** dV/dt en V/Ω llega a **24 kV/ns**. Una pistola IEC 61000-4-2 tarda 0.7–1 ns en subir.
2. **El GDT conduce casi al instante.** Con GRON = 1 Ω, un estado de 0.02 ya equivale a unos 50 Ω. La tensión cae de 1020 V a 229 V en 0.07 ns, cuando el estado sólo vale 0.065. En la práctica es una palanca ideal que se dispara a 1000 V.
3. Un GDT real, con frentes de kV/ns, tarda de decenas de ns a µs en cebar. Su tensión de cebado por impulso sube muy por encima del dato de 1 kV a 100 V/µs. El acta ya avisa de que la extrapolación no está garantizada. Los números siguientes miden cuánto pesa.
4. **Por eso los dos cebados dan el mismo resultado.** Con GDC de 420 y de 780 V, la diferencia en T2 es nula: el umbral es 1000 V en ambos casos. Del modelo no se puede sacar la dispersión del cebado en la ESD.

**Envolvente si el GDT no llega a cebar** (`envolvente_sin_gdt.py`: GDC = GIMP = 100 kV, riel nominal, alimentado, ambos signos). El GDT real queda entre esto y el acta:

| Caso | V/Ω pico | Rprot1 pico; > 160 V durante | Rohm1 pico; > 200 V durante | Relé abierto | I por RX0 / RX1 |
|---|---:|---|---|---:|---|
| 4 kV contacto, modo V | 3793 V | **1262 V; 34.6 µs** (0.32 mJ) | 1441 V; 5.4 ns | **3776 V** | 31.6 / 6.1 mA |
| 8 kV aire, modo V | 7351 V | **2448 V; 47.3 µs** (1.27 mJ) | 2361 V; 7.7 ns | **7333 V** | 38.0 / 10.9 mA |
| 4 kV contacto, ohmios | 3386 V | 1129 V; 0.76 µs | **1686 V; 0.83 µs** (0.45 mJ) | cerrado | 24.0 / 27.7 mA |
| 8 kV aire, ohmios | 5901 V | 1965 V; 1.16 µs | **2943 V; 1.25 µs** (1.61 mJ) | cerrado | 39.6 / 32.8 mA |

Sin GDT, los criterios D2 (relé ≤ 1200 V) y D4 (≤ 10 mA) **no se cumplen**. Es lo mismo que mostró S11.3 sin GDT: Cc1 a 1011/2015 V. **El cumplimiento de D2 y D4 en el acta depende por completo de que el GDT cebe en 1 ns a 1 kV, y eso es un supuesto.**

## 3. D1/D2, Rohm a 543 V y Rprot a 366 V: criterio mal puesto sobre un pulso que es un artefacto

**Duración del pulso**, medida en el `.raw`:
- Rprot1 y Rohm1 superan 160–200 V sólo durante **0.06–0.11 ns**. La anchura a media altura es de 0.07–0.08 ns.
- Energía: 1–12 nJ en Rprot1 y 11–24 nJ en Rohm1.
- Lo dura el retardo del modelo del GDT con un frente ideal. A esa escala de tiempo, la capacidad propia de una 1206 o 2512 (unas décimas de pF) y la inductancia de las pistas ya cambiarían el reparto. **Es un artefacto del generador y del modelo del GDT, no un esfuerzo físico creíble.**

**Comparar con la tensión de trabajo continua es un criterio mal puesto:**
- La tensión de trabajo (200/250 V) es un límite para aplicación permanente.
- La sobrecarga breve de IEC 60115-1 también es lenta: 2.5 × √(P·R), con el tope de V_max de sobrecarga, durante 2 s (5 s según la edición).
  - Rprot (33 kΩ, 0.5 W): 2.5·√16 500 = 321 V, con tope típico de 400 V en 1206.
  - Rohm (1.1 kΩ, 2 W): 2.5·√2200 = **117 V**. Es menor que la tensión de trabajo, porque la sobrecarga es un ensayo térmico de segundos.
  - Tampoco sirve para pulsos de ns o µs.
- La magnitud adecuada es la **resistencia a pulsos o a ESD**:
  - el pulso único de 1.2/50 µs (o 10/700 µs), según IEC 60115-1 o la curva de pulsos del fabricante;
  - o el ensayo ESD de AEC-Q200-002 o IEC 61000-4-2 con ΔR admitido.
- Las resistencias de capa gruesa estándar suelen quedarse por debajo de 1 kV en 1206 de 1.2/50 µs. Las antipulso se especifican con varios kV.

**Especificación de los MPN.** La dimensiono con la envolvente sin GDT, que es el caso real si el GDT es lento:
- **Rprot (3 × 33 kΩ, 1206):**
  - antipulso, con pulso único de 1.2/50 µs de **≥ 1.5 kV** por pieza (cubre 1.26 kV por contacto), y de ≥ 2.5 kV si se quiere cubrir el aire sin GDT;
  - ESD ±8 kV con |ΔR| ≤ 1 %;
  - energía de un pulso de unos 50 µs ≥ 2 mJ por pieza (pide la curva).
  - La FPS1206J333 de FOJAN tiene sólo el dato de 200 V de trabajo y no cumple esto mientras no haya hoja con curva de pulsos.
- **Rohm (2 × 1.1 kΩ, 2512, 2 W):**
  - antipulso, con 1.2/50 µs ≥ **2 kV** por pieza (cubre 1.69 kV) y ≥ 3 kV para el aire;
  - energía de un pulso de unos 1 µs ≥ 5 mJ.
  - Si se elige la HoCR2512, hace falta su curva de pulsos.
- **Rdiv y Rc (1206):** la misma exigencia que Rprot, porque la ESD también reparte la tensión en el divisor. Queda para el bloque 2, como dice el acta.
- **Relé TQ2SA:** sus 1500 V entre contactos abiertos dejan de cubrir la ESD si el GDT es lento (3.8 kV por contacto). Un salto de arco entre contactos sólo cierra el camino hacia Rohm y la TVS, que lo soportan. Hay que comprobarlo en el prototipo, no en la ficha.

**Clasificación.** D1/D2 en el acta: **artefacto del modelo** (pulso de 0.1 ns) **y criterio mal puesto** (tensión de trabajo continua). El riesgo **físico** real está en la envolvente sin GDT, y lo cubren la exigencia de pulso de los MPN y el ensayo en el prototipo.

## 4. D6, seis N2 apagados que siguen derivando: criterio mal puesto

- Con el DMM apagado, los rieles quedan flotando (load switch abierto, 1 µF sobre 1 TΩ). N2 no tiene una referencia estacionaria hacia la que recuperarse. Medir el tiempo de recuperación a 100 µV de un nodo flotante no tiene sentido: el 2.0 s del acta es el final de la ventana, como Codex reconoce.
- Lo que importa es la medida **al encender**. `encendido_t5.py` toma el caso T5 apagado (b0, riel nominal) y cierra el interruptor de carga en t = 12 s, 2 s después de retirar la red:

| t | V(n2) |
|---|---:|
| 11.999 s (apagado) | −45.380 mV |
| 12.0002 s | +2.443 mV |
| 12.0005 s | +1.778 mV |
| 12.001–12.2 s | 1.777647 mV (constante a < 1 nV) |

  Los rieles quedan en ±4.8988 V a los 10 ms y X0 en 2.3 pV.
- **Al encender, N2 se asienta en menos de 1 ms.** Es la misma escala que los casos alimentados del acta (0.12–0.13 ms). El valor final, 1.78 mV, es el reposo con fugas del modelo. Desde 12.001 s no varía más de 1 nV.
- He simulado uno de los seis estados (b0, riel nominal). Los demás difieren en el riel y en el diodo de cuerpo. Encender fija los rieles por el mismo camino, así que espero lo mismo, pero no lo he simulado.
- **Clasificación: criterio mal puesto.** D6 debe evaluarse como «recuperación ≤ 1 s después de retirar el fallo con el equipo encendido, o después de encender». Así se cumple: ≤ 0.13 ms alimentado y < 1 ms al encender.

## 5. Otros puntos

- **D3:** 325.27 V frente a 336 V (80 % de 420 V) en T3, con 230 Vrms nominales.
  - Con +10 % de red (253 Vrms, 357.8 V de pico) se supera el 80 %, aunque queda 15 % por debajo del cebado mínimo.
  - **Riesgo físico no simulado:** si una sobretensión de red (o 400 V entre fases por mal uso) ceba el GDT, el arco de 20 V cortocircuita la red a través de las puntas. La rama V/Ω no tiene fusible que corte esa corriente de seguimiento.
  - Conviene que el manual y el rótulo limiten la entrada V/Ω y que la decisión del GDT lo recoja. No lo clasifico como fallo de S11.4, porque el plan no lo pedía.
- **D4:** sólo cumple con el GDT tal como está modelado. La envolvente da 24–40 mA por RX0/RX1 (§2).
- **D5:** cumple, con 3.606 V y 106 mV de margen. Lo he recalculado.
- **D7:** cumple, con ≤ 10.57 V.
- **Contradicción con la decisión anterior:** P23 y dmm_rev21 descartaban el GDT; la decisión A+B lo añade. Codex lo señala bien.

## 6. Resumen

| Criterio del acta | Clasificación | Qué hace falta |
|---|---|---|
| D1/D2: Rohm 543 V y Rprot 366 V en ESD | **Artefacto** (pulso de 0.1 ns) **y criterio mal puesto** (tensión de trabajo continua) | Exigir pulso en el MPN según la envolvente sin GDT (§3) |
| D2: relé abierto 38.6 V | Cumple sólo con el GDT ideal; envolvente de 3.8/7.3 kV | Ensayo ESD en el prototipo |
| D4: 1.18 mA | Cumple sólo con el GDT ideal; envolvente de 24–40 mA | Ensayo ESD en el prototipo (fuga y latch-up del 4051) |
| D6: seis N2 apagados | **Criterio mal puesto**; al encender se asienta en < 1 ms | Reformular D6 (equipo encendido o al encender) |
| D3, D5, D7 | Cumplen en el modelo | D3: margen pequeño con red +10 % |

## 7. Veredicto

**El bloque 1 puede darse por cerrado en simulación,** con estas salvedades:
- la simulación no puede decidir más sobre la ESD;
- el cumplimiento de D2 y D4 depende de la respuesta real del GDT, que ningún modelo de catálogo garantiza;
- seguir simulando no lo resolverá; lo resuelven el ensayo y los MPN.

**Condiciones para el prototipo:**
1. **ESD IEC 61000-4-2** en V/Ω–COM, en modo V y en ohmios, apagado y encendido: ±4 kV por contacto y ±8 kV en el aire, 10 descargas por polaridad. Después:
   - mide ΔR de Rprot, Rohm y Rdiv (≤ 1 %);
   - mide la fuga de X0/X1 del 74HC4051 y comprueba que no hay latch-up (corriente de los rieles);
   - comprueba que el relé y la medida de 1 kΩ y de 1 MΩ siguen dentro de su exactitud.
2. Si es posible, sonda la tensión en V/Ω durante la descarga para ver a qué tensión y con qué retardo ceba el GDT real.
3. 230 Vrms (y 253 Vrms) en V durante 10 s: el GDT no debe cebar. Mide la corriente.
4. Recuperación de N2 tras la red con el equipo encendido y al encender (≤ 1 s).

**Exigencias para los MPN:**
- Rprot y Rdiv/Rc en 1206 antipulso: 1.2/50 µs ≥ 1.5 kV (mejor ≥ 2.5 kV), ESD ±8 kV con ΔR ≤ 1 %.
- Rohm en 2512 antipulso: 1.2/50 µs ≥ 2 kV (mejor ≥ 3 kV), con curva de energía de pulso.
- El GDT con hoja del fabricante: cebado por impulso a 1 kV/µs, tiempo de respuesta, corriente de seguimiento y vida útil. Sin hoja, los datos de LCSC siguen siendo supuestos.
- El BAT54 del MPN elegido (Nexperia), comprobado frente al modelo Vishay: V_F a 100 µA, Cj y fuga.

**Qué no hago:** no apruebo la supervivencia ESD ni la del relé abierto, ni D4 sin el ensayo. No marco nada como decisión aceptada; Keneth decide.
