#!/usr/bin/env python3
"""
Spatial Summary Generator for Neo4j
===================================

Generates lightweight spatial summaries from full polygon data for efficient 
storage in Neo4j while keeping detailed geometries in external files.

This solves the polygon storage problem by:
1. Storing only centroids and bounding boxes in Neo4j
2. Keeping full geometries in organized external files
3. Enabling efficient spatial queries without large geometry data
"""

import json
import os
from pathlib import Path
import math

def calculate_polygon_centroid(coordinates):
    """Calculate centroid of a polygon using the shoelace formula"""
    # Handle different coordinate structures
    if isinstance(coordinates[0][0], list):
        # MultiPolygon or Polygon with holes - use first ring
        coords = coordinates[0] if len(coordinates[0]) > 2 else coordinates[0][0]
    else:
        # Simple polygon
        coords = coordinates
    
    # Remove last point if it duplicates the first (closed polygon)
    if len(coords) > 3 and coords[0] == coords[-1]:
        coords = coords[:-1]
    
    # Calculate centroid using shoelace formula
    area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    
    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        cross = coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
        area += cross
        centroid_x += (coords[i][0] + coords[j][0]) * cross
        centroid_y += (coords[i][1] + coords[j][1]) * cross
    
    if area == 0:
        # Fallback to simple average if shoelace fails
        centroid_x = sum(coord[0] for coord in coords) / len(coords)
        centroid_y = sum(coord[1] for coord in coords) / len(coords)
    else:
        area *= 3.0
        centroid_x /= area
        centroid_y /= area
    
    return centroid_x, centroid_y

def calculate_bounding_box(coordinates):
    """Calculate bounding box from polygon coordinates"""
    # Flatten all coordinates
    all_coords = []
    
    def flatten_coords(coord_list):
        for item in coord_list:
            if isinstance(item[0], list):
                flatten_coords(item)
            else:
                all_coords.append(item)
    
    flatten_coords(coordinates)
    
    if not all_coords:
        return None
    
    lons = [coord[0] for coord in all_coords]
    lats = [coord[1] for coord in all_coords]
    
    return {
        'min_lon': min(lons),
        'max_lon': max(lons),
        'min_lat': min(lats),
        'max_lat': max(lats)
    }

def calculate_area_km2(coordinates):
    """Calculate approximate area in km² using simple projection"""
    # This is a rough approximation - for precise area calculation,
    # use a proper geographic library like GeoPandas
    
    bbox = calculate_bounding_box(coordinates)
    if not bbox:
        return 0
    
    # Convert to approximate meters (rough)
    lat_center = (bbox['min_lat'] + bbox['max_lat']) / 2
    lon_diff = bbox['max_lon'] - bbox['min_lon']
    lat_diff = bbox['max_lat'] - bbox['min_lat']
    
    # Rough conversion (not accurate but good enough for comparison)
    meters_per_degree_lat = 111000  # approximately
    meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
    
    area_m2 = (lon_diff * meters_per_degree_lon) * (lat_diff * meters_per_degree_lat)
    area_km2 = area_m2 / 1000000
    
    return area_km2

