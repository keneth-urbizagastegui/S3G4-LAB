# S12 — frontal de tensión del DMM

8 oct 2026. Agente: Codex. Contrato: `PLAN_SIMULACION_S12.md`. LTspice 26.0.2, Python 3.12, numpy/scipy. Simulación local; no hardware ni descargas. No se modificaron S11.x, 01_diseno, models, STATE ni DECISIONS. La auditoría queda pendiente.

## Circuito y fuentes

Se usa la decisión DMM del 8 oct: seis 1.5 MΩ + 910 kΩ + 100 kΩ, OPA2192 A, 74HCT4051 y ganancia por escalera fija 91 kΩ/10 kΩ seleccionada en IN− por TMUX4053. La carga del bloque 5 es **supuesto**: 10 kΩ ∥ 10 pF a 1.25 V. No se certifican el driver, el ADC ni la lógica de OL.

El divisor suma **10.01 MΩ**. Relaciones calculadas: X1/Vin = 1.01/10.01 = 0.1008991 (÷9.91089); X2/Vin = 0.1/10.01 = 0.00999001 (÷100.1). Se calibran estas relaciones, sin sustituir piezas.

Compensación calculada, sin retocar valores: cada pareja (1.5+1.5) MΩ ×100 pF da τ=300 µs; 910 kΩ×330 pF da **300.3 µs**; 100 kΩ×3.0 nF da300 µs. El cero fijo del ajuste de firmware se fija en 1/(2π·300 µs)=530.516 Hz (efectivamente infinito en X0). Los 3.3 kΩ de amortiguación y las cargas reales introducen polos adicionales: se conservan en los decks.

Fuentes locales: estudio bloque2 (§0–§10 y decks), bloque1 HTML, decisiones 7/8 oct; `opa2192.pdf` SBOS620E pp8–9; `tmux4053.pdf` SCDS445E pp9–11; `C728673.pdf` Yageo RT V.16 pp5,6,8; biblioteca Nexperia `hc_tnomi.cir`; S11.4 y estudio `GDT_SEGUIMIENTO.md`/`gdt_seguimiento.py`, todos leídos sin editar.

## Validación previa del OPA2192

TI `OPAx192.LIB`, versión1.7 (26-08-2022), común a OPA192/2192/4192. Orden: **IN+ IN− VCC VEE OUT**. Los decks `S12/modelo_seguidor.cir` y `modelo_gbw.cir` fijan explícitamente25°C, ±4.9V, carga10kΩ∥10pF a1.25V.

| Comprobación | Modelo | Hoja | Lectura |
|---|---|---|---|
| Seguidor1V | 0.999998808V | seguidor estable | Orden y realimentación correctos |
| Modo común4.5V | 4.499998569V | (V−)−0.1 a(V+)+0.1V, p8 | Dentro del rango especificado |
| Ib en0V,25°C | 5.06075pA | 5pA típ/20pA máx, p8 | Coincide con típico |
| Ib en4V,25°C | 24.8492pA | máximo5nA en toda temperatura; el dato20pA usa las condiciones de tabla | No extrapolar20pA al cruce de entrada ni a toda temperatura |
| Cruce abierto de unidad, carga10k∥10p | 9.62247MHz (Q0,23°C) | GBW10MHz típico,p9 | −3.8%; el nominal del modelo es compatible, no garantía de mínimo |
| −3dB del seguidor | 16.7691MHz | GBW no es el−3dB cerrado | Se distingue del cruce abierto; no se sustituye por10MHz |

El barrido del frontal con OPA2188 solo se conserva como comparación C5/E4. No se usa como A en el resto. El modelo TI no representa la dispersión de silicio. La Ib máxima de5nA para−40…125°C impide usar20pA como garantía a18/28°C. El ruido y Vos cambian cerca del riel positivo (hoja p8).

## Método y límites

