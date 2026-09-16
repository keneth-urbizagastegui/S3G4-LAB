#!/usr/bin/env python3
"""
tools/tear_diag.py
Controlador serial para los modos de diagnostico de tearing (T2) en ESP32-S3.
Permite alternar entre los modos sin recompilar:
  - Modo A: Medio fotograma (solo 160 lineas superiores, ~10.1 ms)
  - Modo B: Franja unica (16 lineas fijas, ~1.0 ms)
  - Modo C: Patron de prueba sin video (rojo/azul a 30 Hz con TE ON)
  - Modo OFF: Reproduccion normal de video
"""

import sys
import time
import argparse

try:
    import serial
except ImportError:
    print("Error: modulo 'pyserial' no encontrado. Instalar con 'pip install pyserial'.", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Control de diagnostico de tearing ESP32-S3")
    parser.add_argument("--port", default="COM16", help="Puerto serial (default: COM16)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    parser.add_argument("--mode", required=True, choices=["A", "a", "B", "b", "C", "c", "OFF", "off", "0", "?"],
                        help="Modo: A (medio fotograma), B (franja unica), C (rojo/azul 30Hz), OFF (normal), ? (consultar)")
    args = parser.parse_args()

    mode_str = args.mode.upper()
    if mode_str == "0":
        mode_str = "OFF"

    cmd = f"DIAG {mode_str}\n"

    try:
        # Abrir sin toggling DTR/RTS para NO reiniciar la placa
        ser = serial.Serial()
        ser.port = args.port
        ser.baudrate = args.baud
        ser.timeout = 2.0
        ser.dtr = False
        ser.rts = False
        ser.open()
    except Exception as e:
        print(f"Error al abrir puerto serial {args.port}: {e}", file=sys.stderr)
        sys.exit(2)

    time.sleep(0.1)
    ser.reset_input_buffer()
    ser.write(cmd.encode("utf-8"))
    ser.flush()

    # Esperar respuesta DIAG_MODE
    t0 = time.time()
    confirmed = False
    resp_text = ""
    while (time.time() - t0) < 2.0:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            if "DIAG_MODE," in line:
                print(f"[ESP32]: {line}")
                confirmed = True
                resp_text = line
                break

    ser.close()

    if confirmed:
        print(f"Modo de diagnostico configurado con exito: {mode_str}")
        sys.exit(0)
    else:
        print(f"Aviso: no se recibio confirmacion de la placa en 2 segundos. Verifica que el firmware este activo en {args.port}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
