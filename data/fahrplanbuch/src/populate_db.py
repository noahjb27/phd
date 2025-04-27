"""
Script to populate Neo4j database with Berlin transport data.
"""

import pandas as pd
from pathlib import Path
import logging
from db_connector import BerlinTransportDB
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DB_URI = "bolt://100.82.176.18:7687"
DB_USER = "neo4j"
DB_PASSWORD = os.environ.get("NEO4J_PASSWORD")  # Set via environment variable
DATA_DIR = Path("../data/processed")

# Initialize database connection
db = BerlinTransportDB(uri=DB_URI, username=DB_USER, password=DB_PASSWORD)

def setup_schema():
    """Create necessary constraints and indexes in Neo4j"""
    logger.info("Setting up database schema...")
    
    try:
        with db.driver.session() as session:
            # Create constraints for uniqueness
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.stop_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Line) REQUIRE l.line_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (y:Year) REQUIRE y.year IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Ortsteil) REQUIRE o.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:PostalCode) REQUIRE p.code IS UNIQUE")
            
            # Create indexes for performance
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Station) ON (s.name, s.type)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Station) ON (s.east_west)")
            
            logger.info("Schema setup complete")
            return True
    except Exception as e:
        logger.error(f"Error setting up schema: {e}")
        return False

def import_year_data(year_side_dir):
    """Import data for a specific year and side of Berlin"""
    try:
        # Extract year and side from directory name
        year_side = year_side_dir.name
        year, side = year_side.split('_')
        
        logger.info(f"Importing data for {year}_{side}...")
        
        # Create Year node
        with db.driver.session() as session:
            session.run("MERGE (y:Year {year: $year})", year=int(year))
        
        # Import stops
        import_stations(year_side_dir / "stops.csv", int(year), side)
        
        # Import lines
        import_lines(year_side_dir / "lines.csv", int(year))
        
        # Import line-stop relationships
        import_line_stops(year_side_dir / "line_stops.csv")
        
        logger.info(f"Data import completed for {year}_{side}")
        return True
    except Exception as e:
        logger.error(f"Error importing data for {year_side_dir.name}: {e}")
        return False

def import_stations(file_path, year, side):
    """Import stations from CSV file"""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        # Read stations CSV
        stops_df = pd.read_csv(file_path)
        logger.info(f"Importing {len(stops_df)} stations from {file_path}")
        
        # Process in batches for better performance
        batch_size = 200
        total_batches = (len(stops_df) - 1) // batch_size + 1
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(stops_df))
            batch = stops_df.iloc[start_idx:end_idx]
            
            # Create Cypher parameters for this batch
            stations_params = []
            for _, row in batch.iterrows():
                # Parse coordinates if available
                lat, lng = None, None
                if pd.notna(row.get('location')):
                    try:
                        lat, lng = map(float, str(row['location']).split(','))
                    except (ValueError, TypeError):
                        pass
                
                # Prepare station parameters
                station_param = {
                    "stop_id": str(row['stop_id']),
                    "name": row['stop_name'],
                    "type": row['type'],
                    "east_west": side,
                    "latitude": lat,
                    "longitude": lng,
                    "year": year
                }
                
                # Add optional fields if available
                if 'district' in row and pd.notna(row['district']):
                    station_param["district"] = row['district']
                if 'neighbourhood' in row and pd.notna(row['neighbourhood']):
                    station_param["neighbourhood"] = row['neighbourhood']
                if 'postal_code' in row and pd.notna(row['postal_code']):
                    station_param["postal_code"] = row['postal_code']
                if 'identifier' in row and pd.notna(row['identifier']):
                    station_param["identifier"] = row['identifier']
                
                stations_params.append(station_param)
            
            # Execute batch import
            with db.driver.session() as session:
                result = session.run("""
                UNWIND $stations AS station
                MATCH (y:Year {year: station.year})
                
                // Create Station
                MERGE (s:Station {stop_id: station.stop_id})
                SET s.name = station.name,
                    s.type = station.type,
                    s.east_west = station.east_west
                
                // Set coordinates if available
                FOREACH (ignoreMe IN CASE WHEN station.latitude IS NOT NULL AND station.longitude IS NOT NULL 
                         THEN [1] ELSE [] END | 
                    SET s.latitude = station.latitude,
                        s.longitude = station.longitude
                )
                
                // Connect to Year
                MERGE (s)-[:IN_YEAR]->(y)
                
                // Connect to District if available
                FOREACH (district IN CASE WHEN station.district IS NOT NULL THEN [station.district] ELSE [] END |
                    MERGE (d:District {name: district})
                    MERGE (s)-[:IN_DISTRICT]->(d)
                )
                
                // Connect to Neighbourhood if available
                FOREACH (neighbourhood IN CASE WHEN station.neighbourhood IS NOT NULL THEN [station.neighbourhood] ELSE [] END |
                    MERGE (o:Ortsteil {name: neighbourhood})
                    MERGE (s)-[:IN_ORTSTEIL]->(o)
                )
                
                // Connect to PostalCode if available
                FOREACH (postalCode IN CASE WHEN station.postal_code IS NOT NULL THEN [station.postal_code] ELSE [] END |
                    MERGE (p:PostalCode {code: postalCode})
                    MERGE (s)-[:IN_POSTAL_CODE]->(p)
                )
                
                RETURN count(s) as count
                """, stations=stations_params)
                
                count = result.single()["count"]
                logger.info(f"Imported batch {i+1}/{total_batches} with {count} stations")
        
        return True
    except Exception as e:
        logger.error(f"Error importing stations: {e}")
        return False

