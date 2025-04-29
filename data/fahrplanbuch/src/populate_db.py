"""
Script to populate Neo4j database with Berlin transport data.
Enhanced with selective import and update options.
"""

import pandas as pd
from pathlib import Path
import logging
import argparse
import sys
import os
import time
from db_connector import BerlinTransportDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_DB_URI = "bolt://100.82.176.18:7687"
DEFAULT_DB_USER = "neo4j"
DEFAULT_DB_PASSWORD = os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024")
DEFAULT_DATA_DIR = Path("../data/processed")

class BerlinTransportImporter:
    def __init__(self, uri=DEFAULT_DB_URI, username=DEFAULT_DB_USER, 
                 password=DEFAULT_DB_PASSWORD, data_dir=DEFAULT_DATA_DIR):
        """Initialize the importer with database connection and data source"""
        self.uri = uri
        self.username = username
        self.password = password
        self.data_dir = Path(data_dir)
        self.db = BerlinTransportDB(uri=uri, username=username, password=password)
        self.dry_run = False
        
    def setup_schema(self):
        """Create necessary constraints and indexes in Neo4j"""
        logger.info("Setting up database schema...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would create constraints and indexes")
            return True
        
        try:
            self.db.connect()
            with self.db.driver.session() as session:
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
    
    def get_available_data(self):
        """Return a list of available year_side data directories"""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        data_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        year_sides = []
        
        for data_dir in data_dirs:
            try:
                year_side = data_dir.name
                year, side = year_side.split('_')
                year_sides.append((int(year), side, data_dir))
            except (ValueError, IndexError):
                logger.warning(f"Skipping invalid directory name: {data_dir.name}")
        
        # Sort by year and side
        year_sides.sort(key=lambda x: (x[0], x[1]))
        
        return year_sides
    
    def import_data(self, years=None, sides=None, update_existing=False, dry_run=False):
        """
        Import data for specified years and sides
        
        Args:
            years: List of years to import, or None for all
            sides: List of sides to import ('east'/'west'), or None for all
            update_existing: Whether to update existing data or only add new
            dry_run: If True, only simulate the import without making changes
        """
        self.dry_run = dry_run
        self.db.connect()
        
        # Set up schema
        if not self.setup_schema():
            logger.error("Failed to set up schema, aborting import")
            return False
        
        # Get available data
        available_data = self.get_available_data()
        if not available_data:
            logger.error("No data found to import")
            return False
        
        # Filter by year and side if specified
        if years:
            available_data = [d for d in available_data if d[0] in years]
        if sides:
            available_data = [d for d in available_data if d[1] in sides]
        
        if not available_data:
            logger.error("No matching data found with specified filters")
            return False
        
        # Print what will be imported
        logger.info("Will import data for the following year/sides:")
        for year, side, _ in available_data:
            logger.info(f"  {year}_{side}")
        
        success = True
        for year, side, data_dir in available_data:
            logger.info(f"Processing data for {year}_{side}")
            
            if not self.import_year_data(data_dir, update_existing):
                logger.error(f"Failed to import data for {year}_{side}")
                success = False
            
            time.sleep(1)  # Small pause between directories
        
        # Create connections between stations
        if success and not self.dry_run:
            self.create_station_connections()
            self.verify_data_import()
        
        logger.info("Data import process completed")
        return success
    
    def import_year_data(self, year_side_dir, update_existing=False):
        """Import data for a specific year and side of Berlin"""
        try:
            # Extract year and side from directory name
            year_side = year_side_dir.name
            year, side = year_side.split('_')
            year = int(year)
            
            logger.info(f"Importing data for {year}_{side}...")
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would import {year}_{side}")
                # Preview files
                for file_type in ["stops.csv", "lines.csv", "line_stops.csv"]:
                    file_path = year_side_dir / file_type
                    if file_path.exists():
                        df = pd.read_csv(file_path)
                        logger.info(f"[DRY RUN] {file_path}: {len(df)} rows")
                return True
            
            # Create Year node
            with self.db.driver.session() as session:
                session.run("MERGE (y:Year {year: $year})", year=year)
            
            # Import stops
            self.import_stations(year_side_dir / "stops.csv", year, side, update_existing)
            
            # Import lines
            self.import_lines(year_side_dir / "lines.csv", year, update_existing)
            
            # Import line-stop relationships
            self.import_line_stops(year_side_dir / "line_stops.csv", update_existing)
            
            logger.info(f"Data import completed for {year}_{side}")
            return True
        except Exception as e:
            logger.error(f"Error importing data for {year_side_dir.name}: {e}")
            return False
    
    def import_stations(self, file_path, year, side, update_existing=False):
        """Import stations from CSV file"""
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return False
        
        try:
            # Read stations CSV
            stops_df = pd.read_csv(file_path)
            logger.info(f"Importing {len(stops_df)} stations from {file_path}")
            
            # Get existing stations if needed
            if not update_existing:
                with self.db.driver.session() as session:
                    result = session.run("""
                    MATCH (s:Station)-[:IN_YEAR]->(:Year {year: $year})
                    RETURN s.stop_id as stop_id
                    """, year=year)
                    
                    existing_ids = {record["stop_id"] for record in result}
                    
                    # Filter out existing stations
                    before_count = len(stops_df)
                    stops_df = stops_df[~stops_df['stop_id'].astype(str).isin(existing_ids)]
                    after_count = len(stops_df)
                    
                    if before_count > after_count:
                        logger.info(f"Skipping {before_count - after_count} existing stations")
            
            if len(stops_df) == 0:
                logger.info("No new stations to import")
                return True
            
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
                    for field in ['district', 'neighbourhood', 'postal_code', 'identifier']:
                        if field in row and pd.notna(row[field]):
                            station_param[field] = row[field]
                    
                    stations_params.append(station_param)
                
                # Execute batch import
                with self.db.driver.session() as session:
                    # Prepare the query based on update_existing flag
                    if update_existing:
                        # Update all properties regardless
                        query = """
                        UNWIND $stations AS station
                        MATCH (y:Year {year: station.year})
                        
                        // Create or update Station
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
                        """
                    else:
                        # Only set properties on creation (ON CREATE)
                        query = """
                        UNWIND $stations AS station
                        MATCH (y:Year {year: station.year})
                        
                        // Create Station but don't update if exists
                        MERGE (s:Station {stop_id: station.stop_id})
                        ON CREATE SET 
                            s.name = station.name,
                            s.type = station.type,
                            s.east_west = station.east_west
                        
                        // Set coordinates if available and only on creation
                        FOREACH (ignoreMe IN CASE WHEN station.latitude IS NOT NULL AND station.longitude IS NOT NULL 
                                THEN [1] ELSE [] END | 
                            SET s.latitude = CASE WHEN s.latitude IS NULL THEN station.latitude ELSE s.latitude END,
                                s.longitude = CASE WHEN s.longitude IS NULL THEN station.longitude ELSE s.longitude END
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
                        """
                    
                    result = session.run(query, stations=stations_params)
                    count = result.single()["count"]
                    logger.info(f"Imported batch {i+1}/{total_batches} with {count} stations")
            
            return True
        except Exception as e:
            logger.error(f"Error importing stations: {e}")
            return False
    
    def import_lines(self, file_path, year, update_existing=False):
        """Import lines from CSV file"""
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return False
        
        try:
            # Read lines CSV
            lines_df = pd.read_csv(file_path)
            logger.info(f"Importing {len(lines_df)} lines from {file_path}")
            
            # Get existing lines if needed
            if not update_existing:
                with self.db.driver.session() as session:
                    result = session.run("""
                    MATCH (l:Line)-[:IN_YEAR]->(:Year {year: $year})
                    RETURN l.line_id as line_id
                    """, year=year)
                    
                    existing_ids = {record["line_id"] for record in result}
                    
                    # Filter out existing lines
                    before_count = len(lines_df)
                    lines_df = lines_df[~lines_df['line_id'].astype(str).isin(existing_ids)]
                    after_count = len(lines_df)
                    
                    if before_count > after_count:
                        logger.info(f"Skipping {before_count - after_count} existing lines")
            
            if len(lines_df) == 0:
                logger.info("No new lines to import")
                return True
            
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
                        "east_west": row.get('east_west', 'unknown'),  # Default if missing
                        "year": year
                    }
                    
                    # Add optional fields
                    optional_fields = {
                        'frequency (7:30)': 'frequency',
                        'capacity': 'capacity',
                        'length (time)': 'length_time',
                        'length (km)': 'length_km',
                        'profile': 'profile'
                    }
                    
                    for source, target in optional_fields.items():
                        if source in row and pd.notna(row[source]):
                            line_param[target] = row[source]
                    
                    lines_params.append(line_param)
                
                # Execute batch import
                with self.db.driver.session() as session:
                    # Prepare query based on update_existing flag
                    if update_existing:
                        query = """
                        UNWIND $lines AS line
                        MATCH (y:Year {year: line.year})
                        
                        // Create or update Line
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
                        """
                    else:
                        query = """
                        UNWIND $lines AS line
                        MATCH (y:Year {year: line.year})
                        
                        // Create Line but don't update if exists
                        MERGE (l:Line {line_id: line.line_id})
                        ON CREATE SET 
                            l.name = line.name,
                            l.type = line.type,
                            l.east_west = line.east_west
                        
                        // Set optional properties only on creation
                        FOREACH (ignoreMe IN CASE WHEN line.frequency IS NOT NULL THEN [1] ELSE [] END | 
                            SET l.frequency = CASE WHEN l.frequency IS NULL THEN line.frequency ELSE l.frequency END
                        )
                        FOREACH (ignoreMe IN CASE WHEN line.capacity IS NOT NULL THEN [1] ELSE [] END | 
                            SET l.capacity = CASE WHEN l.capacity IS NULL THEN line.capacity ELSE l.capacity END
                        )
                        FOREACH (ignoreMe IN CASE WHEN line.length_time IS NOT NULL THEN [1] ELSE [] END | 
                            SET l.length_time = CASE WHEN l.length_time IS NULL THEN line.length_time ELSE l.length_time END
                        )
                        FOREACH (ignoreMe IN CASE WHEN line.length_km IS NOT NULL THEN [1] ELSE [] END | 
                            SET l.length_km = CASE WHEN l.length_km IS NULL THEN line.length_km ELSE l.length_km END
                        )
                        FOREACH (ignoreMe IN CASE WHEN line.profile IS NOT NULL THEN [1] ELSE [] END | 
                            SET l.profile = CASE WHEN l.profile IS NULL THEN line.profile ELSE l.profile END
                        )
                        
                        // Connect to Year
                        MERGE (l)-[:IN_YEAR]->(y)
                        
                        RETURN count(l) as count
                        """
                    
                    result = session.run(query, lines=lines_params)
                    count = result.single()["count"]
                    logger.info(f"Imported batch {i+1}/{total_batches} with {count} lines")
            
            return True
        except Exception as e:
            logger.error(f"Error importing lines: {e}")
            return False
    
    def import_line_stops(self, file_path, update_existing=False):
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
                with self.db.driver.session() as session:
                    # Relationships are always merged, but stop_order might be updated
                    # if update_existing is True
                    if update_existing:
                        query = """
                        UNWIND $relations AS rel
                        MATCH (l:Line {line_id: rel.line_id})
                        MATCH (s:Station {stop_id: rel.stop_id})
                        MERGE (l)-[r:SERVES]->(s)
                        SET r.stop_order = rel.stop_order
                        RETURN count(r) as count
                        """
                    else:
                        query = """
                        UNWIND $relations AS rel
                        MATCH (l:Line {line_id: rel.line_id})
                        MATCH (s:Station {stop_id: rel.stop_id})
                        MERGE (l)-[r:SERVES]->(s)
                        ON CREATE SET r.stop_order = rel.stop_order
                        RETURN count(r) as count
                        """
                    
                    result = session.run(query, relations=relations_params)
                    count = result.single()["count"]
                    logger.info(f"Imported batch {i+1}/{total_batches} with {count} relationships")
            
            return True
        except Exception as e:
            logger.error(f"Error importing line-stop relationships: {e}")
            return False
    
    def create_station_connections(self):
        """Create CONNECTS_TO relationships between stations based on line sequence"""
        logger.info("Creating station connections...")
        
        try:
            with self.db.driver.session() as session:
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
    
    def verify_data_import(self):
        """Verify data was imported correctly"""
        logger.info("Verifying data import...")
        
        try:
            with self.db.driver.session() as session:
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
    
    def list_available_years_sides(self):
        """List available years and sides for import"""
        year_sides = self.get_available_data()
        
        if not year_sides:
            logger.info("No data available for import")
            return
        
        years = sorted(set(year for year, _, _ in year_sides))
        sides = sorted(set(side for _, side, _ in year_sides))
        
        logger.info("Available years: " + ", ".join(str(y) for y in years))
        logger.info("Available sides: " + ", ".join(sides))
        logger.info("Available year_sides:")
        
        for year, side, _ in year_sides:
            logger.info(f"  {year}_{side}")

