#!/usr/bin/env python3
"""
Unified Berlin Administrative Zone Validation & Visualization
=============================================================

One script that does everything:
1. Automatically detects coordinate system issues
2. Reprojects coordinates if needed
3. Validates data coverage and consistency
4. Creates interactive validation maps for all time periods
5. Generates spatial summaries ready for Neo4j

Usage: python unified_validation.py
"""

import json
import pandas as pd
import folium
from datetime import datetime
import os

# Try to import coordinate transformation libraries
try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False

def detect_and_parse_crs(geojson_data):
    """Detect and parse coordinate system from GeoJSON"""
    # Check if CRS is specified in the data
    if 'crs' in geojson_data:
        crs_info = geojson_data['crs']
        print(f"Found CRS in data: {crs_info}")
        
        # Parse the CRS object to extract EPSG code
        if isinstance(crs_info, dict):
            if 'properties' in crs_info and 'name' in crs_info['properties']:
                crs_name = crs_info['properties']['name']
                
                # Handle different CRS name formats
                if 'urn:ogc:def:crs:EPSG::' in crs_name:
                    epsg_code = crs_name.split('::')[-1]
                    return f"EPSG:{epsg_code}"
                elif 'EPSG:' in crs_name:
                    return crs_name
                elif crs_name.isdigit():
                    return f"EPSG:{crs_name}"
        
        # If it's already a string, return as is
        if isinstance(crs_info, str):
            return crs_info
    
    # Analyze coordinate ranges to guess CRS
    sample_coords = []
    for feature in geojson_data['features'][:5]:  # Sample first 5 features
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0][:5]  # First 5 points
        elif geom['type'] == 'MultiPolygon':
            coords = geom['coordinates'][0][0][:5]  # First ring, first 5 points
        else:
            continue
        sample_coords.extend(coords)
    
    if sample_coords:
        x_vals = [coord[0] for coord in sample_coords]
        y_vals = [coord[1] for coord in sample_coords]
        
        min_x, max_x = min(x_vals), max(x_vals)
        min_y, max_y = min(y_vals), max(y_vals)
        
        print(f"Coordinate ranges: X={min_x:.1f} to {max_x:.1f}, Y={min_y:.1f} to {max_y:.1f}")
        
        # Berlin area detection
        if 300000 < min_x < 400000 and 5800000 < min_y < 5900000:
            print("Detected: Likely ETRS89/UTM Zone 33N (EPSG:25833)")
            return "EPSG:25833"
        elif 10 < min_x < 15 and 52 < min_y < 53:
            print("Detected: Already in WGS84 (EPSG:4326)")
            return "EPSG:4326"
        else:
            print(f"Unknown CRS - assuming ETRS89/UTM Zone 33N (EPSG:25833)")
            return "EPSG:25833"
    
    return "EPSG:25833"  # Default for Berlin

def needs_reprojection(geojson_data):
    """Check if the GeoJSON data needs reprojection to WGS84"""
    source_crs = detect_and_parse_crs(geojson_data)
    return source_crs != "EPSG:4326"

def reproject_coordinates_pyproj(coords, source_crs="EPSG:25833", target_crs="EPSG:4326"):
    """Reproject coordinates using pyproj"""
    
    # Ensure source_crs is a string
    if isinstance(source_crs, dict):
        if 'properties' in source_crs and 'name' in source_crs['properties']:
            crs_name = source_crs['properties']['name']
            if 'urn:ogc:def:crs:EPSG::' in crs_name:
                epsg_code = crs_name.split('::')[-1]
                source_crs = f"EPSG:{epsg_code}"
            else:
                source_crs = "EPSG:25833"
        else:
            source_crs = "EPSG:25833"
    
    try:
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    except Exception as e:
        print(f"Error creating transformer: {e}")
        raise
    
    def transform_coord_list(coord_list):
        if not coord_list:
            return coord_list
        
        if isinstance(coord_list[0], list):
            return [transform_coord_list(sublist) for sublist in coord_list]
        else:
            if len(coord_list) >= 2:
                try:
                    lon, lat = transformer.transform(coord_list[0], coord_list[1])
                    return [lon, lat] + coord_list[2:]
                except Exception as e:
                    print(f"Error transforming coordinates {coord_list}: {e}")
                    return coord_list
            return coord_list
    
    return transform_coord_list(coords)

