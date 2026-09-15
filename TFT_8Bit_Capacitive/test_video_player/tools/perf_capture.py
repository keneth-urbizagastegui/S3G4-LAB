#!/usr/bin/env python3
"""
tools/perf_capture.py
Capturador y validador automatizado de rendimiento para ESP32-S3 Video Player.
Fase F0: Instrumentacion y Autotest.
"""

import sys
import os
import time
import argparse
import re
import csv
from collections import deque

try:
    import serial
except ImportError:
    print("Error: modulo 'pyserial' no encontrado. Instalar con 'pip install pyserial'.", file=sys.stderr)
    sys.exit(3)


CRASH_REGEX = re.compile(r"Guru Meditation|abort\(\)|Backtrace:")
REBOOT_REGEX = re.compile(r"rst:0x")
AUTOTEST_REGEX = re.compile(r"AUTOTEST_DONE,tracks=(\d+)")


def parse_kv_line(line_str, prefix):
    parts = line_str.strip().split(",")
    if not parts or parts[0] != prefix:
        return None
    data = {}
    for part in parts[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def write_csv(filepath, records):
    if not records:
        return
    # Recolectar todas las claves manteniendo el orden del primer registro
    keys = list(records[0].keys())
    for r in records[1:]:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Captura de metricas de rendimiento ESP32-S3")
    parser.add_argument("--port", required=True, help="Puerto serial (ej. COM3 o /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    parser.add_argument("--out", required=True, help="Ruta base de salida para CSV y logs")
    parser.add_argument("--phase", default="F0", help="Fase de prueba (default: F0)")
    parser.add_argument("--timeout", type=float, default=420.0, help="Timeout total en segundos (default: 420)")

    args = parser.parse_args()

    # Rutas Windows normalizadas
    out_norm = os.path.normpath(args.out)
    if out_norm.lower().endswith(".csv"):
        base_out = out_norm[:-4]
        perf_csv_path = out_norm
    else:
        base_out = out_norm
        perf_csv_path = f"{base_out}.csv"

    log_path = f"{base_out}.log"
    media_csv_path = f"{base_out}_media.csv"
    crash_path = f"{base_out}_crash.txt"

    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)

    # Abrir puerto serie
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1.0)
    except Exception as e:
        print(f"Error al abrir puerto serial {args.port}: {e}", file=sys.stderr)
        sys.exit(3)

    print(f"Iniciando captura en {args.port} a {args.baud} baud...")
    print(f"Archivos de salida: {log_path}, {perf_csv_path}, {media_csv_path}")

    # Reset con RTS/DTR (DTR=False, RTS=True, 0.1 s, RTS=False)
    ser.dtr = False
    ser.rts = True
    time.sleep(0.1)
    ser.rts = False

    start_time = time.time()
    recent_lines = deque(maxlen=40)
    perf_records = []
    media_records = []

    autotest_done = False
    autotest_tracks = -1
    crashed = False
    crash_reason = ""

    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        while True:
            now = time.time()
            elapsed = now - start_time
            if elapsed > args.timeout:
                print(f"\n[TIMEOUT] Limite de {args.timeout}s alcanzado.")
                break

            try:
                line_bytes = ser.readline()
            except Exception as e:
                print(f"Error de lectura serial: {e}", file=sys.stderr)
                break

            if not line_bytes:
                continue

            line_str = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            recent_lines.append(line_str)
            log_file.write(line_str + "\n")
            log_file.flush()

            # Imprimir en consola para visibilidad
            if line_str.startswith("PERF,") or line_str.startswith("MEDIA,") or "AUTOTEST_DONE" in line_str:
                print(f"  {line_str}")

            # Deteccion de AUTOTEST_DONE
            m_done = AUTOTEST_REGEX.search(line_str)
            if m_done:
                autotest_done = True
                autotest_tracks = int(m_done.group(1))
                print(f"\n[AUTOTEST_DONE] Detectado final de autotest con {autotest_tracks} pistas.")
                break

            # Deteccion de Crash / Reinicio
            # Ignorar rst:0x durante los primeros 3 segundos tras el reset RTS/DTR
            if elapsed > 3.0 and REBOOT_REGEX.search(line_str):
                crashed = True
                crash_reason = f"Reinicio inesperado detectado: {line_str}"
                break
            if CRASH_REGEX.search(line_str):
                crashed = True
                crash_reason = f"Crash / excepcion detectada: {line_str}"
                break

            # Parsear lineas PERF
            if line_str.startswith("PERF,"):
                kv = parse_kv_line(line_str, "PERF")
                if kv:
                    perf_records.append(kv)

            # Parsear lineas MEDIA
            if line_str.startswith("MEDIA,"):
                kv = parse_kv_line(line_str, "MEDIA")
                if kv:
                    media_records.append(kv)

    try:
        ser.close()
    except Exception:
        pass

    # Guardar CSVs
    if perf_records:
        write_csv(perf_csv_path, perf_records)
    if media_records:
        write_csv(media_csv_path, media_records)

    # Manejo de Crash
    if crashed:
        print(f"\n[CRASH DETECTADO]: {crash_reason}", file=sys.stderr)
        with open(crash_path, "w", encoding="utf-8") as cf:
            cf.write(f"CRASH REASON: {crash_reason}\n\n")
            cf.write("ULTIMAS 40 LINEAS PREVIAS:\n")
            for prev_line in recent_lines:
                cf.write(prev_line + "\n")
        print(f"Dump de crash guardado en {crash_path}", file=sys.stderr)
        sys.exit(2)

    # Validacion: Salida 3 si no hubo PERF
    if not perf_records:
        print("\nError: No se recibio ninguna linea PERF.", file=sys.stderr)
        sys.exit(3)

    # Procesar resumen descartando los primeros 2 segundos de cada escenario
    # Agrupar registros por (track, scn)
    groups = {}
    for r in perf_records:
        trk = r.get("track", "?")
        scn = r.get("scn", "?")
        key = (trk, scn)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    print("\n" + "=" * 94)
    print(f"RESUMEN DE RENDIMIENTO ({args.phase}) - (Primeros 2s descartados por escenario)")
    print("=" * 94)
    print(f"{'Track':<8}{'Escenario':<14}{'Muestras':<10}{'Dec FPS':<12}{'Pres FPS':<12}{'rd_avg(ms)':<14}{'dec_avg(ms)':<14}{'blit_avg(ms)':<14}")
    print("-" * 94)

    for (trk, scn), recs in sorted(groups.items(), key=lambda x: (int(x[0][0]) if str(x[0][0]).isdigit() else str(x[0][0]), str(x[0][1]))):
        # Descartar primeros 2s de cada escenario (el primer reporte de 2s)
        filtered = recs[1:] if len(recs) > 1 else recs
        n = len(filtered)
        if n > 0:
            avg_dec = sum(float(x.get("dec_fps", 0.0)) for x in filtered) / n
            avg_pres = sum(float(x.get("pres_fps", 0.0)) for x in filtered) / n
            avg_rd = sum(float(x.get("rd_avg", 0.0)) for x in filtered) / n
            avg_dec_t = sum(float(x.get("dec_avg", 0.0)) for x in filtered) / n
            avg_blit = sum(float(x.get("blit_avg", 0.0)) for x in filtered) / n
        else:
            avg_dec = 0.0
            avg_pres = 0.0
            avg_rd = 0.0
            avg_dec_t = 0.0
            avg_blit = 0.0

        print(f"{trk:<8}{scn:<14}{n:<10}{avg_dec:<12.1f}{avg_pres:<12.1f}{avg_rd:<14.1f}{avg_dec_t:<14.1f}{avg_blit:<14.1f}")

    print("=" * 94)

    if media_records:
        print("\n" + "=" * 94)
        print("RESUMEN DE MEDIA (Pistas escaneadas en MicroSD)")
        print("=" * 94)
        print(f"{'File':<26}{'Dim':<10}{'FPS Real':<12}{'Frames':<10}{'Duracion':<10}{'Chunk Avg(KB)':<15}{'Chunk Max(KB)':<15}{'Subsampling':<12}")
        print("-" * 94)
        for m in media_records:
            f = m.get("file", "")
            w = m.get("w", "0")
            h = m.get("h", "0")
            dim = f"{w}x{h}"
            fps_m = float(m.get("fps_milli", 0)) / 1000.0
            frames = int(m.get("frames", 0))
            dur_sec = frames / fps_m if fps_m > 0 else 0
            dur_str = f"{int(dur_sec // 60):02d}:{int(dur_sec % 60):02d}"
            c_avg_kb = float(m.get("chunk_avg", 0)) / 1024.0
            c_max_kb = float(m.get("chunk_max", 0)) / 1024.0
            sub = m.get("subsampling", "?")
            print(f"{f:<26}{dim:<10}{fps_m:<12.3f}{frames:<10}{dur_str:<10}{c_avg_kb:<15.1f}{c_max_kb:<15.1f}{sub:<12}")
        print("=" * 94)

    # Criterio F0: todos los tracks de MEDIA tienen PERF y tracks == AUTOTEST_DONE.tracks
    # Obtener lista unica de pistas en MEDIA
    media_files = []
    for m in media_records:
        f = m.get("file", "")
        if f and f not in media_files:
            media_files.append(f)
    num_media_tracks = len(media_files)

    perf_tracks = set()
    for r in perf_records:
        try:
            perf_tracks.add(int(r.get("track", -1)))
        except ValueError:
            pass

    criterion_passed = True

    if not autotest_done:
        print("[CRITERIO F0 FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
        criterion_passed = False
    elif num_media_tracks != autotest_tracks:
        print(f"[CRITERIO F0 FALLIDO]: tracks de MEDIA ({num_media_tracks}) != AUTOTEST_DONE.tracks ({autotest_tracks}).", file=sys.stderr)
        criterion_passed = False

    expected_tracks = set(range(num_media_tracks))
    if not expected_tracks.issubset(perf_tracks):
        missing = expected_tracks - perf_tracks
        print(f"[CRITERIO F0 FALLIDO]: Pistas de MEDIA sin registros PERF: {missing}", file=sys.stderr)
        criterion_passed = False

    if criterion_passed:
        print("\n[RESULTADO F0]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
        sys.exit(0)
    else:
        print("\n[RESULTADO F0]: FALLO - Criterios no cumplidos.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
