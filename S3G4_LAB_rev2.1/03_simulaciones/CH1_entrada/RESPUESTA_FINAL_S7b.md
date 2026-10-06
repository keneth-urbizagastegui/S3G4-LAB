# Respuesta final — S7b

Ficheros: `comun/ch1_comun_s7b.inc`, `ejecutar_s7b.py`, bancos, soluciones iniciales y registros en `S7b/`, `resultados/s7b_*.csv` (incluida tabla de calibración), `ACTA_S7b.md`, este resumen y diario `ai-context/journal/2026-10-04-codex-s7b-reanudacion.md`; diario inicial conservado.

Código **0**; **10496 ejecuciones nativas**, **4416/4416 casos lógicos**, **6912.1 s (115.20 min) de tiempo acumulado registrado**, 10 trabajadores. 13319 archivos protegidos, 0 cambios. Código 0 significa campaña ejecutada, no aceptación eléctrica. Las ejecuciones incluyen intentos fallidos y repetidos; las pruebas de diagnóstico y smoke tienen registros separados.

Errores finales: 0; advertencias finales: 69 mensajes en 1 caso. Historial: 36 intentos lógicos fallidos o sin medición durable, todos recuperados; incluye los 18 preservados durante el reinicio. Auditoría: `S7b/campaign/s7b_auditoria_cierre.json`.

| criterio | fraccion | resultado |
| --- | --- | --- |
| S7b-C1 | 0.005 V/div MC: 500/500 (100.0 %); 0.05 V/div MC: 500/500 (100.0 %); 0.5 V/div MC: 500/500 (100.0 %); 5.0 V/div MC: 500/500 (100.0 %) | PASA |
| S7b-C2 | 0.005 V/div MC: 500/500 (100.0 %); 0.05 V/div MC: 500/500 (100.0 %); 0.5 V/div MC: 500/500 (100.0 %); 5.0 V/div MC: 500/500 (100.0 %) | PASA |
| S7b-C3 | 0.005 V/div MC: 100/100 (100.0 %); 0.5 V/div MC: 100/100 (100.0 %) | PASA |
| S7b-C4 | 0.005 V/div: 500/500 (100.0 %); 0.05 V/div: 500/500 (100.0 %); 0.5 V/div: 500/500 (100.0 %); 5.0 V/div: 500/500 (100.0 %) | PASA |
| S7b-C5 | placas únicas: 416/500 (83.2 %) | FALLA |
| S7b-C6 | casos deterministas K3; no estimador de placas: 36/36 (100.0 %) | PASA |
| S7b-C7 | casos nominales K4; no estimador de placas: 10/10 (100.0 %) | PASA |
| S7b-C8 | 0.005 V/div: 484/500 (96.8 %); 0.05 V/div: 488/500 (97.6 %); 0.5 V/div: 484/500 (96.8 %); 5.0 V/div: 488/500 (97.6 %) | PASA |

C1–C4/C8: fracciones por escala de las mismas 500 placas; C3 usa las primeras 100 por escala. C5 cuenta placas únicas. C6/C7 son fracciones de casos deterministas y no estiman la fracción de placas. Criterios nominales completos: `s7b_criterios.csv`.

Emparejamiento: ganancia C4 en las cuatro escalas simultáneamente 500/500 (100.0 %); margen C8 en las cuatro escalas simultáneamente 481/500 (96.2 %).

## K1 por escala

