#!/usr/bin/env python3
"""
Test script to verify metadata calculation fixes in phase1_foundation.py
"""
import json
import sys
import os
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

from src.phase1_foundation import FoundationDesigner
from src.ai_models import AIModelManager
from config.settings import Config

def test_metadata_calculation():
    """Test the fixed metadata calculation functions"""
    
    # Initialize AI manager (no settings needed as it uses global config)
    ai_manager = AIModelManager()
    phase1 = FoundationDesigner(ai_manager)
    
    # Load the saved responses to simulate the actual data
    print("Loading saved responses...")
    
    # Load hierarchical structure
    with open('debug/hierarchical_structure_response.txt', 'r') as f:
        content = f.read()
        # Extract JSON from markdown code block
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        hierarchical_data = json.loads(content[json_start:json_end])
    
    # Load node structure
    with open('debug/node_structure_response.txt', 'r') as f:
        content = f.read()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        node_data = json.loads(content[json_start:json_end])
    
    # Load relationship categories
    with open('debug/relationship_categories_response.txt', 'r') as f:
        content = f.read()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        relationship_data = json.loads(content[json_start:json_end])
    
    # Store hierarchical summary for metadata calculation
    phase1.hierarchical_summary = hierarchical_data.get('knowledgeGraph', {}).get('summary', {})
    
    print("\n=== Testing Metadata Calculation ===")
    print(f"Hierarchical Summary: {phase1.hierarchical_summary}")
    
    # Test node count calculation
    print("\n1. Testing _count_planned_nodes:")
    node_count = phase1._count_planned_nodes(node_data)
    print(f"   Calculated node count: {node_count}")
    print(f"   Expected (from summary): ~1497 (181+663+291+362)")
    
    # Test relationship estimate calculation
    print("\n2. Testing _estimate_relationships:")
    relationship_count = phase1._estimate_relationships(relationship_data)
    print(f"   Calculated relationship count: {relationship_count}")
    print(f"   Expected: 12 relationship types defined")
    
    # Load and check the actual output file
    print("\n3. Checking output file metadata:")
    with open('output/phase1_foundation_design.json', 'r') as f:
        output_data = json.load(f)
    
    print(f"   Current metadata in output:")
    print(f"   - total_nodes_planned: {output_data['metadata'].get('total_nodes_planned', 'N/A')}")
    print(f"   - total_relationships_estimated: {output_data['metadata'].get('total_relationships_estimated', 'N/A')}")
    
    # Now regenerate with fixed functions
    print("\n4. Regenerating foundation design with fixes...")
    
    # Create foundation design with fixed metadata
    foundation_design = {
        "project_name": "2022 개정 한국 수학과 교육과정 지식 그래프",
        "description": "초등학교 1학년부터 중학교 3학년까지의 수학 교육과정을 체계적으로 구조화한 지식 그래프",
        "node_structure": node_data,
        "relationship_categories": relationship_data,
        "hierarchical_structure": hierarchical_data,
        "community_clusters": output_data.get('community_clusters', {}),
        "metadata": {
            "total_nodes_planned": node_count,
            "total_relationships_estimated": relationship_count,
            "design_timestamp": output_data['metadata'].get('design_timestamp', ''),
            "complexity_level": "high",
            "data_sources": output_data['metadata'].get('data_sources', [])
        }
    }
    
    # Save updated design
    output_path = 'output/phase1_foundation_design_fixed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(foundation_design, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Fixed design saved to: {output_path}")
    print(f"   - total_nodes_planned: {foundation_design['metadata']['total_nodes_planned']}")
    print(f"   - total_relationships_estimated: {foundation_design['metadata']['total_relationships_estimated']}")
    
    return node_count, relationship_count

if __name__ == "__main__":
    try:
        node_count, rel_count = test_metadata_calculation()
        print("\n" + "="*50)
        print("TEST COMPLETED SUCCESSFULLY")
        print(f"Final Results:")
        print(f"  - Nodes: {node_count}")
        print(f"  - Relationships: {rel_count}")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()