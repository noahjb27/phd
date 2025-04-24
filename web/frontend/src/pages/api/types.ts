export interface StationNode {
  id: string;
  east_west: string;
  stop_id: number;
  latitude: number;
  longitude: number;
  name: string;
  description: string | null;
  type: string;
}

export interface Connection {
  id: string;
  type: string;
  startNodeId: string;
  endNodeId: string;
  properties: {
    transport_type: string;
    capacities: Array<{ low: number }>;
    frequencies: Array<{ low: number }>;
    distance_meters: number;
    line_ids: Array<{ low: number }>;
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