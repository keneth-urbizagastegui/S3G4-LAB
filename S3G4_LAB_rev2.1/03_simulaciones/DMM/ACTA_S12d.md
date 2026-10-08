# S12d — DMM bloque 2 con OPA4192

8 oct 2026. Codex. Contrato: `PLAN_SIMULACION_S12d.md`, con S12c/S12b/S12 vigentes salvo sus cambios explícitos. LTspice local, Python/numpy/scipy. Sin descargas ni hardware. **234/234 estados válidos finales. E3/E5/E8 cumplen; E2 marginal, sin cierre incondicional con margen de fabricación.** Auditoría independiente pendiente. Cierre documental17:10 -05:00.

## Circuito y fuentes

Un OPA4192 a ±4.9 V: seguidor X0, seguidor X2, amplificador A y cuarta sección como seguidor de COM. Cuatro instancias del modelo TI monocanal `OPA2192/OPAx192.LIB`, común a OPA192/2192/4192, orden IN+ IN− VCC VEE OUT. No representa acoplo interno de encapsulado ni dispersión entre canales.

Rx0 sustituye los 100 Ω por 10 kΩ; Rx2 añade 10 kΩ ante el buffer de la toma ÷100. X0→buffer→Y0; X2→buffer→Y2; X1 y X3 a COM. Divisor 6×1.5 MΩ+910 kΩ+100 kΩ =10.01 MΩ; relación X2/Vin=100k/10.01M=0.00999001. La ganancia llamada ×10 es ×10.1, por 91 kΩ/10 kΩ y TMUX4053. Carga del bloque 5 supuesta: 10 kΩ∥10 pF a 1.25 V.

Compensación conservada: 3×(100 pF C0G 2 kV +3.3 kΩ antipulso), 330 pF C0G ≥100 V sobre 910 kΩ y 3 nF C0G ≥25 V sobre 100 kΩ. Constantes: 300/300.3/300 µs; cero fijo 530.516 Hz. No se retocan piezas ni valores fuera del contrato.

Fuentes leídas: AGENTS, START y STATE (solo lectura), planes S12d/S12c/S12b/S12 y documentos encadenados; actas y auditorías S12/S12b/S12c; ESTUDIO_BLOQUE2 completo y sus nueve decks; decisiones DMM 7/8 oct, incluida «OPA4192 con buffer en X2»; HTML de bloque 1; ENCARGO_CODEX_S11_1; LEEME de modelos; ejecutores/includes S12c/S12b/S12 y S11.4, y generador local GDT+MOV. Las referencias de hoja son las locales citadas por esas auditorías: OPAx192 SBOS620E pp.6/8–11/26, Nexperia 74HC_HCT4051 pp.9–12, TMUX4053 SCDS445E pp.10–11 y Yageo RT1206. MCP s3g4-context/context-mode no expuestos: respaldo `context.mjs search` y lecturas locales. Se usan pautas de SPICE, con el contrato específico como método rector.

## Método y límites

