#!/usr/bin/env python3
"""
Execute Phase 2: Relationship Extraction
"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

from src.phase2_relationships import run_phase2
from src.data_manager import DatabaseManager
from loguru import logger

async def execute_phase2():
    """Execute Phase 2 with proper data loading"""
    
    logger.info("=" * 60)
    logger.info("Starting Phase 2: Relationship Extraction")
    logger.info("=" * 60)
    
    try:
        # Load Phase 1 output
        logger.info("Loading Phase 1 foundation design...")
        with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
            foundation_design = json.load(f)
        
        logger.info(f"✅ Loaded foundation design with {len(foundation_design)} components")
        logger.info(f"   - Node types: {len(foundation_design.get('node_structure', {}).get('knowledge_graph_schema', {}).get('node_types', []))}")
        logger.info(f"   - Relationship categories: {len(foundation_design.get('relationship_categories', {}))}")
        logger.info(f"   - Hierarchy levels: {len(foundation_design.get('hierarchical_structure', {}).get('knowledgeGraph', {}).get('hierarchicalStructure', []))}")
        logger.info(f"   - Community clusters: {len(foundation_design.get('community_clusters', {}).get('knowledge_graph_clusters', []))}")
        
        # Load curriculum data from database
        logger.info("\nLoading curriculum data from database...")
        db_manager = DatabaseManager()
        curriculum_data = db_manager.extract_all_curriculum_data()
        
        logger.info(f"✅ Loaded curriculum data:")
        logger.info(f"   - Achievement standards: {len(curriculum_data.get('achievement_standards', []))}")
        logger.info(f"   - Achievement levels: {len(curriculum_data.get('achievement_levels', []))}")
        logger.info(f"   - Content elements: {len(curriculum_data.get('content_elements', []))}")
        
        # Check for database suggestions
        if 'prerequisite_suggestions' in curriculum_data:
            logger.info(f"   - Prerequisite suggestions: {len(curriculum_data['prerequisite_suggestions'])}")
        else:
            logger.warning("   - No prerequisite suggestions found in database")
            
        if 'horizontal_suggestions' in curriculum_data:
            logger.info(f"   - Horizontal suggestions: {len(curriculum_data['horizontal_suggestions'])}")
        else:
            logger.warning("   - No horizontal suggestions found in database")
        
        # Run Phase 2
        logger.info("\n" + "=" * 60)
        logger.info("Executing Phase 2 relationship extraction...")
        logger.info("=" * 60)
        
        relationship_extraction = await run_phase2(curriculum_data, foundation_design)
        
        # Check results
        logger.info("\n" + "=" * 60)
        logger.info("Phase 2 Execution Results:")
        logger.info("=" * 60)
        
        if relationship_extraction:
            # Display extraction summary
            logger.info("✅ Relationship extraction completed successfully!")
            
            # Count relationships by type
            logger.info("\nRelationships extracted by type:")
            if 'prerequisite_relations' in relationship_extraction:
                logger.info(f"   - Prerequisite: {len(relationship_extraction['prerequisite_relations'])}")
            if 'horizontal_relations' in relationship_extraction:
                logger.info(f"   - Horizontal: {len(relationship_extraction['horizontal_relations'])}")
            if 'similarity_relations' in relationship_extraction:
                logger.info(f"   - Similarity: {len(relationship_extraction['similarity_relations'])}")
            if 'domain_bridge_relations' in relationship_extraction:
                logger.info(f"   - Domain Bridge: {len(relationship_extraction['domain_bridge_relations'])}")
            if 'grade_progression_relations' in relationship_extraction:
                logger.info(f"   - Grade Progression: {len(relationship_extraction['grade_progression_relations'])}")
            if 'cluster_relations' in relationship_extraction:
                logger.info(f"   - Cluster-based: {len(relationship_extraction['cluster_relations'])}")
            
            # Display weighted relations summary
            weighted_relations = relationship_extraction.get('weighted_relations', [])
            logger.info(f"\nTotal weighted relations: {len(weighted_relations)}")
            
            if weighted_relations:
                # Sample first few relations
                logger.info("\nSample relationships (first 5):")
                for i, rel in enumerate(weighted_relations[:5], 1):
                    logger.info(f"   {i}. {rel.get('source_code')} → {rel.get('target_code')}")
                    logger.info(f"      Type: {rel.get('relation_type')}, Weight: {rel.get('weight')}")
                    logger.info(f"      Validated: {rel.get('validated', False)}, Mapped: {rel.get('mapped_type', 'N/A')}")
            
            # Display foundation integration
            if 'foundation_integration' in relationship_extraction:
                integration = relationship_extraction['foundation_integration']
                logger.info("\n✅ Foundation Design Integration:")
                logger.info(f"   - Categories used: {integration.get('categories_used', [])}")
                logger.info(f"   - Hierarchy levels: {integration.get('hierarchy_levels', 0)}")
                logger.info(f"   - Clusters analyzed: {integration.get('clusters_analyzed', 0)}")
            
            # Display metadata
            metadata = relationship_extraction.get('metadata', {})
            logger.info(f"\nMetadata:")
            logger.info(f"   - Total relations extracted: {metadata.get('total_relations_extracted', 0)}")
            logger.info(f"   - Relation types count: {metadata.get('relation_types_count', 0)}")
            logger.info(f"   - DB suggestions used: {metadata.get('db_suggestions_used', 0)}")
            logger.info(f"   - Foundation integrated: {metadata.get('foundation_design_integrated', False)}")
            
            # Check output file
            output_file = Path('output/phase2_relationship_extraction.json')
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                logger.info(f"\n✅ Output saved to: {output_file}")
                logger.info(f"   File size: {file_size:.2f} KB")
            
            return True
        else:
            logger.error("❌ Phase 2 execution failed - no results returned")
            return False
            
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("Please ensure Phase 1 has been run first")
        return False
        
    except Exception as e:
        logger.error(f"❌ Phase 2 execution failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("PHASE 2: RELATIONSHIP EXTRACTION")
    print("="*60)
    print("\nThis will:")
    print("1. Load Phase 1 foundation design")
    print("2. Load curriculum data from database")
    print("3. Extract relationships using GPT-5")
    print("4. Validate against foundation design")
    print("5. Save results to output/phase2_relationship_extraction.json")
    
    print("\n⚠️  Note: This will use GPT-5 API (costs apply)")
    response = input("\nProceed with Phase 2 execution? (y/n): ")
    
    if response.lower() == 'y':
        success = asyncio.run(execute_phase2())
        
        if success:
            print("\n" + "="*60)
            print("✅ PHASE 2 COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Review output/phase2_relationship_extraction.json")
            print("2. Run Phase 3 for advanced refinement")
            print("3. Run Phase 4 for validation and optimization")
            return 0
        else:
            print("\n" + "="*60)
            print("❌ PHASE 2 FAILED")
            print("="*60)
            print("\nPlease check the error messages above")
            return 1
    else:
        print("\nPhase 2 execution cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main())