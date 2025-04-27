# Filename: df_station_matcher.py

import logging
import pandas as pd
from neo4j import GraphDatabase
from fuzzywuzzy import process, fuzz
from typing import Optional, Dict, List

class DataFrameStationMatcher:
    """
    Matches stations from new data against historical station data fetched once 
    from Neo4j, using fuzzy matching on names and requiring matching type and line name.
    Matches against the single closest previous year for the specified side (east/west).
    """
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize matcher with Neo4j database connection details.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.logger = logging.getLogger(__name__)
        self.historical_stations_df = pd.DataFrame() # To store fetched historical data

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed.")

    def _fetch_historical_stations(self, current_year: int, side: str) -> bool:
        """
        Fetches station data (including associated line names) from the closest year 
        prior to current_year for the specified side (east/west) and stores it 
        in self.historical_stations_df.

        Args:
            current_year: The year currently being processed.
            side: The side ('east' or 'west') being processed.

        Returns:
            True if historical data was successfully fetched, False otherwise.
        """
        self.historical_stations_df = pd.DataFrame() # Reset
        target_year = None

        # 1. Find the closest previous year with data for the given side
        find_year_query = """
        MATCH (s:Station {east_west: $side})-[:IN_YEAR]->(y:Year)
        WHERE y.year > $current_year
        RETURN max(y.year) as target_year
        """
        try:
            with self.driver.session() as session:
                result = session.run(find_year_query, side=side, current_year=current_year)
                record = result.single()
                if record and record["target_year"] is not None:
                    target_year = record["target_year"]
                    self.logger.info(f"Found closest previous year with data for side '{side}': {target_year}")
                else:
                    self.logger.warning(f"No previous year found with data for side '{side}' before {current_year}.")
                    return False
        except Exception as e:
            self.logger.error(f"Error finding target year: {e}")
            return False

        # 2. Fetch all stations from that target year and side, INCLUDING associated line names
        fetch_stations_query = """
        MATCH (s:Station {east_west: $side})-[:IN_YEAR]->(y:Year {year: $target_year})
        WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL // Only fetch stations with coordinates
        OPTIONAL MATCH (l:Line)-[:SERVES]->(s)-[:IN_YEAR]->(y) // Match lines serving the station in that year
        WITH s, y, collect(DISTINCT l.name) as historical_lines // Collect associated line names
        RETURN s.stop_id as stop_id, 
               s.name as name, 
               s.type as type, 
               s.latitude as latitude, 
               s.longitude as longitude,
               historical_lines // Return the list of line names
        // Add s.identifier if/when available and needed: , s.identifier as identifier
        """
        try:
            with self.driver.session() as session:
                result = session.run(fetch_stations_query, side=side, target_year=target_year)
                records = result.data()
                if records:
                    self.historical_stations_df = pd.DataFrame(records)
                    # Add a combined location string for convenience if needed later
                    self.historical_stations_df['location'] = self.historical_stations_df.apply(
                        lambda row: f"{row['latitude']},{row['longitude']}", axis=1
                    )
                    self.logger.info(f"Fetched {len(self.historical_stations_df)} historical stations (with lines) from year {target_year} for side '{side}'.")
                    # Log a sample row to verify 'historical_lines' content
                    if not self.historical_stations_df.empty:
                         self.logger.debug(f"Sample historical data row: {self.historical_stations_df.iloc[0].to_dict()}")
                    return True
                else:
                    self.logger.warning(f"No stations found for year {target_year}, side '{side}'.")
                    return False
        except Exception as e:
            self.logger.error(f"Error fetching stations for year {target_year}: {e}")
            return False

    def add_location_data(self, stops_df: pd.DataFrame, current_year: int, side: str, score_cutoff: int = 90) -> pd.DataFrame:
        """
        Adds location data to the stops dataframe by matching type, line_name, 
        and fuzzy matching names against historical data from the closest 
        previous year for the specified side.

        Args:
            stops_df: DataFrame containing stops for the current year to process. 
                      Must include 'stop_name', 'type', and 'line_name' columns.
            current_year: The year currently being processed.
            side: The side ('east' or 'west') being processed.
            score_cutoff: The minimum fuzzy matching score (0-100) to consider a match.

        Returns:
            DataFrame with added location data ('latitude', 'longitude', 'location', 'match_score', 'matched_name', 'matched_stop_id').
        """
        # Fetch historical data if not already done or if it's empty
        if self.historical_stations_df.empty:
             if not self._fetch_historical_stations(current_year, side):
                 self.logger.warning("Could not fetch historical data. Cannot perform matching.")
                 # Return df with empty columns added if they don't exist
                 for col in ['latitude', 'longitude', 'location', 'match_score', 'matched_name', 'matched_stop_id', 'matched_historical_lines']:
                     if col not in stops_df.columns:
                         stops_df[col] = None
                 return stops_df

        result_df = stops_df.copy()
        match_count = 0
        total_stops = len(result_df)

        # Initialize output columns if they don't exist
        for col in ['latitude', 'longitude', 'location', 'match_score', 'matched_name', 'matched_stop_id', 'matched_historical_lines']:
            if col not in result_df.columns:
                 result_df[col] = None
        
        # Ensure required columns are present in historical data
        if self.historical_stations_df.empty or not all(col in self.historical_stations_df.columns for col in ['name', 'type', 'latitude', 'longitude', 'location', 'stop_id', 'historical_lines']):
             self.logger.error("Historical stations DataFrame is missing required columns (incl. 'historical_lines'). Cannot perform matching.")
             return result_df
             
        # Ensure required columns are present in the input DataFrame
        if not all(col in result_df.columns for col in ['stop_name', 'type', 'line_name']):
            self.logger.error("Input stops DataFrame is missing required columns ('stop_name', 'type', 'line_name'). Cannot perform matching.")
            return result_df


        # Iterate through the stops that need matching
        for idx, row in result_df.iterrows():
            target_name = row['stop_name']
            target_type = row['type']
            target_line_name = row['line_name'] # Get the line name from the current data

            # Filter historical data by station type first
            candidates_df = self.historical_stations_df[self.historical_stations_df['type'] == target_type].copy() # Use .copy() to avoid SettingWithCopyWarning
            
            if candidates_df.empty:
                self.logger.debug(f"No historical candidates found for type '{target_type}' for station '{target_name}'")
                continue

            # Perform fuzzy matching on names within the filtered candidates
            match_result = process.extractOne(
                target_name, 
                candidates_df['name'], 
                scorer=fuzz.WRatio, # WRatio often works well for variations
                score_cutoff=score_cutoff
            )

            if match_result:
                matched_name_fuzzy, score, original_index = match_result
                
                # Get the full data for the potential matched station
                potential_match_data = candidates_df.loc[original_index]

                # --- ADDED CHECK: Verify if the target_line_name matches the historical lines ---
                historical_lines_list = potential_match_data['historical_lines']
                if isinstance(historical_lines_list, list) and target_line_name in historical_lines_list:
                    # Line name match successful! Accept the match.
                    
                    # Add matched data to the result DataFrame
                    result_df.loc[idx, 'latitude'] = potential_match_data['latitude']
                    result_df.loc[idx, 'longitude'] = potential_match_data['longitude']
                    result_df.loc[idx, 'location'] = potential_match_data['location']
                    result_df.loc[idx, 'match_score'] = score
                    result_df.loc[idx, 'matched_name'] = potential_match_data['name'] # Name from historical data
                    result_df.loc[idx, 'matched_stop_id'] = potential_match_data['stop_id']
                    result_df.loc[idx, 'matched_historical_lines'] = historical_lines_list # Store the list of lines for reference
                    
                    match_count += 1
                    self.logger.debug(f"Matched '{target_name}' ({target_type}, Line: {target_line_name}) -> '{potential_match_data['name']}' ({potential_match_data['type']}, Lines: {historical_lines_list}) with score {score}")
                
                else:
                    # Fuzzy name and type matched, but the line name did not match.
                    self.logger.info(f"Partial match (name/type ok, score={score}) but line mismatch for: '{target_name}' ({target_type}, Line: {target_line_name}). Historical lines: {historical_lines_list}")
            
            else:
                # No fuzzy name match found above the cutoff
                self.logger.info(f"No fuzzy name match found (cutoff={score_cutoff}) for station: '{target_name}' ({target_type}, Line: {target_line_name})")

        self.logger.info(f"Successfully matched {match_count} out of {total_stops} stations using fuzzy name, type, and line matching.")
        
        # Fill NaNs in location string col based on lat/lon cols if needed
        result_df['location'] = result_df.apply(
             lambda x: f"{x['latitude']},{x['longitude']}" if pd.notna(x['latitude']) and pd.notna(x['longitude']) and pd.isna(x['location']) else x['location'],
             axis=1
        )

        return result_df