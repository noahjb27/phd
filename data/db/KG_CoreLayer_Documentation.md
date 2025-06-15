# Berlin Transport Knowledge Graph: Extended Schema Documentation

## Overview

This document describes the extended schema for the Berlin Transport Knowledge Graph, which now includes a **Core Identity Layer** above the existing **Temporal Snapshot Layer**. This bi-temporal approach allows for both point-in-time analysis and cross-temporal entity tracking with sophisticated activity period modeling.

## Future Notes

- I could use the serves_core relationship to group stations further as an extra feature that should boost the confidence that the stations are indeed the same.

## Schema Architecture

### 1. Core Identity Layer (NEW)

#### CoreStation Nodes

**Purpose**: Represent persistent transportation stations across multiple snapshots with detailed activity tracking

**Properties**:

- `core_id` (String, UNIQUE): Unique identifier for the core station
- `name` (String): Canonical station name
- `type` (String): Primary transport type (u-bahn, s-bahn, tram, autobus, omnibus, ferry)
- `latitude` (Float): Representative latitude coordinate (averaged from snapshots)
- `longitude` (Float): Representative longitude coordinate (averaged from snapshots)
- `east_west` (String): Geographic/political designation (east/west/unified)
- `activity_period` (JSON String): Detailed activity tracking structure:

 ```json
  {
    "start_snapshot": 1960,
    "end_snapshot": 1989,
    "observed_snapshots": [1960, 1965, 1970, 1980, 1989],
    "missing_snapshots": [1975, 1985],
    "missing_reasons": {
      "1975": "closure",
      "1985": "data_gap"
    },
    "total_period_years": 29,
    "observation_rate": 0.71
  }
  ```

- `in_lines` (List[String]): CoreLine IDs that serve this station
- `source_confidence` (Float): Confidence in entity resolution (0.0-1.0)
- `created_date` (DateTime): When the core entity was created
- `updated_date` (DateTime): Last update timestamp
- `source` (String): How this entity was determined ('core_entity_resolver')

**Indexes**:

- `core_id` (unique constraint)
- `(name, type, east_west)` (composite index)

#### CoreLine Nodes

**Purpose**: Represent persistent transportation lines across multiple snapshots with unified line resolution

**Properties**:

- `core_line_id` (String, UNIQUE): Unique identifier for the core line
- `name` (String): Canonical line name
- `type` (String): Transport type
- `east_west` (String): Geographic/political designation (resolved from 'unified' to 'east'/'west')
- `activity_period` (JSON String): Detailed activity tracking (same structure as CoreStation)
- `source_confidence` (Float): Confidence in entity resolution
- `created_date` (DateTime): Creation timestamp
- `updated_date` (DateTime): Last update timestamp
- `source` (String): Entity resolution method ('core_entity_resolver')

**Indexes**:

- `core_line_id` (unique constraint)
- `(name, type, east_west)` (composite index)

### 2. Temporal Snapshot Layer (EXISTING)

This layer remains unchanged from the current implementation:

#### Station Nodes

- Properties: `stop_id`, `name`, `type`, `east_west`, `latitude`, `longitude`, `source`
- Represents stations as they existed in specific years

#### Line Nodes  

- Properties: `line_id`, `name`, `type`, `east_west`, `frequency`, `capacity`, `length_time`
- Represents lines as they operated in specific years

#### Year Nodes

- Properties: `year`
- Temporal anchors for snapshot data

### 3. Administrative Layer (EXISTING)

- District, Ortsteil, PostalCode nodes (unchanged)

## Relationships

### Core Identity Relationships (NEW)

#### CoreStation Relationships

```cypher
// Links core entities to their yearly snapshots
(CoreStation)-[:HAS_SNAPSHOT {created_date, confidence}]->(Station)

// Service relationships between core entities with connection strength
(CoreLine)-[:SERVES_CORE {
  created_date, 
  overlapping_snapshots: [1960, 1965, 1970],
  connection_strength: 0.75
}]->(CoreStation)
```

#### CoreLine Relationships

```cypher
// Links core lines to their yearly snapshots
(CoreLine)-[:HAS_SNAPSHOT {created_date, confidence}]->(Line)
```

### Temporal Snapshot Relationships (EXISTING)

