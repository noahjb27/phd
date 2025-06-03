# data/fahrplanbuch/src/migrate_add_source_field.py
"""
Migration script to add 'source' field to Station nodes
"""

import logging
from pathlib import Path
import sys
import os
from db_connector import BerlinTransportDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_DB_URI = "bolt://100.82.176.18:7687"
DEFAULT_DB_USER = "neo4j" 
DEFAULT_DB_PASSWORD = os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024")

class SourceFieldMigration:
    def __init__(self, uri=DEFAULT_DB_URI, username=DEFAULT_DB_USER, password=DEFAULT_DB_PASSWORD):
        self.db = BerlinTransportDB(uri=uri, username=username, password=password)
        
    def add_source_field(self, default_source="Fahrplanbuch"):
        """
        Add source field to all existing Station nodes
        
        Args:
            default_source: Default value for existing stations
        """
        logger.info("Adding source field to Station nodes...")
        
        try:
            self.db.connect()
            
            with self.db.driver.session() as session:
                # First, check how many stations don't have a source field
                result = session.run("""
                MATCH (s:Station)
                WHERE s.source IS NULL
                RETURN count(s) as count
                """)
                
                count_without_source = result.single()["count"]
                logger.info(f"Found {count_without_source} stations without source field")
                
                if count_without_source == 0:
                    logger.info("All stations already have source field")
                    return True
                
                # Add source field with default value
                result = session.run("""
                MATCH (s:Station)
                WHERE s.source IS NULL
                SET s.source = $default_source
                RETURN count(s) as updated
                """, default_source=default_source)
                
                updated_count = result.single()["updated"]
                logger.info(f"Updated {updated_count} stations with source field")
                
                # Verify the update
                result = session.run("""
                MATCH (s:Station)
                RETURN s.source as source, count(*) as count
                """)
                
                logger.info("Source field distribution:")
                for record in result:
                    source = record["source"] or "NULL"
                    count = record["count"]
                    logger.info(f"  {source}: {count}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding source field: {e}")
            return False
        finally:
            self.db.close()
    
    def create_source_constraint(self):
        """Create index on source field for better performance"""
        logger.info("Creating index on source field...")
        
        try:
            self.db.connect()
            
            with self.db.driver.session() as session:
                # Create index on source field
                session.run("CREATE INDEX IF NOT EXISTS FOR (s:Station) ON (s.source)")
                logger.info("Created index on Station.source field")
                
                return True
                
        except Exception as e:
            logger.error(f"Error creating source index: {e}")
            return False
        finally:
            self.db.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Add source field to Station nodes")
    parser.add_argument("--uri", default=DEFAULT_DB_URI, help="Neo4j database URI")
    parser.add_argument("--username", default=DEFAULT_DB_USER, help="Neo4j username")
    parser.add_argument("--password", default=DEFAULT_DB_PASSWORD, help="Neo4j password")
    parser.add_argument("--default-source", default="Fahrplanbuch", 
                       help="Default source value for existing stations")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    migration = SourceFieldMigration(args.uri, args.username, args.password)
    
    if args.dry_run:
        logger.info("[DRY RUN] Would add source field to Station nodes")
        logger.info(f"[DRY RUN] Default source: {args.default_source}")
        return 0
    
    # Run migration
    success = migration.add_source_field(args.default_source)
    if success:
        success = migration.create_source_constraint()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())