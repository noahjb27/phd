# station-verifier/db_connector.py

import datetime
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
        self.additions_file = Path("corrections/station_additions.json")
        self.additions_file.parent.mkdir(exist_ok=True)
        
        # Initialize additions file if it doesn't exist
        if not self.additions_file.exists():
            with open(self.additions_file, 'w') as f:
                json.dump({}, f)

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
    
    def add_station_with_line_integration(self, year_side, station_data, line_connections=None):
        """
        Add a new station with proper line integration and save to additions file
        
        Args:
            year_side: Year-side combination in format 'YYYY_side'
            station_data: Dict with station properties
            line_connections: List of dicts with line_id and stop_order
            
        Returns:
            Dict with status and details
        """
        self.connect()
        year, side = year_side.split('_')
        
        try:
            with self.driver.session() as session:
                # Generate new station ID
                new_id_query = """
                MATCH (s:Station)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE s.east_west = $side
                WITH s.stop_id as stop_id
                ORDER BY toInteger(substring(stop_id, 4)) DESC
                LIMIT 1
                RETURN stop_id
                """
                
                id_result = session.run(new_id_query, year=int(year), side=side)
                record = id_result.single()
                
                if record:
                    last_id = record['stop_id']
                    number_part = int(last_id.split('_')[0][4:])
                    new_number = number_part + 1
                else:
                    new_number = 1
                
                new_stop_id = f"{year}{new_number:03d}_{side}"
                
                # Validate line connections if provided
                validated_connections = []
                if line_connections:
                    for connection in line_connections:
                        line_id = connection['line_id']
                        stop_order = connection['stop_order']
                        
                        # Check if the line exists
                        line_check = session.run("""
                        MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y:Year {year: $year})
                        WHERE l.east_west = $side
                        RETURN l.line_id as line_id, l.name as line_name, l.type as line_type
                        """, line_id=line_id, year=int(year), side=side)
                        
                        line_record = line_check.single()
                        if not line_record:
                            return {
                                "status": "error",
                                "message": f"Line {line_id} not found in {year_side}"
                            }
                        
                        # Check if stop_order position is valid
                        order_check = session.run("""
                        MATCH (l:Line {line_id: $line_id})-[r:SERVES]->(:Station)
                        RETURN max(r.stop_order) as max_order, count(r) as total_stops
                        """, line_id=line_id)
                        
                        order_record = order_check.single()
                        max_order = order_record['max_order'] if order_record['max_order'] else 0
                        
                        # Validate stop order
                        if stop_order < 1 or stop_order > max_order + 1:
                            return {
                                "status": "error",
                                "message": f"Invalid stop order {stop_order}. Must be between 1 and {max_order + 1}"
                            }
                        
                        validated_connections.append({
                            "line_id": line_id,
                            "line_name": line_record['line_name'],
                            "line_type": line_record['line_type'],
                            "stop_order": stop_order
                        })
                
                # Create the station
                create_query = """
                MATCH (y:Year {year: $year})
                CREATE (s:Station {
                    stop_id: $stop_id,
                    name: $name,
                    type: $type,
                    latitude: $latitude,
                    longitude: $longitude,
                    east_west: $side,
                    source: $source
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
                                        side=side,
                                        source=station_data.get('source', 'User added'))
                
                new_id = station_result.single()['new_id'] if station_result.single() else None
                
                if not new_id:
                    return {"status": "error", "message": "Failed to create station"}
                
                # Handle line connections with proper CONNECTS_TO relationships
                line_results = []
                for connection in validated_connections:
                    line_id = connection['line_id']
                    stop_order = connection['stop_order']
                    
                    # Get adjacent stations for CONNECTS_TO relationships
                    adjacent_query = """
                    MATCH (l:Line {line_id: $line_id})-[r:SERVES]->(s:Station)
                    WHERE r.stop_order IN [$prev_order, $next_order]
                    RETURN s.stop_id as stop_id, r.stop_order as stop_order,
                           s.latitude as lat, s.longitude as lng
                    ORDER BY r.stop_order
                    """
                    
                    adjacent_result = session.run(adjacent_query,
                                                line_id=line_id,
                                                prev_order=stop_order - 1,
                                                next_order=stop_order)
                    
                    adjacent_stations = [dict(record) for record in adjacent_result]
                    
                    prev_station = None
                    next_station = None
                    
                    for station in adjacent_stations:
                        if station['stop_order'] == stop_order - 1:
                            prev_station = station
                        elif station['stop_order'] == stop_order:
                            next_station = station
                    
                    # Update stop orders to make room
                    shift_query = """
                    MATCH (l:Line {line_id: $line_id})-[r:SERVES]->(s:Station)
                    WHERE r.stop_order >= $stop_order
                    SET r.stop_order = r.stop_order + 1
                    RETURN count(r) as shifted
                    """
                    
                    shift_result = session.run(shift_query,
                                             line_id=line_id,
                                             stop_order=stop_order)
                    
                    shifted = shift_result.single()['shifted'] if shift_result.single() else 0
                    
                    # Connect new station to line
                    connect_query = """
                    MATCH (l:Line {line_id: $line_id})
                    MATCH (s:Station {stop_id: $stop_id})
                    CREATE (l)-[r:SERVES {stop_order: $stop_order}]->(s)
                    RETURN l.line_id as line_id, r.stop_order as stop_order
                    """
                    
                    connect_result = session.run(connect_query,
                                               line_id=line_id,
                                               stop_id=new_id,
                                               stop_order=stop_order)
                    
                    # Handle CONNECTS_TO relationships
                    connects_to_updates = []
                    
                    # If there was a direct connection between prev and next, split it
                    if prev_station and next_station:
                        # Get existing connection properties
                        existing_connection_query = """
                        MATCH (prev:Station {stop_id: $prev_id})-[r:CONNECTS_TO]->(next:Station {stop_id: $next_id})
                        RETURN properties(r) as props
                        """
                        
                        existing_result = session.run(existing_connection_query,
                                                    prev_id=prev_station['stop_id'],
                                                    next_id=next_station['stop_id'])
                        
                        existing_record = existing_result.single()
                        existing_props = existing_record['props'] if existing_record else {}
                        
                        # Delete existing connection
                        session.run("""
                        MATCH (prev:Station {stop_id: $prev_id})-[r:CONNECTS_TO]->(next:Station {stop_id: $next_id})
                        DELETE r
                        """, prev_id=prev_station['stop_id'], next_id=next_station['stop_id'])
                        
                        # Create new connections through the new station
                        if prev_station:
                            # Calculate distance
                            distance_prev_new = self._calculate_distance(
                                prev_station['lat'], prev_station['lng'],
                                station_data['latitude'], station_data['longitude']
                            )
                            
                            # Create prev -> new connection
                            session.run("""
                            MATCH (prev:Station {stop_id: $prev_id})
                            MATCH (new:Station {stop_id: $new_id})
                            CREATE (prev)-[r:CONNECTS_TO]->(new)
                            SET r = $props
                            SET r.distance_meters = $distance
                            """, prev_id=prev_station['stop_id'], new_id=new_id,
                                props=existing_props, distance=distance_prev_new)
                        
                        if next_station:
                            # Calculate distance
                            distance_new_next = self._calculate_distance(
                                station_data['latitude'], station_data['longitude'],
                                next_station['lat'], next_station['lng']
                            )
                            
                            # Create new -> next connection
                            session.run("""
                            MATCH (new:Station {stop_id: $new_id})
                            MATCH (next:Station {stop_id: $next_id})
                            CREATE (new)-[r:CONNECTS_TO]->(next)
                            SET r = $props
                            SET r.distance_meters = $distance
                            """, new_id=new_id, next_id=next_station['stop_id'],
                                props=existing_props, distance=distance_new_next)
                        
                        connects_to_updates.append({
                            'prev_station': prev_station['stop_id'] if prev_station else None,
                            'new_station': new_id,
                            'next_station': next_station['stop_id'] if next_station else None
                        })
                    
                    line_results.append({
                        "line_id": line_id,
                        "line_name": connection['line_name'],
                        "stop_order": stop_order,
                        "shifted_stops": shifted,
                        "connects_to_updates": connects_to_updates
                    })
                
                # Save to additions file
                addition_record = {
                    "station_id": new_id,
                    "year_side": year_side,
                    "station_data": station_data,
                    "line_connections": validated_connections,
                    "created_timestamp": datetime.now().isoformat(),
                    "status": "active"
                }
                
                self.save_station_addition(addition_record)
                
                return {
                    "status": "success",
                    "new_station_id": new_id,
                    "line_connections": line_results,
                    "addition_saved": True
                }
                
        except Exception as e:
            logger.error(f"Error adding station for {year_side}: {e}")
            return {"status": "error", "message": str(e)}
    def save_station_addition(self, addition_record):
        """Save a station addition to the additions file"""
        try:
            # Load existing additions
            with open(self.additions_file, 'r') as f:
                additions = json.load(f)
            
            year_side = addition_record['year_side']
            station_id = addition_record['station_id']
            
            if year_side not in additions:
                additions[year_side] = {}
            
            additions[year_side][station_id] = addition_record
            
            # Save back to file
            with open(self.additions_file, 'w') as f:
                json.dump(additions, f, indent=2)
                
            logger.info(f"Saved station addition {station_id} to additions file")
            return True
            
        except Exception as e:
            logger.error(f"Error saving station addition: {e}")
            return False
    
    def get_station_additions(self):
        """Get all station additions from the additions file"""
        try:
            with open(self.additions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading station additions: {e}")
            return {}
            
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
                # Get stations - NOW INCLUDING SOURCE
                stops_result = session.run("""
                MATCH (s:Station)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE s.east_west = $side
                RETURN 
                    s.stop_id as stop_id,
                    s.name as stop_name,
                    s.type as type,
                    s.latitude as latitude,
                    s.longitude as longitude,
                    s.source as source
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
    
    def get_station_coordinates(self, stop_id):
        """
        Get the coordinates for a station
        
        Args:
            stop_id: Station ID to query
            
        Returns:
            Dict with latitude and longitude if found, None otherwise
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station {stop_id: $stop_id})
                RETURN s.latitude as latitude, s.longitude as longitude
                """, stop_id=stop_id)
                
                record = result.single()
                if record and record["latitude"] is not None and record["longitude"] is not None:
                    return {
                        "latitude": record["latitude"],
                        "longitude": record["longitude"]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting station coordinates: {e}")
            return None
    
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
        Delete a station and properly update both SERVES and CONNECTS_TO relationships
        
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
                # Step 1: Get all line-station relationships for the station to be deleted
                lines_query = """
                MATCH (y:Year {year: $year})
                MATCH (s:Station {stop_id: $stop_id})
                WHERE s.east_west = $side AND (s)-[:IN_YEAR]->(y)
                MATCH (l:Line)-[r:SERVES]->(s)
                RETURN l.line_id as line_id, r.stop_order as stop_order
                """
                
                lines_result = session.run(lines_query, year=int(year), side=side, stop_id=stop_id)
                affected_lines = [dict(record) for record in lines_result]
                
                updated_relationships = []
                connects_to_updates = []
                
                # Step 2: For each affected line, handle both SERVES and CONNECTS_TO relationships
                for line_info in affected_lines:
                    line_id = line_info['line_id']
                    stop_order = line_info['stop_order']
                    
                    # Get adjacent stations (previous and next) on this line
                    adjacent_query = """
                    MATCH (y:Year {year: $year})
                    MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                    WHERE l.east_west = $side
                    MATCH (l)-[r:SERVES]->(s:Station)
                    WHERE r.stop_order IN [$prev_order, $next_order]
                    RETURN s.stop_id as stop_id, r.stop_order as stop_order
                    ORDER BY r.stop_order
                    """
                    
                    adjacent_result = session.run(adjacent_query,
                                                year=int(year),
                                                side=side,
                                                line_id=line_id,
                                                prev_order=stop_order - 1,
                                                next_order=stop_order + 1)
                    
                    adjacent_stations = [dict(record) for record in adjacent_result]
                    
                    prev_station = None
                    next_station = None
                    
                    for station in adjacent_stations:
                        if station['stop_order'] == stop_order - 1:
                            prev_station = station['stop_id']
                        elif station['stop_order'] == stop_order + 1:
                            next_station = station['stop_id']
                    
                    # Step 3: Handle CONNECTS_TO relationships
                    if prev_station and next_station:
                        # Get properties from the existing connections to calculate new connection
                        connection_props_query = """
                        MATCH (deleted:Station {stop_id: $deleted_id})
                        MATCH (prev:Station {stop_id: $prev_id})
                        MATCH (next:Station {stop_id: $next_id})
                        OPTIONAL MATCH (prev)-[r1:CONNECTS_TO]->(deleted)
                        OPTIONAL MATCH (deleted)-[r2:CONNECTS_TO]->(next)
                        RETURN r1, r2, 
                            prev.latitude as prev_lat, prev.longitude as prev_lng,
                            next.latitude as next_lat, next.longitude as next_lng
                        """
                        
                        props_result = session.run(connection_props_query,
                                                deleted_id=stop_id,
                                                prev_id=prev_station,
                                                next_id=next_station)
                        
                        props_record = props_result.single()
                        
                        if props_record:
                            r1 = props_record["r1"]
                            r2 = props_record["r2"]
                            
                            # Calculate new direct connection properties
                            if r1 and r2:
                                # Combine properties from both segments
                                new_distance = self._calculate_distance(
                                    props_record["prev_lat"], props_record["prev_lng"],
                                    props_record["next_lat"], props_record["next_lng"]
                                )
                                
                                # Merge line information
                                combined_line_ids = list(set((r1.get("line_ids", []) + r2.get("line_ids", []))))
                                combined_line_names = list(set((r1.get("line_names", []) + r2.get("line_names", []))))
                                combined_capacities = list(set((r1.get("capacities", []) + r2.get("capacities", []))))
                                combined_frequencies = list(set((r1.get("frequencies", []) + r2.get("frequencies", []))))
                                
                                # Create new CONNECTS_TO relationship
                                create_connection_query = """
                                MATCH (prev:Station {stop_id: $prev_id})
                                MATCH (next:Station {stop_id: $next_id})
                                MERGE (prev)-[r:CONNECTS_TO]->(next)
                                SET r.line_ids = $line_ids,
                                    r.line_names = $line_names,
                                    r.transport_type = $transport_type,
                                    r.distance_meters = $distance_meters,
                                    r.capacities = $capacities,
                                    r.frequencies = $frequencies,
                                    r.hourly_capacity = $hourly_capacity,
                                    r.hourly_services = $hourly_services
                                """
                                
                                # Calculate hourly values
                                total_hourly_capacity = sum(cap * (60 / freq) for cap, freq in zip(combined_capacities, combined_frequencies) if freq > 0)
                                total_hourly_services = sum(60 / freq for freq in combined_frequencies if freq > 0)
                                
                                session.run(create_connection_query,
                                        prev_id=prev_station,
                                        next_id=next_station,
                                        line_ids=combined_line_ids,
                                        line_names=combined_line_names,
                                        transport_type=r1.get("transport_type", "unknown"),
                                        distance_meters=new_distance,
                                        capacities=combined_capacities,
                                        frequencies=combined_frequencies,
                                        hourly_capacity=total_hourly_capacity,
                                        hourly_services=total_hourly_services)
                                
                                connects_to_updates.append({
                                    'line_id': line_id,
                                    'prev_station': prev_station,
                                    'next_station': next_station,
                                    'new_distance': new_distance
                                })
                    
                    # Step 4: Update stop orders for stations after the deleted one
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
                        'prev_stop_id': prev_station,
                        'next_stop_id': next_station
                    })
                
                # Step 5: Delete all relationships involving the station
                delete_relationships_query = """
                MATCH (s:Station {stop_id: $stop_id})
                OPTIONAL MATCH (s)-[r]-()
                DELETE r
                RETURN count(r) as deleted_rel_count
                """

                rel_result = session.run(delete_relationships_query, stop_id=stop_id)
                deleted_rel_count = rel_result.single()['deleted_rel_count'] if rel_result.single() else 0

                # Step 6: Delete the station itself
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
                    "updated_lines": updated_relationships,
                    "connects_to_updates": connects_to_updates
                }
                
        except Exception as e:
            logger.error(f"Error deleting station {stop_id}: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        if None in [lat1, lon1, lat2, lon2]:
            return 1000
        
        from math import radians, cos, sin, sqrt, atan2
        
        R = 6371000
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return int(R * c)
    
    def validate_station_distances(self, year_side, line_id=None):
        """
        Validate distances between adjacent stations on lines
        
        Args:
            year_side: Year-side combination to check
            line_id: Optional specific line to check, otherwise checks all lines
            
        Returns:
            List of validation issues found
        """
        self.connect()
        year, side = year_side.split('_')
        
        # Distance thresholds (in meters)
        MIN_DISTANCE = 200   # Stations closer than this might be duplicates
        MAX_DISTANCE = 3000  # Stations farther than this might have missing stations
        OPTIMAL_MIN = 400    # Preferred minimum distance
        OPTIMAL_MAX = 1500   # Preferred maximum distance
        
        issues = []
        
        try:
            with self.driver.session() as session:
                # Query to get adjacent stations with distances
                distance_query = """
                MATCH (y:Year {year: $year})
                MATCH (l:Line)-[:IN_YEAR]->(y)
                WHERE l.east_west = $side
                """ + (f"AND l.line_id = '{line_id}'" if line_id else "") + """
                MATCH (l)-[r1:SERVES]->(s1:Station)
                MATCH (l)-[r2:SERVES]->(s2:Station)
                WHERE r2.stop_order = r1.stop_order + 1
                OPTIONAL MATCH (s1)-[c:CONNECTS_TO]->(s2)
                RETURN 
                    l.line_id as line_id,
                    l.name as line_name,
                    s1.stop_id as station1_id,
                    s1.name as station1_name,
                    s2.stop_id as station2_id,
                    s2.name as station2_name,
                    r1.stop_order as stop_order1,
                    r2.stop_order as stop_order2,
                    c.distance_meters as distance,
                    s1.latitude as lat1, s1.longitude as lng1,
                    s2.latitude as lat2, s2.longitude as lng2
                ORDER BY l.line_id, r1.stop_order
                """
                
                result = session.run(distance_query, year=int(year), side=side)
                
                for record in result.data():
                    line_id = record['line_id']
                    line_name = record['line_name']
                    station1 = {
                        'id': record['station1_id'],
                        'name': record['station1_name'],
                        'order': record['stop_order1']
                    }
                    station2 = {
                        'id': record['station2_id'],
                        'name': record['station2_name'],
                        'order': record['stop_order2']
                    }
                    
                    # Use stored distance or calculate if missing
                    distance = record['distance']
                    if not distance and all([record['lat1'], record['lng1'], record['lat2'], record['lng2']]):
                        distance = self._calculate_distance(
                            record['lat1'], record['lng1'],
                            record['lat2'], record['lng2']
                        )
                    
                    if distance:
                        issue_type = None
                        severity = 'info'
                        
                        if distance < MIN_DISTANCE:
                            issue_type = 'too_close'
                            severity = 'error'
                        elif distance > MAX_DISTANCE:
                            issue_type = 'too_far'
                            severity = 'warning'
                        elif distance < OPTIMAL_MIN:
                            issue_type = 'closer_than_optimal'
                            severity = 'info'
                        elif distance > OPTIMAL_MAX:
                            issue_type = 'farther_than_optimal'
                            severity = 'info'
                        
                        if issue_type:
                            issues.append({
                                'type': issue_type,
                                'severity': severity,
                                'line_id': line_id,
                                'line_name': line_name,
                                'station1': station1,
                                'station2': station2,
                                'distance': distance,
                                'message': self._format_distance_message(issue_type, distance, station1['name'], station2['name'])
                            })
                    else:
                        # Missing coordinates or distance
                        issues.append({
                            'type': 'missing_distance',
                            'severity': 'warning',
                            'line_id': line_id,
                            'line_name': line_name,
                            'station1': station1,
                            'station2': station2,
                            'distance': None,
                            'message': f"Cannot calculate distance between {station1['name']} and {station2['name']} - missing coordinates"
                        })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating distances for {year_side}: {e}")
            return [{'type': 'validation_error', 'severity': 'error', 'message': str(e)}]

    def _format_distance_message(self, issue_type, distance, station1_name, station2_name):
        """Format a human-readable message for distance issues"""
        distance_km = distance / 1000
        
        messages = {
            'too_close': f"Stations {station1_name} and {station2_name} are very close ({distance_km:.2f}km) - possible duplicate",
            'too_far': f"Stations {station1_name} and {station2_name} are very far apart ({distance_km:.2f}km) - possible missing station",
            'closer_than_optimal': f"Stations {station1_name} and {station2_name} are closer than optimal ({distance_km:.2f}km)",
            'farther_than_optimal': f"Stations {station1_name} and {station2_name} are farther than optimal ({distance_km:.2f}km)"
        }
        
        return messages.get(issue_type, f"Distance issue between {station1_name} and {station2_name}: {distance_km:.2f}km")

    def update_station_source(self, stop_id, new_source):
        """
        Update a station's source in the database
        
        Args:
            stop_id: Station ID to update
            new_source: New source value
            
        Returns:
            True if successful, False otherwise
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station {stop_id: $stop_id})
                SET s.source = $new_source
                RETURN s.stop_id as stop_id
                """, stop_id=stop_id, new_source=new_source)
                
                return result.single() is not None
        except Exception as e:
            logger.error(f"Error updating station source: {e}")
            return False

    def get_station_source(self, stop_id):
        """
        Get the source for a station
        
        Args:
            stop_id: Station ID to query
            
        Returns:
            Source string if found, None otherwise
        """
        self.connect()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station {stop_id: $stop_id})
                RETURN s.source as source
                """, stop_id=stop_id)
                
                record = result.single()
                if record and record["source"] is not None:
                    return record["source"]
                return None
        except Exception as e:
            logger.error(f"Error getting station source: {e}")
            return None
            
    def add_station(self, year_side, station_data, line_connections=None):
        """
        Add a new station to the database with proper CONNECTS_TO relationship handling
        
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
                WITH s.stop_id as stop_id
                ORDER BY toInteger(substring(stop_id, 4)) DESC
                LIMIT 1
                RETURN stop_id
                """
                
                id_result = session.run(new_id_query, year=int(year), side=side)
                record = id_result.single()
                
                if record:
                    # Extract number from existing ID and increment
                    last_id = record['stop_id']
                    # Assuming format like "1965123_west"
                    number_part = int(last_id.split('_')[0][4:])  # Extract number after year
                    new_number = number_part + 1
                else:
                    new_number = 1
                
                new_stop_id = f"{year}{new_number:03d}_{side}"  # e.g. "1965001_west"
                
                # Create the new station
                create_query = """
                MATCH (y:Year {year: $year})
                CREATE (s:Station {
                    stop_id: $stop_id,
                    name: $name,
                    type: $type,
                    latitude: $latitude,
                    longitude: $longitude,
                    east_west: $side,
                    source: $source
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
                                        side=side,
                                        source=station_data.get('source', 'User added'))
                
                new_id = station_result.single()['new_id'] if station_result.single() else None
                
                # Connect to lines if specified
                line_results = []
                connects_to_results = []
                
                if line_connections and new_id:
                    for connection in line_connections:
                        line_id = connection['line_id']
                        stop_order = connection['stop_order']
                        
                        # Step 1: Get adjacent stations at the insertion point
                        adjacent_query = """
                        MATCH (y:Year {year: $year})
                        MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y)
                        WHERE l.east_west = $side
                        MATCH (l)-[r:SERVES]->(s:Station)
                        WHERE r.stop_order IN [$prev_order, $curr_order]
                        RETURN s.stop_id as stop_id, r.stop_order as stop_order
                        ORDER BY r.stop_order
                        """
                        
                        adjacent_result = session.run(adjacent_query,
                                                    year=int(year),
                                                    side=side,
                                                    line_id=line_id,
                                                    prev_order=stop_order - 1,
                                                    curr_order=stop_order)
                        
                        adjacent_stations = [dict(record) for record in adjacent_result]
                        
                        prev_station = None
                        next_station = None
                        
                        for station in adjacent_stations:
                            if station['stop_order'] == stop_order - 1:
                                prev_station = station['stop_id']
                            elif station['stop_order'] == stop_order:
                                next_station = station['stop_id']
                        
                        # Step 2: Handle existing CONNECTS_TO relationship if both adjacent stations exist
                        if prev_station and next_station:
                            # Get properties from existing connection
                            existing_connection_query = """
                            MATCH (prev:Station {stop_id: $prev_id})-[r:CONNECTS_TO]->(next:Station {stop_id: $next_id})
                            RETURN properties(r) as props
                            """
                            
                            existing_result = session.run(existing_connection_query,
                                                        prev_id=prev_station,
                                                        next_id=next_station)
                            
                            existing_record = existing_result.single()
                            existing_props = existing_record['props'] if existing_record else {}
                            
                            # Delete the existing direct connection
                            delete_connection_query = """
                            MATCH (prev:Station {stop_id: $prev_id})-[r:CONNECTS_TO]->(next:Station {stop_id: $next_id})
                            DELETE r
                            """
                            
                            session.run(delete_connection_query,
                                    prev_id=prev_station,
                                    next_id=next_station)
                            
                            # Calculate distances for new connections
                            new_station_coords = (station_data['latitude'], station_data['longitude'])
                            
                            # Get coordinates of adjacent stations
                            coords_query = """
                            MATCH (s:Station {stop_id: $stop_id})
                            RETURN s.latitude as lat, s.longitude as lng
                            """
                            
                            prev_coords_result = session.run(coords_query, stop_id=prev_station)
                            prev_coords_record = prev_coords_result.single()
                            prev_coords = (prev_coords_record['lat'], prev_coords_record['lng']) if prev_coords_record else None
                            
                            next_coords_result = session.run(coords_query, stop_id=next_station)
                            next_coords_record = next_coords_result.single()
                            next_coords = (next_coords_record['lat'], next_coords_record['lng']) if next_coords_record else None
                            
                            # Create new connections
                            if prev_coords:
                                distance_prev_new = self._calculate_distance(
                                    prev_coords[0], prev_coords[1],
                                    new_station_coords[0], new_station_coords[1]
                                )
                                
                                create_prev_connection_query = """
                                MATCH (prev:Station {stop_id: $prev_id})
                                MATCH (new:Station {stop_id: $new_id})
                                CREATE (prev)-[r:CONNECTS_TO]->(new)
                                SET r = $props
                                SET r.distance_meters = $distance
                                """
                                
                                session.run(create_prev_connection_query,
                                        prev_id=prev_station,
                                        new_id=new_id,
                                        props=existing_props,
                                        distance=distance_prev_new)
                            
                            if next_coords:
                                distance_new_next = self._calculate_distance(
                                    new_station_coords[0], new_station_coords[1],
                                    next_coords[0], next_coords[1]
                                )
                                
                                create_next_connection_query = """
                                MATCH (new:Station {stop_id: $new_id})
                                MATCH (next:Station {stop_id: $next_id})
                                CREATE (new)-[r:CONNECTS_TO]->(next)
                                SET r = $props
                                SET r.distance_meters = $distance
                                """
                                
                                session.run(create_next_connection_query,
                                        new_id=new_id,
                                        next_id=next_station,
                                        props=existing_props,
                                        distance=distance_new_next)
                            
                            connects_to_results.append({
                                'prev_station': prev_station,
                                'new_station': new_id,
                                'next_station': next_station,
                                'distance_prev_new': distance_prev_new if prev_coords else None,
                                'distance_new_next': distance_new_next if next_coords else None
                            })
                        
                        # Step 3: Shift stop orders to make room
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
                        
                        # Step 4: Connect the new station to the line
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
                    "line_connections": line_results,
                    "connects_to_updates": connects_to_results
                }
                
        except Exception as e:
            logger.error(f"Error adding station for {year_side}: {e}")
            return {"status": "error", "message": str(e)}
        
    def export_corrected_data(self, corrections_data):
        """
        Export data with corrections applied including location, name, and source updates
        
        Args:
            corrections_data: Dict of corrections by year_side and stop_id
            
        Returns:
            Dict with export status
        """
        results = {"status": "success", "updated_stations": 0, "details": []}
        
        self.connect()
        
        try:
            with self.driver.session() as session:
                for year_side, stops in corrections_data.items():
                    for stop_id, correction in stops.items():
                        # Build the update query dynamically based on available corrections
                        set_clauses = []
                        params = {"stop_id": stop_id}
                        
                        # Always update coordinates if available
                        if "lat" in correction and "lng" in correction:
                            set_clauses.append("s.latitude = $latitude, s.longitude = $longitude")
                            params["latitude"] = correction["lat"]
                            params["longitude"] = correction["lng"]
                        
                        # Update name if provided
                        if "name" in correction and correction["name"]:
                            set_clauses.append("s.name = $name")
                            params["name"] = correction["name"]
                        
                        # Update source if provided (though source is handled separately, 
                        # we include it here for completeness)
                        if "source" in correction and correction["source"]:
                            set_clauses.append("s.source = $source")
                            params["source"] = correction["source"]
                        
                        if set_clauses:
                            update_query = f"""
                            MATCH (s:Station {{stop_id: $stop_id}})
                            SET {', '.join(set_clauses)}
                            RETURN s.stop_id as stop_id, s.name as name, s.latitude as lat, s.longitude as lng
                            """
                            
                            result = session.run(update_query, params)
                            record = result.single()
                            
                            if record:
                                results["updated_stations"] += 1
                                results["details"].append({
                                    "stop_id": record["stop_id"],
                                    "name": record["name"],
                                    "coordinates": [record["lat"], record["lng"]],
                                    "corrections_applied": list(correction.keys())
                                })
                            else:
                                logger.warning(f"Station {stop_id} not found in database")
                                
            return results
        except Exception as e:
            logger.error(f"Error exporting corrections: {e}")
            return {"status": "error", "message": str(e)}
        
    def export_all_corrections_and_sources(self):
        """
        Export all corrections from both the corrections file and database sources
        This creates a comprehensive export that can be reapplied during data import
        
        Returns:
            Dict with all corrections data
        """
        self.connect()
        
        try:
            # Get all stations with their current state
            with self.driver.session() as session:
                result = session.run("""
                MATCH (s:Station)
                RETURN s.stop_id as stop_id, s.name as name, s.latitude as latitude, 
                    s.longitude as longitude, s.source as source, s.east_west as east_west
                """)
                
                all_stations = {}
                for record in result:
                    stop_id = record["stop_id"]
                    all_stations[stop_id] = {
                        "name": record["name"],
                        "latitude": record["latitude"],
                        "longitude": record["longitude"],
                        "source": record["source"],
                        "east_west": record["east_west"]
                    }
                
                return {
                    "status": "success",
                    "stations": all_stations,
                    "export_timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error exporting all corrections: {e}")
            return {"status": "error", "message": str(e)}