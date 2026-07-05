import React from 'react';

interface SpinnerProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  label?: string;
  displayValue?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  value,
  min,
  max,
  step = 1,
  onChange,
  label,
  displayValue,
}) => {
  const handleIncrement = () => {
    const newVal = Math.min(max, value + step);
    onChange(newVal);
  };

  const handleDecrement = () => {
    const newVal = Math.max(min, value - step);
    onChange(newVal);
  };

  return (
    <div className="flex flex-col select-none" style={{ margin: '4px 0' }}>
      {label && (
        <span className="text-[10px] font-semibold mb-1 uppercase tracking-wider text-slate-400">
          {label}
        </span>
      )}
      <div className="flex items-stretch bg-slate-950/80 border border-white/10 rounded-lg overflow-hidden" style={{ height: '32px' }}>
        {/* Valor */}
        <div
          className="flex-1 font-mono text-xs font-bold flex items-center justify-center px-3 min-w-[70px]"
          style={{ color: 'var(--text-primary)' }}
        >
          {displayValue !== undefined ? displayValue : value}
        </div>
        {/* Botones de control arriba/abajo */}
        <div className="flex flex-col border-l border-white/10 w-6">
          <button
            onClick={handleIncrement}
            disabled={value >= max}
            className="flex-1 flex items-center justify-center cursor-pointer hover:bg-white/5 transition-colors"
            style={{
              border: 'none',
              background: 'transparent',
              color: value >= max ? '#64748b' : '#10b981',
              fontSize: '8px',
              padding: 0,
              lineHeight: 1,
            }}
            title="Aumentar"
          >
            ▲
          </button>
          <button
            onClick={handleDecrement}
            disabled={value <= min}
            className="flex-1 flex items-center justify-center cursor-pointer hover:bg-white/5 transition-colors border-t border-white/10"
            style={{
              border: 'none',
              background: 'transparent',
              color: value <= min ? '#64748b' : '#10b981',
              fontSize: '8px',
              padding: 0,
              lineHeight: 1,
            }}
            title="Disminuir"
          >
            ▼
          </button>
        </div>
      </div>
    </div>
  );
};

export default Spinner;
