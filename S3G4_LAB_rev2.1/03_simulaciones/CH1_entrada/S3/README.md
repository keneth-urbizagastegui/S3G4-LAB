# Bancos S3

- `generados/`: 245 decks finales, uno por caso único de la campaña registrada en `resultados/s3_ejecucion.json`. Criterios y cifras de ACTA_S3 provienen exclusivamente de esos casos y CSV.
- `smoke/`: 52 casos de comprobación previa; su estímulo E15 precede a la última corrección de offset, repetida después en los 168 casos finales. No es una campaña de aceptación.
- `diagnostico_*.cir` y sus logs/raw: verificaciones auxiliares de ruido, colapso de paso de SWI1 y reloj de resolución temporal. No se agregan a los 245 casos. Los diagnósticos de ruido usan exactamente los modelos locales sin corrección artificial.
- `probe/`: exploraciones anteriores de convergencia; no alimentan los resultados finales ni demuestran una simulación nativa E15 válida. Se conservan como evidencia histórica del banco, no como entregables de aceptación.

E15 final usa el reemplazo autorizado por §1 del plan ante falta de convergencia nativa. Sus resultados de asentamiento y glitch son aproximados, sin inyección de carga real. No indican ensayos de hardware.