def reproject_coordinates_manual(coords, source_crs="EPSG:25833"):
    """Manual coordinate transformation fallback"""
    if source_crs == "EPSG:4326":
        return coords
    
    def transform_coord_list(coord_list):
        if not coord_list:
            return coord_list
        
        if isinstance(coord_list[0], list):
            return [transform_coord_list(sublist) for sublist in coord_list]
        else:
            x, y = coord_list[0], coord_list[1]
            
            # Approximate transformation for Berlin UTM to WGS84
            if 300000 < x < 400000 and 5800000 < y < 5900000:
                lon = 13.4 + (x - 390000) / 80000
                lat = 52.5 + (y - 5820000) / 111000
            else:
                lon = (x - 500000) / 111320.0 + 15.0
                lat = y / 111320.0 - 52.0
            
            return [lon, lat] + coord_list[2:]
    
    return transform_coord_list(coords)

def reproject_geojson_if_needed(geojson_data):
    """Reproject GeoJSON to WGS84 if needed, return (data, was_reprojected)"""
    
    if not needs_reprojection(geojson_data):
        print("✅ Data already in WGS84, no reprojection needed")
        return geojson_data, False
    
    source_crs = detect_and_parse_crs(geojson_data)
    print(f"🔄 Reprojecting from {source_crs} to EPSG:4326...")
    
    # Choose reprojection method
    if PYPROJ_AVAILABLE:
        print("   Using pyproj for accurate reprojection")
        reproject_func = lambda coords: reproject_coordinates_pyproj(coords, source_crs, "EPSG:4326")
    else:
        print("   Using manual approximation (install pyproj for accuracy)")
        reproject_func = lambda coords: reproject_coordinates_manual(coords, source_crs)
    
    # Create copy and reproject
    reprojected_data = json.loads(json.dumps(geojson_data))
    
    for feature in reprojected_data['features']:
        geometry = feature['geometry']
        if geometry['type'] in ['Polygon', 'MultiPolygon']:
            geometry['coordinates'] = reproject_func(geometry['coordinates'])
        elif geometry['type'] == 'Point':
            geometry['coordinates'] = reproject_func([geometry['coordinates']])[0]
    
    # Update CRS info
    reprojected_data['crs'] = {
        "type": "name",
        "properties": {"name": "EPSG:4326"}
    }
    
    # Verify reprojection
    sample_feature = reprojected_data['features'][0]
    sample_coords = sample_feature['geometry']['coordinates'][0][0][:2]
    
    # Handle nested coordinate structure
    if isinstance(sample_coords[0], list):
        first_coord = sample_coords[0]
        lon, lat = first_coord[0], first_coord[1]
    else:
        lon, lat = sample_coords[0], sample_coords[1]
    
    if 10 < lon < 15 and 52 < lat < 53:
        print(f"✅ Reprojection successful: lon={lon:.3f}, lat={lat:.3f}")
    else:
        print(f"⚠️  Warning: Coordinates may not be correct: lon={lon:.3f}, lat={lat:.3f}")
    
    return reprojected_data, True

def validate_data_coverage(assignments_data, ortsteil_geojson):
    """Check data coverage and consistency"""
    print("\n=== DATA VALIDATION ===")
    
    assignment_ortsteil = set(a['ortsteil_name'] for a in assignments_data['assignments'])
    geojson_ortsteil = set(f['properties']['nam'] for f in ortsteil_geojson['features'])
    
    in_both = assignment_ortsteil & geojson_ortsteil
    only_in_assignments = assignment_ortsteil - geojson_ortsteil
    only_in_geojson = geojson_ortsteil - assignment_ortsteil
    
    print(f"✅ Ortsteil in both assignments and geojson: {len(in_both)}")
    print(f"⚠️  Ortsteil only in assignments: {len(only_in_assignments)}")
    print(f"⚠️  Ortsteil only in geojson: {len(only_in_geojson)}")
    
    if only_in_assignments:
        print(f"   Missing polygons: {sorted(list(only_in_assignments))[:3]}{'...' if len(only_in_assignments) > 3 else ''}")
    
    if only_in_geojson:
        print(f"   Missing assignments: {sorted(list(only_in_geojson))[:3]}{'...' if len(only_in_geojson) > 3 else ''}")
    
    coverage_percent = len(in_both) / max(len(assignment_ortsteil), len(geojson_ortsteil)) * 100
    print(f"📊 Overall coverage: {coverage_percent:.1f}%")
    
    return in_both, only_in_assignments, only_in_geojson

