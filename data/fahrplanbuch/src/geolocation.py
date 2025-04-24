# geolocation_verification.py

import pandas as pd
import numpy as np
import re
import logging
import folium
from pathlib import Path
from typing import Dict, Union, Optional

logger = logging.getLogger(__name__)

def verify_geo_format(df: pd.DataFrame) -> pd.DataFrame:
    """Verify and standardize geolocation format."""
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Function to check and format location string
    def format_location(loc_str):
        if pd.isna(loc_str) or loc_str == '':
            return np.nan
            
        # Check if it contains multiple locations (with a hyphen)
        if ' - ' in loc_str:
            # This will be handled separately
            return loc_str
            
        # Remove any extra spaces
        loc_str = re.sub(r'\s+', '', loc_str)
        
        # Check if it's a valid coordinate pair
        pattern = r'^(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)$'
        if re.match(pattern, loc_str):
            # Valid format, ensure consistent decimal places
            lat, lon = map(float, loc_str.split(','))
            return f"{lat:.8f},{lon:.8f}"
        else:
            logger.warning(f"Invalid coordinate format: {loc_str}")
            return np.nan
    
    # Apply formatting to location column
    df['location'] = df['location'].apply(format_location)
    
    # Count invalid formats
    invalid_count = df['location'].isna().sum()
    logger.info(f"Found {invalid_count} stations with invalid coordinate format")
    
    return df

