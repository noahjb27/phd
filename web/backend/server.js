const express = require('express');
const app = express();
const routes = require('./routes');
const cors = require('cors');

// Define allowed origins
const allowedOrigins = [
  'https://app.berlin-transport-history.me',
  'http://64.226.82.241:3000',  // Your production frontend
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

app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

const port = process.env.PORT || 8000; // default to 8000 to match Docker
app.listen(port, '0.0.0.0', () => {  // '0.0.0.0' to bind to all interfaces
  console.log(`Server listening on port ${port}`);
});