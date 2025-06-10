#!/usr/bin/env python3
"""
Core Entities Population Script for Berlin Transport Knowledge Graph

This script creates CoreStation and CoreLine entities that represent persistent
transport infrastructure across multiple yearly snapshots. It operates as a
layer above the existing populate_db.py script.

Usage:
    python src/populate_core_entities.py [options]

Dependencies:
    - Neo4j database populated with yearly snapshot data
    - populate_db.py script results (stations, lines by year)
"""

import logging
import argparse
import sys
import os
import math
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import json
import re

# Add the src directory to the Python path
sys.path.append(str(Path('./src').resolve()))
from db_connector import BerlinTransportDB

DEFAULT_DB_URI = "neo4j+s://6ae11f66.databases.neo4j.io" # neo4j+s://6ae11f66.databases.neo4j.io or bolt://100.82.176.18:7687
DEFAULT_DB_USER = "neo4j"
DEFAULT_DB_PASSWORD = os.environ.get("NEO4J_AURA_PASSWORD") # NEO4J_AURA_PASSWORD or NEO4J_PASSWORD


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class ActivityPeriod:
    """Represents the activity period of a station or line based on snapshot observations"""
    start_snapshot: int
    end_snapshot: int
    observed_snapshots: List[int]
    missing_snapshots: List[int]
    missing_reasons: Dict[int, str]  # snapshot -> reason (e.g., "closure", "data_gap", etc.)
    
    def to_dict(self) -> Dict:
        return {
            "start_snapshot": self.start_snapshot,
            "end_snapshot": self.end_snapshot,
            "observed_snapshots": sorted(self.observed_snapshots),
            "missing_snapshots": sorted(self.missing_snapshots),
            "missing_reasons": self.missing_reasons,
            "total_period_years": self.end_snapshot - self.start_snapshot,
            "observation_rate": len(self.observed_snapshots) / len(self.get_all_snapshots_in_period()) if self.get_all_snapshots_in_period() else 0
        }
    
    def to_json_string(self) -> str:
        """Convert to JSON string for Neo4j storage"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json_string(cls, json_str: str) -> 'ActivityPeriod':
        """Create ActivityPeriod from JSON string"""
        if not json_str:
            return cls(0, 0, [], [], {})
        
        data = json.loads(json_str)
        return cls(
            start_snapshot=data.get("start_snapshot", 0),
            end_snapshot=data.get("end_snapshot", 0),
            observed_snapshots=data.get("observed_snapshots", []),
            missing_snapshots=data.get("missing_snapshots", []),
            missing_reasons={int(k): v for k, v in data.get("missing_reasons", {}).items()}
        )
    
    def get_all_snapshots_in_period(self) -> List[int]:
        """Get all available snapshots in the period, regardless of observation"""
        return sorted(set(self.observed_snapshots + self.missing_snapshots))

@dataclass
class StationCandidate:
    """Represents a potential CoreStation based on snapshot analysis"""
    name: str
    type: str
    location: Tuple[float, float]  # (lat, lng)
    east_west: str
    snapshot_ids: Set[str]
    snapshots: Set[int]  # Changed from years to snapshots
    source_confidence: float
    
    def get_activity_period(self, available_snapshots: List[int]) -> ActivityPeriod:
        """Calculate activity period from available snapshots"""
        if not self.snapshots:
            return ActivityPeriod(0, 0, [], [], {})
        
        observed_snapshots = sorted(self.snapshots)
        start_snapshot = observed_snapshots[0]
        end_snapshot = observed_snapshots[-1]
        
        # Find all snapshots that should exist in this period
        period_snapshots = [s for s in available_snapshots 
                          if start_snapshot <= s <= end_snapshot]
        
        # Identify missing snapshots
        missing_snapshots = [s for s in period_snapshots 
                           if s not in observed_snapshots]
        
        # Initialize missing reasons (can be updated later)
        missing_reasons = {s: "data_gap" for s in missing_snapshots}
        
        return ActivityPeriod(
            start_snapshot=start_snapshot,
            end_snapshot=end_snapshot,
            observed_snapshots=observed_snapshots,
            missing_snapshots=missing_snapshots,
            missing_reasons=missing_reasons
        )

@dataclass
class LineCandidate:
    """Represents a potential CoreLine based on snapshot analysis"""
    name: str
    type: str
    east_west: str
    snapshot_ids: Set[str]
    snapshots: Set[int]  
    source_confidence: float
    
    def get_activity_period(self, available_snapshots: List[int]) -> ActivityPeriod:
        """Calculate activity period from available snapshots"""
        if not self.snapshots:
            return ActivityPeriod(0, 0, [], [], {})
        
        observed_snapshots = sorted(self.snapshots)
        start_snapshot = observed_snapshots[0]
        end_snapshot = observed_snapshots[-1]
        
        # Find all snapshots that should exist in this period
        period_snapshots = [s for s in available_snapshots 
                          if start_snapshot <= s <= end_snapshot]
        
        # Identify missing snapshots
        missing_snapshots = [s for s in period_snapshots 
                           if s not in observed_snapshots]
        
        # Initialize missing reasons
        missing_reasons = {s: "data_gap" for s in missing_snapshots}
        
        return ActivityPeriod(
            start_snapshot=start_snapshot,
            end_snapshot=end_snapshot,
            observed_snapshots=observed_snapshots,
            missing_snapshots=missing_snapshots,
            missing_reasons=missing_reasons
        )

class CoreEntityResolver:
    """Handles the logic for resolving snapshot entities into core entities"""
    
    def __init__(self, db: BerlinTransportDB):
        self.db = db
        self.station_candidates: Dict[str, StationCandidate] = {}
        self.line_candidates: Dict[str, LineCandidate] = {}
        self.available_snapshots: List[int] = []
        self._load_available_snapshots()
        
    def _load_available_snapshots(self):
        """Load all available snapshot years from the database"""
        self.db.connect()  # Add this line to connect before using the driver
        with self.db.driver.session() as session:
            result = session.run("""
            MATCH (y:Year)
            RETURN y.year as year
            ORDER BY y.year ASC
            """)
            self.available_snapshots = [record["year"] for record in result]
            logger.info(f"Found snapshots: {self.available_snapshots}")
    
    def _get_connected_stations(self) -> Dict[str, Set[str]]:
        """Get all stations that are connected via CONNECTS_TO relationships"""
        connected_pairs = defaultdict(set)
        self.db.connect() 
        with self.db.driver.session() as session:
            result = session.run("""
            MATCH (s1:Station)-[:CONNECTS_TO]-(s2:Station)
            RETURN s1.stop_id as station1, s2.stop_id as station2
            """)
            
            for record in result:
                station1 = record["station1"]
                station2 = record["station2"]
                connected_pairs[station1].add(station2)
                connected_pairs[station2].add(station1)
        
        logger.info(f"Found {len(connected_pairs)} stations with connections")
        return dict(connected_pairs)
    
    def analyze_snapshot_stations(self) -> Dict[str, StationCandidate]:
        """
        Analyze all snapshot stations and group them into CoreStation candidates
        
        Returns:
            Dictionary of core_station_id -> StationCandidate
        """
        logger.info("Analyzing snapshot stations for CoreStation candidates...")
        
        # Get connected stations to avoid grouping consecutive stations
        connected_stations = self._get_connected_stations()
        self.db.connect() 
        with self.db.driver.session() as session:
            # Get all snapshot stations
            result = session.run("""
            MATCH (s:Station)-[:IN_YEAR]->(y:Year)
            RETURN s.stop_id as stop_id, s.name as name, s.type as type,
                   s.latitude as latitude, s.longitude as longitude,
                   s.east_west as east_west, y.year as year,
                   s.source as source
            ORDER BY s.name, y.year
            """)
            
            # Group stations by name and type (basic entity resolution)
            station_groups = defaultdict(list)
            
            for record in result:
                if record["latitude"] and record["longitude"]:
                    key = (record["name"], record["type"], record["east_west"])
                    station_groups[key].append({
                        "stop_id": record["stop_id"],
                        "name": record["name"],
                        "type": record["type"],
                        "latitude": float(record["latitude"]),
                        "longitude": float(record["longitude"]),
                        "east_west": record["east_west"],
                        "year": record["year"],
                        "source": record["source"]
                    })
        
        # Create CoreStation candidates with connection-aware grouping
        candidates = {}
        
        for (name, transport_type, east_west), stations in station_groups.items():
            if len(stations) == 0:
                continue
            
            # Check if any stations in this group are connected to each other
            # If so, we might need to split them into separate core entities
            station_ids = [s["stop_id"] for s in stations]
            
            # Find connected components within this group
            connected_components = self._find_connected_components(station_ids, connected_stations)
            
            # Create separate candidates for each connected component
            for component_idx, component_stations in enumerate(connected_components):
                component_data = [s for s in stations if s["stop_id"] in component_stations]
                
                if len(component_data) == 0:
                    continue
                
                # Calculate representative location (average)
                avg_lat = sum(s["latitude"] for s in component_data) / len(component_data)
                avg_lng = sum(s["longitude"] for s in component_data) / len(component_data)
                
                # Generate core station ID
                suffix = f"_{component_idx}" if len(connected_components) > 1 else ""
                core_id = f"core_{name.replace(' ', '_').lower()}_{transport_type}_{east_west}{suffix}"
                
                # Calculate confidence based on consistency
                confidence = self._calculate_station_confidence(component_data)
                
                candidates[core_id] = StationCandidate(
                    name=name,
                    type=transport_type,
                    location=(avg_lat, avg_lng),
                    east_west=east_west,
                    snapshot_ids={s["stop_id"] for s in component_data},
                    snapshots={s["year"] for s in component_data},
                    source_confidence=confidence
                )
        
        logger.info(f"Identified {len(candidates)} CoreStation candidates")
        return candidates
    
    def _find_connected_components(self, station_ids: List[str], 
                                 connected_stations: Dict[str, Set[str]]) -> List[Set[str]]:
        """
        Find connected components among a set of stations to avoid grouping 
        consecutive stations on the same line
        """
        if len(station_ids) <= 1:
            return [set(station_ids)]
        
        # Check if any stations are connected to each other
        has_connections = any(
            any(other_id in connected_stations.get(station_id, set()) 
                for other_id in station_ids if other_id != station_id)
            for station_id in station_ids
        )
        
        if not has_connections:
            # No connections found, group all together
            return [set(station_ids)]
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        for station_id in station_ids:
            if station_id not in visited:
                component = set()
                self._dfs_component(station_id, station_ids, connected_stations, visited, component)
                if component:
                    components.append(component)
        
        return components
    
    def _dfs_component(self, station_id: str, valid_stations: List[str],
                      connected_stations: Dict[str, Set[str]], 
                      visited: Set[str], component: Set[str]):
        """DFS to find connected component"""
        if station_id in visited or station_id not in valid_stations:
            return
        
        visited.add(station_id)
        component.add(station_id)
        
        # Visit connected stations that are also in our candidate group
        for connected_id in connected_stations.get(station_id, set()):
            if connected_id in valid_stations:
                self._dfs_component(connected_id, valid_stations, connected_stations, visited, component)
    
    def analyze_snapshot_lines(self, core_stations: Dict[str, StationCandidate]) -> Dict[str, LineCandidate]:
        """
        Analyze all snapshot lines and group them into CoreLine candidates
        
        Args:
            core_stations: Dictionary of CoreStation candidates for reference
            
        Returns:
            Dictionary of core_line_id -> LineCandidate
        """
        logger.info("Analyzing snapshot lines for CoreLine candidates...")
        
        self.db.connect()
        with self.db.driver.session() as session:
            # Get all snapshot lines
            result = session.run("""
            MATCH (l:Line)-[:IN_YEAR]->(y:Year)
            RETURN l.line_id as line_id, l.name as name, l.type as type,
                l.east_west as east_west, y.year as year
            ORDER BY l.name, y.year
            """)
            
            # Group lines by name and type (including east_west initially)
            line_groups = defaultdict(list)
            
            for record in result:
                key = (record["name"], record["type"], record["east_west"])
                line_groups[key].append({
                    "line_id": record["line_id"],
                    "name": record["name"],
                    "type": record["type"],
                    "east_west": record["east_west"],
                    "year": record["year"]
                })
        
        # Resolve unified lines with east/west counterparts
        resolved_groups = self._resolve_unified_lines(dict(line_groups))
        
        # Create CoreLine candidates from resolved groups
        candidates = {}
        
        for (name, transport_type, east_west), lines in resolved_groups.items():
            if len(lines) == 0:
                continue
                
            # Generate core line ID
            core_id = f"core_line_{name.replace(' ', '_').lower()}_{transport_type}_{east_west}"
            
            confidence = self._calculate_line_confidence(lines)
            
            candidates[core_id] = LineCandidate(
                name=name,
                type=transport_type,
                east_west=east_west,
                snapshot_ids={l["line_id"] for l in lines},
                snapshots={l["year"] for l in lines},
                source_confidence=confidence
            )
        
        logger.info(f"Identified {len(candidates)} CoreLine candidates after resolution")
        return candidates

    def _resolve_unified_lines(self, line_groups: Dict) -> Dict:
        """
        Merge 'unified' lines with their appropriate 'east' or 'west' counterparts
        based on the geographic location of the stations they serve
        
        Args:
            line_groups: Dictionary with (name, type, east_west) -> lines data
            
        Returns:
            Updated line_groups with unified lines merged appropriately
        """
        logger.info("Resolving unified lines with east/west counterparts...")
        
        # Berlin dividing line (approximate longitude that separates East/West Berlin)
        # The Berlin Wall roughly followed longitude 13.4 degrees
        BERLIN_DIVIDING_LONGITUDE = 13.4
        
        resolved_groups = {}
        unified_groups = {}
        
        # Separate unified lines from others
        for key, lines in line_groups.items():
            name, transport_type, east_west = key
            if east_west == "unified":
                unified_groups[key] = lines
            else:
                resolved_groups[key] = lines
        
        # Process each unified line
        for unified_key, unified_lines in unified_groups.items():
            name, transport_type, _ = unified_key
            
            # Check if east/west counterparts exist
            east_key = (name, transport_type, "east")
            west_key = (name, transport_type, "west")
            
            has_east = east_key in resolved_groups
            has_west = west_key in resolved_groups
            
            if has_east or has_west:
                # Determine which side this unified line belongs to
                side = self._determine_line_side(unified_lines, BERLIN_DIVIDING_LONGITUDE)
                
                if side == "east" and has_east:
                    # Merge with east line
                    resolved_groups[east_key].extend(unified_lines)
                    logger.info(f"Merged unified line {name} ({transport_type}) with east counterpart")
                elif side == "west" and has_west:
                    # Merge with west line  
                    resolved_groups[west_key].extend(unified_lines)
                    logger.info(f"Merged unified line {name} ({transport_type}) with west counterpart")
                elif side == "east" and not has_east:
                    # Create as east line
                    resolved_groups[east_key] = unified_lines
                    logger.info(f"Converted unified line {name} ({transport_type}) to east")
                elif side == "west" and not has_west:
                    # Create as west line
                    resolved_groups[west_key] = unified_lines  
                    logger.info(f"Converted unified line {name} ({transport_type}) to west")
                else:
                    # Fallback: keep as unified
                    resolved_groups[unified_key] = unified_lines
                    logger.warning(f"Could not resolve unified line {name} ({transport_type}), keeping as unified")
            else:
                # No east/west counterparts exist, determine side and create appropriate entry
                side = self._determine_line_side(unified_lines, BERLIN_DIVIDING_LONGITUDE)
                new_key = (name, transport_type, side)
                resolved_groups[new_key] = unified_lines
                logger.info(f"Converted standalone unified line {name} ({transport_type}) to {side}")
        
        logger.info(f"Resolved {len(unified_groups)} unified lines")
        return resolved_groups

    def _determine_line_side(self, lines: List[Dict], dividing_longitude: float) -> str:
        """
        Determine whether a line belongs to east or west based on station locations
        
        Args:
            lines: List of line records with line_id
            dividing_longitude: Longitude that divides east/west
            
        Returns:
            "east" or "west"
        """
        self.db.connect()
        
        all_longitudes = []
        
        with self.db.driver.session() as session:
            for line in lines:
                # Get stations served by this line
                result = session.run("""
                MATCH (l:Line {line_id: $line_id})-[:SERVES]->(s:Station)
                WHERE s.longitude IS NOT NULL
                RETURN s.longitude as longitude
                """, line_id=line["line_id"])
                
                longitudes = [record["longitude"] for record in result]
                all_longitudes.extend(longitudes)
        
        if not all_longitudes:
            logger.warning(f"No station coordinates found for line, defaulting to 'unified'")
            return "unified"
        
        # Calculate average longitude
        avg_longitude = sum(all_longitudes) / len(all_longitudes)
        
        # Determine side based on Berlin dividing line
        side = "east" if avg_longitude > dividing_longitude else "west"
        
        logger.debug(f"Line average longitude: {avg_longitude:.4f}, assigned to: {side}")
        return side

    def _calculate_station_confidence(self, stations: List[Dict]) -> float:
        """Calculate confidence score for station entity resolution"""
        if len(stations) <= 1:
            return 1.0
            
        # Check location consistency
        locations = [(s["latitude"], s["longitude"]) for s in stations]
        max_distance = self._calculate_max_distance(locations)
        
        # Confidence decreases with distance variance
        # Stations within 200m get high confidence
        if max_distance <= 200:
            return 0.95
        elif max_distance <= 250:
            return 0.8
        elif max_distance <= 300:
            return 0.6
        else:
            return 0.3
    
    def _calculate_line_confidence(self, lines: List[Dict]) -> float:
        """Calculate confidence score for line entity resolution"""
        # For now, simple confidence based on consistency
        return 0.9 if len(lines) > 1 else 1.0
    
    def _calculate_max_distance(self, locations: List[Tuple[float, float]]) -> float:
        """Calculate maximum Manhattan distance between locations in meters"""
        if len(locations) <= 1:
            return 0.0
        
        def manhattan_distance(lat1, lon1, lat2, lon2):
            """
            Calculate Manhattan distance between two points in meters
            Uses the street grid assumption typical in urban environments
            """
            # Convert latitude/longitude differences to meters
            # Rough approximation: 1 degree latitude ≈ 111,000 meters
            # 1 degree longitude ≈ 111,000 * cos(latitude) meters
            avg_lat = (lat1 + lat2) / 2
            lat_diff_m = abs(lat2 - lat1) * 111000
            lon_diff_m = abs(lon2 - lon1) * 111000 * abs(math.cos(math.radians(avg_lat)))
            return lat_diff_m + lon_diff_m
        
        max_dist = 0
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                lat1, lon1 = locations[i]
                lat2, lon2 = locations[j]
                dist = manhattan_distance(lat1, lon1, lat2, lon2)
                max_dist = max(max_dist, dist)
        
        return max_dist

class CoreEntityPopulator:
    """Handles the creation and population of core entities in Neo4j"""
    
    def __init__(self, db: BerlinTransportDB, resolver: CoreEntityResolver, dry_run: bool = False):
        self.db = db
        self.resolver = resolver
        self.dry_run = dry_run

    def _analyze_core_connections(self, 
                                station_candidates: Dict[str, StationCandidate],
                                line_candidates: Dict[str, LineCandidate]) -> Dict[str, Dict[str, Dict]]:
        """
        Analyze which CoreStations are served by which CoreLines based on snapshot data
        
        Returns:
            Dict[core_line_id, Dict[core_station_id, connection_info]]
        """
        logger.info("Analyzing CoreStation-CoreLine connections...")
        
        self.db.connect()
        
        # Create reverse mapping: snapshot_station_id -> core_station_id
        snapshot_to_core_station = {}
        for core_station_id, station_candidate in station_candidates.items():
            for snapshot_id in station_candidate.snapshot_ids:
                snapshot_to_core_station[snapshot_id] = core_station_id
        
        # Create reverse mapping: snapshot_line_id -> core_line_id  
        snapshot_to_core_line = {}
        for core_line_id, line_candidate in line_candidates.items():
            for snapshot_id in line_candidate.snapshot_ids:
                snapshot_to_core_line[snapshot_id] = core_line_id
        
        # Query all line-station SERVES relationships
        with self.db.driver.session() as session:
            result = session.run("""
            MATCH (l:Line)-[serves:SERVES]->(s:Station)
            MATCH (l)-[:IN_YEAR]->(y1:Year)
            MATCH (s)-[:IN_YEAR]->(y2:Year)
            WHERE y1.year = y2.year
            RETURN l.line_id as line_id, s.stop_id as station_id, 
                y1.year as year, serves.stop_order as stop_order
            """)
            
            # Build connections map
            core_connections = defaultdict(lambda: defaultdict(lambda: {
                'overlapping_snapshots': [],
                'strength': 0.0
            }))
            
            for record in result:
                snapshot_line_id = record["line_id"]
                snapshot_station_id = record["station_id"]
                year = record["year"]
                
                # Map to core entities
                core_line_id = snapshot_to_core_line.get(snapshot_line_id)
                core_station_id = snapshot_to_core_station.get(snapshot_station_id)
                
                if core_line_id and core_station_id:
                    connection = core_connections[core_line_id][core_station_id]
                    connection['overlapping_snapshots'].append(year)
                    connection['strength'] += 1.0  # Could be more sophisticated
            
            # Calculate final strength scores
            for core_line_id in core_connections:
                for core_station_id in core_connections[core_line_id]:
                    connection = core_connections[core_line_id][core_station_id]
                    # Strength based on number of years the connection exists
                    total_years = len(connection['overlapping_snapshots'])
                    connection['strength'] = total_years / len(self.resolver.available_snapshots)
                    connection['overlapping_snapshots'] = sorted(set(connection['overlapping_snapshots']))
        
        logger.info(f"Found connections between {len(core_connections)} CoreLines and stations")
        return dict(core_connections)


    def create_core_entity_relationships(self, 
                                    station_candidates: Dict[str, StationCandidate],
                                    line_candidates: Dict[str, LineCandidate]) -> int:
        """
        Create relationships between CoreStations and CoreLines based on snapshot data
        
        Args:
            station_candidates: CoreStation candidates
            line_candidates: CoreLine candidates
            
        Returns:
            Number of relationships created
        """
        logger.info("Creating CoreStation-CoreLine relationships...")
        
        if self.dry_run:
            # Calculate potential relationships for dry run
            potential_relationships = 0
            core_connections = self._analyze_core_connections(station_candidates, line_candidates)
            for line_id, served_stations in core_connections.items():
                potential_relationships += len(served_stations)
            
            logger.info(f"[DRY RUN] Would create {potential_relationships} SERVES_CORE relationships")
            return potential_relationships
        
        # Analyze which CoreStations are served by which CoreLines
        core_connections = self._analyze_core_connections(station_candidates, line_candidates)
        
        relationships_created = 0
        
        self.db.connect()
        with self.db.driver.session() as session:
            for core_line_id, served_core_stations in core_connections.items():
                for core_station_id, connection_info in served_core_stations.items():
                    # Create SERVES_CORE relationship between CoreLine and CoreStation
                    result = session.run("""
                    MATCH (cl:CoreLine {core_line_id: $line_id})
                    MATCH (cs:CoreStation {core_id: $station_id})
                    MERGE (cl)-[r:SERVES_CORE]->(cs)
                    ON CREATE SET 
                        r.created_date = datetime(),
                        r.overlapping_snapshots = $snapshots,
                        r.connection_strength = $strength
                    ON MATCH SET
                        r.updated_date = datetime(),
                        r.overlapping_snapshots = $snapshots,
                        r.connection_strength = $strength
                    RETURN count(r) as created
                    """,
                    line_id=core_line_id,
                    station_id=core_station_id,
                    snapshots=connection_info['overlapping_snapshots'],
                    strength=connection_info['strength']
                    )
                    
                    if result.single()["created"]:
                        relationships_created += 1
                    
                    # Also add the line to the station's in_lines property
                    session.run("""
                    MATCH (cs:CoreStation {core_id: $station_id})
                    SET cs.in_lines = CASE 
                        WHEN cs.in_lines IS NULL THEN [$line_id]
                        WHEN NOT $line_id IN cs.in_lines THEN cs.in_lines + [$line_id]
                        ELSE cs.in_lines
                    END
                    """,
                    station_id=core_station_id,
                    line_id=core_line_id
                    )
        
        logger.info(f"Created {relationships_created} CoreStation-CoreLine relationships")
        return relationships_created
            
    def populate_core_stations(self, candidates: Dict[str, StationCandidate]) -> int:
        """
        Create CoreStation nodes and link them to snapshot stations
        
        Args:
            candidates: Dictionary of CoreStation candidates
            
        Returns:
            Number of CoreStations created or updated
        """
        logger.info(f"Creating/updating {len(candidates)} CoreStation nodes...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would create/update CoreStation nodes")
            return len(candidates)
            
        created_count = 0
        updated_count = 0
        
        self.db.connect()
        with self.db.driver.session() as session:
            for core_id, candidate in candidates.items():
                # Check if CoreStation already exists
                existing_result = session.run("""
                MATCH (cs:CoreStation {core_id: $core_id})
                RETURN cs.activity_period as current_period
                """, core_id=core_id)
                
                existing_record = existing_result.single()
                activity_period = candidate.get_activity_period(self.resolver.available_snapshots)
                
                if existing_record:
                    # Update existing CoreStation
                    # Merge the new activity period with existing one
                    current_period_json = existing_record["current_period"]
                    if current_period_json:
                        current_period = ActivityPeriod.from_json_string(current_period_json)
                        updated_period = self._merge_activity_periods(current_period.to_dict(), activity_period)
                    else:
                        updated_period = activity_period
                    
                    session.run("""
                    MATCH (cs:CoreStation {core_id: $core_id})
                    SET cs.activity_period = $activity_period,
                        cs.source_confidence = $confidence,
                        cs.updated_date = datetime(),
                        cs.latitude = $latitude,
                        cs.longitude = $longitude
                    """, 
                    core_id=core_id,
                    activity_period=updated_period.to_json_string(),
                    confidence=candidate.source_confidence,
                    latitude=candidate.location[0],
                    longitude=candidate.location[1]
                    )
                    updated_count += 1
                else:
                    # Create new CoreStation
                    result = session.run("""
                    CREATE (cs:CoreStation {
                        core_id: $core_id,
                        name: $name,
                        type: $type,
                        latitude: $latitude,
                        longitude: $longitude,
                        east_west: $east_west,
                        activity_period: $activity_period,
                        source_confidence: $confidence,
                        created_date: datetime(),
                        source: 'core_entity_resolver'
                    })
                    RETURN cs.core_id as created_id
                    """, 
                    core_id=core_id,
                    name=candidate.name,
                    type=candidate.type,
                    latitude=candidate.location[0],
                    longitude=candidate.location[1],
                    east_west=candidate.east_west,
                    activity_period=activity_period.to_json_string(),
                    confidence=candidate.source_confidence
                    )
                    
                    if result.single():
                        created_count += 1
                
                # Link to snapshot stations (create new relationships)
                for snapshot_id in candidate.snapshot_ids:
                    session.run("""
                    MATCH (cs:CoreStation {core_id: $core_id})
                    MATCH (s:Station {stop_id: $snapshot_id})
                    MERGE (cs)-[:HAS_SNAPSHOT {
                        created_date: datetime(),
                        confidence: $confidence
                    }]->(s)
                    """, 
                    core_id=core_id,
                    snapshot_id=snapshot_id,
                    confidence=candidate.source_confidence
                    )
        
        logger.info(f"Created {created_count} new CoreStation nodes, updated {updated_count} existing ones")
        return created_count + updated_count

    def _merge_activity_periods(self, current_period: Dict, new_period: ActivityPeriod) -> ActivityPeriod:
        """
        Merge a new activity period with an existing one when updating CoreStations
        """
        if not current_period:
            return new_period
        
        # Extract current period data
        current_start = current_period.get("start_snapshot", new_period.start_snapshot)
        current_end = current_period.get("end_snapshot", new_period.end_snapshot)
        current_observed = set(current_period.get("observed_snapshots", []))
        current_missing = set(current_period.get("missing_snapshots", []))
        current_reasons = current_period.get("missing_reasons", {})
        
        # Convert string keys back to integers if needed
        if isinstance(current_reasons, dict):
            current_reasons = {int(k) if isinstance(k, str) else k: v for k, v in current_reasons.items()}
        
        # Merge with new period
        merged_start = min(current_start, new_period.start_snapshot)
        merged_end = max(current_end, new_period.end_snapshot)
        merged_observed = current_observed.union(set(new_period.observed_snapshots))
        
        # Recalculate missing snapshots based on merged data
        all_snapshots_in_period = [s for s in self.resolver.available_snapshots 
                                if merged_start <= s <= merged_end]
        merged_missing = [s for s in all_snapshots_in_period if s not in merged_observed]
        
        # Merge missing reasons, preferring existing reasons
        merged_reasons = dict(current_reasons)
        for snapshot, reason in new_period.missing_reasons.items():
            if snapshot not in merged_reasons:
                merged_reasons[snapshot] = reason
        
        return ActivityPeriod(
            start_snapshot=merged_start,
            end_snapshot=merged_end,
            observed_snapshots=sorted(merged_observed),
            missing_snapshots=merged_missing,
            missing_reasons=merged_reasons
        )

    def populate_core_lines(self, candidates: Dict[str, LineCandidate]) -> int:
        """
        Create CoreLine nodes and link them to snapshot lines
        
        Args:
            candidates: Dictionary of CoreLine candidates
            
        Returns:
            Number of CoreLines created or updated
        """
        logger.info(f"Creating/updating {len(candidates)} CoreLine nodes...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would create/update CoreLine nodes")
            return len(candidates)
            
        created_count = 0
        updated_count = 0
        
        self.db.connect()
        with self.db.driver.session() as session:
            for core_id, candidate in candidates.items():
                # Check if CoreLine already exists
                existing_result = session.run("""
                MATCH (cl:CoreLine {core_line_id: $core_id})
                RETURN cl.activity_period as current_period
                """, core_id=core_id)
                
                existing_record = existing_result.single()
                activity_period = candidate.get_activity_period(self.resolver.available_snapshots)
                
                if existing_record:
                    # Update existing CoreLine
                    current_period_json = existing_record["current_period"]
                    if current_period_json:
                        current_period = ActivityPeriod.from_json_string(current_period_json)
                        updated_period = self._merge_activity_periods(current_period.to_dict(), activity_period)
                    else:
                        updated_period = activity_period
                    
                    session.run("""
                    MATCH (cl:CoreLine {core_line_id: $core_id})
                    SET cl.activity_period = $activity_period,
                        cl.source_confidence = $confidence,
                        cl.updated_date = datetime()
                    """, 
                    core_id=core_id,
                    activity_period=updated_period.to_json_string(),
                    confidence=candidate.source_confidence
                    )
                    updated_count += 1
                else:
                    # Create new CoreLine
                    result = session.run("""
                    CREATE (cl:CoreLine {
                        core_line_id: $core_id,
                        name: $name,
                        type: $type,
                        east_west: $east_west,
                        activity_period: $activity_period,
                        source_confidence: $confidence,
                        created_date: datetime(),
                        source: 'core_entity_resolver'
                    })
                    RETURN cl.core_line_id as created_id
                    """, 
                    core_id=core_id,
                    name=candidate.name,
                    type=candidate.type,
                    east_west=candidate.east_west,
                    activity_period=activity_period.to_json_string(),
                    confidence=candidate.source_confidence
                    )
                    
                    if result.single():
                        created_count += 1
                
                # Link to snapshot lines
                for snapshot_id in candidate.snapshot_ids:
                    session.run("""
                    MATCH (cl:CoreLine {core_line_id: $core_id})
                    MATCH (l:Line {line_id: $snapshot_id})
                    MERGE (cl)-[:HAS_SNAPSHOT {
                        created_date: datetime(),
                        confidence: $confidence
                    }]->(l)
                    """, 
                    core_id=core_id,
                    snapshot_id=snapshot_id,
                    confidence=candidate.source_confidence
                    )
        
        logger.info(f"Created {created_count} new CoreLine nodes, updated {updated_count} existing ones")
        return created_count + updated_count
  
# Updated main function
def main():
    """Main function to run the core entities population"""
    parser = argparse.ArgumentParser(description="Populate CoreStation and CoreLine entities")
    
    # Database connection options
    parser.add_argument("--uri", default="neo4j+s://6ae11f66.databases.neo4j.io", help="Neo4j database URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default=os.environ.get("NEO4J_AURA_PASSWORD"), 
                       help="Neo4j password")
    
    # Operation options
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simulate operations without making changes")
    parser.add_argument("--stations-only", action="store_true",
                       help="Only process CoreStations")
    parser.add_argument("--lines-only", action="store_true",
                       help="Only process CoreLines") 
    parser.add_argument("--verify", action="store_true",
                       help="Verify existing core entities")
    parser.add_argument("--min-confidence", type=float, default=0.9,
                       help="Minimum confidence threshold for entity creation")
    parser.add_argument("--no-relationships", action="store_true",
                       help="Skip creating relationships between core entities")
    
    args = parser.parse_args()
    
    # Initialize database connection
    db = BerlinTransportDB(uri="neo4j+s://6ae11f66.databases.neo4j.io", username="neo4j", password=os.environ.get("NEO4J_AURA_PASSWORD"))
    
    try:
        logger.info("Starting Core Entities Population Process")
        
        if args.verify:
            logger.info("Verifying existing core entities...")
            # TODO: Implement verification logic
            return
        
        # Initialize resolver and populator
        resolver = CoreEntityResolver(db)
        populator = CoreEntityPopulator(db, resolver, dry_run=args.dry_run)
        
        # Analyze and create CoreStations
        if not args.lines_only:
            station_candidates = resolver.analyze_snapshot_stations()
            
            # Filter by confidence
            high_confidence_stations = {
                k: v for k, v in station_candidates.items() 
                if v.source_confidence >= args.min_confidence
            }
            
            logger.info(f"Processing {len(high_confidence_stations)} high-confidence stations "
                       f"(filtered from {len(station_candidates)} candidates)")
            
            stations_created = populator.populate_core_stations(high_confidence_stations)
        else:
            high_confidence_stations = {}
            stations_created = 0
        
        # Analyze and create CoreLines (with unified line resolution)
        if not args.stations_only:
            line_candidates = resolver.analyze_snapshot_lines(high_confidence_stations)
            
            # Filter by confidence
            high_confidence_lines = {
                k: v for k, v in line_candidates.items() 
                if v.source_confidence >= args.min_confidence
            }
            
            logger.info(f"Processing {len(high_confidence_lines)} high-confidence lines "
                       f"(filtered from {len(line_candidates)} candidates)")
            
            lines_created = populator.populate_core_lines(high_confidence_lines)
            
            # Create relationships between CoreStations and CoreLines
            if not args.no_relationships and high_confidence_stations:
                relationships_created = populator.create_core_entity_relationships(
                    high_confidence_stations, high_confidence_lines
                )
            else:
                relationships_created = 0
        else:
            lines_created = 0
            relationships_created = 0
        
        # Summary
        logger.info("Core Entities Population Complete")
        logger.info(f"CoreStations created: {stations_created}")
        logger.info(f"CoreLines created: {lines_created}")
        logger.info(f"Relationships created: {relationships_created}")
        
    except Exception as e:
        logger.error(f"Error during core entities population: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()