| escala | MHz | pico_dB | G_DC | subida_ns | ruido_pct_div | A45_dB |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 2.0076470636195487 | 1.741861881050446e-05 | -49.498204366691645 | 182.05827863774803 | 0.32164412915359325 | 21.699597410789288 |
| 0.01 | 2.007006627631387 | 1.7422879405143897e-05 | -24.741027229818304 | 182.11371663951826 | 0.27706775518838783 | 21.712150742566234 |
| 0.02 | 2.0072689113250894 | 1.7425333013812588e-05 | -12.387950945760789 | 182.09247676658615 | 0.2615612833060895 | 21.70702243244001 |
| 0.05 | 2.007542668707847 | 1.742692205835376e-05 | -4.946293459992416 | 182.07125714396145 | 0.25490868528127547 | 21.701692607956826 |
| 0.1 | 2.007610871221915 | 1.742746784538957e-05 | -2.470671866050922 | 182.0636849930594 | 0.2531858225340373 | 21.70041131921228 |
| 0.2 | 2.007639135794943 | 1.742774497326087e-05 | -1.2353338936373908 | 182.06215984627482 | 0.25242120426809617 | 21.69995922944044 |
| 0.5 | 2.0068432901978297 | 1.771334399799645e-05 | -0.49532556828858626 | 182.08563157364756 | 0.3218227877422076 | 21.70273684683138 |
| 1.0 | 2.0062036010569804 | 1.7712400727579387e-05 | -0.24758197832811174 | 182.14004742275904 | 0.27711957782725666 | 21.715290204949973 |
| 2.0 | 2.0064655652192243 | 1.771224000923424e-05 | -0.12396548343028141 | 182.12084402926004 | 0.2615750459348485 | 21.710161908155538 |
| 5.0 | 2.0067389941719895 | 1.7712244468275355e-05 | -0.04949726249823957 | 182.0956319695796 | 0.2549109363503447 | 21.704832091100275 |
| 10.0 | 2.0068071168178143 | 1.771226569307961e-05 | -0.02472386543142978 | 182.09097693682457 | 0.25318638783733666 | 21.7035508046736 |
| 20.0 | 2.0068353517153716 | 1.771228537882037e-05 | -0.012361912307077673 | 182.08988772777937 | 0.25242134594006244 | 21.70309871602451 |

## Monte Carlo

Semilla 2026100371, 500 placas emparejadas en cuatro escalas.

| escala | magnitud | N | min | p2p5 | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | −3 dB (MHz) | 500 | 1.8249880438491262 | 1.8941523057379466 | 2.1240310452830142 | 2.158582274113354 |
| 0.005 | peak_db | 500 | 1.6679902311834463e-05 | 1.677072561314893e-05 | 0.01038926293554638 | 0.013947841800305684 |
| 0.005 | gain_dc_signed | 500 | -51.00817621306328 | -50.6647700495335 | -48.25482064277448 | -47.834230703112134 |
| 0.005 | noise_pct_div | 100 | 0.30749887446018487 | 0.31056781137500855 | 0.33148695365026076 | 0.335759819120154 |
| 0.05 | −3 dB (MHz) | 500 | 1.824886061589578 | 1.89406165524936 | 2.1239330717353675 | 2.1585174846193387 |
| 0.05 | peak_db | 500 | 1.6681886731942615e-05 | 1.6772849439279723e-05 | 0.010472247113181432 | 0.014025547507521746 |
| 0.05 | gain_dc_signed | 500 | -5.141692471244664 | -5.071128232202469 | -4.819243227927964 | -4.773372713090825 |
| 0.5 | −3 dB (MHz) | 500 | 1.8194045926167004 | 1.8882123182871355 | 2.125906048066543 | 2.171389544432492 |
| 0.5 | peak_db | 500 | 1.73057635920997e-05 | 1.746118421318395e-05 | 0.09817218529874809 | 0.24320726161102735 |
| 0.5 | gain_dc_signed | 500 | -0.5102256085402563 | -0.5069447423682296 | -0.48294603178333506 | -0.4777811242759526 |
| 0.5 | noise_pct_div | 100 | 0.307525906854235 | 0.3107868790156448 | 0.3317333601723249 | 0.3359586588206279 |
| 5.0 | −3 dB (MHz) | 500 | 1.8193013917123135 | 1.8880843693304583 | 2.1258033593401016 | 2.171216198971228 |
| 5.0 | peak_db | 500 | 1.730430557816282e-05 | 1.7459762662205375e-05 | 0.09819828921256286 | 0.24322116500353377 |
| 5.0 | gain_dc_signed | 500 | -0.051431424531877906 | -0.05074157648670651 | -0.04823009728046542 | -0.04771305043977256 |

Trimmer requerido: 0.906933…7.804264 pF; P2.5/P97.5: 1.519531/7.113128 pF. Rango 2–6 pF suficiente en 416/500 placas. Se aplica recorte físico en las demás.

## Protecciones con rieles extremos

Combinaciones independientes 4.80/5.00 V; ±40 V en cinco escalas y ±100 V en POS1/100, acoplo DC/AC.

