// backend/neo4j.js
require('dotenv').config();
const password = process.env.NEO4J_AURA_PASSWORD; // NEO4J_AURA_PASSWORD or DB_PASSWORD
const host = process.env.NEO4J_AURA_URI; // NEO4J_AURA_URI or DB_HOST

const neo4j = require('neo4j-driver');

const driver = neo4j.driver(
    host, 
  neo4j.auth.basic('neo4j', password)
);

module.exports = driver;
