# validation_service.py
import logging
from db_connector import StationVerifierDB

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self, config):
        self.config = config
        self.db = StationVerifierDB(
            uri=config['DB_URI'],
            username=config['DB_USERNAME'],
            password=config['DB_PASSWORD']
        )
    
    def validate_station_distances(self, year_side, line_id=None):
        """Validate distances between stations"""
        try:
            if not year_side:
                return {"status": "error", "message": "year_side is required"}
            
            # Validate year_side format
            try:
                year, side = year_side.split('_')
                int(year)  # Ensure year is numeric
                if side not in ['east', 'west']:
                    return {"status": "error", "message": "Invalid side (must be 'east' or 'west')"}
            except ValueError:
                return {"status": "error", "message": "Invalid year_side format (must be 'YYYY_side')"}
            
            issues = self.db.validate_station_distances(year_side, line_id)
            
            logger.info(f"Validated distances for {year_side}" + 
                       (f" line {line_id}" if line_id else "") + 
                       f", found {len(issues)} issues")
            
            return {
                "status": "success",
                "issues": issues,
                "year_side": year_side,
                "line_id": line_id
            }
            
        except Exception as e:
            logger.error(f"Error validating distances for {year_side}: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_position(self, year_side, latitude, longitude, line_id=None):
        """Validate a proposed station position"""
        try:
            if not all([year_side, latitude is not None, longitude is not None]):
                return {"status": "error", "message": "year_side, latitude, and longitude are required"}
            
            # Validate coordinates
            try:
                lat = float(latitude)
                lng = float(longitude)
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return {"status": "error", "message": "Invalid coordinates"}
            except (ValueError, TypeError):
                return {"status": "error", "message": "Invalid coordinate format"}
            
            # Validate year_side format
            try:
                year, side = year_side.split('_')
                int(year)  # Ensure year is numeric
                if side not in ['east', 'west']:
                    return {"status": "error", "message": "Invalid side (must be 'east' or 'west')"}
            except ValueError:
                return {"status": "error", "message": "Invalid year_side format (must be 'YYYY_side')"}
            
            # Check distance to nearby stations
            min_distance_threshold = 200  # meters
            warning_distance_threshold = 500  # meters
            
            nearby_stations = []
            warning_stations = []
            
            self.db.connect()
            with self.db.driver.session() as session:
                # Base query to get stations
                base_query = """
                MATCH (s:Station)-[:IN_YEAR]->(y:Year {year: $year})
                WHERE s.east_west = $side AND s.latitude IS NOT NULL AND s.longitude IS NOT NULL
                """
                
                # Add line filter if specified
                if line_id:
                    query = base_query + """
                    AND EXISTS((l:Line {line_id: $line_id})-[:SERVES]->(s))
                    RETURN s.stop_id as stop_id, s.name as name, s.type as type,
                           s.latitude as lat, s.longitude as lng
                    """
                    params = {"year": int(year), "side": side, "line_id": line_id}
                else:
                    query = base_query + """
                    RETURN s.stop_id as stop_id, s.name as name, s.type as type,
                           s.latitude as lat, s.longitude as lng
                    """
                    params = {"year": int(year), "side": side}
                
                result = session.run(query, params)
                
                for record in result:
                    distance = self.db._calculate_distance(
                        lat, lng,
                        record['lat'], record['lng']
                    )
                    
                    station_info = {
                        "stop_id": record['stop_id'],
                        "name": record['name'],
                        "type": record['type'],
                        "distance": distance
                    }
                    
                    if distance < min_distance_threshold:
                        nearby_stations.append(station_info)
                    elif distance < warning_distance_threshold:
                        warning_stations.append(station_info)
            
            # Sort by distance
            nearby_stations.sort(key=lambda x: x['distance'])
            warning_stations.sort(key=lambda x: x['distance'])
            
            warnings = []
            
            if nearby_stations:
                warnings.append({
                    "type": "nearby_stations",
                    "severity": "error",
                    "message": f"Proposed station is very close to {len(nearby_stations)} existing station(s)",
                    "stations": nearby_stations[:3]  # Show top 3 closest
                })
            
            if warning_stations:
                warnings.append({
                    "type": "close_stations",
                    "severity": "warning", 
                    "message": f"Proposed station is relatively close to {len(warning_stations)} existing station(s)",
                    "stations": warning_stations[:3]  # Show top 3 closest
                })
            
            # Check if position is within reasonable Berlin bounds
            berlin_bounds = {
                "north": 52.7,
                "south": 52.3,
                "east": 13.8,
                "west": 13.0
            }
            
            if not (berlin_bounds["south"] <= lat <= berlin_bounds["north"] and
                    berlin_bounds["west"] <= lng <= berlin_bounds["east"]):
                warnings.append({
                    "type": "location_bounds",
                    "severity": "warning",
                    "message": "Proposed station is outside typical Berlin boundaries",
                    "stations": []
                })
            
            logger.info(f"Validated position for {year_side}: {len(warnings)} warnings, " +
                       f"{len(nearby_stations)} nearby stations")
            
            return {
                "status": "success",
                "position": {"latitude": lat, "longitude": lng},
                "warnings": warnings,
                "nearby_stations": nearby_stations + warning_stations
            }
            
        except Exception as e:
            logger.error(f"Error validating position: {e}")
            return {"status": "error", "message": str(e)}
    
    def validate_line_connection(self, year_side, line_id, stop_order):
        """Validate a proposed line connection for a new station"""
        try:
            if not all([year_side, line_id, stop_order]):
                return {"status": "error", "message": "year_side, line_id, and stop_order are required"}
            
            try:
                stop_order = int(stop_order)
                if stop_order < 1:
                    return {"status": "error", "message": "stop_order must be positive"}
            except (ValueError, TypeError):
                return {"status": "error", "message": "stop_order must be a number"}
            
            year, side = year_side.split('_')
            
            self.db.connect()
            with self.db.driver.session() as session:
                # Check if line exists
                line_check = session.run("""
                MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y:Year {year: $year})
                WHERE l.east_west = $side
                RETURN l.line_id as line_id, l.name as line_name
                """, line_id=line_id, year=int(year), side=side)
                
                line_record = line_check.single()
                if not line_record:
                    return {
                        "status": "error",
                        "message": f"Line {line_id} not found in {year_side}"
                    }
                
                # Check current stop count and validate stop_order
                order_check = session.run("""
                MATCH (l:Line {line_id: $line_id})-[r:SERVES]->(:Station)
                RETURN max(r.stop_order) as max_order, count(r) as total_stops
                """, line_id=line_id)
                
                order_record = order_check.single()
                max_order = order_record['max_order'] if order_record['max_order'] else 0
                
                if stop_order > max_order + 1:
                    return {
                        "status": "error",
                        "message": f"Invalid stop order {stop_order}. Must be between 1 and {max_order + 1}"
                    }
                
                return {
                    "status": "success",
                    "line_name": line_record['line_name'],
                    "max_order": max_order,
                    "total_stops": order_record['total_stops']
                }
                
        except Exception as e:
            logger.error(f"Error validating line connection: {e}")
            return {"status": "error", "message": str(e)}