All existing relationships remain unchanged:

- `(Station)-[:IN_YEAR]->(Year)`
- `(Line)-[:IN_YEAR]->(Year)`
- `(Line)-[:SERVES {stop_order}]->(Station)`
- `(Station)-[:CONNECTS_TO {properties}]->(Station)`
- Administrative relationships (IN_DISTRICT, IN_ORTSTEIL, IN_POSTAL_CODE)

## Enhanced Entity Resolution Logic

### Connection-Aware Station Resolution

Stations are grouped into CoreStations using sophisticated logic to avoid incorrectly merging consecutive stations on the same line:

1. **Initial Grouping**: Stations grouped by (name, type, east_west)
2. **Connection Analysis**: Uses existing CONNECTS_TO relationships to identify when stations should remain separate
3. **Component Separation**: DFS algorithm finds connected components within each group
4. **Geographic Validation**: Manhattan distance calculation (appropriate for urban street grids)

**Distance Thresholds**:

- High confidence (0.95): ≤200m maximum distance
- Medium confidence (0.8): ≤250m maximum distance  
- Low confidence (0.6): ≤300m maximum distance
- Very low confidence (0.3): >300m maximum distance

### Unified Line Resolution

Sophisticated algorithm to resolve "unified" lines with their east/west counterparts:

1. **Geographic Analysis**: Uses Berlin dividing longitude (~13.4°) to determine line orientation
2. **Station Location Mapping**: Analyzes coordinates of all stations served by unified lines
3. **Counterpart Merging**: Merges unified lines with existing east/west lines when appropriate
4. **Fallback Creation**: Creates new east/west lines when no counterparts exist

```python
# Berlin dividing logic
BERLIN_DIVIDING_LONGITUDE = 13.4
side = "east" if avg_longitude > BERLIN_DIVIDING_LONGITUDE else "west"
```

### Activity Period Calculation

Enhanced temporal tracking that goes beyond simple start/end dates:

**Observation Tracking**:

- `observed_snapshots`: Years where entity actually appears in data
- `missing_snapshots`: Years within the period where entity is absent
- `missing_reasons`: Categorized reasons for absence (closure, data_gap, reconstruction)
- `observation_rate`: Percentage of expected snapshots where entity is observed

**Missing Reason Categories**:

- `"data_gap"`: No data available for that snapshot
- `"closure"`: Known temporary closure (e.g., reconstruction)
- `"disruption"`: Service disrupted (e.g., Berlin Wall effects)
- `"reconstruction"`: Station/line being rebuilt

## Implementation Strategy

### Phase 1: Core Entity Creation ✓

```bash
# Preview core entities (higher default confidence threshold)
python src/populate_core_entities.py --dry-run --min-confidence 0.9

# Create CoreStations and CoreLines with unified line resolution
python src/populate_core_entities.py --min-confidence 0.9

# Create only stations (useful for iterative approach)
python src/populate_core_entities.py --stations-only --min-confidence 0.85

# Skip relationship creation if needed
python src/populate_core_entities.py --no-relationships
```

### Phase 2: Iterative Updates ✓

The system now supports updating existing core entities when new snapshot data is added:

```bash
# Add new snapshot data
python src/populate_db.py --years 1990

# Update existing core entities with new snapshots
python src/populate_core_entities.py --min-confidence 0.9
# This will merge new activity periods with existing ones
```

### Phase 3: Analysis and Validation ✓

```bash
# Analyze created entities
python src/analyze_core_entities.py

# Test and validate the implementation
python src/test_core_queries.py
```

## Example Queries

### Find Persistent Stations

```cypher
// Stations active across the entire period (1945-1989)
MATCH (cs:CoreStation)
WHERE cs.activity_period IS NOT NULL
WITH cs, apoc.convert.fromJsonMap(cs.activity_period) as period
WHERE period.start_snapshot <= 1945 AND period.end_snapshot >= 1989
RETURN cs.name, cs.type, period.observation_rate, period.observed_snapshots
ORDER BY period.observation_rate DESC
```

### Track Station Evolution

