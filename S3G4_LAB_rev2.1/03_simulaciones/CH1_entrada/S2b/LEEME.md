# Reejecución de S2b

Desde `CH1_entrada`:

```powershell
python ejecutar_s2b.py --smoke
python ejecutar_s2b.py
python S2b/verificar_s2b.py
```

Pool de 10 trabajadores; cada instancia de LTspice usa un hilo. Los fallos
eléctricos se informan en las tablas; no hacen fallar el proceso de ejecución.
E7b/c sólo se habilitan tras calibrar E7a sobre 2 Ω a ambos niveles.

Para otra ruta, copiar `ejecutar_s2b.py`, `ejecutar_s2.py` (dependencia de sólo
lectura) y `comun/ch1_comun_s2b.inc`. Se crean las carpetas de resultados.

```powershell
$env:S3G4_MODELS = 'C:\ruta\Simulation_LTSpice\models'
python ejecutar_s2b.py
```

Opcional: `S3G4_LTSPICE` para otra instalación de LTspice. No se copia ni
redistribuye el macromodelo de fabricante. No se descarga ningún archivo.

`generados/` conserva los .cir y .log de la campaña; `smoke/`, la prueba de humo.
Las formas de onda .raw se analizan y eliminan; el ejecutor las regenera.
`verificacion_entrega.json` documenta 120 estados, 5270 nombres de medidas y
la reejecución en una ruta temporal distinta con los 14 CSV idénticos.
La ruta temporal de esa reejecución se conserva para inspección.

Fuentes rectoras: ENCARGO_CODEX_S2b, PLAN_SIMULACION_S2b y S2, planes S1/S1b,
actas S1/S1b/S2, auditorías de esas tres etapas y de P4/P7; decisiones del
2/3 oct. Diseño: revisión_entrada_ch1 §4/§6 y rediseno_afe_rev21 C.6/G.3/G.5/G.6.

Hojas locales consultadas: OPA810 SBOS799E (p4, p6, p8/9), OPA828 SBOS671D
(p4/5) y BAV199 Nexperia 2023-04-01 (p2). PINOUT contrastado contra `.SUBCKT`
en opa810_a.lib y OPAx828.LIB. El modelo BAV199 se conserva idéntico a S2.

La tabla de C5 describe el criterio del encargo, incluido su diferencial fijo
de 7 V para OPA810 apagado. El acta deja explícita la diferencia respecto a
la hoja y la falta de validez del macro sin alimentación. No es certificación
de IEC, seguridad, supervivencia ni aceptación de una segunda fuente.
