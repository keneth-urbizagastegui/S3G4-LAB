import React, { useRef, useEffect } from 'react';
import type { ScopeData } from '../services/MockDataEngine';

// Helper to convert 8-bit raw sample to mV
function calculateMilliVolts(val8Bit: number, scale: number): number {
  const counts = val8Bit << 4;
  const shift = scale + 13;
  return Math.round((counts * 3300) / Math.pow(2, shift));
}

// Cooley-Tukey FFT implementation for real-time spectrum analysis
function computeFFT(samples: Uint8Array): number[] {
  const N = samples.length; // 512
  const log2N = Math.log2(N);
  
  const real = new Float32Array(N);
  const imag = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    // Normalize to range -1.0 to 1.0
    real[i] = (samples[i] - 127.5) / 127.5;
  }

  // Bit reversal
  const reverseBits = (x: number, bits: number) => {
    let y = 0;
    let temp = x;
    for (let i = 0; i < bits; i++) {
      y = (y << 1) | (temp & 1);
      temp >>= 1;
    }
    return y;
  };

  const rReal = new Float32Array(N);
  const rImag = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const rev = reverseBits(i, log2N);
    rReal[rev] = real[i];
    rImag[rev] = imag[i];
  }

  // FFT calculation
  for (let size = 2; size <= N; size <<= 1) {
    const halfSize = size >> 1;
    for (let i = 0; i < N; i += size) {
      for (let j = 0; j < halfSize; j++) {
        const k = i + j;
        const l = k + halfSize;
        const angle = (-2 * Math.PI * j) / size;
        const wReal = Math.cos(angle);
        const wImag = Math.sin(angle);
        
        const tReal = rReal[l] * wReal - rImag[l] * wImag;
        const tImag = rReal[l] * wImag + rImag[l] * wReal;
        
        rReal[l] = rReal[k] - tReal;
        rImag[l] = rImag[k] - tImag;
        rReal[k] += tReal;
        rImag[k] += tImag;
      }
    }
  }

  const magnitudes: number[] = [];
  for (let i = 0; i < N / 2; i++) {
    const mag = Math.sqrt(rReal[i] * rReal[i] + rImag[i] * rImag[i]);
    magnitudes.push(mag);
  }
  return magnitudes;
}

interface OscilloscopeCanvasProps {
  data: ScopeData | null;
  ch1Enabled: boolean;
  ch2Enabled: boolean;
  ch3Enabled: boolean;
  ch4Enabled: boolean;
  offsets: number[];
  triggerLevel: number;
  triggerChannel: number;
  triggerEnabled: boolean;
  
  // Cursors
  activeChannel: number;
  gains: number[];
  timebase: number;
  cursorsVEnabled: boolean;
  cursorsHEnabled: boolean;
  cursorV1: number;
  setCursorV1: (val: number) => void;
  cursorV2: number;
  setCursorV2: (val: number) => void;
  cursorH1: number;
  setCursorH1: (val: number) => void;
  cursorH2: number;
  setCursorH2: (val: number) => void;
  fftEnabled: boolean;
}

