import React, { useState } from 'react';
import { Knob } from './Knob';
import { Spinner } from './Spinner';

interface ControlPanelProps {
  // Run controls
  running: boolean;
  setRunning: (val: boolean) => void;
  onSingle: () => void;
  onResetZoom: () => void;
  zoomMode: 'H' | 'V';
  setZoomMode: (mode: 'H' | 'V') => void;

  // Channels
  activeChannel: number;
  setActiveChannel: (ch: number) => void;
  chEnabled: boolean[];
  setChEnabled: (ch: number, val: boolean) => void;
  gains: number[];
  setGain: (ch: number, val: number) => void;
  offsets: number[];
  setOffset: (ch: number, val: number) => void;
  couplings: string[];
  setCoupling: (ch: number, val: string) => void;

  // Horizontal
  timebase: number;
  setTimebase: (val: number) => void;
  horizOffset: number;
  setHorizOffset: (val: number) => void;
  horizAutoMode: boolean;
  setHorizAutoMode: (val: boolean) => void;

  // Trigger
  triggerLevel: number;
  setTriggerLevel: (val: number) => void;
  triggerChannel: number;
  setTriggerChannel: (val: number) => void;
  triggerSlope: number;
  setTriggerSlope: (val: number) => void;
  triggerMode: number;
  setTriggerMode: (val: number) => void;
  triggerEnabled: boolean;
  setTriggerEnabled: (val: boolean) => void;

  // Utils
  average: number;
  setAverage: (val: number) => void;
  adcBits: number;
  setAdcBits: (val: number) => void;
  fftEnabled: boolean;
  setFftEnabled: (val: boolean) => void;
}

const gainLabels = ['X2', 'X4', 'X8', 'X16', 'X32', 'X64'];
const couplingLabels = ['AC', 'DC', 'GND'];