def get_assignments_at_date(assignments_data, target_date):
    """Get Bezirke composition at specific date"""
    target_dt = pd.to_datetime(target_date)
    
    active_assignments = []
    for assignment in assignments_data['assignments']:
        start_dt = pd.to_datetime(assignment['start_date'])
        end_dt = pd.to_datetime(assignment['end_date']) if assignment['end_date'] else None
        
        if start_dt <= target_dt and (end_dt is None or end_dt >= target_dt):
            active_assignments.append(assignment)
    
    bezirk_composition = {}
    for assignment in active_assignments:
        bezirk_id = assignment['bezirk_id']
        ortsteil_name = assignment['ortsteil_name']
        
        if bezirk_id not in bezirk_composition:
            bezirk_composition[bezirk_id] = []
        bezirk_composition[bezirk_id].append(ortsteil_name)
    
    return bezirk_composition

def create_validation_map(bezirk_composition, bezirke_data, ortsteil_geojson, target_date, filename):
    """Create validation map for specific date"""
    print(f"   Creating map for {target_date}...")
    
    m = folium.Map(location=[52.5200, 13.4050], zoom_start=10)
    
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85929E', '#D5A6BD',
        '#AED6F1', '#A9DFBF', '#F9E79F', '#D7BDE2', '#A3E4D7'
    ]
    
    bezirke_lookup = {b['bezirk_id']: b for b in bezirke_data['bezirke']}
    bezirk_colors = {}
    color_idx = 0
    stats = {'east': 0, 'west': 0, 'ortsteil_added': 0, 'ortsteil_missing': 0}
    
    for bezirk_id, ortsteil_list in bezirk_composition.items():
        if bezirk_id not in bezirke_lookup:
            continue
            
        bezirk_info = bezirke_lookup[bezirk_id]
        bezirk_name = bezirk_info['name']
        east_west = bezirk_info['east_west']
        
        color = colors[color_idx % len(colors)]
        bezirk_colors[bezirk_id] = color
        color_idx += 1
        
        stats[east_west] += 1
        
        for ortsteil_name in ortsteil_list:
            found = False
            for feature in ortsteil_geojson['features']:
                if feature['properties']['nam'] == ortsteil_name:
                    popup_text = f"""
                    <b>{ortsteil_name}</b><br>
                    Bezirk: {bezirk_name}<br>
                    Sector: {east_west.title()}<br>
                    Date: {target_date}
                    """
                    
                    folium.GeoJson(
                        feature,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=f"{ortsteil_name} ({bezirk_name})"
                    ).add_to(m)
                    
                    stats['ortsteil_added'] += 1
                    found = True
                    break
            
            if not found:
                stats['ortsteil_missing'] += 1
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 280px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4 style="margin-top:0">Berlin - {target_date}</h4>
    <p><b>East:</b> {stats['east']} districts<br>
       <b>West:</b> {stats['west']} districts<br>
       <b>Ortsteil:</b> {stats['ortsteil_added']} mapped</p>
    '''
    
    # Add district colors
    east_bezirke = [(bid, bezirke_lookup[bid]['name']) for bid in bezirk_composition.keys() 
                   if bezirke_lookup[bid]['east_west'] == 'east']
    west_bezirke = [(bid, bezirke_lookup[bid]['name']) for bid in bezirk_composition.keys() 
                   if bezirke_lookup[bid]['east_west'] == 'west']
    
    if east_bezirke:
        legend_html += '<b>East:</b><br>'
        for bezirk_id, name in sorted(east_bezirke, key=lambda x: x[1]):
            color = bezirk_colors[bezirk_id]
            legend_html += f'<span style="color:{color}">■</span> {name}<br>'
    
    if west_bezirke:
        legend_html += '<br><b>West:</b><br>'
        for bezirk_id, name in sorted(west_bezirke, key=lambda x: x[1]):
            color = bezirk_colors[bezirk_id]
            legend_html += f'<span style="color:{color}">■</span> {name}<br>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(filename)
    print(f"     ✅ {stats['ortsteil_added']} Ortsteil mapped, {stats['ortsteil_missing']} missing")
    
    return stats

def main():
    """Main unified validation workflow"""
    print("🗺️  Berlin Administrative Zone Unified Validator")
    print("=" * 55)
    
    # Load data files
    try:
        print("📁 Loading data files...")
        
        with open("ortsteil_assignments.json", "r", encoding="utf-8") as f:
            assignments_data = json.load(f)
        
        with open("historical_bezirke.json", "r", encoding="utf-8") as f:
            bezirke_data = json.load(f)
        
        with open("moderne_ortsteile.json", "r", encoding="utf-8") as f:
            ortsteil_geojson = json.load(f)
            
        print(f"✅ Loaded {len(assignments_data['assignments'])} assignments")
        print(f"✅ Loaded {len(bezirke_data['bezirke'])} historical Bezirke")
        print(f"✅ Loaded {len(ortsteil_geojson['features'])} Ortsteil polygons")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find data file: {e}")
        print("Required files: ortsteil_assignments.json, historical_bezirke.json, moderne_ortsteile.json")
        return
    
    # Check and reproject coordinates if needed
    print(f"\n🌍 Checking coordinate system...")
    ortsteil_geojson_wgs84, was_reprojected = reproject_geojson_if_needed(ortsteil_geojson)
    
    if was_reprojected:
        # Save reprojected data for future use
        with open("moderne_ortsteile_wgs84.json", "w", encoding="utf-8") as f:
            json.dump(ortsteil_geojson_wgs84, f, ensure_ascii=False, indent=2)
        print("💾 Saved reprojected data: moderne_ortsteile_wgs84.json")
    
    # Validate data coverage
    in_both, only_assignments, only_geojson = validate_data_coverage(assignments_data, ortsteil_geojson_wgs84)
    
    # Create output directory
    os.makedirs("validation_maps", exist_ok=True)
    
    # Key validation dates
    key_dates = [
        ("1946-01-01", "Initial post-war structure"),
        ("1979-01-05", "After Marzahn creation"), 
        ("1985-09-01", "After Hohenschönhausen creation"),
        ("1986-01-01", "After Pankow transfers"),
        ("1986-06-01", "After Hellersdorf creation"),
        ("1989-12-31", "End of Cold War")
    ]
    
    print(f"\n🗺️  Creating validation maps for {len(key_dates)} time periods...")
    
    all_stats = []
    for date, description in key_dates:
        print(f"\n📅 {description}")
        
        composition = get_assignments_at_date(assignments_data, date)
        filename = f"validation_maps/berlin_{date.replace('-', '_')}.html"
        stats = create_validation_map(composition, bezirke_data, ortsteil_geojson_wgs84, date, filename)
        stats['date'] = date
        stats['description'] = description
        all_stats.append(stats)
    
    # Final summary
    print(f"\n🎉 VALIDATION COMPLETE!")
    print(f"=" * 30)
    print(f"✅ Created {len(key_dates)} validation maps in 'validation_maps/'")
    print(f"📊 Data coverage: {len(in_both)} Ortsteil with complete data")
    
    if was_reprojected:
        print(f"🌍 Coordinates reprojected from UTM to WGS84")
        print(f"   Saved: moderne_ortsteile_wgs84.json")
    
    if only_assignments or only_geojson:
        print(f"\n⚠️  Data gaps found:")
        if only_assignments:
            print(f"   {len(only_assignments)} Ortsteil need polygon data")
        if only_geojson:
            print(f"   {len(only_geojson)} Ortsteil need historical assignments")
    
    print(f"\n📈 Administrative Evolution Summary:")
    for stat in all_stats:
        total = stat['east'] + stat['west']
        print(f"   {stat['date']}: {stat['east']} East + {stat['west']} West = {total} districts")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Open HTML maps in 'validation_maps/' to inspect boundaries")
    print(f"   2. If maps look correct, run: python updated_spatial_generator.py")
    print(f"   3. Import spatial summaries into Neo4j")
    print(f"   4. Assign stations to historical districts")
    
    print(f"\n💡 Files Ready for Neo4j:")
    if was_reprojected:
        print(f"   - Use moderne_ortsteile_wgs84.json for future processing")
    print(f"   - Run spatial summary generator next")

if __name__ == "__main__":
    main()