# GDT en V/Ω: corriente de seguimiento de red y ESD (S11.5, simulación pequeña)

Fecha: 2026-10-07. Agente: Claude. Encargo: comparar con números cuatro formas de montar el GDT SMD4532-600NF entre V/Ω y COM. No decide Claude; decide Keneth.

## 1. Método

- Base: deck T2 de S11_4 (`T2_vo_v_rel0_…_esd_a4000…reduced.cir`: modo V, relé abierto, sin alimentar), que contiene el circuito de `comun/dmm_bloque1_final.inc`. Se copia sin tocarlo y se sustituye solo el GDT.
- El GDT es el modelo del bloque 1 (cebado en continua 420 V corner bajo, 1 kV por impulso, arco 20 V + 1 Ω, mantenimiento 10 mA), con la cadena en serie delante: nodo `vin` → cadena → `ga` → GDT → COM. Se añadió una fuga de 1 GΩ en el GDT (supuesto, resistencia de aislamiento típica).
- ESD: 150 pF / 330 Ω, ±4 kV por contacto, 50 µs, paso 1 ns. Se repite con el cebado del GDT 100 veces más lento (τ = 100 ns frente a 1 ns del modelo) porque `AUDITORIA_CLAUDE_S11_4.md` §2 avisa de que el modelo ceba de forma optimista.
- Red: 325.27 Vpk, 60 Hz, con 0.7 Ω (0.5 de red + 0.2 de puntas), más un transitorio 1.2/50 µs que suma el pico total a 1000 V. Dos fases: en el pico de la red (90°) y a 10° tras el cruce por cero (el caso de arco más largo). 25 ms, paso máx. 100 ns.
- Nominal: 230 y 253 Vrms durante 0.1 s con 100 kΩ de impedancia de fuente, para medir fuga y efecto en la medida.
- Archivos: `gdt_seguimiento/gdt_seguimiento.py` (genera, lanza y analiza), `gdt_seguimiento/decks/*.cir` (56 decks), `gdt_seguimiento/resultados_gdt.json` (todas las medidas). Se ejecutó en `C:\s115`. Los `.raw` no se guardan (hasta 34 MB cada uno). Ninguna ejecución terminó con «tolerance relaxed».
- Validación: «GDT solo» con τ = 1 ns da 38.6 V en el relé abierto y 1.18 mA en X1, igual que el acta S11_4.
- Incidencias del propio banco: (a) el MOV como fuente B con ley de potencia no converge con el frente de la ESD; se descartó y se usan dos diodos antiparalelo con N = 1002 (exponencial) y Rs = 0.15 Ω; (b) el fusible tenía un fallo de histéresis del interruptor, corregido.

## 2. Piezas reales (pcbparts, LCSC) y supuestos

| Pieza | LCSC | Precio | Datos de catálogo |
|---|---|---|---|
| GDT SMD4532-600NF (hongjiacheng) | C47345384 | 0.277 USD | 600 V ±30 %, Vimp 1 kV, 2 kA |
| R 47 Ω 2512 2 W (Ever Ohms CRH2512J47R0E04Z) | C175430 | 0.042 USD | 200 V máx. (10, 22 y 100 Ω equivalentes, ≈ 0.04 USD) |
| Varistor 14D431K (hongjiacheng) | C49069732 | 0.090 USD | V1mA 387–473 V, 275 Vac / 350 Vdc, Vc 710 V, 4.5 kA, 115 J, disco 14 mm, paso 7.5 mm |
| Fusible 0466.125NRHF (Littelfuse), 1206 | C206983 | 0.090 USD | 125 mA, **125 V**, I²t de fusión 0.00064 A²s, 50 A |
| Varistor 14D271K (hongjiacheng), solo como comparación | C49072888 | 0.150 USD | V1mA 243–297 V, **175 Vac**, Vc 455 V, 70 J |

