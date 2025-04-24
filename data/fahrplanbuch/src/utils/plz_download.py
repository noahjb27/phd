# save_postal_codes.py
import requests
import geojson
import geopandas as gpd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_and_save_postal_codes(output_path):
    """
    Fetch postal code data from Berlin's WFS service and save it to a GeoJSON file.
    
    Args:
        output_path: Path where to save the GeoJSON file
    
    Returns:
        Path to the saved file if successful, None otherwise
    """
    try:
        logger.info("Fetching postal code data from WFS service...")
        
        # Specify the URL for the Berlin WFS service
        url = "https://gdi.berlin.de/services/wfs/postleitzahlen"
        
        # Specify WFS parameters
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": "postleitzahlen",
            "outputFormat": "json"
        }
        
        # Make the request
        response = requests.get(url, params=params, timeout=30)
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"WFS request failed with status code {response.status_code}")
            return None
            
        # Parse the GeoJSON response
        try:
            geo_data = geojson.loads(response.content)
        except Exception as e:
            logger.error(f"Failed to parse GeoJSON response: {e}")
            return None
            
        # Create GeoDataFrame from geojson and set coordinate reference system
        plz_gdf = gpd.GeoDataFrame.from_features(geo_data, crs="EPSG:25833")
        
        # Reproject to WGS84 (EPSG:4326) for consistency with other data
        plz_gdf = plz_gdf.to_crs(epsg=4326)
        
        # Save to GeoJSON file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as GeoJSON
        plz_gdf.to_file(output_path, driver='GeoJSON')
        
        logger.info(f"Successfully saved postal code data to {output_path}")
        logger.info(f"Retrieved {len(plz_gdf)} postal code areas")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error fetching and saving postal code data: {e}")
        return None

if __name__ == "__main__":
    # Define output path
    output_file = Path("../data/geo_data/berlin_postal_codes.geojson")
    
    # Fetch and save data
    fetch_and_save_postal_codes(output_file)