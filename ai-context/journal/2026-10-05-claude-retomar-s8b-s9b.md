# Cómo retomar (lunes 5 oct, 21:00) — S8b y S9-B

Lo deja la sesión del 4 oct; el detalle está en `2026-10-04-claude-s9-plan.md`.

## En marcha al cerrar

- **Codex S9-B (LM6172), relanzado a las 20:38 del 4 oct** (PID 11660, con `--resume`), tras cortarse a las 18:28 por falta de red. Encargo `CH23_entrada/ENCARGO_CODEX_S9_B.md`; la nota de reanudación (prompt) está en el scratchpad de la sesión como `s9b2_prompt.txt`.
- **Lo primero el lunes:**
  - comprobar si terminó: el bloque `S9_B_CODEX` de `ACTA_S9.md` y su diario `2026-10-04-codex-s9.md`;
  - si se cortó otra vez, relanzar con `--resume` apuntando a su diario.
- Pedido extra en la reanudación: repetir solo las cohortes de continua de B con el offset bien contado. El modelo de National trae +2.986 mV y el Monte Carlo le sumaba otros ±3 mV, cuando la hoja da ±3 mV en total; con eso C9 bajaba al 53–57 %. Se pidió también comprobar si el modelo del AD8038 tenía la misma doble cuenta.

## Pendiente de Claude

1. **Auditar S9 (A y B)** y traer a Keneth la comparación AD8039 frente a LM6172 para CH2/CH3. Lo que se tiene hasta ahora, sin auditar:
   - **A:** cumple todo (C8 con el criterio vigente de ≤ 2 µs).
   - **B:** C1–C5 cumplen; C9 queda pendiente de la corrección del offset.
2. **S8b:** Keneth lanza la sesión de Konnect con `../S8_CH1/ENCARGO_KONNECT_S8b.md`, redibujo cableado con los símbolos y huellas propios. Después, auditar con `verificar_s8.py`, el ERC, kicad-happy y las vistas, y **unir la rama `ai/s8-ch1-esquema` con `main`** (la copia de trabajo está en esa rama; último commit `3ac0273`).
3. **Abiertos:**
   - D-07 sin aceptación registrada;
   - rehacer la tabla de consumo G.3/G.4 cuando se cierre S9;
   - rotor del trimmer SEHWA, que la hoja no identifica (medir en el prototipo).