def process_ortsteil_geometries(geojson_file):
    """Process Ortsteil geometries into spatial summaries"""
    print(f"Processing geometries from {geojson_file}...")
    
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    spatial_summaries = []
    geometry_files = {}
    
    # Create output directories
    os.makedirs("geometry_files", exist_ok=True)
    os.makedirs("geometry_files/ortsteil", exist_ok=True)
    
    for feature in geojson_data['features']:
        properties = feature['properties']
        geometry = feature['geometry']
        
        ortsteil_name = properties.get('nam')
        if not ortsteil_name:
            continue
        
        # Calculate spatial summary
        try:
            if geometry['type'] in ['Polygon', 'MultiPolygon']:
                coordinates = geometry['coordinates']
                
                # Calculate centroid
                centroid_lon, centroid_lat = calculate_polygon_centroid(coordinates)
                
                # Calculate bounding box
                bbox = calculate_bounding_box(coordinates)
                
                # Calculate approximate area
                area_km2 = calculate_area_km2(coordinates)
                
                # Create clean filename
                clean_name = ortsteil_name.replace(' ', '_').replace('/', '_').replace('-', '_')
                geometry_filename = f"geometry_files/ortsteil/{clean_name}.json"
                
                # Save individual geometry file
                individual_geometry = {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": geometry
                }
                
                with open(geometry_filename, 'w', encoding='utf-8') as f:
                    json.dump(individual_geometry, f, ensure_ascii=False, indent=2)
                
                # Create spatial summary
                spatial_summary = {
                    "ortsteil_name": ortsteil_name,
                    "centroid_lat": round(centroid_lat, 8),
                    "centroid_lon": round(centroid_lon, 8),
                    "bbox_min_lat": round(bbox['min_lat'], 8),
                    "bbox_max_lat": round(bbox['max_lat'], 8),
                    "bbox_min_lon": round(bbox['min_lon'], 8),
                    "bbox_max_lon": round(bbox['max_lon'], 8),
                    "area_km2": round(area_km2, 6),
                    "geometry_type": geometry['type'],
                    "geometry_file": geometry_filename,
                    "properties": {k: v for k, v in properties.items() if k != 'geometry'}
                }
                
                spatial_summaries.append(spatial_summary)
                geometry_files[ortsteil_name] = geometry_filename
                
        except Exception as e:
            print(f"Warning: Could not process {ortsteil_name}: {e}")
            continue
    
    print(f"Processed {len(spatial_summaries)} Ortsteil geometries")
    return spatial_summaries, geometry_files

def create_station_assignment_helpers(spatial_summaries):
    """Create helper data for station assignment"""
    print("Creating station assignment helpers...")
    
    # Create a lookup structure for fast station assignment
    assignment_grid = {}
    
    for summary in spatial_summaries:
        # Create grid cells for faster lookup (0.01 degree grid ≈ 1km)
        min_lat_grid = math.floor(summary['bbox_min_lat'] * 100) / 100
        max_lat_grid = math.ceil(summary['bbox_max_lat'] * 100) / 100
        min_lon_grid = math.floor(summary['bbox_min_lon'] * 100) / 100
        max_lon_grid = math.ceil(summary['bbox_max_lon'] * 100) / 100
        
        lat = min_lat_grid
        while lat <= max_lat_grid:
            lon = min_lon_grid
            while lon <= max_lon_grid:
                grid_key = f"{lat:.2f},{lon:.2f}"
                if grid_key not in assignment_grid:
                    assignment_grid[grid_key] = []
                assignment_grid[grid_key].append(summary['ortsteil_name'])
                lon += 0.01
            lat += 0.01
    
    return assignment_grid

def generate_neo4j_cypher_templates(spatial_summaries):
    """Generate Cypher query templates for Neo4j import"""
    
    cypher_queries = {
        "create_spatial_properties": """
// Add spatial properties to Ortsteil nodes
CALL apoc.load.json("file:///path/to/ortsteil_spatial_summary.json") YIELD value
UNWIND value AS spatial
MATCH (o:Ortsteil {name: spatial.ortsteil_name})
SET 
  o.centroid_lat = spatial.centroid_lat,
  o.centroid_lon = spatial.centroid_lon,
  o.bbox_min_lat = spatial.bbox_min_lat,
  o.bbox_max_lat = spatial.bbox_max_lat,
  o.bbox_min_lon = spatial.bbox_min_lon,
  o.bbox_max_lon = spatial.bbox_max_lon,
  o.area_km2 = spatial.area_km2,
  o.geometry_type = spatial.geometry_type,
  o.geometry_file = spatial.geometry_file;
""",
        
        "create_spatial_indexes": """
// Create spatial indexes for efficient queries
CREATE INDEX ortsteil_centroid IF NOT EXISTS FOR (o:Ortsteil) ON (o.centroid_lat, o.centroid_lon);
CREATE INDEX ortsteil_bbox IF NOT EXISTS FOR (o:Ortsteil) ON (o.bbox_min_lat, o.bbox_max_lat, o.bbox_min_lon, o.bbox_max_lon);
CREATE INDEX station_coords IF NOT EXISTS FOR (s:Station) ON (s.latitude, s.longitude);
""",
        
        "assign_stations_to_ortsteil": """
// Assign stations to Ortsteil using bounding box containment
MATCH (s:Station), (o:Ortsteil)
WHERE s.latitude >= o.bbox_min_lat 
  AND s.latitude <= o.bbox_max_lat
  AND s.longitude >= o.bbox_min_lon 
  AND s.longitude <= o.bbox_max_lon
WITH s, o, 
     // Calculate distance to centroid for tie-breaking
     sqrt(pow(s.latitude - o.centroid_lat, 2) + pow(s.longitude - o.centroid_lon, 2)) AS distance
ORDER BY s.stop_id, distance
WITH s, collect(o)[0] AS closest_ortsteil
WHERE closest_ortsteil IS NOT NULL
CREATE (s)-[:LOCATED_IN_ORTSTEIL {
  assignment_method: "bbox_containment",
  assignment_date: datetime(),
  confidence: "approximate"
}]->(closest_ortsteil);
"""
    }
    
    return cypher_queries

