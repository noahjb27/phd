import os
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import argparse
from typing import List, Dict, Tuple, Set
import shutil
import glob
import re

def fuzzy_match_stations(stops1: List[str], stops2: List[str], threshold: int = 85) -> Dict:
    """
    Perform fuzzy matching between two lists of station names.
    
    Args:
        stops1: First list of station names
        stops2: Second list of station names
        threshold: Similarity threshold (0-100) to consider a match
        
    Returns:
        Dictionary of matches {index_in_stops1: (index_in_stops2, score, original_name1, original_name2)}
    """
    matches = {}
    
    # Try to find the best match for each station in stops1
    for i, stop1 in enumerate(stops1):
        best_match_idx = -1
        best_match_score = 0
        
        for j, stop2 in enumerate(stops2):
            # Skip empty names
            if not stop1 or not stop2:
                continue
            
            # Calculate similarity scores using multiple metrics
            ratio = fuzz.ratio(stop1.lower(), stop2.lower())
            partial_ratio = fuzz.partial_ratio(stop1.lower(), stop2.lower())
            token_sort_ratio = fuzz.token_sort_ratio(stop1.lower(), stop2.lower())
            
            # Use a weighted average of different fuzzy metrics
            score = (ratio + partial_ratio + token_sort_ratio) / 3
            
            # Update best match if this is better
            if score > best_match_score and score >= threshold:
                best_match_score = score
                best_match_idx = j
        
        # If a match was found, store it
        if best_match_idx >= 0:
            matches[i] = (best_match_idx, best_match_score, stops1[i], stops2[best_match_idx])
    
    return matches

def parse_stops(stops_str: str) -> List[str]:
    """Parse the stops string into a list of station names."""
    if pd.isna(stops_str):
        return []
    # Split by " - " which appears to be the delimiter
    return [stop.strip() for stop in stops_str.split(" - ")]

def harmonize_line_stations(df1: pd.DataFrame, df2: pd.DataFrame, prefer_df1: bool = True, 
                           threshold: int = 85, dry_run: bool = True) -> Tuple[pd.DataFrame, Dict]:
    """
    Harmonize station names between two dataframes representing different snapshots.
    
    Args:
        df1: First dataframe
        df2: Second dataframe
        prefer_df1: Whether to prefer names from df1 (True) or df2 (False)
        threshold: Similarity threshold for fuzzy matching
        dry_run: If True, just return changes without applying them
        
    Returns:
        Tuple of (updated_df, changes_log)
    """
    # Determine which is the source (preferred) and target (to be updated)
    source_df = df1 if prefer_df1 else df2
    target_df = df2 if prefer_df1 else df1
    
    # Make a copy of the target dataframe to modify
    updated_df = target_df.copy()
    
    # Track all changes for reporting
    changes_log = {}
    
    # Find common lines between the two datasets
    common_lines = set(df1['line_name']).intersection(set(df2['line_name']))
    
    # For each common line, compare and potentially update stations
    for line_name in common_lines:
        # Get the rows for this line in both dataframes
        source_row = source_df[source_df['line_name'] == line_name].iloc[0]
        target_row = target_df[target_df['line_name'] == line_name].iloc[0]
        
        # Parse the stops
        source_stops = parse_stops(source_row['stops'])
        target_stops = parse_stops(target_row['stops'])
        
        # Skip if either list is empty
        if not source_stops or not target_stops:
            continue
        
        # Find matching stations using fuzzy matching
        matches = fuzzy_match_stations(source_stops, target_stops, threshold)
        
        # Skip if no matches found
        if not matches:
            continue
        
        # Determine which stops need to be updated in the target
        changes = []
        for source_idx, (target_idx, score, source_name, target_name) in matches.items():
            # Only update if the names are different
            if source_name != target_name:
                changes.append((target_name, source_name, score))
        
        # If there are changes, update the target stops
        if changes:
            # Create a mapping of old to new names for this line
            name_mapping = {old: new for old, new, _ in changes}
            
            # Log the changes
            changes_log[line_name] = changes
            
            # If not a dry run, update the target dataframe
            if not dry_run:
                # Get the original stops string
                stops_str = target_row['stops']
                
                # For each old->new name change, update the stops string
                for old_name, new_name, _ in changes:
                    # Use regex with word boundaries to ensure we replace complete station names
                    # and not parts of other names
                    pattern = r'(^|\s- )' + re.escape(old_name) + r'($|\s- )'
                    replacement = r'\1' + new_name + r'\2'
                    stops_str = re.sub(pattern, replacement, stops_str)
                
                # Update the stops column in the updated dataframe
                idx = updated_df[updated_df['line_name'] == line_name].index[0]
                updated_df.at[idx, 'stops'] = stops_str
    
    return updated_df, changes_log

