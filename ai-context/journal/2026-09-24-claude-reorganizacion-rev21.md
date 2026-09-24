# Reorganización del trabajo de la rev 2.1 en `S3G4_LAB_rev2.1/`

- Fecha: 2026-09-24, madrugada.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: crear una carpeta para la rev 2.1 con todo lo hecho, ordenado en carpetas (lo que haremos, simulaciones, esquemas, informes, artefactos…), seguir compartiéndolo con los demás agentes y tenerlo como respaldo.
- Decisiones de Keneth:
  - Dentro del proyecto, con el nombre `S3G4_LAB_rev2.1`, sin espacios.
  - Mover y actualizar referencias, sin copiar.
  - Sólo la rev 2.1, con enlaces a la rev 2.0 y a las referencias.
  - Commit local, sin push.

## Cambio

- **Estructura nueva:** `00_requisitos/`, `01_diseno/`, `02_referencias/`, `03_simulaciones/`, `04_esquematicos/` (vacía), `05_informes/`, `06_plan/` y `herramientas/`, más `LEEME.md` y `ARTEFACTOS.md`.
- **Movido (11 elementos):**
  - 8 páginas HTML de `docs/`.
  - `docs/rediseno_afe_gen/`, que pasa a `herramientas/`.
  - `Simulation_LTSpice_rev21/`, con `P4_P7_grueso/` y `LEEME.md`, que pasa a `03_simulaciones/`.
  - La carpeta vacía `Simulation_LTSpice_rev21/` se borró.
- **Rutas reescritas en 42 archivos:**
  - Las páginas, los scripts y los markdown de la carpeta.
  - `STATE.md`, `SOURCES.md` y `DECISIONS.md`.
  - `index.json`.
  - Dos archivos de memoria de Claude.
- **Rutas relativas:** los scripts de `herramientas/` las calculan desde `S3G4_LAB_rev2.1/`, y los de la simulación desde su propia carpeta.
- **Archivos nuevos:**
  - `LEEME.md`, `ARTEFACTOS.md`, `04_esquematicos/LEEME.md`, `05_informes/LEEME.md` y `06_plan/PLAN.md`.
  - `docs/LEEME_rev21_movido.md`, con la tabla de rutas.
- **Memoria compartida:**
  - START apunta a la carpeta.
  - `index.json` indexa todos los `.md` de la carpeta.
  - DECISIONS lleva la tabla de rutas.
  - STATE, actualizado.
- **`.gitignore`:** excluye `.raw`, `.db`, `__pycache__` y las vistas previas de la carpeta nueva.
- **Artefactos:** las 8 páginas se volvieron a publicar en los mismos enlaces, con las versiones de `ARTEFACTOS.md`.
- **No se tocó:** los diarios anteriores (historia), la rev 2.0, `research_and_tests/` ni `datasheet/`.

## Evidencia y pruebas

- No quedan rutas viejas en los archivos vigentes. La búsqueda de `docs/rediseno_afe`, `docs/analisis_`, `docs/requisitos_`, `docs/g473_` y `Simulation_LTSpice_rev21` en la carpeta nueva, STATE, SOURCES, DECISIONS e `index.json` no encontró nada.
- Se regeneraron desde la carpeta nueva las cuatro páginas que sí salen de su script: los dos requisitos, black_scope y G473.
  - Los requisitos quedaron idénticos, salvo el fin de línea.
  - black_scope y G473 sólo difieren en la línea CSS `.src`, que se añadió al documento vivo con la sección G.
- `analisis_dso112.html` no se regenera: su script no lleva las correcciones de `fix_ruido.py`. Queda anotado en `herramientas/LEEME.md`.
- La simulación se volvió a ejecutar desde `03_simulaciones/P4_P7_grueso/`: código 0, 14 simulaciones, 0 errores y 0 advertencias. `resultados.csv` coincide fila por fila con el de Codex (2345 filas, 0 distintas) y `resumen.md` es idéntico.

## Pendientes

1. Commit local en Git (en curso en esta sesión).
2. El resto del proyecto sigue sin confirmar en Git: firmware, bancos, esquemas de la rev 2.0, informes… No entraba en este encargo.
