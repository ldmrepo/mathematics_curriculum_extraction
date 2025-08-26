#!/usr/bin/env python3
"""
Export all phase results to Neo4j graph database
"""
import json
import sys
from pathlib import Path
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

from src.neo4j_manager import Neo4jManager
from src.data_manager import DatabaseManager
from loguru import logger

def load_all_results():
    """Load all phase results"""
    logger.info("Loading all phase results...")
    
    all_results = {}
    
    # Load Phase 1 results
    try:
        with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
            all_results['foundation_design'] = json.load(f)
        logger.info("✅ Loaded Phase 1 foundation design")
    except Exception as e:
        logger.warning(f"Could not load Phase 1: {e}")
    
    # Load Phase 2 results
    try:
        with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
            all_results['relationship_data'] = json.load(f)
        logger.info("✅ Loaded Phase 2 relationship extraction")
    except Exception as e:
        logger.warning(f"Could not load Phase 2: {e}")
    
    # Load Phase 3 results
    try:
        with open('output/phase3_refinement_results.json', 'r', encoding='utf-8') as f:
            all_results['refinement_results'] = json.load(f)
        logger.info("✅ Loaded Phase 3 refinement results")
    except Exception as e:
        logger.warning(f"Could not load Phase 3: {e}")
    
    # Load Phase 4 results
    try:
        with open('output/phase4_validation_results.json', 'r', encoding='utf-8') as f:
            all_results['validation_results'] = json.load(f)
        logger.info("✅ Loaded Phase 4 validation results")
    except Exception as e:
        logger.warning(f"Could not load Phase 4: {e}")
    
    # Load curriculum data from database
    try:
        db_manager = DatabaseManager()
        all_results['curriculum_data'] = db_manager.extract_all_curriculum_data()
        logger.info(f"✅ Loaded curriculum data from database")
        logger.info(f"   - Achievement standards: {len(all_results['curriculum_data'].get('achievement_standards', []))}")
        logger.info(f"   - Achievement levels: {len(all_results['curriculum_data'].get('achievement_levels', []))}")
    except Exception as e:
        logger.warning(f"Could not load curriculum data: {e}")
    
    return all_results

def export_to_neo4j(all_results: dict):
    """Export all data to Neo4j"""
    neo4j_manager = Neo4jManager()
    
    try:
        # Connect to Neo4j
        logger.info("Connecting to Neo4j...")
        neo4j_manager.connect()
        
        # Clear existing data
        logger.info("Clearing existing data...")
        neo4j_manager.clear_database()
        
        # Create knowledge graph
        logger.info("Creating knowledge graph...")
        neo4j_manager.create_knowledge_graph(all_results)
        
        # Verify import
        with neo4j_manager.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            node_count = result.single()["node_count"]
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            rel_count = result.single()["rel_count"]
            
            # Count by node type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            
            logger.info("\n" + "=" * 60)
            logger.info("Neo4j Import Summary:")
            logger.info("=" * 60)
            logger.info(f"Total nodes created: {node_count}")
            logger.info(f"Total relationships created: {rel_count}")
            logger.info("\nNodes by type:")
            for record in result:
                logger.info(f"  - {record['label']}: {record['count']}")
            
            # Sample relationships
            result = session.run("""
                MATCH (s)-[r]->(t)
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            logger.info("\nRelationship types:")
            for record in result:
                logger.info(f"  - {record['type']}: {record['count']}")
        
        logger.info("\n✅ Export to Neo4j completed successfully!")
        logger.info(f"You can now access the graph at: http://localhost:7474")
        logger.info(f"Login with username: neo4j, password: neo4j123")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to export to Neo4j: {e}")
        return False
    
    finally:
        neo4j_manager.close()

def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("EXPORT TO NEO4J GRAPH DATABASE")
    print("="*60)
    print("\nThis will:")
    print("1. Load all phase results")
    print("2. Load curriculum data from PostgreSQL")
    print("3. Clear existing Neo4j data")
    print("4. Create nodes for standards, levels, domains, grades")
    print("5. Create relationships from all phases")
    print("6. Build indexes and constraints")
    
    print("\n⚠️  Warning: This will clear all existing data in Neo4j")
    response = input("\nProceed with Neo4j export? (y/n): ")
    
    if response.lower() == 'y':
        # Load all results
        all_results = load_all_results()
        
        if not all_results:
            print("❌ No data to export")
            return 1
        
        # Export to Neo4j
        success = export_to_neo4j(all_results)
        
        if success:
            print("\n" + "="*60)
            print("✅ NEO4J EXPORT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Open Neo4j Browser: http://localhost:7474")
            print("2. Login with neo4j/neo4j123")
            print("3. Run queries to explore the graph:")
            print("   - MATCH (n) RETURN n LIMIT 50")
            print("   - MATCH (s:Standard)-[r]->(t:Standard) RETURN s,r,t LIMIT 50")
            return 0
        else:
            print("\n❌ Export failed - check error messages above")
            return 1
    else:
        print("\nExport cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main())