export const OscilloscopeCanvas: React.FC<OscilloscopeCanvasProps> = ({
  data,
  ch1Enabled,
  ch2Enabled,
  ch3Enabled,
  ch4Enabled,
  offsets,
  triggerLevel,
  triggerChannel,
  triggerEnabled,
  activeChannel,
  gains,
  timebase,
  cursorsVEnabled,
  cursorsHEnabled,
  cursorV1,
  setCursorV1,
  cursorV2,
  setCursorV2,
  cursorH1,
  setCursorH1,
  cursorH2,
  setCursorH2,
  fftEnabled,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const draggingRef = useRef<'V1' | 'V2' | 'H1' | 'H2' | null>(null);

  // Convert coordinate from screen client to internal canvas coords
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    
    let clientX = 0;
    let clientY = 0;
    
    if ('touches' in e) {
      if (e.touches.length === 0) return null;
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }
    
    const x = ((clientX - rect.left) / rect.width) * canvas.width;
    const y = ((clientY - rect.top) / rect.height) * canvas.height;
    
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    if (!coords) return;
    const { x, y } = coords;
    
    const width = 800;
    const height = 450;
    const hScope = fftEnabled ? height / 2 - 15 : height;
    
    let detected: 'V1' | 'V2' | 'H1' | 'H2' | null = null;
    let minDist = 15; // px tolerance
    
    if (cursorsVEnabled) {
      const xV1 = cursorV1 * width;
      const xV2 = cursorV2 * width;
      if (Math.abs(x - xV1) < minDist) {
        detected = 'V1';
        minDist = Math.abs(x - xV1);
      }
      if (Math.abs(x - xV2) < minDist) {
        detected = 'V2';
        minDist = Math.abs(x - xV2);
      }
    }
    
    if (cursorsHEnabled) {
      const yH1 = cursorH1 * hScope;
      const yH2 = cursorH2 * hScope;
      if (Math.abs(y - yH1) < minDist) {
        detected = 'H1';
        minDist = Math.abs(y - yH1);
      }
      if (Math.abs(y - yH2) < minDist) {
        detected = 'H2';
        minDist = Math.abs(y - yH2);
      }
    }
    
    if (detected) {
      draggingRef.current = detected;
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const coords = getCanvasCoords(e);
    if (!coords) return;
    const { x, y } = coords;
    
    const width = 800;
    const height = 450;
    const hScope = fftEnabled ? height / 2 - 15 : height;
    
    if (draggingRef.current) {
      const val = draggingRef.current;
      if (val === 'V1') {
        setCursorV1(Math.max(0, Math.min(1, x / width)));
      } else if (val === 'V2') {
        setCursorV2(Math.max(0, Math.min(1, x / width)));
      } else if (val === 'H1') {
        setCursorH1(Math.max(0, Math.min(1, y / hScope)));
      } else if (val === 'H2') {
        setCursorH2(Math.max(0, Math.min(1, y / hScope)));
      }
      e.preventDefault();
      return;
    }
    
    // Change cursor appearance based on hover proximity
    let nearCursor = false;
    let cursorType = 'default';
    const tolerance = 10;
    
    if (cursorsVEnabled) {
      const xV1 = cursorV1 * width;
      const xV2 = cursorV2 * width;
      if (Math.abs(x - xV1) < tolerance || Math.abs(x - xV2) < tolerance) {
        nearCursor = true;
        cursorType = 'col-resize';
      }
    }
    
    if (cursorsHEnabled) {
      const yH1 = cursorH1 * hScope;
      const yH2 = cursorH2 * hScope;
      if (Math.abs(y - yH1) < tolerance || Math.abs(y - yH2) < tolerance) {
        nearCursor = true;
        cursorType = 'row-resize';
      }
    }
    
    canvas.style.cursor = nearCursor ? cursorType : 'default';
  };

  const handleMouseUp = () => {
    draggingRef.current = null;
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    if (!coords) return;
    const { x, y } = coords;
    
    const width = 800;
    const height = 450;
    const hScope = fftEnabled ? height / 2 - 15 : height;
    
    let detected: 'V1' | 'V2' | 'H1' | 'H2' | null = null;
    let minDist = 25; // larger tolerance for touch
    
    if (cursorsVEnabled) {
      const xV1 = cursorV1 * width;
      const xV2 = cursorV2 * width;
      if (Math.abs(x - xV1) < minDist) {
        detected = 'V1';
        minDist = Math.abs(x - xV1);
      }
      if (Math.abs(x - xV2) < minDist) {
        detected = 'V2';
        minDist = Math.abs(x - xV2);
      }
    }
    
    if (cursorsHEnabled) {
      const yH1 = cursorH1 * hScope;
      const yH2 = cursorH2 * hScope;
      if (Math.abs(y - yH1) < minDist) {
        detected = 'H1';
        minDist = Math.abs(y - yH1);
      }
      if (Math.abs(y - yH2) < minDist) {
        detected = 'H2';
        minDist = Math.abs(y - yH2);
      }
    }
    
    if (detected) {
      draggingRef.current = detected;
      e.preventDefault();
    }
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLCanvasElement>) => {
    if (!draggingRef.current) return;
    const coords = getCanvasCoords(e);
    if (!coords) return;
    const { x, y } = coords;
    
    const width = 800;
    const height = 450;
    const hScope = fftEnabled ? height / 2 - 15 : height;
    
    const val = draggingRef.current;
    if (val === 'V1') {
      setCursorV1(Math.max(0, Math.min(1, x / width)));
    } else if (val === 'V2') {
      setCursorV2(Math.max(0, Math.min(1, x / width)));
    } else if (val === 'H1') {
      setCursorH1(Math.max(0, Math.min(1, y / hScope)));
    } else if (val === 'H2') {
      setCursorH2(Math.max(0, Math.min(1, y / hScope)));
    }
    e.preventDefault();
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Draw main black background
    ctx.fillStyle = '#060913';
    ctx.fillRect(0, 0, width, height);

    // Compute layout vertical partitions
    const hScope = fftEnabled ? height / 2 - 15 : height;

    // 1. DRAW GRID
    ctx.lineWidth = 1;
    
    // Vertical Grid Lines (10 columns)
    const colStep = width / 10;
    for (let i = 1; i < 10; i++) {
      ctx.beginPath();
      ctx.strokeStyle = i === 5 ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)';
      ctx.moveTo(i * colStep, 0);
      ctx.lineTo(i * colStep, hScope);
      ctx.stroke();
    }

    // Horizontal Grid Lines (8 divisions)
    const rowStep = hScope / 8;
    for (let j = 1; j < 8; j++) {
      ctx.beginPath();
      ctx.strokeStyle = j === 4 ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)';
      ctx.moveTo(0, j * rowStep);
      ctx.lineTo(width, j * rowStep);
      ctx.stroke();
    }

    // Small ticks along center axes of upper/scope screen
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    const centerX = width / 2;
    const centerY = hScope / 2;
    
    for (let x = 0; x < width; x += colStep / 5) {
      ctx.beginPath();
      ctx.moveTo(x, centerY - 3);
      ctx.lineTo(x, centerY + 3);
      ctx.stroke();
    }
    for (let y = 0; y < hScope; y += rowStep / 5) {
      ctx.beginPath();
      ctx.moveTo(centerX - 3, y);
      ctx.lineTo(centerX + 3, y);
      ctx.stroke();
    }

    // If FFT mode is active, draw the FFT screen split and divider
    if (fftEnabled) {
      // Draw Divider Panel
      ctx.fillStyle = '#0a0f1d';
      ctx.fillRect(0, 210, width, 30);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.fillRect(0, 224, width, 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
      ctx.font = 'bold 9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('FREQUENCY SPECTRUM (FFT ANALYSIS)', width / 2, 237);
      ctx.textAlign = 'left';

      // Draw FFT Grid (Lower Half from Y: 240 to 450)
      const fftYBase = 240;
      const fftHeight = 210;
      const rowStepFFT = fftHeight / 4;
      
      // Horizontal FFT lines
      for (let j = 1; j < 4; j++) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.moveTo(0, fftYBase + j * rowStepFFT);
        ctx.lineTo(width, fftYBase + j * rowStepFFT);
        ctx.stroke();
      }

      // Vertical FFT lines
      for (let i = 1; i < 10; i++) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.moveTo(i * colStep, fftYBase);
        ctx.lineTo(i * colStep, height);
        ctx.stroke();
      }
    }

    // If no signal telemetry is connected, exit drawing
    if (!data) return;

    // 2. DRAW WAVEFORMS
    const drawTrace = (traceData: Uint8Array, color: string, glowColor: string) => {
      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.0;
      
      // GPU neon glow effects
      ctx.shadowBlur = 6;
      ctx.shadowColor = glowColor;

      const samples = traceData.length;
      const xStep = width / (samples - 1);

      for (let i = 0; i < samples; i++) {
        const val = traceData[i];
        // Scale vertical mapping depending on whether FFT mode is split screen
        const y = (1.0 - val / 255) * hScope;

        if (i === 0) {
          ctx.moveTo(0, y);
        } else {
          ctx.lineTo(i * xStep, y);
        }
      }
      ctx.stroke();
      ctx.restore();
    };

    if (ch1Enabled) drawTrace(data.ch1, '#00f0ff', '#00f0ff');
    if (ch2Enabled) drawTrace(data.ch2, '#ffe600', '#ffe600');
    if (ch3Enabled) drawTrace(data.ch3, '#ff007f', '#ff007f');
    if (ch4Enabled) drawTrace(data.ch4, '#39ff14', '#39ff14');

    // 3. DRAW GROUND MARKERS
    const drawGroundMarker = (offset8Bit: number, color: string, label: string) => {
      const y = (1.0 - offset8Bit / 255) * hScope;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(2, y);
      ctx.lineTo(12, y - 5);
      ctx.lineTo(12, y + 5);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = '#060913';
      ctx.font = 'bold 8px sans-serif';
      ctx.fillText(label, 6, y + 3);
    };

    if (ch1Enabled) drawGroundMarker(offsets[0], '#00f0ff', '1');
    if (ch2Enabled) drawGroundMarker(offsets[1], '#ffe600', '2');
    if (ch3Enabled) drawGroundMarker(offsets[2], '#ff007f', '3');
    if (ch4Enabled) drawGroundMarker(offsets[3], '#39ff14', '4');

    // 4. DRAW TRIGGER LEVEL LINE
    if (triggerEnabled) {
      const trigVal8 = triggerLevel >> 4; // 12-bit to 8-bit
      const trigY = (1.0 - trigVal8 / 255) * hScope;

      ctx.save();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, trigY);
      ctx.lineTo(width, trigY);
      ctx.stroke();

      // Trigger indicator arrow
      ctx.fillStyle = 'rgba(255, 255, 255, 0.55)';
      ctx.beginPath();
      ctx.moveTo(width - 2, trigY);
      ctx.lineTo(width - 12, trigY - 5);
      ctx.lineTo(width - 12, trigY + 5);
      ctx.closePath();
      ctx.fill();

      ctx.font = 'bold 8px sans-serif';
      ctx.fillStyle = '#060913';
      ctx.fillText('T', width - 10, trigY + 3);
      ctx.restore();
    }

    // 5. RENDER REAL-TIME FFT SPECTRUM
    if (fftEnabled) {
      const activeBuffer =
        activeChannel === 0
          ? data.ch1
          : activeChannel === 1
          ? data.ch2
          : activeChannel === 2
          ? data.ch3
          : data.ch4;

      const fftData = computeFFT(activeBuffer);
      const fftLen = fftData.length;
      const xStepFFT = width / (fftLen - 1);

      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = '#a855f7'; // Purple neon trace for frequency spectrum
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 5;
      ctx.shadowColor = '#a855f7';

      for (let i = 0; i < fftLen; i++) {
        // Add minimal noise floor to make it look like a live spectrum analyzer
        const mag = fftData[i] + (Math.random() - 0.5) * 0.05;
        const y = 450 - Math.min(195, Math.max(0, mag * 42));

        if (i === 0) {
          ctx.moveTo(0, y);
        } else {
          ctx.lineTo(i * xStepFFT, y);
        }
      }
      ctx.stroke();
      ctx.restore();

      // Draw Frequency Labels on FFT axis
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '9px monospace';
      ctx.fillText('0 Hz', 5, 442);
      ctx.fillText(`${(timebase / 4).toFixed(1)} kHz`, colStep * 2.5 - 20, 442);
      ctx.fillText(`${(timebase / 2).toFixed(1)} kHz`, colStep * 5 - 20, 442);
      ctx.fillText(`${(timebase * 3 / 4).toFixed(1)} kHz`, colStep * 7.5 - 20, 442);
      ctx.fillText(`${timebase.toFixed(1)} kHz`, width - 60, 442);
    }

    // 6. DRAW INTERACTIVE CURSORS
    // Vertical Cursors (Time Axis)
    if (cursorsVEnabled) {
      const xV1 = cursorV1 * width;
      const xV2 = cursorV2 * width;
      const totalTimeMs = 512 / timebase; // sample rate dependent

      // V1 Line
      ctx.save();
      ctx.strokeStyle = '#eab308'; // Orange/yellow
      ctx.lineWidth = 1.2;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(xV1, 0);
      ctx.lineTo(xV1, hScope);
      ctx.stroke();

      // V2 Line
      ctx.beginPath();
      ctx.moveTo(xV2, 0);
      ctx.lineTo(xV2, hScope);
      ctx.stroke();
      ctx.restore();

      // Calculate time metrics
      const t1 = cursorV1 * totalTimeMs;
      const t2 = cursorV2 * totalTimeMs;
      const dt = Math.abs(t2 - t1);
      const df = dt > 0 ? 1000 / dt : 0; // dt in ms, df in Hz

      const formatTime = (time: number) => {
        if (time < 1.0) {
          return `${(time * 1000).toFixed(1)} us`;
        }
        return `${time.toFixed(3)} ms`;
      };

      const formatFreq = (freq: number) => {
        if (freq < 1000) {
          return `${freq.toFixed(1)} Hz`;
        }
        return `${(freq / 1000).toFixed(3)} kHz`;
      };

      // Draw V1/V2 labels on the lines
      ctx.font = 'bold 9px monospace';
      ctx.fillStyle = '#eab308';
      
      ctx.fillText(formatTime(t1), xV1 + 4, 15);
      ctx.fillText(formatTime(t2), xV2 + 4, 15);

      // Draw cota/delta indicators
      const midXV = (xV1 + xV2) / 2;
      const textY = hScope - 25;

      // Draw delta background box
      ctx.fillStyle = 'rgba(7, 10, 19, 0.85)';
      ctx.strokeStyle = '#eab308';
      ctx.lineWidth = 1;
      ctx.fillRect(midXV - 50, textY - 24, 100, 32);
      ctx.strokeRect(midXV - 50, textY - 24, 100, 32);

      // Draw delta text
      ctx.fillStyle = '#eab308';
      ctx.textAlign = 'center';
      ctx.fillText(`Δ ${formatTime(dt)}`, midXV, textY - 14);
      ctx.fillText(`f ${formatFreq(df)}`, midXV, textY - 3);
      ctx.textAlign = 'left';

      // Draw horizontal distance arrow line
      ctx.strokeStyle = '#eab308';
      ctx.beginPath();
      ctx.moveTo(xV1, textY - 8);
      ctx.lineTo(xV2, textY - 8);
      ctx.stroke();

      // Arrows
      ctx.fillStyle = '#eab308';
      ctx.beginPath();
      ctx.moveTo(xV1, textY - 8);
      ctx.lineTo(xV1 + (xV2 > xV1 ? 6 : -6), textY - 11);
      ctx.lineTo(xV1 + (xV2 > xV1 ? 6 : -6), textY - 5);
      ctx.closePath();
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(xV2, textY - 8);
      ctx.lineTo(xV2 - (xV2 > xV1 ? 6 : -6), textY - 11);
      ctx.lineTo(xV2 - (xV2 > xV1 ? 6 : -6), textY - 5);
      ctx.closePath();
      ctx.fill();
    }

    // Horizontal Cursors (Voltage Axis)
    if (cursorsHEnabled) {
      const yH1 = cursorH1 * hScope;
      const yH2 = cursorH2 * hScope;
      const activeScale = gains[activeChannel];

      // H1 Line
      ctx.save();
      ctx.strokeStyle = '#a855f7'; // Purple/Violet
      ctx.lineWidth = 1.2;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(0, yH1);
      ctx.lineTo(width, yH1);
      ctx.stroke();

      // H2 Line
      ctx.beginPath();
      ctx.moveTo(0, yH2);
      ctx.lineTo(width, yH2);
      ctx.stroke();
      ctx.restore();

      // Calculate voltage metrics
      const getVolts = (fraction: number) => {
        const val8 = (1.0 - fraction) * 255;
        const mv = calculateMilliVolts(val8, activeScale);
        return mv / 1000;
      };

      const v1 = getVolts(cursorH1);
      const v2 = getVolts(cursorH2);
      const dv = Math.abs(v2 - v1);

      // Draw H1/H2 labels on screen
      ctx.font = 'bold 9px monospace';
      ctx.fillStyle = '#a855f7';

      ctx.fillText(`${v1.toFixed(3)} V`, 20, yH1 - 4);
      ctx.fillText(`${v2.toFixed(3)} V`, 20, yH2 - 4);

      // Draw vertical cota indicator
      const midYH = (yH1 + yH2) / 2;
      const textX = width - 110;

      // Box
      ctx.fillStyle = 'rgba(7, 10, 19, 0.85)';
      ctx.strokeStyle = '#a855f7';
      ctx.lineWidth = 1;
      ctx.fillRect(textX, midYH - 10, 80, 18);
      ctx.strokeRect(textX, midYH - 10, 80, 18);

      // Label
      ctx.fillStyle = '#a855f7';
      ctx.textAlign = 'center';
      ctx.fillText(`Δ ${dv.toFixed(3)} V`, textX + 40, midYH + 2);
      ctx.textAlign = 'left';

      // Vertical line
      ctx.strokeStyle = '#a855f7';
      ctx.beginPath();
      ctx.moveTo(textX + 40, yH1);
      ctx.lineTo(textX + 40, yH2);
      ctx.stroke();

      // Arrows
      ctx.fillStyle = '#a855f7';
      ctx.beginPath();
      ctx.moveTo(textX + 40, yH1);
      ctx.lineTo(textX + 37, yH1 + (yH2 > yH1 ? 6 : -6));
      ctx.lineTo(textX + 43, yH1 + (yH2 > yH1 ? 6 : -6));
      ctx.closePath();
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(textX + 40, yH2);
      ctx.lineTo(textX + 37, yH2 - (yH2 > yH1 ? 6 : -6));
      ctx.lineTo(textX + 43, yH2 - (yH2 > yH1 ? 6 : -6));
      ctx.closePath();
      ctx.fill();
    }

  }, [
    data,
    ch1Enabled,
    ch2Enabled,
    ch3Enabled,
    ch4Enabled,
    offsets,
    triggerLevel,
    triggerChannel,
    triggerEnabled,
    activeChannel,
    gains,
    timebase,
    cursorsVEnabled,
    cursorsHEnabled,
    cursorV1,
    cursorV2,
    cursorH1,
    cursorH2,
    fftEnabled,
  ]);

  return (
    <div 
      className="relative w-full rounded-2xl overflow-hidden border"
      style={{ 
        borderColor: 'rgba(255,255,255,0.08)',
        boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
        aspectRatio: '16/9'
      }}
    >
      <canvas 
        ref={canvasRef} 
        width={800} 
        height={450} 
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleMouseUp}
        style={{ 
          width: '100%', 
          height: '100%', 
          display: 'block' 
        }} 
      />
    </div>
  );
};

export default OscilloscopeCanvas;
