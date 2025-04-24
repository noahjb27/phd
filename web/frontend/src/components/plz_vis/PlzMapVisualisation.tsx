import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import proj4 from 'proj4';
import { fetchBerlinWallFeatures, Feature } from "../../pages/api/external/BerlinWall";
import { MapControls } from './MapControls';
import { PathOptions } from 'leaflet';
import MapLegend from './MapLegend';

// Extended types to match our specific needs
interface ExtendedFeature extends Omit<Feature, 'properties'> {
  properties: Properties;
}

interface FeatureCollection {
  type: 'FeatureCollection';
  features: ExtendedFeature[];
}

interface Properties {
  postal_code: string;
  district: string | null;
  neighborhood: string | null;
  east_west: string | null;
  postal_area_km2: number;
  neighborhood_area_km2: number;
  area_ratio: number;
  centroid_x: number;
  centroid_y: number;
}
interface CenterPoints {
  [plz: string]: [number, number];
}

interface NetworkNode {
  id: string;
  east_west: string;
  area: number;
  neighborhood?: string;
  district?: string;
}

interface NetworkEdge {
  source: string;
  target: string;
  transport_types: string[];
  hourly_capacity: number;
  hourly_services: number;
  distance_meters: number;
  weight_capacity: number;
  weight_frequency: number;
  weight_combined: number;
}

interface NetworkData {
  [year: string]: {
    nodes: NetworkNode[];
    edges: NetworkEdge[];
  };
}

// Constants
const TRANSPORT_STYLES = {
  's-bahn': { color: '#2ecc71', pattern: '10 10' },
  'u-bahn': { color: '#3498db', pattern: '0' },
  'strassenbahn': { color: '#e74c3c', pattern: '5 5' },
  'bus': { color: '#f1c40f', pattern: '2 4' }
} as const;

// Utility functions
const calculatePLZCenters = (plzData: FeatureCollection): CenterPoints => {
  const centers: CenterPoints = {};
  
  proj4.defs("EPSG:25833", "+proj=utm +zone=33 +ellps=GRS80 +units=m +no_defs");
  
  plzData.features.forEach((feature: Feature) => {
    const props = feature.properties;
    if (isFinite(props.centroid_x) && isFinite(props.centroid_y)) {
      const [lon, lat] = proj4("EPSG:25833", "EPSG:4326", [
        props.centroid_x,
        props.centroid_y
      ]);
      centers[props.postal_code] = [lat, lon];
    }
  });
  
  return centers;
};

const getEdgeStyle = (edge: NetworkEdge) => {
  const baseWeight = Math.min(edge.weight_combined / 5, 5);
  const primaryType = edge.transport_types[0] as keyof typeof TRANSPORT_STYLES;
  
  return {
    color: TRANSPORT_STYLES[primaryType]?.color || '#95a5a6',
    weight: baseWeight,
    dashArray: TRANSPORT_STYLES[primaryType]?.pattern,
    lineCap: 'round' as const,
    lineJoin: 'round' as const
  };
};

const NetworkEdges: React.FC<{
  centers: CenterPoints;
  edges: NetworkEdge[];
}> = ({ centers, edges }) => {
  return (
    <>
      {edges.map((edge, index) => {
        const sourceCenter = centers[edge.source];
        const targetCenter = centers[edge.target];
        
        if (!sourceCenter || !targetCenter) return null;

        return (
          <Polyline
            key={`${edge.source}-${edge.target}-${index}`}
            positions={[sourceCenter, targetCenter]}
            pathOptions={{
              ...getEdgeStyle(edge),
              opacity: 0.75
            }}
            eventHandlers={{
              mouseover: (e) => {
                const layer = e.target;
                layer.setStyle({
                  opacity: 1,
                  weight: layer.options.weight + 2
                });
                layer.bindTooltip(`
                  <div class="p-3 max-w-xs min-w-[300px]">
                    <h3 class="font-semibold mb-2">
                      Connecting: ${edge.source} & ${edge.target}
                    </h3>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <span class="text-gray-600">Transport Types:</span>
                      <span>${edge.transport_types.join(', ')}</span>
                      <span class="text-gray-600">Capacity:</span>
                      <span>${Math.round(edge.hourly_capacity)}</span>
                      <span class="text-gray-600">Services:</span>
                      <span>${Math.round(edge.hourly_services)}</span>
                    </div>
                  </div>
                `).openTooltip();
              },
              mouseout: (e) => {
                const layer = e.target;
                layer.setStyle({
                  opacity: 0.75,
                  weight: layer.options.weight - 2
                });
                layer.unbindTooltip();
              }
            }}
          />
        );
      })}
    </>
  );
};

