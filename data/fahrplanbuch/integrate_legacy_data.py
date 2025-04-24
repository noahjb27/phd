#!/usr/bin/env python
"""
Enhanced script to integrate legacy CSV data into the Berlin transport workflow
with proper handling of Berlin's historical division and better column management.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(".")  # Adjust this to your project base directory
BERLIN_DIVISION_YEAR = 1961  # Now 1961 is treated as divided (east/west), not unified

# Directory structure
DIRS = {
    "raw": BASE_DIR / "data" / "raw",
    "interim_matched": BASE_DIR / "data" / "interim" / "stops_matched_initial",
    "interim_verified": BASE_DIR / "data" / "interim" / "stops_verified",
    "interim_openrefine": BASE_DIR / "data" / "interim" / "stops_for_openrefine",
    "interim_base": BASE_DIR / "data" / "interim" / "stops_base",
    "processed": BASE_DIR / "data" / "processed"
}

# Define the expected column names and order for each DataFrame type based on sample files
EXPECTED_COLUMNS = {
    "stations": [
        "stop_name", "type", "line_name", "stop_id", "location", "identifier", 
        "neighbourhood", "district", "east_west", "postal_code"
    ],
    "lines": [
        "line_id", "year", "line_name", "type", "start_stop", "length (time)", 
        "length (km)", "east_west", "frequency (7:30)", "profile", "capacity"
    ],
    "line_stops": ["stop_order", "stop_id", "line_id"]
}

# Column mapping from legacy to new format
COLUMN_MAPPING = {
    "stations": {
        "stop_description": "description",  # Example mapping
        "Unnamed: 0": None,  # Remove column
        "in_lines": None  # Remove column as it's not in the processed format
    },
    "lines": {
        "Length (time)": "length (time)",
        "Length (km)": "length (km)",
        "Frequency": "frequency (7:30)",
        "Unnamed: 0": None  # Remove column
    },
    "line_stops": {
        "Unnamed: 0": None  # Remove column
    }
}

def create_directories():
    """Create necessary directories if they don't exist."""
    for dir_path in DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def extract_year_from_id(id_str):
    """Extract year from ID (first 4 digits)."""
    match = re.match(r'^(\d{4})', str(id_str))
    if match:
        return int(match.group(1))
    return None

def determine_side(row, division_year=BERLIN_DIVISION_YEAR):
    """
    Determine east/west side from row data.
    
    Args:
        row: DataFrame row
        division_year: Year when Berlin was divided (1961 when Wall was built)
        
    Returns:
        'east' or 'west' based on data
    """
    # Extract year from row
    year = None
    if 'year' in row and pd.notna(row['year']):
        year = int(row['year'])
    else:
        # Try to extract from stop_id or line_id
        for id_field in ['stop_id', 'line_id']:
            if id_field in row and pd.notna(row[id_field]):
                extracted_year = extract_year_from_id(row[id_field])
                if extracted_year:
                    year = extracted_year
                    break
    
    # If year is before division (strictly before 1961), use 'unified'
    # and we'll handle the split later
    if year and year < division_year:
        # For simplicity, we'll default pre-division stations to 'both'
        # so they can be processed both as east and west
        return 'both'  
    
    # After division, determine east/west
    if 'east_west' in row and pd.notna(row['east_west']):
        side = row['east_west'].lower()
        if side == 'both/unkown' or side == 'both/unknown' or side == 'both':
            # For post-division "both" values, default to both
            # (will process as both east and west)
            return 'both'
        if 'east' in side:
            return 'east'
        if 'west' in side:
            return 'west'
        return side
    
    # Default value for post-division is both (will be processed as both east and west)
    return 'both'

def load_combined_data(stations_path, lines_path, line_stops_path):
    """Load the combined CSV data files."""
    stations_df = pd.read_csv(stations_path)
    lines_df = pd.read_csv(lines_path)
    line_stops_df = pd.read_csv(line_stops_path)
    
    logger.info(f"Loaded {len(stations_df)} stations, {len(lines_df)} lines, and {len(line_stops_df)} line-stop relations")
    return stations_df, lines_df, line_stops_df

