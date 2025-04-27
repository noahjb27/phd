import pandas as pd
import difflib
import argparse
from typing import List, Dict, Tuple, Set
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn2
from io import BytesIO
import base64


def parse_stops(stops_str: str) -> List[str]:
    """Parse the stops string into a list of station names."""
    if pd.isna(stops_str):
        return []
    # Split by " - " which appears to be the delimiter in your data
    return [stop.strip() for stop in stops_str.split(" - ")]


def compare_stops(stops1: List[str], stops2: List[str]) -> Dict:
    """Compare two lists of stops and return detailed differences."""
    # Convert to sets to find unique elements
    set1 = set(stops1)
    set2 = set(stops2)
    
    # Find stations that are in each list but not the other
    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    
    # Look at the sequence differences for stations in both lists
    common_stations = set1.intersection(set2)
    
    # Check if there's been a reordering of common stations
    reordered = False
    reordered_stations = []
    
    # Extract only common stations in original order
    seq1 = [s for s in stops1 if s in common_stations]
    seq2 = [s for s in stops2 if s in common_stations]
    
    if seq1 != seq2:
        reordered = True
        # Find stations that changed position
        for i, station in enumerate(seq1):
            idx2 = seq2.index(station) if station in seq2 else -1
            if idx2 != -1 and idx2 != i:
                reordered_stations.append((station, i, idx2))
    
    return {
        "removed": sorted(list(only_in_1)),
        "added": sorted(list(only_in_2)),
        "reordered": reordered,
        "reordered_stations": reordered_stations,
        "total_stops_before": len(stops1),
        "total_stops_after": len(stops2)
    }


