import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple, List
import ast
import logging

logger = logging.getLogger(__name__)

@dataclass
class DistanceThresholds:
    """Distance thresholds for different transport types in kilometers."""
    s_bahn: float = 2.5
    u_bahn: float = 1.5
    strassenbahn: float = 0.8
    bus: float = 0.5

class GeoValidator:
    def __init__(self, thresholds: Optional[DistanceThresholds] = None):
        self.thresholds = thresholds or DistanceThresholds()
        
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def validate_distance(self, row1: pd.Series, row2: pd.Series) -> Tuple[bool, Optional[str]]:
        """
        Validate distance between two consecutive stops.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        transport_type = row1['type']
        threshold = getattr(self.thresholds, transport_type.lower(), 1.0)
        
        try:
            lat1, lon1 = map(float, row1['location'].split(','))
            lat2, lon2 = map(float, row2['location'].split(','))
            
            distance = self.calculate_distance(lat1, lon1, lat2, lon2)
            
            if distance > threshold:
                return False, f"Distance {distance:.2f}km exceeds threshold {threshold}km for {transport_type}"
            return True, None
            
        except (ValueError, AttributeError):
            return False, "Invalid coordinate format"

class StationMatcher:
    """Matches stations with existing station database considering line information."""
    
    def __init__(self, existing_stations: pd.DataFrame):
        """
        Initialize matcher with existing stations dataframe.
        
        Args:
            existing_stations: DataFrame with columns:
                - stop_id
                - stop_name
                - type
                - location
                - in_lines (stringified list)
                - identifier
        """
        self.existing_stations = existing_stations.copy()
        self._parse_line_lists()
        
    def _parse_line_lists(self) -> None:
        """Parse stringified lists in in_lines column to actual lists."""
        def safe_eval(x):
            try:
                if pd.isna(x):
                    return []
                return ast.literal_eval(x)
            except (ValueError, SyntaxError):
                logger.warning(f"Could not parse line list: {x}")
                return []
                
        self.existing_stations['in_lines'] = self.existing_stations['in_lines'].apply(safe_eval)
        
    def _line_match(self, station_line: str, existing_lines: List[str]) -> bool:
        """
        Check if a station's line exists in list of existing lines.
        
        Args:
            station_line: Single line number/name
            existing_lines: List of line numbers/names
        
        Returns:
            True if line matches, False otherwise
        """
        station_line = str(station_line).strip()
        existing_lines = [str(line).strip() for line in existing_lines]
        return station_line in existing_lines
        
    def find_matches(self, station: pd.Series) -> pd.DataFrame:
        """
        Find potential matches for a station in existing database.
        
        Args:
            station: Series containing at least:
                - stop_name
                - type
                - line_name
                
        Returns:
            DataFrame of matching stations with confidence scores
        """
        # First try exact name + type match
        name_type_matches = self.existing_stations[
            (self.existing_stations['stop_name'] == station['stop_name']) &
            (self.existing_stations['type'] == station['type'])
        ].copy()
        
        if not name_type_matches.empty:
            # For these matches, check line overlap
            name_type_matches.loc[:, 'has_line'] = name_type_matches['in_lines'].apply(
                lambda lines: self._line_match(station['line_name'], lines)
            )
            
            # Get matches with line overlap first
            line_matches = name_type_matches[name_type_matches['has_line']]
            if not line_matches.empty:
                return line_matches
            
            # If no line matches, return name+type matches
            return name_type_matches
            
        # If no name+type matches, try just name matches
        name_matches = self.existing_stations[
            self.existing_stations['stop_name'] == station['stop_name']
        ].copy()
        
        if not name_matches.empty:
            name_matches.loc[:, 'has_line'] = name_matches['in_lines'].apply(
                lambda lines: self._line_match(station['line_name'], lines)
            )
            line_matches = name_matches[name_matches['has_line']]
            if not line_matches.empty:
                return line_matches
                
            return name_matches
            
        return pd.DataFrame()  # No matches found
        
    def add_location_data(self, stops_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add location data to stops dataframe from existing stations.
        
        Args:
            stops_df: DataFrame containing stops to process
            
        Returns:
            DataFrame with added location data where matches found
        """
        result_df = stops_df.copy()
        match_count = 0
        total_stops = len(result_df)
        
        # Initialize location and identifier columns with None
        result_df['location'] = None
        result_df['identifier'] = None
        
        for idx, row in result_df.iterrows():
            matches = self.find_matches(row)
            if not matches.empty:
                best_match = matches.iloc[0]
                # Only count as match if location exists
                if pd.notna(best_match['location']):
                    match_count += 1
                    result_df.loc[idx, 'location'] = best_match['location']
                    result_df.loc[idx, 'identifier'] = best_match['identifier']
                    if 'has_line' in matches.columns and not best_match['has_line']:
                        logger.warning(
                            f"Matched station {row['stop_name']} by name/type only, "
                            f"line {row['line_name']} not found in existing lines"
                        )
            else:
                logger.info(f"No match found for station: {row['stop_name']}")
                
        logger.info(f"Successfully matched {match_count} out of {total_stops} stations")
        
        return result_df

def validate_matches(matched_df: pd.DataFrame) -> None:
    """Validate matches and print statistics."""
    total = len(matched_df)
    matched = matched_df['location'].notna().sum()
    unmatched = total - matched
    
    print("\nMatching Statistics:")
    print(f"Total stations: {total}")
    print(f"Matched: {matched} ({matched/total*100:.1f}%)")
    print(f"Unmatched: {unmatched} ({unmatched/total*100:.1f}%)")
    
    # Display sample of unmatched stations
    print("\nSample of unmatched stations:")
    print(matched_df[matched_df['location'].isna()]['stop_name'].head())
