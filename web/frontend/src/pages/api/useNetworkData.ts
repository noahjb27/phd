// hooks/useNetworkData.ts
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { StationNode, Connection } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
console.log('Environment API URL:', process.env.NEXT_PUBLIC_API_URL);
console.log('Window location:', typeof window !== 'undefined' ? window.location.origin : 'No window');
console.log('Final API_BASE_URL:', API_BASE_URL);

const api = axios.create({
    baseURL: API_BASE_URL,
    // Add timeout and debug logs
    timeout: 5000,
    transformRequest: [(data, headers) => {
        console.log('Making request to:', API_BASE_URL);
        return data;
    }]
});

const useNetworkData = (selectedYear: number, selectedType: string,  selectedLine: string) => {
    const [stations, setStations] = useState<StationNode[]>([]);
    const [connections, setConnections] = useState<Connection[]>([]);
    const [filteredConnections, setFilteredConnections] = useState<Connection[]>([]); // Add this
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const processData = (nodes: any[], relationships: any[]) => {
        // Ensure nodes have the right structure
        const validNodes = nodes.filter((node: any) => node.latitude && node.longitude)
        .map((node: any) => ({
            ...node,
            // Ensure stop_id is treated as a string
            stop_id: String(node.stop_id),
            // Ensure other required properties exist
            id: node.id || String(node.stop_id),
            east_west: node.east_west || 'unknown'
        }));

        // Process connections
        const processedPairs = new Set<string>();
        const uniqueConnections = relationships.filter(connection => {
            // Filter valid connections
            if (!connection.startNodeId || !connection.endNodeId) return false;
            
            const pair = [connection.startNodeId, connection.endNodeId].sort().join('-');
            if (processedPairs.has(pair)) return false;
            
            processedPairs.add(pair);
            return true;
        }).map(conn => {
            // Ensure connection properties are in the right format
            if (conn.properties) {
                // Handle capacities, frequencies and line_ids which might have different formats
                if (conn.properties.capacities && !Array.isArray(conn.properties.capacities)) {
                    conn.properties.capacities = [conn.properties.capacities];
                }
                if (conn.properties.frequencies && !Array.isArray(conn.properties.frequencies)) {
                    conn.properties.frequencies = [conn.properties.frequencies];
                }
                if (conn.properties.line_ids && !Array.isArray(conn.properties.line_ids)) {
                    conn.properties.line_ids = [conn.properties.line_ids];
                }
                if (conn.properties.line_names && !Array.isArray(conn.properties.line_names)) {
                    conn.properties.line_names = [conn.properties.line_names];
                }
            }
            return conn;
        });

        setStations(validNodes);
        setConnections(uniqueConnections);
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/network-snapshot/${selectedYear}`, {
                params: selectedType ? { type: selectedType } : undefined
            });
            
            processData(response.data.nodes, response.data.relationships);
            setError(null);
        } catch (err) {
                console.error('Detailed error:', err); // More detailed error logging
                if (axios.isAxiosError(err)) {
                    setError(err.message);
                    if (err.response) {
                        console.error('Response data:', err.response.data);
                        console.error('Response status:', err.response.status);
                    }
                } else {
                    setError('An unexpected error occurred');
                }
            } finally {
                setLoading(false);
        }
    };
    
    const updateStation = async (stopId: string, latitude: number, longitude: number, token: string) => {
        try {
            await api.post(
                `/stations/${stopId}/update`,
                { latitude, longitude },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    }
                }
            );
            await fetchData();
            return true;
        } catch (err) {
            console.error('Station update error:', err);
            throw err;
        }
    };

    useEffect(() => {
        let filtered = connections;
    
        if (selectedType) {
            filtered = filtered.filter(conn => 
                conn.properties.transport_type === selectedType
            );
        }
        
        if (selectedLine) {
            filtered = filtered.filter(conn => {
                // Handle different potential data structures
                if (!conn.properties.line_names) return false;
                
                // Ensure line_names is treated as an array
                const lineNames = Array.isArray(conn.properties.line_names) 
                    ? conn.properties.line_names
                    : [conn.properties.line_names];
                    
                // Convert to strings for comparison since data might contain numbers
                return lineNames.some(name => String(name) === String(selectedLine));
            });
        }
    
        setFilteredConnections(filtered);
    }, [connections, selectedType, selectedLine]);

    useEffect(() => {
        console.log('Raw connections from API:', connections);
        console.log('Filtered connections:', filteredConnections);
      }, [connections, filteredConnections]);

      const getLineNames = useCallback(() => {
        console.log('Raw connections for line filtering:', connections);
        const filteredConnections = selectedType 
          ? connections.filter((conn) => conn.properties.transport_type === selectedType)
          : connections;
        
        const lineNames = Array.from(new Set(
          filteredConnections.flatMap((conn) => {
            console.log('Connection line_names:', conn.properties.line_names);
            return conn.properties.line_names || [];
          })
        )).sort();
        
        console.log('Extracted line names:', lineNames);
        return lineNames;
      }, [connections, selectedType]);

      // Example usage of getLineNames to avoid unused declaration
      useEffect(() => {
        const lineNames = getLineNames();
        console.log('Available line names:', lineNames);
      }, [getLineNames]);
      

    // Separate effect for data fetching
    useEffect(() => {
        const fetchDataWithDelay = async () => {
            try {
                setLoading(true);
                await new Promise(resolve => setTimeout(resolve, 500));
                const response = await api.get(`/network-snapshot/${selectedYear}`, {
                    params: selectedType ? { type: selectedType } : undefined
                });
                processData(response.data.nodes, response.data.relationships);
                setError(null);
            } catch (err) {
                console.error('Detailed error:', err);
                if (axios.isAxiosError(err)) {
                    setError(err.message);
                    if (err.response) {
                        console.error('Response data:', err.response.data);
                        console.error('Response status:', err.response.status);
                    }
                } else {
                    setError('An unexpected error occurred');
                }
            } finally {
                setLoading(false);
            }
        };
        
        fetchDataWithDelay();
    }, [selectedYear, selectedType]);

    return { 
        stations, 
        connections: filteredConnections, // Return filtered connections instead of all connections
        loading, 
        error, 
        refetch: fetchData, 
        updateStation 
    };
};
export default useNetworkData;