def verify_geo_bounds(df: pd.DataFrame, custom_bounds: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Verify coordinates are within expected Berlin bounds.
    
    Args:
        df: DataFrame with stops data
        custom_bounds: Optional dictionary with custom bounds (lat_min, lat_max, lon_min, lon_max)
    
    Returns:
        DataFrame with validation columns added
    """
    # Berlin geographic bounds (approximate)
    BERLIN_BOUNDS = custom_bounds or {
        'lat_min': 52.3,
        'lat_max': 52.7,
        'lon_min': 13.1,
        'lon_max': 13.8
    }
    
    df = df.copy()
    
    def check_bounds(loc_str):
        if pd.isna(loc_str) or loc_str == '':
            return False, "Missing coordinates"
            
        # Multiple locations case
        if ' - ' in loc_str:
            return True, "Multiple coordinates"
            
        try:
            lat, lon = map(float, loc_str.split(','))
            
            if (BERLIN_BOUNDS['lat_min'] <= lat <= BERLIN_BOUNDS['lat_max'] and
                BERLIN_BOUNDS['lon_min'] <= lon <= BERLIN_BOUNDS['lon_max']):
                return True, "Within bounds"
            else:
                return False, f"Outside Berlin bounds: {lat},{lon}"
        except:
            return False, "Invalid format"
    
    # Check bounds for all locations
    results = df['location'].apply(check_bounds)
    df['valid_bounds'] = results.apply(lambda x: x[0])
    df['bounds_message'] = results.apply(lambda x: x[1])
    
    # Log locations outside bounds
    outside_bounds = df[~df['valid_bounds']]
    if not outside_bounds.empty:
        logger.warning(f"Found {len(outside_bounds)} stations outside Berlin bounds:")
        for _, row in outside_bounds.iterrows():
            logger.warning(f"  - {row['stop_name']}: {row['bounds_message']}")

    # Drop the temporary columns if requested
    df.drop(columns=['bounds_message', 'valid_bounds'], inplace=True)
    
    return df

def split_combined_stations(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Split rows where multiple stations are combined with hyphen.
    
    Args:
        df: DataFrame with stops data
        year: Year for generating new stop IDs
        
    Returns:
        Updated DataFrame with split stations
    """
    df = df.copy()
    
    # Find rows with combined stations
    combined_mask = df['location'].apply(lambda x: isinstance(x, str) and ' - ' in x)
    combined_stations = df[combined_mask].copy()
    
    if combined_stations.empty:
        logger.info("No combined stations found")
        return df
        
    logger.info(f"Found {len(combined_stations)} combined stations to split")
    
    # Get the next available stop_id - Make sure all stop_ids are strings for consistency
    df['stop_id'] = df['stop_id'].astype(str)
    
    next_stop_id = int(df['stop_id'].str.replace(r'^\D*', '', regex=True).astype(int).max()) + 1
    
    # Process each combined station
    for idx, row in combined_stations.iterrows():
        # Split station names and locations
        stop_names = row['stop_name'].split(' - ')
        locations = row['location'].split(' - ')
        
        if len(stop_names) != len(locations):
            logger.warning(f"Mismatch between names and locations for {row['stop_name']}")
            continue
        
        # Update the first station in place
        df.at[idx, 'stop_name'] = stop_names[0]
        df.at[idx, 'location'] = locations[0]
        
        # Create new rows for additional stations
        for i in range(1, len(stop_names)):
            new_stop_id = f"{year}{next_stop_id}"
            next_stop_id += 1
            
            # Create new row with same attributes but different name/location
            new_row = row.copy()
            new_row['stop_id'] = new_stop_id
            new_row['stop_name'] = stop_names[i]
            new_row['location'] = locations[i]
            
            # Add to dataframe
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
    return df

def visualize_stations(df: pd.DataFrame, output_path: str):
    """
    Create a folium map with all stations.
    
    Args:
        df: DataFrame with stop data including location column
        output_path: Path where to save the HTML map
        
    Returns:
        Folium map object
    """
    # Filter to only valid locations - properly handle empty strings
    valid_df = df[(df['location'].notna()) & (df['location'] != '')].copy()
    
    # Extract coordinates with better error handling
    def extract_lat(loc_str):
        try:
            if not isinstance(loc_str, str) or loc_str == '':
                return np.nan
            parts = loc_str.split(',')
            if len(parts) != 2:
                return np.nan
            return float(parts[0].strip())
        except (ValueError, IndexError):
            return np.nan
    
    def extract_lon(loc_str):
        try:
            if not isinstance(loc_str, str) or loc_str == '':
                return np.nan
            parts = loc_str.split(',')
            if len(parts) != 2:
                return np.nan
            return float(parts[1].strip())
        except (ValueError, IndexError):
            return np.nan
    
    # Apply coordinate extraction
    valid_df['lat'] = valid_df['location'].apply(extract_lat)
    valid_df['lon'] = valid_df['location'].apply(extract_lon)
    
    # Filter out any rows with invalid coordinates
    valid_df = valid_df[(valid_df['lat'].notna()) & (valid_df['lon'].notna())]
    
    logger.info(f"Creating map with {len(valid_df)} stations")
    
    # Create map centered on Berlin
    m = folium.Map(location=[52.52, 13.40], zoom_start=12)
    
    # Define colors for different transport types
    type_colors = {
        'bus': 'blue',
        'strassenbahn': 'red',
        'u-bahn': 'green',
        's-bahn': 'purple'
    }
    
    # Add markers for each station
    for _, row in valid_df.iterrows():
        popup_text = f"{row['stop_name']} ({row['type']})<br>ID: {row['stop_id']}"
        color = type_colors.get(row['type'].lower(), 'gray')
        
        folium.Marker(
            [row['lat'], row['lon']],
            popup=popup_text,
            icon=folium.Icon(color=color)
        ).add_to(m)
    
    # Save map
    m.save(output_path)
    logger.info(f"Saved map to {output_path}")
    
    return m

def merge_refined_data(original_stops: pd.DataFrame, refined_stops: pd.DataFrame) -> pd.DataFrame:
    """
    Merge refined data with original stops.
    
    Args:
        original_stops: Original stops DataFrame
        refined_stops: Refined stops with updated location data
        
    Returns:
        Merged DataFrame
    """
    merged_stops = original_stops.copy()
    
    for idx, row in refined_stops.iterrows():
        stop_name = row['stop_name']
        stop_type = row['type']
        line_name = row['line_name']
        
        # Check if this stop exists in the original stops
        match = merged_stops[(merged_stops['stop_name'] == stop_name) & 
                            (merged_stops['type'] == stop_type) & 
                            (merged_stops['line_name'] == line_name)]
        
        if not match.empty:
            # Update location and identifier if match is found
            merged_idx = match.index[0]
            merged_stops.at[merged_idx, 'location'] = row['location']
            if 'identifier' in row and not pd.isna(row['identifier']):
                merged_stops.at[merged_idx, 'identifier'] = row['identifier']
        else:
            # This is a new stop, add to merged_stops
            merged_stops = pd.concat([merged_stops, pd.DataFrame([row])], ignore_index=True)
    
    return merged_stops

def process_geolocation_verification(year: int, side: str, data_dir: Union[str, Path]) -> pd.DataFrame:
    """
    Main function to run the entire geolocation verification process.
    
    Args:
        year: Year of data to process
        side: 'east' or 'west'
        data_dir: Base data directory
        
    Returns:
        DataFrame with verified stations
    """
    data_dir = Path(data_dir)
    
    # Load refined data from OpenRefine
    refined_data_path = data_dir / 'interim' / 'stops_for_openrefine' / f'unmatched_stops_{year}_{side}_refined.csv'
    refined_stops = pd.read_csv(refined_data_path)
    logger.info(f"Loaded {len(refined_stops)} stations from OpenRefine")
    
    # Load original stops data
    original_stops = pd.read_csv(data_dir / 'interim' / 'stops_matched_initial' / f'stops_{year}_{side}.csv')
    logger.info(f"Loaded {len(original_stops)} stations from original data")
    
    # Step 1: Split combined stations
    refined_stops = split_combined_stations(refined_stops, year)
    
    # Step 2: Merge refined data with original stops
    merged_stops = merge_refined_data(original_stops, refined_stops)
    
    # Step 3: Verify geo format
    merged_stops = verify_geo_format(merged_stops)
    
    # Step 4: Verify bounds
    merged_stops = verify_geo_bounds(merged_stops)
    
    # Step 5: Create visualization
    map_dir = data_dir / 'visualizations'
    map_dir.mkdir(parents=True, exist_ok=True)
    visualize_stations(merged_stops, str(map_dir / f'stations_{year}_{side}.html'))
    
    # Save verified data
    verified_dir = data_dir / 'interim' / 'stops_verified'
    verified_dir.mkdir(parents=True, exist_ok=True)
    
    verified_path = verified_dir / f'stops_{year}_{side}.csv'
    merged_stops.to_csv(verified_path, index=False)
    logger.info(f"Saved verified stops to {verified_path}")
    
    # Print summary
    valid_locations = merged_stops['location'].notna().sum()
    total_stops = len(merged_stops)
    logger.info(f"Verification complete:")
    logger.info(f"Total stations: {total_stops}")
    logger.info(f"Valid locations: {valid_locations} ({valid_locations/total_stops*100:.1f}%)")
    logger.info(f"Split stations: {len(merged_stops) - len(original_stops)}")
    
    return merged_stops

# If run as script
if __name__ == "__main__":
    import argparse
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Verify and process geolocation data")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument("--side", type=str, required=True, choices=["east", "west"], 
                       help="Side of Berlin (east/west)")
    parser.add_argument("--data-dir", type=str, default="../data", 
                       help="Base data directory path")
    
    args = parser.parse_args()
    
    # Run processing
    process_geolocation_verification(args.year, args.side, args.data_dir)