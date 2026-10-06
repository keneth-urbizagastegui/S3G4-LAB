# Reanudación de S7b (nota de Claude, 3 oct, 23:58)

Codex se quedó sin cupo a las 23:06, durante la prueba rápida. Claude relanzó con el mismo script `python ejecutar_s7b.py --smoke --resume` (registro copiado en `S7b/smoke_claude_23h.log`), sin tocar el código.

**Resultado:**
- La prueba rápida recorrió K1, K3E5, K2, K2NOISE y K2DC, con **10 errores**, todos de convergencia en continua en **K2DC (barrido de V_DAC, `J1DC`) en placas de Monte Carlo** (`mc1`, `mc2`).
- Mensajes: «Source stepping failed to find operating point» y «Missing measures … adc_min_v».
- Además, **dos casos `mc0` del mismo barrido se quedaron colgados más de 39 min** (s03 y s09, POS 1 y 100) y Claude los paró.

**Para Codex:**
- Arregla la convergencia de K2DC **sin cambiar el circuito**: por ejemplo, `.op` por punto en vez de `.dc`, `.options gminsteps`/`srcsteps` u otro método, un barrido más grueso o un tiempo límite por simulación con reintento.
- Repite la prueba rápida y lanza la campaña.
- No se ha ejecutado nada de la campaña (`resultados/` sin `s7b_*`).
