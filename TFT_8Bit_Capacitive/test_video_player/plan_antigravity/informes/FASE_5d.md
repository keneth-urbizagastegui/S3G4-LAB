# Fase 5d — Video girado en origen: EL CORTE DIAGONAL DESAPARECE

**Resultado:** objetivo principal CONSEGUIDO; queda una iteración para 3 fallos.
Informe escrito por el auditor: el primer intento murió por cuota y el segundo se detuvo por la microSD.

## Verificación visual de Keneth (16/09/2026)
- **Pantalla completa con video real: «no se ve corte y el video está derecho».** ✔
- **Modo C (rojo/azul):** la frontera ya **no es diagonal**; es **recta** y se desplaza («como un barrido
  horizontal»). Encaja con escribir en paralelo al barrido. Que se desplace probablemente se debe a que
  el patrón alterna a 30 Hz sin esperar TE (a comprobar, fallo D3).
- **Vista pequeña (Studio): el video se ve girado** (fallo D1).

## Medido (`F5d_run3.csv`, capturado con `perf_capture --no-reset` tras cortar la alimentación)
| Criterio | Umbral | Medido | |
|---|---|---|---|
| pres_fps oculto | ≥ 28,5 | **29,02** | ✔ |
| pres_fps con OSD | ≥ 28,0 | **29,73** | ✔ |
| **drop oculto** | ≤ 1 % por pista y global | **2,46 % global** (pista 0: 7,28 %; pista 3: 2,04 %) | **✘** |
| TE / te_timeout | presente, ±2 Hz / ≤ 1 % | 44,0–45,0 Hz / OK | ✔ |
| present_path / view / hud | direct / coherentes | OK | ✔ |
| \|drift\| | < 100 ms | 71 ms | ✔ |
| TAP · STRESS | 0→1 · mismatch 0 | OK · OK | ✔ |
| reader_rd_avg · q_wait_max | < 15 ms | OK | ✔ |
| heap_int | ≥ 30 000 B | 56 275 B | ✔ |
- `rot=90`, `madctl=0x48` en todos los registros. Decodificación por fotograma **15,9 ms** (sin coste de
  giro); envío **20,8 ms** (F5a: 20,2 ms), con 1,6 ms de margen frente al periodo de 22,42 ms.

## Fallos que quedan (iteración 2)
- **D1. Vista Studio girada.** El decodificador de la vista pequeña escala a 240×160 con
  `rotate = JPEG_ROTATE_0D` (`avi_player.c` ~l.262-264), sin tener en cuenta que el fichero es 320×480.
- **D2. Descartes 2,46 %.** El envío subió 0,6 ms y el margen es estrecho; la pista 0 (ariana, 7,28 %)
  concentra el problema.
- **D3. El modo C de `tear_diag` probablemente no espera TE**, así que no representa el camino del video.
- **D4. Regresión: tras flashear o reiniciar por RTS, la microSD queda colgada (0x107)** y solo vuelve
  cortando la alimentación. **Con el firmware de F5a (d404c22) no pasaba**: el auditor flasheó dos veces
  sin problema. En F5d se añadió `sdcard_spi_pre_sync()` (100 pulsos por GPIO antes del montaje), que es
  el primer sospechoso.
- **Contorno aplicado por el auditor:** `perf_capture.py --no-reset`, que abre el puerto sin tocar
  RTS/DTR (el script reiniciaba la placa al empezar y eso colgaba la tarjeta).

## Estado del banco
Puerto **COM16** (reenumera entre COM16 y COM17 al reconectar). Firmware normal con TE y diagnóstico en
OFF. MicroSD solo con los 4 videos girados.
