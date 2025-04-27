import os
import re
import pandas as pd
import glob

def standardize_station_name(name):
    """
    Standardize German station names for consistency.
    Handles various spacing and capitalization patterns.
    
    Args:
        name: Original station name
        
    Returns:
        Standardized station name
    """
    if pd.isna(name) or name == '':
        return ''
    
    # Store original capitalization for later restoration
    has_capital = name[0].isupper() if name else False
    
    # Convert to lowercase for processing
    name = name.lower()
    
    # Handle compound "straße/strasse" (both with and without spaces, including hyphenated cases)
    # This matches "Tempelhofer Strasse", "Tempelhoferstrasse", and "Tempelhofer-Strasse"
    name = re.sub(r'([a-zäöüß]+)er\s*stra(?:ss|ß)e\b', r'\1erstr.', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*stra(?:ss|ß)e\b', r'\1str.', name)      # Non-adjective forms
    name = re.sub(r'([a-zäöüß]+)-([a-zäöüß]+)-stra(?:ss|ß)e\b', r'\1-\2-str.', name)  # Hyphenated forms
    
    # Compound "damm" variants (both with and without spaces)
    name = re.sub(r'([a-zäöüß]+)er\s*damm\b', r'\1erdamm', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*damm\b', r'\1damm', name)      # Non-adjective forms
    
    # Compound "platz" variants (both with and without spaces)
    name = re.sub(r'([a-zäöüß]+)er\s*platz\b', r'\1erplatz', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*platz\b', r'\1platz', name)      # Non-adjective forms
    
    # Compound "allee" variants (both with and without spaces)
    name = re.sub(r'([a-zäöüß]+)e\s*allee\b', r'\1eallee', name)    # With "e" ending like Märkische
    name = re.sub(r'([a-zäöüß]+)er\s*allee\b', r'\1erallee', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*allee\b', r'\1allee', name)      # Non-adjective forms
    
    # Compound "chaussee" variants (both with and without spaces)
    name = re.sub(r'([a-zäöüß]+)er\s*chaussee\b', r'\1erchaussee', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*chaussee\b', r'\1chaussee', name)      # Non-adjective forms
    
    # Compound "weg" variants (both with and without spaces)
    name = re.sub(r'([a-zäöüß]+)er\s*weg\b', r'\1erweg', name)  # Adjective forms
    name = re.sub(r'([a-zäöüß]+)\s*weg\b', r'\1weg', name)      # Non-adjective forms
    
    # Final cleanup
    name = name.strip()
    
    # Restore initial capitalization
    if has_capital and name:
        name = name[0].upper() + name[1:]
    
    # Recapitalize 'B' in 'bhf.'
    name = re.sub(r'\bbhf\.', 'Bhf.', name)
    
    # Capitalize the first letter after '-' and after a whitespace
    name = re.sub(r'(?<=\s|-)([a-zäöüß])', lambda match: match.group(1).upper(), name)
    return name

def process_stops_column(stops_str):
    """
    Process the stops column by standardizing each station name.
    
    Args:
        stops_str: String containing stops separated by delimiter
        
    Returns:
        Standardized stops string
    """
    if pd.isna(stops_str):
        return stops_str
    
    # Split by delimiters and standardize each stop
    stops = [stop.strip() for stop in stops_str.split(" - ")]
    standardized_stops = [standardize_station_name(stop) for stop in stops]
    
    # Rejoin with the same delimiter
    return " - ".join(standardized_stops)

def process_file(input_file, output_file):
    """
    Process a single transport data file by standardizing station names.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output standardized CSV file
    """
    try:
        # Read the data
        df = pd.read_csv(input_file, encoding='utf-8')
        
        # Apply the standardization to the 'stops' column
        if 'stops' in df.columns:
            df['stops'] = df['stops'].apply(process_stops_column)
        
        # Save the standardized data
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Processed: {os.path.basename(input_file)} → {os.path.basename(output_file)}")
        return True
    except Exception as e:
        print(f"✗ Error processing {input_file}: {str(e)}")
        return False

def process_directory(input_dir, output_dir, pattern="*.csv"):
    """
    Process all CSV files in a directory, standardizing station names.
    
    Args:
        input_dir: Directory containing input CSV files
        output_dir: Directory to save standardized CSV files
        pattern: File pattern to match (default: "*.csv")
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all matching files in the input directory
    input_files = glob.glob(os.path.join(input_dir, pattern))
    
    if not input_files:
        print(f"No files matching pattern '{pattern}' found in {input_dir}")
        return
    
    # Process each file
    success_count = 0
    for input_file in input_files:
        # Create output file path with same name in output directory
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        
        # Process the file
        if process_file(input_file, output_file):
            success_count += 1
    
    # Print summary
    print(f"\nProcessing complete: {success_count}/{len(input_files)} files processed successfully")

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Standardize station names in transport data files")
    parser.add_argument("input_dir", help="Directory containing input CSV files")
    parser.add_argument("output_dir", help="Directory to save standardized CSV files")
    parser.add_argument("--pattern", default="*.csv", help="File pattern to match (default: *.csv)")
    
    args = parser.parse_args()
    
    # Process the directory
    process_directory(args.input_dir, args.output_dir, args.pattern)