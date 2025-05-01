import os
import sys
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pathlib import Path
import mercantile
from PIL import Image
import numpy as np
from pyproj import Transformer

def generate_xyz_tiles_rasterio(tiff_file, output_dir, min_zoom=10, max_zoom=16):
    """Generate XYZ tiles using Rasterio for georeferenced images"""
    try:
        tiff_file = Path(tiff_file).resolve()
        output_dir = Path(output_dir).resolve()
        
        print(f"Processing file: {tiff_file}")
        print(f"Output directory: {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Open the source dataset
        with rasterio.open(tiff_file) as src:
            # Check if the source has a valid CRS
            if src.crs is None:
                print("Error: Image is not georeferenced. Please georeference the image first.")
                return False
            
            # Get the bounds
            bounds = src.bounds
            west, south, east, north = bounds
            
            print(f"Source image bounds (original CRS): {bounds}")
            print(f"Source image CRS: {src.crs}")
            
            # Convert bounds to WGS84 (EPSG:4326) for mercantile
            if src.crs.to_epsg() != 4326:
                transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
                west_lng, south_lat = transformer.transform(west, south)
                east_lng, north_lat = transformer.transform(east, north)
                print(f"Converted bounds to WGS84: {west_lng}, {south_lat}, {east_lng}, {north_lat}")
            else:
                west_lng, south_lat, east_lng, north_lat = west, south, east, north
                
 
            # Calculate the actual tiles that would contain our image
            for zoom in range(min_zoom, max_zoom + 1):
                # Find all tiles that intersect with the bounds at this zoom level using WGS84 coordinates
                tiles = list(mercantile.tiles(west_lng, south_lat, east_lng, north_lat, zoom))
                
                # Process each tile
                success_count = 0
                error_count = 0
                
                for tile in tiles:
                    # Create directory for this tile
                    tile_dir = output_dir / str(zoom) / str(tile.x)
                    os.makedirs(tile_dir, exist_ok=True)
                    tile_path = tile_dir / f"{tile.y}.png"
                    
                    if tile_path.exists():
                        continue  # Skip if already exists
                    
                    # Get the bounds of this tile in the original CRS of the image
                    # First get the bounds in WGS84
                    tile_bounds_wgs84 = mercantile.bounds(tile)
                    
                    # Then transform back to the image's CRS
                    if src.crs.to_epsg() != 4326:
                        transformer_back = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                        tile_left, tile_bottom = transformer_back.transform(tile_bounds_wgs84.west, tile_bounds_wgs84.south)
                        tile_right, tile_top = transformer_back.transform(tile_bounds_wgs84.east, tile_bounds_wgs84.north)
                    else:
                        tile_left, tile_bottom = tile_bounds_wgs84.west, tile_bounds_wgs84.south
                        tile_right, tile_top = tile_bounds_wgs84.east, tile_bounds_wgs84.north
                    
                    try:
                        # Calculate window in pixel coordinates
                        window = src.window(tile_left, tile_bottom, tile_right, tile_top)
                        
                        # Ensure window is within image bounds
                        from rasterio.windows import Window
                        row_start = max(0, int(window.row_off))
                        row_stop = min(src.height, int(window.row_off + window.height))
                        col_start = max(0, int(window.col_off))
                        col_stop = min(src.width, int(window.col_off + window.width))
                        
                        # Skip if window is empty
                        if row_stop <= row_start or col_stop <= col_start:
                            continue
                        
                        # Create a safe window
                        safe_window = Window(col_start, row_start, col_stop - col_start, row_stop - row_start)
                        
                        # Read data for this window
                        data = src.read(
                            window=safe_window,
                            out_shape=(src.count, 256, 256),
                            resampling=Resampling.bilinear
                        )
                        
                        # Create a PIL image
                        if src.count == 1:
                            # For grayscale images
                            image_data = data[0]
                            mode = "L"
                        elif src.count == 3:
                            # For RGB images
                            image_data = np.transpose(data, (1, 2, 0))
                            mode = "RGB"
                        elif src.count == 4:
                            # For RGBA images
                            image_data = np.transpose(data, (1, 2, 0))
                            mode = "RGBA"
                        else:
                            # Use the first band for other cases
                            image_data = data[0]
                            mode = "L"
                        
                        # Normalize data for PIL (values between 0-255)
                        if image_data.dtype != np.uint8:
                            # Check if we have valid data
                            if np.all(np.isnan(image_data)) or image_data.min() == image_data.max():
                                image_data = np.zeros_like(image_data, dtype=np.uint8)
                            else:
                                image_data = ((image_data - image_data.min()) / 
                                             (image_data.max() - image_data.min()) * 255).astype(np.uint8)
                        
                        # Create and save the image
                        image = Image.fromarray(image_data, mode=mode)
                        image.save(tile_path)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        # Only log the first few errors to avoid spamming
                        if error_count <= 3:
                            print(f"  Error processing tile {tile.x}/{tile.y}/{zoom}: {e}")
                
                print(f"  Zoom level {zoom}: {success_count} tiles created, {error_count} errors")
            
            return True
            
    except Exception as e:
        print(f"Error generating tiles: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_tif_directory(base_dir, output_base_dir, min_zoom=10, max_zoom=16):
    """Process all TIF files in a directory structure"""
    base_dir = Path(base_dir)
    output_base_dir = Path(output_base_dir)
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return {}
    
    results = {}
    
    # Look for TIF files in the specified directory
    tif_files = list(base_dir.glob("*.tif")) + list(base_dir.glob("*.tiff"))
    
    if not tif_files:
        print(f"No TIF files found in {base_dir}")
        return {}
    
    print(f"Found {len(tif_files)} TIF files to process")
    
    for tif_file in tif_files:
        # Use the TIF filename (without extension) as the output directory name
        output_name = tif_file.stem
        output_dir = output_base_dir / output_name
        
        success = generate_xyz_tiles_rasterio(
            tiff_file=tif_file,
            output_dir=output_dir,
            min_zoom=min_zoom,
            max_zoom=max_zoom
        )
        
        results[str(tif_file)] = {
            "success": success,
            "output_dir": str(output_dir),
            "url_path": f"{output_name}/{{z}}/{{x}}/{{y}}.png"
        }
    
    return results