Supuestos (sin ficha local): curva del MOV 430 V a 1 mA y 710 V a 50 A (el 14D271K: 270 V a 1 mA y 455 V a 50 A); resistencia fría del fusible 6 Ω; capacidad de pulso de una 2512 de película gruesa ≈ 1 J (pulso de ms); no hay dato de corriente alterna de seguimiento del GDT.

Aviso de nomenclatura: un **14D271K no es de 275 Vrms**. «271» es V1mA = 270 V y 175 Vac. La pieza de 275 Vrms es el **14D431K**.

## 3. ESD ±4 kV por contacto

Los resultados son idénticos para +4 kV y −4 kV (diferencia < 1 %). Unidades: V en el relé abierto (vin − ptin), V en la cadena R_PROT completa (vin − x0), V en X0, mA por Rx0/Rx1.

| Opción | Relé abierto τ=1 ns / 100 ns | R_PROT τ=1 / 100 ns | X0 | I(X0) / I(X1) máx. | ¿ESD protegida? |
|---|---|---|---|---|---|
| Sin GDT (referencia) | 3790 / 3790 V | 3800 V | 1.4 V | 4.3 / 4.8 mA | **No** (relé > 1200 V) |
| GDT solo (referencia) | 39 / 602 V | 1070 / 2240 V | 0.5–0.6 V | 1.5–4.0 / 1.2–2.1 mA | Sí |
| R 10 Ω | 126 / 645 V | 1140 / 2290 V | 0.6 V | 1.7–4.0 / 2.1–2.4 mA | Sí |
| R 22 Ω | 238 / 687 V | 1210 / 2290 V | 0.6 V | 2.4–4.0 / 2.5–2.7 mA | Sí |
| R 47 Ω | 452 / 784 V | 1360 / 2310 V | 0.7 V | 3.1–4.0 / 2.9–3.0 mA | Sí |
| R 100 Ω | 832 / 1030 V | 1640 / 2350 V | 0.7 V | 3.6–4.0 / 3.3 mA | Sí, margen justo con GDT lento |
| GDT + MOV 14D431K | 682 / 941 V | 1670 / 2460 V | 0.8 V | 3.5–4.1 / 3.8 mA | Sí |
| GDT + fusible 125 mA | 88 / 622 V | 1090 / 2240 V | 0.6 V | 1.6–4.0 / 1.9–2.3 mA | Sí (fusible al 0.55 % de su I²t) |
| (comparación) GDT + MOV 14D271K | 447 / 797 V | — | 0.8 V | 3.0–4.0 / 3.5 mA | Sí |

Notas:
- Todas las variantes con GDT cumplen relé ≤ 1200 V y X0/X1 ≤ 10 mA, incluso con el GDT 100 veces más lento. Sin GDT no se cumple el relé. La ESD no distingue entre las opciones; la decisión la marca el seguimiento de red.
- Este deck está sin alimentar (POWER = 0), por eso X0/X1 salen en 3–5 mA incluso sin GDT. La auditoría S11_4 daba 24–40 mA en su envolvente con riel alimentado: no es comparable y sigue pendiente de ensayo.
- La resistencia en serie sube la tensión del relé casi en proporción (12 A × R). Con 100 Ω queda a 1030 V con GDT lento (86 % de 1200 V).

## 4. Red cebando el GDT (1000 V en el pico de 325 V, 0.7 Ω de red)

