# 04 — Protocolo de loop engineering: compilar, flashear, medir y revisar

Cada fase de `02` se cierra con este bucle. **Una fase no está terminada porque compile: está
terminada cuando sus criterios de aceptación se cumplen con cifras medidas en la placa.**

---

## 1. Entorno (copiar tal cual en PowerShell)

```powershell
$env:IDF_PATH = "C:\esp\v6.0.1\esp-idf"
$env:IDF_TOOLS_PATH = "C:\Users\Keneth\.espressif"
. "C:\esp\v6.0.1\esp-idf\export.ps1"
cd "C:\Users\Keneth\Desktop\S3G4 LAB\TFT_8Bit_Capacitive\test_video_player"
```
- `export.bat` desde Git Bash **no funciona**. Hay que usar PowerShell.
- Hay dos juegos de herramientas de ESP-IDF en la máquina y **solo sirve** el de
  `%USERPROFILE%\.espressif`. Si aparece *«python.exe is currently active … run idf.py fullclean»*,
  estás usando el que no toca.
- Python es nativo de Windows: pásale **rutas de Windows** (`C:\...`), no `/c/...`.

## 2. Puerto de la placa

**El ESP32-S3 del reproductor está en el UART COM17** (confirmado por Keneth el 15/09/2026).
Antes de cada sesión, comprueba que sigue ahí (los puertos se reenumeran):
```powershell
python -m serial.tools.list_ports -v
```
Si COM17 no aparece o ha cambiado, **para y pregunta**. **Nunca uses COM8** (ese es el ESP32-S3 del
`l_bridge` del banco S3G4). En todo este documento, `COMx` = `COM17`.
Si la placa se queda en `boot:0x0 (DOWNLOAD)` tras flashear, ver la anomalía 5 del acta
(`python -m esptool --port COMx run`).

## 3. Modo de autoprueba del firmware (se añade en F0)

Opción de Kconfig `CONFIG_APP_PERF_AUTOTEST` (en `main/Kconfig.projbuild`, desactivada por defecto):
- Al arrancar, reproduce **cada video de la biblioteca** durante `CONFIG_APP_PERF_SECONDS_PER_TRACK`
  (60 por defecto), en este orden de escenarios por video: 20 s con la OSD oculta, 20 s con la OSD
  visible (forzada) y 20 s con 10 saltos aleatorios.
- Cada línea `PERF,` añade `track=<idx>,scn=<hidden|osd|seek>`.
- Al terminar imprime `AUTOTEST_DONE,tracks=<N contados>` y se queda en reposo.

Compilar la variante de medición sin tocar la de producción:
```powershell
idf.py -B build_perf -D SDKCONFIG=sdkconfig.perf -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.perf.defaults" build
idf.py -B build_perf -p COMx flash
```
(`sdkconfig.perf.defaults` contiene solo `CONFIG_APP_PERF_AUTOTEST=y`.)

## 4. Captura y evaluación: `tools/perf_capture.py` (lo escribe Antigravity en F0)

Especificación:
```
python tools\perf_capture.py --port COMx --baud 115200 --out plan_antigravity\mediciones\F3_run1.csv --phase F3 --timeout 420
```
1. Abre el puerto con pyserial y **reinicia la placa** con la secuencia RTS/DTR (la de esptool).
2. Guarda **todas** las líneas en `…\F3_run1.log` y las `PERF,` parseadas en el CSV (una columna por
   clave, las claves **leídas de la línea**, no escritas en una lista fija).
3. Termina al ver `AUTOTEST_DONE`, o por `--timeout`, o si detecta `Guru Meditation`, `abort()`,
   `Backtrace:` o `rst:0x` inesperados (en ese caso guarda las 40 líneas previas en
   `…_crash.txt`).
4. Evalúa los criterios de la fase (tabla de §5), por escenario, **descartando los primeros 2 s** de
   cada escenario (calentamiento).
5. Imprime un resumen y **sale con**: `0` = todos los criterios cumplidos · `1` = algún criterio
   incumplido · `2` = fallo o reinicio de la placa · `3` = no se pudo abrir el puerto o no llegaron
   líneas PERF.

## 5. Criterios por fase (los usa `perf_capture.py --phase`)

| Fase | Criterio | Umbral |
|---|---|---|
| F0 | hay líneas PERF en todos los videos | tracks contados == tracks en `AUTOTEST_DONE` |
| F1 | sin fallos durante toda la autoprueba (incluye 10 saltos por video) | código ≠ 2 |
| F2 | `late_max` no crece: pendiente de regresión de `late_max` en `hidden` | < 1 ms por minuto |
| F3 | `pres_fps` medio en `hidden` / `osd` | ≥ 28,5 / ≥ 28,0 |
| F3 | `drop / dec` en `hidden` | ≤ 1 % |
| F4 | `rd_max` | < 15 ms |
| F6 | los criterios de F3 **con la UI de EEZ cargada** | ídem F3 |
| todas | `heap_int` mínimo | ≥ 30 000 B y sin tendencia a bajar |

