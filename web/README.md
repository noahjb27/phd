# Berlin Transport History Project

## Project Overview

The Berlin Transport History Project is a digital humanities research platform examining the evolution of Berlin's public transportation system from 1945-1989, with a particular focus on the Cold War period. This web application combines historical research with interactive visualizations to explore how Berlin's divided public transport networks evolved over time.

The project consists of:
- A comprehensive database of historical transportation data
- Interactive web-based visualizations (station network and postal code maps)
- Educational articles and blog posts on Berlin's transport history
- Research tools for network analysis and historical comparison

### Research Goals

- Understanding Berlin's historical public transportation system development
- Examining differences between East and West Berlin transport networks
- Creating a digital resource for researchers, students, and the public
- Preserving and visualizing transport history through time-based analysis

## System Architecture

The application uses a containerized microservice architecture with the following components:

```
Client Browser → Cloudflare → Nginx (Reverse Proxy) → Frontend/Backend Services → Neo4j Database
```

### Components

- **Frontend**: Next.js React application serving the user interface
- **Backend**: Express.js API providing data access and processing
- **Database**: Neo4j graph database storing historical transport network data
- **Nginx**: Reverse proxy handling routing between components
- **Docker**: Container management for deployment and scaling

## Technical Stack

### Frontend
- **Framework**: Next.js with TypeScript
- **UI Components**: Custom React components styled with Tailwind CSS
- **State Management**: React hooks and context
- **Authentication**: NextAuth.js
- **Visualization Libraries**: Leaflet.js for maps
- **Content Management**: Markdown for articles and blog posts

### Backend
- **Framework**: Express.js (Node.js)
- **Authentication**: JWT-based authentication
- **Caching**: Node-cache for API response caching
- **API**: RESTful endpoints for data access

### Database
- **Neo4j Graph Database**: Stores transportation network data modeled as a graph
- **Schema**: Custom schema for modeling temporal aspects of transportation networks

### Infrastructure
- **Docker & Docker Compose**: Application containerization
- **Nginx**: Reverse proxy and static file serving
- **Cloudflare**: DNS management and DDoS protection

## Database Schema

The application uses a graph database to represent the complex relationships in Berlin's transport network. The schema includes:

### Node Types
- **Station**: Transportation stops with properties including coordinates, name, type
- **Line**: Transport routes with properties like frequency, capacity, length
- **Year**: Temporal nodes representing specific years for historical tracking
- **District**: Administrative regions of Berlin
- **Ortsteil**: Sub-districts or neighborhoods
- **PostalCode**: Postal code regions

### Relationships
- **SERVES**: Connects Line nodes to Station nodes
- **CONNECTS_TO**: Links directly connected Station nodes
- **IN_YEAR**: Temporal relationship connecting Station and Line nodes to Year nodes
- **IN_DISTRICT**: Links Station nodes to their administrative District
- **IN_ORTSTEIL**: Links Station nodes to their neighborhood Ortsteil
- **IN_POSTAL_CODE**: Links Station nodes to their PostalCode

## Data Sources

The application incorporates data from various historical sources:

- **Fahrplanbücher**: Historical timetables for Berlin's public transport
- **Historical Maps**: Georeferenced historical maps of Berlin
- **Statistical Data**: Population and transportation statistics
- **Archival Material**: Reports from transport authorities

## Main Features

### Interactive Network Visualization

- **Year-based Timeline**: View the transportation network at specific points in time
- **Transport Type Filtering**: Filter by transport mode (U-Bahn, S-Bahn, tram, bus)
- **Line Filtering**: View specific transit lines
- **Berlin Wall Overlay**: Toggle the historical Berlin Wall on the map
- **Historical Map Layers**: Multiple historical map overlays
- **Station Details**: View metadata about specific stations

### Postal Code (PLZ) Visualization

- **Area-based Analysis**: View transportation network data aggregated by postal code
- **Heat Map Visualization**: Color-coded intensity based on service levels
- **East-West Comparison**: Compare transportation coverage between East and West Berlin

### Content Features

- **Research Articles**: In-depth analysis of Berlin's transport history
- **Blog Posts**: Updates on research progress and historical insights
- **Methodology Documentation**: Explanations of research approaches
- **About Pages**: Information about the project and its goals

### Administrative Features

- **Station Geo-correction**: Admin interface for updating station coordinates
- **Authentication**: Secure login for administrative users
- **Monitoring**: System health and performance monitoring

## Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for development)
- Neo4j Desktop (optional, for local database management)
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/berlin-transport-history.git
   cd berlin-transport-history
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Install dependencies:
   ```bash
   # Frontend dependencies
   cd web/frontend
   npm install
   
   # Backend dependencies
   cd ../backend
   npm install
   ```

