# S3G4 LAB — rev 2.1

Carpeta de trabajo del rediseño **rev 2.1**: AFE a batería con 3 canales, DMM de baja tensión y AWG de 2 canales. Se creó el 24 sep 2026 al reorganizar el trabajo. Antes vivía en `docs/` y en `Simulation_LTSpice_rev21/` (tabla de rutas en `ai-context/DECISIONS.md`, entrada del 24 sep).

| Carpeta | Qué hay | Estado |
|---|---|---|
| `00_requisitos/` | `requisitos_osciloscopio.html` (RF-01…RF-19) y `requisitos_dmm_awg.html` (RD y RG) | Acordados el 23 sep |
| `01_diseno/` | `rediseno_afe_rev21.html`, el documento vivo: decisiones D-01…D-09 y secciones A, B, C y G | En curso |
| `02_referencias/` | Anatomías del DSO112, el WAVE2, el OpenScope MZ y black_scope, y revisión analógica del STM32G473 | Cerradas |
| `03_simulaciones/` | `P4_P7_grueso/`: plan, encargo, acta de Codex, auditoría de Claude, ejecutor y resultados | Auditada; P4 queda por RF-07 |
| `04_esquematicos/` | Esquemas de la rev 2.1 | Vacía |
| `05_informes/` | Índice de actas y material para el informe | — |
| `06_plan/` | `PLAN.md`: lo que falta y las decisiones abiertas | Vivo |
| `herramientas/` | Scripts de dibujos, cálculos y páginas | — |

También: `ARTEFACTOS.md`, con el enlace de claude.ai de cada página.

## Lo que se quedó fuera (se enlaza, no se movió)

- **Rev 2.0:**
  - `docs/S3G4-AFE_v1.0_frontend_analogico.html`.
  - `docs/esbozo_hardware_s3g4.html` y su generador `docs/esbozo_hardware_gen/`.
  - `docs/MAPA_PINES_FIRMADO.md` y `docs/ACTA_VERIFICACION_MAPA_PINES.md`.
  - `docs/netlist_hoja*.py`.
  - `Simulation_LTSpice/`.
- **Referencias:**
  - `research_and_tests/`: DSO112, Wave2, openscope-mz, black_scope, NI ELVIS II, Micro-DMM…
  - `datasheet/`: DS12712, RM0440, LM27762, REF3325, OPA313, ESP32-S3.
- **Memoria compartida entre agentes:** `ai-context/` (START, STATE, DECISIONS, SOURCES, journal) y el índice `s3g4-context`.

## Reglas

- **Una sola copia de cada cosa:** se edita aquí.
- **Los artefactos son copias publicadas de estos HTML.** Si cambias uno, vuelve a publicarlo en el mismo enlace; la tabla está en `ARTEFACTOS.md`.
- **No regenerar las páginas de `02_referencias/` con su `build_*.py`.** DSO112, WAVE2 y OpenScope se corrigieron después de generarlas (`fix_ruido.py` y otros parches), y regenerarlas perdería esas correcciones. Las de `00_requisitos/`, black_scope y G473 sí salen tal cual de su script.
- **Los `.raw` de LTspice (~1.8 GB) no van a Git.** Se regeneran con `03_simulaciones/P4_P7_grueso/ejecutar_todo.py`, que ya usa rutas relativas.
- **Rutas:** dentro de esta carpeta no hay espacios. La raíz del proyecto (`S3G4 LAB`) sí tiene uno: entrecomíllala.
