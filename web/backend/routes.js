// backend/routes.js
const express = require('express');
const router = express.Router();
const driver = require('./neo4j');
const neo4j = require('neo4j-driver');
const authenticateToken = require('./authMiddleware'); // Import the middleware
const NodeCache = require('node-cache'); // Import node-cache
const cache = new NodeCache(); // Initialize cache
const fs = require('fs');
const path = require('path');

// Middleware to parse JSON bodies
router.use(express.json());

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Test Neo4j Aura connection
    const session = driver.session();
    await session.run('MATCH (n) RETURN count(n) LIMIT 1');
    await session.close();
    
    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected',
      server: process.env.NODE_ENV || 'unknown'
    });
  } catch (error) {
    console.error('Health check failed:', error);
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      database: 'disconnected',
      error: error.message
    });
  }
});

router.get('/graph-data', async (req, res) => {
    const session = driver.session();
    try {
      const result = await session.run(`
        MATCH (n)-[r]->(m)
        RETURN n, r, m
      `);
  
      const nodes = {};
      const relationships = [];
  
      result.records.forEach(record => {
        const n = record.get('n');
        const m = record.get('m');
        const r = record.get('r');
  
        // Process nodes
        [n, m].forEach(node => {
          const nodeId = node.identity.toString();
          if (!nodes[nodeId]) {
            nodes[nodeId] = {
              id: nodeId,
              ...node.properties,
            };
  
            // Convert Neo4j integers to JavaScript numbers
            for (const [key, value] of Object.entries(nodes[nodeId])) {
              if (neo4j.isInt(value)) {
                nodes[nodeId][key] = value.toNumber();
              }
            }
          }
        });
  
        // Process relationships
        relationships.push({
          id: r.identity.toString(),
          type: r.type,
          startNodeId: r.start.toString(),
          endNodeId: r.end.toString(),
          properties: r.properties,
        });
      });
  
      res.json({ nodes: Object.values(nodes), relationships });
    } catch (error) {
      console.error('Error fetching data:', error);
      res.status(500).json({ error: error.message });
    } finally {
      await session.close();
    }
  });

router.get('/available-years', async (req, res) => {
  const cacheKey = 'available_years';
  
  // Check cache first
  const cachedData = cache.get(cacheKey);
  if (cachedData) {
    return res.json(cachedData);
  }

  const session = driver.session();
  try {
    const result = await session.run(`
      MATCH (y:Year)
      RETURN y.year as year
      ORDER BY y.year ASC
    `);

    const years = result.records.map(record => {
      const year = record.get('year');
      // Handle Neo4j integer conversion
      return neo4j.isInt(year) ? year.toNumber() : year;
    });

    // Cache for 1 hour since years don't change frequently
    cache.set(cacheKey, years, 3600);
    
    res.json(years);
  } catch (error) {
    console.error('Error fetching available years:', error);
    res.status(500).json({ error: error.message });
  } finally {
    await session.close();
  }
});

//  dedicated route for year-specific queries
router.get('/network-snapshot/:year', async (req, res) => {
  const year = parseInt(req.params.year);
  const type = req.query.type; // Optional transport type filter
  const cacheKey = `network_${year}_${type || 'all'}`;
  console.log(`Fetching network snapshot for year: ${year}, type: ${type || 'all'}`);

  // Check cache first
  const cachedData = cache.get(cacheKey);
  if (cachedData) {
      return res.json(cachedData);
  }

  const session = driver.session();
  try {
    const query = `
      MATCH (year:Year {year: $year})
      MATCH (s:Station)-[in:IN_YEAR]->(year)
      ${type ? 'WHERE s.type = $type' : ''}
      WITH s
      OPTIONAL MATCH (s)-[c:CONNECTS_TO]-(other:Station)-[:IN_YEAR]->(year)
      ${type ? 'WHERE c.transport_type = $type' : ''}
      RETURN DISTINCT s, c, other
    `;
      
      const result = await session.run(query, { 
          year: neo4j.int(year),
          type: type 
      });

      // Process the data
      const nodes = {};
      const relationships = [];

      result.records.forEach(record => {
          // Process station node
          const station = record.get('s');
          const nodeId = station.identity.toString();
          if (!nodes[nodeId]) {
              nodes[nodeId] = {
                  id: nodeId,
                  ...station.properties,
                  stop_id: station.properties.stop_id.toString()
              };
          }

          // Process other station node if exists
          const other = record.get('other');
          if (other) {
              const otherId = other.identity.toString();
              if (!nodes[otherId]) {
                  nodes[otherId] = {
                      id: otherId,
                      ...other.properties,
                      stop_id: other.properties.stop_id.toString()
                  };
              }
          }

          // Process connection if exists
          const connection = record.get('c');
          if (connection) {
              // Transform connection properties to match frontend expectations
              const connectionProps = {...connection.properties};
              
              // Ensure arrays are properly formatted
              ['capacities', 'frequencies', 'line_ids', 'line_names'].forEach(propName => {
                if (connectionProps[propName] && !Array.isArray(connectionProps[propName])) {
                  connectionProps[propName] = [connectionProps[propName]];
                }
              });
              relationships.push({
                  id: connection.identity.toString(),
                  type: connection.type,
                  startNodeId: connection.start.toString(),
                  endNodeId: connection.end.toString(),
                  properties: connection.properties,
              });
          }
      });

      const networkData = {
          nodes: Object.values(nodes),
          relationships
      };

      // Cache the processed data
      console.log(`Returning ${networkData.nodes.length} nodes and ${networkData.relationships.length} relationships`);

      cache.set(cacheKey, networkData);
      res.json(networkData);

  } catch (error) {
      console.error('Error fetching network snapshot:', error);
      res.status(500).json({ error: error.message });
  } finally {
      await session.close();
  }
});

// Update the route to match the frontend request
router.post('/stations/:stopId/update', authenticateToken, async (req, res) => {
  const session = driver.session();
  const { stopId } = req.params;
  const { latitude, longitude } = req.body;

  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    return res.status(400).json({ error: 'Invalid latitude or longitude' });
  }

  try {
    const result = await session.run(
      `
      MATCH (station {stop_id: $stopId})
      SET station.latitude = $latitude, station.longitude = $longitude
      RETURN station
      `,
      {
        stopId: neo4j.int(stopId),
        latitude: latitude,
        longitude: longitude,
      }
    );
    console.log('Query result:', result.records[0]?.get('station').properties);

    if (result.records.length === 0) {
      return res.status(404).json({ error: 'Station not found' });
    }

    const updatedStation = result.records[0].get('station').properties;
    res.status(200).json({ 
      message: 'Station updated successfully', 
      station: updatedStation 
    });
  } catch (error) {
    console.error('Error updating station:', error);
    res.status(500).json({ error: error.message });
  } finally {
    await session.close();
  }
});

module.exports = router;