- E1: **200 placas virtuales por rango**, cuatro rangos sobre los mismos pasivos aleatorios; red completa en LTspice con macromodelo TI. R del divisor/escalera±0.1% uniformes; C0G±5% individuales; parásitas±30%; Ron±30%. El modelo TI no aleatoriza GBW, Cin ni Ib. El 4051 se representa por Ron y C de hoja en AC, porque Nexperia declara SWI1 solo para transitorio. El ajuste usa cero fijo, ganancia y polo libres, tres puntos100Hz/1kHz/20kHz; ruido gaussiano relativo0.05% y0.1%, evaluado en101 frecuencias40Hz…20kHz. Semillas en el ejecutor. «p95» es percentil de esta población supuesta; no certifica95% de producción.
- E2: doce barridos DC nominales, con fuga agregada en COM de1nA a23°C, que se duplica por10°C (**supuesto**). Comparación tras calibrar pendiente y cero a23°C. Presupuesto separado de10000 muestras de TC independientes±25ppm/°C. Reserva conservadora de deriva Vos SOIC0.5µV/°C y de Ib20pA; fuga del TMUX típica0.3nA, con la misma ley térmica supuesta. Estas reservas no son distribuciones garantizadas. El autocero en funcionamiento puede cancelar parte del Vos, por lo que se informa el presupuesto conservador.
- TMUX4053: modelo paramétrico, RTMUX60Ω típico y400Ω corner (±5V,25°C); el selector SW añade1Ω, de modo que la ruta total es61/401Ω. `ron60/ron400` en los nombres designa RTMUX. Capacitancia lumped10pF en IN−. No modela todas las capacidades entre terminales, la inyección ni el break-before-make interno. La fuga típica0.3nA se incluye en el presupuesto E2, no en las fuentes de corriente de los decks (GTLEAK=0). La hoja admite100nA máximos en su ensayo24V: no garantiza1nA.
- Transitorios: ocho SWI1 de Nexperia. En autocero se abre X3 en1ms y se ordena Xn en1.002ms, con flancos1µs; es una hipótesis explícita del control. Se mide desde1ms, incluyendo la demora. El pulso adicional5pC se aplica al abrir X3, no al cerrar Xn. Se usa trap/normal tras fallar los flancos1ns/20ns. `cshunt=1f` es regularización numérica, no pieza elegida. No se barre su valor: incertidumbre numérica restante.
- E4: lectura válida de tensión definida en A como |Vout|≤2.02V (200mV×10.1 o2V×1). Se identifica como engañosa una salida en ese intervalo cuando la entrada exige OL. La definición es supuesto de interfaz pendiente del bloque5; no valida la interpretación de todas las escalas de Ω ni la protección del driver.
- E5: retorno de lazo por inyección serie en IN−, −V(inv)/V(test), con circuito cerrado y punto DC conservado. El margen se extrae del RAW complejo. El control de la llave de ganancia es ideal (flancos1ns), distinto del supuesto NXP de autocero.
- E6: primero se repite la protección reducida **contractual S11.4 con GDT solo**, con divisor nuevo. Se adapta exclusivamente la exposición equivalente del OPA a6.4pF/1.6pF y1mA/canal según su hoja. Después `ejecutar_s12_e6_actual.py` repite con **GDT+MOV14D431K aprobado**, reutilizando el modelo del estudio local y τ de cebado1ns/100ns. Se conserva la contradicción entre contrato y cadena vigente. El reducido no simula transferencia ni daño.
- E7: `.noise`0.1Hz…100kHz y filtro sinc de integración rectangular100ms; se integra la **densidad al cuadrado**, no la `.meas` que integra densidad. También se informa √2 por restar un autocero independiente. El límite inferior0.1Hz y la independencia son supuestos; no se simulan ADC, interferencia de red ni deriva por debajo de0.1Hz.
- C3: capacitancia efectiva del común de ochoSWI1 ante un escalón10mV/100ns; Y del canal activo sigue a Z, los otros Y están aCOM. Se integra I(Vz), descontando su nivel DC. No es una extracción de capacitancias individuales ni prueba de la pieza real. Se añaden senos20kHz, amplitudes0.2/2Vpk, para THD2…9 y RMS.

No se montaron buffers ni se ensayó el retoque270pF/2.7nF: son variantes propuestas en C1/C4 del estudio que contradicen las piezas/topología fijas del contrato S12. Tampoco se garantiza fuga de placa o envejecimiento anual.

