#!/usr/bin/env python3
"""
Execute Phase 3: Advanced Refinement
"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

from src.phase3_refinement import run_phase3
from loguru import logger

async def execute_phase3():
    """Execute Phase 3 with proper data loading"""
    
    logger.info("=" * 60)
    logger.info("Starting Phase 3: Advanced Refinement")
    logger.info("=" * 60)
    
    try:
        # Load Phase 1 output (foundation design)
        logger.info("Loading Phase 1 foundation design...")
        with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
            foundation_design = json.load(f)
        
        logger.info(f"✅ Loaded foundation design with {len(foundation_design)} components")
        
        # Load Phase 2 output (relationship extraction)
        logger.info("\nLoading Phase 2 relationship extraction...")
        with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
            relationship_data = json.load(f)
        
        logger.info(f"✅ Loaded relationship data:")
        logger.info(f"   - Total relations: {len(relationship_data.get('weighted_relations', []))}")
        logger.info(f"   - Relation types: {relationship_data.get('metadata', {}).get('relation_types_count', 0)}")
        logger.info(f"   - Foundation integrated: {relationship_data.get('metadata', {}).get('foundation_design_integrated', False)}")
        
        # Run Phase 3
        logger.info("\n" + "=" * 60)
        logger.info("Executing Phase 3 refinement with Claude Sonnet 4...")
        logger.info("=" * 60)
        
        refinement_results = await run_phase3(relationship_data, foundation_design)
        
        # Check results
        logger.info("\n" + "=" * 60)
        logger.info("Phase 3 Execution Results:")
        logger.info("=" * 60)
        
        if refinement_results:
            logger.info("✅ Relationship refinement completed successfully!")
            
            # Display refinement summary
            logger.info("\nRefinement Summary:")
            
            # Final relations
            final_relations = refinement_results.get('final_relations', [])
            logger.info(f"   - Final refined relations: {len(final_relations)}")
            
            # Missing relations added
            missing_relations = refinement_results.get('missing_relations', [])
            logger.info(f"   - Missing relations added: {len(missing_relations)}")
            
            # Data integration
            if 'data_integration' in refinement_results:
                integration = refinement_results['data_integration']
                logger.info("\n✅ Data Integration Report:")
                
                # Phase 1 components
                phase1 = integration.get('phase1_components', {})
                logger.info("   From Phase 1:")
                logger.info(f"      - Node types: {phase1.get('node_types', 0)}")
                logger.info(f"      - Relationship categories: {phase1.get('relationship_categories', 0)}")
                logger.info(f"      - Hierarchy levels: {phase1.get('hierarchy_levels', 0)}")
                logger.info(f"      - Clusters used: {phase1.get('clusters_used', 0)}")
                
                # Phase 2 components
                phase2 = integration.get('phase2_components', {})
                logger.info("   From Phase 2:")
                logger.info(f"      - Relations extracted: {phase2.get('relations_extracted', 0)}")
                logger.info(f"      - Relation types: {phase2.get('relation_types', 0)}")
                logger.info(f"      - DB suggestions: {phase2.get('db_suggestions', 0)}")
                
                # Phase 3 enhancements
                phase3 = integration.get('phase3_enhancements', {})
                logger.info("   Phase 3 Enhancements:")
                logger.info(f"      - Relations refined: {phase3.get('relations_refined', 0)}")
                logger.info(f"      - Missing added: {phase3.get('missing_added', 0)}")
                logger.info(f"      - Conflicts resolved: {phase3.get('conflicts_resolved', 0)}")
                logger.info(f"      - Hierarchical validated: {phase3.get('hierarchical_validated', 0)}")
            
            # Metadata
            metadata = refinement_results.get('metadata', {})
            logger.info(f"\nMetadata:")
            logger.info(f"   - Total relations refined: {metadata.get('total_relations_refined', 0)}")
            logger.info(f"   - New relations added: {metadata.get('new_relations_added', 0)}")
            logger.info(f"   - Conflicts resolved: {metadata.get('conflicts_resolved', 0)}")
            logger.info(f"   - Data fully integrated: {metadata.get('data_fully_integrated', False)}")
            
            # Sample refined relations
            if final_relations:
                logger.info("\nSample refined relationships (first 5):")
                for i, rel in enumerate(final_relations[:5], 1):
                    logger.info(f"   {i}. {rel.get('source_code')} → {rel.get('target_code')}")
                    logger.info(f"      Type: {rel.get('refined_type', rel.get('relation_type'))}")
                    logger.info(f"      Weight: {rel.get('weight', 'N/A')}")
                    if 'educational_context' in rel:
                        logger.info(f"      Context: {rel['educational_context'][:50]}...")
            
            # Check output file
            output_file = Path('output/phase3_refinement_results.json')
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                logger.info(f"\n✅ Output saved to: {output_file}")
                logger.info(f"   File size: {file_size:.2f} KB")
            
            return True
        else:
            logger.error("❌ Phase 3 execution failed - no results returned")
            return False
            
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("Please ensure Phase 1 and Phase 2 have been run first")
        return False
        
    except Exception as e:
        logger.error(f"❌ Phase 3 execution failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("PHASE 3: ADVANCED REFINEMENT")
    print("="*60)
    print("\nThis will:")
    print("1. Load Phase 1 foundation design")
    print("2. Load Phase 2 relationship extraction")
    print("3. Refine relationships using Claude Sonnet 4")
    print("4. Add educational metadata")
    print("5. Identify missing critical relationships")
    print("6. Save results to output/phase3_refinement_results.json")
    
    print("\n⚠️  Note: This will use Claude Sonnet 4 API (costs apply)")
    response = input("\nProceed with Phase 3 execution? (y/n): ")
    
    if response.lower() == 'y':
        success = asyncio.run(execute_phase3())
        
        if success:
            print("\n" + "="*60)
            print("✅ PHASE 3 COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Review output/phase3_refinement_results.json")
            print("2. Run Phase 4 for validation and optimization")
            print("3. Export to Neo4j for visualization")
            return 0
        else:
            print("\n" + "="*60)
            print("❌ PHASE 3 FAILED")
            print("="*60)
            print("\nPlease check the error messages above")
            return 1
    else:
        print("\nPhase 3 execution cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main())