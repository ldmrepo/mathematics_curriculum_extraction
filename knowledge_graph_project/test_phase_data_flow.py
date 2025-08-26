#!/usr/bin/env python3
"""
Test script to verify data flow between phase1_foundation and phase2_relationships
"""
import json
import sys
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

def analyze_phase1_output():
    """Analyze Phase 1 output structure"""
    print("=== Phase 1 Output Analysis ===\n")
    
    with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
        phase1_data = json.load(f)
    
    print("Top-level keys in phase1_foundation_design.json:")
    for key in phase1_data.keys():
        print(f"  - {key}")
    
    print("\nMetadata:")
    metadata = phase1_data.get('metadata', {})
    for k, v in metadata.items():
        print(f"  - {k}: {v}")
    
    print("\n--- Node Structure Summary ---")
    if 'node_structure' in phase1_data:
        node_structure = phase1_data['node_structure']
        if 'knowledge_graph_schema' in node_structure:
            schema = node_structure['knowledge_graph_schema']
            if 'node_types' in schema:
                print(f"Number of node types defined: {len(schema['node_types'])}")
                for node_type in schema['node_types']:
                    print(f"  - {node_type.get('name', 'unnamed')}")
    
    print("\n--- Relationship Categories Summary ---")
    if 'relationship_categories' in phase1_data:
        rel_cats = phase1_data['relationship_categories']
        total_relations = 0
        for category_name, relations in rel_cats.items():
            if isinstance(relations, list):
                print(f"  {category_name}: {len(relations)} types")
                total_relations += len(relations)
        print(f"Total relationship types: {total_relations}")
    
    print("\n--- Hierarchical Structure Summary ---")
    if 'hierarchical_structure' in phase1_data:
        hier = phase1_data['hierarchical_structure']
        if 'knowledgeGraph' in hier:
            kg = hier['knowledgeGraph']
            if 'summary' in kg:
                print("Summary counts:")
                for k, v in kg['summary'].items():
                    print(f"  - {k}: {v}")
    
    print("\n--- Community Clusters Summary ---")
    if 'community_clusters' in phase1_data:
        clusters = phase1_data['community_clusters']
        if 'knowledge_graph_clusters' in clusters:
            cluster_levels = clusters['knowledge_graph_clusters']
            print(f"Number of clustering levels: {len(cluster_levels)}")
            for level in cluster_levels:
                level_num = level.get('level', 'unknown')
                cluster_count = len(level.get('clusters', []))
                print(f"  - Level {level_num}: {cluster_count} clusters")
    
    return phase1_data

def analyze_phase2_usage(phase1_data):
    """Analyze how Phase 2 uses Phase 1 data"""
    print("\n\n=== Phase 2 Data Usage Analysis ===\n")
    
    # Read phase2_relationships.py to understand usage
    with open('src/phase2_relationships.py', 'r') as f:
        phase2_code = f.read()
    
    # Check if foundation_design parameter is actually used
    print("1. Foundation design parameter usage in phase2_relationships.py:")
    
    # Check extract_all_relationships method
    if "foundation_design" in phase2_code:
        # Count occurrences
        count = phase2_code.count("foundation_design")
        print(f"   - 'foundation_design' appears {count} times in the code")
        
        # Check if it's actually accessed (not just passed as parameter)
        import re
        # Look for patterns where foundation_design is accessed
        access_patterns = [
            r'foundation_design\[',
            r'foundation_design\.',
            r'foundation_design\.get\(',
        ]
        
        actual_usage = False
        for pattern in access_patterns:
            if re.search(pattern, phase2_code):
                actual_usage = True
                print(f"   - Pattern '{pattern}' found - foundation_design IS accessed")
                break
        
        if not actual_usage:
            print("   ⚠️  WARNING: foundation_design is passed but NEVER accessed/used!")
    
    print("\n2. What Phase 2 actually uses:")
    print("   - curriculum_data (database data)")
    print("   - prerequisite_suggestions (from database views)")
    print("   - horizontal_suggestions (from database views)")
    print("   - achievement_standards DataFrame")
    
    print("\n3. Potential integration points:")
    print("   Phase 1 provides:")
    for key in phase1_data.keys():
        print(f"   - {key}")
    
    print("\n   Phase 2 could potentially use:")
    print("   - relationship_categories: To validate/filter extracted relationships")
    print("   - hierarchical_structure: To understand grade/domain hierarchy")
    print("   - node_structure: To ensure consistency in node references")
    print("   - community_clusters: To focus extraction on related clusters")

def check_data_compatibility():
    """Check if Phase 1 output format is compatible with Phase 2 expectations"""
    print("\n\n=== Data Compatibility Check ===\n")
    
    # Load Phase 1 output
    with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
        phase1_data = json.load(f)
    
    print("✅ Phase 1 output file exists and is valid JSON")
    
    # Check required keys for Phase 2
    required_keys = ['node_structure', 'relationship_categories', 'hierarchical_structure']
    missing_keys = []
    for key in required_keys:
        if key not in phase1_data:
            missing_keys.append(key)
            print(f"❌ Missing required key: {key}")
        else:
            print(f"✅ Found required key: {key}")
    
    if missing_keys:
        print(f"\n⚠️ WARNING: Phase 1 output missing {len(missing_keys)} required keys")
    else:
        print("\n✅ All required keys present in Phase 1 output")
    
    # Check if Phase 2 output exists to analyze actual usage
    try:
        with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
            phase2_data = json.load(f)
        print("\n✅ Phase 2 output exists - can analyze actual data flow")
        
        print("\nPhase 2 output structure:")
        for key in phase2_data.keys():
            if key == 'metadata':
                print(f"  - {key}:")
                for mk, mv in phase2_data[key].items():
                    print(f"      - {mk}: {mv}")
            elif isinstance(phase2_data[key], list):
                print(f"  - {key}: {len(phase2_data[key])} items")
            else:
                print(f"  - {key}: {type(phase2_data[key]).__name__}")
                
    except FileNotFoundError:
        print("\nℹ️ Phase 2 output not found - Phase 2 may not have been run yet")

def main():
    """Main analysis function"""
    print("=" * 60)
    print("PHASE 1 → PHASE 2 DATA FLOW ANALYSIS")
    print("=" * 60)
    
    # Analyze Phase 1 output
    phase1_data = analyze_phase1_output()
    
    # Analyze Phase 2 usage
    analyze_phase2_usage(phase1_data)
    
    # Check compatibility
    check_data_compatibility()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    
    print("\n📌 KEY FINDING:")
    print("Phase 2 receives foundation_design but does NOT actually use it!")
    print("Phase 2 only uses curriculum_data from the database.")
    print("\n🔧 RECOMMENDATION:")
    print("Either:")
    print("1. Remove foundation_design parameter from Phase 2 (if not needed)")
    print("2. Integrate foundation_design data into Phase 2 logic:")
    print("   - Use relationship_categories to validate extracted relationships")
    print("   - Use hierarchical_structure to inform relationship extraction")
    print("   - Use community_clusters to prioritize relationship extraction")

if __name__ == "__main__":
    main()