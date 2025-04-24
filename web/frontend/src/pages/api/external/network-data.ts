// pages/api/network-data.ts
import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const filePath = path.join(process.cwd(), 'public', 'network-data.json');
    const fileContents = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(fileContents);
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to load network data' });
  }
}