# db_schema.py
import sys
from pathlib import Path
import json
from neo4j import GraphDatabase
import os
import argparse
from tabulate import tabulate
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DBSchemaInspector:
    def __init__(self, uri="bolt://localhost:7687", username="neo4j", password=None):
        """
        Initialize connection to Neo4j database
        
        Args:
            uri: Database URI
            username: Database username
            password: Database password (defaults to env variable NEO4J_PASSWORD)
        """
        self.uri = uri
        self.username = username
        self.password = password or os.environ.get("NEO4J_PASSWORD", "BerlinTransport2024")
        self.driver = None

    def connect(self):
        """Connect to the database"""
        self.driver = GraphDatabase.driver(
            self.uri, 
            auth=(self.username, self.password)
        )
        # Test the connection
        with self.driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            if test_value != 1:
                raise Exception("Failed to connect to database")
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
    
    def inspect_schema(self):
        """
        Inspect Neo4j database schema and return information about labels,
        relationship types, constraints, indexes, and properties.
        
        Returns:
            Dictionary containing schema information
        """
        logger.info("Inspecting database schema...")
        
        schema_info = {
            "node_labels": [],
            "relationship_types": [],
            "constraints": [],
            "indexes": [],
            "property_keys": {},
            "sample_counts": {}
        }
        
        try:
            self.connect()
            
            with self.driver.session() as session:
                # Get node labels
                logger.info("Retrieving node labels...")
                result = session.run("CALL db.labels()")
                schema_info["node_labels"] = [record["label"] for record in result]
                
                # Get relationship types
                logger.info("Retrieving relationship types...")
                result = session.run("CALL db.relationshipTypes()")
                schema_info["relationship_types"] = [record["relationshipType"] for record in result]
                
                # Get constraints
                logger.info("Retrieving constraints...")
                try:
                    result = session.run("SHOW CONSTRAINTS")
                    for record in result:
                        constraint = {
                            "name": record.get("name", "unnamed"),
                            "type": record.get("type", "unknown"),
                            "entity_type": record.get("entityType", ""),
                            "properties": record.get("properties", []),
                            "label_or_type": record.get("labelsOrTypes", [])
                        }
                        schema_info["constraints"].append(constraint)
                except Exception as e:
                    logger.warning(f"Error retrieving constraints (may be due to Neo4j version): {e}")
                    schema_info["constraints"] = [{"error": "Could not retrieve constraints"}]
                
                # Get indexes
                logger.info("Retrieving indexes...")
                try:
                    result = session.run("SHOW INDEXES")
                    for record in result:
                        index = {
                            "name": record.get("name", "unnamed"),
                            "type": record.get("type", "unknown"),
                            "entity_type": record.get("entityType", ""),
                            "properties": record.get("properties", []),
                            "label_or_type": record.get("labelsOrTypes", [])
                        }
                        schema_info["indexes"].append(index)
                except Exception as e:
                    logger.warning(f"Error retrieving indexes (may be due to Neo4j version): {e}")
                    schema_info["indexes"] = [{"error": "Could not retrieve indexes"}]
                
                # Get property keys for each node label
                logger.info("Retrieving property keys for each node label...")
                for label in schema_info["node_labels"]:
                    try:
                        result = session.run(
                            f"MATCH (n:{label}) WITH n LIMIT 1 RETURN keys(n) as props"
                        )
                        record = result.single()
                        if record:
                            schema_info["property_keys"][label] = record["props"]
                        else:
                            schema_info["property_keys"][label] = []
                    except Exception as e:
                        logger.warning(f"Error retrieving properties for node label {label}: {e}")
                
                # Get property keys for each relationship type
                logger.info("Retrieving property keys for each relationship type...")
                for rel_type in schema_info["relationship_types"]:
                    try:
                        # Escape relationship type if it contains special characters
                        escaped_rel_type = rel_type.replace("`", "``")
                        query = f"MATCH ()-[r:`{escaped_rel_type}`]->() WITH r LIMIT 1 RETURN keys(r) as props"
                        result = session.run(query)
                        record = result.single()
                        if record:
                            schema_info["property_keys"][rel_type] = record["props"]
                        else:
                            schema_info["property_keys"][rel_type] = []
                    except Exception as e:
                        logger.warning(f"Error retrieving properties for relationship type {rel_type}: {e}")
                
                # Get counts for each node label and relationship type
                logger.info("Retrieving counts...")
                for label in schema_info["node_labels"]:
                    try:
                        result = session.run(f"MATCH (:{label}) RETURN count(*) as count")
                        schema_info["sample_counts"][label] = result.single()["count"]
                    except Exception as e:
                        logger.warning(f"Error counting nodes with label {label}: {e}")
                
                for rel_type in schema_info["relationship_types"]:
                    try:
                        # Escape relationship type if it contains special characters
                        escaped_rel_type = rel_type.replace("`", "``")
                        query = f"MATCH ()-[:`{escaped_rel_type}`]->() RETURN count(*) as count"
                        result = session.run(query)
                        schema_info["sample_counts"][rel_type] = result.single()["count"]
                    except Exception as e:
                        logger.warning(f"Error counting relationships of type {rel_type}: {e}")
                
                # Get sample nodes and relationships
                logger.info("Retrieving sample data...")
                schema_info["sample_data"] = {}
                
                # Get sample nodes for each label
                for label in schema_info["node_labels"][:5]:  # Limit to 5 labels to avoid excessive output
                    try:
                        result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 3")
                        schema_info["sample_data"][f"nodes_{label}"] = [dict(record["n"]) for record in result]
                    except Exception as e:
                        logger.warning(f"Error retrieving sample nodes with label {label}: {e}")
                
                # Get sample relationships for each type
                for rel_type in schema_info["relationship_types"][:5]:  # Limit to 5 types
                    try:
                        # Escape relationship type if it contains special characters
                        escaped_rel_type = rel_type.replace("`", "``")
                        query = f"MATCH (a)-[r:`{escaped_rel_type}`]->(b) RETURN a.name AS from, b.name AS to, properties(r) AS props LIMIT 3"
                        result = session.run(query)
                        schema_info["sample_data"][f"rels_{rel_type}"] = [dict(record) for record in result]
                    except Exception as e:
                        logger.warning(f"Error retrieving sample relationships of type {rel_type}: {e}")
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error inspecting schema: {e}")
            return {"error": str(e)}
        finally:
            self.close()
    
    def print_schema_summary(self, schema_info):
        """Print a human-readable summary of the schema."""
        print("\n" + "="*80)
        print("DATABASE SCHEMA SUMMARY")
        print("="*80)
        
        # Print node label counts
        print("\nNODE LABELS:")
        node_data = [
            [label, schema_info["sample_counts"].get(label, 0), 
             ", ".join(schema_info["property_keys"].get(label, [])[:5]) + 
             ("..." if len(schema_info["property_keys"].get(label, [])) > 5 else "")]
            for label in schema_info["node_labels"]
        ]
        print(tabulate(node_data, headers=["Label", "Count", "Sample Properties"], tablefmt="grid"))
        
        # Print relationship type counts
        print("\nRELATIONSHIP TYPES:")
        rel_data = [
            [rel_type, schema_info["sample_counts"].get(rel_type, 0),
             ", ".join(schema_info["property_keys"].get(rel_type, [])[:5]) + 
             ("..." if len(schema_info["property_keys"].get(rel_type, [])) > 5 else "")]
            for rel_type in schema_info["relationship_types"]
        ]
        print(tabulate(rel_data, headers=["Type", "Count", "Sample Properties"], tablefmt="grid"))
        
        # Print constraints if available
        if schema_info["constraints"] and "error" not in schema_info["constraints"][0]:
            print("\nCONSTRAINTS:")
            constraint_data = [
                [c["name"], 
                 ", ".join(c["label_or_type"]) if isinstance(c["label_or_type"], list) else c["label_or_type"], 
                 ", ".join(c["properties"]) if isinstance(c["properties"], list) else c["properties"], 
                 c["type"]]
                for c in schema_info["constraints"]
            ]
            print(tabulate(constraint_data, 
                          headers=["Name", "Label/Type", "Properties", "Type"], 
                          tablefmt="grid"))
        
        # Print indexes if available
        if schema_info["indexes"] and "error" not in schema_info["indexes"][0]:
            print("\nINDEXES:")
            index_data = [
                [i["name"], 
                 ", ".join(i["label_or_type"]) if isinstance(i["label_or_type"], list) else i["label_or_type"], 
                 ", ".join(i["properties"]) if isinstance(i["properties"], list) else i["properties"], 
                 i["type"]]
                for i in schema_info["indexes"]
            ]
            print(tabulate(index_data, 
                          headers=["Name", "Label/Type", "Properties", "Type"], 
                          tablefmt="grid"))
        
        # Print sample node data
        print("\nSAMPLE NODE DATA:")
        for label, samples in schema_info.get("sample_data", {}).items():
            if label.startswith("nodes_") and samples:
                node_label = label[6:]  # Remove "nodes_" prefix
                print(f"\n{node_label} (sample):")
                sample = samples[0]
                sample_data = []
                for key, value in sample.items():
                    if isinstance(value, (list, dict)):
                        value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    sample_data.append([key, value])
                print(tabulate(sample_data, headers=["Property", "Value"], tablefmt="simple"))
        
        print("\n" + "="*80)
    
    def query_station_structure(self):
        """Run a specific query to understand the Station node structure"""
        logger.info("Querying Station structure...")
        
        try:
            self.connect()
            
            with self.driver.session() as session:
                # Get sample Station nodes
                result = session.run("""
                MATCH (s:Station)
                RETURN s.stop_id as stop_id, s.name as name, s.type as type, 
                       s.latitude as latitude, s.longitude as longitude, 
                       s.east_west as east_west
                LIMIT 5
                """)
                
                stations = [dict(record) for record in result]
                
                # Get Station-Year relationships
                result = session.run("""
                MATCH (s:Station)-[:IN_YEAR]->(y:Year)
                RETURN s.stop_id as stop_id, y.year as year
                LIMIT 10
                """)
                
                station_years = [dict(record) for record in result]
                
                # Get Station-Line relationships
                result = session.run("""
                MATCH (l:Line)-[r:SERVES]->(s:Station)
                RETURN l.line_id as line_id, l.name as line_name, 
                       s.stop_id as stop_id, s.name as station_name,
                       r.stop_order as stop_order
                LIMIT 10
                """)
                
                station_lines = [dict(record) for record in result]
                
                return {
                    "sample_stations": stations,
                    "station_years": station_years,
                    "station_lines": station_lines
                }
                
        except Exception as e:
            logger.error(f"Error querying Station structure: {e}")
            return {"error": str(e)}
        finally:
            self.close()

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Inspect Neo4j database schema")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default=None, 
                       help="Neo4j password (can also be set via NEO4J_PASSWORD environment variable)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--station-details", action="store_true", help="Get detailed Station node information")
    
    args = parser.parse_args()
    
    # Initialize inspector
    inspector = DBSchemaInspector(args.uri, args.username, args.password)
    
    # Inspect schema
    schema_info = inspector.inspect_schema()
    
    if "error" in schema_info:
        logger.error(f"Error: {schema_info['error']}")
        sys.exit(1)
    
    # Print human-readable summary
    inspector.print_schema_summary(schema_info)
    
    # Get Station details if requested
    if args.station_details:
        print("\n" + "="*80)
        print("STATION NODE DETAILS")
        print("="*80)
        
        station_info = inspector.query_station_structure()
        
        if "error" in station_info:
            logger.error(f"Error: {station_info['error']}")
        else:
            print("\nSample Stations:")
            print(tabulate(station_info["sample_stations"], headers="keys", tablefmt="grid"))
            
            print("\nStation-Year Relationships:")
            print(tabulate(station_info["station_years"], headers="keys", tablefmt="grid"))
            
            print("\nStation-Line Relationships:")
            print(tabulate(station_info["station_lines"], headers="keys", tablefmt="grid"))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(schema_info, f, indent=2)
        logger.info(f"Schema information saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())