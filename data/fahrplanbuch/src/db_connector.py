# db_connector.py - Can be used by both notebook and station-verifier

from neo4j import GraphDatabase
import logging
from typing import Optional, Dict, List, Tuple

class BerlinTransportDB:
    def __init__(self, uri: str, username: str, password: str, max_retries: int = 3):
        self.uri = uri
        self.username = username
        self.password = password
        self.max_retries = max_retries
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
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
    
    def find_matching_stations(self, station_name: str, station_type: str, 
                              current_year: int) -> List[Dict]:
        """
        Find stations matching name/type from previous years
        
        Args:
            station_name: Name of the station
            station_type: Type of station (u-bahn, s-bahn, etc.)
            current_year: Current year being processed
            
        Returns:
            List of matching stations from the database
        """
        self.connect()
        
        # Query matching stations from the database
        query = """
        MATCH (s:Station)
        WHERE s.name = $name AND s.type = $type
        WITH s
        MATCH (s)-[:IN_YEAR]->(y:Year)
        WHERE toInteger(y.year) < $year
        RETURN s.stop_id as stop_id, s.name as name, s.type as type,
               s.latitude as latitude, s.longitude as longitude, 
               y.year as year
        ORDER BY y.year DESC
        LIMIT 5
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    query, 
                    name=station_name,
                    type=station_type,
                    year=current_year
                )
                return result.data()
        except Exception as e:
            self.logger.error(f"Error finding matching stations: {e}")
            return []
    
    def save_station_location(self, stop_id: str, latitude: float, 
                             longitude: float) -> bool:
        """
        Update station location in the database
        
        Args:
            stop_id: Station ID
            latitude: New latitude value
            longitude: New longitude value
            
        Returns:
            True if successful, False otherwise
        """
        self.connect()
        
        query = """
        MATCH (s:Station {stop_id: $stop_id})
        SET s.latitude = $latitude, s.longitude = $longitude
        RETURN s
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    stop_id=stop_id,
                    latitude=latitude,
                    longitude=longitude
                )
                return result.single() is not None
        except Exception as e:
            self.logger.error(f"Error updating station location: {e}")
            return False
    
    def get_stations_for_year_side(self, year: int, side: str) -> List[Dict]:
        """
        Get all stations for a specific year and side
        
        Args:
            year: Year to get stations for
            side: Side of Berlin (east/west)
            
        Returns:
            List of stations with their attributes
        """
        self.connect()
        
        query = """
        MATCH (s:Station)-[:IN_YEAR]->(:Year {year: $year})
        WHERE s.east_west = $side
        RETURN s.stop_id as stop_id, s.name as name, s.type as type,
               s.latitude as latitude, s.longitude as longitude,
               s.east_west as east_west
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, year=year, side=side)
                return result.data()
        except Exception as e:
            self.logger.error(f"Error getting stations for year {year}, side {side}: {e}")
            return []
    
    def add_station(self, station_data: Dict) -> str:
        """
        Add a new station to the database
        
        Args:
            station_data: Dictionary with station data
            
        Returns:
            Station ID if successful, None otherwise
        """
        self.connect()
        
        query = """
        MATCH (y:Year {year: $year})
        MERGE (s:Station {stop_id: $stop_id})
        ON CREATE SET 
            s.name = $name,
            s.type = $type,
            s.latitude = $latitude,
            s.longitude = $longitude,
            s.east_west = $east_west
        ON MATCH SET
            s.name = CASE WHEN $name IS NOT NULL THEN $name ELSE s.name END,
            s.type = CASE WHEN $type IS NOT NULL THEN $type ELSE s.type END,
            s.latitude = CASE WHEN $latitude IS NOT NULL THEN $latitude ELSE s.latitude END,
            s.longitude = CASE WHEN $longitude IS NOT NULL THEN $longitude ELSE s.longitude END,
            s.east_west = CASE WHEN $east_west IS NOT NULL THEN $east_west ELSE s.east_west END
        MERGE (s)-[:IN_YEAR]->(y)
        RETURN s.stop_id as stop_id
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, **station_data)
                record = result.single()
                return record["stop_id"] if record else None
        except Exception as e:
            self.logger.error(f"Error adding station: {e}")
            return None