import * as React from "react";
import { useCallback, useRef, useState } from "react";
import { Plus, Minus } from "lucide-react";

interface SliderProps {
  value: number[];
  min: number;
  max: number;
  step?: number;
  onValueChange: (value: number[]) => void;
  className?: string;
  label?: string;
  disabled?: boolean;
}

export const Slider: React.FC<SliderProps> = ({
  value,
  min,
  max,
  step = 1,
  onValueChange,
  className = "",
  label,
  disabled = false,
}) => {
  const sliderRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const percentage = ((value[0] - min) / (max - min)) * 100;
  
  // Convert percentage to actual value
  const percentageToValue = useCallback(
    (percentage: number) => {
      const rawValue = (percentage / 100) * (max - min) + min;
      const steppedValue = Math.round(rawValue / step) * step;
      return Math.min(Math.max(steppedValue, min), max);
    },
    [max, min, step]
  );

  // Handle increment/decrement
  const handleIncrement = () => {
    if (disabled) return;
    const newValue = Math.min(value[0] + step, max);
    onValueChange([newValue]);
  };

  const handleDecrement = () => {
    if (disabled) return;
    const newValue = Math.max(value[0] - step, min);
    onValueChange([newValue]);
  };

  // Handle mouse/touch interactions
  const handlePointerMove = useCallback(
    (event: PointerEvent) => {
      if (!isDragging || !sliderRef.current || disabled) return;

      const rect = sliderRef.current.getBoundingClientRect();
      const percentage = Math.min(
        Math.max(((event.clientX - rect.left) / rect.width) * 100, 0),
        100
      );
      
      onValueChange([percentageToValue(percentage)]);
    },
    [isDragging, onValueChange, percentageToValue, disabled]
  );

  const handlePointerUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add and remove event listeners
  React.useEffect(() => {
    if (isDragging) {
      window.addEventListener("pointermove", handlePointerMove);
      window.addEventListener("pointerup", handlePointerUp);
    }

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [isDragging, handlePointerMove, handlePointerUp]);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled) return;
    
    const increment = event.shiftKey ? step * 10 : step;
    let newValue = value[0];

    switch (event.key) {
      case "ArrowRight":
      case "ArrowUp":
        newValue = Math.min(value[0] + increment, max);
        break;
      case "ArrowLeft":
      case "ArrowDown":
        newValue = Math.max(value[0] - increment, min);
        break;
      case "Home":
        newValue = min;
        break;
      case "End":
        newValue = max;
        break;
      default:
        return;
    }

    event.preventDefault();
    onValueChange([newValue]);
  };

  return (
    <div 
      className={`relative w-full ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      aria-disabled={disabled}
    >
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}
      <div className="flex items-center gap-4">
        {/* Minus button */}
        <button
          onClick={handleDecrement}
          disabled={disabled || value[0] <= min}
          className={`p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500
            ${disabled || value[0] <= min ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600'}
          `}
          aria-label="Decrease value"
        >
          <Minus size={16} />
        </button>

        {/* Slider */}
        <div
          ref={sliderRef}
          className="relative h-6 flex-1 flex items-center"
          onPointerDown={(e) => {
            if (!disabled) {
              const rect = sliderRef.current!.getBoundingClientRect();
              const percentage = ((e.clientX - rect.left) / rect.width) * 100;
              onValueChange([percentageToValue(percentage)]);
              setIsDragging(true);
            }
          }}
        >
          {/* Track background */}
          <div className="absolute w-full h-2 bg-gray-200 rounded-full">
            {/* Filled track */}
            <div
              className={`absolute h-full rounded-full transition-colors ${
                disabled ? 'bg-gray-400' : 'bg-blue-600'
              }`}
              style={{ width: `${percentage}%` }}
            />
          </div>

          {/* Hidden input for native functionality */}
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value[0]}
            onChange={(e) => onValueChange([Number(e.target.value)])}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            className="absolute w-full h-2 opacity-0 cursor-pointer"
            disabled={disabled}
            aria-label={label}
            aria-valuemin={min}
            aria-valuemax={max}
            aria-valuenow={value[0]}
          />

          {/* Thumb */}
          <div
            className={`absolute h-4 w-4 rounded-full shadow-md transform -translate-y-1/2 top-1/2 transition-all
              ${disabled ? 'bg-gray-300 border-gray-400' : 'bg-white border-gray-300'}
              ${isDragging || isFocused ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
              ${isDragging ? 'scale-110' : ''}
            `}
            style={{ left: `${percentage}%` }}
          />
        </div>

        {/* Plus button */}
        <button
          onClick={handleIncrement}
          disabled={disabled || value[0] >= max}
          className={`p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500
            ${disabled || value[0] >= max ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600'}
          `}
          aria-label="Increase value"
        >
          <Plus size={16} />
        </button>
      </div>
      
    </div>
  );
};