import React from 'react';

const TransportNetworkBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 opacity-5">
      <svg 
        className="w-full h-full" 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <pattern 
            id="transport-network" 
            x="0" 
            y="0" 
            width="20" 
            height="20" 
            patternUnits="userSpaceOnUse"
          >
            {/* Station dots */}
            <circle cx="5" cy="5" r="0.5" fill="currentColor" opacity="0.6"/>
            <circle cx="15" cy="5" r="0.5" fill="currentColor" opacity="0.6"/>
            <circle cx="5" cy="15" r="0.5" fill="currentColor" opacity="0.6"/>
            <circle cx="15" cy="15" r="0.5" fill="currentColor" opacity="0.6"/>
            <circle cx="10" cy="10" r="0.8" fill="currentColor" opacity="0.8"/>
            
            {/* Connection lines */}
            {/* Horizontal lines */}
            <line x1="5" y1="5" x2="15" y2="5" stroke="currentColor" strokeWidth="0.2" opacity="0.4"/>
            <line x1="5" y1="15" x2="15" y2="15" stroke="currentColor" strokeWidth="0.2" opacity="0.4"/>
            
            {/* Vertical lines */}
            <line x1="5" y1="5" x2="5" y2="15" stroke="currentColor" strokeWidth="0.2" opacity="0.4"/>
            <line x1="15" y1="5" x2="15" y2="15" stroke="currentColor" strokeWidth="0.2" opacity="0.4"/>
            
            {/* Diagonal connections to center */}
            <line x1="5" y1="5" x2="10" y2="10" stroke="currentColor" strokeWidth="0.15" opacity="0.3"/>
            <line x1="15" y1="5" x2="10" y2="10" stroke="currentColor" strokeWidth="0.15" opacity="0.3"/>
            <line x1="5" y1="15" x2="10" y2="10" stroke="currentColor" strokeWidth="0.15" opacity="0.3"/>
            <line x1="15" y1="15" x2="10" y2="10" stroke="currentColor" strokeWidth="0.15" opacity="0.3"/>
            
            {/* Some curved "metro" lines */}
            <path 
              d="M 0 10 Q 10 5 20 10" 
              stroke="currentColor" 
              strokeWidth="0.3" 
              fill="none" 
              opacity="0.3"
            />
            <path 
              d="M 10 0 Q 15 10 10 20" 
              stroke="currentColor" 
              strokeWidth="0.3" 
              fill="none" 
              opacity="0.3"
            />
          </pattern>
        </defs>
        
        <rect 
          width="100%" 
          height="100%" 
          fill="url(#transport-network)" 
          className="text-blue-400"
        />
      </svg>
    </div>
  );
};

export default TransportNetworkBackground;