```cypher
// See how a station changed over time with activity details
MATCH (cs:CoreStation {name: "Alexanderplatz"})-[:HAS_SNAPSHOT]->(s:Station)
MATCH (s)-[:IN_YEAR]->(y:Year)
WITH cs, collect({year: y.year, lat: s.latitude, lng: s.longitude}) as evolution,
     apoc.convert.fromJsonMap(cs.activity_period) as period
RETURN cs.name, cs.type, evolution, period.missing_snapshots, period.missing_reasons
ORDER BY cs.name
```

### Find Lines That Served a Core Station

```cypher
// What lines served Potsdamer Platz over time with connection strength?
MATCH (cs:CoreStation {name: "Potsdamer Platz"})
MATCH (cl:CoreLine)-[r:SERVES_CORE]->(cs)
RETURN cl.name, cl.type, r.connection_strength, r.overlapping_snapshots
ORDER BY r.connection_strength DESC
```

### Analyze Network Disruption

```cypher
// Find stations with closures or disruptions in their activity period
MATCH (cs:CoreStation)
WHERE cs.activity_period IS NOT NULL
WITH cs, apoc.convert.fromJsonMap(cs.activity_period) as period
WHERE size(period.missing_snapshots) > 0
UNWIND keys(period.missing_reasons) as missing_year
WITH cs, period, toInteger(missing_year) as year, period.missing_reasons[missing_year] as reason
WHERE reason IN ["closure", "disruption"]
RETURN cs.name, cs.east_west, year, reason, period.observation_rate
ORDER BY year, cs.name
```

### Find Stations with Poor Data Coverage

```cypher
// Stations with low observation rates (potential data quality issues)
MATCH (cs:CoreStation)
WHERE cs.activity_period IS NOT NULL
WITH cs, apoc.convert.fromJsonMap(cs.activity_period) as period
WHERE period.observation_rate < 0.5
RETURN cs.name, cs.type, cs.east_west, period.observation_rate, 
       period.observed_snapshots, period.missing_snapshots
ORDER BY period.observation_rate ASC
```

### Unified Line Resolution Analysis

```cypher
// Find lines that were resolved from 'unified' to east/west
MATCH (cl:CoreLine)-[:HAS_SNAPSHOT]->(l:Line)
WHERE l.east_west = "unified" AND cl.east_west IN ["east", "west"]
RETURN cl.name, cl.type, cl.east_west as resolved_side, 
       collect(DISTINCT l.east_west) as original_designations
ORDER BY cl.name
```

## Data Quality Considerations

### Confidence Tracking

Every core entity and relationship includes confidence scores to track:

- Entity resolution reliability
- Data source quality
- Temporal inference accuracy

### Validation Rules

1. **Temporal Consistency**: Activity periods must align with snapshot availability
2. **Geographic Validation**: Core coordinates should be within reasonable bounds
3. **Relationship Integrity**: SERVES_CORE relationships require overlapping activity periods
4. **Source Tracking**: All entities must track their derivation method

### Error Handling

- Low confidence entities (< 0.5) flagged for manual review
- Geographic outliers identified and reviewed
- Temporal gaps documented and explained

## Migration Path

### From Current Schema

1. **Backward Compatibility**: All existing queries continue to work
2. **Gradual Enhancement**: Core layer added without disrupting snapshots
3. **Incremental Processing**: Can be run repeatedly as new data is added

### Future Extensions

- **CoreDistrict**: Administrative persistence tracking
- **CoreRoute**: Route-level analysis across time
- **EventNodes**: Historical events that affected the network
- **AlternativeHistory**: What-if scenario modeling

## Performance Considerations

### Indexing Strategy

```cypher
// Core entity indexes
CREATE CONSTRAINT core_station_id FOR (cs:CoreStation) REQUIRE cs.core_id IS UNIQUE;
CREATE CONSTRAINT core_line_id FOR (cl:CoreLine) REQUIRE cl.core_line_id IS UNIQUE;
CREATE INDEX core_station_name FOR (cs:CoreStation) ON (cs.name, cs.type);
CREATE INDEX core_line_name FOR (cl:CoreLine) ON (cl.name, cs.type);
```

### Query Optimization

- Use core entities for cross-temporal queries
- Use snapshot entities for point-in-time analysis
- Composite indexes on frequently queried property combinations

This extended schema provides a foundation for sophisticated temporal analysis while maintaining the detailed snapshot-level data that drives the interactive visualizations.
