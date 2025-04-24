import pandas as pd
import numpy as np
from typing import List

class DataValidator:
    """Validates processed transport data for common issues."""
    
    @staticmethod
    def validate_line_continuity(line_stops_df: pd.DataFrame) -> List[dict]:
        """Check for gaps in stop sequences."""
        issues = []
        
        for line_id in line_stops_df['line_id'].unique():
            line_stops = line_stops_df[line_stops_df['line_id'] == line_id].sort_values('stop_order')
            
            # Check for missing stop orders
            stop_orders = line_stops['stop_order'].values
            expected_orders = np.arange(stop_orders.min(), stop_orders.max() + 1)
            
            missing = set(expected_orders) - set(stop_orders)
            if missing:
                issues.append({
                    'line_id': line_id,
                    'issue': 'Gap in stop sequence',
                    'missing_orders': sorted(missing)
                })
                
        return issues
    
    @staticmethod
    def validate_terminal_stations(line_df: pd.DataFrame, line_stops_df: pd.DataFrame) -> List[dict]:
        """Verify terminal stations match Fahrplanbuch data."""
        issues = []
        
        for _, line in line_df.iterrows():
            stops = line_stops_df[line_stops_df['line_id'] == line['line_id']].sort_values('stop_order')
            
            if stops.empty:
                continue
                
            start_stop, end_stop = line['start_stop'].split('<>')
            start_stop = start_stop.strip()
            end_stop = end_stop.strip()
            
            if stops.iloc[0]['stop_name'] != start_stop:
                issues.append({
                    'line_id': line['line_id'],
                    'issue': 'First stop mismatch',
                    'expected': start_stop,
                    'found': stops.iloc[0]['stop_name']
                })
                
            if stops.iloc[-1]['stop_name'] != end_stop:
                issues.append({
                    'line_id': line['line_id'],
                    'issue': 'Last stop mismatch',
                    'expected': end_stop,
                    'found': stops.iloc[-1]['stop_name']
                })
                
        return issues
