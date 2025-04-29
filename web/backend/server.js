const express = require('express');
const app = express();
const routes = require('./routes');
const cors = require('cors');

// Define allowed origins
const allowedOrigins = [
  'https://berlin-transport-history.de',
  'http://localhost:3000'        // Local development
];

// Configure CORS options
const corsOptions = {
  origin: function (origin, callback) {
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
};

// Apply CORS with options
app.use(cors(corsOptions));
app.use(express.json());

app.use('/api', routes);

const port = process.env.PORT || 5000; 
app.listen(port, '0.0.0.0', () => { 
  console.log(`Server listening on port ${port}`);
});
