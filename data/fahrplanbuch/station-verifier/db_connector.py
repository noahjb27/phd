# station-verifier/db_connector.py

from neo4j import GraphDatabase
import logging
import os
from pathlib import Path
import pandas as pd
import json

logger = logging.getLogger(__name__)

class StationVerifierDB:
    def __init__(self, uri=None, username=None, password=None):
        """
        Initialize connection to Neo4j database
        
        Args:
            uri: Database URI (defaults to env variable NEO4J_URI)
            username: Database username (defaults to env variable NEO4J_USERNAME)
            password: Database password (defaults to env variable NEO4J_PASSWORD)
        """
        # Get connection details from environment variables if not provided
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://100.82.176.18:7687")
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024")
        
        self.driver = None
        
    def connect(self):
        """Connect to the database if not already connected"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password),
                max_connection_lifetime=3600  # 1 hour
            )
    
    def close(self):
        """Close the database connection"""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
    
    def get_available_year_sides(self):
        """
        Get list of all available year-side combinations from the database
        
        Returns:
            List of dicts with year and side information
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (y:Year)<-[:IN_YEAR]-(s:Station)
                WITH y.year as year, s.east_west as side
                WHERE side IS NOT NULL
                RETURN DISTINCT year, side, toString(year) + '_' + side as id
                ORDER BY year, side
                """)
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error retrieving year-side combinations: {e}")
            return []
    
    def get_year_side_data(self, year_side):
        """
        Get all data for a specific year_side
        
        Args:
            year_side: String in format 'YYYY_side'
            
        Returns:
            Dict containing stops and lines data
        """
        self.connect()
        
        try:
            year, side = year_side.split('_')
            
            with self.driver.session() as session:
                # Get stations
                stops_result = session.run("""
                MATCH (s:Station)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE s.east_west = $side
                RETURN 
                    s.stop_id as stop_id,
                    s.name as stop_name,
                    s.type as type,
                    s.latitude as latitude,
                    s.longitude as longitude
                """, year=int(year), side=side)
                
                stops_df = pd.DataFrame([dict(record) for record in stops_result])
                
                # Get lines
                lines_result = session.run("""
                MATCH (l:Line)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE l.east_west = $side
                RETURN 
                    l.line_id as line_id,
                    l.name as line_name,
                    l.type as type
                """, year=int(year), side=side)
                
                lines_df = pd.DataFrame([dict(record) for record in lines_result])
                
                # Get line-station relationships
                line_stops_result = session.run("""
                MATCH (l:Line)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE l.east_west = $side
                MATCH (l)-[r:SERVES]->(s:Station)
                RETURN 
                    l.line_id as line_id,
                    s.stop_id as stop_id,
                    r.stop_order as stop_order,
                    l.name as line_name
                """, year=int(year), side=side)
                
                line_stops_df = pd.DataFrame([dict(record) for record in line_stops_result])
                
                # Join line names to stops dataframe for display
                stops_with_lines = stops_df.copy()
                if not line_stops_df.empty and not stops_df.empty:
                    stops_with_lines = pd.merge(
                        stops_df,
                        line_stops_df[['stop_id', 'line_name']],
                        on='stop_id',
                        how='left'
                    )
                
                # Format into the structure expected by the frontend
                return {
                    "stops": stops_with_lines,
                    "lines": lines_df,
                    "line_stops": line_stops_df
                }
                
        except Exception as e:
            logger.error(f"Error retrieving data for {year_side}: {e}")
            return {"stops": pd.DataFrame(), "lines": pd.DataFrame(), "line_stops": pd.DataFrame()}
    
    def update_station_location(self, stop_id, latitude, longitude):
        """
        Update a station's location in the database
        
        Args:
            stop_id: Station ID to update
            latitude: New latitude
            longitude: New longitude
            
        Returns:
            True if successful, False otherwise
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station {stop_id: $stop_id})
                SET s.latitude = $latitude, s.longitude = $longitude
                RETURN s.stop_id as stop_id
                """, stop_id=stop_id, latitude=latitude, longitude=longitude)
                
                return result.single() is not None
        except Exception as e:
            logger.error(f"Error updating station location: {e}")
            return False
    
    def update_station_name(self, stop_id, new_name):
        """
        Update a station's name in the database
        
        Args:
            stop_id: Station ID to update
            new_name: New station name
            
        Returns:
            True if successful, False otherwise
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station {stop_id: $stop_id})
                SET s.name = $new_name
                RETURN s.stop_id as stop_id
                """, stop_id=stop_id, new_name=new_name)
                
                return result.single() is not None
        except Exception as e:
            logger.error(f"Error updating station name: {e}")
            return False

    def delete_station(self, stop_id, year_side):
        """
        Delete a station and update line-station relationships for stop order continuity
        
        Args:
            stop_id: Station ID to delete
            year_side: Year-side combination in format 'YYYY_side'
            
        Returns:
            Dict with deletion status and updated relationships
        """
        self.connect()
        year, side = year_side.split('_')
        
        try:
            with self.driver.session() as session:
                # First get all line-station relationships for the station to be deleted
                lines_query = """
                MATCH (y:Year {year: $year})
                MATCH (s:Station {stop_id: $stop_id})-[:IN_YEAR]->(y)
                WHERE s.east_west = $side
                MATCH (l:Line)-[r:SERVES]->(s)
                RETURN l.line_id as line_id, r.stop_order as stop_order
                """
                
                lines_result = session.run(lines_query, year=int(year), side=side, stop_id=stop_id)
                affected_lines = [dict(record) for record in lines_result]
                
                updated_relationships = []
                
                # For each affected line, update stop order for stations after the deleted one
                for line_info in affected_lines:
                    line_id = line_info['line_id']
                    stop_order = line_info['stop_order']
                    
                    # Get stations before and after the deleted station
                    prev_station_query = """
                    MATCH (y:Year {year: $year})
                    MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                    WHERE l.east_west = $side
                    MATCH (l)-[r:SERVES]->(s:Station)
                    WHERE r.stop_order = $prev_order
                    RETURN s.stop_id as stop_id
                    """
                    
                    next_station_query = """
                    MATCH (y:Year {year: $year})
                    MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                    WHERE l.east_west = $side
                    MATCH (l)-[r:SERVES]->(s:Station)
                    WHERE r.stop_order = $next_order
                    RETURN s.stop_id as stop_id
                    """
                    
                    prev_result = session.run(prev_station_query, 
                                              year=int(year), 
                                              side=side,
                                              line_id=line_id,
                                              prev_order=stop_order - 1)
                    prev_record = prev_result.single()
                    
                    next_result = session.run(next_station_query, 
                                              year=int(year), 
                                              side=side,
                                              line_id=line_id,
                                              next_order=stop_order + 1)
                    next_record = next_result.single()
                    
                    # Update stop orders for all stations after the deleted one
                    update_orders_query = """
                    MATCH (y:Year {year: $year})
                    MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                    WHERE l.east_west = $side
                    MATCH (l)-[r:SERVES]->(s:Station)
                    WHERE r.stop_order > $stop_order
                    SET r.stop_order = r.stop_order - 1
                    RETURN count(r) as updated_count
                    """
                    
                    update_result = session.run(update_orders_query,
                                               year=int(year),
                                               side=side,
                                               line_id=line_id,
                                               stop_order=stop_order)
                    
                    updated_count = update_result.single()['updated_count'] if update_result.single() else 0
                    
                    updated_relationships.append({
                        'line_id': line_id,
                        'updated_stops': updated_count,
                        'prev_stop_id': prev_record['stop_id'] if prev_record else None,
                        'next_stop_id': next_record['stop_id'] if next_record else None
                    })
                
                # Now delete the station's relationships and the station itself
                delete_relationships_query = """
                MATCH (s:Station {stop_id: $stop_id})
                MATCH (s)-[r]-()
                DELETE r
                RETURN count(r) as deleted_rel_count
                """
                
                rel_result = session.run(delete_relationships_query, stop_id=stop_id)
                deleted_rel_count = rel_result.single()['deleted_rel_count'] if rel_result.single() else 0
                
                delete_station_query = """
                MATCH (s:Station {stop_id: $stop_id})
                DELETE s
                RETURN count(s) as deleted
                """
                
                station_result = session.run(delete_station_query, stop_id=stop_id)
                deleted_count = station_result.single()['deleted'] if station_result.single() else 0
                
                return {
                    "status": "success" if deleted_count > 0 else "error",
                    "deleted_station": stop_id,
                    "deleted_relationships": deleted_rel_count,
                    "updated_lines": updated_relationships
                }
                
        except Exception as e:
            logger.error(f"Error deleting station {stop_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def add_station(self, year_side, station_data, line_connections=None):
        """
        Add a new station to the database
        
        Args:
            year_side: Year-side combination in format 'YYYY_side'
            station_data: Dict with station properties (name, type, latitude, longitude)
            line_connections: Optional list of dicts with line_id and stop_order for connecting to lines
            
        Returns:
            Dict with new station ID and status
        """
        self.connect()
        year, side = year_side.split('_')
        
        try:
            with self.driver.session() as session:
                # Generate a new station ID based on year and side
                new_id_query = """
                MATCH (s:Station)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE s.east_west = $side
                RETURN max(toInteger(s.stop_id)) as max_id
                """
                
                id_result = session.run(new_id_query, year=int(year), side=side)
                record = id_result.single()
                
                max_id = record['max_id'] if record and record['max_id'] is not None else 0
                new_stop_id = f"{year}{side[0]}_{max_id + 1}"  # e.g. "1965w_12345"
                
                # Create the new station
                create_query = """
                MATCH (y:Year {year: $year})
                CREATE (s:Station {
                    stop_id: $stop_id,
                    name: $name,
                    type: $type,
                    latitude: $latitude,
                    longitude: $longitude,
                    east_west: $side
                })
                CREATE (s)-[:IN_YEAR]->(y)
                RETURN s.stop_id as new_id
                """
                
                station_result = session.run(create_query,
                                           year=int(year),
                                           stop_id=new_stop_id,
                                           name=station_data['name'],
                                           type=station_data['type'],
                                           latitude=station_data['latitude'],
                                           longitude=station_data['longitude'],
                                           side=side)
                
                new_id = station_result.single()['new_id'] if station_result.single() else None
                
                # Connect to lines if specified
                line_results = []
                if line_connections and new_id:
                    for connection in line_connections:
                        line_id = connection['line_id']
                        stop_order = connection['stop_order']
                        
                        # First, shift stop orders to make room
                        shift_query = """
                        MATCH (y:Year {year: $year})
                        MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                        WHERE l.east_west = $side
                        MATCH (l)-[r:SERVES]->(s:Station)
                        WHERE r.stop_order >= $stop_order
                        SET r.stop_order = r.stop_order + 1
                        RETURN count(r) as shifted
                        """
                        
                        shift_result = session.run(shift_query,
                                                 year=int(year),
                                                 side=side,
                                                 line_id=line_id,
                                                 stop_order=stop_order)
                        
                        shifted = shift_result.single()['shifted'] if shift_result.single() else 0
                        
                        # Now connect the new station
                        connect_query = """
                        MATCH (y:Year {year: $year})
                        MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                        WHERE l.east_west = $side
                        MATCH (s:Station {stop_id: $stop_id})
                        CREATE (l)-[r:SERVES {stop_order: $stop_order}]->(s)
                        RETURN l.line_id as line_id, r.stop_order as stop_order
                        """
                        
                        connect_result = session.run(connect_query,
                                                   year=int(year),
                                                   side=side,
                                                   line_id=line_id,
                                                   stop_id=new_id,
                                                   stop_order=stop_order)
                        
                        line_result = connect_result.single()
                        if line_result:
                            line_results.append({
                                "line_id": line_result['line_id'],
                                "stop_order": line_result['stop_order'],
                                "shifted_stops": shifted
                            })
                
                return {
                    "status": "success" if new_id else "error",
                    "new_station_id": new_id,
                    "line_connections": line_results
                }
                
        except Exception as e:
            logger.error(f"Error adding station for {year_side}: {e}")
            return {"status": "error", "message": str(e)}

    def export_corrected_data(self, corrections_data):
        """
        Export data with corrections applied
        
        Args:
            corrections_data: Dict of corrections by year_side and stop_id
            
        Returns:
            Dict with export status
        """
        results = {"status": "success", "updated_stations": 0}
        
        self.connect()
        
        try:
            with self.driver.session() as session:
                for year_side, stops in corrections_data.items():
                    for stop_id, correction in stops.items():
                        # Update station location in database
                        update_query = """
                        MATCH (s:Station {stop_id: $stop_id})
                        SET s.latitude = $latitude, s.longitude = $longitude
                        """
                        
                        params = {
                            "stop_id": stop_id, 
                            "latitude": correction["lat"], 
                            "longitude": correction["lng"]
                        }
                        
                        # Add name update if provided
                        if "name" in correction and correction["name"]:
                            update_query += ", s.name = $name"
                            params["name"] = correction["name"]
                        
                        session.run(update_query, params)
                        results["updated_stations"] += 1
                        
            return results
        except Exception as e:
            logger.error(f"Error exporting corrections: {e}")
            return {"status": "error", "message": str(e)}