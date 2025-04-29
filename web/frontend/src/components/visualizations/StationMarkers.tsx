import { useEffect } from 'react';
import { Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import StandardIcon from "../../../public/assets/marker-icon.png";
import { Session } from 'next-auth';
import { StationNode, Connection } from '../../pages/api/types';

interface StationMarkersProps {
  stations: StationNode[];
  connections: Connection[];
  onUpdateStation: (stopId: string, lat: number, lng: number) => Promise<void>;
  session: Session | null;
}

interface Neo4jInt {
  low: number;
  high: number;
}

const getStationLines = (station: StationNode, connections: Connection[]) => {
  const lines = new Set<string>();
  
  connections.forEach(connection => {
    if (connection.startNodeId === station.id || connection.endNodeId === station.id) {
      const lineNames = connection.properties.line_names;
      // Add direct line_names if it exists
      if (lineNames) {
        if (Array.isArray(lineNames)) {
          lineNames.forEach(name => lines.add(String(name)));
        } else {
          // If it's not an array, add it directly
          lines.add(String(lineNames));
        }
      }
    }
  });
  
  return Array.from(lines).sort();
};

export const StationMarkers: React.FC<StationMarkersProps> = ({
  stations,
  connections,
  session,
  onUpdateStation,
}) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    const markerClusterGroup = L.markerClusterGroup();

    stations.forEach((station) => {
      const stationLines = getStationLines(station, connections);
      
      const marker = L.marker([station.latitude, station.longitude], {
        draggable: !!session && session.user.role === 'admin',
        icon: L.icon({
          iconUrl: StandardIcon.src,
          iconSize: [25, 41],
          iconAnchor: [12, 41],
        }),
      });

      const popupContent = `
        <div class="p-2 max-w-xs">
          <div class="font-bold mb-2">${station.name}</div>
          <div class="text-sm space-y-1">
            <div class="flex justify-between">
              <span class="text-gray-600">Type:</span>
              <span class="font-medium">${station.type}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Region:</span>
              <span class="font-medium">${station.east_west}</span>
            </div>
            ${stationLines.length > 0 ? `
              <div class="mt-2">
                <span class="text-gray-600">Lines:</span>
                <div class="font-medium mt-1">
                  ${stationLines.join(', ')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);

      if (!!session && session.user.role === 'admin') {
        marker.on('dragend', (event) => {
          const newLatLng = event.target.getLatLng();
          const stopId = station.stop_id.toString();
          onUpdateStation(stopId, newLatLng.lat, newLatLng.lng);
        });
      }

      markerClusterGroup.addLayer(marker);
    });

    map.addLayer(markerClusterGroup);

    return () => {
      map.removeLayer(markerClusterGroup);
    };
  }, [map, stations, connections, session, onUpdateStation]);

  return null;
};