- Solo E2/E3/E5/E8, 234 estados: E2=24, E3=56, E5=4, E8=150. Se hereda metodología de S12c mediante carga en memoria y redirección exclusiva a S12d. 10 trabajadores, límite 900 s/caso; grupos completos E2→E3→E5→E8. `status=ok` significa ejecución válida, no conformidad.
- El campo `n_population=200` del JSON es el argumento `--n` heredado del ejecutor; **no se ejecutan 200 placas SPICE en S12d**. `cases()` usa la confirmación corta fija. Las10000 muestras de TC son cálculo de presupuesto, no lanzamientos adicionales deLTspice.
- E2: 4 rangos×3 temperaturas (18/23/28 °C)×2 signos de fuga. 21 plateaus de 20 ms, media de los últimos 2 ms, ajuste pendiente/cero y calibración a 23 °C por signo. Fuga ON **agregada** ±0.4 µA a 25 °C inyectada en COM del mux, que la ruta seleccionada lleva a la salida del buffer a través de Ron. No se multiplica por ocho ni se cuenta otra vez en Yn. La ley heredada ×2/10 °C es un supuesto térmico: equivale a 0.348 µA a 23 °C, no a un máximo garantizado interpolado de catálogo. ±0.6 nA en cada entrada de buffer a 23 °C, con la misma ley. GTLEAK=0 en SPICE; fuga típica TMUX 0.3 nA, Ib 20 pA, deriva SOIC 0.5 µV/°C por canal y Rout≤1 Ω se reservan aparte en el presupuesto conservador. Los 20 pA de hoja a 25 °C no son garantía de todo 18…28 °C. Ganancia: 10000 TC independientes uniformes ±25 ppm/°C; no se aleatoriza silicio.
- E3 DC: 48 casos, 4 rangos y 0/±FS/±20/±50 V con duplicados eliminados, carga 0/5 pC. Rampa de 20 µs; 20 ms antes de autocero; X3 abre a 21 ms y la señal cierra a 21.002 ms. Evaluación a 21.1 ms en X0 y 24 ms en X2. Error absoluto respecto al nominal solo dentro del rango; se informa también error de asiento respecto a la cola. Paso máximo 1 µs con breakpoints 100 ns en la conmutación. Los casos fuera de escala califican rieles/pinza, no precisión de medida.
- E3 AC: 8 casos, todas las selecciones a 50 Vrms (70.71 Vpk), 40 Hz/20 kHz. Mismo evento X3→señal, preacondicionamiento y espera. Solo la selección 50 V/X2×1 puede calificar precisión. Se compara un ciclo tras 3 ms con un ciclo de la cola a idéntica fase, por interpolación RAW: error de adquisición con transferencia periódica calibrada, no error sin corregir de ganancia/fase. Los otros rangos están sobrecargados. No es nueva campaña E1 ni barrido continuo de frecuencia/amplitud.
- E3/E8 con TI completo: se guardan las corrientes de los cuatro interruptores internos ESD de cada buffer; conducción IN+ separada de IN− y desplazamiento capacitivo. La condición continua ≤50 µA se aplica a IN+ después del arranque (t>1 ms DC; tras ≥2 ciclos AC). El máximo de arranque queda informado aparte. La tolerancia del mux es riel+50 mV; no se impone modo común al buffer no seleccionado que está sujeto por su protección.
- E5: cuatro lazos A, ×1/×10.1 y Ron TMUX 60/400 Ω (+1 Ω del selector ideal). CD(ON)=10 pF repartida 5 pF/5 pF. Retorno −V(inv)/V(test); fase interpolada en log|T| y logf en el primer cruce unitario. Criterio ≥40°. No se añade Cf ni se repiten conmutaciones heredadas.
- E8: 148 estados heredados de protección S11.4 con cadena **vigente GDT+14D431K**, esquinas GDC420/780 V, cebado 1/100 ns, ESD ±4/±8 kV, encendido/apagado, rieles y tomas heredadas, más dos rampas ±50 V con TI completo. X1 está a COM incluso en los estados cuyo nombre histórico dice tap1. Modelo reducido PINOPA Vf=0.5 V/Ron=1 Ω con Cin6.4 pF/Cdiff1.6 pF y transferencia TI aislada de los rieles; se miden directamente los diodos, no toda la corriente de entrada. Es una IV supuesta, no daño de silicio. Se incorporan buffer X2 y canal libre al presupuesto de carga reducido (6.116 mA, que conserva además B/protección fuera del bloque 2; no equivale a consumo completo medido). Modelo ESD 150 pF/330 Ω también en «aire 8 kV»: no modela arco IEC ni certifica cumplimiento normativo.
- Reanudación exige hash de fuentes, include/modelos y deck idéntico. Nombres cortos por hash; cada `.meas` lleva identidad completa del caso, borne/modo/relé/riel/estímulo/GDT/tiempos cuando corresponde, OPA4192, Rx0/Rx2=10 kΩ y X1=COM. Las corridas previas son solo dependencias de lectura.

## Contradicciones conservadas

