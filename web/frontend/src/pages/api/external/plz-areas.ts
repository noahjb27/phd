// pages/api/plz-areas.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const filePath = path.join(process.cwd(), 'public', 'berlin_postal_districts.json');
    
    if (!fs.existsSync(filePath)) {
      console.error('PLZ areas file not found at:', filePath);
      return res.status(404).json({ error: 'PLZ areas data not found' });
    }

    const fileContents = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(fileContents);
    
    res.setHeader('Content-Type', 'application/json');
    res.status(200).json(data);
  } catch (error) {
    console.error('Error serving PLZ areas:', error);
    res.status(500).json({ 
      error: 'Failed to load PLZ areas data', 
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
