# Mapa de fuentes

Las rutas son relativas a la raíz del repositorio. La lista de indexación ejecutable está en `index.json`.

| Tema | Fuentes y uso |
|---|---|
| Objetivo e integrantes | `README.md`; resumen general, no inventario completo del avance |
| Arquitectura del sistema | `docs/propuesta_arquitectura_s3g4.md`; distinguir su propuesta del estado de las actas |
| Protocolo S3G4-IP | `comm_testbench/shared/s3g4_frame.h`, `comm_testbench/shared/s3g4_cmd.h`, `comm_testbench/docs/errata_protocolo_v1_1.md`; documento completo en `docs/S3G4-IP_v1.0_protocolo.pdf` |
| Evidencia del protocolo | `comm_testbench/docs/acta_etapa_*.md`, `comm_testbench/README.md`; consultar alcance y fecha |
| Cliente remoto S3G4-UI | `docs/S3G4-UI_v1.0_cliente_remoto.md`, `client_app_testbench/README.md`, actas y checklists en `client_app_testbench/docs/` |
| Comandos del cliente | `client_app_testbench/app/package.json`; desde esa carpeta `npm run verify` ejecuta capas estrictas, literales, build y suites TS |
| Banco real | `client_app_testbench/docs/guia_uso_banco_ui.md`, `bitacora_2026-08-28_enlace_wifi.md`; verificar puertos/dispositivos actuales |
| Hardware rev. 2 | `docs/MAPA_PINES_FIRMADO.md`, `docs/ACTA_VERIFICACION_MAPA_PINES.md`, `firmware/stm32_afe_rev2/s3g4_afe_rev2.ioc` |
| Verificación de pines | `python docs/verifica_ioc.py firmware/stm32_afe_rev2/s3g4_afe_rev2.ioc`, según mapa firmado; no implica nueva validación del hardware |
| Diseño y simulación | `Schematics/S3G4_LAB_Schematic/`, `Simulation_LTSpice/Oscilloscope/`, `hardware/`, `datasheet/`; abrir sólo el archivo/ensayo necesario |
| Informes académicos | `informes_tecnicos/`, `informe/`, `plan_pfc2/`; los binarios PDF/DOCX/XLSX no se indexan como texto bruto |
| Rediseño del AFE rev. 2.1 | `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` es el documento vivo; su estado y decisiones abiertas en `ai-context/journal/2026-09-22-claude-rediseno-afe-rev21.md`. La rev. 2.0 (`docs/esbozo_hardware_s3g4.html`, `docs/netlist_hoja*.py`) queda como referencia, no como línea base |
| Instrumentos de referencia | `research_and_tests/`: DSO112 (`schematic_112g.pdf`, manuales), DSO150 (`105-15006-00A.pdf`), DSO138 mini (`dso138-mini-schematic-analog-j.pdf`), WAVE2 (ahora en `research_and_tests/Wave2/`), OpenScope MZ, TI TIDA-01012 (`tidubv5b (1).pdf`), `Micro-DMM/`, `EMBO/`, `black_scope/`. Comparativa ya extraída en el diario del 22 sep; no volver a recorrerlos enteros. `DSO183_Schematic.pdf` y `dso138-mini-schematic-main-i.pdf` son vectoriales sin texto extraíble, pero se pueden ver renderizándolos con PyMuPDF |
| Análisis del DSO112 | `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html`; resumen en texto y valores en `ai-context/journal/2026-09-23-claude-analisis-dso112.md`. Generadores de los dibujos en `S3G4_LAB_rev2.1/herramientas/`. Para ver un PDF o SVG hay que renderizarlo con PyMuPDF (`crop_pdf.py`, `render_svg.py`): el lector de PDF de la herramienta no funciona aquí |
| Análisis del WAVE2 | `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html`; valores y conclusiones en `ai-context/journal/2026-09-23-claude-analisis-wave2.md`. Fuentes en `research_and_tests/Wave2/` (placas analógicas 105-15801-00E y 105-15803-00A, placas principales 00G/00J/00M, protocolo, firmware `113-15801-092.hex`) |
| Análisis del OpenScope MZ | `S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html`; valores en `ai-context/journal/2026-09-23-claude-analisis-openscope.md`. Fuentes: `research_and_tests/openscope-mz/` (esquemático de 12 hojas sin texto extraíble —hay que renderizarlo—, firmware C/C++ de Digilent, adaptador de terceros) y `research_and_tests/waveforms-live/` |
| Simulaciones rev 2.1 | `S3G4_LAB_rev2.1/03_simulaciones/` (separada de `Simulation_LTSpice/`, rev 2.0). P4 frente a P7: `P4_P7_grueso/PLAN_SIMULACION.md`, `ENCARGO_CODEX.md` y, cuando exista, `ACTA_RESULTADOS_P4_P7.md` |
| Análisis de black_scope | `S3G4_LAB_rev2.1/02_referencias/analisis_black_scope.html`; valores en `ai-context/journal/2026-09-23-claude-analisis-black-scope.md` y `S3G4_LAB_rev2.1/herramientas/calc_black_scope.py`. Fuentes: `research_and_tests/black_scope/` (esquemático KiCad con texto en `hardware/black_scope/outputs/pdf/`, netlist `.xml`, firmware Nuklear y LVGL) |
| Partes analógicas del STM32G473 | `S3G4_LAB_rev2.1/02_referencias/g473_analogico.html`; valores en `ai-context/journal/2026-09-23-claude-g473-analogico.md` y `S3G4_LAB_rev2.1/herramientas/calc_g473.py`. Fuentes: `datasheet/stm32g473.pdf` (DS12712 Rev 5) y `datasheet/rm0440-…(1).pdf` (RM0440 Rev 9), capítulos 21–25 y tablas 268/292 |
| Componentes candidatos | `datasheet - componentes/`: C2837587 y C41416668 (BNC), C725760 y C883267 (conmutadores deslizantes). Varios son PDF de imagen; se leen extrayendo los JPEG embebidos |

## Selección y vigencia

- El índice inicial cubre documentos de arranque, arquitectura, actas, checklists, manifiestos y cabeceras normativas; no recorre dependencias, builds ni todo el código.
- `docs/` está ignorado por Git. La indexación local explícita no garantiza que exista en otro clon. `sync` informa de ausencias; no inventa ni descarga sustitutos.
- Una fuente encontrada en memoria debe contrastarse con su archivo actual si la tarea cambia ese subsistema. Los resúmenes pueden quedar atrás; las fechas del archivo no prueban aceptación.
- Para incorporar otra fuente, añadir su ruta a `index.json` o indexarla puntualmente con `source: "S3G4/ruta_relativa"`.
