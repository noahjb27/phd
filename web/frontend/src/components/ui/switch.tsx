// components/ui/switch.tsx
import * as React from "react";

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}

export const Switch: React.FC<SwitchProps> = ({ checked, onCheckedChange, className = "" }) => {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full 
        transition-colors focus-visible:outline-none focus-visible:ring-2 
        focus-visible:ring-offset-2 focus-visible:ring-blue-500
        ${checked ? 'bg-blue-600' : 'bg-gray-200'}
        ${className}
      `}
    >
      <span
        className={`
          pointer-events-none block h-5 w-5 rounded-full bg-white 
          shadow-lg ring-0 transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  );
};