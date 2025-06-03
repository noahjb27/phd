# station-verifier/app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import os
from pathlib import Path
from flask_cors import CORS
import rasterio
from db_connector import StationVerifierDB

app = Flask(__name__)

# Configuration
DATA_DIR = Path("data")
CORRECTIONS_DIR = Path("corrections")
CORRECTIONS_FILE = CORRECTIONS_DIR / "station_corrections.json"

# Create corrections directory if it doesn't exist
CORRECTIONS_DIR.mkdir(exist_ok=True)

# Initialize corrections file if it doesn't exist
if not CORRECTIONS_FILE.exists():
    with open(CORRECTIONS_FILE, 'w') as f:
        json.dump({}, f)

# Define tiles directory
TILES_DIR = Path("tiles")
TILES_DIR.mkdir(exist_ok=True)

# Make sure the TIF files directory exists
TIF_DIR = TILES_DIR / "tif"
TIF_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database connection
db = StationVerifierDB()

CORS(app)

@app.route('/')
def index():
    # Get list of all available year_side combinations from the database
    year_sides = db.get_available_year_sides()
    
    return render_template('index.html', year_sides=year_sides)

@app.route('/data/<year_side>')
def get_year_side_data(year_side):
    """Get all data for a specific year_side"""
    
    # Load corrected stations
    corrections = {}
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            corrections = json.load(f)
    
    # Read data from database
    try:
        data = db.get_year_side_data(year_side)
        stops_df = data["stops"]
        lines_df = data["lines"]
        
        if stops_df.empty:
            return jsonify({"error": f"No data found for {year_side}"}), 404
        
        # Apply corrections to stops dataframe (only for display, not modifying original)
        stops_display = stops_df.copy()
        for stop_id, correction in corrections.get(year_side, {}).items():
            if stop_id in stops_display['stop_id'].values:
                idx = stops_display.loc[stops_display['stop_id'] == stop_id].index[0]
                stops_display.at[idx, 'latitude'] = correction['lat']
                stops_display.at[idx, 'longitude'] = correction['lng']
                if 'name' in correction:
                    stops_display.at[idx, 'stop_name'] = correction['name']
        
        # Convert to GeoJSON for mapping
        features = []
        for _, row in stops_display.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                try:
                    lat, lng = float(row['latitude']), float(row['longitude'])
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lng, lat]  # GeoJSON uses [lng, lat] order
                        },
                        "properties": {
                            "stop_id": row['stop_id'],
                            "name": row['stop_name'],
                            "type": row['type'],
                            "line": row['line_name'],
                            "corrected": str(row['stop_id']) in corrections.get(year_side, {})
                        }
                    }
                    features.append(feature)
                except Exception as e:
                    print(f"Error with stop {row['stop_id']}: {e}")
        
        # Get line data
        lines = []
        for _, row in lines_df.iterrows():
            lines.append({
                "line_id": row['line_id'],
                "line_name": row['line_name'],
                "type": row['type']
            })
            
        return jsonify({
            "geojson": {"type": "FeatureCollection", "features": features},
            "lines": lines
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/multi_data', methods=['POST'])
def get_multiple_datasets():
    """Get data for multiple year_sides with optional line filtering"""
    # Get request data
    data = request.json
    year_sides = data.get('year_sides', [])
    line_filters = data.get('line_filters', {})  # Dict mapping year_side to line_id
    
    if not year_sides:
        return jsonify({"error": "No year_sides specified"}), 400
    
    # Load corrected stations
    corrections = {}
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            corrections = json.load(f)
    
    # Process each year_side
    result = {}
    
    for year_side in year_sides:
        try:
            # Get data from database
            data = db.get_year_side_data(year_side)
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
            
            # Apply corrections to stops dataframe
            stops_display = stops_df.copy()
            for stop_id, correction in corrections.get(year_side, {}).items():
                if stop_id in stops_display['stop_id'].values:
                    idx = stops_display.loc[stops_display['stop_id'] == stop_id].index[0]
                    stops_display.at[idx, 'latitude'] = correction['lat']
                    stops_display.at[idx, 'longitude'] = correction['lng']
                    if 'name' in correction:
                        stops_display.at[idx, 'stop_name'] = correction['name']
            
            # Convert to GeoJSON for mapping
            features = []
            for _, row in stops_display.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    try:
                        lat, lng = float(row['latitude']), float(row['longitude'])
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lng, lat]  # GeoJSON uses [lng, lat] order
                            },
                            "properties": {
                                "stop_id": row['stop_id'],
                                "name": row['stop_name'],
                                "type": row['type'],
                                "line": row['line_name'],
                                "year_side": year_side,  # Add year_side for identification
                                "corrected": str(row['stop_id']) in corrections.get(year_side, {})
                            }
                        }
                        features.append(feature)
                    except Exception as e:
                        print(f"Error with stop {row['stop_id']}: {e}")
            
            # Get line data
            lines = []
            for _, row in lines_df.iterrows():
                lines.append({
                    "line_id": row['line_id'],
                    "line_name": row['line_name'],
                    "type": row['type']
                })
                
            result[year_side] = {
                "geojson": {"type": "FeatureCollection", "features": features},
                "lines": lines
            }
            
        except Exception as e:
            result[year_side] = {"error": str(e)}
    
    return jsonify(result)

