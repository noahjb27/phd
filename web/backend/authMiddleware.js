const jwt = require('jsonwebtoken');

// Middleware to verify authentication
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ message: 'Access denied. No token provided.' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET); // Replace with your JWT secret
    req.user = decoded; // Attach the decoded user data to the request
    next(); // Proceed to the next middleware/route handler
  } catch (error) {
    res.status(403).json({ message: 'Invalid token.' });
  }
};

module.exports = authenticateToken;
