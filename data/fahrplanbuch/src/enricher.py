"""
Module for enriching Berlin transport network data with additional information.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import json
import logging
from typing import Dict, Tuple, Optional, List, Union
from shapely.geometry import Point

logger = logging.getLogger(__name__)

# ---- Data Loading Functions ----

def load_data(paths: Dict[str, Path], year: int, side: str) -> Tuple:
    """
    Load all required data files for enrichment.
    
    Args:
        paths: Dictionary of paths
        year: Year to process
        side: Side of Berlin (east/west)
        
    Returns:
        Tuple of (line_df, stops_df)
    """
    try:
        # Load base data
        line_path = paths['interim_dir'] / 'stops_base' / f'lines_{year}_{side}.csv'
        
        line_df = pd.read_csv(line_path)
        logger.info(f"Loaded base data: {len(line_df)} lines")
        
        # Load verified stops
        verified_path = paths['interim_dir'] / 'stops_verified' / f'stops_{year}_{side}.csv'
        if not verified_path.exists():
            logger.error(f"Verified stops data not found at {verified_path}")
            raise FileNotFoundError(f"Verified stops file not found")
            
        final_stops = pd.read_csv(verified_path)
        logger.info(f"Loaded verified stops: {len(final_stops)} stops")
        
        return line_df, final_stops
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

# ---- Line Enrichment Functions ----

def enrich_lines(line_df: pd.DataFrame, side) -> pd.DataFrame:
    """
    Enrich lines with profile and capacity information.
    
    Args:
        line_df: DataFrame with line information
        
    Returns:
        Enriched line DataFrame
    """
    try:
        line_df = line_df.copy()
        
        # Define sets for U-Bahn profile classification
        kleinprofil = {'1', '2', '3', '4', 'A', 'A I', 'A II', 'A III', 'A1', 'A2', 'B', 'B I', 'B II', 'B III', 'B1', 'B2'}
        grossprofil = {'5', '6', '7', '8', '9', 'C', 'C I', 'C II', 'D', 'E', 'G'}
        
        # Add profile for U-Bahn lines
        line_df['profile'] = None
        
        # Filter for U-Bahn lines
        u_bahn_mask = line_df['type'] == 'u-bahn'
        
        # Add profile based on line name
        for idx, row in line_df[u_bahn_mask].iterrows():
            line_name = row['line_name']
            if line_name in kleinprofil:
                line_df.loc[idx, 'profile'] = 'Kleinprofil'
            elif line_name in grossprofil:
                line_df.loc[idx, 'profile'] = 'Großprofil'
        
        # Add capacity information based on type and profile
        line_df['capacity'] = 0
        
        # Set capacity values based on transport type
        for idx, row in line_df.iterrows():
            transport_type = row['type']
            
            if transport_type == 'u-bahn':
                if row['profile'] == 'Kleinprofil':
                    line_df.loc[idx, 'capacity'] = 750
                elif row['profile'] == 'Großprofil':
                    line_df.loc[idx, 'capacity'] = 1000
                else:
                    line_df.loc[idx, 'capacity'] = 875  # Average if profile unknown
                    
            elif transport_type == 's-bahn':
                line_df.loc[idx, 'capacity'] = 1100
                
            elif transport_type == 'strassenbahn' or transport_type == 'tram':
                line_df.loc[idx, 'capacity'] = 195
                
            elif transport_type.startswith('bus'):
                line_df.loc[idx, 'capacity'] = 100
                
            elif transport_type == 'fähre' or transport_type == 'FÃ¤hre':
                line_df.loc[idx, 'capacity'] = 300

        line_df['line_id'] = line_df['line_id'].astype(str) + '_' + side
        
        logger.info(f"Enriched lines with profile and capacity information")
        return line_df
        
    except Exception as e:
        logger.error(f"Error enriching lines: {e}")
        return line_df

# ---- Geographic Data Functions ----

def load_district_data(geo_data_dir: Path) -> Tuple[Optional[gpd.GeoDataFrame], Optional[List[str]]]:
    """
    Load district data for administrative enrichment.
    
    Args:
        geo_data_dir: Directory containing geographic data files
        
    Returns:
        Tuple of (districts_gdf, west_berlin_districts)
    """
    try:
        # Load district GeoJSON
        districts_path = geo_data_dir / "lor_ortsteile.geojson"
        if not districts_path.exists():
            logger.warning(f"District data not found at {districts_path}")
            return None, None
            
        districts_gdf = gpd.read_file(districts_path)
        logger.info(f"Loaded district data: {len(districts_gdf)} districts")
        
        # Load West Berlin districts
        west_berlin_path = geo_data_dir / "West-Berlin-Ortsteile.json"
        if not west_berlin_path.exists():
            logger.warning(f"West Berlin district list not found at {west_berlin_path}")
            return districts_gdf, None
            
        with open(west_berlin_path, "r") as f:
            west_berlin_data = json.load(f)
            west_berlin_districts = west_berlin_data.get("West_Berlin", [])
            
        logger.info(f"Loaded {len(west_berlin_districts)} West Berlin districts")
        return districts_gdf, west_berlin_districts
        
    except Exception as e:
        logger.error(f"Error loading district data: {e}")
        return None, None

def load_postal_code_data(geo_data_dir: Path = None) -> Optional[gpd.GeoDataFrame]:
    """
    Load postal code data from local GeoJSON file.
    
    Args:
        geo_data_dir: Directory containing geographic data files
        
    Returns:
        GeoDataFrame with postal code boundaries or None if not available
    """
    try:
        # Path to local file
        if geo_data_dir is None:
            geo_data_dir = Path('../data/data-external')
            
        local_file = geo_data_dir / "berlin_postal_codes.geojson"
            
        if local_file.exists():
            logger.info(f"Loading postal code data from local file {local_file}")
            plz_gdf = gpd.read_file(local_file)
            logger.info(f"Loaded postal code data: {len(plz_gdf)} areas")
            return plz_gdf
        else:
            logger.warning(f"Postal code file not found at {local_file}")
            logger.info("Run the save_postal_codes.py script to download the data")
            return None
        
    except Exception as e:
        logger.error(f"Error loading postal code data: {e}")
        return None

def convert_stops_to_geodataframe(stops_df: pd.DataFrame, crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """
    Convert stops DataFrame to GeoDataFrame with proper geometry.
    
    Args:
        stops_df: DataFrame with stops and location column
        crs: Coordinate reference system (default: WGS84)
        
    Returns:
        GeoDataFrame with Point geometries
    """
    try:
        stops_df = stops_df.copy()
        
        # Function to create Point geometry from location string
        def create_point(loc_str):
            if pd.isna(loc_str) or loc_str == '':
                return None
            try:
                lat, lon = map(float, str(loc_str).split(','))
                return Point(lon, lat)  # Note: GeoDataFrame expects (lon, lat)
            except (ValueError, TypeError):
                return None
        
        # Create geometry column
        geometries = stops_df['location'].apply(create_point)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(stops_df, geometry=geometries, crs=crs)
        
        # Remove rows with invalid geometries
        valid_gdf = gdf[~gdf.geometry.isna()].copy()
        logger.info(f"Created GeoDataFrame with {len(valid_gdf)} valid geometries "
                    f"from {len(stops_df)} total stops")
        
        return valid_gdf
        
    except Exception as e:
        logger.error(f"Error converting stops to GeoDataFrame: {e}")
        # Return empty GeoDataFrame with same schema
        return gpd.GeoDataFrame(stops_df.head(0), geometry=gpd.GeoSeries(dtype=object), crs=crs)

def add_administrative_data(side, stops_df: pd.DataFrame, 
                           districts_gdf: gpd.GeoDataFrame, 
                           west_berlin_districts: List[str]) -> pd.DataFrame:
    """
    Add district and neighborhood information to stops.
    
    Args:
        stops_df: DataFrame with stops
        districts_gdf: GeoDataFrame with district boundaries
        west_berlin_districts: List of district names in West Berlin
        
    Returns:
        DataFrame with added administrative data
    """
    try:
        # Convert stops to GeoDataFrame
        stops_gdf = convert_stops_to_geodataframe(stops_df)
        
        if len(stops_gdf) == 0:
            logger.warning("No valid geometries in stops data, skipping administrative enrichment")
            return stops_df
            
        # Ensure CRS match
        if districts_gdf.crs != stops_gdf.crs:
            logger.info(f"Converting district CRS from {districts_gdf.crs} to {stops_gdf.crs}")
            districts_gdf = districts_gdf.to_crs(stops_gdf.crs)
        
        # Perform spatial join
        result_gdf = gpd.sjoin(stops_gdf, districts_gdf, how="left", predicate='within')
        
        # Drop unnecessary columns from the join
        columns_to_drop = ["index_right", "gml_id", "spatial_name", "spatial_alias", 
                           "spatial_type", "FLAECHE_HA"]
        for col in columns_to_drop:
            if col in result_gdf.columns:
                result_gdf = result_gdf.drop(columns=[col])
        
        # Add east/west column
        result_gdf['east_west'] = f"{side}"
        
        # Rename district columns to standardized names
        column_mapping = {
            'OTEIL': 'neighbourhood',
            'BEZIRK': 'district'
        }
        result_gdf = result_gdf.rename(columns=column_mapping)
        
        # Convert back to DataFrame
        result_df = pd.DataFrame(result_gdf.drop(columns='geometry'))
        
        logger.info(f"Added administrative data to {len(result_df)} stops")
        return result_df
        
    except Exception as e:
        logger.error(f"Error adding administrative data: {e}")
        return stops_df

def add_postal_code_data(stops_df: pd.DataFrame, 
                         plz_gdf: Optional[gpd.GeoDataFrame] = None, 
                         geo_data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Add postal code information to stops.
    
    Args:
        stops_df: DataFrame with stops
        plz_gdf: GeoDataFrame with postal code boundaries (optional)
        geo_data_dir: Directory containing geographic data files (used if plz_gdf is None)
        
    Returns:
        DataFrame with added postal code data
    """
    try:
        # If no plz_gdf is provided, try to load it
        if plz_gdf is None:
            plz_gdf = load_postal_code_data(geo_data_dir)
            if plz_gdf is None:
                logger.warning("Could not load postal code data, skipping postal code enrichment")
                return stops_df
        
        # Convert stops to GeoDataFrame
        stops_gdf = convert_stops_to_geodataframe(stops_df)
        
        if len(stops_gdf) == 0:
            logger.warning("No valid geometries in stops data, skipping postal code enrichment")
            return stops_df
            
        # Ensure CRS match
        if plz_gdf.crs != stops_gdf.crs:
            logger.info(f"Converting postal code CRS from {plz_gdf.crs} to {stops_gdf.crs}")
            plz_gdf = plz_gdf.to_crs(stops_gdf.crs)
        
        # Perform spatial join
        joined_gdf = gpd.sjoin(stops_gdf, plz_gdf, how="left", predicate='within')
        
        # Check if the 'plz' column is in the result
        postal_code_column = 'plz'
        if postal_code_column not in joined_gdf.columns:
            logger.warning(f"Postal code column '{postal_code_column}' not found in joined data")
            return stops_df
        
        # Create a copy of the original DataFrame and add the postal code
        result_df = stops_df.copy()
        result_df['postal_code'] = joined_gdf[postal_code_column]
        
        # Count how many stops got a postal code
        postal_codes_added = result_df['postal_code'].notna().sum()
        logger.info(f"Added postal codes to {postal_codes_added} out of {len(result_df)} stops")
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error adding postal code data: {e}")
        return stops_df