## 6. El bucle

```
┌─► 1. Implementar el cambio mínimo de la fase
│   2. idf.py build                     → ¿warnings nuevos? arreglarlos o anotarlos
│   3. idf.py -B build_perf … flash
│   4. perf_capture.py --phase Fx       → código de salida
│   5. Si 0 → ir a 7
│   6. Si 1/2/3 → diagnosticar con el CSV/log (NO cambiar umbrales), anotar hipótesis en el informe,
└──────  volver a 1   (máximo 5 iteraciones por fase; en la 5.ª se entrega con lo medido y se para)
    7. Flashear la variante normal y pedir la VERIFICACIÓN VISUAL a Keneth (§7)
    8. /review sobre el diff de la fase (§8)
    9. Informe de fase (§9) y commit en rama `video-player/fase-N` (§10)
```

Reglas del bucle:
- **Nunca se tocan los umbrales** para que algo pase. Si un umbral te parece imposible, **anótalo**
  con las cifras: lo decide el auditor.
- Cada iteración deja su CSV (`F3_run1.csv`, `F3_run2.csv`…). No se sobrescribe ninguno.
- Un criterio **incumplido pero medido** se entrega. Un criterio **sin medir** no.

## 7. Verificación visual (no la puede hacer Antigravity)

La cámara no está en el bucle: al terminar cada fase, pedir a Keneth que confirme en la placa y anotar
su respuesta literal:
1. ¿Tearing o bandas horizontales en escenas con movimiento? (F3)
2. ¿La OSD parpadea o el video pisa las barras al mostrarla u ocultarla? (F3, F6)
3. ¿Colores correctos (piel, cielo azul)? (F6, formato de color de EEZ)
4. ¿Píxeles corruptos tras 10 min de reproducción? (riesgo del bus a 16 MHz, `01` §5)
5. ¿Los gestos responden donde se espera? (F6)

## 8. Revisión (`/review`)

Al cerrar cada fase, antes del commit:
- Ejecutar `/review` sobre el diff de la fase, con el foco en: llamadas `lv_*` fuera de `gui_task`,
  datos compartidos entre núcleos sin protección, `heap_caps_*` sin comprobar NULL, esperas con
  `portMAX_DELAY` en rutas de video y constantes que deberían contarse.
- Cada hallazgo de la revisión se **corrige o se justifica por escrito** en el informe. No se ignora en
  silencio.
- Después, Claude hace una auditoría independiente contra este plan (no contra el informe).

## 9. Informe de fase (`plan_antigravity/informes/FASE_N.md`)

```
# Fase N — <nombre>
Resultado: CUMPLE | NO CUMPLE | PARCIAL
Iteraciones del bucle: k
Ficheros tocados: (lista)
Tabla de criterios: criterio | umbral | medido | ✔/✘   (valores copiados del resumen de perf_capture, no redondeados a mano)
Verificación visual de Keneth: (respuestas literales)
Hallazgos de /review y qué se hizo con cada uno
CONTRADICCIONES ENCONTRADAS (con el plan, el acta, las cabeceras de IDF/LVGL o el hardware) — sin resolver
Decisiones que tomé y que el auditor debe validar
Qué queda pendiente
```

## 10. Ramas y versiones

- Punto de partida: etiqueta **`vp-v0.0-base`** (código de Antigravity tal cual + este plan), en la rama
  `video-player/fase-0`.
- **Una rama por fase**: `video-player/fase-N`, creada desde la etiqueta de la fase anterior.
- Commits pequeños dentro de la fase, uno por iteración del bucle que cambie código:
  `vp F<N> it<k>: <qué cambia> — <resultado perf_capture: código y cifra clave>`.
- Al cerrar una fase **aprobada por el auditor** (Claude), se etiqueta **`vp-v0.<N>`** sobre el último
  commit. Antigravity **no crea etiquetas ni fusiona**: eso lo hace el auditor tras revisar.
- Nunca `git push`, `--force`, `rebase` ni reescribir historia. Nunca commitear `build*/`,
  `managed_components/` ni `.avi` (ya están en `.gitignore`).
- El `CHANGELOG.md` de `test_video_player/` recibe una entrada por versión etiquetada, con las cifras
  medidas de esa versión.