export const ControlPanel: React.FC<ControlPanelProps> = ({
  running,
  setRunning,
  onSingle,
  onResetZoom,
  zoomMode,
  setZoomMode,
  activeChannel,
  setActiveChannel,
  chEnabled,
  setChEnabled,
  gains,
  setGain,
  offsets,
  setOffset,
  couplings,
  setTimebase,
  timebase,
  setHorizOffset,
  horizOffset,
  horizAutoMode,
  setHorizAutoMode,
  triggerLevel,
  setTriggerLevel,
  triggerChannel,
  setTriggerChannel,
  triggerSlope,
  setTriggerSlope,
  triggerMode,
  setTriggerMode,
  triggerEnabled,
  setTriggerEnabled,
  average,
  setAverage,
  adcBits,
  setAdcBits,
  fftEnabled,
  setFftEnabled,
}) => {
  // Accordion/Collapsible sections state
  const [isTriggerOpen, setIsTriggerOpen] = useState(true);
  const [isHorizontalOpen, setIsHorizontalOpen] = useState(true);
  const [isVerticalOpen, setIsVerticalOpen] = useState(true);
  const [isUtilsOpen, setIsUtilsOpen] = useState(true);

  const getChannelColor = (ch: number) => {
    switch (ch) {
      case 0: return 'var(--ch1-color)';
      case 1: return 'var(--ch2-color)';
      case 2: return 'var(--ch3-color)';
      case 3: return 'var(--ch4-color)';
      default: return 'var(--ch1-color)';
    }
  };



  // Convert Width in ms back to Fs frequency in kHz
  const handleWidthChange = (widthMs: number) => {
    if (widthMs > 0) {
      const freqKHz = Math.round(512 / widthMs);
      const clampedVal = Math.max(10, Math.min(1000, Math.round(freqKHz / 10) * 10));
      setTimebase(clampedVal);
    }
  };

  return (
    <div className="glass-panel flex flex-col h-full overflow-hidden select-none" style={{ gap: '12px', padding: '16px' }}>
      
      {/* 1. TOP HEADER PANEL (RUN, SINGLE, RESET ZOOM) */}
      <div 
        className="grid grid-cols-2 gap-2 border-b pb-3" 
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}
      >
        {/* RUN / STOP Button */}
        <button
          onClick={() => setRunning(!running)}
          className={`col-span-2 py-2 rounded-lg font-bold text-sm cursor-pointer transition-all flex items-center justify-center gap-2 border`}
          style={{
            backgroundColor: running ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            borderColor: running ? '#22c55e' : '#ef4444',
            color: running ? '#22c55e' : '#ef4444',
            boxShadow: running ? '0 0 10px rgba(34, 197, 94, 0.2)' : 'none',
          }}
        >
          <span className="text-xs">⏻</span>
          {running ? 'RUNNING' : 'STOPPED'}
        </button>

        {/* SINGLE button */}
        <button
          onClick={onSingle}
          className="py-1.5 rounded-lg border font-bold text-xs bg-slate-800/40 border-white/10 hover:bg-slate-700/40 hover:border-white/20 transition-all text-white"
        >
          SINGLE
        </button>

        {/* RESET ZOOM button */}
        <button
          onClick={onResetZoom}
          className="py-1.5 rounded-lg border font-bold text-xs bg-slate-800/40 border-white/10 hover:bg-slate-700/40 hover:border-white/20 transition-all text-white"
        >
          RESET ZOOM
        </button>

        {/* Zoom H / V radio-like selector */}
        <div className="col-span-2 flex items-center justify-between mt-1 text-xs">
          <span className="text-slate-400">Zoom Mode:</span>
          <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5" style={{ padding: '2px' }}>
            <button
              onClick={() => setZoomMode('H')}
              className={`px-3 py-1 rounded-md font-bold text-[10px] cursor-pointer transition-all border-none`}
              style={{
                backgroundColor: zoomMode === 'H' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                color: zoomMode === 'H' ? '#ffffff' : '#64748b',
              }}
            >
              Zoom H
            </button>
            <button
              onClick={() => setZoomMode('V')}
              className={`px-3 py-1 rounded-md font-bold text-[10px] cursor-pointer transition-all border-none`}
              style={{
                backgroundColor: zoomMode === 'V' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                color: zoomMode === 'V' ? '#ffffff' : '#64748b',
              }}
            >
              Zoom V
            </button>
          </div>
        </div>
      </div>

      {/* 2. SCROLLABLE SIDEBAR SECTIONS */}
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3" style={{ minHeight: 0 }}>
        
        {/* A. TRIGGER CARD */}
        <div className="border rounded-xl p-3 bg-slate-900/20" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
          <div 
            onClick={() => setIsTriggerOpen(!isTriggerOpen)}
            className="flex justify-between items-center cursor-pointer mb-2"
          >
            <span className="text-xs font-bold tracking-wide text-slate-300">⚡ TRIGGER</span>
            <span className="text-xs text-slate-500">{isTriggerOpen ? '▼' : '▶'}</span>
          </div>

          {isTriggerOpen && (
            <div className="flex flex-col gap-2.5 mt-2 pt-2 border-t border-white/5">
              {/* Trigger Enable/Disable */}
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Status:</span>
                <button
                  onClick={() => setTriggerEnabled(!triggerEnabled)}
                  className="px-2 py-0.5 rounded text-[10px] font-bold"
                  style={{
                    backgroundColor: triggerEnabled ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: triggerEnabled ? '#10b981' : '#ef4444',
                    border: triggerEnabled ? '1px solid #10b981' : '1px solid #ef4444'
                  }}
                >
                  {triggerEnabled ? 'ENABLED' : 'DISABLED'}
                </button>
              </div>

              {/* Source Channel Select */}
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Channel:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  {[0, 1, 2, 3].map((ch) => (
                    <button
                      key={ch}
                      onClick={() => setTriggerChannel(ch)}
                      className="w-7 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                      style={{
                        backgroundColor: triggerChannel === ch ? getChannelColor(ch) : 'transparent',
                        color: triggerChannel === ch ? '#070a13' : '#64748b',
                      }}
                    >
                      CH{ch + 1}
                    </button>
                  ))}
                </div>
              </div>

              {/* Slope Selector */}
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Slope:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  <button
                    onClick={() => setTriggerSlope(0)}
                    className="px-2 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: triggerSlope === 0 ? getChannelColor(triggerChannel) : 'transparent',
                      color: triggerSlope === 0 ? '#070a13' : '#64748b',
                    }}
                  >
                    Rising
                  </button>
                  <button
                    onClick={() => setTriggerSlope(1)}
                    className="px-2 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: triggerSlope === 1 ? getChannelColor(triggerChannel) : 'transparent',
                      color: triggerSlope === 1 ? '#070a13' : '#64748b',
                    }}
                  >
                    Falling
                  </button>
                </div>
              </div>

              {/* Mode Selector */}
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Mode:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  {['AUTO', 'NORMAL', 'DISABLED'].map((m, idx) => (
                    <button
                      key={m}
                      onClick={() => setTriggerMode(idx)}
                      className="px-2 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                      style={{
                        backgroundColor: triggerMode === idx ? getChannelColor(triggerChannel) : 'transparent',
                        color: triggerMode === idx ? '#070a13' : '#64748b',
                      }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              {/* Nivel de Trigger: Dual Spinner + Knob */}
              <div className="flex items-center justify-between border-t border-white/5 pt-2 mt-1">
                <Spinner
                  value={triggerLevel}
                  min={0}
                  max={4095}
                  step={16}
                  onChange={setTriggerLevel}
                  label="Trigger Level"
                  displayValue={`${Math.round((triggerLevel / 4095) * 3300)} mV`}
                />
                <Knob
                  value={triggerLevel}
                  min={0}
                  max={4095}
                  step={16}
                  onChange={setTriggerLevel}
                  label=""
                  size={42}
                  color={getChannelColor(triggerChannel)}
                  displayValue=""
                />
              </div>
            </div>
          )}
        </div>

        {/* B. HORIZONTAL CARD */}
        <div className="border rounded-xl p-3 bg-slate-900/20" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
          <div 
            onClick={() => setIsHorizontalOpen(!isHorizontalOpen)}
            className="flex justify-between items-center cursor-pointer mb-2"
          >
            <span className="text-xs font-bold tracking-wide text-slate-300">↔️ HORIZONTAL</span>
            <span className="text-xs text-slate-500">{isHorizontalOpen ? '▼' : '▶'}</span>
          </div>

          {isHorizontalOpen && (
            <div className="flex flex-col gap-2.5 mt-2 pt-2 border-t border-white/5">
              {/* Horiz Mode: Auto / Manual */}
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Mode:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  <button
                    onClick={() => setHorizAutoMode(false)}
                    className="px-3 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: !horizAutoMode ? 'rgba(255,255,255,0.1)' : 'transparent',
                      color: !horizAutoMode ? '#ffffff' : '#64748b',
                    }}
                  >
                    Manual
                  </button>
                  <button
                    onClick={() => setHorizAutoMode(true)}
                    className="px-3 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: horizAutoMode ? 'rgba(255,255,255,0.1)' : 'transparent',
                      color: horizAutoMode ? '#ffffff' : '#64748b',
                    }}
                  >
                    Auto
                  </button>
                </div>
              </div>

              {/* Fs (Sps) Sampling Rate Spinner + Knob */}
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <Spinner
                  value={timebase}
                  min={10}
                  max={1000}
                  step={10}
                  onChange={setTimebase}
                  label="Fs (Sps / kHz)"
                  displayValue={`${timebase * 1000} Sps`}
                />
                <Knob
                  value={timebase}
                  min={10}
                  max={1000}
                  step={10}
                  onChange={setTimebase}
                  label=""
                  size={42}
                  color="var(--text-primary)"
                  displayValue=""
                />
              </div>

              {/* Width: Horizontal signal length Spinner + Knob */}
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <Spinner
                  value={Number((512 / timebase).toFixed(2))}
                  min={0.51}
                  max={51.2}
                  step={0.1}
                  onChange={handleWidthChange}
                  label="Width (Window)"
                  displayValue={`${(512 / timebase).toFixed(2)} ms`}
                />
                <Knob
                  value={Number((512 / timebase).toFixed(2))}
                  min={0.51}
                  max={51.2}
                  step={0.1}
                  onChange={handleWidthChange}
                  label=""
                  size={42}
                  color="var(--text-primary)"
                  displayValue=""
                />
              </div>

              {/* Horizontal Position X Spinner + Knob */}
              <div className="flex items-center justify-between mt-1">
                <Spinner
                  value={horizOffset}
                  min={-100}
                  max={100}
                  step={2}
                  onChange={setHorizOffset}
                  label="Position X"
                  displayValue={`${horizOffset}`}
                />
                <Knob
                  value={horizOffset}
                  min={-100}
                  max={100}
                  step={2}
                  onChange={setHorizOffset}
                  label=""
                  size={42}
                  color="var(--text-primary)"
                  displayValue=""
                />
              </div>

              {/* Real Fs Info */}
              <div className="text-[10px] text-slate-500 bg-slate-950/40 p-2 rounded-lg mt-1 border border-white/5 flex flex-col gap-1">
                <div className="flex justify-between">
                  <span>Real Fs (Sps):</span>
                  <strong className="text-slate-300">{timebase * 1000}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Max Impedance:</span>
                  <strong className="text-slate-300">73.43 Ω</strong>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* C. VERTICAL CARD (SIDE-BY-SIDE CANALES) */}
        <div className="border rounded-xl p-3 bg-slate-900/20" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
          <div 
            onClick={() => setIsVerticalOpen(!isVerticalOpen)}
            className="flex justify-between items-center cursor-pointer mb-2"
          >
            <span className="text-xs font-bold tracking-wide text-slate-300">🎛️ VERTICAL CHANNELS</span>
            <span className="text-xs text-slate-500">{isVerticalOpen ? '▼' : '▶'}</span>
          </div>

          {isVerticalOpen && (
            <div className="flex flex-col mt-2 pt-2 border-t border-white/5 gap-3">
              {/* Acoplamiento del Canal Activo */}
              <div className="flex justify-between items-center text-xs pb-1 border-b border-white/5">
                <span className="text-slate-400">CH{activeChannel + 1} Coupling:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  {couplingLabels.map((c) => (
                    <button
                      key={c}
                      onClick={() => couplings[activeChannel] !== c} // simulated change
                      className="px-2 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                      style={{
                        backgroundColor: couplings[activeChannel] === c ? getChannelColor(activeChannel) : 'transparent',
                        color: couplings[activeChannel] === c ? '#070a13' : '#64748b',
                      }}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Columnas Side-by-Side para los 4 canales */}
              <div className="flex gap-1 justify-between w-full">
                {[0, 1, 2, 3].map((ch) => {
                  const isChActive = activeChannel === ch;
                  const isChEnabled = chEnabled[ch];
                  const chColor = getChannelColor(ch);

                  return (
                    <div 
                      key={ch} 
                      onClick={() => setActiveChannel(ch)}
                      className="flex-1 flex flex-col items-center border rounded-lg p-1.5 transition-all cursor-pointer relative"
                      style={{
                        backgroundColor: isChActive ? 'rgba(255,255,255,0.02)' : 'transparent',
                        borderColor: isChActive ? chColor : 'transparent',
                        boxShadow: isChActive ? `0 0 8px ${chColor}22` : 'none',
                        minWidth: '68px',
                      }}
                    >
                      {/* Cabecera del Canal con Botón Power Integrado */}
                      <div className="flex items-center justify-between w-full border-b pb-1 mb-1.5 border-white/5">
                        <span 
                          className="text-[9px] font-bold"
                          style={{ color: isChEnabled ? chColor : '#64748b' }}
                        >
                          CH{ch + 1}
                        </span>
                        {/* Power Indicator Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation(); // Evita seleccionar canal al apagar
                            setChEnabled(ch, !isChEnabled);
                          }}
                          className="w-4.5 h-4.5 rounded flex items-center justify-center cursor-pointer transition-colors border-none"
                          style={{
                            backgroundColor: isChEnabled ? `${chColor}20` : 'rgba(255, 255, 255, 0.03)',
                            color: isChEnabled ? chColor : '#64748b',
                            fontSize: '9px',
                            boxShadow: isChEnabled ? `0 0 6px ${chColor}20` : 'none',
                            padding: 0,
                          }}
                          title={isChEnabled ? 'Apagar Canal' : 'Encender Canal'}
                        >
                          ⏻
                        </button>
                      </div>

                      {/* Gain Selector (Mini Spinner) */}
                      <div className="w-full mb-1">
                        <Spinner
                          value={gains[ch]}
                          min={0}
                          max={5}
                          step={1}
                          onChange={(val) => setGain(ch, val)}
                          displayValue={gainLabels[gains[ch]]}
                        />
                      </div>

                      {/* Offset Y (Mini Dial) */}
                      <Knob
                        value={offsets[ch]}
                        min={0}
                        max={255}
                        step={2}
                        onChange={(val) => setOffset(ch, val)}
                        label=""
                        size={32}
                        color={chColor}
                        displayValue=""
                      />
                      <span className="text-[8px] text-slate-500 mt-1 uppercase font-semibold">Offset</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* D. UTILITIES CARD */}
        <div className="border rounded-xl p-3 bg-slate-900/20 mb-2" style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}>
          <div 
            onClick={() => setIsUtilsOpen(!isUtilsOpen)}
            className="flex justify-between items-center cursor-pointer mb-2"
          >
            <span className="text-xs font-bold tracking-wide text-slate-300">⚙️ UTILITIES</span>
            <span className="text-xs text-slate-500">{isUtilsOpen ? '▼' : '▶'}</span>
          </div>

          {isUtilsOpen && (
            <div className="flex flex-col gap-3 mt-2 pt-2 border-t border-white/5">
              {/* Average Control */}
              <div className="flex items-center justify-between">
                <Spinner
                  value={average}
                  min={1}
                  max={50}
                  step={1}
                  onChange={setAverage}
                  label="Digital Average"
                  displayValue={average === 1 ? 'OFF' : `${average}x`}
                />
                <span className="text-[10px] text-slate-500 italic max-w-[80px] text-right">
                  Smooths noise traces
                </span>
              </div>

              {/* ADC Bits Resolution */}
              <div className="flex justify-between items-center text-xs border-t border-white/5 pt-2">
                <span className="text-slate-400">ADC Resolution:</span>
                <div className="flex bg-slate-950 p-0.5 rounded-lg border border-white/5">
                  <button
                    onClick={() => setAdcBits(8)}
                    className="px-2.5 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: adcBits === 8 ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                      color: adcBits === 8 ? '#ffffff' : '#64748b',
                    }}
                  >
                    8 bits
                  </button>
                  <button
                    onClick={() => setAdcBits(12)}
                    className="px-2.5 py-0.5 rounded font-bold text-[9px] border-none cursor-pointer"
                    style={{
                      backgroundColor: adcBits === 12 ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                      color: adcBits === 12 ? '#ffffff' : '#64748b',
                    }}
                  >
                    12 bits
                  </button>
                </div>
              </div>

              {/* FFT Toggle Button */}
              <button
                onClick={() => setFftEnabled(!fftEnabled)}
                className="w-full py-1.5 rounded-lg font-bold text-xs cursor-pointer border transition-all flex items-center justify-center gap-1.5 mt-1"
                style={{
                  backgroundColor: fftEnabled ? 'rgba(168, 85, 247, 0.15)' : 'rgba(15, 23, 42, 0.4)',
                  borderColor: fftEnabled ? '#a855f7' : 'rgba(255, 255, 255, 0.1)',
                  color: fftEnabled ? '#a855f7' : '#94a3b8',
                  boxShadow: fftEnabled ? '0 0 10px rgba(168, 85, 247, 0.2)' : 'none',
                }}
              >
                📊 {fftEnabled ? 'SPECTRUM FFT ACTIVE' : 'ACTIVATE FFT SPECTRAL'}
              </button>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
};
export default ControlPanel;
