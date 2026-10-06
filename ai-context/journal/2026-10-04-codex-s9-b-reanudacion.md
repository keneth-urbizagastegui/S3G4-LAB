# Reanudación S9-B — Codex, 4 octubre 2026

Inicio de recuperación: aproximadamente 20:37 −05:00 (America/Lima). Se leen START/STATE, diario S9 hasta 18:06, ENCARGO_CODEX_S9_B, bloque S9_B_CODEX y motor del banco. MCP s3g4-context disponible; búsquedas timeline/source S3G4 y análisis por context-mode. No se descarga nada ni se simula/modifica A.

## Cambio autorizado y evidencia

- Usuario ordena completar campaña B con `ejecutar_s9_b.py --resume` y repetir solamente sus cuatro cohortes MC OP con fuentes LM6172 desplazadas −2.986 mV. Modelo original ya contiene +2.986006 mV (K0). La distribución anterior llega aproximadamente a +5.986 mV y no representa ±3 mV total de SNOS792E p.7.
- Reanudación iniciada con 1870/2000 OP originales reutilizadas, 130 pendientes en 5 V/div. AC y ruido completamente reutilizados. Consola nueva: TEMP/s9b_campaign_console_resume_20261004b.log. No había runner de campaña ni LTspice de simulación vivos al iniciar (sólo servidores MCP).
- C8 vigente ≤2 µs según instrucción actual y DECISIONS del 4 oct; no se cambia el umbral histórico de A.
- Nuevo `ejecutar_s9_b_op_corregido.py`: trabajo separado `S9/B_hoja/op_corregido`, seis OP independientes por placa, 500 placas × cuatro escalas; sólo VOA/VOB/VOFA/VOFB cambian −2.986 mV. Semilla, pasivos, rieles, otras fuentes y macromodelo intactos. Lock de modelo/corrección para --resume.
- Nuevo auditor `verificar_s9_b_op_corregido.py`: contrasta las seis OP de cada placa con los decks originales, restaurando las cuatro fuentes para comparar el resto byte a byte (salvo ruta .loadbias). El generador de informe incorporará las dos versiones y la inspección de A.
- Inspección AD8038 sin simular: `Simulation_LTSpice/models/AD8039/AD8038_ltspice.sub` tiene B1/B2 con funciones idénticas y sentidos opuestos; no contiene fuente fija VOS. Offset diferencial nominal algebraico 0 mV con alimentación simétrica, sin la misma doble suma de casi +3 mV. No se mide de nuevo el error por rieles asimétricos/modo común ni el de otros amplificadores.

## Pruebas y pendientes iniciales

Sintaxis AST de los dos scripts nuevos y el informe: correcta. Auditoría completa y medidas corregidas aún pendientes; no se infiere C9 de la corrección. Pendientes: cierre OP original, K6/K2/K8, smoke definitivo, 2000 casos OP corregidos, auditorías, acta/respuesta final, STATE y sync. No se elige variante ni remedio.

## Corrección de polaridad — antes de lanzar las OP corregidas

La orientación real de las fuentes es `VOSA IPA IPAR {VOA}`, `VOSB IPB IPBR {VOB}` y `VOS IP IPR {VOS}` en SK_S9. Así, V(IN+ del modelo)=V(nodo externo)−fuente. K0 conecta IN+=0 y OUT a IN− y mide OUT=+2.986006 mV: el error equivalente de salida nativo es positivo. Restar 2.986 mV al parámetro de esas fuentes **aumentaría**, en vez de cancelar, ese error. Se informa al usuario en comentario y se corrige el signo del parámetro: fuentes SPICE +2.986 mV, que producen desplazamiento efectivo del amplificador −2.986 mV. Total efectivo = +2.986006−(draw+2.986) mV ≈−draw, uniforme ±3 mV (residual 6 nV). Es el objetivo contractual del usuario; no se ejecutan cohortes adicionales con el signo que duplica el sesgo. Esta conversión de signo se documentará explícitamente en acta/respuesta. No se cambia topología ni modelo.

## 21:12 −05:00 — OP original cerrada; K6 en curso

OP originales: 500/500 en cada escala, ganancia y centrado cumplen en todas. C9: 267/500 (53.4 %) a 5 mV/div y 0.5 V/div; 287/500 (57.4 %) a 50 mV/div y 5 V/div. Extremos mínimos de posición positiva 3.671130/3.807424/3.671094/3.807420 div; negativos 4.904176/4.902146/4.904179/4.902147 div. Evidencia: checkpoint y CSV/JSON individuales de S9/B_hoja/campaign.

K6 lleva 46/72 barridos nativos, sin errores de ejecución, pero aún no se cierra el criterio eléctrico. `finalizar_s9_b.py --wait-pid 6756` espera al runner original y después ejecutará secuencialmente auditoría, smoke B nuevo, comparación contra baseline, OP corregidas, auditoría corregida e informe. Consola: TEMP/s9b_cierre_pipeline.log; diez trabajadores simultáneos como máximo.

`verificar_cierre_s9_b.py --snapshot` terminó: 54035 huellas de archivos A y acta fuera de B. Base en resultados/s9b_integridad_base.json; la tabla de calibración B se excluye explícitamente por ser entregable de B. Historial original conserva 248 intentos OP nativos fallidos por PermissionError «El medio está protegido contra escritura»; los casos finales OP fueron recuperados. No se confunden esas incidencias E/S con fallos eléctricos.
