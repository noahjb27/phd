import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const MapLegend = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const legendItems = [
    {
      label: 'East Berlin - High Intensity',
      color: '#ff6b6b',
      opacity: '1'
    },
    {
      label: 'East Berlin - Medium Intensity',
      color: '#ff6b6b',
      opacity: '0.7'
    },
    {
      label: 'East Berlin - Low Intensity',
      color: '#ff6b6b',
      opacity: '0.5'
    },
    {
      label: 'West Berlin - High Intensity',
      color: '#4dabf7',
      opacity: '1'
    },
    {
      label: 'West Berlin - Medium Intensity',
      color: '#4dabf7',
      opacity: '0.7'
    },
    {
      label: 'West Berlin - Low Intensity',
      color: '#4dabf7',
      opacity: '0.5'
    }
  ];

  return (
    <div className="absolute bottom-6 right-6 bg-white rounded-lg shadow-lg z-[1000]">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg"
      >
        <span>Legend</span>
        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>
      
      {isExpanded && (
        <div className="p-4 space-y-3">
          {legendItems.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-6 h-6 rounded"
                style={{ 
                  backgroundColor: item.color,
                  opacity: item.opacity
                }}
              />
              <span className="text-sm text-gray-600">{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MapLegend;