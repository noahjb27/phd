# verification.py
"""
Module for verifying processed Berlin transport network data.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial.distance import euclidean


logger = logging.getLogger(__name__)

# Define valid transport types
VALID_TRANSPORT_TYPES = {'autobus', 'omnibus', 'tram', 'u-bahn', 's-bahn', 'ferry'}

def load_processed_data(base_dir: Path, year: int, side: str) -> Dict[str, pd.DataFrame]:
    """
    Load processed data files for verification.
    
    Args:
        base_dir: Base data directory
        year: Year of data
        side: Side of Berlin (east/west)
        
    Returns:
        Dictionary containing loaded DataFrames
    """
    try:
        processed_dir = base_dir / 'processed' / f"{year}_{side}"
        
        if not processed_dir.exists():
            logger.error(f"Processed directory not found: {processed_dir}")
            return {}
            
        # Load the three main files
        lines_path = processed_dir / 'lines.csv'
        stops_path = processed_dir / 'stops.csv'
        line_stops_path = processed_dir / 'line_stops.csv'
        
        # Check if all files exist
        if not all(p.exists() for p in [lines_path, stops_path, line_stops_path]):
            missing = [p.name for p in [lines_path, stops_path, line_stops_path] if not p.exists()]
            logger.error(f"Missing files in {processed_dir}: {', '.join(missing)}")
            return {}
            
        # Load data
        lines_df = pd.read_csv(lines_path)
        stops_df = pd.read_csv(stops_path)
        line_stops_df = pd.read_csv(line_stops_path)
        
        logger.info(f"Loaded processed data: {len(lines_df)} lines, {len(stops_df)} stops, "
                   f"{len(line_stops_df)} line-stop relationships")
                    
        return {
            'lines': lines_df,
            'stops': stops_df,
            'line_stops': line_stops_df
        }
        
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        return {}
    
def calculate_station_distances(stops_df: pd.DataFrame, line_stops_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Euclidean distances between connected stations.
    
    Args:
        stops_df: DataFrame with stop information including location
        line_stops_df: DataFrame with line-stop relationships
        
    Returns:
        DataFrame with line-stop relationships enriched with distances
    """
    try:
        # Create a copy to avoid modifying the original
        line_stops_with_dist = line_stops_df.copy()
        
        # Create a function to extract lat/lon from location string
        def extract_coords(loc_str):
            if pd.isna(loc_str) or loc_str == '':
                return None
            try:
                lat, lon = map(float, loc_str.split(','))
                return (lat, lon)
            except (ValueError, TypeError):
                return None
        
        # Create a mapping of stop_id to coordinates
        stop_coords = {}
        for _, row in stops_df.iterrows():
            if pd.notna(row['location']) and row['location'] != '':
                coords = extract_coords(row['location'])
                if coords:
                    stop_coords[row['stop_id']] = coords
        
        # Group line_stops by line_id to get pairs of connected stops
        line_stops_grouped = line_stops_with_dist.sort_values(['line_id', 'stop_order']).groupby('line_id')
        
        # Initialize distance column
        line_stops_with_dist['distance_meters'] = np.nan
        
        # Calculate distances
        for line_id, group in line_stops_grouped:
            # Get the ordered stops for this line
            ordered_stops = group.sort_values('stop_order')
            
            if len(ordered_stops) < 2:
                continue
                
            # Calculate distance between consecutive stops
            for i in range(len(ordered_stops) - 1):
                current_stop_id = ordered_stops.iloc[i]['stop_id']
                next_stop_id = ordered_stops.iloc[i + 1]['stop_id']
                
                # Skip if we don't have coordinates for either stop
                if current_stop_id not in stop_coords or next_stop_id not in stop_coords:
                    continue
                
                # Get coordinates
                current_coords = stop_coords[current_stop_id]
                next_coords = stop_coords[next_stop_id]
                
                # Calculate rough distance in meters (approximation)
                # 1 degree of latitude ~ 111km
                # 1 degree of longitude ~ 111km * cos(latitude)
                lat1, lon1 = current_coords
                lat2, lon2 = next_coords
                
                # Simple Euclidean distance scaled to approximate meters
                dx = (lon2 - lon1) * 111000 * np.cos(np.radians((lat1 + lat2) / 2))
                dy = (lat2 - lat1) * 111000
                distance = np.sqrt(dx**2 + dy**2)
                
                # Update the distance for the current stop
                idx = ordered_stops.iloc[i].name
                line_stops_with_dist.loc[idx, 'distance_meters'] = distance
        
        return line_stops_with_dist
        
    except Exception as e:
        logger.error(f"Error calculating station distances: {e}")
        return line_stops_df

