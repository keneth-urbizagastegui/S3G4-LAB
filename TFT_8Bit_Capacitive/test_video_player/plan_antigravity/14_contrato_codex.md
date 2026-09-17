# 14 — Contrato de trabajo con Codex (constructor desde el 17/09/2026)

Antigravity agotó su cuota **semanal** (vuelve hacia el 22/09/2026). **Codex pasa a ser el constructor**
con el mismo contrato: Claude planifica, audita y mide; Codex construye. Este documento sustituye a
`04_protocolo_loop_engineering.md` **solo en la parte de quién construye y cómo se le encarga**; todo lo
demás de `04` (mediciones, umbrales, informes) sigue igual.

## 1. Modelo y forma de invocarlo
- Modelo fijado por Keneth: **`gpt-5.6-terra`, esfuerzo `medium`**.
- Llamada (el `node` del sistema no está en el PATH; hay que dar la ruta completa):

```bash
/c/Users/Keneth/scoop/apps/fnm/current/node-versions/v24.16.0/installation/node.exe \
  "C:/Users/Keneth/.claude/plugins/cache/openai-codex/codex/1.0.6/scripts/codex-companion.mjs" \
  task --background --write --model gpt-5.6-terra --effort medium "<encargo>"
```
- Seguimiento: `status <job-id>` y `result <job-id>` del mismo script. Continuación de un trabajo
  anterior: `task --resume-last`. Cancelar: `cancel <job-id>`.
- **Ojo con la carpeta:** Codex trabaja en la raíz del repositorio (`S3G4 LAB`), no en la del firmware.
  En cada encargo hay que decirle que todo ocurre dentro de `TFT_8Bit_Capacitive/test_video_player` y
  que empiece por ahí.
- **Verificado el 17/09/2026:** el trabajo de prueba `task-mu5v0qcp-3h8suw` se ejecutó con
  `model=gpt-5.6-terra` y `effort=medium`, y respondió correctamente. (Al preguntarle, Codex dice
  llamarse «GPT-5»: los modelos no conocen su propio nombre de versión, así que lo que vale es el
  registro del trabajo.)

## 2. Reparto de responsabilidades (igual que con Antigravity)
| | Claude (auditor) | Codex (constructor) |
|---|---|---|
| Escribe el paquete de trabajo con criterios medibles | ✔ | |
| Implementa y hace commit por punto | | ✔ |
| Compila, flashea y mide | ✔ (verificación) | ✔ (durante el trabajo) |
| Verifica los datos en bruto y aprueba o rechaza | ✔ | |
| Etiqueta la versión | ✔ | |
| Prueba con el dedo en la placa | Keneth | |

## 3. Reglas del banco (idénticas)
- Placa en **COM16** (a veces reenumera a COM17). **NUNCA COM8.**
- Entorno de compilación, en PowerShell:
  `$env:IDF_PATH="C:\esp\v6.0.1\esp-idf"; $env:IDF_TOOLS_PATH="C:\Users\Keneth\.espressif"; . $env:IDF_PATH\export.ps1`
- Firmware normal: `idf.py -p COM16 build flash`.
  Firmware de autoprueba: `idf.py -B build_perf -D SDKCONFIG=sdkconfig.perf -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.perf.defaults" build` y `idf.py -B build_perf -p COM16 flash`.
- Medición: `python tools/perf_capture.py --port COM16 --out plan_antigravity/mediciones/<nombre> --phase <fase> --timeout 900`.
  Los ficheros van **siempre** a `plan_antigravity/mediciones/`.
- Rutas con espacio (**«S3G4 LAB»**) siempre entre comillas.
- Al terminar: **firmware normal flasheado** (sin autoprueba) para que Keneth pruebe.

## 4. Prohibiciones (motivo: ya pasó con Antigravity)
1. Desactivar perros guardianes o alargar sus tiempos.
2. Relajar umbrales de la medición (descartes ≤ 1 % por pista y global, `pres_fps` hidden ≥ 28,5 y
   osd ≥ 28,0, TE, drift, heap).
3. Redefinir métricas: incluye el re-anclaje PTS (`late > 100000`), el umbral de descarte
   (`2 × us_per_frame − 2000`) y marcar muestras como `init` para que no cuenten.
4. Tocar la secuencia de inicio del panel, TE, la ventana única por fotograma o la orientación
   (`MADCTL 0x48`), salvo autorización expresa del auditor por escrito en el paquete.
5. Escribir `PASS` (o `offenders=0`) sin comprobar el efecto real.
6. Editar a mano `main/ui` (código generado por EEZ): todo cambio de interfaz va en el proyecto
   `video_player/video_player.eez-project` y se regenera.
7. Dejar la autoprueba (`CONFIG_APP_PERF_AUTOTEST=y`) en el firmware normal.
8. Reescribir o enmendar commits ajenos.

## 5. Obligaciones
- **Commit por cada punto del paquete**, con mensaje `<tipo>(<ámbito>): <punto> - <qué>`.
- **No terminar el turno mientras una medición siga en marcha**: esperar su resultado y analizarlo.
- Si un criterio no se cumple: **parar y reportar con cifras**, nunca buscar un atajo.
- Informe final en `plan_antigravity/informes/FASE_<n>.md` con una fila por punto: estado, prueba y
  dato que lo respalda.
- Si se agota el tiempo o la cuota: dejar commits de lo hecho y la lista de pendientes en el informe.

## 6. Qué lee antes de empezar
`03_especificacion_ui_eez.md` (contrato de la interfaz), `diseno_ui/referencia/` (PNG 480×320, medidas
por elemento y mapa de controles), el paquete de la fase en curso y el informe de la fase anterior.

## 7. Estado al firmar este contrato (17/09/2026)
Rama `video-player/fase-6b`, último commit `d42e163`. F6a cerrada como `vp-v0.7`. De F6b están hechas
las secciones 0 (capas sobre el video, verificada por el auditor), 1 (cola) y 2 (ajustes); pendientes
las secciones 3 a 10 de `13_paquete_F6b_it2.md`.
