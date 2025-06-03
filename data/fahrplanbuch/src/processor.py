# processor.py

import pandas as pd
import logging
from typing import Dict, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class TransportDataProcessor:
    """Main class coordinating the processing of transport data."""
    
    def __init__(self, year: int, side: str):
        """
        Initialize processor for a specific year and side of Berlin.
        
        Args:
            year: The year of the data
            side: Either 'east' or 'west'
        """
        self.year = year
        self.side = side.lower()
        if self.side not in ['east', 'west', 'unified']:
            raise ValueError("side must be either 'east' or 'west'")
    
    def process_raw_data(self, 
                        input_data: Union[str, Path, pd.DataFrame], 
                        existing_stations: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
        """
        Process raw Fahrplanbuch data into standardized tables.
        
        Args:
            input_data: Either a path to CSV file or a pandas DataFrame
            existing_stations: DataFrame of existing station data (optional)
            
        Returns:
            Dictionary containing processed dataframes
        """
        try:
            # Handle input data
            if isinstance(input_data, (str, Path)):
                df = pd.read_csv(input_data)
                logger.info(f"Loaded data from file: {input_data}")
            elif isinstance(input_data, pd.DataFrame):
                df = input_data.copy()
                logger.info("Using provided DataFrame")
            else:
                raise TypeError("input_data must be either a file path or DataFrame")
            
            # Clean data
            df = self._clean_line_data(df)
            
            # Create basic tables
            line_df = self._create_line_table(df)
            stops_df = self._create_stops_table(df)
            
            logger.info(f"Created tables: lines ({len(line_df)} rows), "
                    f"stops ({len(stops_df)} rows), ")
            
            return {
                'lines': line_df,
                'stops': stops_df
            }
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise
    
    def _clean_line_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize raw line data."""
        df = df.copy()
        
        # Clean string columns
        string_cols = ['line_name', 'type', 'stops', 'east_west']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Clean numeric columns
        df['year'] = self.year
        df['frequency (7:30)'] = pd.to_numeric(df['frequency (7:30)'], errors='coerce').fillna(0)
        df['length (time)'] = pd.to_numeric(df['length (time)'], errors='coerce').fillna(0)
        
        return df
    
    def _create_line_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create standardized line table."""
        def extract_terminals(stops: str) -> str:
            stations = stops.split(' - ')
            return f"{stations[0]}<> {stations[-1]}"
            
        # Create line IDs
        line_ids = [f"{self.year}{i}" for i in range(1, len(df) + 1)]
        
        line_df = pd.DataFrame({
            'line_id': line_ids,
            'year': self.year,
            'line_name': df['line_name'],
            'type': df['type'],
            'start_stop': df['stops'].apply(extract_terminals),
            'length (time)': df['length (time)'],
            'length (km)': df['length (km)'] if 'length (km)' in df.columns else None,
            'east_west': df['east_west'],
            'frequency (7:30)': df['frequency (7:30)']
        })

        return line_df
    
    def _create_stops_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create stops table with unique stations."""
        # Split stops into individual stations
        all_stops = []
        for idx, row in df.iterrows():
            stops = row['stops'].split(' - ')
            for stop in stops:
                all_stops.append({
                    'stop_name': stop.strip(),
                    'type': row['type'],
                    'line_name': row['line_name']
                })
        
        stops_df = pd.DataFrame(all_stops)
        
        # Remove duplicates keeping first occurrence
        stops_df = stops_df.drop_duplicates(subset=['stop_name', 'type', 'line_name'])
        
        # Add stop IDs
        stops_df['stop_id'] = [f"{self.year}{i}_{self.side}" for i in range(len(stops_df))]
        
        # Initialize location and identifier columns
        stops_df['location'] = ''
        stops_df['identifier'] = ''
        
        return stops_df