# 05 — Sincronización con el pin TE del ILI9488 (eliminar el tearing diagonal)

**Decisión de Keneth (15/09/2026):** se acepta un cambio de hardware mínimo, un cable, para sincronizar
el envío de fotogramas con el barrido del panel. Se integra en la siguiente fase (F5) cuando Antigravity
esté disponible.

---

## 1. Por qué hay cortes diagonales

- Enviar un fotograma completo por el bus 8080 tarda **~20,2 ms** (20 franjas de ~1,0 ms, medido en F3/F4).
- El panel refresca su imagen desde la GRAM a **~60 Hz (~16,7 ms)**, por su cuenta y sin saber cuándo
  llega un fotograma nuevo.
- El panel barre en su orientación **nativa vertical (320×480)**. Con `MADCTL 0x28` (horizontal)
  nosotros escribimos filas de 480 píxeles que, para el panel, son **columnas**. La escritura avanza
  perpendicular al barrido, y la frontera entre el fotograma viejo y el nuevo sale **inclinada**.
- Se nota en escenas rápidas porque es donde más difieren dos fotogramas seguidos.

## 2. Conexión física (la hace Keneth)

| Display ER-TFT035IPS-6-4405, conector **JP1 (40 pines)** | → | WeAct ESP32-S3 |
|---|---|---|
| **Pin 22 — TE** (Tearing Effect, salida del ILI9488) | cable directo | **GPIO 7** (header izquierdo, serigrafía «7») |

**Por qué GPIO 7:**
- No es pin de arranque (0, 3, 45, 46), ni de la memoria Octal (26–37), ni USB (19/20), ni UART0 (43/44).
- No lo usa este firmware: `TOUCH_RST_IO GPIO_NUM_7` está definido en `ft6236_i2c.c` pero **nunca se
  usa**, y el INT del táctil está sin conectar (confirmado por Keneth).
- **No choca con el proyecto S3G4 completo**, que ya compromete GPIO 17/18 (SPI3 con el STM32),
  47 (BOOT0), 4 (DATA_READY) y 21 (NRST) según `ACTA_REVISION_Y_TEST_ER-TFT035IPS-6-4405.md` §4.1.

**Cómo conectarlo:**
1. **Desconecta el USB** (placa sin alimentación).
2. Cable corto (**< 10 cm**) del **pin 22 de JP1** al **GPIO 7**. La masa ya es común (JP1 pines 1 y 40).
3. Opcional y recomendable: una **resistencia de 330 Ω a 1 kΩ en serie** en ese cable. Protege si por
   error el GPIO quedara configurado como salida.
4. **No lo confundas con el pin 39 (CTP_INT)**, que sigue sin conectar.
5. Niveles: con el puente `JP` abierto (regulador de la placa activo, acta §3.4), la lógica del ILI9488
   es de **3,3 V**, compatible con el ESP32-S3 sin adaptador.
6. Con el firmware actual el cable no hace nada: GPIO 7 queda como entrada sin usar. No hay riesgo en
   conectarlo antes de que llegue el firmware nuevo.

## 3. Cambios de firmware (para Antigravity en F5)

### 3.1 Activar la señal TE
- Tras la inicialización existente (**sin modificar ni reordenar la secuencia congelada**), enviar
  **`0x35` (TEON) con parámetro `0x00`** (solo pulso de borrado vertical).
- `lcd_bus.c`: `te_init(GPIO_NUM_7)` → GPIO de entrada, **sin pull-up ni pull-down**, interrupción
  por **flanco de subida**. La ISR guarda la marca de tiempo y notifica a `player_task`.

### 3.2 Medir antes de sincronizar
- Añadir a `PERF`: `te_hz` (pulsos por segundo, **contados**), `te_jitter_ms` (desviación del periodo)
  y `te_present=0|1`.
- Si en 1 s no llega ningún pulso: `TE,absent=1` en el log y **reproducción sin sincronía**, como hoy.
  Ni bloqueos ni fallos.

### 3.3 Sincronizar el envío
- En `player_task`, antes de la franja 0 de cada fotograma: esperar el siguiente flanco TE con un
  **tiempo máximo de 1,5 × periodo medido**. Si vence, enviar igual y contar `te_timeout`.
- Métricas: `te_wait_ms_avg/max` y `te_timeout`.
- **Límite físico:** si el envío completo (~20,2 ms) dura más que un periodo de refresco (~16,7 ms a
  60 Hz), el panel vuelve a barrer antes de terminar y **quedará un corte residual en la parte final**.
  Arrancar en TE mejora, pero puede no eliminarlo del todo. Por eso existe la opción del apartado 3.4.

### 3.4 Opción B: bajar el refresco del panel (REQUIERE APROBACIÓN EXPLÍCITA DE KENETH)
- Cambiar `FRMCTR1 (0xB1)` para que el periodo de refresco supere el envío de ~20 ms, entre **30 y
  45 Hz**. Toca la secuencia de inicialización congelada: **no se hace sin autorización**.
- Probar con valores contados a partir de `te_hz` medido, cada uno con su CSV. Keneth valida el
  parpadeo: los paneles IPS a menos de ~40 Hz pueden parpadear.

### 3.5 Criterios de aceptación (umbrales fijos)
- `te_present=1` y `te_hz` estable (±2 Hz entre ventanas).
- `te_timeout` ≤ 1 % de los fotogramas.
- **Sin pérdida de rendimiento:** pres_fps hidden ≥ 28,5, osd ≥ 28,0, drop hidden ≤ 1 % (se mantienen).
- **Verificación visual de Keneth:** ¿desaparece el corte diagonal en escenas rápidas? ¿Hay parpadeo?

## 4. Prueba rápida de la conexión (antes de tocar el reproductor)
Con el cable puesto y el firmware de F5, el log de arranque debe mostrar `TE,present=1,hz=<medido>`
cerca de 60. Si sale `absent=1`, revisar el cable (pin 22, no 39) y que se envió `0x35`.
