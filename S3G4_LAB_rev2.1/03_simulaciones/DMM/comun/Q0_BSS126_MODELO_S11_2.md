# Q0 — BSS126 y borne A — S11.2

Codex, 7 octubre 2026. Fuentes locales; ninguna descarga. Modelo de ingeniería, no modelo del fabricante.

## Datos y páginas

| Hoja | Página PDF | Dato y condición |
|---|---:|---|
| Infineon BSS126 rev. 2.1 | 1 | 600 V; Ptot 0.50 W a TA=25 °C; Tj máximo 150 °C; ID admisible 21 mA a25 °C,17 mA a70 °C; VGS ±20 V; ESD HBM clase0; la hoja imprime literalmente «0 >250 V», sin resolver esa notación |
| BSS126 | 2 | IDSS mínimo7 mA aVGS0,VDS25 V; **sin típico ni máximo**. VGS(th) −2.7/−2.0/−1.6 V aID8 µA,VDS3 V. No es una especificación de corte a corriente cero |
| BSS126 | 2 | Ron320 Ω típico/700 Ω máximo aVGS0,ID3 mA; Ron280/500 Ω aVGS10,ID16 mA; RthJA250 K/W, huella mínima; BV600 V aVGS−5,ID250 µA |
| BSS126 | 3 | Ciss21/Coss2.4/Crss1 pF típicos a25 V; máximos28/3.2/1.5 pF; diodo cuerpo16 mA continuo,64 mA pulsado; VF0.81 típico/1.2 V máximo a16 mA; trr160 ns típico |
| BSS126 | 4 | SOA y ZthJA; Ptot se reduce con TA. No se sustituyen esas curvas por un rating de avalancha |
| BSS126 | 5–6 | Curvas típicas IV, transferencia, Ron(T), umbral(T) y capacidades(V). No son extremos garantizados de temperatura |
| GBU808, Diodes DS21227 rev8 | 2 | 800 V;8 A; IFSM200 A, media senoide8.3 ms; I²t166 A²s a8.3 ms; VF1 V máximo a4 A; CT130 pF; RthJC2.2 °C/W bajo montaje especificado |
| Littelfuse216 GD.06/16/22 | 1 | 3.15 A: 275% 10 ms–2 s;400% 3–300 ms;1000% ≤20 ms. A150% ≥60 min,210% ≤30 min |
| Littelfuse216 | 2 | 3.15 A;250 Vac; corte1500 A; Rfría0.0368 Ω nominal; I²t fusión6.7 A²s nominal; curva tiempo-corriente promedio, dibujada hasta1 ms |

Los 21 mA de BSS126 p1 **no son IDSS máxima**. Los175 A/127 A²s del rediseño no coinciden con la hoja local del GBU808. El fusible mantiene0.040 Ω del contrato; se conserva la discrepancia con0.0368 Ω nominal de su hoja.

## Modelo y comprobación

`bss126_s11_2.inc`: MOS de nivel1, puertas cruzadas externamente; umbral a8 µA e IDSS ajustados conjuntamente:

```
VTO = |VGS(th)| / (1 − sqrt(8 µA / IDSS))
KP = 2 IDSS / VTO²
ID_sat = KP/2 · max(VGS + VTO, 0)²
```

RD añade la resistencia necesaria para obtener700 Ω a3 mA, sin cambiar IDSS saturada. El uso simultáneo de extremos independientes es una envolvente de ingeniería: la hoja no publica su correlación. La sensibilidad IDSS21 mA sirve para exponer el riesgo; no cierra la envolvente superior de producción. Se usan VGS(th)−1.6 y−2.7 V y TA0,25,70 °C. El típico de umbral−2 V está documentado; no existe IDSS típico garantizado para construir una pareja nominal inequívoca.

La p6 se inspeccionó visualmente. Aproximaciones gráficas: VTO aumenta3.7 mV/K y Ron se multiplica por exp(0.0055·(T−25)). KP varía de modo que la resistencia del canal crezca con ese factor. No hay curva de BV(T) garantizada; se deja BV600 V sin inventar su coeficiente. Capacitancias constantes de p3: Cgs20,Cgd1,Cds1.4 pF. El diodo cuerpo se aproxima con N2,IS2 nA,Rs1 Ω,trr160 ns; no es un ajuste único de la curva completa. La avalancha a600 V permite estimar estrés; **no modela avería ni garantiza energía**. Su rodilla se fija a250 µA en600 V: no reproduce simultáneamente la especificación de Ioff≤0.1 µA en600 V de p2. No se añade un clamp de puerta ficticio. La indicación HBM de p1 no certifica la descarga IEC del borne.

