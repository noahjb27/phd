// hooks/useAvailableYears.ts
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
});

const useAvailableYears = () => {
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        setLoading(true);
        const response = await api.get('/available-years');
        setAvailableYears(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching available years:', err);
        if (axios.isAxiosError(err)) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred');
        }
        // Fallback to default years if API fails
        setAvailableYears([1946, 1951, 1956, 1960, 1961, 1964, 1965, 1967, 1971]);
      } finally {
        setLoading(false);
      }
    };

    fetchAvailableYears();
  }, []);

  return { availableYears, loading, error };
};

export default useAvailableYears;