# S3G4 LAB — contexto mínimo

Proyecto de instrumentación portátil e inalámbrica de Ingeniería Electrónica (UTEC): osciloscopio, generador de funciones y multímetro. Autores según README: Keneth Joseph Urbizagastegui Fernández y William Roberto Chacón Fernández; asesor Miguel Angel Lozano Bravo.

## Arquitectura y mapa

- **ESP32-S3:** interfaz local TFT/táctil con LVGL 9, conectividad Wi-Fi, HTTP/WebSocket y puente de comunicaciones.
- **STM32G473:** adquisición, generación, procesamiento y comunicaciones con el ESP32. El banco documenta STM32G473VET6, LQFP100. No aplicar automáticamente documentación histórica de LQFP64.
- `firmware/esp32_firmware` y `firmware/stm32_firmware`: proyectos de firmware identificados como producción en el README. No equivalen a los bridges de los bancos.
- `firmware/stm32_afe_rev2`: proyecto separado del front-end rev. 2; consultar mapa de pines firmado y su verificador antes de tocar el `.ioc`.
- `comm_testbench`: banco del protocolo S3G4-IP, firmware de ensayo, bridges ESP-IDF, herramientas host, actas y definiciones normativas en `shared/`.
- `client_app_testbench`: cliente remoto unificado S3G4-UI. `app/` usa React 18, Vite 6, TypeScript y Zustand; `desktop/` usa Tauri 2/Rust; `mobile/` usa Capacitor 7. Su estructura separa transporte/códec, estado y presentación.
- `software/web_client`: otro cliente React/Vite, con versiones y propósito distintos. No asumir que es el cliente avanzado del banco; verificar el objetivo antes de elegir dónde editar.
- `Schematics/S3G4_LAB_Schematic`, `hardware/`, `Simulation_LTSpice/`, `datasheet/`: diseño, exportaciones, simulaciones y referencias eléctricas.
- `S3G4_LAB_rev2.1/`: **todo el rediseño rev 2.1** (requisitos, documento vivo, referencias, simulaciones, herramientas y plan). Empieza por su `LEEME.md` y `06_plan/PLAN.md`.
- `docs/`, `informes_tecnicos/`, `informe/`, `plan_pfc2/`: especificaciones, informes y planificación. `docs/` y `research_and_tests/` están ignorados por Git, pero sí existen localmente.

## Cómo continuar sin repetir contexto

Lee `STATE.md` (estado/preguntas abiertas) y consulta `SOURCES.md` (dónde verificar). Recupera sólo lo pertinente con `s3g4-context.ctx_search`, usando `sort: "timeline"` y, para fuentes del proyecto, `source: "S3G4/"`.

Los archivos de esta carpeta son memoria mantenida por las IA; el índice de context-mode es reconstruible. Una sesión nueva no hereda literalmente otro chat. Sus decisiones relevantes se comparten mediante estos archivos y las fuentes indexadas.