def standardize_dataframe(df, df_type, keep_year_and_side=False):
    """
    Standardize DataFrame columns according to the new workflow.
    
    Args:
        df: DataFrame to standardize
        df_type: Type of DataFrame ('stations', 'lines', or 'line_stops')
        keep_year_and_side: Whether to keep 'year' and 'side' columns
        
    Returns:
        Standardized DataFrame
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # 1. Rename columns according to mapping
    if df_type in COLUMN_MAPPING:
        # Create a mapping of only the columns that actually exist in the DataFrame
        existing_cols = {k: v for k, v in COLUMN_MAPPING[df_type].items() if k in result_df.columns}
        # Remove columns marked with None
        cols_to_drop = [k for k, v in existing_cols.items() if v is None]
        result_df.drop(columns=cols_to_drop, errors='ignore', inplace=True)
        # Rename remaining columns
        rename_map = {k: v for k, v in existing_cols.items() if v is not None}
        result_df.rename(columns=rename_map, inplace=True)
    
    # 2. Ensure all expected columns exist
    if df_type in EXPECTED_COLUMNS:
        # Add expected columns that don't exist
        for col in EXPECTED_COLUMNS[df_type]:
            if col not in result_df.columns:
                result_df[col] = None
                logger.info(f"Added missing column '{col}' to {df_type} DataFrame")
    
    # 3. Create a list of columns to keep, including expected columns and helper columns
    columns_to_keep = list(EXPECTED_COLUMNS[df_type])
    if keep_year_and_side:
        if 'year' in result_df.columns and 'year' not in columns_to_keep:
            columns_to_keep.append('year')
        if 'side' in result_df.columns and 'side' not in columns_to_keep:
            columns_to_keep.append('side')
    
    # 4. Keep only the specified columns
    extra_cols = [col for col in result_df.columns if col not in columns_to_keep]
    if extra_cols:
        logger.info(f"Removing extra columns from {df_type} DataFrame: {extra_cols}")
        result_df = result_df[columns_to_keep]
    
    # 5. Reorder columns without helper columns
    if df_type in EXPECTED_COLUMNS:
        # Only include expected columns that exist in our DataFrame
        ordered_cols = [col for col in EXPECTED_COLUMNS[df_type] if col in result_df.columns]
        
        # Add helper columns to the end if keeping them
        if keep_year_and_side:
            helper_cols = []
            if 'year' in result_df.columns and 'year' not in ordered_cols:
                helper_cols.append('year')
            if 'side' in result_df.columns and 'side' not in ordered_cols:
                helper_cols.append('side')
            ordered_cols = ordered_cols + helper_cols
        
        # Reorder the columns
        result_df = result_df[ordered_cols]
    
    return result_df

def prepare_stations_for_split(stations_df):
    """Prepare stations DataFrame for splitting by year and side."""
    # Extract year from stop_id
    stations_df['year'] = stations_df['stop_id'].apply(extract_year_from_id)
    
    # Determine side for stations with historical accuracy
    stations_df['side'] = stations_df.apply(determine_side, axis=1)
    
    # Standardize DataFrame - keep 'year' and 'side' for processing
    stations_df = standardize_dataframe(stations_df, 'stations', keep_year_and_side=True)
    
    return stations_df

def prepare_lines_for_split(lines_df):
    """Prepare lines DataFrame for splitting by year and side."""
    # Determine side with historical accuracy
    lines_df['side'] = lines_df.apply(determine_side, axis=1)
    
    # Standardize DataFrame - keep 'side' for processing
    lines_df = standardize_dataframe(lines_df, 'lines', keep_year_and_side=True)
    
    return lines_df

def prepare_line_stops_for_split(line_stops_df, lines_df):
    """Prepare line_stops DataFrame for splitting by year and side."""
    # Extract year from line_id
    line_stops_df['year'] = line_stops_df['line_id'].apply(extract_year_from_id)
    
    # Create a mapping of line_id to side
    line_side_map = {}
    for _, row in lines_df.iterrows():
        if pd.notna(row.get('line_id')):
            line_side_map[row['line_id']] = row.get('side', 'both')
    
    # Determine side for line_stops using the mapping
    line_stops_df['side'] = line_stops_df['line_id'].map(line_side_map)
    
    # Default value depends on year
    def default_side(row):
        year = extract_year_from_id(row.get('line_id'))
        # Default to both for pre-division
        return 'both' if year and year < BERLIN_DIVISION_YEAR else 'both'
    
    # Fill missing side values
    line_stops_df['side'] = line_stops_df.apply(
        lambda row: row['side'] if pd.notna(row.get('side')) else default_side(row), 
        axis=1
    )
    
    # Standardize DataFrame
    line_stops_df = standardize_dataframe(line_stops_df, 'line_stops', keep_year_and_side=True)
    
    return line_stops_df

def expand_both_sides(df):
    """
    Expand rows with 'both' side into separate rows for 'east' and 'west'.
    
    Args:
        df: DataFrame with 'side' column
    
    Returns:
        DataFrame with 'both' rows duplicated as 'east' and 'west'
    """
    # Make a copy of the DataFrame
    result_df = df.copy()
    
    # Find rows with 'both' side
    both_mask = result_df['side'] == 'both'
    both_rows = result_df[both_mask].copy()
    
    # Skip if no 'both' rows
    if both_rows.empty:
        return result_df
    
    # Create east copies
    east_rows = both_rows.copy()
    east_rows['side'] = 'east'
    
    # Create west copies
    west_rows = both_rows.copy()
    west_rows['side'] = 'west'
    
    # Remove original 'both' rows
    result_df = result_df[~both_mask]
    
    # Concatenate with east and west copies
    result_df = pd.concat([result_df, east_rows, west_rows], ignore_index=True)
    
    return result_df

def split_and_save_data(stations_df, lines_df, line_stops_df):
    """Split data by year and side and save to appropriate locations."""
    # Expand 'both' sides to 'east' and 'west'
    stations_df = expand_both_sides(stations_df)
    lines_df = expand_both_sides(lines_df)
    line_stops_df = expand_both_sides(line_stops_df)
    
    # Get unique years and sides
    years = set(stations_df['year'].dropna().unique()) | set(lines_df['year'].dropna().unique())
    years = sorted([int(y) for y in years if pd.notna(y)])
    
    logger.info(f"Splitting data for years: {years}")
    logger.info(f"Sides after expansion: {stations_df['side'].unique()}")
    
    for year in years:
        # Filter data for this year
        year_stations = stations_df[stations_df['year'] == year]
        year_lines = lines_df[lines_df['year'] == year]
        year_line_stops = line_stops_df[line_stops_df['year'] == year]
        
        # Get unique sides for this year
        sides = set(year_stations['side'].dropna().unique()) | set(year_lines['side'].dropna().unique())
        sides = [s for s in sides if pd.notna(s) and s != 'both']  # Exclude 'both'
        
        for side in sides:
            logger.info(f"Processing year {year}, side {side}")
            
            # Filter data for this side
            side_stations = year_stations[year_stations['side'] == side]
            side_lines = year_lines[year_lines['side'] == side]
            side_line_stops = year_line_stops[year_line_stops['side'] == side]
            
            # Skip if no data for this year/side combination
            if len(side_stations) == 0 and len(side_lines) == 0:
                logger.warning(f"No data for year {year}, side {side}")
                continue
            
            # Final standardization without helper columns
            final_stations = standardize_dataframe(side_stations, 'stations', keep_year_and_side=False)
            final_lines = standardize_dataframe(side_lines, 'lines', keep_year_and_side=False)
            final_line_stops = standardize_dataframe(side_line_stops, 'line_stops', keep_year_and_side=False)
            
            # Save stops_matched_initial
            matched_file = DIRS['interim_matched'] / f"stops_{year}_{side}.csv"
            final_stations.to_csv(matched_file, index=False)
            logger.info(f"Saved {len(final_stations)} stations to {matched_file}")
            
            # Save lines to interim_base
            lines_file = DIRS['interim_base'] / f"lines_{year}_{side}.csv"
            final_lines.to_csv(lines_file, index=False)
            logger.info(f"Saved {len(final_lines)} lines to {lines_file}")
            
            # Create empty processed directories
            processed_dir = DIRS['processed'] / f"{year}_{side}"
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # For demonstration/testing, also save directly to verified
            # In real use, you would run the geolocation verification notebook instead
            verified_file = DIRS['interim_verified'] / f"stops_{year}_{side}.csv"
            final_stations.to_csv(verified_file, index=False)
            logger.info(f"Saved {len(final_stations)} stations to {verified_file} (for demo only)")
            
            # Save line_stops to a custom location for later use
            if not final_line_stops.empty:
                line_stops_file = DIRS['interim_base'] / f"line_stops_{year}_{side}.csv"
                final_line_stops.to_csv(line_stops_file, index=False)
                logger.info(f"Saved {len(final_line_stops)} line-stop relations to {line_stops_file}")

def main():
    """Main function to run the integration process."""
    logger.info("Starting legacy data integration with historical context")
    logger.info(f"Using Berlin division year: {BERLIN_DIVISION_YEAR}")
    
    # Create necessary directories
    create_directories()
    
    # Load combined data
    stations_path = "legacy_data/stations.csv"
    lines_path = "legacy_data/lines.csv"
    line_stops_path = "legacy_data/line_stops.csv"
    
    try:
        stations_df, lines_df, line_stops_df = load_combined_data(stations_path, lines_path, line_stops_path)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return
    
    # Prepare data for splitting with standardized columns
    logger.info("Standardizing data formats...")
    stations_df = prepare_stations_for_split(stations_df)
    lines_df = prepare_lines_for_split(lines_df)
    line_stops_df = prepare_line_stops_for_split(line_stops_df, lines_df)
    
    # Count and display the number of records by year and side before expansion
    logger.info("Station counts by year and side before expansion:")
    year_side_counts = stations_df.groupby(['year', 'side']).size()
    for (year, side), count in year_side_counts.items():
        logger.info(f"Year {year}, Side {side}: {count} stations")
    
    # Split and save data
    split_and_save_data(stations_df, lines_df, line_stops_df)
    
    logger.info("""
    Data integration complete! Next steps:
    1. Verify the data in the interim directories
    2. Run 01_geolocation_verification_splitting.ipynb for each year/side
    3. Run 02_enrichment.ipynb for each year/side
    4. Run verification and other processing as needed
    """)

if __name__ == "__main__":
    main()