1. DECISIONS cita ±100 nA del 4051; la auditoría y S12d distinguen OFF ±0.1 µA de **ON ±0.4 µA** a 25 °C. Se aplica ON de S12d. La ley térmica y la extrapolación entre temperaturas no son garantía de hoja.
2. DECISIONS dice 3 ms en X2 y entre paréntesis 1.5 ms con buffer. S12d exige 3 ms; se aplica 3 ms, sin editar firmware.
3. El plan llama 74HC4051 al mux y las decisiones seleccionaron **74HCT4051** por GPIO3.3 V. Se conserva HCT en piezas y el SWI1 HC transitorio con controles 0/4.9 V, como en S12c; no se certifica el interfaz GPIO real mediante ese modelo.
4. HTML de bloque 1 conserva 3×3 MΩ/900 kΩ, toma ÷10, 100 Ω y una etiqueta 630 V. Prevalecen los contratos/decisiones posteriores; no se edita el HTML. GDT+MOV prevalece sobre GDT solo de S11.4.
5. S12d dice que E1/E4/E6/E7 pasaron y no cambian. Se heredan sin repetir, pero el acta S12c dejó **E6 condicionado a MPN/curvas de impulso**. El buffer nuevo cambia la carga de X2 y 10 kΩ cambia la de X0: la herencia ordenada no constituye una recualificación de AC/ruido del circuito nuevo.

## Piezas finales del bloque 2

| Cantidad | Pieza / valor | Referencia y condición |
|---|---|---|
|6|Yageo RT1206BRD071M5L, 1.5 MΩ|C728673, 0.1%, 25 ppm/°C; 200 V/0.25 W; curva de impulso pendiente|
|1|Yageo RT1206BRD07910KL, 910 kΩ|C870935; misma familia/tolerancia/TC|
|1|Yageo RT1206BRD07100KL, 100 kΩ|C728669; misma familia/tolerancia/TC|
|3|CCTC TCC1206COG101J202FT, 100 pF C0G, 2 kV|C7393967; ficha definitiva pendiente|
|3|3.3 kΩ antipulso|≥1.5 kV, ≥25 µJ, ΔR≤1%; MPN/curva pendientes|
|1|330 pF C0G ≥100 V|MPN pendiente|
|1|3 nF C0G ≥25 V|MPN pendiente; no se sustituye por otro valor|
|2|10 kΩ, serie de entrada de buffers X0/X2|MPN pendiente; X0 sustituye 100 Ω, X2 nueva|
|1|Nexperia 74HCT4051|C87239; Y0/Y2 desde buffers, Y1/Y3 a COM|
|1 cuádruple|TI OPA4192|X0, X2, A y seguidor COM; MPN de encapsulado/compra pendiente, no reutilizar C110074 del dual|
|1 sección|TI TMUX4053|C5377936; las otras dos secciones del bloque 4 fuera de alcance|
|1+1|91 kΩ/10 kΩ|0.1%, 25 ppm/°C; MPN pendientes; ganancia real 10.1|

Frontera del bloque 1 conservada: R_PROT 3×33 kΩ, BAV199 en X0 y cadena GDT SMD4532-600NF+14D431K. La sujeción y la serie de X1 permanecen eliminadas. La carga del bloque 5 es supuesto de prueba, no pieza final seleccionada.

## Resultados y cierre

Campaña terminada: E2=24/24, E3=56/56, E5=4/4 y E8=150/150 válidos. Los resultados nominales y el presupuesto se mantienen separados: no se declara fabricación conforme a partir del macromodelo.

| Ensayo | Resultado | Dictamen y procedencia |
|---|---|---|
|E1|S12c: p95 conjunto 0.151% /0.251% con ruido de calibración 0.05% /0.1%; gran señal 50 Vrms, residuo nominal 0.033%|Herencia contractual, **no repetido** en S12d; no recualifica la carga nueva|
|E2|SPICE ≈3.9 cuentas máximo; presupuesto conservador ≈4.4 en 200 mV/20 V; ganancia p95 máxima 235 ppm <500|Nominal cumple ≤4; presupuesto no cumple en dos rangos. **Marginal de criterio/presupuesto**, sin margen de fabricación demostrado|
|E3|DC ≤0.42 cuentas tras espera; AC 50 V ≤0.13 cuentas respecto a cola periódica; mux ≤4.900 V frente a4.950 V; pinza continua ≤40.1 µA frente a50 µA|Cumple los 56 casos modelados. Precisión solo dentro del rango; AC de los otros rangos es sobrecarga|
|E4|S12c: 0 puntos válidos engañosos; recuperación OPA2192 ≤15.52 µs|Herencia contractual, **no repetido**; OL/driver dependen del bloque5|
|E5|PM mínimo43.6°; ×1 típica49.0°; ×10.1:64.5°/64.1° paraRon60/400Ω|Cumple ≥40° en los cuatro lazos; transitorios de ganancia heredados de S12c|
|E6|S12c: red253Vrms, cada1.5M≤53.62V; ESD8kV, RT≤556.54V/40.77nJ y3.3k≤1112.32V/2.321µJ|Herencia contractual, **no repetido**; régimen cumple. MPN/curvas/ΔR de impulso pendientes: no aprobación de fabricación|
|E7|S12c: ruido con autocero0.03595/0.02710 cuentas en200mV/20V,100ms|Herencia contractual, **no repetido**; no incluye ADC ni interferencia|
|E8|Pinza máxima0.461mA; ±50V0.0239mA; red0.0334mA;4kV0.427mA;8kV0.461mA|Cumple≤5mA en150estados; conducción de pinza, no desplazamiento capacitivo|

