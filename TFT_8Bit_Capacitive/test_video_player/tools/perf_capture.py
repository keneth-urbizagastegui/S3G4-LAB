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
    parser.add_argument("--compare", default=None, help="Ruta al CSV de fase anterior para calcular la comparacion")
    parser.add_argument("--timeout", type=float, default=420.0, help="Timeout total en segundos (default: 420)")
    parser.add_argument("--no-reset", action="store_true",
                        help="No reiniciar la placa al abrir el puerto (para medir tras un corte de "
                             "alimentacion: un reinicio por RTS deja colgada la microSD). Se pierden las "
                             "lineas MEDIA del arranque, que solo usa el criterio de F0.")

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
        ser = serial.Serial()
        ser.port = args.port
        ser.baudrate = args.baud
        ser.timeout = 1.0
        if args.no_reset:
            ser.dtr = False   # abrir sin tocar EN/IO0: la placa sigue corriendo
            ser.rts = False
        ser.open()
    except Exception as e:
        print(f"Error al abrir puerto serial {args.port}: {e}", file=sys.stderr)
        sys.exit(3)

    print(f"Iniciando captura en {args.port} a {args.baud} baud (Fase: {args.phase})...")
    print(f"Archivos de salida: {log_path}, {perf_csv_path}, {media_csv_path}")

    if args.no_reset:
        print("Sin reinicio (--no-reset): se captura desde el estado actual de la placa.")
    else:
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
    sdpull_data = None
    mount_data = None
    lib_data = None
    ui_data = None
    uinav_records = []
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
                line_str.startswith("LIB,") or
                line_str.startswith("UI,") or
                line_str.startswith("UINAV,") or
                line_str.startswith("STRESS,") or
                line_str.startswith("TAP,") or
                line_str.startswith("SDPULL,") or
                line_str.startswith("MOUNT_TEST,") or
                "AUTOTEST_DONE" in line_str):
                print(f"  {line_str}")

            # Deteccion de UI
            if line_str.startswith("UI,"):
                kv = parse_kv_line(line_str, "UI")
                if kv:
                    ui_data = kv

            # Deteccion de UINAV
            if line_str.startswith("UINAV,"):
                kv = parse_kv_line(line_str, "UINAV")
                if kv:
                    uinav_records.append(kv)

            # Deteccion de LIB
            if line_str.startswith("LIB,"):
                kv = parse_kv_line(line_str, "LIB")
                if kv:
                    lib_data = kv

            # Deteccion de SDPULL
            if line_str.startswith("SDPULL,"):
                kv = parse_kv_line(line_str, "SDPULL")
                if kv:
                    sdpull_data = kv

            # Deteccion de MOUNT_TEST
            if line_str.startswith("MOUNT_TEST,"):
                kv = parse_kv_line(line_str, "MOUNT_TEST")
                if kv:
                    mount_data = kv

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
                for _ in range(25):
                    try:
                        extra_b = ser.readline()
                        if extra_b:
                            extra_s = extra_b.decode("utf-8", errors="replace").rstrip("\r\n")
                            recent_lines.append(extra_s)
                            log_file.write(extra_s + "\n")
                    except Exception:
                        break
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

    print("\n" + "=" * 172)
    print(f"RESUMEN DE RENDIMIENTO ({args.phase}) - (Primeros 2s descartados por escenario)")
    print("=" * 172)
    print(f"{'Track':<7}{'Escenario':<11}{'View':<7}{'HUD':<5}{'Muestras':<9}{'Dec FPS':<9}{'Pres FPS':<9}{'drop':<6}{'rd_avg':<8}{'rd_p50':<8}{'rd_p95':<8}{'rd_max':<8}{'rd_slow':<9}{'dec_f_avg':<11}{'dec_f_max':<11}{'blit_avg':<9}{'drift':<8}")
    print("-" * 172)

    def sort_key(item):
        trk, scn = item[0]
        trk_str = str(trk)
        trk_num = int(trk_str) if trk_str.isdigit() else 9999
        return (trk_num, trk_str, str(scn))

    summary_data = {}

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
            avg_rd_p50 = sum(float(x.get("rd_p50", 0.0)) for x in filtered) / n
            avg_rd_p95 = sum(float(x.get("rd_p95", 0.0)) for x in filtered) / n
            max_rd = max((float(x.get("rd_max", 0.0)) for x in filtered), default=0.0)
            tot_rd_slow = sum(int(x.get("rd_slow", 0)) for x in filtered)
            avg_dec_t = sum(float(x.get("dec_avg", 0.0)) for x in filtered) / n
            avg_dec_frame = sum(float(x.get("dec_frame_ms_avg", 0.0)) for x in filtered) / n
            max_dec_frame = max((float(x.get("dec_frame_ms_max", 0.0)) for x in filtered), default=0.0)
            avg_blit = sum(float(x.get("blit_avg", 0.0)) for x in filtered) / n
            v_mode = filtered[0].get("view", "?")
            hud_mode = filtered[0].get("hud", "?")
            pres_path = filtered[0].get("present_path", "?")
            v_rect = filtered[0].get("vrect", "?")
            avg_strip_t = sum(float(x.get("strip_ms_avg", 0.0)) for x in filtered) / n
            avg_te_hz = sum(float(x.get("te_hz", 0.0)) for x in filtered) / n
            avg_te_jitter = sum(float(x.get("te_jitter_ms", 0.0)) for x in filtered) / n
            avg_te_wait = sum(float(x.get("te_wait_ms_avg", 0.0)) for x in filtered) / n
            tot_te_timeout = sum(int(x.get("te_timeout", 0)) for x in filtered)
            avg_q_wait = sum(float(x.get("q_wait_avg", x.get("rd_avg", 0.0))) for x in filtered) / n
            max_reader_rd = max((float(x.get("reader_rd_max", x.get("rd_max", 0.0))) for x in filtered), default=0.0)
            avg_slots_ready = sum(float(x.get("slots_ready_avg", 0.0)) for x in filtered) / n
        else:
            avg_dec = avg_pres = avg_drift = avg_rd = avg_rd_p50 = avg_rd_p95 = max_rd = avg_dec_t = avg_dec_frame = max_dec_frame = avg_blit = max_late = avg_strip_t = 0.0
            avg_te_hz = avg_te_jitter = avg_te_wait = avg_q_wait = max_reader_rd = avg_slots_ready = 0.0
            tot_drop = tot_rd_slow = tot_te_timeout = 0
            v_mode = hud_mode = pres_path = v_rect = "?"

        summary_data[(str(trk), str(scn))] = {
            "dec": avg_dec,
            "pres": avg_pres,
            "drop": tot_drop,
            "late": max_late,
            "drift": avg_drift,
            "rd_avg": avg_rd,
            "rd_p50": avg_rd_p50,
            "rd_p95": avg_rd_p95,
            "rd_max": max_rd,
            "rd_slow": tot_rd_slow,
            "dec_avg": avg_dec_t,
            "dec_f_avg": avg_dec_frame,
            "dec_f_max": max_dec_frame,
            "blit": avg_blit,
            "view": v_mode,
            "hud": hud_mode,
            "path": pres_path,
            "vrect": v_rect,
            "strip_ms": avg_strip_t,
            "te_hz": avg_te_hz,
            "te_jitter": avg_te_jitter,
            "te_wait": avg_te_wait,
            "te_timeout": tot_te_timeout,
            "q_wait": avg_q_wait,
            "reader_rd_max": max_reader_rd,
            "slots_ready": avg_slots_ready,
        }

        te_str = f" te_hz={avg_te_hz:.1f} te_wait={avg_te_wait:.1f}ms te_to={tot_te_timeout}" if avg_te_hz > 0 else ""
        print(f"{trk:<7}{scn:<11}{v_mode:<7}{hud_mode:<5}{n:<9}{avg_dec:<9.1f}{avg_pres:<9.1f}{tot_drop:<6}{avg_rd:<8.1f}{avg_rd_p50:<8.1f}{avg_rd_p95:<8.1f}{max_rd:<8.1f}{tot_rd_slow:<9}{avg_dec_frame:<11.1f}{max_dec_frame:<11.1f}{avg_blit:<9.1f}{avg_drift:<8.1f}{te_str}")

    print("=" * 172)

    # Tabla comparativa dinamica desde --compare (Condicion e de F3)
    if args.compare:
        compare_data = {}
        if os.path.isfile(args.compare):
            try:
                with open(args.compare, mode="r", encoding="utf-8") as cf:
                    reader = csv.DictReader(cf)
                    cmp_groups = {}
                    for row in reader:
                        c_trk = row.get("track", "?")
                        c_scn = row.get("scn", "?")
                        cmp_groups.setdefault((c_trk, c_scn), []).append(row)
                    for (c_trk, c_scn), recs in cmp_groups.items():
                        c_filt = recs[1:] if len(recs) > 1 else recs
                        cn = len(c_filt)
                        if cn > 0:
                            c_pres = sum(float(x.get("pres_fps", 0.0)) for x in c_filt) / cn
                            c_drop = sum(int(x.get("drop", 0)) for x in c_filt)
                            c_rd_avg = sum(float(x.get("rd_avg", 0.0)) for x in c_filt) / cn
                            c_rd_max = max((float(x.get("rd_max", 0.0)) for x in c_filt), default=0.0)
                            c_strip = sum(float(x.get("strip_ms_avg", 0.0)) for x in c_filt) / cn
                        else:
                            c_pres = c_rd_avg = c_rd_max = c_strip = 0.0
                            c_drop = 0
                        compare_data[(str(c_trk), str(c_scn))] = {
                            "pres": c_pres,
                            "drop": c_drop,
                            "rd_avg": c_rd_avg,
                            "rd_max": c_rd_max,
                            "strip_ms": c_strip,
                        }
            except Exception as e:
                print(f"Advertencia al leer compare CSV {args.compare}: {e}", file=sys.stderr)

        if compare_data:
            cmp_name = os.path.basename(args.compare)
            print("\n" + "=" * 144)
            print(f"TABLA COMPARATIVA: {cmp_name} vs {args.phase}")
            print("=" * 144)
            print(f"{'Track':<7}{'Escenario':<11}{'Base Pres':<11}{'Cur Pres':<11}{'Delta Pres':<12}{'Base Drop':<11}{'Cur Drop':<11}{'Base rd_max':<13}{'Cur rd_max':<13}{'Cur rd_p95':<12}{'Cur slow':<10}")
            print("-" * 144)
            for (trk, scn), cur_vals in sorted(summary_data.items(), key=sort_key):
                cmp_vals = compare_data.get((trk, scn), {})
                b_pres = cmp_vals.get("pres", 0.0)
                b_drop = cmp_vals.get("drop", 0)
                b_rd_max = cmp_vals.get("rd_max", 0.0)
                c_pres = cur_vals.get("pres", 0.0)
                c_drop = cur_vals.get("drop", 0)
                c_rd_max = cur_vals.get("rd_max", 0.0)
                c_rd_p95 = cur_vals.get("rd_p95", 0.0)
                c_slow = cur_vals.get("rd_slow", 0)
                delta_p = c_pres - b_pres if b_pres > 0 else 0.0
                print(f"{trk:<7}{scn:<11}{b_pres:<11.1f}{c_pres:<11.1f}{delta_p:+12.1f}{b_drop:<11}{c_drop:<11}{b_rd_max:<13.1f}{c_rd_max:<13.1f}{c_rd_p95:<12.1f}{c_slow:<10}")
            print("=" * 144)

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
    if args.phase.upper() in ("F5", "F5A", "F5B", "F5D", "F6", "F6A"):
        f5a_passed = True
        print("\n" + "=" * 80)
        print(f"EVALUACION DE CRITERIOS FASE {args.phase.upper()}")
        print("=" * 80)

        # 1. Autotest completado
        if not autotest_done:
            print("[CRITERIO F5a FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: AUTOTEST_DONE recibido con {autotest_tracks} pistas.")

        # 2. Presencia de senal TE y estabilidad de frecuencia
        te_present_all = True
        te_hz_vals = []
        for r in perf_records:
            scn = r.get("scn", "")
            tp = r.get("te_present", "0")
            if tp != "1":
                te_present_all = False
            if scn not in ("init", "?"):
                try:
                    hz = float(r.get("te_hz", 0.0))
                    if hz > 0.0:
                        te_hz_vals.append(hz)
                except ValueError:
                    pass

        if not te_present_all or not te_hz_vals:
            print(f"[CRITERIO F5a FALLIDO]: te_present != 1 en todos los registros o sin muestras de te_hz.", file=sys.stderr)
            f5a_passed = False
        else:
            hz_min = min(te_hz_vals)
            hz_max = max(te_hz_vals)
            hz_var = hz_max - hz_min
            print(f"[EVALUACION TE]: presente en 100% de registros. te_hz min={hz_min:.1f}, max={hz_max:.1f}, variacion={hz_var:.2f} Hz (umbral <= 2.0 Hz)")
            if hz_var > 2.0:
                print(f"[CRITERIO F5a FALLIDO]: Variacion de te_hz ({hz_var:.2f} Hz) > 2.0 Hz.", file=sys.stderr)
                f5a_passed = False
            else:
                print(f"[CRITERIO F5a OK]: Senal TE detectada y frecuencia estable ({hz_min:.1f}-{hz_max:.1f} Hz).")

        # 3. Tasa de timeouts de TE <= 1.0% de frames
        total_te_timeouts = sum(int(r.get("te_timeout", 0)) for r in perf_records)
        total_frames_dec = sum(int(r.get("dec_frames", round(float(r.get("dec_fps", 0.0)) * 2.0))) for r in perf_records)
        te_timeout_rate = (total_te_timeouts / total_frames_dec * 100.0) if total_frames_dec > 0 else 0.0
        print(f"[EVALUACION TE TIMEOUT]: timeouts={total_te_timeouts}, frames={total_frames_dec}, tasa={te_timeout_rate:.2f}% (umbral: <= 1.0%)")
        if te_timeout_rate > 1.0:
            print(f"[CRITERIO F5a FALLIDO]: Tasa de te_timeout ({te_timeout_rate:.2f}%) > 1.0%.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: Tasa de te_timeout <= 1.0%.")

        # 4. Toque sintetico TAP
        if not tap_data:
            print("[CRITERIO F5a FALLIDO]: No se recibio la linea TAP.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[EVALUACION TAP]: hud_before={tap_data['hud_before']}, hud_after={tap_data['hud_after']}")
            if tap_data['hud_before'] != 0 or tap_data['hud_after'] != 1:
                print(f"[CRITERIO F5a FALLIDO]: TAP requiere hud_before=0 y hud_after=1 (obtenido: {tap_data['hud_before']}, {tap_data['hud_after']}).", file=sys.stderr)
                f5a_passed = False
            else:
                print("[CRITERIO F5a OK]: TAP paso de 0 a 1 correctamente.")

        # 5. STRESS con title_mismatch == 0
        if not stress_data:
            print("[CRITERIO F5a FALLIDO]: No se recibio linea STRESS.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[EVALUACION STRESS]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}, title_wait_ms_max={stress_data.get('title_wait_ms_max')}")
            if stress_data['title_mismatch'] != 0:
                print(f"[CRITERIO F5a FALLIDO]: title_mismatch={stress_data['title_mismatch']} (debe ser 0).", file=sys.stderr)
                f5a_passed = False
            if stress_data['changes'] < 20:
                print(f"[CRITERIO F5a FALLIDO]: changes={stress_data['changes']} < 20.", file=sys.stderr)
                f5a_passed = False
            if stress_data['seeks'] < 50:
                print(f"[CRITERIO F5a FALLIDO]: seeks={stress_data['seeks']} < 50.", file=sys.stderr)
                f5a_passed = False
            if stress_data['title_mismatch'] == 0 and stress_data['changes'] >= 20 and stress_data['seeks'] >= 50:
                print("[CRITERIO F5a OK]: STRESS sin fallos de sincronizacion.")

        # 6. View y HUD coherentes en todos los registros hidden/osd/seek
        view_hud_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek"):
                v = r.get("view", "")
                h = r.get("hud", "")
                if v != "full":
                    print(f"[CRITERIO F5a FALLIDO]: Registro con scn='{scn}' tiene view='{v}' (debe ser 'full').", file=sys.stderr)
                    view_hud_ok = False
                    f5a_passed = False
                    break
                if scn == "osd" and h != "1":
                    print(f"[CRITERIO F5a FALLIDO]: Registro con scn='osd' tiene hud='{h}' (debe ser '1').", file=sys.stderr)
                    view_hud_ok = False
                    f5a_passed = False
                    break
                if scn in ("hidden", "seek") and h != "0":
                    print(f"[CRITERIO F5a FALLIDO]: Registro con scn='{scn}' tiene hud='{h}' (debe ser '0').", file=sys.stderr)
                    view_hud_ok = False
                    f5a_passed = False
                    break
        if view_hud_ok:
            print("[CRITERIO F5a OK]: view=full y hud coherente en todos los escenarios.")

        # 7. Present path == direct en todos los registros de fullscreen
        path_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek", "toggle"):
                p = r.get("present_path", "")
                if p != "direct":
                    print(f"[CRITERIO F5a FALLIDO]: Registro con scn='{scn}' tiene present_path='{p}' (debe ser 'direct').", file=sys.stderr)
                    path_ok = False
                    f5a_passed = False
                    break
        if path_ok:
            print("[CRITERIO F5a OK]: present_path=direct en todos los escenarios a pantalla completa.")

        # 8. |drift_ms| < 100 en todos los registros hidden/osd/seek tras descartar primeros 2 s
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
                        print(f"[CRITERIO F5a FALLIDO]: drift_ms={d_val} >= 100 ms en track={trk}, scn={scn}, t_ms={r.get('t_ms')}", file=sys.stderr)
                        drift_ok = False
                        f5a_passed = False
        if drift_ok:
            print(f"[CRITERIO F5a OK]: |drift_ms| < 100 ms en todos los registros (max observado: {max_drift_observed:.1f} ms).")

        # 9. pres_fps medio en hidden >= 28.5 y en osd >= 28.0
        hidden_pres_list = []
        osd_pres_list = []
        for (trk, scn), recs in groups.items():
            filtered = recs[1:] if len(recs) > 1 else recs
            if scn == "hidden":
                for r in filtered:
                    hidden_pres_list.append(float(r.get("pres_fps", 0.0)))
            elif scn == "osd":
                for r in filtered:
                    osd_pres_list.append(float(r.get("pres_fps", 0.0)))

        avg_pres_hidden = sum(hidden_pres_list) / len(hidden_pres_list) if hidden_pres_list else 0.0
        avg_pres_osd = sum(osd_pres_list) / len(osd_pres_list) if osd_pres_list else 0.0

        print(f"[EVALUACION pres_fps HIDDEN]: media = {avg_pres_hidden:.2f} FPS (umbral: >= 28.5 FPS)")
        if avg_pres_hidden < 28.5:
            print(f"[CRITERIO F5a FALLIDO]: pres_fps en hidden = {avg_pres_hidden:.2f} < 28.5 FPS.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: pres_fps en hidden = {avg_pres_hidden:.2f} >= 28.5 FPS.")

        print(f"[EVALUACION pres_fps OSD]: media = {avg_pres_osd:.2f} FPS (umbral: >= 28.0 FPS)")
        if avg_pres_osd < 28.0:
            print(f"[CRITERIO F5a FALLIDO]: pres_fps en osd = {avg_pres_osd:.2f} < 28.0 FPS.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: pres_fps en osd = {avg_pres_osd:.2f} >= 28.0 FPS.")

        # 10. Criterio de descartes: drop / (dec + drop) en hidden <= 1.0% por track y global
        drop_per_track_ok = True
        total_hidden_drop = 0
        total_hidden_dec = 0
        for (trk, scn), recs in sorted(groups.items(), key=sort_key):
            if scn == "hidden":
                filtered = recs[1:] if len(recs) > 1 else recs
                trk_drop = sum(int(r.get("drop", 0)) for r in filtered)
                trk_dec = sum(int(r.get("dec_frames", round(float(r.get("dec_fps", 0.0)) * 2.0))) for r in filtered)
                trk_total = trk_dec + trk_drop
                trk_rate = (trk_drop / trk_total * 100.0) if trk_total > 0 else 0.0
                total_hidden_drop += trk_drop
                total_hidden_dec += trk_dec
                print(f"[EVALUACION DROP HIDDEN TRACK {trk}]: drop={trk_drop}, dec={trk_dec}, tasa={trk_rate:.2f}% (umbral: <= 1.0%)")
                if trk_rate > 1.0:
                    print(f"[CRITERIO F5a FALLIDO]: tasa de drop en track {trk} ({trk_rate:.2f}%) > 1.0%.", file=sys.stderr)
                    drop_per_track_ok = False
                    f5a_passed = False

        glob_total = total_hidden_dec + total_hidden_drop
        glob_rate = (total_hidden_drop / glob_total * 100.0) if glob_total > 0 else 0.0
        print(f"[EVALUACION DROP HIDDEN GLOBAL]: drop={total_hidden_drop}, dec={total_hidden_dec}, tasa={glob_rate:.2f}% (umbral: <= 1.0%)")
        if glob_rate > 1.0:
            print(f"[CRITERIO F5a FALLIDO]: tasa de drop global ({glob_rate:.2f}%) > 1.0%.", file=sys.stderr)
            f5a_passed = False
        elif drop_per_track_ok:
            print(f"[CRITERIO F5a OK]: tasa de drop en hidden <= 1.0% por track y global.")

        # 11. Latencia de E/S de MicroSD: reader_rd_avg < 15.0 ms y q_wait_max < 15.0 ms
        rd_avg_ok = True
        q_wait_ok = True
        max_reader_rd_observed = 0.0
        max_q_wait_observed = 0.0
        reader_rd_list = []
        for (trk, scn), recs in groups.items():
            if scn in ("hidden", "osd", "seek"):
                filtered = recs[1:] if len(recs) > 1 else recs
                for r in filtered:
                    try:
                        rd_a = float(r.get("reader_rd_avg", r.get("rd_avg", 0.0)))
                        rd_m = float(r.get("reader_rd_max", r.get("rd_max", 0.0)))
                        qw_m = float(r.get("q_wait_max", 0.0))
                    except ValueError:
                        rd_a = rd_m = qw_m = 0.0
                    if rd_a > 0.0:
                        reader_rd_list.append(rd_a)
                    if rd_m > max_reader_rd_observed:
                        max_reader_rd_observed = rd_m
                    if qw_m > max_q_wait_observed:
                        max_q_wait_observed = qw_m
                    if qw_m >= 15.0:
                        q_wait_ok = False
        avg_reader_rd = (sum(reader_rd_list) / len(reader_rd_list)) if reader_rd_list else 0.0
        if avg_reader_rd >= 15.0:
            rd_avg_ok = False
        print(f"[EVALUACION SD READER]: reader_rd_avg={avg_reader_rd:.1f} ms (umbral: < 15.0 ms), reader_rd_max={max_reader_rd_observed:.1f} ms, q_wait_max={max_q_wait_observed:.1f} ms (umbral: < 15.0 ms)")
        if not rd_avg_ok:
            print(f"[CRITERIO F5a FALLIDO]: reader_rd_avg ({avg_reader_rd:.1f} ms) >= 15.0 ms.", file=sys.stderr)
            f5a_passed = False
        elif not q_wait_ok:
            print(f"[CRITERIO F5a FALLIDO]: q_wait_max ({max_q_wait_observed:.1f} ms) >= 15.0 ms.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: reader_rd_avg < 15.0 ms y cola de prefetch sin inanicion (q_wait_max < 15.0 ms).")

        # 12. SDPULL
        if sdpull_data:
            if sdpull_data.get("skipped") == "1":
                print("[INFO SDPULL]: SDPULL omitido (skipped=1) - pendiente de prueba manual.")
            elif sdpull_data.get("resumed") == "1":
                print(f"[CRITERIO F5a OK]: SDPULL recuperado con exito (resumed=1, removed_ms={sdpull_data.get('removed_ms')}, remount_ms={sdpull_data.get('remount_ms')}).")
            else:
                print(f"[CRITERIO F5a FALLIDO]: SDPULL no reanudado (resumed={sdpull_data.get('resumed', '0')}).", file=sys.stderr)
                f5a_passed = False
        else:
            print("[INFO SDPULL]: Escenario SDPULL no ejecutado en este run.")

        # 13. Memoria interna heap_int >= 30000 B
        min_heap_int = min((int(r.get("heap_int", 0)) for r in perf_records if "heap_int" in r), default=0)
        print(f"[EVALUACION HEAP_INT]: minimo observado = {min_heap_int} B (umbral: >= 30000 B)")
        if min_heap_int < 30000:
            print(f"[CRITERIO F5a FALLIDO]: heap_int minimo = {min_heap_int} < 30000 B.", file=sys.stderr)
            f5a_passed = False
        else:
            print(f"[CRITERIO F5a OK]: heap_int minimo = {min_heap_int} >= 30000 B.")

        # 14. Criterios especificos F5b / F6a: Biblioteca dinamica, metadatos y NVS (linea LIB)
        if args.phase.upper() in ("F5B", "F6", "F6A"):
            print("\n" + "-" * 80)
            print(f"EVALUACION CRITERIOS ESPECIFICOS FASE {args.phase.upper()} (BIBLIOTECA Y NVS)")
            print("-" * 80)
            if not lib_data:
                print(f"[CRITERIO {args.phase.upper()} FALLIDO]: No se recibio la linea LIB.", file=sys.stderr)
                f5a_passed = False
            else:
                try:
                    lib_count = int(lib_data.get("count", -1))
                    lib_compat = int(lib_data.get("compatible", -1))
                    lib_incompat = int(lib_data.get("incompatible", -1))
                    lib_json = int(lib_data.get("with_json", -1))
                    lib_thumb = int(lib_data.get("with_thumb", -1))
                    lib_scan_ms = int(lib_data.get("scan_ms", -1))
                except ValueError:
                    lib_count = lib_compat = lib_incompat = lib_json = lib_thumb = lib_scan_ms = -1

                print(f"[EVALUACION LIB]: count={lib_count}, compatible={lib_compat}, incompatible={lib_incompat}, with_json={lib_json}, with_thumb={lib_thumb}, scan_ms={lib_scan_ms} ms")

                # a) count == compatible + incompatible
                if lib_count != (lib_compat + lib_incompat):
                    print(f"[CRITERIO {args.phase.upper()} FALLIDO]: count ({lib_count}) != compatible ({lib_compat}) + incompatible ({lib_incompat}).", file=sys.stderr)
                    f5a_passed = False
                else:
                    print(f"[CRITERIO {args.phase.upper()} OK]: count == compatible + incompatible ({lib_count} == {lib_compat} + {lib_incompat}).")

                # b) count == len(media_records)
                num_media = len(media_records)
                if num_media > 0 and lib_count != num_media:
                    print(f"[CRITERIO {args.phase.upper()} FALLIDO]: count ({lib_count}) != pistas de MEDIA ({num_media}).", file=sys.stderr)
                    f5a_passed = False
                elif num_media > 0:
                    print(f"[CRITERIO {args.phase.upper()} OK]: count coincide con registros de MEDIA ({lib_count} == {num_media}).")

                # c) scan_ms < 3000 ms
                if lib_scan_ms >= 3000 or lib_scan_ms < 0:
                    print(f"[CRITERIO {args.phase.upper()} FALLIDO]: scan_ms={lib_scan_ms} ms >= 3000 ms.", file=sys.stderr)
                    f5a_passed = False
                else:
                    print(f"[CRITERIO {args.phase.upper()} OK]: scan_ms={lib_scan_ms} ms < 3000 ms.")

                # d) PSRAM libre tras escaneo >= 6 MB (6 000 000 B)
                min_psram = min((int(r.get("heap_psram", 0)) for r in perf_records if "heap_psram" in r), default=0)
                print(f"[EVALUACION PSRAM LIBRE]: minimo observado = {min_psram} B (umbral: >= 6000000 B)")
                if min_psram < 6000000:
                    print(f"[CRITERIO {args.phase.upper()} FALLIDO]: PSRAM libre minima = {min_psram} < 6000000 B.", file=sys.stderr)
                    f5a_passed = False
                else:
                    print(f"[CRITERIO {args.phase.upper()} OK]: PSRAM libre minima = {min_psram} B >= 6 MB.")

        # 15. Criterios especificos F6/F6a: UI EEZ y navegacion de botones (UINAV)
        if args.phase.upper() in ("F6", "F6A"):
            print("\n" + "-" * 80)
            print("EVALUACION CRITERIOS ESPECIFICOS FASE F6a (UI EEZ + NAVEGACION UINAV)")
            print("-" * 80)
            if ui_data:
                print(f"[EVALUACION UI]: screens={ui_data.get('screens')}, widgets={ui_data.get('widgets')}, fonts={ui_data.get('fonts')}, images={ui_data.get('images')}")
                print("[CRITERIO F6a OK]: Componentes UI reportados con exito.")
            else:
                print("[INFO F6a]: Linea UI no recibida en este run.")

            if uinav_records:
                all_uinav_pass = True
                for rec in uinav_records:
                    btn = rec.get("btn", "?")
                    res = rec.get("result", "FAIL")
                    print(f"[EVALUACION UINAV]: btn={btn} -> {res}")
                    if res != "PASS":
                        all_uinav_pass = False
                if all_uinav_pass:
                    print("[CRITERIO F6a OK]: Todos los botones verificados con PASS en UINAV.")
                else:
                    print("[CRITERIO F6a FALLIDO]: Al menos un boton fallo en UINAV.", file=sys.stderr)
                    f5a_passed = False
            else:
                print("[INFO UINAV]: No se recibieron registros UINAV en este run.")

        print("=" * 80)
        if f5a_passed:
            print(f"\n[RESULTADO {args.phase.upper()}]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
            sys.exit(0)
        else:
            print(f"\n[RESULTADO {args.phase.upper()}]: FALLO - Criterios no cumplidos.", file=sys.stderr)
            sys.exit(1)

    elif args.phase.upper() == "F4":
        f4_passed = True
        print("\n" + "=" * 80)
        print("EVALUACION DE CRITERIOS FASE F4")
        print("=" * 80)

        # 1. Autotest completado
        if not autotest_done:
            print("[CRITERIO F4 FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[CRITERIO F4 OK]: AUTOTEST_DONE recibido con {autotest_tracks} pistas.")

        # 2. Toque sintetico TAP
        if not tap_data:
            print("[CRITERIO F4 FALLIDO]: No se recibio la linea TAP.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[EVALUACION TAP]: hud_before={tap_data['hud_before']}, hud_after={tap_data['hud_after']}")
            if tap_data['hud_before'] != 0 or tap_data['hud_after'] != 1:
                print(f"[CRITERIO F4 FALLIDO]: TAP requiere hud_before=0 y hud_after=1 (obtenido: {tap_data['hud_before']}, {tap_data['hud_after']}).", file=sys.stderr)
                f4_passed = False
            else:
                print("[CRITERIO F4 OK]: TAP paso de 0 a 1 correctamente.")

        # 3. STRESS con title_mismatch == 0
        if not stress_data:
            print("[CRITERIO F4 FALLIDO]: No se recibio linea STRESS.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[EVALUACION STRESS]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}")
            if stress_data['title_mismatch'] != 0:
                print(f"[CRITERIO F4 FALLIDO]: title_mismatch={stress_data['title_mismatch']} (debe ser 0).", file=sys.stderr)
                f4_passed = False
            if stress_data['changes'] < 20:
                print(f"[CRITERIO F4 FALLIDO]: changes={stress_data['changes']} < 20.", file=sys.stderr)
                f4_passed = False
            if stress_data['seeks'] < 50:
                print(f"[CRITERIO F4 FALLIDO]: seeks={stress_data['seeks']} < 50.", file=sys.stderr)
                f4_passed = False
            if stress_data['title_mismatch'] == 0 and stress_data['changes'] >= 20 and stress_data['seeks'] >= 50:
                print("[CRITERIO F4 OK]: STRESS sin fallos de sincronizacion.")

        # 4. View y HUD coherentes en todos los registros hidden/osd/seek
        view_hud_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek"):
                v = r.get("view", "")
                h = r.get("hud", "")
                if v != "full":
                    print(f"[CRITERIO F4 FALLIDO]: Registro con scn='{scn}' tiene view='{v}' (debe ser 'full').", file=sys.stderr)
                    view_hud_ok = False
                    f4_passed = False
                    break
                if scn == "osd" and h != "1":
                    print(f"[CRITERIO F4 FALLIDO]: Registro con scn='osd' tiene hud='{h}' (debe ser '1').", file=sys.stderr)
                    view_hud_ok = False
                    f4_passed = False
                    break
                if scn in ("hidden", "seek") and h != "0":
                    print(f"[CRITERIO F4 FALLIDO]: Registro con scn='{scn}' tiene hud='{h}' (debe ser '0').", file=sys.stderr)
                    view_hud_ok = False
                    f4_passed = False
                    break
        if view_hud_ok:
            print("[CRITERIO F4 OK]: view=full y hud coherente en todos los escenarios.")

        # 5. Present path == direct en todos los registros de fullscreen
        path_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek", "toggle"):
                p = r.get("present_path", "")
                if p != "direct":
                    print(f"[CRITERIO F4 FALLIDO]: Registro con scn='{scn}' tiene present_path='{p}' (debe ser 'direct').", file=sys.stderr)
                    path_ok = False
                    f4_passed = False
                    break
        if path_ok:
            print("[CRITERIO F4 OK]: present_path=direct en todos los escenarios a pantalla completa.")

        # 6. |drift_ms| < 100 en todos los registros hidden/osd/seek tras descartar primeros 2 s
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
                        print(f"[CRITERIO F4 FALLIDO]: drift_ms={d_val} >= 100 ms en track={trk}, scn={scn}, t_ms={r.get('t_ms')}", file=sys.stderr)
                        drift_ok = False
                        f4_passed = False
        if drift_ok:
            print(f"[CRITERIO F4 OK]: |drift_ms| < 100 ms en todos los registros (max observado: {max_drift_observed:.1f} ms).")

        # 7. pres_fps medio en hidden >= 28.5 y en osd >= 28.0
        hidden_pres_list = []
        osd_pres_list = []
        for (trk, scn), recs in groups.items():
            filtered = recs[1:] if len(recs) > 1 else recs
            if scn == "hidden":
                for r in filtered:
                    hidden_pres_list.append(float(r.get("pres_fps", 0.0)))
            elif scn == "osd":
                for r in filtered:
                    osd_pres_list.append(float(r.get("pres_fps", 0.0)))

        avg_pres_hidden = sum(hidden_pres_list) / len(hidden_pres_list) if hidden_pres_list else 0.0
        avg_pres_osd = sum(osd_pres_list) / len(osd_pres_list) if osd_pres_list else 0.0

        print(f"[EVALUACION pres_fps HIDDEN]: media = {avg_pres_hidden:.2f} FPS (umbral: >= 28.5 FPS)")
        if avg_pres_hidden < 28.5:
            print(f"[CRITERIO F4 FALLIDO]: pres_fps en hidden = {avg_pres_hidden:.2f} < 28.5 FPS.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[CRITERIO F4 OK]: pres_fps en hidden = {avg_pres_hidden:.2f} >= 28.5 FPS.")

        print(f"[EVALUACION pres_fps OSD]: media = {avg_pres_osd:.2f} FPS (umbral: >= 28.0 FPS)")
        if avg_pres_osd < 28.0:
            print(f"[CRITERIO F4 FALLIDO]: pres_fps en osd = {avg_pres_osd:.2f} < 28.0 FPS.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[CRITERIO F4 OK]: pres_fps en osd = {avg_pres_osd:.2f} >= 28.0 FPS.")

        # 8. Criterio de descartes T3: drop / (dec + drop) en hidden <= 1.0% por track y global
        drop_per_track_ok = True
        total_hidden_drop = 0
        total_hidden_dec = 0
        for (trk, scn), recs in sorted(groups.items(), key=sort_key):
            if scn == "hidden":
                filtered = recs[1:] if len(recs) > 1 else recs
                trk_drop = sum(int(r.get("drop", 0)) for r in filtered)
                trk_dec = sum(int(r.get("dec_frames", round(float(r.get("dec_fps", 0.0)) * 2.0))) for r in filtered)
                trk_total = trk_dec + trk_drop
                trk_rate = (trk_drop / trk_total * 100.0) if trk_total > 0 else 0.0
                total_hidden_drop += trk_drop
                total_hidden_dec += trk_dec
                print(f"[EVALUACION DROP HIDDEN TRACK {trk}]: drop={trk_drop}, dec={trk_dec}, tasa={trk_rate:.2f}% (umbral: <= 1.0%)")
                if trk_rate > 1.0:
                    print(f"[CRITERIO F4 FALLIDO]: tasa de drop en track {trk} ({trk_rate:.2f}%) > 1.0%.", file=sys.stderr)
                    drop_per_track_ok = False
                    f4_passed = False

        glob_total = total_hidden_dec + total_hidden_drop
        glob_rate = (total_hidden_drop / glob_total * 100.0) if glob_total > 0 else 0.0
        print(f"[EVALUACION DROP HIDDEN GLOBAL]: drop={total_hidden_drop}, dec={total_hidden_dec}, tasa={glob_rate:.2f}% (umbral: <= 1.0%)")
        if glob_rate > 1.0:
            print(f"[CRITERIO F4 FALLIDO]: tasa de drop global ({glob_rate:.2f}%) > 1.0%.", file=sys.stderr)
            f4_passed = False
        elif drop_per_track_ok:
            print(f"[CRITERIO F4 OK]: tasa de drop en hidden <= 1.0% por track y global.")

        # 9. rd_max < 15.0 ms en hidden, osd, seek tras descartar primeros 2 s
        rd_max_ok = True
        max_rd_observed = 0.0
        for (trk, scn), recs in groups.items():
            if scn in ("hidden", "osd", "seek"):
                filtered = recs[1:] if len(recs) > 1 else recs
                for r in filtered:
                    try:
                        rd_m = float(r.get("rd_max", 0.0))
                    except ValueError:
                        rd_m = 0.0
                    if rd_m > max_rd_observed:
                        max_rd_observed = rd_m
                    if rd_m >= 15.0:
                        print(f"[CRITERIO F4 FALLIDO]: rd_max={rd_m:.1f} >= 15.0 ms en track={trk}, scn={scn}, t_ms={r.get('t_ms')}", file=sys.stderr)
                        rd_max_ok = False
                        f4_passed = False
        print(f"[EVALUACION rd_max]: max observado en hidden/osd/seek = {max_rd_observed:.1f} ms (umbral: < 15.0 ms)")
        if not rd_max_ok:
            print(f"[CRITERIO F4 FALLIDO]: rd_max maximo ({max_rd_observed:.1f} ms) >= 15.0 ms.", file=sys.stderr)
        else:
            print(f"[CRITERIO F4 OK]: rd_max < 15.0 ms en todos los escenarios.")

        # 10. SDPULL
        if sdpull_data:
            if sdpull_data.get("skipped") == "1":
                print("[CRITERIO F4 OK]: SDPULL omitido (skipped=1).")
            elif sdpull_data.get("resumed") == "1":
                print(f"[CRITERIO F4 OK]: SDPULL recuperado con exito (resumed=1, removed_ms={sdpull_data.get('removed_ms')}, remount_ms={sdpull_data.get('remount_ms')}).")
            else:
                print(f"[CRITERIO F4 FALLIDO]: SDPULL no reanudado (resumed={sdpull_data.get('resumed', '0')}).", file=sys.stderr)
                f4_passed = False
        else:
            print("[INFO SDPULL]: Escenario SDPULL no ejecutado en este run.")

        # 11. Memoria interna heap_int >= 30000 B
        min_heap_int = min((int(r.get("heap_int", 0)) for r in perf_records if "heap_int" in r), default=0)
        print(f"[EVALUACION HEAP_INT]: minimo observado = {min_heap_int} B (umbral: >= 30000 B)")
        if min_heap_int < 30000:
            print(f"[CRITERIO F4 FALLIDO]: heap_int minimo = {min_heap_int} < 30000 B.", file=sys.stderr)
            f4_passed = False
        else:
            print(f"[CRITERIO F4 OK]: heap_int minimo = {min_heap_int} >= 30000 B.")

        print("=" * 80)
        if f4_passed:
            print("\n[RESULTADO F4]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
            sys.exit(0)
        else:
            print("\n[RESULTADO F4]: FALLO - Criterios no cumplidos.", file=sys.stderr)
            sys.exit(1)

    elif args.phase.upper() == "F3":
        f3_passed = True
        print("\n" + "=" * 80)
        print("EVALUACION DE CRITERIOS FASE F3")
        print("=" * 80)

        # 1. Autotest completado
        if not autotest_done:
            print("[CRITERIO F3 FALLIDO]: No se recibio AUTOTEST_DONE.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[CRITERIO F3 OK]: AUTOTEST_DONE recibido con {autotest_tracks} pistas.")

        # 2. Toque sintetico TAP (Bug T2)
        if not tap_data:
            print("[CRITERIO F3 FALLIDO]: No se recibio la linea TAP.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[EVALUACION TAP]: hud_before={tap_data['hud_before']}, hud_after={tap_data['hud_after']}")
            if tap_data['hud_before'] != 0 or tap_data['hud_after'] != 1:
                print(f"[CRITERIO F3 FALLIDO]: TAP requiere hud_before=0 y hud_after=1 (obtenido: {tap_data['hud_before']}, {tap_data['hud_after']}).", file=sys.stderr)
                f3_passed = False
            else:
                print("[CRITERIO F3 OK]: TAP paso de 0 a 1 correctamente.")

        # 3. STRESS con title_mismatch == 0
        if not stress_data:
            print("[CRITERIO F3 FALLIDO]: No se recibio linea STRESS.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[EVALUACION STRESS]: changes={stress_data['changes']}, seeks={stress_data['seeks']}, title_mismatch={stress_data['title_mismatch']}")
            if stress_data['title_mismatch'] != 0:
                print(f"[CRITERIO F3 FALLIDO]: title_mismatch={stress_data['title_mismatch']} (debe ser 0).", file=sys.stderr)
                f3_passed = False
            if stress_data['changes'] < 20:
                print(f"[CRITERIO F3 FALLIDO]: changes={stress_data['changes']} < 20.", file=sys.stderr)
                f3_passed = False
            if stress_data['seeks'] < 50:
                print(f"[CRITERIO F3 FALLIDO]: seeks={stress_data['seeks']} < 50.", file=sys.stderr)
                f3_passed = False
            if stress_data['title_mismatch'] == 0 and stress_data['changes'] >= 20 and stress_data['seeks'] >= 50:
                print("[CRITERIO F3 OK]: STRESS sin fallos de sincronizacion.")

        # 4. View y HUD coherentes en todos los registros hidden/osd/seek
        view_hud_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek"):
                v = r.get("view", "")
                h = r.get("hud", "")
                if v != "full":
                    print(f"[CRITERIO F3 FALLIDO]: Registro con scn='{scn}' tiene view='{v}' (debe ser 'full').", file=sys.stderr)
                    view_hud_ok = False
                    f3_passed = False
                    break
                if scn == "osd" and h != "1":
                    print(f"[CRITERIO F3 FALLIDO]: Registro con scn='osd' tiene hud='{h}' (debe ser '1').", file=sys.stderr)
                    view_hud_ok = False
                    f3_passed = False
                    break
                if scn in ("hidden", "seek") and h != "0":
                    print(f"[CRITERIO F3 FALLIDO]: Registro con scn='{scn}' tiene hud='{h}' (debe ser '0').", file=sys.stderr)
                    view_hud_ok = False
                    f3_passed = False
                    break
        if view_hud_ok:
            print("[CRITERIO F3 OK]: view=full y hud coherente en todos los escenarios.")

        # 5. Present path == direct en todos los registros de fullscreen
        path_ok = True
        for r in perf_records:
            scn = r.get("scn", "")
            if scn in ("hidden", "osd", "seek", "toggle"):
                p = r.get("present_path", "")
                if p != "direct":
                    print(f"[CRITERIO F3 FALLIDO]: Registro con scn='{scn}' tiene present_path='{p}' (debe ser 'direct').", file=sys.stderr)
                    path_ok = False
                    f3_passed = False
                    break
        if path_ok:
            print("[CRITERIO F3 OK]: present_path=direct en todos los escenarios a pantalla completa.")

        # 6. |drift_ms| < 100 en todos los registros hidden/osd/seek tras descartar primeros 2 s
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
                        print(f"[CRITERIO F3 FALLIDO]: drift_ms={d_val} >= 100 ms en track={trk}, scn={scn}, t_ms={r.get('t_ms')}", file=sys.stderr)
                        drift_ok = False
                        f3_passed = False
        if drift_ok:
            print(f"[CRITERIO F3 OK]: |drift_ms| < 100 ms en todos los registros (max observado: {max_drift_observed:.1f} ms).")

        # 7. pres_fps medio en hidden >= 28.5 y en osd >= 28.0
        hidden_pres_list = []
        osd_pres_list = []
        for (trk, scn), recs in groups.items():
            filtered = recs[1:] if len(recs) > 1 else recs
            if scn == "hidden":
                for r in filtered:
                    hidden_pres_list.append(float(r.get("pres_fps", 0.0)))
            elif scn == "osd":
                for r in filtered:
                    osd_pres_list.append(float(r.get("pres_fps", 0.0)))

        avg_pres_hidden = sum(hidden_pres_list) / len(hidden_pres_list) if hidden_pres_list else 0.0
        avg_pres_osd = sum(osd_pres_list) / len(osd_pres_list) if osd_pres_list else 0.0

        print(f"[EVALUACION pres_fps HIDDEN]: media = {avg_pres_hidden:.2f} FPS (umbral: >= 28.5 FPS)")
        if avg_pres_hidden < 28.5:
            print(f"[CRITERIO F3 FALLIDO]: pres_fps en hidden = {avg_pres_hidden:.2f} < 28.5 FPS.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[CRITERIO F3 OK]: pres_fps en hidden = {avg_pres_hidden:.2f} >= 28.5 FPS.")

        print(f"[EVALUACION pres_fps OSD]: media = {avg_pres_osd:.2f} FPS (umbral: >= 28.0 FPS)")
        if avg_pres_osd < 28.0:
            print(f"[CRITERIO F3 FALLIDO]: pres_fps en osd = {avg_pres_osd:.2f} < 28.0 FPS.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[CRITERIO F3 OK]: pres_fps en osd = {avg_pres_osd:.2f} >= 28.0 FPS.")

        # 8. Criterio de descartes T3: drop / (dec + drop) en hidden <= 1.0% por track y global (Condicion a de F3)
        drop_per_track_ok = True
        total_hidden_drop = 0
        total_hidden_dec = 0
        for (trk, scn), recs in sorted(groups.items(), key=sort_key):
            if scn == "hidden":
                filtered = recs[1:] if len(recs) > 1 else recs
                trk_drop = sum(int(r.get("drop", 0)) for r in filtered)
                trk_dec = sum(int(r.get("dec_frames", round(float(r.get("dec_fps", 0.0)) * 2.0))) for r in filtered)
                trk_total = trk_dec + trk_drop
                trk_rate = (trk_drop / trk_total * 100.0) if trk_total > 0 else 0.0
                total_hidden_drop += trk_drop
                total_hidden_dec += trk_dec
                print(f"[EVALUACION DROP HIDDEN TRACK {trk}]: drop={trk_drop}, dec={trk_dec}, tasa={trk_rate:.2f}% (umbral: <= 1.0%)")
                if trk_rate > 1.0:
                    print(f"[CRITERIO F3 FALLIDO]: tasa de drop en track {trk} ({trk_rate:.2f}%) > 1.0%.", file=sys.stderr)
                    drop_per_track_ok = False
                    f3_passed = False

        glob_total = total_hidden_dec + total_hidden_drop
        glob_rate = (total_hidden_drop / glob_total * 100.0) if glob_total > 0 else 0.0
        print(f"[EVALUACION DROP HIDDEN GLOBAL]: drop={total_hidden_drop}, dec={total_hidden_dec}, tasa={glob_rate:.2f}% (umbral: <= 1.0%)")
        if glob_rate > 1.0:
            print(f"[CRITERIO F3 FALLIDO]: tasa de drop global ({glob_rate:.2f}%) > 1.0%.", file=sys.stderr)
            f3_passed = False
        elif drop_per_track_ok:
            print(f"[CRITERIO F3 OK]: tasa de drop en hidden <= 1.0% por track y global.")

        # 9. Memoria interna heap_int >= 30000 B
        min_heap_int = min((int(r.get("heap_int", 0)) for r in perf_records if "heap_int" in r), default=0)
        print(f"[EVALUACION HEAP_INT]: minimo observado = {min_heap_int} B (umbral: >= 30000 B)")
        if min_heap_int < 30000:
            print(f"[CRITERIO F3 FALLIDO]: heap_int minimo = {min_heap_int} < 30000 B.", file=sys.stderr)
            f3_passed = False
        else:
            print(f"[CRITERIO F3 OK]: heap_int minimo = {min_heap_int} >= 30000 B.")

        print("=" * 80)
        if f3_passed:
            print("\n[RESULTADO F3]: EXITO - Todos los criterios cumplidos satisfactoriamente.")
            sys.exit(0)
        else:
            print("\n[RESULTADO F3]: FALLO - Criterios no cumplidos.", file=sys.stderr)
            sys.exit(1)

    elif args.phase.upper() == "F2":
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
