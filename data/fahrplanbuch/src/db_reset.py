# db_reset.py

import logging
from pathlib import Path
import sys
from neo4j import GraphDatabase
import os
import argparse

# Add the src directory to the Python path
sys.path.append(str(Path('./src').resolve()))
from db_connector import BerlinTransportDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def reset_database(uri, username, password, confirm=False):
    """
    Reset the Neo4j database by removing all nodes and relationships.
    
    Args:
        uri: Database URI
        username: Database username
        password: Database password
        confirm: Whether the user has confirmed the reset
    
    Returns:
        True if successful, False otherwise
    """
    if not confirm:
        logger.error("Database reset not confirmed. Add --confirm flag to proceed.")
        return False
    
    logger.warning("Resetting database - this will delete ALL data!")
    
    try:
        # Connect to database
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # First, remove all constraints and indexes
            logger.info("Removing constraints and indexes...")
            
            # Get all constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = [record["name"] for record in result if "name" in record]
            
            # Drop each constraint
            for constraint in constraints:
                logger.info(f"Dropping constraint: {constraint}")
                session.run(f"DROP CONSTRAINT {constraint}")
            
            # Get all indexes
            result = session.run("SHOW INDEXES")
            indexes = [record["name"] for record in result if "name" in record]
            
            # Drop each index (excluding those automatically created by constraints)
            for index in indexes:
                if index not in constraints:  # Skip constraint-created indexes
                    logger.info(f"Dropping index: {index}")
                    session.run(f"DROP INDEX {index}")
            
            # Now delete all data
            logger.info("Deleting all nodes and relationships...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Verify deletion
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            
            if node_count == 0:
                logger.info("Database reset successful. All data has been removed.")
                return True
            else:
                logger.error(f"Database still contains {node_count} nodes after reset.")
                return False
            
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False
    finally:
        driver.close()

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Reset Neo4j database")
    parser.add_argument("--uri", default="bolt://100.82.176.18:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024"), 
                       help="Neo4j password (can also be set via NEO4J_PASSWORD environment variable)")
    parser.add_argument("--confirm", action="store_true", 
                       help="Confirm database reset (REQUIRED to proceed)")
    
    args = parser.parse_args()
    
    # Execute reset
    success = reset_database(args.uri, args.username, args.password, args.confirm)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()