def generate_visualizations(df1, df2, year1, year2):
    """
    Generate visualizations to compare network snapshots.
    
    Args:
        df1: DataFrame for the first year
        df2: DataFrame for the second year
        year1: First year label
        year2: Second year label
    
    Returns:
        Dict of base64-encoded PNG images
    """
    images = {}
    
    # Set plot style
    sns.set(style="whitegrid")
    
    # 1. Line count by type
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Count lines by type for each year
    type_counts1 = df1['type'].value_counts().reset_index()
    type_counts1.columns = ['type', year1]
    
    type_counts2 = df2['type'].value_counts().reset_index()
    type_counts2.columns = ['type', year2]
    
    # Merge the two counts
    combined = pd.merge(type_counts1, type_counts2, on='type', how='outer').fillna(0)
    
    # Create a grouped bar chart
    combined.plot(x='type', y=[year1, year2], kind='bar', ax=ax)
    plt.title(f'Line Counts by Type: {year1} vs {year2}')
    plt.xlabel('Transport Type')
    plt.ylabel('Number of Lines')
    plt.tight_layout()
    
    # Convert to base64 for embedding in the report
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    images['type_counts'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # 2. Venn diagram of line names
    fig, ax = plt.subplots(figsize=(8, 6))
    
    lines_set1 = set(df1['line_name'])
    lines_set2 = set(df2['line_name'])
    
    v = venn2([lines_set1, lines_set2], (year1, year2), ax=ax)
    plt.title(f'Line Overlap: {year1} vs {year2}')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    images['line_overlap'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return images


def compare_network_snapshots(file1: str, file2: str, output_path: str = None, include_viz: bool = True):
    """
    Compare two network snapshots and generate a report of differences.
    
    Args:
        file1: Path to the first CSV file
        file2: Path to the second CSV file
        output_path: Optional path to write the report to
        include_viz: Whether to include visualizations in the report
    """
    # Extract years from filenames if possible
    year1 = re.search(r'(\d{4})_', os.path.basename(file1))
    year2 = re.search(r'(\d{4})_', os.path.basename(file2))
    
    year1 = year1.group(1) if year1 else "first snapshot"
    year2 = year2.group(1) if year2 else "second snapshot"
    
    # Read CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Add parsed stops columns
    df1['parsed_stops'] = df1['stops'].apply(parse_stops)
    df2['parsed_stops'] = df2['stops'].apply(parse_stops)
    
    # Basic counts
    lines_count1 = len(df1)
    lines_count2 = len(df2)
    
    # Find unique lines in each dataset
    lines_set1 = set(df1['line_name'])
    lines_set2 = set(df2['line_name'])
    
    only_in_1 = lines_set1 - lines_set2
    only_in_2 = lines_set2 - lines_set1
    common_lines = lines_set1.intersection(lines_set2)
    
    # Prepare report
    report = [
        f"# Network Comparison: {year1} vs {year2}",
        "",
        f"## Summary",
        f"- {year1}: {lines_count1} lines",
        f"- {year2}: {lines_count2} lines",
        f"- Lines added in {year2}: {len(only_in_2)}",
        f"- Lines removed from {year1}: {len(only_in_1)}",
        f"- Common lines: {len(common_lines)}",
        "",
    ]
    
    # Track discrepancy counts for common lines
    diff_stops_count = 0
    diff_frequency_count = 0
    diff_length_time_count = 0
    diff_length_km_count = 0
    
    # Compare all common lines to get summary statistics
    for line_name in common_lines:
        line1 = df1[df1['line_name'] == line_name].iloc[0]
        line2 = df2[df2['line_name'] == line_name].iloc[0]
        
        # Compare stops
        stops_comparison = compare_stops(line1['parsed_stops'], line2['parsed_stops'])
        if stops_comparison['added'] or stops_comparison['removed'] or stops_comparison['reordered']:
            diff_stops_count += 1
        
        # Compare other attributes
        if line1['frequency (7:30)'] != line2['frequency (7:30)']:
            diff_frequency_count += 1
            
        if line1['length (time)'] != line2['length (time)']:
            diff_length_time_count += 1
            
        if 'length (km)' in df1.columns and 'length (km)' in df2.columns:
            if line1['length (km)'] != line2['length (km)']:
                diff_length_km_count += 1
    
    # Add discrepancy summary to report
    report.extend([
        f"## Discrepancy Summary for Common Lines",
        f"- Lines with different stops: {diff_stops_count} ({diff_stops_count/len(common_lines)*100:.1f}%)",
        f"- Lines with different frequencies: {diff_frequency_count} ({diff_frequency_count/len(common_lines)*100:.1f}%)",
        f"- Lines with different time lengths: {diff_length_time_count} ({diff_length_time_count/len(common_lines)*100:.1f}%)",
    ])
    
    if 'length (km)' in df1.columns and 'length (km)' in df2.columns:
        report.append(f"- Lines with different km lengths: {diff_length_km_count} ({diff_length_km_count/len(common_lines)*100:.1f}%)")
    
    report.append("")
    
    # Lines unique to each snapshot
    if only_in_1:
        report.extend([
            f"## Lines only in {year1} ({len(only_in_1)})",
            ", ".join(sorted(only_in_1)),
            ""
        ])
    
    if only_in_2:
        report.extend([
            f"## Lines only in {year2} ({len(only_in_2)})",
            ", ".join(sorted(only_in_2)),
            ""
        ])
    
    # Create sections for different types of discrepancies
    if diff_stops_count > 0:
        report.extend([
            f"## Lines with Different Stops ({diff_stops_count})",
            ""
        ])
        
        for line_name in sorted(common_lines):
            line1 = df1[df1['line_name'] == line_name].iloc[0]
            line2 = df2[df2['line_name'] == line_name].iloc[0]
            stops_comparison = compare_stops(line1['parsed_stops'], line2['parsed_stops'])
            
            if stops_comparison['added'] or stops_comparison['removed'] or stops_comparison['reordered']:
                report.extend([
                    f"### Line {line_name} ({line1['type']})",
                    f"- Total stops: {stops_comparison['total_stops_before']} → {stops_comparison['total_stops_after']}",
                    ""
                ])
                
                if stops_comparison['removed']:
                    report.extend([
                        f"#### Stations removed ({len(stops_comparison['removed'])})",
                        "- " + "\n- ".join(stops_comparison['removed']),
                        ""
                    ])
                
                if stops_comparison['added']:
                    report.extend([
                        f"#### Stations added ({len(stops_comparison['added'])})",
                        "- " + "\n- ".join(stops_comparison['added']),
                        ""
                    ])
                
                if stops_comparison['reordered']:
                    report.extend([
                        f"#### Stations reordered",
                        "There were changes in the order of stations.",
                        ""
                    ])
    
    # Frequency changes
    if diff_frequency_count > 0:
        report.extend([
            f"## Lines with Different Frequencies ({diff_frequency_count})",
            ""
        ])
        
        freq_changes = []
        for line_name in sorted(common_lines):
            line1 = df1[df1['line_name'] == line_name].iloc[0]
            line2 = df2[df2['line_name'] == line_name].iloc[0]
            
            if line1['frequency (7:30)'] != line2['frequency (7:30)']:
                freq_changes.append(f"{line_name} ({line1['type']}): {line1['frequency (7:30)']} → {line2['frequency (7:30)']}")
        
        report.extend([
            "- " + "\n- ".join(freq_changes),
            ""
        ])
    
    # Length (time) changes
    if diff_length_time_count > 0:
        report.extend([
            f"## Lines with Different Time Lengths ({diff_length_time_count})",
            ""
        ])
        
        length_changes = []
        for line_name in sorted(common_lines):
            line1 = df1[df1['line_name'] == line_name].iloc[0]
            line2 = df2[df2['line_name'] == line_name].iloc[0]
            
            if line1['length (time)'] != line2['length (time)']:
                length_changes.append(f"{line_name} ({line1['type']}): {line1['length (time)']} → {line2['length (time)']}")
        
        report.extend([
            "- " + "\n- ".join(length_changes),
            ""
        ])
    
    # Length (km) changes
    if 'length (km)' in df1.columns and 'length (km)' in df2.columns and diff_length_km_count > 0:
        report.extend([
            f"## Lines with Different KM Lengths ({diff_length_km_count})",
            ""
        ])
        
        km_changes = []
        for line_name in sorted(common_lines):
            line1 = df1[df1['line_name'] == line_name].iloc[0]
            line2 = df2[df2['line_name'] == line_name].iloc[0]
            
            if line1['length (km)'] != line2['length (km)']:
                km_changes.append(f"{line_name} ({line1['type']}): {line1['length (km)']} → {line2['length (km)']}")
        
        report.extend([
            "- " + "\n- ".join(km_changes),
            ""
        ])
    
    # Generate visualizations if requested
    if include_viz:
        try:
            images = generate_visualizations(df1, df2, year1, year2)
            
            # Add visualizations to the report
            report.extend([
                "## Visualizations",
                "",
                "### Line Counts by Type",
                f"![Line Counts by Type](data:image/png;base64,{images['type_counts']})",
                "",
                "### Line Overlap Between Years",
                f"![Line Overlap](data:image/png;base64,{images['line_overlap']})",
                ""
            ])
        except ImportError:
            report.extend([
                "## Visualizations",
                "",
                "Note: Visualizations were requested but could not be generated. Please install matplotlib, seaborn, and matplotlib-venn packages.",
                ""
            ])
        except Exception as e:
            report.extend([
                "## Visualizations",
                "",
                f"Note: Error generating visualizations: {str(e)}",
                ""
            ])
    
    # Write report to file or return as string
    report_text = "\n".join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return f"Report written to {output_path}"
    else:
        return report_text


def export_discrepancies_csv(file1: str, file2: str, output_csv: str):
    """
    Export discrepancies between two network snapshots to a CSV file.
    
    Args:
        file1: Path to the first CSV file
        file2: Path to the second CSV file
        output_csv: Path to write the output CSV
    """
    # Extract years from filenames if possible
    year1 = re.search(r'(\d{4})_', os.path.basename(file1))
    year2 = re.search(r'(\d{4})_', os.path.basename(file2))
    
    year1 = year1.group(1) if year1 else "snapshot1"
    year2 = year2.group(1) if year2 else "snapshot2"
    
    # Read CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Add parsed stops columns
    df1['parsed_stops'] = df1['stops'].apply(parse_stops)
    df2['parsed_stops'] = df2['stops'].apply(parse_stops)
    
    # Find common lines
    lines_set1 = set(df1['line_name'])
    lines_set2 = set(df2['line_name'])
    common_lines = lines_set1.intersection(lines_set2)
    
    # Prepare discrepancy data
    discrepancies = []
    
    for line_name in sorted(common_lines):
        line1 = df1[df1['line_name'] == line_name].iloc[0]
        line2 = df2[df2['line_name'] == line_name].iloc[0]
        
        # Compare stops
        stops_comparison = compare_stops(line1['parsed_stops'], line2['parsed_stops'])
        
        # Check for differences
        stops_different = len(stops_comparison['added']) > 0 or len(stops_comparison['removed']) > 0 or stops_comparison['reordered']
        frequency_different = line1['frequency (7:30)'] != line2['frequency (7:30)']
        length_time_different = line1['length (time)'] != line2['length (time)']
        
        length_km_different = False
        if 'length (km)' in df1.columns and 'length (km)' in df2.columns:
            length_km_different = line1['length (km)'] != line2['length (km)']
        
        # Only add if there's at least one difference
        if stops_different or frequency_different or length_time_different or length_km_different:
            discrepancies.append({
                'line_name': line_name,
                'type': line1['type'],
                'stops_different': stops_different,
                'stops_added': len(stops_comparison['added']),
                'stops_removed': len(stops_comparison['removed']),
                'stops_reordered': stops_comparison['reordered'],
                'frequency_different': frequency_different,
                f'frequency_{year1}': line1['frequency (7:30)'],
                f'frequency_{year2}': line2['frequency (7:30)'],
                'length_time_different': length_time_different,
                f'length_time_{year1}': line1['length (time)'],
                f'length_time_{year2}': line2['length (time)'],
                'length_km_different': length_km_different,
                f'length_km_{year1}': line1['length (km)'] if 'length (km)' in df1.columns else None,
                f'length_km_{year2}': line2['length (km)'] if 'length (km)' in df2.columns else None
            })
    
    # Convert to DataFrame and export
    discrepancies_df = pd.DataFrame(discrepancies)
    discrepancies_df.to_csv(output_csv, index=False)
    return f"Discrepancies exported to {output_csv}"


def main():
    parser = argparse.ArgumentParser(description='Compare two network snapshots')
    parser.add_argument('file1', help='Path to the first CSV file')
    parser.add_argument('file2', help='Path to the second CSV file')
    parser.add_argument('--output', '-o', help='Output markdown report path (optional)')
    parser.add_argument('--csv', help='Output CSV discrepancies path (optional)')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualizations')
    
    args = parser.parse_args()
    
    # Generate the markdown report if requested
    if args.output or not args.csv:
        result = compare_network_snapshots(
            args.file1, 
            args.file2, 
            args.output, 
            include_viz=not args.no_viz
        )
        
        if not args.output:
            print(result)
    
    # Export CSV discrepancies if requested
    if args.csv:
        export_result = export_discrepancies_csv(args.file1, args.file2, args.csv)
        print(export_result)


if __name__ == "__main__":
    main()