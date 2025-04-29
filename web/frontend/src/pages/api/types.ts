// src/pages/api/types.ts - Update these interfaces
export interface StationNode {
  id: string;
  east_west: string;
  stop_id: string; // Change from number to string (e.g. "19650_east")
  latitude: number;
  longitude: number;
  name: string;
  description: string | null;
  type: string; // Will now contain: "autobus", "omnibus", "tram", "u-bahn", "s-bahn", "ferry"
}

export interface Connection {
  id: string;
  type: string;
  startNodeId: string;
  endNodeId: string;
  properties: {
    transport_type: string; // Will be one of the new types
    capacities: Array<number>; // Format may differ from original
    frequencies: Array<number>; // Format may differ from original
    distance_meters: number;
    line_ids: Array<string>; // Change to match new format (likely strings now)
    line_names: Array<string>;
    hourly_capacity: number;
    hourly_services: number;
  };
}

// Add this to types.ts or wherever you keep your interfaces
export interface LineInfo {
  id: number;
  name: string;
}

export interface NetworkDataPlz {
  [year: number]: {
    nodes: {
      [plz: string]: {
        east_west: 'east' | 'west',
        weight_capacity: number,
        weight_frequency: number,
        weight_combined: number,
        area: number
      }
    },
    edges: {
      [id: string]: {
        source: string,
        target: string,
        transport_type: string,
        hourly_capacity: number,
        hourly_services: number
      }
    }
  }
}