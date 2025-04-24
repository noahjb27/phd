import axios from 'axios';

const BASE_URL = 'https://gdi.berlin.de/services/wfs/berlinermauer';

export interface Feature {
  properties: any;
  type: string;
  id: string;
  geometry: {
    type: string;
    coordinates: number[][];
  };
}

export const fetchBerlinWallFeatures = async (): Promise<Feature[]> => {
  try {
    const response = await axios.get(`${BASE_URL}?service=WFS&version=2.0.0&request=GetFeature&typeNames=berlinermauer:a_grenzmauer&outputFormat=application/json`);
    return response.data.features;
  } catch (error) {
    console.error('Error fetching Berlin Wall features:', error);
    throw error;
  }
};