import { useState } from 'react';
import dynamic from 'next/dynamic';
import Layout from '../../components/common/Layout';
import { Network, Map } from 'lucide-react';

// Dynamically import both visualization components with no SSR
const PlzMapVisualization = dynamic(
  () => import('../../components/plz_vis/PlzMapVisualisation'),
  { ssr: false }
);

const MapVisualization = dynamic(
  () => import('../../components/visualizations/MapVisualization'),
  { ssr: false }
);

const VisualizationsPage: React.FC = () => {
  const [activeView, setActiveView] = useState<'station' | 'plz'>('station');

  return (
    <Layout>
      <section className="container mx-auto p-4">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-4xl font-bold">Map Visualization</h1>
          
          <div className="flex gap-2 bg-white rounded-lg shadow p-1">
            <button
              onClick={() => setActiveView('station')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeView === 'station' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <Map size={18} />
              <span>Station View</span>
            </button>
            <button
              onClick={() => setActiveView('plz')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeView === 'plz' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <Network size={18} />
              <span>Postal Code View</span>
            </button>
          </div>
        </div>

        {activeView === 'station' ? (
          <MapVisualization />
        ) : (
          <PlzMapVisualization />
        )}
      </section>
    </Layout>
  );
};

export default VisualizationsPage;