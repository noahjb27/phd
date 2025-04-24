#!/usr/bin/env python
"""
Script to normalize side names in Berlin transport data files.
Renames files with 'ost' to 'east' and 'west' to 'west'.
"""

import os
from pathlib import Path
import shutil
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(".")  # Adjust to your project base directory
SIDE_MAPPING = {
    "ost": "east",
    "west": "west",
    "ost ": "east",  # Handle cases with extra space
    "west ": "west"  # Handle cases with extra space
}

def normalize_filenames(directory):
    """
    Normalize filenames in the given directory by replacing German side names with English ones.
    
    Args:
        directory: Path to the directory to process
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return 0
    
    count = 0
    # Find files matching the pattern year_side.csv
    pattern = re.compile(r'(.+_)(ost|west)(\s*)(.csv)')
    
    for file_path in directory.glob("*.*"):
        match = pattern.search(file_path.name)
        if match:
            prefix, side, space, extension = match.groups()
            normalized_side = SIDE_MAPPING.get(side + space, side)
            new_filename = f"{prefix}{normalized_side}{extension}"
            new_path = file_path.parent / new_filename
            
            # Rename the file
            if file_path != new_path:
                try:
                    shutil.move(str(file_path), str(new_path))
                    logger.info(f"Renamed: {file_path.name} -> {new_filename}")
                    count += 1
                except Exception as e:
                    logger.error(f"Error renaming {file_path.name}: {e}")
    
    return count

def process_directories():
    """Process all relevant directories to normalize side names."""
    # Directories to process
    directories = [
        BASE_DIR / "data" / "interim" / "stops_matched_initial",
        BASE_DIR / "data" / "interim" / "stops_verified",
        BASE_DIR / "data" / "interim" / "stops_for_openrefine",
        BASE_DIR / "data" / "interim" / "stops_base",
        BASE_DIR / "data" / "processed"
    ]
    
    total_renamed = 0
    for directory in directories:
        logger.info(f"Processing directory: {directory}")
        renamed = normalize_filenames(directory)
        total_renamed += renamed
        
        # Also process subdirectories (especially for processed)
        for subdir in directory.glob("*"):
            if subdir.is_dir():
                logger.info(f"Processing subdirectory: {subdir}")
                renamed = normalize_filenames(subdir)
                total_renamed += renamed
    
    return total_renamed

def clean_empty_directories():
    """Remove empty processed subdirectories."""
    processed_dir = BASE_DIR / "data" / "processed"
    if not processed_dir.exists():
        return 0
    
    count = 0
    # Find year_side directories
    pattern = re.compile(r'\d{4}_(ost|west)(\s*)')
    
    for subdir in processed_dir.glob("*"):
        if subdir.is_dir():
            match = pattern.match(subdir.name)
            if match:
                # Check if directory is empty
                if not any(subdir.iterdir()):
                    try:
                        subdir.rmdir()
                        logger.info(f"Removed empty directory: {subdir}")
                        count += 1
                    except Exception as e:
                        logger.error(f"Error removing directory {subdir}: {e}")
    
    return count

def main():
    """Main function to normalize side names in Berlin transport data files."""
    logger.info("Starting side name normalization")
    
    # Process all directories
    total_renamed = process_directories()
    logger.info(f"Total files renamed: {total_renamed}")
    
    # Clean up empty directories
    removed = clean_empty_directories()
    logger.info(f"Removed {removed} empty directories")
    
    logger.info("""
Normalization complete! Next steps:

1. Run the geolocation verification notebook for each year/side:
   - Open 01_geolocation_verification_splitting.ipynb
   - Set YEAR = [year] and SIDE = "east" or "west"
   - Run all cells

2. Run the enrichment notebook for each year/side:
   - Open 02_enrichment.ipynb
   - Set YEAR = [year] and SIDE = "east" or "west"
   - Run all cells

3. The processed directories will be populated after running these notebooks
""")

if __name__ == "__main__":
    main()