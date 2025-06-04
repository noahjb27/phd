# app.py - Refactored main application file
from flask import Flask, render_template, request, jsonify
import json
import os
from pathlib import Path
from flask_cors import CORS
import logging

# Import our modular services
from data_handlers import DataHandler
from station_manager import StationManager
from validation_service import ValidationService
from tile_service import TileService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config.update(
        DATA_DIR=Path("data"),
        CORRECTIONS_DIR=Path("corrections"),
        TILES_DIR=Path("tiles"),
        DB_URI=os.environ.get("NEO4J_URI", "bolt://100.82.176.18:7687"),
        DB_USERNAME=os.environ.get("NEO4J_USERNAME", "neo4j"),
        DB_PASSWORD=os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024")
    )
    
    # Ensure directories exist
    for dir_path in [app.config['CORRECTIONS_DIR'], app.config['TILES_DIR']]:
        dir_path.mkdir(exist_ok=True)
    
    # Initialize services
    data_handler = DataHandler(app.config)
    station_manager = StationManager(app.config)
    validation_service = ValidationService(app.config)
    tile_service = TileService(app.config)
    
    # Register routes
    register_main_routes(app, data_handler)
    register_data_routes(app, data_handler)
    register_station_routes(app, station_manager)
    register_validation_routes(app, validation_service)
    register_tile_routes(app, tile_service)
    
    logger.info("Station Verifier application initialized successfully")
    return app

# =============================================================================
# MAIN ROUTES
# =============================================================================
def register_main_routes(app, data_handler):
    @app.route('/')
    def index():
        """Main application page"""
        try:
            year_sides = data_handler.get_available_year_sides()
            return render_template('index.html', year_sides=year_sides)
        except Exception as e:
            logger.error(f"Error loading main page: {e}")
            return render_template('error.html', error=str(e)), 500

# =============================================================================
# DATA ROUTES
# =============================================================================
def register_data_routes(app, data_handler):
    @app.route('/data/<year_side>')
    def get_year_side_data(year_side):
        """Get all data for a specific year_side"""
        try:
            result = data_handler.get_year_side_data(year_side)
            if "error" in result:
                return jsonify(result), 404
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error retrieving data for {year_side}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/multi_data', methods=['POST'])
    def get_multiple_datasets():
        """Get data for multiple year_sides with optional line filtering"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            year_sides = data.get('year_sides', [])
            line_filters = data.get('line_filters', {})
            
            if not year_sides:
                return jsonify({"error": "No year_sides specified"}), 400
            
            result = data_handler.get_multiple_datasets(year_sides, line_filters)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error retrieving multiple datasets: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/get_corrections')
    def get_corrections():
        """Get all corrections"""
        try:
            corrections = data_handler.get_corrections()
            return jsonify(corrections)
        except Exception as e:
            logger.error(f"Error getting corrections: {e}")
            return jsonify({}), 500

    @app.route('/export_corrections')
    def export_corrections():
        """Export corrected data to Neo4j database"""
        try:
            corrections = data_handler.get_corrections()
            result = data_handler.export_corrections(corrections)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error exporting corrections: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

# =============================================================================
# STATION MANAGEMENT ROUTES
# =============================================================================
def register_station_routes(app, station_manager):
    @app.route('/add_station', methods=['POST'])
    def add_station():
        """Add a new station with proper line integration"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            result = station_manager.add_station(data)
            
            # Return appropriate HTTP status based on result
            if result["status"] == "success":
                return jsonify(result), 201
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error adding station: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/delete_station', methods=['POST'])
    def delete_station():
        """Delete a station and update relationships"""
        try:
            data = request.json
            if not data or 'stop_id' not in data or 'year_side' not in data:
                return jsonify({"status": "error", "message": "Missing required fields"}), 400
            
            result = station_manager.delete_station(
                data['stop_id'], 
                data['year_side']
            )
            
            if result["status"] == "success":
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error deleting station: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/save_correction', methods=['POST'])
    def save_correction():
        """Save a station location correction"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            required_fields = ['year_side', 'stop_id', 'lat', 'lng']
            for field in required_fields:
                if field not in data:
                    return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400
            
            result = station_manager.save_location_correction(
                data['year_side'],
                data['stop_id'],
                data['lat'],
                data['lng']
            )
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error saving correction: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/save_name_correction', methods=['POST'])
    def save_name_correction():
        """Save a station name correction"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            required_fields = ['year_side', 'stop_id', 'name']
            for field in required_fields:
                if field not in data:
                    return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400
            
            result = station_manager.save_name_correction(
                data['year_side'],
                data['stop_id'],
                data['name']
            )
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error saving name correction: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/save_source_correction', methods=['POST'])
    def save_source_correction():
        """Save a station source correction"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            if 'stop_id' not in data or 'source' not in data:
                return jsonify({"status": "error", "message": "Missing required fields"}), 400
            
            result = station_manager.save_source_correction(
                data['stop_id'],
                data['source']
            )
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error saving source correction: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/get_line_details/<year_side>/<line_id>')
    def get_line_details(year_side, line_id):
        """Get detailed information about a specific line for station insertion"""
        try:
            result = station_manager.get_line_details(year_side, line_id)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error getting line details: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

# =============================================================================
# VALIDATION ROUTES
# =============================================================================
def register_validation_routes(app, validation_service):
    @app.route('/validate_distances', methods=['POST'])
    def validate_distances():
        """Validate distances between adjacent stations"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            result = validation_service.validate_station_distances(
                data.get('year_side'),
                data.get('line_id')
            )
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error validating distances: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/validate_station_position', methods=['POST'])
    def validate_station_position():
        """Validate a proposed station position"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No data provided"}), 400
            
            result = validation_service.validate_position(
                data.get('year_side'),
                data.get('latitude'),
                data.get('longitude'),
                data.get('line_id')
            )
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error validating position: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

# =============================================================================
# TILE SERVICE ROUTES
# =============================================================================
def register_tile_routes(app, tile_service):
    @app.route('/tiles/<path:filepath>')
    def serve_tile(filepath):
        """Serve a tile from the tiles directory"""
        return tile_service.serve_tile(filepath)

    @app.route('/available_tile_sets')
    def available_tile_sets():
        """List all available tile sets"""
        try:
            tile_sets = tile_service.get_available_tile_sets()
            return jsonify(tile_sets)
        except Exception as e:
            logger.error(f"Error getting tile sets: {e}")
            return jsonify([]), 500

    @app.route('/list_tif_files')
    def list_tif_files():
        """List all TIF files in the tiles/tif directory"""
        try:
            result = tile_service.list_tif_files()
            if "error" in result:
                return jsonify(result), 404
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error listing TIF files: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/process_tif/<filename>', methods=['POST'])
    def process_single_tif(filename):
        """Process a single TIF file"""
        try:
            result = tile_service.process_single_tif(filename)
            if result["status"] == "success":
                return jsonify(result)
            else:
                return jsonify(result), 400
        except Exception as e:
            logger.error(f"Error processing TIF {filename}: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/process_all_tifs', methods=['POST'])
    def process_all_tifs():
        """Process all TIF files in the tif directory"""
        try:
            result = tile_service.process_all_tifs()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error processing all TIFs: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/tile_set_info/<tile_set_name>')
    def get_tile_set_info(tile_set_name):
        """Get detailed information about a tile set"""
        try:
            result = tile_service.get_tile_set_info(tile_set_name)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error getting tile set info: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

# =============================================================================
# ERROR HANDLERS
# =============================================================================
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

# Create the application
app = create_app()
register_error_handlers(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)