def import_lines(file_path, year):
    """Import lines from CSV file"""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        # Read lines CSV
        lines_df = pd.read_csv(file_path)
        logger.info(f"Importing {len(lines_df)} lines from {file_path}")
        
        # Process in batches
        batch_size = 50
        total_batches = (len(lines_df) - 1) // batch_size + 1
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(lines_df))
            batch = lines_df.iloc[start_idx:end_idx]
            
            # Create Cypher parameters
            lines_params = []
            for _, row in batch.iterrows():
                line_param = {
                    "line_id": str(row['line_id']),
                    "name": row['line_name'],
                    "type": row['type'],
                    "east_west": row['east_west'],
                    "year": year
                }
                
                # Add optional fields
                if 'frequency (7:30)' in row and pd.notna(row['frequency (7:30)']):
                    line_param["frequency"] = row['frequency (7:30)']
                if 'capacity' in row and pd.notna(row['capacity']):
                    line_param["capacity"] = row['capacity']
                if 'length (time)' in row and pd.notna(row['length (time)']):
                    line_param["length_time"] = row['length (time)']
                if 'length (km)' in row and pd.notna(row['length (km)']):
                    line_param["length_km"] = row['length (km)']
                if 'profile' in row and pd.notna(row['profile']):
                    line_param["profile"] = row['profile']
                
                lines_params.append(line_param)
            
            # Execute batch import
            with db.driver.session() as session:
                result = session.run("""
                UNWIND $lines AS line
                MATCH (y:Year {year: line.year})
                
                // Create Line
                MERGE (l:Line {line_id: line.line_id})
                SET l.name = line.name,
                    l.type = line.type,
                    l.east_west = line.east_west
                
                // Set optional properties
                FOREACH (ignoreMe IN CASE WHEN line.frequency IS NOT NULL THEN [1] ELSE [] END | 
                    SET l.frequency = line.frequency
                )
                FOREACH (ignoreMe IN CASE WHEN line.capacity IS NOT NULL THEN [1] ELSE [] END | 
                    SET l.capacity = line.capacity
                )
                FOREACH (ignoreMe IN CASE WHEN line.length_time IS NOT NULL THEN [1] ELSE [] END | 
                    SET l.length_time = line.length_time
                )
                FOREACH (ignoreMe IN CASE WHEN line.length_km IS NOT NULL THEN [1] ELSE [] END | 
                    SET l.length_km = line.length_km
                )
                FOREACH (ignoreMe IN CASE WHEN line.profile IS NOT NULL THEN [1] ELSE [] END | 
                    SET l.profile = line.profile
                )
                
                // Connect to Year
                MERGE (l)-[:IN_YEAR]->(y)
                
                RETURN count(l) as count
                """, lines=lines_params)
                
                count = result.single()["count"]
                logger.info(f"Imported batch {i+1}/{total_batches} with {count} lines")
        
        return True
    except Exception as e:
        logger.error(f"Error importing lines: {e}")
        return False

def import_line_stops(file_path):
    """Import line-stop relationships from CSV file"""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        # Read line_stops CSV
        line_stops_df = pd.read_csv(file_path)
        logger.info(f"Importing {len(line_stops_df)} line-stop relationships from {file_path}")
        
        # Process in batches
        batch_size = 500
        total_batches = (len(line_stops_df) - 1) // batch_size + 1
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(line_stops_df))
            batch = line_stops_df.iloc[start_idx:end_idx]
            
            # Create Cypher parameters
            relations_params = []
            for _, row in batch.iterrows():
                relation_param = {
                    "line_id": str(row['line_id']),
                    "stop_id": str(row['stop_id']),
                    "stop_order": int(row['stop_order'])
                }
                relations_params.append(relation_param)
            
            # Execute batch import
            with db.driver.session() as session:
                result = session.run("""
                UNWIND $relations AS rel
                MATCH (l:Line {line_id: rel.line_id})
                MATCH (s:Station {stop_id: rel.stop_id})
                MERGE (l)-[r:SERVES]->(s)
                SET r.stop_order = rel.stop_order
                RETURN count(r) as count
                """, relations=relations_params)
                
                count = result.single()["count"]
                logger.info(f"Imported batch {i+1}/{total_batches} with {count} relationships")
        
        return True
    except Exception as e:
        logger.error(f"Error importing line-stop relationships: {e}")
        return False