def verify_station_distances(stops_df: pd.DataFrame, line_stops_df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, pd.DataFrame]:
    """
    Verify that distances between connected stations are within reasonable limits.
    
    Args:
        stops_df: DataFrame with stop information
        line_stops_df: DataFrame with line-stop relationships (should include distances)
        
    Returns:
        Tuple of (is_valid, too_close_stops, too_far_stops)
    """
    try:
        # Define distance thresholds by transport type (in meters)
        # These are approximate values and can be adjusted based on domain knowledge
        MIN_DISTANCE = 200  # Minimum distance between any connected stations
        
        MAX_DISTANCES = {
            'u-bahn': 2000,    # U-Bahn typically has stops 0.5-1.5km apart
            's-bahn': 3000,    # S-Bahn typically has stops 1-2.5km apart
            'tram': 1000,       # Trams typically have stops 400-700m apart
            'autobus': 1000,    # Buses typically have stops 300-500m apart
            'omnibus': 1000,    # Same as bus
            'ferry': 3000,     # Ferries can have longer distances
        }
        
        # Default maximum distance for unknown types
        DEFAULT_MAX_DISTANCE = 1500
        
        # Calculate distances if not already done
        if 'distance_meters' not in line_stops_df.columns:
            line_stops_with_dist = calculate_station_distances(stops_df, line_stops_df)
        else:
            line_stops_with_dist = line_stops_df.copy()
        
        # Get transport type for each line
        line_types = {}
        for _, row in stops_df.iterrows():
            line_types[row['line_name']] = row['type'].lower() if pd.notna(row['type']) else None
        
        # Filter out rows without distance (e.g., terminal stations)
        valid_distances = line_stops_with_dist[line_stops_with_dist['distance_meters'].notna()].copy()
        
        if len(valid_distances) == 0:
            logger.warning("No valid distances calculated between stations")
            return True, pd.DataFrame(), pd.DataFrame()
        
        # Add transport type to distances DataFrame using line_name from stops
        valid_distances['transport_type'] = valid_distances['line_id'].apply(
            lambda x: next((line_types.get(ln) for ln in line_types if ln in x), None)
        )
        
        # Determine max distance for each connection based on transport type
        def get_max_distance(transport_type):
            if pd.isna(transport_type):
                return DEFAULT_MAX_DISTANCE
            return MAX_DISTANCES.get(transport_type.lower(), DEFAULT_MAX_DISTANCE)
        
        valid_distances['max_allowed_distance'] = valid_distances['transport_type'].apply(get_max_distance)
        
        # Identify stops that are too close or too far apart
        too_close = valid_distances[valid_distances['distance_meters'] < MIN_DISTANCE].copy()
        too_far = valid_distances[valid_distances['distance_meters'] > valid_distances['max_allowed_distance']].copy()
        
        # Add stop names for better readability
        stop_names = stops_df[['stop_id', 'stop_name']].set_index('stop_id')['stop_name'].to_dict()
        
        if not too_close.empty:
            too_close['stop_name'] = too_close['stop_id'].map(stop_names)
        
        if not too_far.empty:
            too_far['stop_name'] = too_far['stop_id'].map(stop_names)
        
        is_valid = len(too_close) == 0 and len(too_far) == 0
        
        if not is_valid:
            logger.warning(f"Found {len(too_close)} connections that are too close and "
                          f"{len(too_far)} connections that are too far apart")
        
        return is_valid, too_close, too_far
        
    except Exception as e:
        logger.error(f"Error verifying station distances: {e}")
        return False, pd.DataFrame(), pd.DataFrame()