## Piezas del bloque2

| Cantidad | Pieza | Valor / referencia | Hoja o condición |
|---|---|---|---|
| 6 | Yageo RT1206BRD071M5L | 1.5MΩ,0.1%,25ppm, C728673 | RT1206:200V trabajo/400V sobrecarga,0.25W |
| 1 | Yageo RT1206BRD07910KL | 910kΩ,0.1%,25ppm,C870935 | Misma familia RT1206; referencia según estudio |
| 1 | Yageo RT1206BRD07100KL | 100kΩ,0.1%,25ppm,C728669 | Misma familia RT1206 |
| 3 | C0G | 100pF,2kV,C7393967 | Valor del bloque1; sin ficha local definitiva |
| 3 | amortiguación | 3.3kΩ | Referencia y rating pendientes |
| 1+1 | C0G | 330pF /3.0nF | Referencia/rating pendientes |
| 1 | Nexperia74HCT4051 | C87239 | SWI1 para transitorio; equivalente de hoja en AC |
| 1 canal | TI OPA2192 | A,C110074 | Otro canal pertenece al bloque4, no certificado aquí |
| 1 sección | TI TMUX4053 | C5377936 | Otras secciones fuera del alcance |
| 1+1 | escalera fija | 91kΩ /10kΩ,0.1%,25ppm | Referencias pendientes; ganancia10.1 |

R_PROT99kΩ, BAV199 y100Ω de X0/X1 son frontera del bloque1 y permanecen en los decks. El consumo aquí informado corresponde a A y a la carga supuesta; no incluye el segundo canal ni todas las llaves del bloque4.

## Resultados

**S12 no se cierra como conforme:** E2 falla en200mV; E3 falla en X1/X2; E5 falla en el corner; E6 falla con la cadena vigente y el cebado lento. `status=ok` en los CSV significa ejecución/lectura válidas, no cumplimiento eléctrico.

