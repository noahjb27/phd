
"""
Module for enriching Berlin transport network data with additional information.
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Tuple, Optional, List, Union

logger = logging.getLogger(__name__)


# ---- Line-Stop Relationship Functions ----

def create_line_stops_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a DataFrame representing the relationships between lines and stops.
    
    Args:
        base_df: Base DataFrame with stop information
        
    Returns:
        DataFrame with line-stop relationships
    """
    # Split the stops and create a DataFrame
    line_stops = raw_df['stops'].str.split(' - ', expand=True).stack().reset_index(level=1, drop=True).reset_index(name='stop_name')

    # Add the 'type' column from the raw_df to the line_stops DataFrame
    line_stops = line_stops.merge(raw_df[['type', 'line_name']], left_on='index', right_index=True)

    line_stops['stop_order'] = line_stops.groupby('index').cumcount()
    #index starts from 0 so it looks like 1 row is missing but this is not true

    # Clean the 'Stop Name' column by removing whitespace and non-breaking spaces
    line_stops['stop_name'] = line_stops['stop_name'].str.replace(u'\xa0', ' ').str.strip()

    return line_stops


def add_stop_foreign_keys(line_stops: pd.DataFrame, stops_df: pd.DataFrame, year, side) -> pd.DataFrame:
    """
    Add stop foreign keys to line-stops DataFrame.
    
    Args:
        line_stops: DataFrame with line-stop relationships
        stops_df: DataFrame with stop information
        
    Returns:
        Updated line-stops DataFrame with stop foreign keys
    """
    try:
        result = line_stops.copy()
        
        # Create a mapping from stop name to stop ID
        stop_id_map = {}
        for _, row in stops_df.iterrows():
            stop_id_map[(str(row['stop_name']), str(row['type']), str(row['line_name']))] = str(row['stop_id'])
        
        def get_line_id(row):
                key = (str(row['stop_name']), str(row['type']), str(row['line_name']))
                return stop_id_map.get(key, None)
            
        result['stop_id'] = result.apply(get_line_id, axis=1)

        # Add 1 to the 'index' column and convert to string with year prefix
        result['line_id'] = result['index'].apply(lambda x: f"{year}{x + 1}_{side}")
        
        result = result.drop(columns=['stop_name', 'index', 'type', 'line_name'])
        
        logger.info(f"Added stop foreign keys to {len(result)} line-stop relationships")
        return result
        
    except Exception as e:
        logger.error(f"Error adding stop foreign keys: {e}")
        return line_stops

def finalize_data(line_df: pd.DataFrame, 
                 stops_df: pd.DataFrame, 
                 line_stops: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Finalize data for output.
    
    Args:
        line_df: DataFrame with line information
        stops_df: DataFrame with stop information
        line_stops: DataFrame with line-stop relationships
        
    Returns:
        Tuple of (final_line_df, final_stops_df, final_line_stops_df)
    """
    try:
        # Finalize line DataFrame
        final_line_df = line_df.copy()
        
        # Finalize stops DataFrame
        final_stops_df = stops_df.copy()
        
        # Finalize line-stops DataFrame
        final_line_stops_df = line_stops.copy()
        
        logger.info(f"Finalized data: {len(final_line_df)} lines, {len(final_stops_df)} stops, "
                   f"{len(final_line_stops_df)} line-stop relationships")
                    
        return final_line_df, final_stops_df, final_line_stops_df
        
    except Exception as e:
        logger.error(f"Error finalizing data: {e}")
        return line_df, stops_df, pd.DataFrame()

def save_data(paths: Dict[str, Path], 
             final_line_df: pd.DataFrame, 
             final_stops_df: pd.DataFrame, 
             final_line_stops_df: pd.DataFrame,
             year: int,
             side: str) -> None:
    """
    Save final processed data.
    
    Args:
        paths: Dictionary of paths
        final_line_df: Final line DataFrame
        final_stops_df: Final stop DataFrame
        final_line_stops_df: Final line-stops DataFrame
        year: Year of data
        side: Side of Berlin (east/west)
    """
    try:
        # Create processed directory
        processed_dir = paths['processed_dir'] / f"{year}_{side}"
        processed_dir.mkdir(exist_ok=True, parents=True)
        
        # Save files
        final_line_df.to_csv(processed_dir / "lines.csv", index=False)
        final_stops_df.to_csv(processed_dir / "stops.csv", index=False)
        final_line_stops_df.to_csv(processed_dir / "line_stops.csv", index=False)
        
        logger.info(f"Saved processed data to {processed_dir}")
        
    except Exception as e:
        logger.error(f"Error saving processed data: {e}")

def print_summary(year: int, 
                 side: str, 
                 final_line_df: pd.DataFrame, 
                 final_stops_df: pd.DataFrame, 
                 final_line_stops_df: pd.DataFrame,
                 paths: Dict[str, Path]) -> None:
    """
    Print a summary of the processed data and next steps.
    
    Args:
        year: Year of data
        side: Side of Berlin (east/west)
        final_line_df: Final line DataFrame
        final_stops_df: Final stop DataFrame
        final_line_stops_df: Final line-stops DataFrame
        paths: Dictionary of paths
    """
    print("\n" + "="*80)
    print(f"ENRICHMENT SUMMARY: {year} {side.upper()}")
    print("="*80)
    
    print(f"\nProcessed data summary:")
    print(f"  - Lines: {len(final_line_df)}")
    print(f"  - Stops: {len(final_stops_df)}")
    print(f"  - Line-stop connections: {len(final_line_stops_df)}")
    
    # Transport type distribution
    transport_counts = final_line_df['type'].value_counts()
    print("\nTransport type distribution:")
    for transport_type, count in transport_counts.items():
        print(f"  - {transport_type}: {count} lines")
    
    # Geographic distribution
    if 'east_west' in final_stops_df.columns:
        east_west_counts = final_stops_df['east_west'].value_counts()
        print("\nGeographic distribution:")
        for side, count in east_west_counts.items():
            print(f"  - {side.title()}: {count} stops")
    
    # Data completeness
    location_count = final_stops_df['location'].notna().sum()
    location_pct = location_count / len(final_stops_df) * 100
    print(f"\nData completeness:")
    print(f"  - Stops with location: {location_count} ({location_pct:.1f}%)")
    
    processed_dir = paths['processed_dir'] / f"{year}_{side}"
    print(f"\nData saved to: {processed_dir}")
    
    print("\nNext steps:")
    print("  1. Analyze the processed data to understand network structure")
    print("  2. Run network metrics to compare East and West Berlin")
    print("  3. Create visualizations of the transport network")
    print("="*80 + "\n")