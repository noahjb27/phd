// components/map/ConnectionLines.tsx
import { Polyline, Popup } from 'react-leaflet';
import { Connection, StationNode } from '../../pages/api/types';
interface ConnectionLinesProps {
  connections: Connection[];
  stations: StationNode[];
}

const InfoRow = ({label, value, tooltip}: {
  label: string;
  value: string;
  tooltip?: string;
}) => (
  <div className="flex justify-between py-1 group">
    <span className="text-gray-600">{label}:</span>
    <span className="font-medium" title={tooltip}>{value}</span>
  </div>
);

export const ConnectionLines: React.FC<ConnectionLinesProps> = ({
  connections,
  stations,
}) => {
  const getLineStyle = (type: string, hourlyCapacity: number, hourly_services: number) => {
    const baseColor = {
      'bus': '#9333EA',
      'autobus': '#9333EA',
      'u-bahn': '#2563EB',
      's-bahn': '#16A34A',
      'strassenbahn': '#DC2626',
      'default': '#6B7280'
    }[type] || '#6B7280';

    // Weight now based on hourly capacity, the higher the better
    const weight = Math.min(8, Math.max(2, hourlyCapacity / 100));

    // Opacity based on how many services in one hour, the higher the higher opacity
    const opacity = Math.min(0.9, Math.max(0.4, hourly_services / 10));

    // Get line pattern based on type
    const dashArray = {
      'bus': '5, 5',
      'autobus': '5, 5',
      'strassenbahn': '10, 5',
      'u-bahn': '',
      's-bahn': '',
      'default': '5, 5, 1, 5'
    }[type] || '5, 5, 1, 5';

    return { color: baseColor, weight, opacity, dashArray };
  };

  return (
    <>
      {connections.map((connection) => {
        const startStation = stations.find((s) => s.id === connection.startNodeId);
        const endStation = stations.find((s) => s.id === connection.endNodeId);

        if (!startStation || !endStation) return null;

        const positions: L.LatLngTuple[] = [
          [startStation.latitude, startStation.longitude],
          [endStation.latitude, endStation.longitude],
        ];

        const lineStyle = getLineStyle(
          connection.properties.transport_type,
          connection.properties.hourly_capacity,
          connection.properties.hourly_services
        );

        return (
          <Polyline
            key={`${connection.startNodeId}-${connection.endNodeId}`}
            positions={positions}
            {...lineStyle}
            className="transition-all duration-300 ease-in-out"
          >
            <Popup className="transport-popup">
              <div className="space-y-3 p-2 max-w-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{backgroundColor: lineStyle.color}} />
                  <h3 className="font-medium capitalize">{connection.properties.transport_type}</h3>
                </div>
                
                <div className="text-sm space-y-2 divide-y divide-gray-200">
                  <InfoRow 
                  label="Lines"
                  value={`${(connection.properties.line_names).toString()}`}
                  />
                  <InfoRow 
                  label="Hourly Capacity" 
                  value={`${Math.round(connection.properties.hourly_capacity)} passengers/hour`}
                  />
                  <InfoRow
                  label="Hourly Services"
                  value={`${(connection.properties.hourly_services ?? 0).toFixed(1)} services/hour`}
                  />
                  <InfoRow
                  label="Distance"
                  value={`${(connection.properties.distance_meters / 1000).toFixed(1)} km`}
                  />
                </div>
              </div>
            </Popup>
          </Polyline>
        );
      })}
    </>
  );
};