import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, LayersControl } from 'react-leaflet';
import { useSession } from 'next-auth/react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import Legend from './Legend'; // Import the Legend component
import { fetchBerlinWallFeatures, Feature } from "../../pages/api/external/BerlinWall";
import { MapControls } from './MapControls';
import { StationMarkers } from './StationMarkers';
import { ConnectionLines } from './ConnectionLines';
import proj4 from 'proj4';
import 'leaflet';
import { WMSTileLayer } from 'react-leaflet/WMSTileLayer'
import useNetworkData from '@/pages/api/useNetworkData';

// Define EPSG:25833 to EPSG:4326 transformation
proj4.defs("EPSG:25833", "+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs");

const transformCoordinates = (coordinates: number[][]) => {
  return coordinates.map(coord => proj4("EPSG:25833", "EPSG:4326", coord));
};

// Fix the icon issue by specifying the paths to the icon images
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: '../../../public/assets/marker-icon.png',
  iconRetinaUrl: '../../../public/assets/marker-icon-2x.png',
  shadowUrl: '../../../public/assets/marker-shadow.png',
});

const BerlinWallLayer: React.FC<{ features: Feature[] }> = ({ features }) => {
  return (
    <>
      {features.map((feature, index) => (
        <Polyline
          key={index}
          positions={transformCoordinates(feature.geometry.coordinates).map(coord => [coord[1], coord[0]])}
        />
      ))}
    </>
  );
};

const MapVisualization: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(1946);
  const [selectedType, setSelectedType] = useState<string>('');
  const { data: session } = useSession();
  const [features, setFeatures] = useState<Feature[]>([]);
  const [showBerlinWall, setShowBerlinWall] = useState(false);
  const availableYears = [1946, 1951, 1956, 1960, 1961, 1963, 1964, 1967, 1971, 1976, 1980, 1982, 1984, 1989];
  // New state for selected line and derived line names
  const [selectedLine, setSelectedLine] = useState<string>('');
  const { stations, connections, loading, error, refetch, updateStation } = useNetworkData(selectedYear, selectedType, selectedLine);

  const handleUpdateStation = async (stopId: string, latitude: number, longitude: number) => {
    if (!session?.accessToken) {
        alert('You need to be signed in to update stations.');
        return;
    }

    try {
        await updateStation(stopId, latitude, longitude, session.accessToken);
        alert('Station updated successfully!');
    } catch (error) {
        console.log(stopId)
        console.error('Update error:', error);
        alert('Failed to update station');
    }
};

  // Update the year selection handler
  const handleYearChange = (newYear: number) => {
    const closestYear = availableYears.reduce((prev, curr) => {
      return Math.abs(curr - newYear) < Math.abs(prev - newYear) ? curr : prev;
    });
    setSelectedYear(closestYear);
  };

  const getLineNames = useCallback(() => {
    if (!connections) return [];
    
    const filteredConnections = selectedType 
      ? connections.filter((conn: { properties: { transport_type: string; }; }) => conn.properties.transport_type === selectedType)
      : connections;
  
    
    const lineNames = Array.from(new Set(
      filteredConnections.flatMap((conn: { properties: { line_names: any; }; }) => conn.properties.line_names)
    )).sort();
    
    return lineNames;
  }, [connections, selectedType]);

  // Reset selected line when transport type changes
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedType(e.target.value);
    setSelectedLine(''); // Reset line selection when type changes
  };

  // Handle line selection change
  const handleLineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLine(e.target.value);
  };

  // Fetch Berlin Wall data when checkbox is toggled
  useEffect(() => {
    if (showBerlinWall) {
      fetchBerlinWallFeatures().then(setFeatures).catch(console.error);
    } else {
      setFeatures([]);
    }
  }, [showBerlinWall]);

  return (
    <div className="relative w-full h-[calc(100vh-6rem)]">
      

      <div className="absolute inset-0 z-0">
        {loading ? (
          <div className="flex justify-center items-center h-full bg-gray-50">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading map data...</p>
            </div>
          </div>
        ) : (
            <MapContainer
            center={[52.5200, 13.4050]}
            zoom={12}
            scrollWheelZoom={true}
            className="h-full w-full"
            >
            <LayersControl position="topright">
              <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
              />
              </LayersControl.BaseLayer>
              <LayersControl.Overlay name="Berlin 1986">
              <WMSTileLayer
                url="https://gdi.berlin.de/services/wms/staedtebauliche_entwicklung"
                layers="berlin_1986"
                format="image/png"
                transparent={true}
                version="1.3.0"
                crs={L.CRS.EPSG4326}
              />
              </LayersControl.Overlay>
              <LayersControl.Overlay name="Luftbilder 1953">
              <WMSTileLayer
                url="https://fbinter.stadt-berlin.de/fb/wms/senstadt/k_luftbild1953"
                layers="k_luftbild1953"
                format="image/png"
                transparent={true}
                version="1.3.0"
                crs={L.CRS.EPSG4326}
              />
              </LayersControl.Overlay>
              <LayersControl.Overlay name="Berlin 1945 Gebäudeschäden">
              <WMSTileLayer
                url="https://gdi.berlin.de/services/wms/staedtebauliche_entwicklung"
                layers="berlin_1945_gebaeudeschaeden"
                format="image/png"
                transparent={true}
                version="1.3.0"
                crs={L.CRS.EPSG4326}
              />
              </LayersControl.Overlay>
              <LayersControl.Overlay name="Georeferenced Schwarz Map Overlay">
              <TileLayer
                url="https://allmaps.xyz/maps/ef9b93beb8041b8c/{z}/{x}/{y}.png"
                attribution="Schwarz Stadtplan von Berlin. Richard Schwarz, Landkartenhandlung u. Geogr. Verlag, 1946. Gehosted via allmaps.org"
              />
              </LayersControl.Overlay>
              <LayersControl.Overlay name="Georeferenced Benutzen Sie Die S-Bahn 1939 Overlay">
              <TileLayer
                url="https://allmaps.xyz/maps/69353a7a26fb567d/{z}/{x}/{y}.png"
                attribution="Benutzen Sie Die S-Bahn. H. M. Hauschild, 1939.. Gehosted via allmaps.org"
              />
              </LayersControl.Overlay>
            </LayersControl>
            <StationMarkers
              stations={stations}
              connections={connections}
              session={session}
              onUpdateStation={handleUpdateStation}
            />

            <ConnectionLines
              connections={connections}
              stations={stations}
            />

            {/* Conditionally render Berlin Wall layer */}
            {showBerlinWall && <BerlinWallLayer features={features} />}

          </MapContainer>
        )}
      </div>

      <div className="absolute left-0 top-16 bottom-0 z-10">
              <MapControls
              selectedYear={selectedYear}
              selectedType={selectedType}
              availableYears={availableYears}
              lineNames={getLineNames()}
              selectedLine={selectedLine}
              showBerlinWall={showBerlinWall}
              onYearChange={(value) => handleYearChange(value)}
              onTypeChange={handleTypeChange}
              onLineChange={handleLineChange}
              onBerlinWallToggle={(e) => setShowBerlinWall(e.target.checked)}
              />
            </div>
            {/* Legend - Fixed position bottom right */}
      <div className="absolute right-4 bottom-4 z-10">
        <Legend/>
      </div>
      {error && (
        <div className="absolute bottom-4 left-4 right-4 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
};

export default MapVisualization;
