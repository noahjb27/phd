import { useState } from 'react';
import dynamic from 'next/dynamic';
import Layout from '../../components/common/Layout';
import { Network, Map, ArrowRight, Eye, Zap, MousePointer, Filter, ExternalLink } from 'lucide-react';

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
      <div className="py-12">
        {/* Hero Section */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-blue-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-blue-400/20 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Explore Berlin's Transport Evolution
            </h1>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto leading-relaxed">
              See how politics, geography, and ideology shaped the movement of millions across a divided city
            </p>
          </div>
        </div>

        {/* What You're Looking At */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-purple-600/90 to-indigo-600/90 rounded-xl p-8 shadow-2xl border border-purple-400/20">
            <div className="flex items-center mb-6">
              <Eye className="h-8 w-8 text-purple-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">What You're Looking At</h2>
            </div>
            <p className="text-lg text-purple-100 leading-relaxed">
              These interactive maps visualize Berlin's public transport networks from 1945-1989, 
              showing how the divided city's transportation evolved differently in East and West. 
              Each view reveals different aspects of the story—from individual stations and connections 
              to broader patterns across postal districts.
            </p>
          </div>
        </div>

        {/* View Explanations */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Station View */}
            <div className="bg-gradient-to-br from-indigo-600/90 to-blue-600/90 rounded-xl p-6 shadow-2xl border border-indigo-400/20">
              <div className="flex items-center mb-4">
                <Map className="h-6 w-6 text-indigo-200 mr-2" />
                <h3 className="text-2xl font-bold text-white">Station View</h3>
              </div>
              <p className="text-indigo-100 leading-relaxed mb-4">
                Explore individual stations and transport lines across Berlin. See how different 
                areas were connected—or isolated—by various transport types: buses, trams, 
                U-Bahn, and S-Bahn.
              </p>
              <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20 mb-4">
                <h4 className="font-semibold text-white mb-2">Key Insights:</h4>
                <ul className="text-indigo-100 text-sm space-y-1">
                  <li>• How the Berlin Wall disrupted transport networks</li>
                  <li>• Different transport philosophies in East vs West</li>
                  <li>• Areas that gained or lost connectivity over time</li>
                </ul>
              </div>
              <a 
                href="/articles/station-networks-explained" 
                className="inline-flex items-center text-blue-300 hover:text-blue-200 font-medium transition-colors"
              >
                Read detailed analysis
                <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </div>

            {/* PLZ View */}
            <div className="bg-gradient-to-br from-blue-600/90 to-cyan-600/90 rounded-xl p-6 shadow-2xl border border-blue-400/20">
              <div className="flex items-center mb-4">
                <Network className="h-6 w-6 text-blue-200 mr-2" />
                <h3 className="text-2xl font-bold text-white">Postal Code View</h3>
              </div>
              <p className="text-blue-100 leading-relaxed mb-4">
                View transport intensity and connections at the district level. This reveals 
                broader patterns of urban development and shows which neighborhoods were 
                transport hubs versus peripheral areas.
              </p>
              <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20 mb-4">
                <h4 className="font-semibold text-white mb-2">Key Insights:</h4>
                <ul className="text-blue-100 text-sm space-y-1">
                  <li>• Transport inequality between different districts</li>
                  <li>• How political geography shaped accessibility</li>
                  <li>• Network density differences across the divided city</li>
                </ul>
              </div>
              <a 
                href="/articles/district-analysis-methods" 
                className="inline-flex items-center text-cyan-300 hover:text-cyan-200 font-medium transition-colors"
              >
                Learn about the methodology
                <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </div>
          </div>
        </div>

        {/* How to Use */}
        <div className="max-w-5xl mx-auto px-6 mb-12">
          <div className="bg-gradient-to-br from-cyan-600/90 to-purple-600/90 rounded-xl p-8 shadow-2xl border border-cyan-400/20">
            <div className="flex items-center mb-6">
              <MousePointer className="h-8 w-8 text-cyan-200 mr-3" />
              <h2 className="text-3xl font-bold text-white">How to Use the Maps</h2>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                <div className="flex items-center mb-3">
                  <Filter className="h-5 w-5 text-cyan-300 mr-2" />
                  <h3 className="font-semibold text-white">Filter & Explore</h3>
                </div>
                <ul className="text-cyan-100 text-sm space-y-1">
                  <li>• Use the year slider to see changes over time</li>
                  <li>• Filter by transport type (bus, tram, U-Bahn, etc.)</li>
                  <li>• Toggle the Berlin Wall overlay on/off</li>
                </ul>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                <div className="flex items-center mb-3">
                  <Eye className="h-5 w-5 text-cyan-300 mr-2" />
                  <h3 className="font-semibold text-white">Interact & Discover</h3>
                </div>
                <ul className="text-cyan-100 text-sm space-y-1">
                  <li>• Click stations/areas for detailed information</li>
                  <li>• Hover over connections to see capacity data</li>
                  <li>• Zoom and pan to explore different districts</li>
                </ul>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/20">
                <div className="flex items-center mb-3">
                  <Zap className="h-5 w-5 text-cyan-300 mr-2" />
                  <h3 className="font-semibold text-white">Key Features</h3>
                </div>
                <ul className="text-cyan-100 text-sm space-y-1">
                  <li>• Line thickness shows transport capacity</li>
                  <li>• Colors represent different transport types</li>
                  <li>• Historical map overlays available</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* View Toggle & Maps */}
        <div className="max-w-7xl mx-auto px-6">
          <div className="bg-gradient-to-br from-gray-800/90 to-gray-700/90 rounded-xl shadow-2xl border border-gray-600/20 overflow-hidden">
            {/* Header with Toggle */}
            <div className="p-6 border-b border-gray-600/30">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white">Interactive Maps</h2>
                
                <div className="flex gap-2 bg-gray-900/50 rounded-lg shadow p-1">
                  <button
                    onClick={() => setActiveView('station')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ${
                      activeView === 'station' 
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' 
                        : 'hover:bg-gray-700 text-gray-300 hover:text-white'
                    }`}
                  >
                    <Map size={18} />
                    <span>Station View</span>
                  </button>
                  <button
                    onClick={() => setActiveView('plz')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 ${
                      activeView === 'plz' 
                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg' 
                        : 'hover:bg-gray-700 text-gray-300 hover:text-white'
                    }`}
                  >
                    <Network size={18} />
                    <span>Postal Code View</span>
                  </button>
                </div>
              </div>
              
              <p className="text-gray-300 text-sm">
                {activeView === 'station' 
                  ? 'Explore individual stations and transport connections across Berlin'
                  : 'Analyze transport patterns and intensity at the district level'
                }
              </p>
            </div>
            
            {/* Map Container */}
            <div className="relative">
              {activeView === 'station' ? (
                <MapVisualization />
              ) : (
                <PlzMapVisualization />
              )}
            </div>
          </div>
        </div>

        {/* Learn More */}
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <h2 className="text-2xl font-bold mb-6 text-white">Want to Learn More?</h2>
          <p className="text-gray-300 mb-8 leading-relaxed">
            Explore detailed articles about the data, methods, and historical insights behind these visualizations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/articles/data-sources-fahrplanbuch"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1"
            >
              <ExternalLink className="h-5 w-5 mr-2" />
              Data Sources & Methods
            </a>
            <a 
              href="/articles/digital-history-tools"
              className="inline-flex items-center px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors border border-gray-600"
            >
              <ExternalLink className="h-5 w-5 mr-2" />
              How This Was Built
            </a>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default VisualizationsPage;