| # | Resultado | Estado y alcance |
|---|---|---|
| E1 | p95 conjunto4rangos: **0.20825%** con calibración0.05%; **0.27093%** con0.1% | Cumple el análisis AC pequeño y la población supuesta; no confirma el gran-señal de20/50V ante el hallazgo deE3 |
| E2 | p95 de ganancia0/176.1/115.6/136.0ppm por rango2V/200mV/20V/50V. A1nA: offset nominal SPICE máximo4.008/0.401/3.719/0.401cuentas para200mV/2V/20V/50V. Presupuesto conservador4.552/0.444/3.828/0.444 | **Falla200mV**; el resto cumple condicionalmente. Ib/fuga reales no garantizados por estas hipótesis |
| E3 | X0:22.50µs (200mV),20.29µs (2V). X1final2.79254V frente a2.01798V; X2final4.87857V frente a0.499500V | **FallaX1/X2:** no llegan a media cuenta en8ms; 7677/43834cuentas de error final. No aceptar0.477/0.163ms medidos respecto a la cola equivocada |
| E4 | OPA2192:0puntos engañosos; recuperación18.66µs×1/22.63µs×10.1. OPA2188:21.75/28.07µs, con su limitación3.4V en×1 | Cumple el modelo y umbral deOL definido, sujeto al bloque5 |
| E5 | PM×1:49.11° típico/**40.46° corner**; PM×10.1:64.96°/64.19°. Cambio de ganancia: máximo**11.45µs** a media cuenta de200mV | **Falla el margen>45°** en×1 conRTMUX400Ω (ruta401Ω). Transitorios cumplen |
| E6 | Régimen253Vrms:58.65V por1.5MΩ. GDT solo:177.86V máximo por pieza enESD. GDT+MOV:288.22V (τ1ns), **558.07V (τ100ns)** con+8kV; con±4kV lento ya llega412.03V | **Falla la sobrecarga400V** con cadena aprobada y corner lento; ratings de3.3kΩ/capacitores bajos siguen pendientes |
| E7 | Sin autocero independiente:0.01915cuenta rms (200mV) /0.003179(20V). Con resta independiente: **0.02708 /0.004495cuenta rms** | Cumple el modelo de ruido/integración indicado; ADC e interferencia quedan fuera |

E1 por rango, en200 unidades cada uno:

| Rango | Ruta/ganancia | p95 con0.05% | p95 con0.1% |
|---|---|---|---|
| 200mV | X0×10.1 | 0.11273% | 0.19313% |
| 2V | X0×1 | 0.09528% | 0.20343% |
| 20V | X1×1 | 0.19302% | 0.25676% |
| 50V | X2×1 | 0.17324% | 0.22530% |

### Fuga tolerable y deriva

Límites **a23°C**, para deriva de offset≤4cuentas entre18 y28°C, con la ley térmica y reservas de E2. La tolerancia se refiere a corriente **agregada deCOM**, no a la fuga garantizada de cada uno de ocho canales ni a una superficie dePCB concreta.

| Rango | Fuga máxima del presupuesto | Offset con1nA | Ganancia p95,±5°C |
|---|---|---|---|
| 200mV | **0.866nA** | 4.552cuentas | 176.1ppm |
| 2V | **9.657nA** | 0.444cuentas | 0ppm resistivo |
| 20V | **1.046nA** | 3.828cuentas | 115.6ppm |
| 50V | **9.657nA** | 0.444cuentas | 136.0ppm |

El dato de fuga del estudio≈0.7nA usaba3cuentas y temperatura25°C; aquí el contrato da4cuentas y calibración23°C. No son límites intercambiables. El máximo5nA deIb sobre toda temperatura no entra en esta tabla como garantía: hace falta medirIb/fuga en18…28°C y confirmar el comportamiento del autocero. En particular,20pA es un dato a25°C bajo las condiciones de tabla.

### C2, C3 y consumo

C2, con nueva calibración por variante: añadir−10/0/+10pF a la carga común del caminoX0 da caída20kHz −8.16/−12.58/−17.31%; el residuo de ese nominal se mantiene≈0.0342%. EnX1, −20/0/+20pF da −6.99/−11.94/−16.40%; residuo≈0.0943…0.0974%. **Limitación:** el barrido se aplica al nodo común, no al padX1 antes de100Ω; es sensibilidad a carga vista a través del mux y no un barrido geométrico dePCB. El error sin recalibrar es del orden de varios puntos porcentuales en los extremos.

C3, C efectiva del común extraída del SWI1: a−2/−1/0/+1/+2V = **0.8855/0.8878/0.8908/0.8946/0.9000pF**. La dependencia relativa es pequeña, pero el valor no reproduce los25pF usados desde hoja. La extracción comparte el movimiento deY/Z y el modelo SWI1 no incluye toda la pieza/encapsulado: **no sustituye la capacidad de hoja ni valida E3**. THD20kHz=0.000922% a0.2Vpk y0.01837% a2Vpk; RMS0.138443/1.384387V. La caída nativa≈−2.11% contrasta con≈−12.58% del equivalente de hoja. Es evidencia de que no se debe inferir la planitud real a partir del SWI1 solo.

Consumo de los rieles del banco, A con carga y mux:≈**10.26…10.30mW** en rutasX0 válidas,≈1.05mA equivalente sobre9.8V. Los11.41/13.27mW de X1/X2 corresponden a sus estados erróneos y no son nominales válidos. Hoja: A1mA típico/1.2mA máx a25°C; encapsulado dual≈2mA típico antes de cargas. TMUX4053 completo:18µA deVDD y6µA deVSS típicos a±5V (p9); ese reposo no está modelado por las llaves ideales. HCT4051 y segundo amplificador deben presupuestarse aparte. No es el consumo del DMM completo.

### E6 y piezas cargadas

La cadena vigente se ensayó con todos los estados de los74casos contractuales y dos tiempos de cebado (148casos). Peor1.5MΩ: +8kV,alimentado,±4.802V,GDC780V,τ100ns,tomaX0,relé abierto; **558.07V**,140% de400V. Con−8kV:557.47V. Con±4kV lento:410.72/412.03V; conτ1ns el máximo de toda la campaña es288.22V. La respuesta del GDT sigue siendo una hipótesis de modelo, no tolerancia de hoja.

En ese peor caso los tres3.3kΩ ven≈**1115.39V** cada uno, sin referencia de pulso confirmada. Los100pF ven máximo170.23V en toda la campaña, lejos de2kV nominales;330pF/3nF ven≈5.14/0.564V en el caso peor de resistencia (régimen253Vrms:5.44/0.598V). La familiaRT1206 garantiza sobrecarga de5s según el ensayo de su hoja, no una calificación IECESD: aun bajar de400V no certifica repetición de impulsos ni mantenimiento de0.1%.

### Contradicciones y pendientes

1. HTML bloque1 conserva3×3MΩ/900kΩ y una etiqueta630V; prevalecen decisión8oct/contratoS12. No se editó el HTML.
2. El contrato ordena reutilizarS11.4, pero su GDT solo difiere de la cadenaGDT+MOV aprobada posteriormente. Ambas quedan ensayadas y separadas; no se reemplaza el resultado vigente por el favorable del antiguo.
3. SWI1 ofrece capacitancia y colas no representativas de la respuesta del equivalente de hoja. La sobreexcursión del X0 no seleccionado cuandoVin=20/50V es un mecanismo **posible** del fallo deX1/X2; no se demostró causalidad ni se extrapola a todas las piezas reales. Hay que cualificar el modelo de mux completo y probar los canales no seleccionados con sobreexcursión.
4. ConfirmarRon, capacitancias y fase del TMUX en18…28°C; el corner garantizado falla aunque el nominal pasa. No se eligió remedio ni otra pieza.
5. Medir fugas agregadas,Ib ypatrón de calibración; confirmarOL/control deautocero y tolerancia del driver. Sin esas mediciones, ni E1/E2/E4/E7 son certificación de≥95% de fabricación.
6. Ratings de los3.3kΩ,330pF/3nF y respuesta real delGDT; no se descargaron fichas ni se cambiaron piezas.

## Ejecuciones y archivos

| Grupo | Casos válidos | Reutilizados | Tiempo de su ejecutor |
|---|---|---|---|
| Smoke principal | 10/10 | 0 | 163.504s |
| Campaña principal | **927/927** | 1 | **976.339s (16min16s)** |
| Smoke cadena vigente | 1/1 | 0 | 12.316s |
| Campaña cadena vigente | **148/148** | 1 | **268.307s (4min28s)** |

Total de campañas: **1075casos**,1073 lanzados en esas campañas y2 ya ejecutados/reutilizados. Los dos ejecutores de campaña se solaparon: la suma1244.646s (20min45s) no es tiempo mural. Smoke:11ejecuciones,175.820s sumados. Validaciones del modelo, preflights e intentos fallidos de desarrollo quedan fuera de esas cifras. Todos los casos usaron900s de límite; no hubo timeout en las campañas finales. Reanálisis927+10 sin relanzar LTspice para corregir E3/E5.

Archivos: `comun/dmm_bloque2.inc`, `ejecutar_s12.py`, `ejecutar_s12_e6_actual.py`, `S12/` (decks,RAW,logs,JSON por caso), `resultados/s12_campaign.csv`, `s12_smoke.csv`, `s12_e6_actual_campaign.csv`, `s12_e6_actual_smoke.csv`, `s12_dc_budget.csv`, JSON de tiempos y este acta. Diario: `ai-context/journal/2026-10-08-codex-s12.md`.

Repetir desde la raíz entrecomillada:

```powershell
Set-Location -LiteralPath 'C:\Users\Keneth\Desktop\S3G4 LAB'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12.py' --smoke
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12.py' --resume
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12_e6_actual.py' --smoke
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12_e6_actual.py' --resume
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12.py' --reanalyze
```

`S3G4_MODELS` y `S3G4_LTSPICE` aceptan rutas locales alternas. `--resume` exige el hash de código/deck/include/modelos y solo reutiliza ejecuciones válidas. El reanálisis comprueba deck idéntico y conserva la firma antigua; tras cambiar el algoritmo el siguiente resume repetirá los casos cuya firma haya cambiado, deliberadamente. Los archivos S11.x permanecen como dependencias de lectura.
