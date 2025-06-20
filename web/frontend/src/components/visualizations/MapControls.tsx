// components/visualizations/MapControls.tsx
import { useState } from 'react';
import { Switch } from '../ui/switch';
import { Slider } from '../ui/slider';
import { ChevronLeft, ChevronRight, Clock, Filter, Map } from 'lucide-react';

interface MapControlsProps {
  selectedYear: number;
  selectedType: string;
  availableYears: number[];
  showBerlinWall: boolean;
  lineNames?: string[];
  selectedLine?: string;
  onYearChange: (year: number) => void;
  onTypeChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  onLineChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  onBerlinWallToggle: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  selectedYear,
  selectedType,
  availableYears,
  showBerlinWall,
  lineNames,
  selectedLine,
  onYearChange,
  onTypeChange,
  onLineChange,
  onBerlinWallToggle,
}) => {

const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="absolute top-4 left-4">
      {/* Collapsed state shows as a button with icon and label */}
      {isCollapsed ? (
        <button
          onClick={() => setIsCollapsed(false)}
          className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg hover:bg-gray-50 transition-colors"
        >
          <Filter size={16} className="text-gray-600" />
          <span className="text-sm font-medium text-gray-800">Show Controls</span>
          <ChevronRight size={16} className="text-gray-500" />
        </button>
      ) : (
        <div 
        className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg w-80"
        >

            <div className="p-4 space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="font-medium flex items-center gap-2 text-gray-800">
                  <Filter size={16} className="text-gray-600" />
                  Map Controls
                </h3>
                <button
                  onClick={() => setIsCollapsed(true)}
                  className="p-1 hover:bg-gray-100 rounded-full text-gray-600 hover:text-gray-800"
                >
                  <ChevronLeft size={16} />
                </button>
              </div>
              
              {/* Year Selection with Timeline */}
              <div className="space-y-2">
                <label htmlFor="year" className="text-sm font-medium flex items-center gap-2 text-gray-700">
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
                    disabled={false}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{availableYears[0]}</span>
                  <span>{availableYears[availableYears.length - 1]}</span>
                </div>
              </div>

              {/* Transport Type Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Transport Type</label>
                <select
                  value={selectedType}
                  onChange={onTypeChange}
                  className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Types</option>
                  <option value="autobus">Autobus</option>
                  <option value="omnibus">Omnibus</option>
                  <option value="tram">Tram</option>
                  <option value="u-bahn">U-Bahn</option>
                  <option value="s-bahn">S-Bahn</option>
                  <option value="ferry">Ferry</option>
                </select>
              </div>

              {/* Line Filter - Only shows when a transport type is selected */}
              {selectedType && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Line Name</label>
                  <select
                    value={selectedLine}
                    onChange={onLineChange}
                    className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Lines</option>
                    {lineNames?.map((line) => (
                      <option key={line} value={line}>
                        {line}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Berlin Wall Toggle */}
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">Show Berlin Wall</label>
                <Switch
                  checked={showBerlinWall}
                  onCheckedChange={(checked) => 
                    onBerlinWallToggle({ target: { checked } } as any)
                  }
                />
              </div>
          </div>
        </div>
      )}
    </div>
  );
};