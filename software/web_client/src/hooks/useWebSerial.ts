import { useState, useRef, useEffect } from 'react';
import type { ScopeData, Telemetry } from '../services/MockDataEngine';

const SYNC_BYTE = 0xAA;
const MAGIC_NUMBER = 0x55AA;
const PACKET_SIZE = 2064; // 16 header + 512 * 4 channels

export function useWebSerial(onData: (data: ScopeData) => void) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const portRef = useRef<any | null>(null);
  const readerRef = useRef<any | null>(null);
  const keepReadingRef = useRef(false);

  const connectSerial = async () => {
    setError(null);
    if (!('serial' in navigator)) {
      setError('Web Serial API no está soportada en este navegador. Usa Chrome, Edge u Opera.');
      return false;
    }

    try {
      const port = await (navigator as any).serial.requestPort();
      await port.open({ baudRate: 921600 }); // Alta velocidad para osciloscopio
      portRef.current = port;
      setConnected(true);
      keepReadingRef.current = true;
      startReading(port);
      return true;
    } catch (err: any) {
      console.error(err);
      setError('Error al abrir el puerto serie: ' + err.message);
      return false;
    }
  };

  const disconnectSerial = async () => {
    keepReadingRef.current = false;
    if (readerRef.current) {
      try {
        await readerRef.current.cancel();
      } catch (e) {}
    }
    if (portRef.current) {
      try {
        await portRef.current.close();
      } catch (e) {}
      portRef.current = null;
    }
    setConnected(false);
  };

  const sendCommand = async (cmdId: number, param1: number, data: number) => {
    if (!portRef.current || !portRef.current.writable) return;

    // Estructura de comando: 8 bytes
    // [SYNC (0xAA)][CMD_ID][PARAM1][DATA_BYTE_0][DATA_BYTE_1][DATA_BYTE_2][DATA_BYTE_3][CHECKSUM]
    const buf = new ArrayBuffer(8);
    const view = new DataView(buf);
    
    view.setUint8(0, SYNC_BYTE);
    view.setUint8(1, cmdId);
    view.setUint8(2, param1);
    view.setUint32(3, data, true); // Little endian

    // Checksum = suma de los primeros 7 bytes
    let checksum = 0;
    for (let i = 0; i < 7; i++) {
      checksum += view.getUint8(i);
    }
    view.setUint8(7, checksum & 0xFF);

    const writer = portRef.current.writable.getWriter();
    try {
      await writer.write(new Uint8Array(buf));
    } catch (err) {
      console.error('Error al enviar comando serial:', err);
    } finally {
      writer.releaseLock();
    }
  };

  const startReading = async (port: any) => {
    let rxBuffer = new Uint8Array(PACKET_SIZE * 2);
    let rxLen = 0;

    while (port.readable && keepReadingRef.current) {
      try {
        const reader = port.readable.getReader();
        readerRef.current = reader;

        while (keepReadingRef.current) {
          const { value, done } = await reader.read();
          if (done) break;

          if (value) {
            // Asegurar que no desborde el buffer de acumulación
            if (rxLen + value.length > rxBuffer.length) {
              // Si desborda, desplazar o reiniciar
              rxLen = 0;
            }
            rxBuffer.set(value, rxLen);
            rxLen += value.length;

            // Buscar cabecera 0x55AA (Magic Number) en los datos acumulados
            while (rxLen >= PACKET_SIZE) {
              let headerIndex = -1;
              for (let i = 0; i <= rxLen - 2; i++) {
                const magic = (rxBuffer[i + 1] << 8) | rxBuffer[i];
                if (magic === MAGIC_NUMBER) {
                  headerIndex = i;
                  break;
                }
              }

              if (headerIndex === -1) {
                // Si no se encuentra el Magic Number, descartar todo menos el último byte
                rxBuffer[0] = rxBuffer[rxLen - 1];
                rxLen = 1;
                break;
              }

              if (headerIndex > 0) {
                // Descartar bytes basura anteriores a la cabecera
                rxBuffer.copyWithin(0, headerIndex, rxLen);
                rxLen -= headerIndex;
                headerIndex = 0;
              }

              // ¿Tenemos un paquete completo?
              if (rxLen >= PACKET_SIZE) {
                const packet = rxBuffer.slice(0, PACKET_SIZE);
                parseTelemetryPacket(packet);

                // Desplazar el resto del buffer hacia el inicio
                rxBuffer.copyWithin(0, PACKET_SIZE, rxLen);
                rxLen -= PACKET_SIZE;
              } else {
                break;
              }
            }
          }
        }
        reader.releaseLock();
      } catch (err) {
        console.error('Error de lectura serial:', err);
        break;
      }
    }
  };

  const parseTelemetryPacket = (data: Uint8Array) => {
    const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
    
    // Parsear la cabecera de 16 bytes
    // uint16_t magic_number (0-1)
    // uint16_t vpp (2-3)
    // uint16_t vrms (4-5)
    // uint16_t vavg (6-7)
    // uint32_t frequency (8-11)
    // uint8_t duty_cycle (12)
    // uint8_t gain_state (13)
    // uint16_t padding (14-15)
    const magic = view.getUint16(0, true);
    if (magic !== MAGIC_NUMBER) return;

    const telemetry: Telemetry = {
      vpp: view.getUint16(2, true),
      vrms: view.getUint16(4, true),
      vavg: view.getUint16(6, true),
      frequency: view.getUint32(8, true),
      dutyCycle: view.getUint8(12),
      gainState: view.getUint8(13),
    };

    // Extraer buffers decimados de los 4 canales (512 muestras de 8 bits cada uno)
    const ch1 = data.slice(16, 16 + 512);
    const ch2 = data.slice(16 + 512, 16 + 1024);
    const ch3 = data.slice(16 + 1024, 16 + 1536);
    const ch4 = data.slice(16 + 1536, 16 + 2048);

    onData({ ch1, ch2, ch3, ch4, telemetry });
  };

  useEffect(() => {
    return () => {
      disconnectSerial();
    };
  }, []);

  return {
    connected,
    error,
    connectSerial,
    disconnectSerial,
    sendCommand,
  };
}
