import { useState, useRef, useEffect } from 'react';
import type { ScopeData, Telemetry } from '../services/MockDataEngine';

const SYNC_BYTE = 0xAA;
const MAGIC_NUMBER = 0x55AA;
const PACKET_SIZE = 2064;

export function useWebSockets(onData: (data: ScopeData) => void) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const connectWebSocket = (ipAddress: string) => {
    setError(null);
    if (!ipAddress) {
      setError('Por favor ingresa una dirección IP válida.');
      return false;
    }

    try {
      if (socketRef.current) {
        socketRef.current.close();
      }

      const wsUrl = `ws://${ipAddress}/ws`;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      socketRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
      };

      ws.onclose = () => {
        setConnected(false);
      };

      ws.onerror = (err) => {
        console.error('Error en WebSocket:', err);
        setError('Error de conexión con el dispositivo. Verifica la IP y la red.');
        setConnected(false);
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          if (event.data.byteLength === PACKET_SIZE) {
            parseTelemetryPacket(new Uint8Array(event.data));
          }
        }
      };

      return true;
    } catch (err: any) {
      console.error(err);
      setError('No se pudo establecer la conexión: ' + err.message);
      return false;
    }
  };

  const disconnectWebSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setConnected(false);
  };

  const sendCommand = (cmdId: number, param1: number, data: number) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;

    // Estructura de comando: 8 bytes
    const buf = new ArrayBuffer(8);
    const view = new DataView(buf);
    
    view.setUint8(0, SYNC_BYTE);
    view.setUint8(1, cmdId);
    view.setUint8(2, param1);
    view.setUint32(3, data, true); // Little endian

    // Checksum
    let checksum = 0;
    for (let i = 0; i < 7; i++) {
      checksum += view.getUint8(i);
    }
    view.setUint8(7, checksum & 0xFF);

    try {
      socketRef.current.send(buf);
    } catch (err) {
      console.error('Error al enviar comando por WebSocket:', err);
    }
  };

  const parseTelemetryPacket = (data: Uint8Array) => {
    const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
    
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

    // Extraer buffers decimados de los 4 canales
    const ch1 = data.slice(16, 16 + 512);
    const ch2 = data.slice(16 + 512, 16 + 1024);
    const ch3 = data.slice(16 + 1024, 16 + 1536);
    const ch4 = data.slice(16 + 1536, 16 + 2048);

    onData({ ch1, ch2, ch3, ch4, telemetry });
  };

  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, []);

  return {
    connected,
    error,
    connectWebSocket,
    disconnectWebSocket,
    sendCommand,
  };
}