def format_changes_report(changes_log: Dict) -> str:
    """Format the changes log into a readable report."""
    if not changes_log:
        return "No changes to make."
    
    lines = ["Station Name Harmonization Report", "=" * 30, ""]
    
    total_changes = sum(len(changes) for changes in changes_log.values())
    lines.append(f"Total lines with changes: {len(changes_log)}")
    lines.append(f"Total station names to update: {total_changes}")
    lines.append("")
    
    for line_name, changes in changes_log.items():
        lines.append(f"Line {line_name} ({len(changes)} changes):")
        for old_name, new_name, score in changes:
            lines.append(f"  • {old_name} → {new_name} (match score: {score:.1f}%)")
        lines.append("")
    
    return "\n".join(lines)

def main():
    """Main function to run the station name harmonization."""
    parser = argparse.ArgumentParser(description="Harmonize station names between two transport network snapshots")
    parser.add_argument("file1", help="Path to first CSV file")
    parser.add_argument("file2", help="Path to second CSV file")
    parser.add_argument("--prefer", type=int, choices=[1, 2], default=1,
                        help="Which snapshot to prefer (1 or 2, default: 1)")
    parser.add_argument("--threshold", type=int, default=85,
                        help="Similarity threshold for fuzzy matching (0-100, default: 85)")
    parser.add_argument("--output", help="Output file path (default: updates file2 if prefer=1, file1 if prefer=2)")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Only show changes without applying them")
    parser.add_argument("--backup", action="store_true",
                        help="Create backup of original file before modifying")
    
    args = parser.parse_args()
    
    # Read the CSV files
    df1 = pd.read_csv(args.file1)
    df2 = pd.read_csv(args.file2)
    
    # Extract year and side information from filenames for better reporting
    file1_name = os.path.basename(args.file1)
    file2_name = os.path.basename(args.file2)
    
    match1 = re.search(r'(\d{4})_([a-z]+)\.csv', file1_name)
    match2 = re.search(r'(\d{4})_([a-z]+)\.csv', file2_name)
    
    snapshot1_name = f"{match1.group(1)}_{match1.group(2)}" if match1 else file1_name
    snapshot2_name = f"{match2.group(1)}_{match2.group(2)}" if match2 else file2_name
    
    # Determine which snapshot to prefer
    prefer_df1 = args.prefer == 1
    preferred_name = snapshot1_name if prefer_df1 else snapshot2_name
    target_name = snapshot2_name if prefer_df1 else snapshot1_name
    
    print(f"Harmonizing station names:")
    print(f"  • Preferred snapshot: {preferred_name}")
    print(f"  • Target snapshot: {target_name}")
    print(f"  • Match threshold: {args.threshold}%")
    print(f"  • Mode: {'Dry run (no changes will be made)' if args.dry_run else 'Applying changes'}")
    
    # Perform the harmonization
    updated_df, changes_log = harmonize_line_stations(
        df1, df2, 
        prefer_df1=prefer_df1, 
        threshold=args.threshold,
        dry_run=args.dry_run
    )
    
    # Print the changes report
    report = format_changes_report(changes_log)
    print("\n" + report)
    
    # If not a dry run and there are changes, save the updated file
    if not args.dry_run and changes_log:
        # Determine output file path
        if args.output:
            output_path = args.output
        else:
            # Update the non-preferred file by default
            output_path = args.file2 if prefer_df1 else args.file1
        
        # Create backup if requested
        if args.backup and os.path.exists(output_path):
            backup_path = output_path + ".bak"
            shutil.copy2(output_path, backup_path)
            print(f"Backup created: {backup_path}")
        
        # Save the updated dataframe
        updated_df.to_csv(output_path, index=False)
        print(f"Updated file saved: {output_path}")
    
    # Print a summary
    if changes_log:
        print(f"\nSummary: {sum(len(changes) for changes in changes_log.values())} station names harmonized across {len(changes_log)} lines.")
    else:
        print("\nNo changes needed or made.")

if __name__ == "__main__":
    main()