def main():
    """Main function to run the import process"""
    parser = argparse.ArgumentParser(description="Import Berlin Transport data to Neo4j")
    
    # Database connection options
    parser.add_argument("--uri", default=DEFAULT_DB_URI, help="Neo4j database URI")
    parser.add_argument("--username", default=DEFAULT_DB_USER, help="Neo4j username")
    parser.add_argument("--password", default=DEFAULT_DB_PASSWORD, 
                       help="Neo4j password (can also be set via NEO4J_PASSWORD env variable)")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), 
                       help="Directory containing processed data files")
    
    # Import filtering options
    parser.add_argument("--years", type=int, nargs="+", help="Specific years to import")
    parser.add_argument("--sides", choices=["east", "west"], nargs="+", 
                       help="Specific sides to import (east/west)")
    
    # Import behavior options
    parser.add_argument("--update-existing", action="store_true", 
                       help="Update existing data instead of only adding new data")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simulate import without making changes")
    parser.add_argument("--list", action="store_true",
                       help="List available years and sides for import")
    parser.add_argument("--reset-schema", action="store_true",
                       help="Reset database schema before import (creates constraints and indexes)")
    
    # Actions
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--import", action="store_true", dest="do_import",
                             help="Import data (default action)")
    action_group.add_argument("--verify", action="store_true", 
                             help="Only verify existing data, no import")
    action_group.add_argument("--connections", action="store_true",
                             help="Only create station connections, no import")
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = BerlinTransportImporter(
        uri=args.uri,
        username=args.username,
        password=args.password,
        data_dir=args.data_dir
    )
    
    # Connect to database
    importer.db.connect()
    
    try:
        # List available data if requested
        if args.list:
            importer.list_available_years_sides()
            return 0
        
        # Verify existing data if requested
        if args.verify:
            success = importer.verify_data_import()
            return 0 if success else 1
        
        # Create connections if requested
        if args.connections:
            success = importer.create_station_connections()
            return 0 if success else 1
        
        # Default action is import
        success = importer.import_data(
            years=args.years,
            sides=args.sides,
            update_existing=args.update_existing,
            dry_run=args.dry_run
        )
        
        return 0 if success else 1
    finally:
        # Close database connection
        importer.db.close()

if __name__ == "__main__":
    sys.exit(main())