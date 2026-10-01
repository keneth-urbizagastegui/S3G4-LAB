#!/usr/bin/env python3
"""
tools/reset_torture.py
Prueba de robustez ante reinicios en caliente (warm reset torture test).
Ejecuta 20 reinicios aleatorios via RTS durante la reproducción de video
para verificar que la recuperación SPI de la MicroSD monta 10/10 ciclos y
reanuda la reproducción de video (pres_fps > 0) sin colgarse.
"""

import sys
import os
import time
import random
import argparse
import re

try:
    import serial
except ImportError:
    print("Error: modulo 'pyserial' no encontrado. Instalar con 'pip install pyserial'.", file=sys.stderr)
    sys.exit(3)


def parse_args():
    parser = argparse.ArgumentParser(description="Prueba de tortura de reinicios en caliente (MicroSD SPI)")
    parser.add_argument("--port", default="COM16", help="Puerto serial (default: COM16)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    parser.add_argument("--cycles", type=int, default=20, help="Numero de ciclos de reinicio (default: 20)")
    parser.add_argument("--min-play-sec", type=float, default=2.0, help="Tiempo minimo de reproduccion antes de reset (s)")
    parser.add_argument("--max-play-sec", type=float, default=15.0, help="Tiempo maximo de reproduccion antes de reset (s)")
    parser.add_argument("--boot-timeout", type=float, default=30.0, help="Tiempo limite para arranque y primer frame (s)")
    parser.add_argument("--out", default=r"plan_antigravity\mediciones\F5d_reset_torture.log", help="Ruta del log de salida")
    return parser.parse_args()


def reset_esp32(ser):
    """Genera un pulso en RTS para reiniciar el ESP32 en caliente."""
    ser.dtr = False
    ser.rts = True
    time.sleep(0.1)
    ser.rts = False


def extract_pres_fps(line):
    """Extrae pres_fps de una linea PERF si esta presente."""
    m = re.search(r"pres_fps=([0-9.]+)", line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def extract_sd_mount_passed(line):
    """Extrae passed de la linea SD_FREQ_TEST."""
    m = re.search(r"SD_FREQ_TEST,[^,]+,passed=(\d+)/10", line)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def main():
    args = parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    log_fp = open(args.out, "w", encoding="utf-8", errors="replace")

    def log_print(msg):
        print(msg)
        log_fp.write(msg + "\n")
        log_fp.flush()

    log_print(f"================================================================")
    log_print(f" TORTURE TEST: 20 REINICIOS EN CALIENTE MICROSD SPI (RTS)")
    log_print(f" Puerto: {args.port} @ {args.baud} | Ciclos: {args.cycles}")
    log_print(f" Intervalo aleatorio de reproduccion: [{args.min_play_sec}, {args.max_play_sec}] s")
    log_print(f" Archivo log: {args.out}")
    log_print(f"================================================================\n")

    try:
        ser = serial.Serial()
        ser.port = args.port
        ser.baudrate = args.baud
        ser.timeout = 0.5
        ser.dtr = False
        ser.rts = False
        ser.open()
    except Exception as e:
        log_print(f"ERROR: No se pudo abrir el puerto {args.port}: {e}")
        log_fp.close()
        sys.exit(1)

    # Esperar a que el firmware este en marcha inicialmente si no lo esta
    log_print("Sincronizando con la placa antes del primer ciclo...")
    t_sync_start = time.time()
    saw_perf = False
    while time.time() - t_sync_start < 15.0:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        log_fp.write(f"[INIT] {line}\n")
        fps = extract_pres_fps(line)
        if fps is not None and fps > 0:
            saw_perf = True
            log_print(f"Placa detectada activa y reproduciendo (pres_fps={fps:.2f})")
            break

    if not saw_perf:
        log_print("No se detecto reproduccion activa, enviando reset inicial...")
        reset_esp32(ser)
        time.sleep(2.0)

    results = []

    for cycle in range(1, args.cycles + 1):
        # 1. Esperar un tiempo aleatorio entre min_play_sec y max_play_sec mientras el video reproduce
        play_wait = random.uniform(args.min_play_sec, args.max_play_sec)
        log_print(f"\n--- CICLO {cycle}/{args.cycles}: Reproduciendo video durante {play_wait:.2f} s...")
        
        t0 = time.time()
        last_fps = None
        while time.time() - t0 < play_wait:
            raw = ser.readline()
            if raw:
                line = raw.decode("utf-8", errors="replace").strip()
                log_fp.write(f"[C{cycle}_PLAY] {line}\n")
                fps = extract_pres_fps(line)
                if fps is not None:
                    last_fps = fps

        log_print(f"Ciclo {cycle}: Ultimo pres_fps antes de reset: {last_fps if last_fps is not None else 'N/A'}")
        log_print(f"Ciclo {cycle}: ¡Enviando pulso RTS para reinicio en caliente!")
        
        # 2. Resetear en caliente via RTS
        reset_esp32(ser)

        # 3. Monitorear el arranque
        boot_start = time.time()
        mount_passed = None
        first_pres_fps = None
        boot_recovered = False
        saw_recovery_log = False
        error_lines = []

        while time.time() - boot_start < args.boot_timeout:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            log_fp.write(f"[C{cycle}_BOOT] {line}\n")

            if "secuencia de recuperacion" in line.lower():
                saw_recovery_log = True

            passed = extract_sd_mount_passed(line)
            if passed is not None:
                mount_passed = passed
                log_print(f"Ciclo {cycle}: Montaje SD: passed={passed}/10")

            fps = extract_pres_fps(line)
            if fps is not None and fps > 0:
                first_pres_fps = fps
                log_print(f"Ciclo {cycle}: Video reproduciendo: pres_fps={fps:.2f}")
                boot_recovered = True
                break

            if "0x107" in line or "Fallo al montar sistema de archivos FATFS tras" in line:
                error_lines.append(line)
                log_print(f"Ciclo {cycle} ERROR: {line}")

        cycle_ok = (mount_passed == 10) and boot_recovered and (first_pres_fps is not None and first_pres_fps > 0)
        results.append({
            "cycle": cycle,
            "play_wait_s": play_wait,
            "mount_passed": mount_passed,
            "first_pres_fps": first_pres_fps,
            "recovery_logged": saw_recovery_log,
            "ok": cycle_ok,
            "errors": error_lines
        })

        status_str = "EXITO (10/10 OK, pres_fps > 0)" if cycle_ok else "FALLO"
        log_print(f">>> RESULTADO CICLO {cycle}/{args.cycles}: {status_str} (mount={mount_passed}/10, fps={first_pres_fps})")

    ser.close()

    # Resumen final
    log_print(f"\n================================================================")
    log_print(f" RESUMEN DE PRUEBA DE TORTURA ({args.cycles} CICLOS)")
    log_print(f"================================================================")
    
    success_count = sum(1 for r in results if r["ok"])
    log_print(f"Total ciclos exitosos: {success_count}/{args.cycles}")

    for r in results:
        mark = "[OK]   " if r["ok"] else "[FALLO]"
        log_print(f" {mark} Ciclo {r['cycle']:2d}: espera={r['play_wait_s']:.1f}s | SD={r['mount_passed']}/10 | pres_fps={r['first_pres_fps']} | recov={r['recovery_logged']}")

    if success_count == args.cycles:
        log_print(f"RESULTADO FINAL: PERFECTO 20/20.")
        log_fp.close()
        sys.exit(0)
    else:
        log_print(f"RESULTADO FINAL: {success_count}/{args.cycles}. Requiere documentar fallos.")
        log_fp.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
