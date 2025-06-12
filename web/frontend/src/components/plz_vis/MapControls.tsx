import { useState } from 'react';
import { Switch } from '../ui/switch';
import { Slider } from '../ui/slider';
import { ChevronLeft, ChevronRight, Clock, Filter } from 'lucide-react';

interface MapControlsProps {
  selectedYear: number;
  selectedType: string;
  availableYears: number[];
  showBerlinWall: boolean;
  onYearChange: (year: number) => void;
  onBerlinWallToggle: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  selectedYear,
  availableYears,
  showBerlinWall,
  onYearChange,
  onBerlinWallToggle,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="absolute top-20 left-4 z-[1000] transition-all duration-300">
      <div className="relative">
        {/* Collapse toggle button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-4 top-1/2 -translate-y-1/2 bg-white rounded-full p-1.5 shadow-md hover:bg-gray-50 transition-colors"
          aria-label={isCollapsed ? "Expand controls" : "Collapse controls"}
        >
          {isCollapsed ? <ChevronRight size={16} className="text-gray-600" /> : <ChevronLeft size={16} className="text-gray-600" />}
        </button>

        <div className={`
          bg-white/95 backdrop-blur-sm rounded-lg shadow-lg overflow-hidden transition-all duration-300
          ${isCollapsed ? 'p-3' : 'w-80'}
        `}>
          {isCollapsed ? (
            // Collapsed state - show just the year
            <div className="flex flex-col items-center gap-2">
              <Filter size={16} className="text-gray-600" />
              <span className="text-sm font-medium text-gray-800">Show Controls</span>
            </div>
          ) : (
            // Expanded state
            <div className="p-4 space-y-6">
              {/* Header */}
              <div className="flex justify-between items-center">
                <h3 className="font-medium flex items-center gap-2 text-gray-800">
                  <Filter size={16} className="text-gray-600" />
                  Map Controls
                </h3>
              </div>

              {/* Year Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2 text-gray-700">
                  <Clock size={14} className="text-gray-600" />
                  Year: {selectedYear}
                </label>
                <div className="px-2">
                  <Slider
                    value={[availableYears.indexOf(selectedYear)]}
                    min={0}
                    max={availableYears.length - 1}
                    step={1}
                    onValueChange={(values) => onYearChange(availableYears[values[0]])}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{availableYears[0]}</span>
                  <span>{availableYears[availableYears.length - 1]}</span>
                </div>
              </div>

              {/* Berlin Wall Toggle */}
              <div className="flex items-center justify-between pt-2">
                <label className="text-sm font-medium text-gray-700">Show Berlin Wall</label>
                <Switch
                  checked={showBerlinWall}
                  onCheckedChange={(checked) => 
                    onBerlinWallToggle({ target: { checked } } as any)
                  }
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};