def main():
    """Main processing workflow"""
    print("🗺️  Berlin Spatial Summary Generator")
    print("=" * 40)
    
    # Check input file
    geojson_file = "moderne_ortsteile.json"
    if not os.path.exists(geojson_file):
        print(f"❌ Error: Could not find {geojson_file}")
        print("Make sure you have the moderne_ortsteile.json file in the current directory")
        return
    
    # Process geometries
    spatial_summaries, geometry_files = process_ortsteil_geometries(geojson_file)
    
    if not spatial_summaries:
        print("❌ No spatial summaries generated")
        return
    
    # Save spatial summary for Neo4j
    output_file = "ortsteil_spatial_summary.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spatial_summaries, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved spatial summary: {output_file}")
    
    # Create station assignment helpers
    assignment_grid = create_station_assignment_helpers(spatial_summaries)
    
    with open("station_assignment_grid.json", 'w', encoding='utf-8') as f:
        json.dump(assignment_grid, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved assignment grid: station_assignment_grid.json")
    
    # Generate Cypher templates
    cypher_queries = generate_neo4j_cypher_templates(spatial_summaries)
    
    with open("neo4j_spatial_import.cypher", 'w', encoding='utf-8') as f:
        f.write("// Neo4j Spatial Data Import Queries\n")
        f.write("// =====================================\n\n")
        for name, query in cypher_queries.items():
            f.write(f"// {name.replace('_', ' ').title()}\n")
            f.write(query)
            f.write("\n\n")
    
    print(f"✅ Saved Cypher queries: neo4j_spatial_import.cypher")
    
    # Summary statistics
    total_area = sum(s['area_km2'] for s in spatial_summaries)
    avg_area = total_area / len(spatial_summaries)
    
    print(f"\n📊 SPATIAL SUMMARY STATISTICS:")
    print(f"   Ortsteil processed: {len(spatial_summaries)}")
    print(f"   Total area: {total_area:.2f} km²")
    print(f"   Average area: {avg_area:.2f} km²")
    print(f"   Geometry files created: {len(geometry_files)}")
    print(f"   Assignment grid cells: {len(assignment_grid)}")
    
    # Show largest and smallest Ortsteil
    largest = max(spatial_summaries, key=lambda x: x['area_km2'])
    smallest = min(spatial_summaries, key=lambda x: x['area_km2'])
    
    print(f"\n📏 SIZE RANGE:")
    print(f"   Largest: {largest['ortsteil_name']} ({largest['area_km2']:.2f} km²)")
    print(f"   Smallest: {smallest['ortsteil_name']} ({smallest['area_km2']:.2f} km²)")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Review the generated files:")
    print(f"      - {output_file} (for Neo4j import)")
    print(f"      - geometry_files/ortsteil/ (individual polygon files)")
    print(f"      - neo4j_spatial_import.cypher (import queries)")
    print(f"   2. Import spatial summaries into Neo4j using the Cypher file")
    print(f"   3. Run station assignment queries")
    print(f"   4. Use validation script to check results")
    print(f"\n💡 STORAGE EFFICIENCY:")
    print(f"   - Neo4j stores only ~{len(spatial_summaries) * 8 * 9} bytes of spatial data")
    print(f"   - Full geometries kept in organized external files")
    print(f"   - Enables fast spatial queries without geometry overhead")

if __name__ == "__main__":
    main()