`verificar_q0_s11_2.py`:12/12 verificaciones LTspice,2.721 s de pared. A25 °C: IDSS7.000002/21.000002 mA; I aVGS(th)=8.00173 µA; Ron699.99985…699.99998 Ω. `resultados/s11_2_q0_ltspice.csv` conserva todos los valores. El CSV de transferencia calcula la curva saturada; a3 V y corrientes altas la RD hace que la curva real deje de estar saturada, lo que limita su comparación con la Fig7.

La temperatura de unión que se informa es **estimada por potencia media de10 s**, Tj=TA+250·E10/10. No hay realimentación electro térmica ni validación del rizado térmico de60 Hz. El límite contractual es120 °C; además,50% de Ptot a70 °C equivale aproximadamente a0.16 W, no0.25 W.

## R_LIM

**No se ha elegido una resistencia garantizada.** En la aproximación Shockley que identifica Vp con1.6/2.7 V, el extremo bajo exige R≤700.374 Ω; la ausencia de cota superior de IDSS exige R≥1125 Ω. Ajustando VTO al umbral de8 µA, el primer límite pasa a724.880 Ω: sigue sin solaparse con1125 Ω. Esto demuestra la incompatibilidad dentro del modelo; la hoja por sí sola no proporciona una curva extrema completa para probar existencia física de otra R.

La campaña emplea **700 Ω exclusivamente como diagnóstico**, para no detener la evaluación del borne A, ESD y los riesgos de O2. No se fuerza su aceptación ni se cambia otro valor. La etiqueta de cada caso identifica R_LIM y los supuestos reales.

## Fusible y puente

El fusible integra q=∫I_fusible²dt. Funde a6.7 A²s nominal y abre a6.7·k para k1,2,3; el segundo tramo representa el arco supuesto del rediseño. Un interruptor Schmitt de0.040 Ω abre en ese umbral, con histéresis2 mA²s para impedir que el error de redondeo vuelva a cerrar el fusible fundido. La apertura conserva el borne A conectado a la red y su aviso por10 MΩ; B queda tras10 kΩ. Se informa corriente residual después de abrir.

La curva promedio de la p2 fue inspeccionada, junto con la tabla de p1: el modelo adiabático predice42.20 ms a400% y6.752 ms a1000%, dentro de sus intervalos IEC; a275% da89.29 ms (10 ms–2 s). **No se usa esta ley a150%**, donde violaría el mínimo de60 min. Los cortocircuitos de Q5 son de alta corriente. La mayoría de las aperturas calculadas están por debajo del1 ms mínimo dibujado en la curva: son extrapolaciones de I²t nominal, sin curva garantizada de corriente de corte ni tolerancia de I²t. El factor de arco tampoco es de la hoja. No se afirma cumplimiento exacto de una curva digitalizada ni una corriente de corte real.

GBU808: ajuste VF1 V a4 A,N2,Rs15 mΩ por diodo; Rs es supuesto del rediseño, no dato garantizado. IFSM e I²t se comparan con200 A/166 A²s, y con el criterio más estricto100 A/83 A²s. La I²t publicada es para8.3 ms; extenderla a20–3000 µs es una comparación orientativa, no una nueva garantía de pulso.

## Otras incertidumbres

No se encontró hoja local del BZT52C5V6. Se conserva su pieza y se modela un sumidero nominal5.6 V a5 mA,Rs40 Ω,Cjo100 pF, con parámetros sin garantía. No hay MPN/hoja de pulso de R_PROT,R_LIM,R_B ni del derivador: no se certifica su energía a partir del encapsulado.

La ESD sigue la red contractual150 pF/330 Ω,8 kV aire con300 Ω adicionales; no es el generador RLC calibrado de S2b. Energías iniciales1.2/4.8 mJ. Se conserva paso≤1 ns y10 µs totales; no se descarga nada ni se añade TVS.