| Opción | Corriente de seguimiento (pico tras el transitorio) | Duración del arco (fase 90° / 10°) | Energía de la pieza principal (90° / 10°) | Energía en el GDT (arco) |
|---|---|---|---|---|
| GDT solo (referencia) | 183 A; 576 A en el transitorio | 4.0 / 7.7 ms | — | 90 / 162 J |
| R 10 Ω | 26.6 A | 4.0 / 7.7 ms | R: 17.0 / 30.2 J | 3.1 / 5.8 J |
| R 22 Ω | 13.2 A | 4.0 / 7.7 ms | R: 9.1 / 16.2 J | 1.1 / 2.1 J |
| R 47 Ω | 6.4 A | 4.0 / 7.7 ms | R: 4.6 / 8.2 J | 0.44 / 0.84 J |
| R 100 Ω | 3.06 A | 4.0 / 7.7 ms | R: 2.2 / 4.0 J | 0.19 / 0.36 J |
| GDT + MOV 14D431K | **0 A** (el arco se apaga al acabar el transitorio) | 0.09 / 0.05 ms | MOV: 1.96 / 1.38 J, 134 A pico, 752 V | 0.28 / 0.20 J |
| GDT + fusible 125 mA | 0 A (el fusible abre) | 0.0002 ms | I²t = 0.00064 A²s (100 % de fusión), 76 A pico | 0.0008 J |
| (comparación) GDT + MOV 14D271K | 12.8 mA durante 0.04 ms (límite) | 0.34 / 0.09 ms | MOV: 5.7 / 3.6 J, 270 A pico | 2.0 / 1.4 J |

Claves:
- La resistencia en serie **no corta el seguimiento**: la corriente baja como (325 − 20)/(R + 1.7) y el arco dura hasta el cruce por cero (4.0 ms si el transitorio llega en el pico, 7.7 ms si llega justo después del cruce). A 100 Ω siguen siendo 3 A durante ms, y la resistencia disipa 2–30 J.
- El MOV 14D431K sí lo corta: con 305 V (325 V menos el arco de 20 V) por debajo de su V1mA mínimo de 387 V, solo circulan µA. El arco del GDT cae por debajo de 10 mA al terminar el transitorio. La red nunca ve un cortocircuito.
- El fusible también interrumpe, pero con 125 V de tensión nominal debe abrir con ≈ 980–1020 V a sus extremos: el modelo es ideal, la pieza real no está calificada para ello (ver §6).
- El 14D271K, en el nominal de 270 V, queda justo en el límite (12.8 mA al pico, apenas por encima de los 10 mA de mantenimiento del modelo). Con la tolerancia baja de la ficha (243 V) estimo, extrapolando la curva, ≈ 38 mA continuos en cada pico: el arco no se apagaría y el MOV se calentaría. Por tanto, **no es válido** (y además su máximo es 175 Vac).

## 5. Fuga y efecto sobre la medida (230 y 253 Vrms, fuente de 100 kΩ)

| Cadena | Corriente RMS de la rama | Cambio de x2 frente a sin GDT |
|---|---|---|
| GDT solo (fuga 1 GΩ supuesta) | 0.19 µA (230 V) / 0.21 µA (253 V) | −0.01 % / +0.1 % |
| GDT + MOV 14D431K | 0.013 µA / 0.019 µA (el MOV estrangula la fuga) | +0.08 % / +0.14 % |

- El GDT no se ceba en ningún caso (estado máximo = 0): 325 V (230 Vrms) es el 77 % del cebado mínimo de 420 V; 358 V (253 Vrms) es el **85 %**, por encima del 80 % pedido. La diferencia de x2 está dentro del ruido de la simulación (±0.1 %).
- La fuga de 0.2 µA frente a los ≈ 23 µA del divisor es ≈ 1 %. No altera la relación del divisor, solo carga la fuente: error ≈ Rs/1 GΩ (0.01 % con 100 kΩ). Con el MOV en serie queda 15 veces menor.
- La capacidad de la cadena (0.5 pF del GDT, 460 pF del MOV detrás del GDT abierto) no aparece en la medida porque el GDT en serie la aísla.

## 6. Criterio ≤ 80 % de tensión y ≤ 50 % de energía por pieza