| etapa | diferencial_max_V | I_entrada_max_mA |
| --- | --- | --- |
| OPA810 | 0.9197347583284019 | 7.741819733097827e-09 |
| U103A | 0.6870306399357464 | 4.409585440584809 |
| U103B | 0.6806465793489831 | 3.9131135592297164 |
| U105A | 0.03712926761385038 | 0.0003957645038401855 |
| U105B | 0.025748111546257224 | 0.00039215908017595333 |
| OPA836 | 0.6243412966071812 | 0.03190737687260322 |

ADC: 0.006878…3.288984 V. 4051: margen inferior mínimo 0.115322 V, superior 0.113765 V; alimentación máxima real 9.954115 V. Límites: OPA810 10 mA, OPA836 0.43 mA, U103/U105 2 V, ADC 0…3.3 V, 4051 dentro de VEE…VCC y suministro ≤10 V. Detalle por escala/riel: `s7b_limits.csv`, `s7b_k3.csv`.

Recuperación: 10 casos sin conducción directa BAV199; máximo medido 0.671636 µs. Consumo total simulado: reposo 62.724264 mW, seno 65.065475 mW. Consumo por etapa y riel: `s7b_consumption.csv`; calibración: `s7b_tabla_calibracion.csv`.

## Método y dudas

- Cambios nominales únicos: AFE ±4.90 V; C_S fijo 1.20 nF. El circuito recuperado fija C_EQ=8.67 pF; el contrato cita 8.7 pF seleccionado y 8.67 pF nominal. Se conserva esta discrepancia de redondeo sin modificar el circuito durante la reparación numérica. Rieles regulados conservan 0.5 Ω, carga 5/42 mA y 5/39 mA, TVS y todos los valores previos. El 4051 usa los mismos ocho SWI1; niveles altos del decodificador siguen el riel real. No se simulan cambios dinámicos de toma.
- Monte Carlo: semilla 2026100371, 500 placas emparejadas en cuatro escalas; offsets independientes, pasivos independientes por instancia; uniformes, factores guardados. R ±1 %, divisor ±0.1 %; C ±5 %, pistas explícitas de 1/3 pF ±50 %. El trimmer no recibe tolerancia adicional: se ajusta y recorta a 2..6 pF. Réplica C_EQ recibe ±5 % tal como manda §2 aunque la selección en prueba podría reducirlo. CMID y condensadores internos/rieles no se dispersan: §2 especifica C0G y no asigna dispersión a esos otros modelos.
- Trimmer: Rtop=Rt1+Rt2; Rbp=Rb||Rbias; Csel=Cj(V+)+Cj(|V−|)+Csel_pista+2.5 pF+CswAC+CswGND; Ctop=Rbp*(Cb+Csel+Ctap)/Rtop−Coff; Ct2=Ct1*Ctop/(Ct1−Ctop); trimmer=Ct2−Ct2fixed. Cb no se reajusta por placa: el contrato pide dispersarlo ±5 % y ajustar el trimmer. La sonda ×10 motivó el ajuste en S1b; la igualdad de tau se calcula sin sustituir la transferencia BNC→PIN por la de punta de sonda.
- Offset OPA836 ±400 µV: hoja local opa836.pdf, SLOS712J, pp. 10/12, máximo a 25 °C; a −40..125 °C llega a 1080 µV (p.12). Fuentes adicionales en serie con IN+ para los seis amplificadores; no se suprime el offset propio del macromodelo (incertidumbre de doble contabilización de su típico). OPA810 ±715 µV y AD8039 ±3 mV según contrato.
- K2 DC: ganancia medida en tres puntos distintos de entrada (−0.01/0/+0.01 div) con DAC 1.25 V, mediante dos recorridos desde cero. DAC recorrido desde 1.25 hacia 0.2 y 2.3 V, paso 5 mV, entrada cero; se miden centros y extremos, sin sustituir DC por AC. La solución AC de la misma placa/escala se guarda con .savebias internal y se carga como recomendación .nodeset; no impone tensiones permanentes, componentes o tolerancias nuevos. Offset referido a centro ADC 1.25 V; DAC de centrado inferido con pendiente medida entre los dos primeros ajustes; posición restante comprobada con los extremos reales, incluido recorte. ±4.5 div exige llegar a 0.125 y 2.375 V. Esto juzga desplazamiento de traza en entrada cero, no amplitud de señal adicional a esa posición.
- K2 AC/ruido puede reutilizar su propio punto guardado o el punto de mc0 del smoke en la misma escala como recomendación inicial; siempre resuelve nuevamente todos los nodos con los valores y offsets de la placa actual. Se conservan semilla, realizaciones, tolerancias y todos los componentes; itl1/itl2=1000 amplía sólo el número máximo de iteraciones.
- Cada proceso tiene tiempo límite: 120 s AC/DC/ruido, 600 s K3 y 900 s transitorios. Popen sin pipes y taskkill /T /F al vencer, para evitar procesos o manejadores heredados colgados. Las cuatro ejecuciones nativas de cada K2DC se registran como hijas con su estado real en el nombre .meas. CSV y extras se ordenan por claves fijas.
- Si J2 falla numéricamente, reintento automático con la solución AC nominal de la misma escala como guía y itl4=1000; no cambia flancos, amplitudes, paso máximo ni tolerancias. --resume --retry-numerical aplica directamente ese método a los pendientes. El registro conserva los intentos fallidos como hijos/historia, y el resultado final se evalúa por el último intento de cada caso.
- Si J8 falla o agota el tiempo, reintento con la misma guía AC nominal y continuación desde DAC 1.25 V al valor solicitado, paso ≤5 mV calculado para alcanzar exactamente el extremo. Entrada cero; medida en el extremo real solicitado. No se cambia la tensión objetivo.
- Si K3 falla en su punto inicial, reintento con guía AC recalculada en la misma escala, acoplo y combinación de rieles que el caso; itl1/itl2=1000 como presupuesto numérico. Los barridos de protección mantienen extremos y paso de 1 mV; las recomendaciones de nodo se liberan al resolver el circuito.
- K1/J8 conserva definición relativa al centro nominal del S7. J2 conserva flancos y amplitudes S7; K4 conserva final de flanco a 11.02 µs y banda ±0.1 div. Conducción BAV199: polarización directa >0.4 V, no corriente capacitiva.
- K3: cuatro combinaciones de magnitud de riel 4.80/5.00 V, barridos iniciados en 0 y continuados con paso 1 mV a ambos extremos; J5 ±40 V en cinco escalas, E5b ±100 V en POS1/100, DC y AC. No incluye seno 100 Vpk ni ESD: S7b pide E5b en continua. Se guarda cada polaridad real en el nombre .meas. La señal del 4051 se comprueba en los ocho Y y Z, incluso la toma no seleccionada. La corriente OPA810 es del pin de entrada, no la corriente de carga de salida. Corrientes de U103 incluyen su red de protección, cota conservadora.
- C6 y C7 son barridos deterministas, no fracciones poblacionales de placas; se reporta la fracción de casos y se declara que no hay Monte Carlo de sobrecarga/recuperación. C1..C4/C8 se juzgan por escala, no sólo agregando placas. Las muestras de ruido son los primeros 100 casos de las mismas 500 placas. No se presenta 2000 realizaciones emparejadas como 2000 placas independientes.
- No se dispersan GBW, I_B, ganancia abierta, ruido intrínseco ni temperatura: el contrato S7b §2 no los exige, aunque la decisión permanente es más amplia. Ruido sólo AFE de 1 Hz a 3.15 MHz con AD8038_ltspice_ruido_hoja.sub; sin ruido, cuantización, jitter ni desajuste del ADC. SWI1 está declarado para transitorio por Nexperia; uso AC/DC conserva limitación histórica. OPA836 ESD es supuesto externo; BAV99HY Rohm representa BAV99 Nexperia. TVS genérica y absorción de rieles pendientes de placa.
- Contradicción: ±2 % de 4.90 implica 4.802..4.998, y dos rieles máximos suman 9.996 V en la fuente ideal, no 9.95 V. K3 exige extremos redondeados 4.80/5.00: suma de fuente 10.0 V, margen nulo en ese extremo; se informa tensión real tras resistencia/consumo.
- Consumo de macromodelo OPA810 ≈1.9 mA frente a 3.7 mA típico de hoja: reportar simulado no revisa G.3 ni certifica autonomía. Sin carga ficticia U103B. No se eligieron remedios ni se modificaron entregables previos, modelos, STATE, DECISIONS o chequeo_claude. No hay nueva evidencia física.

J2 cuadrada en 50 mV/div conserva 69 advertencias nativas de relajación automática de convergencia al arranque (t ≈1.16e−14 s), sin cambio explícito de tolerancias en el netlist. Sus medidas finales son válidas; se declara la advertencia numérica y se conserva el log.