4. Start the development environment:
   ```bash
   # From the project root
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. Access the development server:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Neo4j Browser: http://localhost:7474

### Production Deployment

1. Build and start the production containers:
   ```bash
   docker-compose up -d --build
   ```

2. Configure Nginx for your domain:
   - Update `nginx/default.conf` with your domain settings
   - Set up SSL certificates using Let's Encrypt or Cloudflare

3. Set up Cloudflare for DNS management and additional security

4. Run the monitoring script periodically:
   ```bash
   ./monitor.sh
   ```

## Database Management

### Populating the Database

Use the provided Python scripts in the `data/fahrplanbuch/src` directory:

```bash
# Setup the database schema
python db_schema.py

# Import data for specific years and sides of Berlin
python populate_db.py --years 1964 1965 --sides east west
```

### Updating Station Data

Station coordinates can be corrected through the admin interface or directly via API:

```bash
curl -X POST https://berlin-transport-history.de/api/stations/19640_east/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 52.50910764, "longitude": 13.43550619}'
```

## Configuration Details

### Nginx Configuration

The Nginx configuration handles routing between frontend and backend services:

```nginx
server {
    listen 80;
    server_name localhost;
    
    # Frontend routes
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API endpoints
    location /api/ {
        proxy_pass http://backend:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Variables

The application uses several environment variables for configuration:

```
# Database settings
DB_HOST=bolt://neo4j:7687
DB_PASSWORD=BerlinTransport2024

# Authentication
JWT_SECRET=your_secret_key
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=https://berlin-transport-history.de

# API configuration
NEXT_PUBLIC_API_URL=/api
```

## Development Guidelines

### Code Structure

- **Frontend**: Component-based architecture with Next.js
  - `/src/components`: Reusable UI components
  - `/src/pages`: Next.js page components and API routes
  - `/src/data`: Content for blog and articles
  - `/src/util`: Utility functions and helpers

- **Backend**: Express.js REST API
  - `/routes.js`: API route definitions
  - `/server.js`: Main application entry point
  - `/authMiddleware.js`: Authentication middleware
  - `/neo4j.js`: Database connection and query helpers

### Adding New Features

1. **New Visualization Type**:
   - Add new component in `/src/components/visualizations`
   - Create corresponding API endpoint in backend if needed
   - Add route in frontend pages

2. **New Content**:
   - Add Markdown files to `/src/data/blog` or `/src/data/articles`
   - Images should be placed in `/public/images`

3. **New Data Source**:
   - Add import scripts to `/data/fahrplanbuch/src`
   - Update database schema if needed
   - Add data processing to backend API

## Troubleshooting

### Common Issues

1. **API 404 Errors**:
   - Check Nginx configuration - ensure `/api/` location block uses `proxy_pass http://backend:5000/api/`
   - Verify backend is running with `docker-compose ps`
   - Check backend logs with `docker-compose logs backend`

2. **Database Connection Issues**:
   - Verify Neo4j container is running with `docker-compose ps`
   - Check Neo4j connection string in backend environment variables
   - Ensure correct credentials are being used

3. **Visualization Not Loading**:
   - Check browser console for JavaScript errors
   - Verify network requests to API endpoints succeed
   - Check data format matches expected frontend format

4. **Docker Container Failures**:
   - Check logs with `docker-compose logs [service_name]`
   - Verify all required environment variables are set
   - Ensure proper network connectivity between containers

### Monitoring

The project includes a monitoring script (`monitor.sh`) to check system health:

```bash
./monitor.sh
# Or add to crontab for regular checks
# */15 * * * * /path/to/berlin-transport-project/monitor.sh >> /path/to/logs/monitoring.log 2>&1
```

## Maintenance Procedures

### Backups

Regularly backup the Neo4j database:

```bash
# From the project root
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +"%Y%m%d").dump
```

### Updates

1. **Update Dependencies**:
   ```bash
   # Update frontend
   cd web/frontend
   npm update
   
   # Update backend
   cd ../backend
   npm update
   ```

2. **Rebuild Containers**:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Data Updates**:
   ```bash
   # Import new years or data
   python data/fahrplanbuch/src/populate_db.py --years 1966 --sides east west
   ```

## License & Attribution

This project is developed as part of PhD research at Humboldt University of Berlin. When using or citing this project, please use the following attribution:

> Baumann, N. (2025). Berlin Public Transport History: A Digital History of Berlin's Cold War Public Transportation. https://berlin-transport-history.de

## Contact

For questions, feedback, or collaboration inquiries, please contact:

Noah J. Baumann  
[noah.baumann@yahoo.de](mailto:noah.baumann@yahoo.de)

---

*Last updated: April 30, 2025*