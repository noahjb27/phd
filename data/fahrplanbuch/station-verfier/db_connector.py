# station-verifier/db_connector.py

from neo4j import GraphDatabase
import logging
import os
from pathlib import Path
import pandas as pd
import json

logger = logging.getLogger(__name__)

class StationVerifierDB:
    def __init__(self, uri="bolt://100.82.176.18:7687", username="neo4j", password="BerlinTransport2024"):
        """
        Initialize connection to Neo4j database
        
        Args:
            uri: Database URI
            username: Database username
            password: Database password (defaults to env variable NEO4J_PASSWORD)
        """
        self.uri = uri
        self.username = username
        
        # Get password from environment variable if not provided
        self.password = password or os.environ.get("NEO4J_PASSWORD")
        
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
    
    # Modified get_available_year_sides method with correct syntax
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
                        # Update station in database
                        session.run("""
                        MATCH (s:Station {stop_id: $stop_id})
                        SET s.latitude = $latitude, s.longitude = $longitude
                        """, 
                        stop_id=stop_id, 
                        latitude=correction["lat"], 
                        longitude=correction["lng"])
                        
                        results["updated_stations"] += 1
                        
            return results
        except Exception as e:
            logger.error(f"Error exporting corrections: {e}")
            return {"status": "error", "message": str(e)}