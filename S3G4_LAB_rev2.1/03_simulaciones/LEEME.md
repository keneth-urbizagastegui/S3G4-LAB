# Simulaciones LTspice de la rev 2.1

Carpeta **separada a propósito** de `Simulation_LTSpice/`, que contiene las simulaciones de la rev 2.0 con sus actas. Nada de aquí modifica aquella carpeta ni la usa como línea base: la rev 2.0 es una referencia más.

| Carpeta | Qué decide | Estado |
|---|---|---|
| `P4_P7_grueso/` | Atenuador grueso: con relé (P4) o sin relé (P7) | Construida por Codex, auditada por Claude (`AUDITORIA_CLAUDE_P4_P7.md`). Por RF-07 queda P4. Pendiente: corregir P4 y volver a simular |

Documentos de diseño que gobiernan estas simulaciones:

- `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` (documento vivo, secciones B y C).
- `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html` (P1–P6), `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html` (P7) y `S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html` (P8–P11).

`ejecutar_todo.py` usa rutas relativas: funciona desde cualquier ubicación de la carpeta.

Convenciones (las mismas que en la rev 2.0): LTspice 26 en modo lote (`-b`); cada ensayo `.asc` lleva dentro sus medidas `.meas`; cada carpeta cierra con un acta de resultados.
