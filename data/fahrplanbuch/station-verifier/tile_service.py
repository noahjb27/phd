# tile_service.py
import os
import logging
from pathlib import Path
from flask import send_from_directory

logger = logging.getLogger(__name__)

class TileService:
    def __init__(self, config):
        self.config = config
        self.tiles_dir = config['TILES_DIR']
        self.tif_dir = self.tiles_dir / "tif"
        
        # Ensure directories exist
        self.tiles_dir.mkdir(exist_ok=True)
        self.tif_dir.mkdir(exist_ok=True)
        
        logger.info(f"TileService initialized - tiles_dir: {self.tiles_dir}, tif_dir: {self.tif_dir}")
    
    def serve_tile(self, filepath):
        """Serve a tile from the tiles directory"""
        try:
            return send_from_directory(str(self.tiles_dir), filepath)
        except Exception as e:
            logger.error(f"Error serving tile {filepath}: {e}")
            return {"error": "Tile not found"}, 404
    
    def get_available_tile_sets(self):
        """List all available tile sets"""
        if not self.tiles_dir.exists():
            logger.warning(f"Tiles directory does not exist: {self.tiles_dir}")
            return []
        
        tile_sets = []
        
        try:
            for item in os.listdir(self.tiles_dir):
                item_path = self.tiles_dir / item
                
                # Skip the TIF source files directory and individual files
                if item.endswith(('.tif', '.tiff')) or item == "tif":
                    continue
                    
                if item_path.is_dir():
                    # Check if this directory contains zoom level subdirectories
                    try:
                        zoom_dirs = [d for d in os.listdir(item_path) 
                                   if d.isdigit() and (item_path / d).is_dir()]
                        
                        if zoom_dirs:
                            # Verify that zoom directories contain tile files
                            has_tiles = False
                            for zoom_dir in zoom_dirs[:3]:  # Check first few zoom levels
                                zoom_path = item_path / zoom_dir
                                if any((zoom_path / x_dir).is_dir() for x_dir in os.listdir(zoom_path) 
                                      if x_dir.isdigit()):
                                    has_tiles = True
                                    break
                            
                            if has_tiles:
                                tile_sets.append({
                                    "name": item,
                                    "url": f"/tiles/{item}/{{z}}/{{x}}/{{y}}.png",
                                    "zoom_levels": sorted([int(z) for z in zoom_dirs])
                                })
                                logger.debug(f"Found tile set: {item} with zoom levels {zoom_dirs}")
                    except Exception as e:
                        logger.warning(f"Error processing tile directory {item}: {e}")
                        continue
            
            logger.info(f"Found {len(tile_sets)} available tile sets")
            return tile_sets
            
        except Exception as e:
            logger.error(f"Error listing tile sets: {e}")
            return []
    
    def list_tif_files(self):
        """List all TIF files in the tif directory"""
        if not self.tif_dir.exists():
            logger.warning(f"TIF directory does not exist: {self.tif_dir}")
            return {"error": "TIF directory not found"}
        
        try:
            tif_files = []
            for item in os.listdir(self.tif_dir):
                if item.lower().endswith(('.tif', '.tiff')):
                    file_path = self.tif_dir / item
                    file_size = file_path.stat().st_size
                    tif_files.append({
                        "name": item,
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
            
            tif_files.sort(key=lambda x: x['name'])
            
            logger.info(f"Found {len(tif_files)} TIF files")
            return {"tif_files": tif_files}
            
        except Exception as e:
            logger.error(f"Error listing TIF files: {e}")
            return {"error": f"Error listing TIF files: {str(e)}"}
    
    def process_single_tif(self, filename):
        """Process a single TIF file into tiles"""
        try:
            from rasterio_tile_generator import generate_xyz_tiles_rasterio
            
            tif_path = self.tif_dir / filename
            
            if not tif_path.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
            
            # Validate file size (optional - prevent processing huge files)
            file_size = tif_path.stat().st_size
            max_size = 500 * 1024 * 1024  # 500 MB limit
            
            if file_size > max_size:
                return {
                    "status": "error",
                    "message": f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size / (1024*1024):.1f}MB)"
                }
            
            output_dir = self.tiles_dir / tif_path.stem
            
            logger.info(f"Processing TIF file: {filename} -> {output_dir}")
            
            success = generate_xyz_tiles_rasterio(
                tiff_file=tif_path,
                output_dir=output_dir,
                min_zoom=10,
                max_zoom=16
            )
            
            if success:
                logger.info(f"Successfully processed {filename}")
                return {
                    "status": "success",
                    "message": f"Tiles generated for {filename}",
                    "url": f"/tiles/{tif_path.stem}/{{z}}/{{x}}/{{y}}.png",
                    "output_dir": str(output_dir)
                }
            else:
                logger.error(f"Failed to process {filename}")
                return {"status": "error", "message": "Failed to generate tiles"}
                
        except ImportError:
            logger.error("rasterio_tile_generator module not found")
            return {"status": "error", "message": "Tile generation module not available"}
        except Exception as e:
            logger.error(f"Error processing TIF file {filename}: {e}")
            return {"status": "error", "message": f"Processing error: {str(e)}"}
    
    def process_all_tifs(self):
        """Process all TIF files in the tif directory"""
        try:
            from rasterio_tile_generator import process_tif_directory
            
            # Check if TIF directory exists and has files
            if not self.tif_dir.exists():
                return {
                    "status": "error",
                    "message": "TIF directory does not exist. Please create it and add TIF files."
                }
            
            tif_files = [f for f in os.listdir(self.tif_dir) 
                        if f.lower().endswith(('.tif', '.tiff'))]
            
            if not tif_files:
                return {
                    "status": "error",
                    "message": "No TIF files found in the tiles/tif directory. Please add TIF files first."
                }
            
            logger.info(f"Processing {len(tif_files)} TIF files: {tif_files}")
            
            # Calculate total file size for progress estimation
            total_size = sum((self.tif_dir / f).stat().st_size for f in tif_files)
            total_size_mb = total_size / (1024 * 1024)
            
            logger.info(f"Total file size to process: {total_size_mb:.1f} MB")
            
            results = process_tif_directory(
                base_dir=self.tif_dir,
                output_base_dir=self.tiles_dir,
                min_zoom=10,
                max_zoom=16
            )
            
            success_count = sum(1 for result in results.values() if result["success"])
            failed_count = len(results) - success_count
            
            logger.info(f"Processing complete: {success_count} succeeded, {failed_count} failed")
            
            return {
                "status": "success",
                "message": f"Processed {len(results)} files. {success_count} succeeded, {failed_count} failed.",
                "details": results,
                "summary": {
                    "total_files": len(results),
                    "successful": success_count,
                    "failed": failed_count,
                    "total_size_mb": total_size_mb
                }
            }
            
        except ImportError:
            logger.error("rasterio_tile_generator module not found")
            return {
                "status": "error",
                "message": "Tile generation module not available. Please ensure rasterio_tile_generator.py is present."
            }
        except Exception as e:
            logger.error(f"Error processing all TIFs: {e}")
            return {"status": "error", "message": f"Processing error: {str(e)}"}
    
    def cleanup_tiles(self, tile_set_name=None):
        """Clean up generated tiles (for maintenance)"""
        try:
            if tile_set_name:
                # Clean up specific tile set
                tile_set_path = self.tiles_dir / tile_set_name
                if tile_set_path.exists() and tile_set_path.is_dir():
                    import shutil
                    shutil.rmtree(tile_set_path)
                    logger.info(f"Cleaned up tile set: {tile_set_name}")
                    return {"status": "success", "message": f"Cleaned up tile set: {tile_set_name}"}
                else:
                    return {"status": "error", "message": f"Tile set not found: {tile_set_name}"}
            else:
                # Clean up all generated tiles (keep TIF source files)
                for item in os.listdir(self.tiles_dir):
                    item_path = self.tiles_dir / item
                    if item_path.is_dir() and item != "tif":
                        import shutil
                        shutil.rmtree(item_path)
                        logger.info(f"Cleaned up tile directory: {item}")
                
                return {"status": "success", "message": "Cleaned up all generated tiles"}
                
        except Exception as e:
            logger.error(f"Error cleaning up tiles: {e}")
            return {"status": "error", "message": f"Cleanup error: {str(e)}"}
    
    def get_tile_set_info(self, tile_set_name):
        """Get detailed information about a specific tile set"""
        try:
            tile_set_path = self.tiles_dir / tile_set_name
            
            if not tile_set_path.exists():
                return {"status": "error", "message": f"Tile set not found: {tile_set_name}"}
            
            info = {
                "name": tile_set_name,
                "path": str(tile_set_path),
                "zoom_levels": [],
                "total_tiles": 0,
                "total_size": 0
            }
            
            # Analyze zoom levels
            for item in os.listdir(tile_set_path):
                if item.isdigit() and (tile_set_path / item).is_dir():
                    zoom_level = int(item)
                    zoom_path = tile_set_path / item
                    
                    # Count tiles in this zoom level
                    tile_count = 0
                    total_size = 0
                    
                    for x_dir in os.listdir(zoom_path):
                        x_path = zoom_path / x_dir
                        if x_path.is_dir():
                            for y_file in os.listdir(x_path):
                                if y_file.endswith('.png'):
                                    tile_count += 1
                                    total_size += (x_path / y_file).stat().st_size
                    
                    info["zoom_levels"].append({
                        "zoom": zoom_level,
                        "tiles": tile_count,
                        "size_mb": round(total_size / (1024 * 1024), 2)
                    })
                    
                    info["total_tiles"] += tile_count
                    info["total_size"] += total_size
            
            info["zoom_levels"].sort(key=lambda x: x["zoom"])
            info["total_size_mb"] = round(info["total_size"] / (1024 * 1024), 2)
            
            return {"status": "success", "info": info}
            
        except Exception as e:
            logger.error(f"Error getting tile set info for {tile_set_name}: {e}")
            return {"status": "error", "message": str(e)}