@app.route('/save_correction', methods=['POST'])
def save_correction():
    """Save a station location and/or name correction"""
    data = request.json
    year_side = data['year_side']
    stop_id = str(data['stop_id'])  # Ensure stop_id is a string
    lat = data['lat']
    lng = data['lng']
    name = data.get('name')  # Optional name update
    
    # Load existing corrections
    with open(CORRECTIONS_FILE, 'r') as f:
        corrections = json.load(f)
    
    # Add or update correction
    if year_side not in corrections:
        corrections[year_side] = {}
    
    # Create or update the correction entry
    if stop_id not in corrections[year_side]:
        corrections[year_side][stop_id] = {}
        
    # Update coordinates
    corrections[year_side][stop_id]["lat"] = lat
    corrections[year_side][stop_id]["lng"] = lng
    
    # Update name if provided
    if name is not None:
        corrections[year_side][stop_id]["name"] = name
    
    # Save corrections
    with open(CORRECTIONS_FILE, 'w') as f:
        json.dump(corrections, f, indent=2)
    
    return jsonify({"status": "success"})

@app.route('/delete_station', methods=['POST'])
def delete_station():
    """Delete a station and update line-station relationships"""
    data = request.json
    year_side = data['year_side']
    stop_id = str(data['stop_id'])  # Ensure stop_id is a string
    
    # Delete from database
    result = db.delete_station(stop_id, year_side)
    
    # If successful, also remove from corrections file if present
    if result['status'] == 'success':
        try:
            with open(CORRECTIONS_FILE, 'r') as f:
                corrections = json.load(f)
            
            if year_side in corrections and stop_id in corrections[year_side]:
                del corrections[year_side][stop_id]
                
                with open(CORRECTIONS_FILE, 'w') as f:
                    json.dump(corrections, f, indent=2)
        except Exception as e:
            print(f"Error removing deleted station from corrections: {e}")
    
    return jsonify(result)

@app.route('/add_station', methods=['POST'])
def add_station():
    """Add a new station with optional line connections"""
    data = request.json
    year_side = data['year_side']
    station_data = {
        'name': data['name'],
        'type': data['type'],
        'latitude': data['latitude'],
        'longitude': data['longitude']
    }
    
    # Optional line connections
    line_connections = data.get('line_connections', None)
    
    # Add to database
    result = db.add_station(year_side, station_data, line_connections)
    
    return jsonify(result)

@app.route('/export_corrections')
def export_corrections():
    """Export corrected data to Neo4j database"""
    # Load corrections
    with open(CORRECTIONS_FILE, 'r') as f:
        corrections = json.load(f)
    
    # Update database with all corrections
    result = db.export_corrected_data(corrections)
    
    return jsonify(result)

@app.route('/get_corrections')
def get_corrections():
    """Get all corrections"""
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            corrections = json.load(f)
        return jsonify(corrections)
    return jsonify({})

# Keep the existing tile-related routes unchanged
@app.route('/tiles/<path:filepath>')
def serve_tile(filepath):
    """Serve a tile from the tiles directory"""
    return send_from_directory(str(TILES_DIR), filepath)

@app.route('/available_tile_sets')
def available_tile_sets():
    """List all available tile sets"""
    if not TILES_DIR.exists():
        return jsonify([])
    
    tile_sets = []
    
    # Look for directories containing tile data (zoom level directories)
    for item in os.listdir(TILES_DIR):
        item_path = TILES_DIR / item
        
        # Skip the original TIF files or directories
        if item.endswith(('.tif', '.tiff')) or item == "tif":
            continue
            
        if item_path.is_dir():
            # Check if this looks like a valid tile directory (has zoom level subdirectories)
            zoom_dirs = [d for d in os.listdir(item_path) if d.isdigit()]
            
            if zoom_dirs:
                tile_sets.append({
                    "name": item,
                    "url": f"/tiles/{item}/{{z}}/{{x}}/{{y}}.png",
                    "zoom_levels": sorted([int(z) for z in zoom_dirs])
                })
    
    return jsonify(tile_sets)

