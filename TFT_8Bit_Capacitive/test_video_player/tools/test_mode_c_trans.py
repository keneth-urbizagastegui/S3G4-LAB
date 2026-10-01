#!/usr/bin/env python3
"""
tools/test_mode_c_trans.py
Prueba de transicion dinamica:
1. Monitoreo previo en modo OFF (10 s).
2. Activacion de Modo C (patron rojo/azul) durante 12 s.
3. Retorno a Modo OFF durante 35 s.
Verifica que te_wait_ms_avg se mantiene coherente, pres_fps se mantiene a ~30 fps
y no hay caida de sincronismo ni acumulacion de descartes.
"""

import sys
import os
import time
import re
import serial

def main():
    port = "COM16"
    baud = 115200
    out_file = r"plan_antigravity\mediciones\F5d_mode_c_test.log"
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    log_fp = open(out_file, "w", encoding="utf-8", errors="replace")

    def log_print(msg):
        print(msg)
        log_fp.write(msg + "\n")
        log_fp.flush()

    log_print(f"Abriendo {port} a {baud}...")
    ser = serial.Serial(port, baud, timeout=0.5)
    ser.dtr = False
    ser.rts = False

    log_print("Fase 1: Monitoreo previo en modo OFF (10 s)...")
    t0 = time.time()
    pre_te_waits = []
    pre_fps = []
    while time.time() - t0 < 10.0:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            log_fp.write(f"[PRE] {line}\n")
            m_te = re.search(r"te_wait_ms_avg=([0-9.]+)", line)
            if m_te: pre_te_waits.append(float(m_te.group(1)))
            m_fps = re.search(r"pres_fps=([0-9.]+)", line)
            if m_fps: pre_fps.append(float(m_fps.group(1)))

    log_print(f"Pre-C: te_wait_avg = {sum(pre_te_waits)/len(pre_te_waits) if pre_te_waits else 0:.2f} ms | pres_fps = {sum(pre_fps)/len(pre_fps) if pre_fps else 0:.2f}")

    log_print("Fase 2: Enviando DIAG C...")
    ser.write(b"DIAG C\r\n")
    time.sleep(0.5)

    t_c = time.time()
    c_te_waits = []
    while time.time() - t_c < 12.0:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            log_fp.write(f"[MODE_C] {line}\n")
            m_te = re.search(r"te_wait_ms_avg=([0-9.]+)", line)
            if m_te: c_te_waits.append(float(m_te.group(1)))

    log_print(f"En Modo C: te_wait_avg = {sum(c_te_waits)/len(c_te_waits) if c_te_waits else 0:.2f} ms")

    log_print("Fase 3: Enviando DIAG OFF (retorno a normal, monitoreo 35 s)...")
    ser.write(b"DIAG OFF\r\n")
    time.sleep(0.5)

    t_off = time.time()
    post_te_waits = []
    post_fps = []
    post_drops = []
    while time.time() - t_off < 35.0:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            log_fp.write(f"[POST] {line}\n")
            m_te = re.search(r"te_wait_ms_avg=([0-9.]+)", line)
            if m_te: post_te_waits.append(float(m_te.group(1)))
            m_fps = re.search(r"pres_fps=([0-9.]+)", line)
            if m_fps: post_fps.append(float(m_fps.group(1)))
            m_d = re.search(r"drop=(\d+)", line)
            if m_d: post_drops.append(int(m_d.group(1)))

    ser.close()

    avg_post_te = sum(post_te_waits)/len(post_te_waits) if post_te_waits else 0
    avg_post_fps = sum(post_fps)/len(post_fps) if post_fps else 0
    tot_drops = sum(post_drops)

    log_print("\n================================================================")
    log_print("RESUMEN DE PRUEBA TRANSICION MODO C -> MODO OFF")
    log_print("================================================================")
    log_print(f"te_wait_ms_avg antes de Modo C: {sum(pre_te_waits)/len(pre_te_waits) if pre_te_waits else 0:.2f} ms")
    log_print(f"te_wait_ms_avg durante Modo C:  {sum(c_te_waits)/len(c_te_waits) if c_te_waits else 0:.2f} ms")
    log_print(f"te_wait_ms_avg despues de Modo C (35s): {avg_post_te:.2f} ms")
    log_print(f"pres_fps despues de Modo C: {avg_post_fps:.2f} FPS")
    log_print(f"Total descartes en 35 s post-Modo C: {tot_drops}")
    log_print("================================================================")

    log_fp.close()

if __name__ == "__main__":
    main()
