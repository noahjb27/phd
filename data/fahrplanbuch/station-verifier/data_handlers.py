# data_handlers.py
import pandas as pd
import json
import logging
from pathlib import Path
from db_connector import StationVerifierDB

logger = logging.getLogger(__name__)

class DataHandler:
    def __init__(self, config):
        self.config = config
        self.corrections_file = config['CORRECTIONS_DIR'] / "station_corrections.json"
        self.corrections_file.parent.mkdir(exist_ok=True)
        
        # Initialize corrections file if it doesn't exist
        if not self.corrections_file.exists():
            with open(self.corrections_file, 'w') as f:
                json.dump({}, f)
        
        self.db = StationVerifierDB(
            uri=config['DB_URI'],
            username=config['DB_USERNAME'],
            password=config['DB_PASSWORD']
        )
    
    def get_available_year_sides(self):
        """Get list of all available year-side combinations"""
        return self.db.get_available_year_sides()
    
    def get_year_side_data(self, year_side):
        """Get all data for a specific year_side with corrections applied"""
        # Load corrections
        corrections = self.get_corrections()
        
        # Get raw data from database
        data = self.db.get_year_side_data(year_side)
        stops_df = data["stops"]
        lines_df = data["lines"]
        
        if stops_df.empty:
            return {"error": f"No data found for {year_side}"}
        
        # Apply corrections
        stops_display = self._apply_corrections_to_dataframe(stops_df, corrections, year_side)
        
        # Convert to GeoJSON
        geojson_features = self._dataframe_to_geojson(stops_display, year_side, corrections)
        
        # Format lines data
        lines = [{"line_id": row['line_id'], "line_name": row['line_name'], "type": row['type']} 
                for _, row in lines_df.iterrows()]
        
        return {
            "geojson": {"type": "FeatureCollection", "features": geojson_features},
            "lines": lines
        }
    
    def get_multiple_datasets(self, year_sides, line_filters):
        """Get data for multiple year_sides with line filtering"""
        corrections = self.get_corrections()
        result = {}
        
        for year_side in year_sides:
            try:
                data = self.db.get_year_side_data(year_side)
                stops_df = data["stops"]
                lines_df = data["lines"]
                line_stops_df = data["line_stops"]
                
                if stops_df.empty:
                    result[year_side] = {"error": f"No data found for {year_side}"}
                    continue
                
                # Apply line filter if specified
                if year_side in line_filters and line_filters[year_side] != "all":
                    line_id = line_filters[year_side]
                    filtered_line_stops = line_stops_df[line_stops_df['line_id'] == line_id]
                    stops_df = stops_df[stops_df['stop_id'].isin(filtered_line_stops['stop_id'])]
                
                # Apply corrections and convert to GeoJSON
                stops_display = self._apply_corrections_to_dataframe(stops_df, corrections, year_side)
                geojson_features = self._dataframe_to_geojson(stops_display, year_side, corrections)
                
                lines = [{"line_id": row['line_id'], "line_name": row['line_name'], "type": row['type']} 
                        for _, row in lines_df.iterrows()]
                
                result[year_side] = {
                    "geojson": {"type": "FeatureCollection", "features": geojson_features},
                    "lines": lines
                }
            except Exception as e:
                logger.error(f"Error processing {year_side}: {e}")
                result[year_side] = {"error": str(e)}
        
        return result
    
    def _apply_corrections_to_dataframe(self, stops_df, corrections, year_side):
        """Apply corrections to a stops dataframe"""
        stops_display = stops_df.copy()
        
        for stop_id, correction in corrections.get(year_side, {}).items():
            if stop_id in stops_display['stop_id'].values:
                idx = stops_display.loc[stops_display['stop_id'] == stop_id].index[0]
                if 'lat' in correction and 'lng' in correction:
                    stops_display.at[idx, 'latitude'] = correction['lat']
                    stops_display.at[idx, 'longitude'] = correction['lng']
                if 'name' in correction:
                    stops_display.at[idx, 'stop_name'] = correction['name']
        
        return stops_display
    
    def _dataframe_to_geojson(self, stops_df, year_side, corrections):
        """Convert stops dataframe to GeoJSON features"""
        features = []
        
        for _, row in stops_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                try:
                    lat, lng = float(row['latitude']), float(row['longitude'])
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lng, lat]
                        },
                        "properties": {
                            "stop_id": row['stop_id'],
                            "name": row['stop_name'],
                            "type": row['type'],
                            "line": row.get('line_name', ''),
                            "source": row.get('source', 'Not specified'),
                            "year_side": year_side,
                            "corrected": str(row['stop_id']) in corrections.get(year_side, {})
                        }
                    }
                    features.append(feature)
                except Exception as e:
                    logger.warning(f"Error processing stop {row['stop_id']}: {e}")
        
        return features
    
    def get_corrections(self):
        """Load corrections from file"""
        try:
            if self.corrections_file.exists() and self.corrections_file.stat().st_size > 0:
                with open(self.corrections_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading corrections: {e}")
        return {}
    
    def export_corrections(self, corrections):
        """Export corrections to database"""
        try:
            result = self.db.export_corrected_data(corrections)
            return result
        except Exception as e:
            logger.error(f"Error exporting corrections: {e}")
            return {"status": "error", "message": str(e)}