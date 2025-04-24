// backend/neo4j.js
require('dotenv').config();
const password = process.env.DB_PASSWORD;
const host = process.env.DB_HOST;

const neo4j = require('neo4j-driver');

const driver = neo4j.driver(
    host, 
  neo4j.auth.basic('neo4j', password)
);

module.exports = driver;