@app.route('/list_tif_files')
def list_tif_files():
    """List all TIF files in the tiles/tif directory"""
    tif_dir = TILES_DIR / "tif"
    
    if not tif_dir.exists():
        return jsonify({"error": "Directory not found"}), 404
    
    tif_files = []
    for item in os.listdir(tif_dir):
        if item.lower().endswith(('.tif', '.tiff')):
            tif_files.append(item)
    
    return jsonify({"tif_files": tif_files})

@app.route('/process_tif/<filename>', methods=['POST'])
def process_single_tif(filename):
    """Process a single TIF file"""
    from rasterio_tile_generator import generate_xyz_tiles_rasterio
    
    tif_path = TILES_DIR / "tif" / filename
    
    if not tif_path.exists():
        return jsonify({"error": f"File not found: {filename}"}), 404
    
    output_dir = TILES_DIR / tif_path.stem
    
    success = generate_xyz_tiles_rasterio(
        tiff_file=tif_path,
        output_dir=output_dir,
        min_zoom=10,
        max_zoom=16
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Tiles generated for {filename}",
            "url": f"/tiles/{tif_path.stem}/{{z}}/{{x}}/{{y}}.png"
        })
    else:
        return jsonify({"error": "Failed to generate tiles"}), 500

@app.route('/process_all_tifs', methods=['POST'])
def process_all_tifs():
    """Process all TIF files in the tif directory"""
    from rasterio_tile_generator import process_tif_directory
    
    # Make sure the directory exists
    tif_dir = TILES_DIR / "tif"
    if not tif_dir.exists() or not any(f.endswith(('.tif', '.tiff')) for f in os.listdir(tif_dir)):
        return jsonify({
            "status": "error",
            "message": "No TIF files found in the tiles/tif directory. Please add TIF files first."
        }), 400
    
    results = process_tif_directory(
        base_dir=TILES_DIR / "tif",
        output_base_dir=TILES_DIR,
        min_zoom=10,
        max_zoom=16
    )
    
    success_count = sum(1 for result in results.values() if result["success"])
    
    return jsonify({
        "status": "success",
        "message": f"Processed {len(results)} files. {success_count} succeeded.",
        "details": results
    })

@app.route('/save_name_correction', methods=['POST'])
def save_name_correction():
    """Save a station name correction"""
    data = request.json
    year_side = data['year_side']
    stop_id = str(data['stop_id'])  # Ensure stop_id is a string
    name = data['name']
    
    if not name or not name.strip():
        return jsonify({"status": "error", "message": "Name cannot be empty"}), 400
    
    # Initialize corrections with an empty dict in case the file is empty or corrupted
    corrections = {}
    
    # Load existing corrections with better error handling
    try:
        if CORRECTIONS_FILE.exists() and CORRECTIONS_FILE.stat().st_size > 0:
            with open(CORRECTIONS_FILE, 'r') as f:
                file_content = f.read()
                if file_content.strip():  # Check if file is not just whitespace
                    corrections = json.loads(file_content)
    except json.JSONDecodeError as e:
        # If JSON is invalid, log error and start fresh
        print(f"Error reading corrections file: {e}")
        corrections = {}
    except Exception as e:
        print(f"Unexpected error reading corrections file: {e}")
        return jsonify({"status": "error", "message": f"Error reading corrections file: {str(e)}"}), 500
    
    # Add or update correction
    if year_side not in corrections:
        corrections[year_side] = {}
    
    # Create or update the correction entry
    if stop_id not in corrections[year_side]:
        corrections[year_side][stop_id] = {}
        
    # For name-only updates, preserve existing lat/lng if they exist
    if 'lat' in corrections[year_side][stop_id] and 'lng' in corrections[year_side][stop_id]:
        corrections[year_side][stop_id]["name"] = name
    else:
        # If no existing lat/lng, need to get current coordinates from the database
        station_coords = db.get_station_coordinates(stop_id)
        if station_coords:
            corrections[year_side][stop_id]["lat"] = station_coords["latitude"]
            corrections[year_side][stop_id]["lng"] = station_coords["longitude"]
            corrections[year_side][stop_id]["name"] = name
        else:
            return jsonify({"status": "error", "message": "Could not find station coordinates"}), 404
    
    # Save corrections with error handling
    try:
        with open(CORRECTIONS_FILE, 'w') as f:
            json.dump(corrections, f, indent=2)
    except Exception as e:
        print(f"Error saving corrections file: {e}")
        return jsonify({"status": "error", "message": f"Error saving corrections: {str(e)}"}), 500
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)