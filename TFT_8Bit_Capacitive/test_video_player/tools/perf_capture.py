#!/usr/bin/env python3
"""
tools/perf_capture.py
Capturador y validador automatizado de rendimiento para ESP32-S3 Video Player.
Fases soportadas: F0 (Instrumentacion/Autotest base), F1 (Concurrencia, cola, tactil, stress).
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
STRESS_REGEX = re.compile(r"STRESS,changes=(\d+),seeks=(\d+),title_mismatch=(\d+)(?:,title_wait_ms_max=(\d+))?")
TAP_REGEX = re.compile(r"TAP,hud_before=(\d+),hud_after=(\d+)")


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
    parser.add_argument("--port", required=True, help="Puerto serial (ej. COM17)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    parser.add_argument("--out", required=True, help="Ruta base de salida para CSV y logs")
    parser.add_argument("--phase", default="F0", help="Fase de prueba (F0, F1, etc.)")
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

    print(f"Iniciando captura en {args.port} a {args.baud} baud (Fase: {args.phase})...")
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
    stress_data = None
    tap_data = None
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
            if (line_str.startswith("PERF,") or
                line_str.startswith("MEDIA,") or
                line_str.startswith("STRESS,") or
                line_str.startswith("TAP,") or
                "AUTOTEST_DONE" in line_str):
                print(f"  {line_str}")

            # Deteccion de TAP
            m_tap = TAP_REGEX.search(line_str)
            if m_tap:
                tap_data = {
                    "hud_before": int(m_tap.group(1)),
                    "hud_after": int(m_tap.group(2))
                }

            # Deteccion de STRESS
            m_stress = STRESS_REGEX.search(line_str)
            if m_stress:
                stress_data = {
                    "changes": int(m_stress.group(1)),
                    "seeks": int(m_stress.group(2)),
                    "title_mismatch": int(m_stress.group(3)),
                    "title_wait_ms_max": int(m_stress.group(4)) if m_stress.group(4) is not None else None
                }

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
    groups = {}
    for r in perf_records:
        trk = r.get("track", "?")
        scn = r.get("scn", "?")
        key = (trk, scn)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    print("\n" + "=" * 148)
    print(f"RESUMEN DE RENDIMIENTO ({args.phase}) - (Primeros 2s descartados por escenario)")
    print("=" * 148)
    print(f"{'Track':<8}{'Escenario':<12}{'View':<8}{'HUD':<6}{'Muestras':<10}{'Dec FPS':<10}{'Pres FPS':<10}{'drop':<8}{'late(ms)':<10}{'drift(ms)':<11}{'rd(ms)':<10}{'dec(ms)':<10}{'blit(ms)':<10}")
    print("-" * 148)

    def sort_key(item):
        trk, scn = item[0]
        trk_str = str(trk)
        trk_num = int(trk_str) if trk_str.isdigit() else 9999
        return (trk_num, trk_str, str(scn))

    f2_summary_data = {}

    for (trk, scn), recs in sorted(groups.items(), key=sort_key):
        # Descartar primeros 2s de cada escenario (el primer reporte de 2s)
        filtered = recs[1:] if len(recs) > 1 else recs
        n = len(filtered)
        if n > 0:
            avg_dec = sum(float(x.get("dec_fps", 0.0)) for x in filtered) / n
            avg_pres = sum(float(x.get("pres_fps", 0.0)) for x in filtered) / n
            tot_drop = sum(int(x.get("drop", 0)) for x in filtered)
            max_late = max((float(x.get("late_max", 0.0)) for x in filtered), default=0.0)
            avg_drift = sum(float(x.get("drift_ms", 0.0)) for x in filtered) / n
            avg_rd = sum(float(x.get("rd_avg", 0.0)) for x in filtered) / n
            avg_dec_t = sum(float(x.get("dec_avg", 0.0)) for x in filtered) / n
            avg_blit = sum(float(x.get("blit_avg", 0.0)) for x in filtered) / n
            v_mode = filtered[0].get("view", "?")
            hud_mode = filtered[0].get("hud", "?")
        else:
            avg_dec = avg_pres = avg_drift = avg_rd = avg_dec_t = avg_blit = max_late = 0.0
            tot_drop = 0
            v_mode = hud_mode = "?"

        f2_summary_data[(str(trk), str(scn))] = {
            "dec": avg_dec,
            "pres": avg_pres,
            "drop": tot_drop,
            "late": max_late,
            "drift": avg_drift,
            "view": v_mode,
            "hud": hud_mode,
        }

        print(f"{trk:<8}{scn:<12}{v_mode:<8}{hud_mode:<6}{n:<10}{avg_dec:<10.1f}{avg_pres:<10.1f}{tot_drop:<8}{max_late:<10.1f}{avg_drift:<11.1f}{avg_rd:<10.1f}{avg_dec_t:<10.1f}{avg_blit:<10.1f}")

    print("=" * 148)

    # Tabla comparativa con F1 it3
    F1_IT3_BASE = {
        ("0", "hidden"): {"dec": 17.5, "pres": 13.9, "blit": 2.7},
        ("0", "osd"):    {"dec": 18.0, "pres": 7.3,  "blit": 2.7},
        ("0", "seek"):   {"dec": 18.4, "pres": 13.8, "blit": 2.7},
        ("1", "hidden"): {"dec": 17.9, "pres": 14.0, "blit": 2.7},
        ("1", "osd"):    {"dec": 15.9, "pres": 7.4,  "blit": 2.7},
        ("1", "seek"):   {"dec": 16.7, "pres": 14.1, "blit": 2.7},
        ("2", "hidden"): {"dec": 18.8, "pres": 13.8, "blit": 2.7},
        ("2", "osd"):    {"dec": 16.5, "pres": 7.4,  "blit": 2.7},
        ("2", "seek"):   {"dec": 17.2, "pres": 13.8, "blit": 2.7},
        ("3", "hidden"): {"dec": 16.8, "pres": 14.1, "blit": 2.7},
        ("3", "osd"):    {"dec": 16.2, "pres": 7.4,  "blit": 2.7},
        ("3", "seek"):   {"dec": 16.8, "pres": 14.2, "blit": 2.7},
    }

    print("\n" + "=" * 110)
    print("COMPARATIVA DE RENDIMIENTO: F1 it3 vs F2")
    print("=" * 110)
    print(f"{'Track':<8}{'Escenario':<12}{'F1 Dec':<10}{'F2 Dec':<10}{'F1 Pres':<10}{'F2 Pres':<10}{'Delta Pres':<12}{'F2 Drop':<10}{'F2 Drift(ms)':<14}")
    print("-" * 110)
    for (trk, scn), f1_vals in sorted(F1_IT3_BASE.items(), key=lambda x: (int(x[0][0]), x[0][1])):
        cur = f2_summary_data.get((trk, scn), {})
        f2_dec = cur.get("dec", 0.0)
        f2_pres = cur.get("pres", 0.0)
        f2_drop = cur.get("drop", 0)
        f2_drift = cur.get("drift", 0.0)
        delta_pres = f2_pres - f1_vals["pres"]
        print(f"{trk:<8}{scn:<12}{f1_vals['dec']:<10.1f}{f2_dec:<10.1f}{f1_vals['pres']:<10.1f}{f2_pres:<10.1f}{delta_pres:+12.1f}{f2_drop:<10}{f2_drift:<14.1f}")
    print("=" * 110)

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

    # Evaluacion de criterios segun la fase
    if args.phase.upper() == "F2":
        f2_passed = True
        print("\n" + "=" * 80)
        print("EVALUACION DE CRITERIOS FASE F2")
        print("=" * 80)

        # 1. Autotest completado
        if not autotest_done:
            print("[CRITERIO F2 FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
            f2_passed = False
        else:
            print(f"[CRITERIO F2 OK]: AUTOTEST_DONE recibido con {autotest_tracks} pistas.")

        # 2. Toque sintetico TAP (Bug T2)
        if not tap_data:
            print("[CRITERIO F2 FALLIDO]: No se recibio la linea TAP.", file=sys.stderr)
            f2_passed = False
        else:
            print(f"[EVALUACION TAP]: hud_before={tap_data['hud_before']}, hud_after={tap_data['hud_after']}")
            if tap_data['hud_before'] != 0 or tap_data['hud_after'] != 1:
                print(f"[CRITERIO F2 FALLIDO]: TAP requiere hud_before=0 y hud_after=1 (obtenido: {tap_data['hud_before']}, {tap_data['hud_after']}).", file=sys.stderr)
                f2_passed = False
            else:
                print("[CRITERIO F2 OK]: TAP paso de 0 a 1 correctamente.")

        # 3. STRESS con title_mismatch == 0
        if not stress_data:
            print("[CRITERIO F2 FALLIDO]: No se recibio linea STRESS.", file=sys.stderr)
            f2_passed = False
        else:
            print(f"[EVALUACION STRESS]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}")
            if stress_data['title_mismatch'] != 0:
                print(f"[CRITERIO F2 FALLIDO]: title_mismatch={stress_data['title_mismatch']} (debe ser 0).", file=sys.stderr)
                f2_passed = False
            if stress_data['changes'] < 20:
                print(f"[CRITERIO F2 FALLIDO]: changes={stress_data['changes']} < 20.", file=sys.stderr)
                f2_passed = False
            if stress_data['seeks'] < 50:
                print(f"[CRITERIO F2 FALLIDO]: seeks={stress_data['seeks']} < 50.", file=sys.stderr)
                f2_passed = False
            if stress_data['title_mismatch'] == 0 and stress_data['changes'] >= 20 and stress_data['seeks'] >= 50:
                print("[CRITERIO F2 OK]: STRESS sin fallos de sincronizacion.")

        # 4. View y HUD coherentes en todos los registros hidden/osd/seek
        view_hud_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek"):
                v = r.get("view", "")
                h = r.get("hud", "")
                if v != "full":
                    print(f"[CRITERIO F2 FALLIDO]: Registro con scn='{scn}' tiene view='{v}' (debe ser 'full').", file=sys.stderr)
                    view_hud_ok = False
                    f2_passed = False
                    break
                if scn == "osd" and h != "1":
                    print(f"[CRITERIO F2 FALLIDO]: Registro con scn='osd' tiene hud='{h}' (debe ser '1').", file=sys.stderr)
                    view_hud_ok = False
                    f2_passed = False
                    break
                if scn in ("hidden", "seek") and h != "0":
                    print(f"[CRITERIO F2 FALLIDO]: Registro con scn='{scn}' tiene hud='{h}' (debe ser '0').", file=sys.stderr)
                    view_hud_ok = False
                    f2_passed = False
                    break
        if view_hud_ok:
            print("[CRITERIO F2 OK]: view=full y hud coherente en todos los escenarios.")

        # 5. |drift_ms| < 100 en todos los registros hidden/osd/seek pasados los primeros 2 s de cada escenario
        drift_ok = True
        max_drift_observed = 0.0
        for (trk, scn), recs in groups.items():
            if scn in ("hidden", "osd", "seek"):
                filtered = recs[1:] if len(recs) > 1 else recs
                for r in filtered:
                    try:
                        d_val = float(r.get("drift_ms", 0))
                    except ValueError:
                        d_val = 0.0
                    if abs(d_val) > max_drift_observed:
                        max_drift_observed = abs(d_val)
                    if abs(d_val) >= 100.0:
                        print(f"[CRITERIO F2 FALLIDO]: drift_ms={d_val} >= 100 ms en track={trk}, scn={scn}, t_ms={r.get('t_ms')}", file=sys.stderr)
                        drift_ok = False
                        f2_passed = False
        if drift_ok:
            print(f"[CRITERIO F2 OK]: |drift_ms| < 100 ms en todos los registros (max observado: {max_drift_observed:.1f} ms).")

        # 6. late_max no crece: pendiente de regresion lineal de late_max frente a t_ms en registros hidden < 1 ms por minuto
        hidden_points = []
        for (trk, scn), recs in groups.items():
            if scn == "hidden":
                filtered = recs[1:] if len(recs) > 1 else recs
                for r in filtered:
                    try:
                        t_m = float(r.get("t_ms", 0)) / 60000.0 # minutos
                        l_m = float(r.get("late_max", 0))       # ms
                        hidden_points.append((t_m, l_m))
                    except ValueError:
                        pass

        if len(hidden_points) >= 2:
            n_pts = len(hidden_points)
            sum_t = sum(p[0] for p in hidden_points)
            sum_y = sum(p[1] for p in hidden_points)
            mean_t = sum_t / n_pts
            mean_y = sum_y / n_pts

            num = sum((p[0] - mean_t) * (p[1] - mean_y) for p in hidden_points)
            den = sum((p[0] - mean_t) ** 2 for p in hidden_points)
            slope = (num / den) if den != 0 else 0.0

            print(f"[REGRESION LINEAL late_max HIDDEN]: pendiente = {slope:.4f} ms/min (umbral: < 1.0 ms/min, muestras: {n_pts})")
            if slope >= 1.0:
                print(f"[CRITERIO F2 FALLIDO]: Pendiente de regresion {slope:.4f} ms/min >= 1.0 ms/min.", file=sys.stderr)
                f2_passed = False
            else:
                print(f"[CRITERIO F2 OK]: Pendiente de late_max estable ({slope:.4f} ms/min < 1.0 ms/min).")
        else:
            print("[ADVERTENCIA]: Muestras insuficientes para regresion lineal de late_max.")

        print("=" * 80)
        if f2_passed:
            print("\n[RESULTADO F2]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
            sys.exit(0)
        else:
            print("\n[RESULTADO F2]: FALLO - Criterios no cumplidos.", file=sys.stderr)
            sys.exit(1)

    elif args.phase.upper() == "F1":
        f1_passed = True
        if not autotest_done:
            print("\n[CRITERIO F1 FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
            f1_passed = False
        if not stress_data:
            print("\n[CRITERIO F1 FALLIDO]: No se recibio linea STRESS.", file=sys.stderr)
            f1_passed = False
        else:
            if stress_data.get('title_wait_ms_max') is not None:
                print(f"\n[EVALUACION STRESS F1]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}, title_wait_ms_max={stress_data['title_wait_ms_max']} ms")
            else:
                print(f"\n[EVALUACION STRESS F1]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}")

            if stress_data['title_mismatch'] != 0:
                print(f"[CRITERIO F1 FALLIDO]: title_mismatch={stress_data['title_mismatch']} (debe ser 0).", file=sys.stderr)
                f1_passed = False
            if stress_data['changes'] < 20:
                print(f"[CRITERIO F1 FALLIDO]: changes={stress_data['changes']} < 20.", file=sys.stderr)
                f1_passed = False
            if stress_data['seeks'] < 50:
                print(f"[CRITERIO F1 FALLIDO]: seeks={stress_data['seeks']} < 50.", file=sys.stderr)
                f1_passed = False

        # Validar consistencia de view y hud en escenarios de autotest (X1)
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek"):
                v = r.get("view", "")
                h = r.get("hud", "")
                if v != "full":
                    print(f"[CRITERIO F1 FALLIDO]: Registro con scn='{scn}' tiene view='{v}' (debe ser 'full').", file=sys.stderr)
                    f1_passed = False
                    break
                if scn == "osd" and h != "1":
                    print(f"[CRITERIO F1 FALLIDO]: Registro con scn='osd' tiene hud='{h}' (debe ser '1').", file=sys.stderr)
                    f1_passed = False
                    break
                if scn in ("hidden", "seek") and h != "0":
                    print(f"[CRITERIO F1 FALLIDO]: Registro con scn='{scn}' tiene hud='{h}' (debe ser '0').", file=sys.stderr)
                    f1_passed = False
                    break

        if f1_passed:
            print("\n[RESULTADO F1]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
            sys.exit(0)
        else:
            print("\n[RESULTADO F1]: FALLO - Criterios no cumplidos.", file=sys.stderr)
            sys.exit(1)

    else:
        # Criterio F0 (default)
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
