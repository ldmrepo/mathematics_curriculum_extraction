#!/usr/bin/env python3
"""
Execute Phase 4: Validation and Optimization
"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.append('/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project')

from src.phase4_validation import run_phase4
from loguru import logger

async def execute_phase4():
    """Execute Phase 4 with all previous phase data"""
    
    logger.info("=" * 60)
    logger.info("Starting Phase 4: Validation and Optimization")
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
        
        logger.info(f"✅ Loaded relationship data with {len(relationship_data.get('weighted_relations', []))} relations")
        
        # Load Phase 3 output (refinement results)
        logger.info("\nLoading Phase 3 refinement results...")
        with open('output/phase3_refinement_results.json', 'r', encoding='utf-8') as f:
            refinement_results = json.load(f)
        
        logger.info(f"✅ Loaded refinement results:")
        logger.info(f"   - Final relations: {len(refinement_results.get('final_relations', []))}")
        logger.info(f"   - Missing relations added: {len(refinement_results.get('missing_relations', []))}")
        
        # Prepare all results for validation
        all_results = {
            'foundation_design': foundation_design,
            'relationship_data': relationship_data,
            'refinement_results': refinement_results
        }
        
        # Run Phase 4
        logger.info("\n" + "=" * 60)
        logger.info("Executing Phase 4 validation with GPT-4o...")
        logger.info("=" * 60)
        
        validation_results = await run_phase4(all_results)
        
        # Check results
        logger.info("\n" + "=" * 60)
        logger.info("Phase 4 Execution Results:")
        logger.info("=" * 60)
        
        if validation_results:
            logger.info("✅ Validation and optimization completed successfully!")
            
            # Display validation summary
            logger.info("\nValidation Summary:")
            
            # Validation report
            validation_report = validation_results.get('validation_report', {})
            logger.info(f"   - Structural integrity: {validation_report.get('structural_integrity', 'N/A')}")
            logger.info(f"   - Type consistency: {validation_report.get('type_consistency', 'N/A')}")
            logger.info(f"   - Weight validity: {validation_report.get('weight_validity', 'N/A')}")
            
            # Cycle detection
            cycle_detection = validation_results.get('cycle_detection', {})
            logger.info(f"\n✅ Cycle Detection:")
            logger.info(f"   - Cycles found: {cycle_detection.get('cycles_found', 0)}")
            logger.info(f"   - Graph is DAG: {cycle_detection.get('is_dag', False)}")
            
            # Educational coherence
            coherence = validation_results.get('educational_coherence', {})
            logger.info(f"\n✅ Educational Coherence:")
            logger.info(f"   - Grade progression valid: {coherence.get('grade_progression_valid', False)}")
            logger.info(f"   - Domain consistency: {coherence.get('domain_consistency', 'N/A')}")
            logger.info(f"   - Prerequisite logic sound: {coherence.get('prerequisite_logic_sound', False)}")
            
            # Coverage analysis
            coverage = validation_results.get('coverage_analysis', {})
            logger.info(f"\n✅ Coverage Analysis:")
            logger.info(f"   - Standards covered: {coverage.get('standards_covered', 0)}/{coverage.get('total_standards', 0)}")
            logger.info(f"   - Coverage percentage: {coverage.get('coverage_percentage', 0):.1f}%")
            logger.info(f"   - Isolated nodes: {coverage.get('isolated_nodes', 0)}")
            
            # Quality assessment
            quality = validation_results.get('quality_assessment', {})
            logger.info(f"\n✅ Quality Assessment:")
            logger.info(f"   - Overall score: {quality.get('overall_score', 0)}/100")
            logger.info(f"   - Graph density: {quality.get('graph_density', 0):.3f}")
            logger.info(f"   - Clustering coefficient: {quality.get('clustering_coefficient', 0):.3f}")
            
            # Optimization recommendations
            recommendations = validation_results.get('optimization_recommendations', {})
            if recommendations:
                rec_items = recommendations.get('recommendations', []) if isinstance(recommendations, dict) else recommendations
                if rec_items:
                    logger.info(f"\n📋 Optimization Recommendations ({len(rec_items)} items):")
                    for i, rec in enumerate(rec_items[:5] if isinstance(rec_items, list) else list(rec_items.items())[:5], 1):
                        if isinstance(rec, dict):
                            logger.info(f"   {i}. {rec.get('category', 'General')}: {rec.get('recommendation', '')[:80]}...")
                        elif isinstance(rec, tuple):
                            logger.info(f"   {i}. {rec[0]}: {str(rec[1])[:80]}...")
                        else:
                            logger.info(f"   {i}. {str(rec)[:80]}...")
            
            # Metadata
            metadata = validation_results.get('metadata', {})
            logger.info(f"\nMetadata:")
            logger.info(f"   - Total validations performed: {metadata.get('total_validations', 0)}")
            logger.info(f"   - Issues found: {metadata.get('issues_found', 0)}")
            logger.info(f"   - Critical issues: {metadata.get('critical_issues', 0)}")
            logger.info(f"   - Optimization potential: {metadata.get('optimization_potential', 'N/A')}")
            
            # Check output file
            output_file = Path('output/phase4_validation_results.json')
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                logger.info(f"\n✅ Output saved to: {output_file}")
                logger.info(f"   File size: {file_size:.2f} KB")
            
            return True
        else:
            logger.error("❌ Phase 4 execution failed - no results returned")
            return False
            
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("Please ensure Phase 1, 2, and 3 have been run first")
        return False
        
    except Exception as e:
        logger.error(f"❌ Phase 4 execution failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("PHASE 4: VALIDATION AND OPTIMIZATION")
    print("="*60)
    print("\nThis will:")
    print("1. Load all previous phase outputs")
    print("2. Validate structural integrity")
    print("3. Detect cycles in relationships")
    print("4. Check educational coherence")
    print("5. Analyze coverage and completeness")
    print("6. Generate optimization recommendations")
    print("7. Save results to output/phase4_validation_results.json")
    
    print("\n⚠️  Note: This will use GPT-4o API (costs apply)")
    response = input("\nProceed with Phase 4 execution? (y/n): ")
    
    if response.lower() == 'y':
        success = asyncio.run(execute_phase4())
        
        if success:
            print("\n" + "="*60)
            print("✅ PHASE 4 COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Review output/phase4_validation_results.json")
            print("2. Export to Neo4j for visualization")
            print("3. Generate final report")
            return 0
        else:
            print("\n" + "="*60)
            print("❌ PHASE 4 FAILED")
            print("="*60)
            print("\nPlease check the error messages above")
            return 1
    else:
        print("\nPhase 4 execution cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main())