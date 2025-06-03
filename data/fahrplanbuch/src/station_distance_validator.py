# data/fahrplanbuch/src/station_distance_validator.py
"""
Utility module for validating distances between adjacent stations
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math
from db_connector import BerlinTransportDB

logger = logging.getLogger(__name__)

@dataclass
class DistanceIssue:
    """Represents a distance validation issue"""
    station_id: str
    station_name: str
    line_id: str
    line_name: str
    issue_type: str  # 'too_close' or 'too_far'
    actual_distance: float
    expected_min: float
    expected_max: float
    adjacent_station_id: str
    adjacent_station_name: str
    severity: str  # 'warning' or 'error'

class StationDistanceValidator:
    def __init__(self, db_connector: BerlinTransportDB):
        self.db = db_connector
        
        # Distance thresholds by transport type (in meters)
        self.distance_thresholds = {
            'u-bahn': {'min': 400, 'max': 2500},
            's-bahn': {'min': 800, 'max': 5000}, 
            'tram': {'min': 150, 'max': 1500},
            'autobus': {'min': 200, 'max': 2000},
            'omnibus': {'min': 200, 'max': 2000},
            'ferry': {'min': 500, 'max': 10000}
        }
    
    def validate_station_distances(self, year: int, transport_type: Optional[str] = None) -> List[DistanceIssue]:
        """
        Validate distances between adjacent stations for a given year
        
        Args:
            year: Year to validate
            transport_type: Optional filter by transport type
            
        Returns:
            List of distance issues found
        """
        logger.info(f"Validating station distances for year {year}")
        
        issues = []
        
        try:
            self.db.connect()
            
            with self.db.driver.session() as session:
                # Query to get adjacent stations with distances
                query = """
                MATCH (year:Year {year: $year})
                MATCH (s1:Station)-[:IN_YEAR]->(year)
                MATCH (s2:Station)-[:IN_YEAR]->(year)
                MATCH (l:Line)-[:IN_YEAR]->(year)
                MATCH (l)-[r1:SERVES]->(s1)
                MATCH (l)-[r2:SERVES]->(s2)
                WHERE r1.stop_order = r2.stop_order - 1
                """
                
                if transport_type:
                    query += " AND l.type = $transport_type"
                
                query += """
                WITH s1, s2, l, 
                     CASE 
                     WHEN s1.latitude IS NOT NULL AND s1.longitude IS NOT NULL 
                          AND s2.latitude IS NOT NULL AND s2.longitude IS NOT NULL
                     THEN point.distance(
                         point({latitude: s1.latitude, longitude: s1.longitude}),
                         point({latitude: s2.latitude, longitude: s2.longitude})
                     )
                     ELSE null
                     END AS distance
                WHERE distance IS NOT NULL
                RETURN s1.stop_id as station1_id, s1.name as station1_name,
                       s2.stop_id as station2_id, s2.name as station2_name,
                       l.line_id as line_id, l.name as line_name, l.type as transport_type,
                       distance
                """
                
                params = {'year': year}
                if transport_type:
                    params['transport_type'] = transport_type
                
                result = session.run(query, params)
                
                for record in result:
                    station1_id = record['station1_id']
                    station1_name = record['station1_name'] 
                    station2_id = record['station2_id']
                    station2_name = record['station2_name']
                    line_id = record['line_id']
                    line_name = record['line_name']
                    transport_type_actual = record['transport_type']
                    distance = record['distance']
                    
                    # Get thresholds for this transport type
                    thresholds = self.distance_thresholds.get(transport_type_actual, 
                                                            self.distance_thresholds['autobus'])
                    
                    # Check if distance is outside acceptable range
                    if distance < thresholds['min']:
                        severity = 'error' if distance < thresholds['min'] * 0.5 else 'warning'
                        issues.append(DistanceIssue(
                            station_id=station1_id,
                            station_name=station1_name,
                            line_id=line_id,
                            line_name=line_name,
                            issue_type='too_close',
                            actual_distance=distance,
                            expected_min=thresholds['min'],
                            expected_max=thresholds['max'],
                            adjacent_station_id=station2_id,
                            adjacent_station_name=station2_name,
                            severity=severity
                        ))
                    elif distance > thresholds['max']:
                        severity = 'error' if distance > thresholds['max'] * 2 else 'warning'
                        issues.append(DistanceIssue(
                            station_id=station1_id,
                            station_name=station1_name,
                            line_id=line_id,
                            line_name=line_name,
                            issue_type='too_far',
                            actual_distance=distance,
                            expected_min=thresholds['min'],
                            expected_max=thresholds['max'],
                            adjacent_station_id=station2_id,
                            adjacent_station_name=station2_name,
                            severity=severity
                        ))
                
        except Exception as e:
            logger.error(f"Error validating station distances: {e}")
            
        logger.info(f"Found {len(issues)} distance issues")
        return issues
    
    def get_station_distance_status(self, station_id: str, year: int) -> Dict:
        """
        Get distance validation status for a specific station
        
        Args:
            station_id: Station ID to check
            year: Year context
            
        Returns:
            Dictionary with validation status
        """
        try:
            self.db.connect()
            
            with self.db.driver.session() as session:
                # Get station and its adjacent connections
                query = """
                MATCH (year:Year {year: $year})
                MATCH (s:Station {stop_id: $station_id})-[:IN_YEAR]->(year)
                MATCH (l:Line)-[:IN_YEAR]->(year)
                MATCH (l)-[r1:SERVES]->(s)
                
                // Get previous station
                OPTIONAL MATCH (l)-[r_prev:SERVES]->(s_prev:Station)-[:IN_YEAR]->(year)
                WHERE r_prev.stop_order = r1.stop_order - 1
                
                // Get next station  
                OPTIONAL MATCH (l)-[r_next:SERVES]->(s_next:Station)-[:IN_YEAR]->(year)
                WHERE r_next.stop_order = r1.stop_order + 1
                
                WITH s, l, s_prev, s_next,
                     CASE 
                     WHEN s_prev IS NOT NULL AND s.latitude IS NOT NULL AND s.longitude IS NOT NULL 
                          AND s_prev.latitude IS NOT NULL AND s_prev.longitude IS NOT NULL
                     THEN point.distance(
                         point({latitude: s.latitude, longitude: s.longitude}),
                         point({latitude: s_prev.latitude, longitude: s_prev.longitude})
                     )
                     ELSE null
                     END AS prev_distance,
                     CASE 
                     WHEN s_next IS NOT NULL AND s.latitude IS NOT NULL AND s.longitude IS NOT NULL 
                          AND s_next.latitude IS NOT NULL AND s_next.longitude IS NOT NULL
                     THEN point.distance(
                         point({latitude: s.latitude, longitude: s.longitude}),
                         point({latitude: s_next.latitude, longitude: s_next.longitude})
                     )
                     ELSE null
                     END AS next_distance
                     
                RETURN l.type as transport_type, l.name as line_name,
                       s_prev.stop_id as prev_station_id, s_prev.name as prev_station_name,
                       s_next.stop_id as next_station_id, s_next.name as next_station_name,
                       prev_distance, next_distance
                """
                
                result = session.run(query, {'station_id': station_id, 'year': year})
                
                validation_results = []
                
                for record in result:
                    transport_type = record['transport_type']
                    line_name = record['line_name']
                    thresholds = self.distance_thresholds.get(transport_type, 
                                                            self.distance_thresholds['autobus'])
                    
                    line_result = {
                        'line_name': line_name,
                        'transport_type': transport_type,
                        'thresholds': thresholds,
                        'previous_station': None,
                        'next_station': None
                    }
                    
                    # Check previous station distance
                    if record['prev_distance'] is not None:
                        prev_distance = record['prev_distance']
                        status = 'ok'
                        if prev_distance < thresholds['min']:
                            status = 'too_close'
                        elif prev_distance > thresholds['max']:
                            status = 'too_far'
                            
                        line_result['previous_station'] = {
                            'station_id': record['prev_station_id'],
                            'station_name': record['prev_station_name'],
                            'distance': prev_distance,
                            'status': status
                        }
                    
                    # Check next station distance
                    if record['next_distance'] is not None:
                        next_distance = record['next_distance']
                        status = 'ok'
                        if next_distance < thresholds['min']:
                            status = 'too_close'
                        elif next_distance > thresholds['max']:
                            status = 'too_far'
                            
                        line_result['next_station'] = {
                            'station_id': record['next_station_id'],
                            'station_name': record['next_station_name'],
                            'distance': next_distance,
                            'status': status
                        }
                    
                    validation_results.append(line_result)
                
                return {
                    'station_id': station_id,
                    'year': year,
                    'lines': validation_results
                }
                
        except Exception as e:
            logger.error(f"Error getting station distance status: {e}")
            return {'error': str(e)}
        finally:
            self.db.close()