### E2 — fuga tolerable y clasificación del resultado marginal

La auditoría S12c estimaba ≈2 cuentas tras añadir buffer X2. Al aplicar **también los10 kΩ reales** de S12d,0.6nA ante ambos buffers, el máximo ON de hoja y las reservas conservadoras, aparece un presupuesto de ≈4.4 cuentas en ambos rangos sensibles. No se modifica el circuito para esconderlo.

|Rango|Ganancia TC p95,ppm|Offset nominal SPICE,cuentas|Offset conservador,cuentas|Fuga externa máxima por entrada a23°C,nA|
|---|---:|---:|---:|---:|
|200mV|176|3.92|4.44|0.504|
|2V|0|0.392|0.43|8.50|
|20V|235|3.92|4.44|0.503|
|50V|136|0.392|0.43|8.49|

Manda **≈0.50nA por entrada de buffer a23°C**, con Ib reservado aparte, ley térmica×2/10°C, ON0.4µA a25°C y demás supuestos indicados. No es límite de fuga del mux ni garantía de hoja. Si0.6nA se interpreta como total que ya contiene Ib, se evita su doble reserva, pero el presupuesto sigue por encima de4cuentas: no se resuelve la conclusión mediante esa convención.

En200mV el presupuesto se descompone en2.71cuentas de fuga de entrada,1.02 del ON del mux,0.50 deVos,0.09 deIb y0.11 delTMUX.20V es prácticamente igual, porque la cuenta de1mV en el borne se convierte en9.99µV enX2. Al pasar de100Ω a10kΩ sube la impedancia de fuente de99.1kΩ a109kΩ enX0;X2 pasa de≈99.0kΩ a≈109.0kΩ. La fuga del mux queda desacoplada de esas impedancias, pero ve≈71Ω y aún consume≈1cuenta en la deriva supuesta.

**Clase principal: criterio/presupuesto.** La suma lineal de máximos y la ley térmica elegida producen el exceso; el nominal SPICE queda apenas bajo4. Eso no prueba un fallo físico a18/28°C ni acredita margen real. La fuga de entrada sobre109kΩ sí es un mecanismo físico. El modelo usa derivas típicas y no aleatoriza silicio; una confirmación nominal cerca del límite no demuestra≥95% de placas. No se persiguen decimales ni se solicita cambiar piezas.

### E8 — detalle y peor estado

|Estímulo|Casos|Pinza máxima,mA|
|---|---:|---:|
|±50V,TI completo|2|0.0239|
|±4kV,contacto|72|0.427|
|±8kV,etiquetado aire|72|0.461|
|230/253Vrms|4|0.0334|

Peor estado: `e8_4425993663b4fa46050b`, +8kV, **apagado**, diodo de cuerpo presente, riel nominal0.98, relé abierto, selecciónX0, GDC780V yτ100ns. La pinza dominante es la de **bufferX2** (0.461mA); X0 da0.0346mA en ese caso. Es≈9.2% del criterio5mA y≈4.6% del absoluto10mA. Los canales apagados reciben el impulso con los rieles sin alimentación: no se extrapola al silicio real más allá de la IV reducida declarada.

### Ejecución, trazabilidad e integridad

