#!/usr/bin/env python3
"""
Verify Neo4j import completeness
"""
import json
import sys
from pathlib import Path
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

def load_phase_data():
    """Load all phase output data"""
    phase_data = {}
    
    # Load Phase 3 refinement results (final relations)
    try:
        with open('output/phase3_refinement_results.json', 'r', encoding='utf-8') as f:
            phase3 = json.load(f)
            phase_data['phase3_final_relations'] = len(phase3.get('final_relations', []))
            phase_data['phase3_missing_relations'] = len(phase3.get('missing_relations', []))
            
            # Count unique source/target codes
            unique_sources = set()
            unique_targets = set()
            for rel in phase3.get('final_relations', []):
                unique_sources.add(rel.get('source_code'))
                unique_targets.add(rel.get('target_code'))
            phase_data['unique_nodes_in_relations'] = len(unique_sources.union(unique_targets))
    except Exception as e:
        logger.error(f"Failed to load Phase 3: {e}")
    
    # Load Phase 2 relationship extraction
    try:
        with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
            phase2 = json.load(f)
            phase_data['phase2_weighted_relations'] = len(phase2.get('weighted_relations', []))
    except Exception as e:
        logger.error(f"Failed to load Phase 2: {e}")
    
    # Load Phase 1 foundation design
    try:
        with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
            phase1 = json.load(f)
            phase_data['phase1_components'] = len(phase1)
    except Exception as e:
        logger.error(f"Failed to load Phase 1: {e}")
    
    return phase_data

