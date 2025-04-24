// hooks/useNetworkData.ts
import { useState, useEffect } from 'react';
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

    const processData = (nodes: StationNode[], relationships: Connection[]) => {
        const validNodes = nodes.filter((node: StationNode) => node.latitude && node.longitude);
        
        // Create Set to track processed connections
        const processedPairs = new Set<string>();
        const uniqueConnections = relationships.filter(connection => {
            const pair = [connection.startNodeId, connection.endNodeId].sort().join('-');
            if (processedPairs.has(pair)) {
                return false;
            }
            processedPairs.add(pair);
            return true;
        });

        setStations(validNodes);
        setConnections(uniqueConnections);
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/api/network-snapshot/${selectedYear}`, {
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
                `/api/stations/${stopId}/update`,
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
            filtered = filtered.filter(conn => 
                conn.properties.line_names.includes(selectedLine)
            );
        }
    
        setFilteredConnections(filtered);
    }, [connections, selectedType, selectedLine]);

         // Separate effect for data fetching
    useEffect(() => {
        const fetchDataWithDelay = async () => {
            try {
                setLoading(true);
                await new Promise(resolve => setTimeout(resolve, 500));
                const response = await api.get(`/api/network-snapshot/${selectedYear}`, {
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