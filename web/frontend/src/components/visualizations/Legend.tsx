// components/map/Legend.tsx
import React, { useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronUp, MapPin, X } from 'lucide-react';

interface LegendProps {
  defaultCollapsed?: boolean;
}

const transportTypes = [
  {
    name: 'autobus',
    color: '#9333EA', // Tailwind purple-600
    label: 'Autobus',
    lineStyle: 'dashed',
    capacity: '80-120 passengers'
  },
  {
    name: 'omnibus',
    color: '#9333EA', // Same color for similar types
    label: 'Omnibus',
    lineStyle: 'dashed',
    capacity: '80-120 passengers'
  },
  {
    name: 'u-bahn',
    color: '#2563EB', // Tailwind blue-600
    label: 'U-Bahn',
    lineStyle: 'solid',
    capacity: '750-1000 passengers'
  },
  {
    name: 's-bahn',
    color: '#16A34A', // Tailwind green-600
    label: 'S-Bahn',
    lineStyle: 'solid',
    capacity: '1000+ passengers'
  },
  {
    name: 'tram',
    color: '#DC2626', // Tailwind red-600
    label: 'Tram',
    lineStyle: 'dotted',
    capacity: '150-250 passengers'
  },
  {
    name: 'ferry',
    color: '#0891B2', // Tailwind cyan-600
    label: 'Ferry',
    lineStyle: 'dotted',
    capacity: '100-300 passengers'
  }
];

const Legend: React.FC<LegendProps> = ({ defaultCollapsed = true }) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div className="relative">
      {/* Collapsed state */}
      {isCollapsed ? (
        <button
          onClick={() => setIsCollapsed(false)}
          className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg p-2 shadow-lg hover:bg-gray-50 transition-colors"
        >
          <MapPin size={16} />
          <span className="text-sm font-medium">Legend</span>
          <ChevronLeft size={16} className="text-gray-500" />
        </button>
      ) : (
        <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg w-64">
          <div className="p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium flex items-center gap-2">
                <MapPin size={16} />
                Legend
              </h3>
              <button
                onClick={() => setIsCollapsed(true)}
                className="p-1 hover:bg-gray-100 rounded-full"
              >
                <X size={16} />
              </button>
            </div>
            
            <div className="space-y-4">
              {transportTypes.map((type) => (
                <div key={type.name} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-8 h-0 border-2" 
                      style={{
                        borderStyle: type.lineStyle as any,
                        borderColor: type.color
                      }} 
                    />
                    <span className="text-sm font-medium">{type.label}</span>
                  </div>
                  <div className="text-xs text-gray-500 ml-10">
                    {type.capacity}
                  </div>
                </div>
              ))}
              <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-xs font-medium mb-2">Line Thickness</h4>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0 border-[1px] border-gray-400" />
                  <span className="text-xs text-gray-500">Low capacity</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0 border-[3px] border-gray-400" />
                  <span className="text-xs text-gray-500">Medium capacity</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0 border-[5px] border-gray-400" />
                  <span className="text-xs text-gray-500">High capacity</span>
                  </div>
              </div>
            </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


export default Legend;