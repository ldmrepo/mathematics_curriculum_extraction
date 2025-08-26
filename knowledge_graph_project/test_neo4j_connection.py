#!/usr/bin/env python3
"""
Test Neo4j connection
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test Neo4j connection"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j123")
    
    print(f"Testing connection to Neo4j...")
    print(f"URI: {uri}")
    print(f"User: {user}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test query
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Neo4j connection successful!")
                
                # Get database info
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                for record in result:
                    print(f"  - {record['name']}: {record['versions'][0]} ({record['edition']})")
                
                # Count nodes
                result = session.run("MATCH (n) RETURN count(n) AS node_count")
                node_count = result.single()["node_count"]
                print(f"  - Current nodes in database: {node_count}")
                
                return True
            else:
                print("❌ Neo4j test query failed")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_connection()