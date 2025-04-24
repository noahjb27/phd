// components/common/PageBackground.tsx
import React from 'react';

const TransitPattern = () => (
  <div className="absolute inset-0 w-full h-full opacity-[0.03] pointer-events-none">
    <div className="relative w-full h-full">
      <svg className="absolute w-full h-full" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <defs>
          <pattern id="transit-grid" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            {/* Horizontal lines */}
            <path d="M0 20 H100" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.3"/>
            <path d="M0 80 H100" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.3"/>
            
            {/* Vertical lines */}
            <path d="M20 0 V100" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.3"/>
            <path d="M80 0 V100" stroke="currentColor" strokeWidth="0.5" fill="none" opacity="0.3"/>
            
            {/* Diagonal "routes" */}
            <path d="M0 0 L100 100" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.2"/>
            <path d="M100 0 L0 100" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.2"/>
            
            {/* "Stations" */}
            <circle cx="20" cy="20" r="2" fill="currentColor" opacity="0.4"/>
            <circle cx="80" cy="80" r="2" fill="currentColor" opacity="0.4"/>
            <circle cx="20" cy="80" r="2" fill="currentColor" opacity="0.4"/>
            <circle cx="80" cy="20" r="2" fill="currentColor" opacity="0.4"/>
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#transit-grid)"/>
      </svg>
    </div>
  </div>
);

const PageBackground: React.FC = () => {
  return (
    <>
      {/* Background Pattern */}
      <TransitPattern />
      
      {/* Gradient overlay */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-5">
        <div className="absolute -right-1/4 -top-1/4 w-1/2 h-1/2 bg-blue-200 rounded-full blur-3xl" />
        <div className="absolute -left-1/4 -bottom-1/4 w-1/2 h-1/2 bg-purple-200 rounded-full blur-3xl" />
      </div>
    </>
  );
};

export default PageBackground;