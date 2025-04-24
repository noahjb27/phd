"""
Functions for loading and processing Berlin transport data from raw CSV files.
"""

import pandas as pd
import logging
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class DataLoader:
    """Handles loading and initial cleaning of raw transport data."""
    
    EXPECTED_COLUMNS = [
        'line_name', 'type', 'stops', 'frequency (7:30)', 
        'length (time)', 'length (km)', 'year', 
        'east_west', 'info'
    ]
    
    def __init__(self):
        """Initialize the data loader."""
        self.raw_df = None
        
    def load_raw_data(self, file_path: str) -> pd.DataFrame:
        """
        Load raw CSV data with proper handling of delimiters and encoding.
        
        Args:
            file_path: Path to raw CSV file
            
        Returns:
            Cleaned DataFrame
        """
        try:
            # First try standard CSV reading
            self.raw_df = pd.read_csv(
                file_path,
                encoding='utf-8',
                dtype={
                    'line_name': str,
                    'type': str,
                    'stops': str,
                    'frequency (7:30)': float,
                    'length (time)': float,
                    'length (km)': float,
                    'year': int,
                    'east_west': str,
                    'info': str
                }
            )
        except (pd.errors.ParserError, UnicodeDecodeError):
            # If that fails, try with different parameters
            self.raw_df = pd.read_csv(
                file_path,
                encoding='utf-8',
                sep=None,  # Let pandas detect separator
                engine='python',
                dtype=str  # Read everything as string first
            )
            
        # Clean up column names
        self.raw_df.columns = [col.strip().lower() for col in self.raw_df.columns]
        
        # Check for expected columns
        missing_cols = set(self.EXPECTED_COLUMNS) - set(self.raw_df.columns)
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}")
            # Add missing columns with NaN values
            for col in missing_cols:
                self.raw_df[col] = np.nan
                
        # Convert numeric columns
        self._convert_numeric_columns()
        
        # Clean string columns
        self._clean_string_columns()
        
        return self.raw_df
        
    def _convert_numeric_columns(self) -> None:
        """Convert numeric columns to appropriate types."""
        # Convert frequency and length columns
        numeric_cols = ['frequency (7:30)', 'length (time)', 'length (km)']
        for col in numeric_cols:
            try:
                self.raw_df[col] = pd.to_numeric(self.raw_df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Error converting {col} to numeric: {e}")
                
        # Convert year to int
        try:
            self.raw_df['year'] = self.raw_df['year'].astype(int)
        except Exception as e:
            logger.warning(f"Error converting year to int: {e}")
            
    def _clean_string_columns(self) -> None:
        """Clean string columns by removing whitespace and standardizing format."""
        string_cols = ['line_name', 'type', 'stops', 'east_west', 'info']
        for col in string_cols:
            self.raw_df[col] = self.raw_df[col].astype(str).str.strip()
            
        # Special cleaning for stops column
        self.raw_df['stops'] = self.raw_df['stops'].apply(self._clean_stops)
            
    def _clean_stops(self, stops: str) -> str:
        """Clean stops string by standardizing separators and whitespace."""
        if pd.isna(stops):
            return ""
            
        stops = str(stops)
        # Standardize various dash types
        stops = stops.replace('–', '-')  # en dash
        stops = stops.replace('—', '-')  # em dash
        
        # Fix spacing around dashes
        stops = stops.replace(' - ', ' - ')
        stops = stops.replace('  ', ' ')
        
        return stops.strip()
        
def format_line_list(line_name: str) -> str:
    """
    Format line name into proper list string format.
    
    Args:
        line_name: Raw line name/number
        
    Returns:
        Properly formatted line list string
    """
    if pd.isna(line_name):
        return "[]"
        
    # Clean the line name
    line_name = str(line_name).strip()
    
    # If it's already a list string, return as is
    if line_name.startswith('[') and line_name.endswith(']'):
        return line_name
        
    # Split on comma if multiple lines
    if ',' in line_name:
        lines = [l.strip() for l in line_name.split(',')]
    else:
        lines = [line_name]
        
    # Format as list string
    return str(lines)

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create loader
    loader = DataLoader()
    
    # Load sample data
    df = loader.load_raw_data("sample_data.csv")
    print("\nLoaded DataFrame:")
    print(df.head())
    
    # Example line list formatting
    sample_lines = ["A53", "A34,A35", "KBS 106a,KBS 103,KBS 103a"]
    print("\nLine list formatting examples:")
    for line in sample_lines:
        print(f"Raw: {line}")
        print(f"Formatted: {format_line_list(line)}\n")