// Helper functions
const transformPlzData = (plzJson: any[]): FeatureCollection => {
  proj4.defs("EPSG:25833", "+proj=utm +zone=33 +ellps=GRS80 +units=m +no_defs");
  
  const transformedFeatures = plzJson.map((item): ExtendedFeature => {
    const transformedCoordinates = item.postal_geometry.coordinates.map((polygon: any[][]) => 
      polygon.map((ring: any[]) => 
        ring.map((coord: number[]) => {
          const [x, y] = proj4('EPSG:25833', 'EPSG:4326', coord);
          return [x, y];
        })
      )
    );

    return {
      type: "Feature",
      id: String(item.postal_code), // Ensure id is a string
      properties: {
        postal_code: item.postal_code,
        district: item.district,
        neighborhood: item.neighborhood,
        east_west: item.east_west,
        postal_area_km2: item.postal_area_km2,
        neighborhood_area_km2: item.neighborhood_area_km2,
        area_ratio: item.area_ratio,
        centroid_x: item.centroid_x,
        centroid_y: item.centroid_y
      },
      geometry: {
        type: "MultiPolygon",
        coordinates: transformedCoordinates
      }
    };
  });

  return {
    type: "FeatureCollection",
    features: transformedFeatures
  };
};

const getAreaStyle = (networkData: NetworkData | null, selectedYear: number) => {
  const defaultStyle: PathOptions = {
    fillColor: '#cccccc',
    weight: 1,
    opacity: 1,
    color: '#666666',
    fillOpacity: 0.2
  };

  return (feature: ExtendedFeature): PathOptions => {
    if (!networkData) return defaultStyle;

    const plzCode = feature.properties.postal_code;
    const node = networkData[selectedYear]?.nodes.find(n => n.id === plzCode);
    
    const selfLoops = networkData[selectedYear]?.edges.filter(
      edge => edge.source === plzCode && edge.target === plzCode
    ) || [];

    const calculateIntensity = (loops: NetworkEdge[]) => {
      if (!loops.length) return 0;
      const totalWeight = loops.reduce((sum, edge) => {
        return sum + (edge.weight_capacity + edge.weight_frequency) / 2;
      }, 0);
      return Math.min(totalWeight / 20, 1);
    };

    const getIntensityColor = (intensity: number, isEast: boolean) => {
      const baseColor = isEast ? '#ff6b6b' : '#4dabf7';
      return intensity === 0 ? '#f8f9fa' : 
             intensity < 0.3 ? `${baseColor}80` :
             intensity < 0.6 ? `${baseColor}b3` :
             `${baseColor}`;
    };

    const intensity = calculateIntensity(selfLoops);
    return {
      fillColor: getIntensityColor(intensity, node?.east_west === 'east'),
      weight: 1.5,
      opacity: 0.8,
      color: '#666666',
      fillOpacity: 0.35
    };
  };
};

