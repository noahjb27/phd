# station_manager.py
import json
import logging
from pathlib import Path
from db_connector import StationVerifierDB

logger = logging.getLogger(__name__)

class StationManager:
    def __init__(self, config):
        self.config = config
        self.corrections_file = config['CORRECTIONS_DIR'] / "station_corrections.json"
        self.additions_file = config['CORRECTIONS_DIR'] / "station_additions.json"
        
        # Ensure files exist
        for file_path in [self.corrections_file, self.additions_file]:
            file_path.parent.mkdir(exist_ok=True)
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump({}, f)
        
        self.db = StationVerifierDB(
            uri=config['DB_URI'],
            username=config['DB_USERNAME'],
            password=config['DB_PASSWORD']
        )
    
    def add_station(self, station_data):
        """Add a new station with proper validation and line integration"""
        try:
            # Validate required fields
            required_fields = ['year_side', 'name', 'type', 'latitude', 'longitude']
            for field in required_fields:
                if field not in station_data or not station_data[field]:
                    return {"status": "error", "message": f"Missing required field: {field}"}
            
            # Validate coordinates
            try:
                lat = float(station_data['latitude'])
                lng = float(station_data['longitude'])
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return {"status": "error", "message": "Invalid coordinates"}
            except (ValueError, TypeError):
                return {"status": "error", "message": "Invalid coordinate format"}
            
            # Validate year_side format
            try:
                year, side = station_data['year_side'].split('_')
                int(year)  # Ensure year is numeric
                if side not in ['east', 'west', 'unified']:
                    return {"status": "error", "message": "Invalid side (must be 'unified', 'east' or 'west')"}
            except ValueError:
                return {"status": "error", "message": "Invalid year_side format (must be 'YYYY_side')"}
            
            # Validate station name
            station_name = station_data['name'].strip()
            if len(station_name) < 2:
                return {"status": "error", "message": "Station name must be at least 2 characters long"}
            
            # Prepare station data for database
            db_station_data = {
                'name': station_name,
                'type': station_data['type'],
                'latitude': lat,
                'longitude': lng,
                'source': station_data.get('source', 'User added')
            }
            
            # Use the consolidated add_station method
            result = self.db.add_station(
                station_data['year_side'],
                db_station_data,
                station_data.get('line_connections', [])
            )
            
            if result['status'] == 'success':
                logger.info(f"Successfully added station {result.get('new_station_id')} in {station_data['year_side']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding station: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}
        
    def delete_station(self, stop_id, year_side):
        """Delete a station and handle corrections cleanup"""
        try:
            # Delete from database
            result = self.db.delete_station(stop_id, year_side)
            
            # If successful, also remove from corrections
            if result.get('status') == 'success':
                self._remove_from_corrections(stop_id, year_side)
                logger.info(f"Successfully deleted station {stop_id} from {year_side}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting station {stop_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def save_location_correction(self, year_side, stop_id, lat, lng):
        """Save a location correction"""
        try:
            # Validate coordinates
            try:
                lat = float(lat)
                lng = float(lng)
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return {"status": "error", "message": "Invalid coordinates"}
            except (ValueError, TypeError):
                return {"status": "error", "message": "Invalid coordinate format"}
            
            corrections = self._load_corrections()
            
            if year_side not in corrections:
                corrections[year_side] = {}
            
            if stop_id not in corrections[year_side]:
                corrections[year_side][stop_id] = {}
            
            corrections[year_side][stop_id]["lat"] = lat
            corrections[year_side][stop_id]["lng"] = lng
            
            self._save_corrections(corrections)
            logger.info(f"Saved location correction for station {stop_id} in {year_side}")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error saving location correction: {e}")
            return {"status": "error", "message": str(e)}
    
    def save_name_correction(self, year_side, stop_id, name):
        """Save a name correction"""
        try:
            if not name or not name.strip():
                return {"status": "error", "message": "Name cannot be empty"}
            
            name = name.strip()
            if len(name) < 2:
                return {"status": "error", "message": "Name must be at least 2 characters long"}
            
            corrections = self._load_corrections()
            
            if year_side not in corrections:
                corrections[year_side] = {}
            
            if stop_id not in corrections[year_side]:
                # Need to get current coordinates for new correction
                coords = self.db.get_station_coordinates(stop_id)
                if not coords:
                    return {"status": "error", "message": "Could not find station coordinates"}
                
                corrections[year_side][stop_id] = {
                    "lat": coords["latitude"],
                    "lng": coords["longitude"]
                }
            
            corrections[year_side][stop_id]["name"] = name
            
            self._save_corrections(corrections)
            logger.info(f"Saved name correction for station {stop_id} in {year_side}")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error saving name correction: {e}")
            return {"status": "error", "message": str(e)}
    
    def save_source_correction(self, stop_id, source):
        """Save a source correction directly to database"""
        try:
            if not source or not source.strip():
                return {"status": "error", "message": "Source cannot be empty"}
            
            source = source.strip()
            success = self.db.update_station_source(stop_id, source)
            
            if success:
                logger.info(f"Updated source for station {stop_id} to '{source}'")
                return {"status": "success"}
            else:
                return {"status": "error", "message": "Could not update station source"}
                
        except Exception as e:
            logger.error(f"Error saving source correction: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_line_details(self, year_side, line_id):
        """Get line details for station insertion"""
        try:
            year, side = year_side.split('_')
            
            self.db.connect()
            with self.db.driver.session() as session:
                # Get line stops in order
                result = session.run("""
                MATCH (l:Line {line_id: $line_id})-[:IN_YEAR]->(y:Year {year: $year})
                WHERE l.east_west = $side
                MATCH (l)-[r:SERVES]->(s:Station)
                RETURN s.stop_id as stop_id, s.name as name, r.stop_order as stop_order
                ORDER BY r.stop_order
                """, line_id=line_id, year=int(year), side=side)
                
                stops = [dict(record) for record in result]
                
                # Calculate insertion points
                insertion_points = []
                for i in range(len(stops) + 1):
                    if i == 0:
                        description = f"Before {stops[0]['name']}" if stops else "First stop"
                    elif i == len(stops):
                        description = f"After {stops[-1]['name']}"
                    else:
                        description = f"Between {stops[i-1]['name']} and {stops[i]['name']}"
                    
                    insertion_points.append({
                        "stop_order": i + 1,
                        "description": description
                    })
                
                return {
                    "status": "success",
                    "line_id": line_id,
                    "stops": stops,
                    "insertion_points": insertion_points
                }
                
        except Exception as e:
            logger.error(f"Error getting line details for {year_side}/{line_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _load_corrections(self):
        """Load corrections from file with error handling"""
        try:
            if self.corrections_file.exists() and self.corrections_file.stat().st_size > 0:
                with open(self.corrections_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in corrections file: {e}")
        except Exception as e:
            logger.error(f"Error loading corrections: {e}")
        return {}
    
    def _save_corrections(self, corrections):
        """Save corrections to file"""
        try:
            with open(self.corrections_file, 'w') as f:
                json.dump(corrections, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving corrections: {e}")
            raise
    
    def _remove_from_corrections(self, stop_id, year_side):
        """Remove a station from corrections file"""
        try:
            corrections = self._load_corrections()
            if year_side in corrections and stop_id in corrections[year_side]:
                del corrections[year_side][stop_id]
                
                # Clean up empty year_side entries
                if not corrections[year_side]:
                    del corrections[year_side]
                
                self._save_corrections(corrections)
                logger.info(f"Removed station {stop_id} from corrections file")
        except Exception as e:
            logger.error(f"Error removing from corrections: {e}")