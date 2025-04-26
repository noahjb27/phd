import pandas as pd
import os
import re
from collections import defaultdict

# Create output directory if it doesn't exist
output_dir = "./data/raw"
os.makedirs(output_dir, exist_ok=True)

# 1. Load the combined CSV files
stations_df = pd.read_csv("legacy_data/stations.csv")
lines_df = pd.read_csv("legacy_data/lines.csv")
line_stops_df = pd.read_csv("legacy_data/line_stops.csv")

# 2. Normalize transport types
def normalize_type(transport_type, line_name=None):
    """Normalize the transport type terminology."""
    # Check line_name pattern first if provided
    if line_name is not None:
        # If line_name starts with O followed by a number, it's omnibus
        if re.match(r'^O\d+', str(line_name)):
            return 'omnibus'
        
        # If line_name starts with A followed by a number, it's autobus
        if re.match(r'^A\d+', str(line_name)) or re.match(r'^AS\d+', str(line_name)):
            return 'autobus'
        
        # KBS prefixes are for s-bahn
        if isinstance(line_name, str) and line_name.startswith('KBS'):
            return 's-bahn'
    
    if not isinstance(transport_type, str):
        return 'unknown'
        
    transport_type = transport_type.lower()
    
    # Handle omnibus, bus, autobus variations
    if transport_type in ['omnibus', 'autobus', 'bus']:
        return 'autobus'
    
    # Handle strassenbahn, tram
    if transport_type in ['strassenbahn', 'tram']:
        return 'tram'
    
    # Other types remain the same (s-bahn, u-bahn, ferry)
    return transport_type

# Apply transport type normalization based on both the type field and line_name
lines_df['type'] = [normalize_type(row['type'], row['line_name']) for _, row in lines_df.iterrows()]
stations_df['type'] = stations_df['type'].apply(lambda x: normalize_type(x))

# 3. Normalize east/west terminology
def normalize_side(side, year):
    """Normalize the east/west terminology with year consideration."""
    if not isinstance(side, str):
        # For post-1961, use 'ambiguous' instead of 'unified'
        return 'ambiguous' if year >= 1961 else 'unified'
        
    side = side.lower()
    
    if side in ['ost', 'east']:
        return 'east'
    elif side in ['west']:
        return 'west'
    elif side in ['both/unkown', 'both', 'unknown', 'unified']:
        # For post-1961, use 'ambiguous' instead of 'unified'
        return 'ambiguous' if year >= 1961 else 'unified'
    
    # Default case - consider year
    return 'ambiguous' if year >= 1961 else 'unified'

# Apply side normalization with year consideration
lines_df['east_west'] = lines_df.apply(lambda row: normalize_side(row['east_west'], row['year']), axis=1)

# Additional check: Look for "Ost" or "West" in line_name/stop data for context clues
def infer_side_from_line_data(row):
    """Try to infer east/west from line data if current side is unified/ambiguous"""
    if row['east_west'] not in ['unified', 'ambiguous']:
        return row['east_west']
        
    # Check line name for Ost/West indicators
    if isinstance(row['line_name'], str):
        if 'ost' in row['line_name'].lower() or 'east' in row['line_name'].lower():
            return 'east'
        if 'west' in row['line_name'].lower():
            return 'west'
    
    # Check start_stop for Ost/West indicators
    if isinstance(row['start_stop'], str):
        if 'ost' in row['start_stop'].lower() or 'east' in row['start_stop'].lower():
            return 'east'
        if 'west' in row['start_stop'].lower():
            return 'west'
            
    # Return original value (either 'unified' or 'ambiguous')
    return row['east_west']

# Apply side inference where possible
lines_df['east_west'] = lines_df.apply(infer_side_from_line_data, axis=1)

# 4. Set pre-1961 data as unified (keep ambiguous for post-1961)
lines_df.loc[lines_df['year'] < 1961, 'east_west'] = 'unified'

# 5. Check if the line_name needs type correction 
def check_line_type_from_name(line_name, current_type):
    """Check if the line name suggests a different transport type"""
    if not isinstance(line_name, str):
        return current_type
        
    # If line_name starts with O followed by a number, it's omnibus
    if re.match(r'^O\d+', line_name):
        return 'omnibus'
    
    # If line_name starts with A followed by a number, it's autobus
    if re.match(r'^A\d+', line_name) or re.match(r'^AS\d+', line_name):
        return 'autobus'
        
    # KBS prefixes are for s-bahn
    if line_name.startswith('KBS'):
        return 's-bahn'
    
    return current_type

# Apply additional line name-based type correction
lines_df['type'] = [check_line_type_from_name(row['line_name'], row['type']) 
                    for _, row in lines_df.iterrows()]

# 6. Group data by year and side
years = sorted(lines_df['year'].unique())

for year in years:
    # For each year, identify sides (east, west, unified, or ambiguous)
    year_data = lines_df[lines_df['year'] == year]
    sides = year_data['east_west'].unique()
    
    for side in sides:
        # Skip invalid sides
        if not isinstance(side, str):
            continue
            
        # Get lines for this year and side
        side_lines = year_data[year_data['east_west'] == side]
        
        # Prepare the output dataframe
        output_data = []
        
        # Process each line
        for _, line in side_lines.iterrows():
            line_id = line['line_id']
            line_name = line['line_name']
            
            # Get all stops for this line and order them
            line_stops = line_stops_df[line_stops_df['line_id'] == line_id].sort_values('stop_order')
            
            # If we have stop data, format it as a string
            if not line_stops.empty:
                stops_list = line_stops['stop_name'].tolist()
                stops_str = " - ".join(stops_list)
            else:
                # If no specific stops, use the start_stop field if available
                stops_str = line['start_stop'] if isinstance(line['start_stop'], str) else ""
            
            # Final type check based on line_name pattern
            line_type = check_line_type_from_name(line_name, line['type'])
            
            # Build the output row
            output_row = {
                'line_name': line_name,
                'type': line_type,
                'stops': stops_str,
                'frequency (7:30)': line['Frequency'] if not pd.isna(line['Frequency']) else '',
                'length (time)': line['Length (time)'] if not pd.isna(line['Length (time)']) else '',
                'Length (km)': line['Length (km)'] if not pd.isna(line['Length (km)']) else '',  # Match exact column name
                'year': year,
                'east_west': side,
                'info': ''  # No direct mapping for additional info
            }
            
            output_data.append(output_row)
        
        # Create the output dataframe
        if output_data:
            output_df = pd.DataFrame(output_data)
            
            # Ensure the columns are in the correct order to match your existing files
            column_order = [
                'line_name', 
                'type', 
                'stops', 
                'frequency (7:30)', 
                'length (time)', 
                'Length (km)', 
                'year', 
                'east_west', 
                'info'
            ]
            
            # Reorder columns and handle missing columns
            for col in column_order:
                if col not in output_df.columns:
                    output_df[col] = ''
            
            output_df = output_df[column_order]
            
            # Save to CSV (with UTF-8 BOM to match your existing files)
            filename = f"{year}_{side}.csv"
            filepath = os.path.join(output_dir, filename)
            output_df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"Created {filepath} with {len(output_data)} lines")

print("Data migration complete!")