def verify_neo4j_data():
    """Verify data in Neo4j"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j123")
    
    neo4j_data = {}
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) AS count")
            neo4j_data['total_nodes'] = result.single()["count"]
            
            # Count total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            neo4j_data['total_relationships'] = result.single()["count"]
            
            # Count AchievementStandard nodes
            result = session.run("MATCH (n:AchievementStandard) RETURN count(n) AS count")
            neo4j_data['achievement_standards'] = result.single()["count"]
            
            # Count AchievementLevel nodes
            result = session.run("MATCH (n:AchievementLevel) RETURN count(n) AS count")
            neo4j_data['achievement_levels'] = result.single()["count"]
            
            # Count relationship types and their counts
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            neo4j_data['relationship_types'] = {record['type']: record['count'] for record in result}
            
            # Count PREREQUISITE relationships specifically
            result = session.run("MATCH ()-[r:PREREQUISITE]->() RETURN count(r) AS count")
            neo4j_data['prerequisite_relations'] = result.single()["count"]
            
            # Count RELATED_TO relationships
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count")
            neo4j_data['related_to_relations'] = result.single()["count"]
            
            # Count standards with relationships
            result = session.run("""
                MATCH (s:AchievementStandard)-[r]-(t:AchievementStandard)
                RETURN count(DISTINCT s) AS count
            """)
            neo4j_data['standards_with_relations'] = result.single()["count"]
            
            # Check for isolated standards (no relationships to other standards)
            result = session.run("""
                MATCH (s:AchievementStandard)
                WHERE NOT (s)-[:PREREQUISITE|:RELATED_TO|:SIMILAR_TO|:BRIDGES_DOMAIN]-(:AchievementStandard)
                RETURN count(s) AS count
            """)
            neo4j_data['isolated_standards'] = result.single()["count"]
            
            # Count standards by grade level
            result = session.run("""
                MATCH (g:GradeLevel)-[:CONTAINS_STANDARD]->(s:AchievementStandard)
                RETURN g.name AS grade, g.grade_start AS grade_start, count(s) AS count
                ORDER BY grade_start
            """)
            neo4j_data['standards_by_grade'] = {record['grade']: record['count'] for record in result}
            
        driver.close()
        return neo4j_data
        
    except Exception as e:
        logger.error(f"Failed to verify Neo4j data: {e}")
        return None

def generate_verification_report(phase_data, neo4j_data):
    """Generate verification report"""
    
    print("\n" + "=" * 70)
    print("NEO4J DATA IMPORT VERIFICATION REPORT")
    print("=" * 70)
    
    print("\n📊 PHASE OUTPUT DATA:")
    print("-" * 40)
    print(f"Phase 1 Components: {phase_data.get('phase1_components', 0)}")
    print(f"Phase 2 Weighted Relations: {phase_data.get('phase2_weighted_relations', 0)}")
    print(f"Phase 3 Final Relations: {phase_data.get('phase3_final_relations', 0)}")
    print(f"Phase 3 Missing Relations Added: {phase_data.get('phase3_missing_relations', 0)}")
    print(f"Unique Nodes in Relations: {phase_data.get('unique_nodes_in_relations', 0)}")
    
    print("\n🗄️ NEO4J DATABASE DATA:")
    print("-" * 40)
    print(f"Total Nodes: {neo4j_data.get('total_nodes', 0)}")
    print(f"Total Relationships: {neo4j_data.get('total_relationships', 0)}")
    print(f"Achievement Standards: {neo4j_data.get('achievement_standards', 0)}")
    print(f"Achievement Levels: {neo4j_data.get('achievement_levels', 0)}")
    
    print("\n🔗 RELATIONSHIP BREAKDOWN:")
    print("-" * 40)
    for rel_type, count in neo4j_data.get('relationship_types', {}).items():
        print(f"  {rel_type}: {count}")
    
    print("\n📈 STANDARDS ANALYSIS:")
    print("-" * 40)
    print(f"Standards with Relations: {neo4j_data.get('standards_with_relations', 0)}")
    print(f"Isolated Standards: {neo4j_data.get('isolated_standards', 0)}")
    
    print("\n🎓 STANDARDS BY GRADE:")
    print("-" * 40)
    for grade, count in neo4j_data.get('standards_by_grade', {}).items():
        print(f"  {grade}: {count}")
    
    print("\n✅ VERIFICATION RESULTS:")
    print("-" * 40)
    
    # Check if Phase 3 relations were imported
    phase3_relations = phase_data.get('phase3_final_relations', 0)
    prerequisite_count = neo4j_data.get('prerequisite_relations', 0)
    related_count = neo4j_data.get('related_to_relations', 0)
    
    # Calculate expected vs actual
    expected_relations = phase3_relations
    actual_standard_relations = prerequisite_count + related_count + \
                                neo4j_data.get('relationship_types', {}).get('SIMILAR_TO', 0) + \
                                neo4j_data.get('relationship_types', {}).get('BRIDGES_DOMAIN', 0)
    
    print(f"Expected Standard Relations (Phase 3): {expected_relations}")
    print(f"Actual Standard Relations in Neo4j: {actual_standard_relations}")
    
    if actual_standard_relations >= expected_relations * 0.8:  # Allow 20% tolerance
        print("✅ Relationship import: SUCCESSFUL")
    else:
        print(f"⚠️ Relationship import: PARTIAL ({actual_standard_relations}/{expected_relations})")
    
    # Check node completeness
    if neo4j_data.get('achievement_standards', 0) == 181:
        print("✅ Achievement Standards: COMPLETE (181/181)")
    else:
        print(f"⚠️ Achievement Standards: {neo4j_data.get('achievement_standards', 0)}/181")
    
    if neo4j_data.get('achievement_levels', 0) >= 663:
        print(f"✅ Achievement Levels: COMPLETE ({neo4j_data.get('achievement_levels', 0)}/663)")
    else:
        print(f"⚠️ Achievement Levels: {neo4j_data.get('achievement_levels', 0)}/663")
    
    # Check for data integrity
    isolated_ratio = neo4j_data.get('isolated_standards', 0) / max(neo4j_data.get('achievement_standards', 1), 1)
    if isolated_ratio < 0.5:  # Less than 50% isolated is good
        print(f"✅ Graph Connectivity: GOOD ({100*(1-isolated_ratio):.1f}% connected)")
    else:
        print(f"⚠️ Graph Connectivity: POOR ({100*(1-isolated_ratio):.1f}% connected)")
    
    print("\n" + "=" * 70)
    
    # Return verification summary
    return {
        'success': actual_standard_relations >= expected_relations * 0.8,
        'completeness': {
            'standards': neo4j_data.get('achievement_standards', 0) == 181,
            'levels': neo4j_data.get('achievement_levels', 0) >= 663,
            'relationships': actual_standard_relations >= expected_relations * 0.8
        },
        'stats': {
            'expected_relations': expected_relations,
            'actual_relations': actual_standard_relations,
            'isolated_standards': neo4j_data.get('isolated_standards', 0),
            'connectivity': 100*(1-isolated_ratio)
        }
    }

def main():
    """Main verification function"""
    
    print("\n" + "="*60)
    print("VERIFYING NEO4J IMPORT COMPLETENESS")
    print("="*60)
    
    # Load phase data
    print("\nLoading phase output data...")
    phase_data = load_phase_data()
    
    # Verify Neo4j data
    print("Querying Neo4j database...")
    neo4j_data = verify_neo4j_data()
    
    if not neo4j_data:
        print("❌ Failed to connect to Neo4j")
        return 1
    
    # Generate report
    summary = generate_verification_report(phase_data, neo4j_data)
    
    if summary['success']:
        print("\n✅ VERIFICATION PASSED: Data successfully imported to Neo4j")
    else:
        print("\n⚠️ VERIFICATION WARNING: Some data may be missing")
        print("\nRecommended actions:")
        print("1. Check Neo4j logs for import errors")
        print("2. Re-run export_to_neo4j.py")
        print("3. Verify Phase 3 output file integrity")
    
    return 0 if summary['success'] else 1

if __name__ == "__main__":
    sys.exit(main())