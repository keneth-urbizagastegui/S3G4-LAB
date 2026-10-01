# Auditoría de la simulación P4 frente a P7 (trabajo de Codex)

- Fecha: 2026-09-23, noche.
- Agente: Claude Code (Opus 5.5), como auditor.
- Objeto: tarea de Codex `task-muenuphs-puqefo` (gpt-5.6-sol, esfuerzo medium, 1 h 5 min) sobre `Simulation_LTSpice_rev21/P4_P7_grueso/`.

## Cambio

- Nuevo `Simulation_LTSpice_rev21/P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md`, con la lista de §9 del plan, la causa de cada criterio fallido, el juicio sobre los 10 s de red y lo que falta.
- Nueva subcarpeta `auditoria/`: los netlists de diagnóstico (`diag_ab.cir`, `diag_c3.cir`, `d_v1/v2/v3.cir`) y sus includes.
- No se tocó ningún entregable de Codex. `ejecutar_todo.py` regeneró `.log`, `.raw` y `resultados/` con el mismo contenido.

## Evidencia

- **Reejecución:** `python ejecutar_todo.py` da código 0, 14 simulaciones, 0 errores y 0 advertencias en 4 min 45 s. `resultados.csv` es idéntico fila por fila (2345 filas) y `resumen.md` es idéntico.
- **Diagnóstico A** (P4 500 mV/div, con `COFF_RELE` sumado arriba y diodos con CJO ≈ 0): planitud del 0.015 % hasta 100 kHz y Cb = 1076 pF, frente a los 976 pF del plan.
- **Diagnóstico B** (P7 5 mV/div, sin contar dos veces los clamps): planitud del 0.017 %, con CbF = 2 pF, un margen frágil.
- **Variantes v1, v2 y v3** (P7 500 mV/div):
  - El realce de +0.48 dB a 1.5 MHz y +3.2 dB a 8.4 MHz sólo aparece con COFF_4053 = 5 pF.
  - Con COFF ≈ 0, el frente queda plano hasta 5 MHz.
  - Causa: la fuga del 4053 desde la rama fina, cuya señal es 100 veces mayor.
  - Un primer intento con `.step` sobre `COFF_4053` no aplicaba el valor y dio cifras engañosas. Se descartó y se repitió con includes separados.

## Hallazgos

- **Errores de mi plan:**
  - `Cb` de P4 debía sumar la capacidad del contacto abierto a Ct: acopla la BNC a través de C_S.
  - `CPAR_FINO` ya incluía los clamps, y los modelos de diodo los volvían a añadir con su CJO.
  - La métrica de T03 era ambigua: Codex midió contra el nivel asentado de una cuadrada simétrica, lo que da el doble que referido al escalón.
- **Propiedades reales de los diseños:**
  - P4 da 0.909 MΩ en ×1 y cambia 8 pF entre posiciones.
  - P4 tiene −1.19 % de ganancia en ×1 (R_S/R_BIAS más la toma 1/40).
  - En los dos diseños la entrada del buffer llega a 5.86–6.09 V con los clamps BAV199.
  - P7 tiene rodilla (739 kΩ a 40 V) y 4.4 % de THD con sonda ×10.
  - P7 sufre la fuga del 4053.
- **Red, 10 s:**
  - P2-base (100 kΩ 0805): 598 mW y 347 V. No sobrevive.
  - P2-AT (2 × 49.9 kΩ 1206): 299 mW y 174 V por pieza. Verosímil, pendiente de confirmar con la hoja de la pieza. **Adoptar P2-AT.**
  - P7 sobrevive en todas las posiciones.
- **Entregables:**
  - T07 parcial.
  - `.asc` escritos como texto, sin esquema dibujado.
  - `CPROBE` aproxima Cin (23 pF en vez de 18.6 pF), sin efecto a 1 kHz.
  - Los `.raw` ocupan ~1.8 GB.

## Pendientes

1. Corregir en el plan la contabilidad de parásitas.
2. Rediseñar la entrada de P4 para RF-08: R_BIAS delante del relé, 1 MΩ en paralelo y capacidad igualada con el segundo polo del relé.
3. Añadir la resistencia serie antes del buffer.
4. Volver a simular T01–T03 y T06, y completar T07 sólo para P4.
