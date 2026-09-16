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

---

## Iteración 2 (16/09/2026)

### 1. Resolución y demostración de D4 (Regresión MicroSD en reinicios RTS)
- **Causa raíz:** La función `sdcard_spi_pre_sync()` añadida en it1 reconfiguraba la matriz GPIO de los pines del bus SPI (CS:21, CLK:13, MOSI:11) como pines GPIO de propósito general e inyectaba 100 pulsos manuales lentos por software antes de `spi_bus_initialize()`. Esto alteraba el estado del periférico SPI nativo de ESP-IDF y dejaba la tarjeta en un estado no reconocido durante reinicios por señal RTS sin ciclo de alimentación.
- **Corrección:** Se eliminó `sdcard_spi_pre_sync()` de `main/sdcard_spi.c`, restaurando exactamente el código de inicialización de F5a (`d404c22`).
- **Prueba empírica de validación (5 reinicios seguidos por RTS sin tocar el cable USB):**
  - **Reinicio 1/5:** `SD_FREQ_TEST,freq_khz=20000,passed=10/10` | Tarjeta: `SD32G (29664 MB)` ✔
  - **Reinicio 2/5:** `SD_FREQ_TEST,freq_khz=20000,passed=10/10` | Tarjeta: `SD32G (29664 MB)` ✔
  - **Reinicio 3/5:** `SD_FREQ_TEST,freq_khz=20000,passed=10/10` | Tarjeta: `SD32G (29664 MB)` ✔
  - **Reinicio 4/5:** `SD_FREQ_TEST,freq_khz=20000,passed=10/10` | Tarjeta: `SD32G (29664 MB)` ✔
  - **Reinicio 5/5:** `SD_FREQ_TEST,freq_khz=20000,passed=10/10` | Tarjeta: `SD32G (29664 MB)` ✔
  - **Resultado:** 100% de éxito en los 5 reinicios consecutivos, eliminando la necesidad de desconectar el cable USB.

### 2. Resolución de D1 (Vista pequeña Studio girada)
- **Causa raíz:** `s_dec_studio` estaba configurado estáticamente con `scale.width=240, scale.height=160` y `rotate=JPEG_ROTATE_0D`, asumiendo entrada horizontal de 480x320.
- **Corrección:** Se implementó `ensure_studio_decoder(src_w, src_h)` en `main/avi_player.c`, llamado dinámicamente al abrir cada archivo AVI. Para videos girados en origen ($320 \times 480$), se configura con:
  - `scale.width = 160`, `scale.height = 240` (downscaling exacto 2:1 por SIMD).
  - `rotate = JPEG_ROTATE_270D` (rotación horaria de 270°, equivalente a 90° antihorario, que deshace exactamente la rotación `transpose=1` de ffmpeg).
  - **Salida generada:** $240 \times 160$ píxeles RGB565 Little Endian, orientada verticalmente derecha.

### 3. Resolución de D3 (Modo C de `tear_diag` sincronizado con TE)
- **Causa raíz:** El modo C ejecutaba un retardo de preparación y llenado de búfer por software *después* de despertar de TE, y dormía con `vTaskDelay(33)`, desfasándose de los ciclos de barrido del panel (22.42 ms a 44.6 Hz).
- **Corrección en `main/player.c`:**
  1. Relleno previo de `s_diag_c_buf` con el color antes de esperar TE.
  2. Adquisición de `lcd_bus_lock()` previa.
  3. Espera de flanco TE (`lcd_bus_wait_te`).
  4. Envío inmediato de la primera franja por DMA en el milisegundo cero del V-blank.
  5. Cadencia ajustada para no desfasar la fase del panel.

### 4. Diagnóstico detallado de D2 (Descartes de fotogramas)
- **Desglose temporal medido por fotograma (`F5d_run4.csv`):**
  - Decodificación SIMD (`dec_f_avg`): 13.0 ms – 19.2 ms (media global: 16.2 ms).
  - Envío DMA por franjas (`strip_ms_avg`): 0.68 ms – 0.76 ms por franja $\times 30 = 20.4$ ms – $22.8$ ms.
  - Espera de TE (`te_wait_ms_avg`): 7.7 ms – 19.4 ms.
  - Lectura MicroSD (`reader_rd_avg`): 7.2 ms – 12.0 ms (media: 8.5 ms).
- **Causa de la concentración de descartes en Pista 0 (`ariana.avi`, 6.92%):**
  Entre los segundos 6 y 14 de `ariana.avi`, la alta entropía y densidad visual eleva la decodificación SIMD a 19.2 ms y el blit a 22.8 ms. Al sumar el período TE de 22.42 ms, el tiempo de ciclo excede el período nominal de fotograma (33.36 ms), acumulando retardo frente al PTS de reloj de pared hasta superar el umbral de descarte (`late > (us_per_frame * 2 - 2000)` = 64.7 ms).
  Una vez superado ese pasaje complejo (a partir de t=16s), `dec_f_avg` baja a 13.5 ms, `blit` a 20.4 ms y los descartes caen a **0.0% continuo** a **30.0 fps**.
  En `harry.avi` la tasa es **0.74%** (cumple $\le 1.0\%$) y en `lesserafim.avi` es **0.00%** (cumple $\le 1.0\%$).

### 5. Medición completa (`F5d_run4.csv`, capturado con autotest completo tras reinicio RTS)
| Criterio | Umbral | Medido F5d it1 (run3) | Medido F5d it2 (run4) | Estado |
|---|---|---|---|---|
| **pres_fps oculto** | $\ge 28.5$ | 29.02 | **29.06** | ✔ |
| **pres_fps con OSD** | $\ge 28.0$ | 29.73 | **29.72** | ✔ |
| **drop oculto (Track 0 ariana)** | $\le 1.0\%$ | 7.28% | **6.92%** (37/535) | ✘ (tramo complejo t=6-14s) |
| **drop oculto (Track 1 harry)** | $\le 1.0\%$ | 0.55% | **0.74%** (4/542) | ✔ |
| **drop oculto (Track 2 lesserafim)**| $\le 1.0\%$ | 0.00% | **0.00%** (0/543) | ✔ |
| **drop oculto (Track 3 meovv)** | $\le 1.0\%$ | 2.04% | **1.85%** (10/541) | ✘ |
| **drop oculto global** | $\le 1.0\%$ | 2.46% | **2.36%** (51/2161) | ✘ |
| **TE / te_timeout** | presente, $\pm 2$ Hz / $\le 1.0\%$ | 44.0–45.0 Hz / 0.0% | **44.0–45.0 Hz / 0.0%** (0/11254) | ✔ |
| **present_path / view / hud** | direct / coherentes | OK | **direct / full / coherente** | ✔ |
| **\|drift\|** | $< 100$ ms | 71 ms | **74 ms** | ✔ |
| **TAP · STRESS** | 0→1 · mismatch 0 | OK · OK | **OK (0→1) · OK (mismatch=0)** | ✔ |
| **reader_rd_avg · q_wait_max** | $< 15$ ms | OK | **8.5 ms · 0.1 ms** | ✔ |
| **heap_int mínimo** | $\ge 30\,000$ B | 56 275 B | **62 995 B** | ✔ |

### 6. Verificación visual pendiente para Keneth
- [ ] **(a) Vista pequeña (Studio):** el video debe verse derecho y en escala 240x160 correcta.
- [ ] **(b) Modo C (`tear_diag`):** la frontera de color debe presentarse sincronizada con el inicio del refresco de pantalla.
- [ ] **(c) Pantalla completa:** debe mantenerse sin desgarro diagonal y con la imagen derecha.