- Smoke definitivo:7/7 válidos,96.808s, inicio16:40:29 -05:00. Campaña inicial:234/234,1238.672s (**20min38.7s**), inicio16:42:17 -05:00, siete reutilizados del smoke y227 lanzamientos nuevos.
- Revisión final encontró ocho nombres`.meas` de AC heredados del constructor DC (`kind=zero`). Se corrigió solo el prefijo y se repitieron esos ocho casos, con prueba automática de circuito idéntico al neutralizar exclusivamente el nombre de la medida:8/8 válidos,239.510s (**3min59.5s**). Los226 decks idénticos se re-firmaron sin relanzar, conservando historial de firma. Datos iniciales conservados en`s12d_campaign_inicial.csv/json` y`s12d_smoke_inicial.csv`.
- Tiempo de campaña más corrección:1478.182s (**24min38.2s**); con smoke:1574.991s (**26min15.0s**). Es suma de fases secuenciales medidas, excluye preparación y redacción. Final:234estados,234válidos,242lanzamientos desde el smoke definitivo (7+227+8), cero timeouts.
- Preparación separada:dos smokes preliminares,7casos cada uno,74.259s y99.755s; primero6válidos/1error de generador, segundo7válidos. Con ellos:256lanzamientos totales y1749.005s (**29min09.0s**) de fases medidas. El build con error de cargador no lanzó LTspice. No se mezclan errores de desarrollo con el dictamen eléctrico final.
- Verificación final con`analizar_s12d.py`, código0:234/234 decks exactos,234/234 firmas actuales y234/234 prefijos`.meas` con estado real. El resumen conserva métricas nominales, presupuestos y tiempos separados; el CSV final contiene las fichas actuales, no la cronología de reutilización (para ella están los archivos iniciales y JSON de tiempos).
- Integridad:18286 archivos protegidos con SHA256 agregado idéntico al inicial`9645fd7ea830a00c9186f3d923924b4f998e57b5275c75ae948ce549b2a0fada`. Se excluyen artefactos nuevos S12d, su include autorizado y RAW/log/net/cachés de simulación de la selección. S11.x/S12/S12b/S12c,01_diseno,modelos,STATE yDECISIONS quedan intactos. Evidencia:`s12d_protegidos.json`.

```powershell
Set-Location -LiteralPath 'C:\Users\Keneth\Desktop\S3G4 LAB'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12d.py' --smoke --workers 10
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12d.py' --resume --workers 10
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/analizar_s12d.py'
```

`--collect` conserva resultados únicamente con prueba de deck idéntico y reejecuta los cambios de nombre`.meas`; está documentado para auditoría de esta reparación. Se mantienen`S3G4_MODELS`/`S3G4_LTSPICE` y900s por caso. Artefactos:`comun/dmm_bloque2d.inc`,`ejecutar_s12d.py`,`analizar_s12d.py`,`S12d/` y`resultados/s12d_*`; diario propio`ai-context/journal/2026-10-08-codex-s12d.md`.

### Dudas y alcance del cierre

1. **E2:** nominal3.9cuentas, presupuesto4.4; el límite externo conservador≈0.50nA es inferior a0.6nA del contrato. Es un resultado marginal clasificado, no una decisión nueva ni un cambio de piezas. No queda demostrado «que funcione con margen» en≥95% de fabricación.
2. Ley térmica del ON, Ib/Vos reales18…28°C, impedancia de salida/Ron y acoplo interno delOPA4192 durante saturación/inyección. El modelo monocanal no puede cerrar esos puntos.
3. MPN delOPA4192 y de10kΩ/91kΩ/10kΩ,330pF/3nF y3.3kΩ; curvas de impulso deRT1206 yRc, yΔR medido. No se inventan referencias, ratings ni compras.
4. IV real de las pinzas, cebado delGDT y arco de ESD aire; ensayos físicos deESD/red y offset conX0 forzado cuando exista placa. Ninguna simulación certificaIEC.
5. E1/E4/E6/E7 son evidencia heredada por mandato, con sus límites; driver/ADC/OL, firmware real yconsumo completo fuera del alcance. Auditoría deClaude pendiente.

**Encargo S12d ejecutado y documentado. E3/E5/E8 confirmados en el modelo; E2 marginal impide declarar un cierre incondicional con margen.** No se actualizanSTATE/DECISIONS por prohibición expresa del usuario.
