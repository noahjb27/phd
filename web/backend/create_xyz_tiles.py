import os
import subprocess
from osgeo import gdal

def create_xyz_tiles(input_tiff, output_dir, min_zoom=8, max_zoom=16):
    """
    Convert a TIFF file to XYZ tiles using GDAL
    
    Parameters:
    -----------
    input_tiff : str
        Path to input TIFF file
    output_dir : str
        Path to output directory for tiles
    min_zoom : int
        Minimum zoom level
    max_zoom : int
        Maximum zoom level
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if the TIFF is in Web Mercator (EPSG:3857)
    ds = gdal.Open(input_tiff)
    proj = ds.GetProjection()
    ds = None
    
    # If not in Web Mercator, reproject it
    if "EPSG:3857" not in proj and "3857" not in proj:
        print("Reprojecting to Web Mercator (EPSG:3857)...")
        reprojected_tiff = input_tiff.replace('.tif', '_3857.tif')
        subprocess.run([
            'gdalwarp', 
            '-s_srs', 'EPSG:4326',  # Assuming original is in WGS84, adjust if needed
            '-t_srs', 'EPSG:3857',
            input_tiff, 
            reprojected_tiff
        ])
        input_tiff = reprojected_tiff
    
    # Generate XYZ tiles
    print(f"Generating tiles from zoom level {min_zoom} to {max_zoom}...")
    subprocess.run([
        'gdal2tiles.py',
        '-z', f"{min_zoom}-{max_zoom}",
        '-w', 'none',
        '--processes=4',  # Use multiple CPU cores
        '--xyz',  # Ensure XYZ format (not TMS)
        input_tiff,
        output_dir
    ])
    
    print(f"Tiles generated in {output_dir}")

# Example usage
if __name__ == "__main__":
    create_xyz_tiles(
        input_tiff="berlin_1960.tiff", 
        output_dir="/var/www/tiles/berlin_1960",
        min_zoom=10,
        max_zoom=18
    )