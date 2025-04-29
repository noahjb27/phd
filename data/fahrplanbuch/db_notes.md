# Guide: Using the Improved populate_db.py Script

The updated `populate_db.py` script provides more control over how you upload data to your Neo4j database. This guide shows you how to run the script for different scenarios.

## Setup

First, make sure your environment is set up:

1. Copy the updated script into your `src` directory
2. Make sure your Neo4j database is running
3. Set your Neo4j password as an environment variable (or use the `--password` option):

```bash
export NEO4J_PASSWORD="YourPassword"
```

## Basic Usage Examples

### List Available Data

To see what data is available for import:

```bash
python src/populate_db.py --list
```

This will show all years and sides (east/west) available in your data directory.

### Initial Data Import

For your first data import of all available data:

```bash
python src/populate_db.py
```

This will import all available data, skipping any data that already exists in the database.

### Dry Run (Preview Import)

To preview what would be imported without making changes:

```bash
python src/populate_db.py --dry-run
```

### Import Specific Years or Sides

Import data for specific years:

```bash
python src/populate_db.py --years 1960 1970 1980
```

Import data for one side of Berlin only:

```bash
python src/populate_db.py --sides east
```

Or combine both filters:

```bash
python src/populate_db.py --years 1970 1980 --sides west
```

### Updating Existing Data

To overwrite existing data (for example, if you have corrected some data):

```bash
python src/populate_db.py --update-existing
```

Or update specific years:

```bash
python src/populate_db.py --years 1970 --update-existing
```

### Verify Data

To check the state of your database without importing:

```bash
python src/populate_db.py --verify
```

### Create Missing Connections

If you need to rebuild connections between stations:

```bash
python src/populate_db.py --connections
```

## Advanced Options

### Different Database Connection

Connect to a different Neo4j instance:

```bash
python src/populate_db.py --uri bolt://alternate-server:7687 --username neo4j
```

### Different Data Directory

Use data from an alternate directory:

```bash
python src/populate_db.py --data-dir /path/to/other/data/processed
```

## Workflow Examples

### Workflow 1: Initial Setup

```bash
# Reset database (careful!)
python src/db_reset.py --confirm

# Import all data
python src/populate_db.py

# Check schema
python src/db_schema.py
```

### Workflow 2: Adding New Data

```bash
# List what's available for import
python src/populate_db.py --list

# Preview the import
python src/populate_db.py --years 1985 --dry-run

# Import only new data
python src/populate_db.py --years 1985
```

### Workflow 3: Correcting Data

```bash
# Update specific years with corrected data
python src/populate_db.py --years 1970 --update-existing

# Verify the data looks correct
python src/populate_db.py --verify
```

## Troubleshooting

If you encounter issues:

1. Check the logs for error messages
2. Verify your database connection settings
3. Make sure your CSV files have the expected format
4. Try running with `--dry-run` to see what would happen
5. Check that files exist in the expected locations

## Understanding Data Processing

The script processes the following files for each year and side:

- `stops.csv`: Station information
- `lines.csv`: Transportation line information
- `line_stops.csv`: Connections between lines and stations

Each file is processed in batches to improve performance and reduce memory usage.