def verify_transport_types(lines_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Verify that all transport types are valid.
    
    Args:
        lines_df: DataFrame with line information
        
    Returns:
        Tuple of (is_valid, invalid_types)
    """
    if 'type' not in lines_df.columns:
        logger.error(f"'type' column not found in lines DataFrame")
        return False, []
        
    # Get unique transport types
    unique_types = set(lines_df['type'].str.lower())
    
    # Find invalid types
    invalid_types = unique_types - VALID_TRANSPORT_TYPES
    
    is_valid = len(invalid_types) == 0
    
    if not is_valid:
        logger.warning(f"Found invalid transport types: {', '.join(invalid_types)}")
        
    return is_valid, list(invalid_types)

def verify_stop_uniqueness(stops_df: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
    """
    Verify that each combination of stop_name, line_name, and year is unique.
    
    Args:
        stops_df: DataFrame with stop information
        
    Returns:
        Tuple of (is_unique, duplicate_rows)
    """
    # Check if required columns exist
    required_cols = ['stop_name', 'line_name']
    missing_cols = [col for col in required_cols if col not in stops_df.columns]
    
    if missing_cols:
        logger.error(f"Missing columns in stops DataFrame: {', '.join(missing_cols)}")
        return False, pd.DataFrame()
    
    # Add year if not already in DataFrame
    if 'year' not in stops_df.columns and 'stop_id' in stops_df.columns:
        # Try to extract year from stop_id
        try:
            stops_df['year'] = stops_df['stop_id'].str.extract(r'^(\d{4})').astype(int)
        except:
            logger.warning("Could not extract year from stop_id")
            stops_df['year'] = 0
    
    # Find duplicates
    duplicates = stops_df.duplicated(subset=['stop_name', 'line_name', 'year'], keep=False)
    duplicate_rows = stops_df[duplicates].copy()
    
    is_unique = not duplicates.any()
    
    if not is_unique:
        logger.warning(f"Found {len(duplicate_rows)} duplicate stop entries")
        
    return is_unique, duplicate_rows

def verify_stop_connections(stops_df: pd.DataFrame, line_stops_df: pd.DataFrame) -> Tuple[bool, Dict[str, pd.DataFrame]]:
    """
    Verify that each stop has at least one connection and no more than two connections.
    
    Args:
        stops_df: DataFrame with stop information
        line_stops_df: DataFrame with line-stop relationships
        
    Returns:
        Tuple of (is_valid, problematic_stops)
    """
    if 'stop_id' not in stops_df.columns or 'stop_id' not in line_stops_df.columns:
        logger.error("Missing 'stop_id' column in dataframes")
        return False, {}
    
    # Count connections per stop
    stop_connection_counts = line_stops_df['stop_id'].value_counts().reset_index()
    stop_connection_counts.columns = ['stop_id', 'connection_count']
    
    # Find stops with no connections
    all_stop_ids = set(stops_df['stop_id'])
    connected_stop_ids = set(line_stops_df['stop_id'])
    disconnected_stop_ids = all_stop_ids - connected_stop_ids
    
    disconnected_stops = stops_df[stops_df['stop_id'].isin(disconnected_stop_ids)].copy()
    
    # Find stops with more than 2 connections
    too_many_connections = stop_connection_counts[stop_connection_counts['connection_count'] > 2]
    too_many_connections_stops = stops_df[stops_df['stop_id'].isin(too_many_connections['stop_id'])].copy()
    
    # Merge connection counts into the result
    if not too_many_connections_stops.empty:
        too_many_connections_stops = too_many_connections_stops.merge(
            stop_connection_counts, on='stop_id', how='left'
        )
    
    is_valid = len(disconnected_stops) == 0 and len(too_many_connections_stops) == 0
    
    if not is_valid:
        logger.warning(f"Found {len(disconnected_stops)} disconnected stops and "
                      f"{len(too_many_connections_stops)} stops with more than 2 connections")
    
    return is_valid, {
        'disconnected': disconnected_stops,
        'too_many_connections': too_many_connections_stops
    }

def verify_line_stops_integrity(lines_df: pd.DataFrame, stops_df: pd.DataFrame, line_stops_df: pd.DataFrame) -> Tuple[bool, Dict[str, pd.DataFrame]]:
    """
    Verify referential integrity between lines, stops, and line_stops.
    
    Args:
        lines_df: DataFrame with line information
        stops_df: DataFrame with stop information
        line_stops_df: DataFrame with line-stop relationships
        
    Returns:
        Tuple of (is_valid, invalid_references)
    """
    if 'line_id' not in lines_df.columns or 'line_id' not in line_stops_df.columns:
        logger.error("Missing 'line_id' column in dataframes")
        return False, {}
        
    if 'stop_id' not in stops_df.columns or 'stop_id' not in line_stops_df.columns:
        logger.error("Missing 'stop_id' column in dataframes")
        return False, {}
        
    # Check for line_stops referencing non-existent line_ids
    valid_line_ids = set(lines_df['line_id'])
    line_stops_line_ids = set(line_stops_df['line_id'])
    invalid_line_ids = line_stops_line_ids - valid_line_ids
    
    invalid_line_refs = line_stops_df[line_stops_df['line_id'].isin(invalid_line_ids)].copy()
    
    # Check for line_stops referencing non-existent stop_ids
    valid_stop_ids = set(stops_df['stop_id'])
    line_stops_stop_ids = set(line_stops_df['stop_id'])
    invalid_stop_ids = line_stops_stop_ids - valid_stop_ids
    
    invalid_stop_refs = line_stops_df[line_stops_df['stop_id'].isin(invalid_stop_ids)].copy()
    
    is_valid = len(invalid_line_ids) == 0 and len(invalid_stop_ids) == 0
    
    if not is_valid:
        logger.warning(f"Found {len(invalid_line_refs)} invalid line references and "
                      f"{len(invalid_stop_refs)} invalid stop references")
                      
    return is_valid, {
        'invalid_line_refs': invalid_line_refs,
        'invalid_stop_refs': invalid_stop_refs
    }

def verify_geographic_data(stops_df: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
    """
    Verify that stops have geographic data.
    
    Args:
        stops_df: DataFrame with stop information
        
    Returns:
        Tuple of (is_valid, missing_geo)
    """
    if 'location' not in stops_df.columns:
        logger.error("Missing 'location' column in stops DataFrame")
        return False, pd.DataFrame()
        
    # Find stops with missing location
    missing_geo = stops_df[stops_df['location'].isna() | (stops_df['location'] == '')].copy()
    
    is_valid = len(missing_geo) == 0
    
    if not is_valid:
        logger.warning(f"Found {len(missing_geo)} stops with missing geographic data")
        
    return is_valid, missing_geo

def run_verification(base_dir: Path, year: int, side: str) -> Dict[str, Dict[str, object]]:
    """
    Run all verification checks on processed data.
    
    Args:
        base_dir: Base data directory
        year: Year of data
        side: Side of Berlin (east/west)
        
    Returns:
        Dictionary containing verification results
    """
    results = {
        'loaded': False,
        'transport_types': {'valid': False, 'invalid_types': []},
        'stop_uniqueness': {'valid': False, 'duplicate_count': 0},
        'stop_connections': {
            'valid': False, 
            'disconnected_count': 0, 
            'too_many_connections_count': 0
        },
        'referential_integrity': {
            'valid': False,
            'invalid_line_refs_count': 0,
            'invalid_stop_refs_count': 0
        },
        'geographic_data': {'valid': False, 'missing_geo_count': 0},
        'station_distances': {
            'valid': False,
            'too_close_count': 0,
            'too_far_count': 0
        },
        'overall': False
    }
    
    # Load data
    data = load_processed_data(base_dir, year, side)
    
    if not data:
        logger.error("Failed to load processed data")
        return results
        
    results['loaded'] = True
    lines_df = data['lines']
    stops_df = data['stops']
    line_stops_df = data['line_stops']
    
    # Run verification checks
    # 1. Transport types
    valid_types, invalid_types = verify_transport_types(lines_df)
    results['transport_types']['valid'] = valid_types
    results['transport_types']['invalid_types'] = invalid_types
    
    # 2. Stop uniqueness
    unique_stops, duplicate_stops = verify_stop_uniqueness(stops_df)
    results['stop_uniqueness']['valid'] = unique_stops
    results['stop_uniqueness']['duplicate_count'] = len(duplicate_stops)
    results['stop_uniqueness']['duplicates'] = duplicate_stops
    
    # 3. Stop connections
    valid_connections, problem_stops = verify_stop_connections(stops_df, line_stops_df)
    results['stop_connections']['valid'] = valid_connections
    results['stop_connections']['disconnected_count'] = len(problem_stops['disconnected'])
    results['stop_connections']['too_many_connections_count'] = len(problem_stops['too_many_connections'])
    results['stop_connections']['disconnected'] = problem_stops['disconnected']
    results['stop_connections']['too_many_connections'] = problem_stops['too_many_connections']
    
    # 4. Referential integrity
    valid_integrity, invalid_refs = verify_line_stops_integrity(lines_df, stops_df, line_stops_df)
    results['referential_integrity']['valid'] = valid_integrity
    results['referential_integrity']['invalid_line_refs_count'] = len(invalid_refs['invalid_line_refs'])
    results['referential_integrity']['invalid_stop_refs_count'] = len(invalid_refs['invalid_stop_refs'])
    results['referential_integrity']['invalid_line_refs'] = invalid_refs['invalid_line_refs']
    results['referential_integrity']['invalid_stop_refs'] = invalid_refs['invalid_stop_refs']
    
    # 5. Geographic data
    valid_geo, missing_geo = verify_geographic_data(stops_df)
    results['geographic_data']['valid'] = valid_geo
    results['geographic_data']['missing_geo_count'] = len(missing_geo)
    results['geographic_data']['missing_geo'] = missing_geo
    
    # 6. Station distances
    # Calculate distances and save to line_stops_df
    line_stops_with_dist = calculate_station_distances(stops_df, line_stops_df)
    
    # Save the enriched line_stops DataFrame with distances
    processed_dir = base_dir / 'processed' / f"{year}_{side}"
    if processed_dir.exists():
        try:
            line_stops_with_dist.to_csv(processed_dir / "line_stops_with_dist.csv", index=False)
            logger.info(f"Saved line_stops with distances to {processed_dir / 'line_stops_with_dist.csv'}")
        except Exception as e:
            logger.error(f"Error saving line_stops with distances: {e}")
    
    # Verify distances
    valid_distances, too_close, too_far = verify_station_distances(stops_df, line_stops_with_dist)
    results['station_distances']['valid'] = valid_distances
    results['station_distances']['too_close_count'] = len(too_close)
    results['station_distances']['too_far_count'] = len(too_far)
    results['station_distances']['too_close'] = too_close
    results['station_distances']['too_far'] = too_far
    
    # Overall result
    results['overall'] = all([
        valid_types,
        unique_stops,
        valid_connections,
        valid_integrity,
        valid_geo,
        valid_distances
    ])
    
    return results

def generate_verification_report(results: Dict[str, Dict[str, object]], year: int, side: str) -> str:
    """
    Generate a human-readable verification report.
    
    Args:
        results: Dictionary containing verification results
        year: Year of data
        side: Side of Berlin (east/west)
        
    Returns:
        Report as a string
    """
    report = []
    report.append("="*80)
    report.append(f"VERIFICATION REPORT: {year} {side.upper()}")
    report.append("="*80)
    
    if not results['loaded']:
        report.append("\nFAILED TO LOAD DATA - VERIFICATION ABORTED")
        return "\n".join(report)
    
    # Overall result
    status = "PASSED" if results['overall'] else "FAILED"
    report.append(f"\nOVERALL STATUS: {status}")
    
    # Transport types
    status = "PASSED" if results['transport_types']['valid'] else "FAILED"
    report.append(f"\n1. Transport Types: {status}")
    if not results['transport_types']['valid']:
        invalid = ", ".join(results['transport_types']['invalid_types'])
        report.append(f"   - Invalid transport types found: {invalid}")
        report.append(f"   - Valid types are: {', '.join(sorted(VALID_TRANSPORT_TYPES))}")
    
    # Stop uniqueness
    status = "PASSED" if results['stop_uniqueness']['valid'] else "FAILED"
    report.append(f"\n2. Stop Uniqueness: {status}")
    if not results['stop_uniqueness']['valid']:
        report.append(f"   - Found {results['stop_uniqueness']['duplicate_count']} duplicate stop entries")
    
    # Stop connections
    status = "PASSED" if results['stop_connections']['valid'] else "FAILED"
    report.append(f"\n3. Stop Connections: {status}")
    if not results['stop_connections']['valid']:
        report.append(f"   - Found {results['stop_connections']['disconnected_count']} disconnected stops "
                     f"(stops with no connections)")
        report.append(f"   - Found {results['stop_connections']['too_many_connections_count']} stops with more than "
                     f"2 connections")
    
    # Referential integrity
    status = "PASSED" if results['referential_integrity']['valid'] else "FAILED"
    report.append(f"\n4. Referential Integrity: {status}")
    if not results['referential_integrity']['valid']:
        report.append(f"   - Found {results['referential_integrity']['invalid_line_refs_count']} references to "
                     f"non-existent line IDs")
        report.append(f"   - Found {results['referential_integrity']['invalid_stop_refs_count']} references to "
                     f"non-existent stop IDs")
    
    # Geographic data
    status = "PASSED" if results['geographic_data']['valid'] else "FAILED"
    report.append(f"\n5. Geographic Data: {status}")
    if not results['geographic_data']['valid']:
        report.append(f"   - Found {results['geographic_data']['missing_geo_count']} stops with missing geographic data")
    
    # Station distances
    status = "PASSED" if results['station_distances']['valid'] else "FAILED"
    report.append(f"\n6. Station Distances: {status}")
    if not results['station_distances']['valid']:
        report.append(f"   - Found {results['station_distances']['too_close_count']} connections that are too close "
                     f"(< 200m)")
        report.append(f"   - Found {results['station_distances']['too_far_count']} connections that are too far apart "
                     f"(exceeding thresholds for their transport type)")
    
    # Recommendations
    report.append("\nRECOMMENDATIONS:")
    if not results['overall']:
        if not results['transport_types']['valid']:
            report.append("  - Standardize transport types in the lines.csv file")
        if not results['stop_uniqueness']['valid']:
            report.append("  - Resolve duplicate stop entries by consolidating or renaming")
        if results['stop_connections']['disconnected_count'] > 0:
            report.append("  - Add missing line_stops entries for disconnected stops")
        if results['stop_connections']['too_many_connections_count'] > 0:
            report.append("  - Review stops with more than 2 connections to ensure they're valid")
        if not results['referential_integrity']['valid']:
            report.append("  - Fix invalid references in line_stops.csv")
        if not results['geographic_data']['valid']:
            report.append("  - Add missing geographic coordinates to stops")
        if not results['station_distances']['valid']:
            report.append("  - Review and fix station coordinates for stops with unrealistic distances")
    else:
        report.append("  - No issues found! Data is ready for analysis.")
    
    report.append("="*80)
    return "\n".join(report)

if __name__ == "__main__":
    import sys
    import argparse
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Verify processed Berlin transport data")
    parser.add_argument("--year", type=int, required=True, help="Year to verify")
    parser.add_argument("--side", type=str, required=True, choices=["east", "west"], 
                       help="Side of Berlin (east/west)")
    parser.add_argument("--data-dir", type=str, default="../data", 
                       help="Base data directory path")
    
    args = parser.parse_args()
    
    # Run verification
    results = run_verification(Path(args.data_dir), args.year, args.side)
    
    # Print report
    report = generate_verification_report(results, args.year, args.side)
    print(report)
    
    # Return exit code based on overall result
    sys.exit(0 if results['overall'] else 1)