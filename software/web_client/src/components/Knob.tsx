import React, { useRef, useState, useEffect } from 'react';

interface KnobProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  label: string;
  unit?: string;
  size?: number;
  color?: string;
  displayValue?: string; // Valor formateado opcional para mostrar
}

export const Knob: React.FC<KnobProps> = ({
  value,
  min,
  max,
  step = 1,
  onChange,
  label,
  unit = '',
  size = 56,
  color = 'var(--ch1-color)',
  displayValue,
}) => {
  const knobRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const startYRef = useRef(0);
  const startValueRef = useRef(0);

  // Mapear el valor actual a un ángulo en grados (-135 a 135 grados para el rango del dial)
  const angle = ((value - min) / (max - min)) * 270 - 135;

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    startYRef.current = e.clientY;
    startValueRef.current = value;
    e.preventDefault();
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    startYRef.current = e.touches[0].clientY;
    startValueRef.current = value;
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;

      const deltaY = startYRef.current - e.clientY; // Arriba aumenta, abajo disminuye
      const range = max - min;
      // Ajuste de sensibilidad: 150 píxeles de arrastre para recorrer todo el rango
      const valDelta = (deltaY / 150) * range;
      let newValue = startValueRef.current + valDelta;

      // Restringir y redondear al step más cercano
      newValue = Math.max(min, Math.min(max, newValue));
      newValue = Math.round(newValue / step) * step;

      onChange(newValue);
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (!isDragging) return;

      const deltaY = startYRef.current - e.touches[0].clientY;
      const range = max - min;
      const valDelta = (deltaY / 150) * range;
      let newValue = startValueRef.current + valDelta;

      newValue = Math.max(min, Math.min(max, newValue));
      newValue = Math.round(newValue / step) * step;

      onChange(newValue);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchmove', handleTouchMove);
      window.addEventListener('touchend', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging, value, min, max, step, onChange]);

  return (
    <div className="flex flex-col items-center select-none" style={{ margin: '10px 0' }}>
      {/* Etiqueta del Knob */}
      <span className="text-xs font-semibold mb-1" style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>

      {/* Dial rotativo */}
      <div
        ref={knobRef}
        className="knob-outer"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        <div
          className="knob-dial"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            transform: `rotate(${angle}deg)`,
            borderColor: isDragging ? color : 'rgba(255, 255, 255, 0.1)',
            boxShadow: isDragging 
              ? `0 0 10px ${color}33, inset 0 2px 4px rgba(255,255,255,0.05), 0 4px 10px rgba(0,0,0,0.5)`
              : 'inset 0 2px 4px rgba(255,255,255,0.05), 0 4px 10px rgba(0,0,0,0.5)'
          }}
        >
          {/* Marcador indicador del dial */}
          <div className="knob-marker" style={{ backgroundColor: color }} />
        </div>
      </div>

      {/* Valor visualizado */}
      <span className="font-mono text-xs mt-1.5 font-bold" style={{ color: 'var(--text-primary)', fontSize: '12px' }}>
        {displayValue !== undefined ? displayValue : `${value}${unit}`}
      </span>
    </div>
  );
};
