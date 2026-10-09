# Reproducir S11.2

No se descargan ni modifican modelos del fabricante. Python3.12,numpy,scipy y LTspice26. Archivos previos importados en modo lectura: `ejecutar_s11_1.py`, `leer_raw_s11_1.py`, `comun/dmm_bloque1.inc` y `comun/dmm_reducido_s11_1.inc`. El generador construye `comun/dmm_bloque1_o2.inc` a partir de ellos; la firma incluye el deck, el ejecutor, el modelo BSS126 y las bibliotecas principales OPA/4051.

Desde la raíz, PowerShell:

```powershell
$env:S3G4_MODELS = 'C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/verificar_q0_s11_2.py'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s11_2.py' --preflight
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s11_2.py' --smoke --resume
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s11_2.py' --resume
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/auditar_apertura_s11_2.py'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/resumir_s11_2.py'
```

Diez trabajadores por defecto; LTspice con un hilo por proceso; límite fijo300 s por caso. `--keep-raw` conserva ondas; si se omite, se extraen métricas y se eliminan `.raw` tras leerlas. `--only Q3 Q5 ...` limita el conjunto. `--resume` conserva exclusivamente los `ok` de firma actual; nunca convierte un timeout en aceptación. Los grupos sonQ3(72),Q5(162),Q4(150),Q1(30),Q6(72),Q7(12).

Para auditoría en una ruta corta, usar por ejemplo **`C:\s112\sim\DMM`**, conservando esa estructura de tres niveles para el cálculo de raíz. Copiar allí los scripts nuevos, los cuatro archivos previos de lectura indicados y `comun/bss126_s11_2.inc`; apuntar `S3G4_MODELS` al directorio original o a una copia autorizada. La ruta absoluta de los modelos y los includes cambia las firmas: una copia limpia vuelve a ejecutar los casos. LTspice se localiza por su ruta del usuario o por `S3G4_LTSPICE`.

El valor700 Ω de R_LIM es **diagnóstico**, no una selección aprobada. IDSS21 mA es sensibilidad, no un máximo de la hoja. Q7 conserva11 s directos y puede agotar300 s. No se reintenta un timeout con otros ajustes del simulador.

`auditar_apertura_s11_2.py` repite sólo los Q5 completos cuya marca de apertura quedó vacía por igualdad numérica en el umbral; usa decks idénticos, mide el estado abierto por corriente y guarda diferencias de pico/I²t respecto de la campaña. No reemplaza sus valores originales. Los intentos previos a la corrección de la apertura y del guardado de corrientes están en `s11_2_attempts.jsonl`; los resultados válidos de campaña son los de `s11_2_campaign.csv` y su firma actual.
