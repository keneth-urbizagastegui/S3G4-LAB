# S7 — evidencia y reproducción

Ejecutar desde `CH1_entrada`:

```powershell
$env:S3G4_MODELS = 'C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models'
python ejecutar_s7.py --smoke
python ejecutar_s7.py
python verificar_s7.py --reorder
```

El ejecutor usa 10 trabajadores desde el primer control. Un código 0 significa cobertura completa y comprobación de archivos protegidos, no aceptación eléctrica.

- `quick/`: controles iniciales de J1 y J9.
- `smoke/`: decks y logs de smoke. El primer intento tuvo errores de implementación; la repetición completó 42/42 simulaciones, con código 1 sólo por cambios externos en STATE/DECISIONS. Sus registros se conservan en `s7_initial_smoke_*` y `s7_smoke_*`.
- `campaign/`: campaña original. Las inicializaciones de J5 a −40 V en 10 mV/div y 200 mV/div se interrumpieron tras intentos de convergencia; no son fallos eléctricos medidos.
- `dc_convergence/`, `dc_continuation/`, `dc_fine_continuation/`: diagnósticos de inicialización. No se usan sus tablas parciales de límites en el acta final: las etiquetas de extremos del analizador original eran para el barrido completo. Los nombres de las medidas y los decks describen el barrido real de cada diagnóstico.
- `resume/`: continuación desde 0 V a cada extremo, a pasos de 1 mV, para los dos casos de J5. Los dos barridos se fusionan en 80001 puntos de −40 a +40 V. Componentes/modelos invariables.
- `dc_repair/`, `s7_dc_repair.json`: las cuatro ejecuciones válidas de continuación, obtenidas con `--repair-dc` mientras termina J7. `--resume` puede integrarlas sólo si coinciden los hashes de los archivos protegidos y los decks generados con el ejecutor actual; el tiempo de esta ejecución paralela ya está incluido en el tiempo de pared de la campaña principal.
- `s7_completed_data.json`: datos procesados de la última campaña, para regenerar informes sin repetir simulaciones.
- `s7_attempt1_*`: datos y registros intactos de los 690 intentos originales (688 válidos y dos inicializaciones interrumpidas).
- `s7_run.json`, `s7_registro.json`: resultado final y registro. El registro de cada J5 dividido conserva sus dos ejecuciones hijas.
- `s7_protected_before/after.json` dentro de cada ejecución: SHA256 de archivos protegidos; los registros operativos y todo `S7/` quedan fuera de esa comprobación.

`python ejecutar_s7.py --resume` retoma una campaña ya terminada con casos fallidos y ejecuta sólo los casos que faltan. Conserva el tiempo y el número de ejecuciones previas en el total; no borra la evidencia de intentos anteriores.

La campaña corresponde al contrato original de S7 (±5 V y FRONT_S2B sin cambios). La decisión concurrente de ±4.90 V y C_S=1.2 nF requiere S7b; esta campaña no la certifica.

El verificador comprueba conexiones, valores nominales, independencia de tolerancias, cobertura de los cinco barridos J5, aperturas de 1024 muestras y esquema fijo de CSV. Con `--reorder`, regenera informes bajo `reorder_validation/` con el orden de los resultados invertido y compara sus CSV byte a byte con los entregados. No equivale a una segunda ejecución de LTspice.

Resultado final: código 0, 690 casos completos, 694 ejecuciones nativas contando dos intentos de inicialización interrumpidos; 692 ejecuciones válidas. Tiempo de pared de campaña y consolidación: 2275.5371 s. La reparación DC duró 203.2102 s en paralelo dentro de ese intervalo; no se suma dos veces. Las pruebas rápidas, smoke y diagnósticos tienen sus registros y tiempos propios y no se incluyen en este total.

`python ejecutar_s7.py --reports-only` regenera únicamente los informes desde los datos completos. La generación trabaja con copias de las filas para evitar mutaciones entre llamadas. Verificación final: topología, 66 variables físicas independientes, cobertura, extremos, aperturas y 12404 hashes protegidos correctos; 20 CSV idénticos por bytes con orden invertido y contra la entrega.
