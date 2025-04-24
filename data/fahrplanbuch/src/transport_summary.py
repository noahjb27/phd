"""
Generate summary files from year-by-year transport data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Set
import logging
from datetime import datetime

class TransportSummaryGenerator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the summary generation process."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler('summary_generation.log')
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(formatter)
        f_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)
        
    def load_year_data(self, year: int, side: str) -> Dict[str, pd.DataFrame]:
        """Load all data files for a specific year and side."""
        files = {
            'stations': f'stops_{year}_{side}_enriched.csv',
            'lines': f'lines_{year}_{side}_enriched.csv',
            'connections': f'connections_{year}_{side}.csv'
        }
        
        data = {}
        for key, filename in files.items():
            try:
                filepath = self.data_dir / filename
                data[key] = pd.read_csv(filepath)
                self.logger.info(f"Loaded {key} data for {year} {side}")
            except FileNotFoundError:
                self.logger.warning(f"Missing file: {filename}")
                data[key] = None
                
        return data
        
    def generate_station_summary(self, years: List[int], sides: List[str]) -> pd.DataFrame:
        """
        Generate a comprehensive station summary across all years.
        
        Returns DataFrame with columns:
        - stop_id: Unique identifier
        - name: Station name
        - type: Transport type
        - location: Coordinates
        - postal_code: Postal code
        - district: District name
        - neighborhood: Neighborhood name
        - east_west: East/West classification
        - years_active: List of years the station was active
        - lines_by_year: Dictionary of years to line lists
        - first_appearance: First year the station appears
        - last_appearance: Last year the station appears
        - consistent_location: Whether location stayed constant
        - location_changes: List of years where location changed
        - name_changes: List of years where name changed
        """
        all_stations = []
        station_history = {}
        
        # First pass: collect all station data
        for year in years:
            for side in sides:
                data = self.load_year_data(year, side)
                if data['stations'] is not None:
                    stations_df = data['stations']
                    
                    for _, station in stations_df.iterrows():
                        station_id = station['stop_id']
                        if station_id not in station_history:
                            station_history[station_id] = {
                                'years': set(),
                                'locations': {},
                                'names': {},
                                'lines': {},
                                'latest_data': None
                            }
                        
                        history = station_history[station_id]
                        history['years'].add(year)
                        history['locations'][year] = station['location']
                        history['names'][year] = station['stop_name']
                        history['lines'][year] = station['in_lines']
                        history['latest_data'] = station
                        
        # Second pass: create summary records
        for station_id, history in station_history.items():
            latest = history['latest_data']
            
            # Check for location and name changes
            location_changes = []
            name_changes = []
            prev_loc = None
            prev_name = None
            
            for year in sorted(history['years']):
                curr_loc = history['locations'][year]
                curr_name = history['names'][year]
                
                if prev_loc is not None and curr_loc != prev_loc:
                    location_changes.append(year)
                if prev_name is not None and curr_name != prev_name:
                    name_changes.append(year)
                    
                prev_loc = curr_loc
                prev_name = curr_name
                
            summary = {
                'stop_id': station_id,
                'name': latest['stop_name'],
                'type': latest['type'],
                'location': latest['location'],
                'postal_code': latest.get('postal_code', None),
                'district': latest.get('district', None),
                'neighborhood': latest.get('neighborhood', None),
                'east_west': latest.get('east_west', None),
                'years_active': sorted(list(history['years'])),
                'lines_by_year': history['lines'],
                'first_appearance': min(history['years']),
                'last_appearance': max(history['years']),
                'consistent_location': len(location_changes) == 0,
                'location_changes': location_changes,
                'name_changes': name_changes,
                'total_years_active': len(history['years'])
            }
            
            all_stations.append(summary)
            
        # Create DataFrame and sort by first appearance
        summary_df = pd.DataFrame(all_stations)
        summary_df.sort_values('first_appearance', inplace=True)
        
        self.logger.info(f"Generated summary for {len(summary_df)} stations")
        return summary_df
        
    def generate_line_summary(self, years: List[int], sides: List[str]) -> pd.DataFrame:
        """
        Generate a comprehensive line summary across all years.
        
        Returns DataFrame with columns:
        - line_id: Unique identifier
        - name: Line name
        - type: Transport type
        - east_west: East/West classification
        - years_active: List of years the line was active
        - stations_by_year: Dictionary of years to station lists
        - first_appearance: First year the line appears
        - last_appearance: Last year the line appears
        - avg_frequency: Average service frequency
        - avg_capacity: Average capacity
        - route_changes: List of years where route changed
        - capacity_changes: List of years where capacity changed
        """
        all_lines = []
        line_history = {}
        
        # First pass: collect all line data
        for year in years:
            for side in sides:
                data = self.load_year_data(year, side)
                if data['lines'] is not None and data['stations'] is not None:
                    lines_df = data['lines']
                    stations_df = data['stations']
                    
                    for _, line in lines_df.iterrows():
                        line_id = line['line_id']
                        if line_id not in line_history:
                            line_history[line_id] = {
                                'years': set(),
                                'stations': {},
                                'frequencies': {},
                                'capacities': {},
                                'latest_data': None
                            }
                        
                        history = line_history[line_id]
                        history['years'].add(year)
                        
                        # Get stations for this line
                        line_stations = stations_df[
                            stations_df['in_lines'].str.contains(str(line['line_name']), na=False)
                        ]['stop_id'].tolist()
                        
                        history['stations'][year] = line_stations
                        history['frequencies'][year] = line['Frequency']
                        history['capacities'][year] = line.get('capacity', None)
                        history['latest_data'] = line
                        
        # Second pass: create summary records
        for line_id, history in line_history.items():
            latest = history['latest_data']
            
            # Check for route changes
            route_changes = []
            capacity_changes = []
            prev_stations = None
            prev_capacity = None
            
            for year in sorted(history['years']):
                curr_stations = set(history['stations'][year])
                curr_capacity = history['capacities'][year]
                
                if prev_stations is not None and curr_stations != prev_stations:
                    route_changes.append(year)
                if prev_capacity is not None and curr_capacity != prev_capacity:
                    capacity_changes.append(year)
                    
                prev_stations = curr_stations
                prev_capacity = curr_capacity
                
            summary = {
                'line_id': line_id,
                'name': latest['line_name'],
                'type': latest['type'],
                'east_west': latest.get('east_west', None),
                'years_active': sorted(list(history['years'])),
                'stations_by_year': history['stations'],
                'first_appearance': min(history['years']),
                'last_appearance': max(history['years']),
                'avg_frequency': np.mean(list(history['frequencies'].values())),
                'avg_capacity': np.mean([c for c in history['capacities'].values() if c is not None]),
                'route_changes': route_changes,
                'capacity_changes': capacity_changes,
                'total_years_active': len(history['years'])
            }
            
            all_lines.append(summary)
            
        # Create DataFrame and sort by first appearance
        summary_df = pd.DataFrame(all_lines)
        summary_df.sort_values('first_appearance', inplace=True)
        
        self.logger.info(f"Generated summary for {len(summary_df)} lines")
        return summary_df
        
    def save_summaries(self, output_dir: Path = None):
        """Generate and save all summary files."""
        if output_dir is None:
            output_dir = self.data_dir / 'summaries'
            
        output_dir.mkdir(exist_ok=True)
        
        # Define years and sides
        years = range(1945, 1990)
        sides = ['east', 'west']
        
        # Generate summaries
        station_summary = self.generate_station_summary(years, sides)
        line_summary = self.generate_line_summary(years, sides)
        
        # Save files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        station_summary.to_csv(output_dir / f'station_summary_{timestamp}.csv', index=False)
        line_summary.to_csv(output_dir / f'line_summary_{timestamp}.csv', index=False)
        
        # Generate statistics report
        stats = {
            'total_stations': len(station_summary),
            'total_lines': len(line_summary),
            'stations_with_changes': len(station_summary[station_summary['location_changes'].str.len() > 0]),
            'lines_with_changes': len(line_summary[line_summary['route_changes'].str.len() > 0]),
            'avg_station_lifetime': station_summary['total_years_active'].mean(),
            'avg_line_lifetime': line_summary['total_years_active'].mean()
        }
        
        with open(output_dir / f'summary_stats_{timestamp}.txt', 'w') as f:
            for key, value in stats.items():
                f.write(f"{key}: {value}\n")
                
        self.logger.info(f"Saved summaries to {output_dir}")
        return station_summary, line_summary, stats

# Example usage:
if __name__ == "__main__":
    data_dir = Path('../data')
    generator = TransportSummaryGenerator(data_dir)
    station_summary, line_summary, stats = generator.save_summaries()
    
    print("\nSummary Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")