const createTooltipContent = (
  feature: ExtendedFeature,
  networkData: NetworkData | null,
  selectedYear: number
) => {
  const props = feature.properties;
  const plzCode = props.postal_code;
  const node = networkData?.[selectedYear]?.nodes.find(n => n.id === plzCode);
  const selfLoops = networkData?.[selectedYear]?.edges.filter(
    edge => edge.source === plzCode && edge.target === plzCode
  ) || [];

  const nonSelfLoops = networkData?.[selectedYear]?.edges.filter(
    edge => (edge.source === plzCode || edge.target === plzCode) && edge.source !== edge.target
  ) || [];

  return `
    <div class="p-3 max-w-xs min-w-[350px]">
      <h3 class="font-semibold mb-2">${props.postal_code}</h3>
      <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <span class="text-gray-600">District:</span>
        <span>${props.district || 'N/A'}</span>
        <span class="text-gray-600">Area:</span>
        <span>${props.postal_area_km2?.toFixed(2) || 'N/A'} km²</span>
        ${node ? `
          <span class="text-gray-600">Side:</span>
          <span class="capitalize">${node.east_west}</span>
          <span class="text-gray-600">Inner Connections:</span>
          <span>${selfLoops?.length}</span>
          <span class="text-gray-600">External Connections:</span>
          <span>${nonSelfLoops?.length}</span>
        ` : ''}
      </div>
    </div>
  `;
};

const BerlinWallLayer: React.FC<{ features: Feature[] }> = ({ features }) => {
  return (
    <>
      {features.map((feature, index) => {
        const transformedCoords = (feature.geometry as any).coordinates.map((coord: number[]) => {
          const [x, y] = proj4("EPSG:25833", "EPSG:4326", coord);
          return [y, x];
        });
        
        return (
          <Polyline
            key={index}
            positions={transformedCoords}
            pathOptions={{
              color: '#000000',
              weight: 2,
              opacity: 0.8
            }}
          />
        );
      })}
    </>
  );
};

const PlzMapVisualization: React.FC = () => {
  const [plzData, setPlzData] = useState<FeatureCollection | null>(null);
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [selectedYear, setSelectedYear] = useState(1946);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [showBerlinWall, setShowBerlinWall] = useState(false);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [plzResponse, networkResponse] = await Promise.all([
          fetch('/api/external/plz-areas'),
          fetch('/api/external/network-data')
        ]);
        
        const plzJson = await plzResponse.json();
        const networkJson = await networkResponse.json();
        
        setNetworkData(networkJson);
        setPlzData(transformPlzData(plzJson));
        
        const years = Object.keys(networkJson)
          .map(Number)
          .sort((a, b) => a - b);
        setAvailableYears(years);
        
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (showBerlinWall) {
      fetchBerlinWallFeatures()
        .then(setFeatures)
        .catch(console.error);
    } else {
      setFeatures([]);
    }
  }, [showBerlinWall]);

  if (loading) {
    return (
      <div className="w-full h-[800px] flex items-center justify-center">
        Loading PLZ areas...
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[800px] flex items-center justify-center text-red-500">
        Error: {error}
      </div>
    );
  }

  const centers = plzData ? calculatePLZCenters(plzData) : {};
  const currentYearData = networkData?.[selectedYear];

  return (
    <div className="w-full h-[800px] relative">
      <MapContainer
        center={[52.52, 13.405]}
        zoom={11}
        className="w-full h-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {plzData && (
          <GeoJSON 
            key={selectedYear}
            data={plzData}
            style={(feature) => getAreaStyle(networkData, selectedYear)(feature as ExtendedFeature)}
            onEachFeature={(feature, layer) => {
              const extendedFeature = { ...feature, id: String(feature.id) } as ExtendedFeature;
              const tooltipContent = createTooltipContent(extendedFeature, networkData, selectedYear);
              layer.bindTooltip(tooltipContent);
            }}
          />
        )}

        {currentYearData && (
          <NetworkEdges 
            centers={centers}
            edges={currentYearData.edges}
          />
        )}

        {showBerlinWall && <BerlinWallLayer features={features} />}
      </MapContainer>
      <MapLegend />
      <MapControls
        selectedYear={selectedYear}
        availableYears={availableYears}
        showBerlinWall={showBerlinWall}
        onYearChange={setSelectedYear}
        onBerlinWallToggle={(event) => setShowBerlinWall(event.target.checked)} selectedType={''}      />
    </div>
  );
};

export default PlzMapVisualization;