def create_station_connections():
    """Create CONNECTS_TO relationships between stations based on line sequence"""
    logger.info("Creating station connections...")
    
    try:
        with db.driver.session() as session:
            # This query finds adjacent stops on the same line and creates CONNECTS_TO relationships
            result = session.run("""
            MATCH (l:Line)-[s1:SERVES]->(station1:Station)
            MATCH (l)-[s2:SERVES]->(station2:Station)
            WHERE s1.stop_order = s2.stop_order - 1
            
            MERGE (station1)-[c:CONNECTS_TO]->(station2)
            ON CREATE SET 
                c.line_ids = [l.line_id],
                c.line_names = [l.name],
                c.transport_type = l.type,
                c.capacities = CASE WHEN l.capacity IS NOT NULL THEN [l.capacity] ELSE [] END,
                c.frequencies = CASE WHEN l.frequency IS NOT NULL THEN [l.frequency] ELSE [] END
            ON MATCH SET
                c.line_ids = CASE WHEN NOT l.line_id IN c.line_ids THEN c.line_ids + l.line_id ELSE c.line_ids END,
                c.line_names = CASE WHEN NOT l.name IN c.line_names THEN c.line_names + l.name ELSE c.line_names END,
                c.capacities = CASE WHEN l.capacity IS NOT NULL AND NOT l.capacity IN c.capacities 
                                THEN c.capacities + l.capacity ELSE c.capacities END,
                c.frequencies = CASE WHEN l.frequency IS NOT NULL AND NOT l.frequency IN c.frequencies 
                                THEN c.frequencies + l.frequency ELSE c.frequencies END
            
            RETURN count(c) as connections_created
            """)
            
            connections = result.single()["connections_created"]
            logger.info(f"Created {connections} station connections")
            
            return True
    except Exception as e:
        logger.error(f"Error creating station connections: {e}")
        return False

def verify_data_import():
    """Verify data was imported correctly"""
    logger.info("Verifying data import...")
    
    try:
        with db.driver.session() as session:
            # Count nodes
            counts = {}
            for label in ["Station", "Line", "Year", "District", "Ortsteil", "PostalCode"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                counts[label] = result.single()["count"]
            
            # Count relationships
            for rel_type in ["IN_YEAR", "SERVES", "CONNECTS_TO", "IN_DISTRICT", "IN_ORTSTEIL", "IN_POSTAL_CODE"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                counts[rel_type] = result.single()["count"]
            
            # Print summary
            logger.info("Database contents:")
            for key, count in counts.items():
                logger.info(f"  {key}: {count}")
            
            # Check for data problems
            problems = []
            
            # Stations without coordinates
            result = session.run("""
            MATCH (s:Station)
            WHERE s.latitude IS NULL OR s.longitude IS NULL
            RETURN count(s) as count
            """)
            missing_coords = result.single()["count"]
            if missing_coords > 0:
                problems.append(f"{missing_coords} stations missing coordinates")
            
            # Stations not connected to any line
            result = session.run("""
            MATCH (s:Station)
            WHERE NOT (s)<-[:SERVES]-()
            RETURN count(s) as count
            """)
            orphan_stations = result.single()["count"]
            if orphan_stations > 0:
                problems.append(f"{orphan_stations} stations not connected to any line")
            
            if problems:
                logger.warning("Potential data issues found:")
                for problem in problems:
                    logger.warning(f"  - {problem}")
            else:
                logger.info("No data issues found")
            
            return True
    except Exception as e:
        logger.error(f"Error verifying data import: {e}")
        return False

def main():
    """Main function to run the import process"""
    logger.info("Starting data import process...")
    
    try:
        # Connect to database
        db.connect()
        
        # Setup schema
        if not setup_schema():
            logger.error("Failed to set up schema, aborting import")
            return
        
        # Find data directories to import
        data_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]
        logger.info(f"Found {len(data_dirs)} data directories to import")
        
        # Import each data directory
        for data_dir in data_dirs:
            import_year_data(data_dir)
            time.sleep(1)  # Small pause between directories
        
        # Create station connections
        create_station_connections()
        
        # Verify data import
        verify_data_import()
        
        logger.info("Data import process completed successfully")
    except Exception as e:
        logger.error(f"Error during import process: {e}")
    finally:
        # Close database connection
        db.close()

if __name__ == "__main__":
    main()