| Opción | Cumple | Motivo |
|---|---|---|
| 1. R 10–100 Ω | **No** | En el transitorio de 1 kV, la R ve 840–960 V frente a 200 V de catálogo (4–5×) y disipa 2–30 J frente a ≈ 1 J supuesto. Solo cumple la ESD (35–270 µJ). El GDT tampoco: 26 A durante 3.7 ms con 10 Ω, sin dato de ficha. |
| 2. GDT + MOV 14D431K | **Sí, con dos condiciones** | MOV: 2.0 J de 115 J (1.7 %), 134 A de 4500 A (3 %); en operación normal no ve tensión (el GDT la aísla); su tensión de trabajo máx. es 275 Vac frente a 253 Vrms (92 %), pero solo la vería si el GDT cebara. GDT: 134 A de 2 kA (7 %) y 0.28 J. Condición 1: el GDT queda al 77 % (230 V) y al 85 % a 253 Vrms. Condición 2: una sobretensión sostenida (por ejemplo 400 Vrms por mal uso) haría conducir el MOV de forma continua; es una limitación de cualquier MOV. |
| 3. GDT + fusible 125 mA | **No** | Tensión: el fusible, de 125 V, tiene que abrir con ≈ 1000 V. No hay en LCSC un fusible SMD de 125 mA con 250 V que pude encontrar (lo más cercano, AEM MF2410, es de 2 A). ESD: solo gasta el 0.55 % de su I²t, bien. Pero tras fundirse el fusible el GDT queda desconectado y no hay aviso: la ESD pasaría a ser la del caso «sin GDT» (3.8 kV en el relé). |
| 4. Sin GDT | Solo referencia | ESD: relé 3790 V y R_PROT 3800 V; D2 no se cumple. Habría que dimensionar las piezas de impulso según la envolvente del §2 de la auditoría S11_4 y verificar en prototipo. |

## 7. Costes (LCSC, 1 unidad)

| Opción | Piezas añadidas | Coste total de la rama |
|---|---|---|
| 1. GDT + R | 0.04 USD | 0.32 USD |
| 2. GDT + 14D431K | 0.09 USD (C49069732) | 0.37 USD |
| 3. GDT + fusible | 0.09 USD (C206983) | 0.37 USD |
| 4. Sin GDT | 0 | 0 (más el sobrecoste de las piezas de pulso del bloque 1) |

## 8. Recomendación

**Opción 2: GDT SMD4532-600NF en serie con un varistor 14D431K (C49069732, 0.09 USD).** No la decido yo; es lo que apoyan los números.

1. Es la única que elimina el seguimiento de red sin añadir una pieza que se consuma: la corriente de seguimiento es 0 A (frente a 3–27 A durante 4–8 ms con la resistencia) y toda la energía queda en 2 J en un MOV de 115 J.
2. Mantiene la ESD protegida con margen: relé abierto 682 V (941 V si el GDT fuera 100 veces más lento) frente a 1200 V, y X0/X1 ≤ 4.1 mA.
3. No afecta a la medida: fuga ≈ 0.01–0.02 µA y el GDT aísla.
4. La resistencia en serie solo empeora el relé y no corta el arco. El fusible de 125 V no está calificado para 1 kV y se pierde sin aviso.

Avisos:
- **No uses el 14D271K** (175 Vac, V1mA 243–297 V): en el límite de apagado del arco y fuera de rango a 230 Vrms.
- Es una pieza de disco, 14 mm y paso 7.5 mm. No encontré en el catálogo de LCSC un varistor SMD de 275 Vac (los 1812 llegan a 125 V). Hay que confirmar el espacio en la rev 2.1, la distancia de aislamiento, y que quepa en la zona de V/Ω.
- El 253 Vrms deja el GDT al 85 % de su cebado mínimo. Si se quiere el 80 %, haría falta un GDT de 800 V o más (no simulado).
- El manual debería limitar la entrada V/Ω a 253 Vrms: con una sobretensión sostenida el MOV conduce y no hay fusible.
- Todos los datos de pieza son de catálogo, sin ficha local. El GDT tiene mantenimiento 10 mA, arco 20 V y cebado (τ) supuestos. La fuente de 0.7 Ω da 576 A con un transitorio de 1 kV, más duro que la fuente de 2 Ω de IEC 61000-4-5. La curva del MOV (exponencial ajustada a 1 mA y 50 A) es una aproximación.
- Pendiente de prototipo: ensayo de red con transitorio, medida de la fuga del GDT a 253 Vrms y comportamiento tras repetidas descargas.
