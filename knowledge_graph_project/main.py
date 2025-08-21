"""
Main orchestrator for the Knowledge Graph Construction Project
"""
import asyncio
import json
import os
from datetime import datetime
from loguru import logger
from typing import Dict, Any

# Import all phases
from src.data_manager import DatabaseManager
from src.phase1_foundation import run_phase1
from src.phase2_relationships import run_phase2
from src.phase3_refinement import run_phase3
from src.phase4_validation import run_phase4
from src.neo4j_manager import Neo4jManager
from src.ai_models import AIModelManager

class KnowledgeGraphOrchestrator:
    """Main orchestrator for the knowledge graph construction project"""
    
    def __init__(self):
        self.setup_logging()
        self.db_manager = DatabaseManager()
        self.neo4j_manager = Neo4jManager()
        self.ai_manager = AIModelManager()
        self.results = {}
        
    def setup_logging(self):
        """Setup logging configuration"""
        logger.add(
            "logs/knowledge_graph_{time}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
    async def run_complete_pipeline(self, resume_from_phase: int = 1) -> Dict[str, Any]:
        """Run the complete knowledge graph construction pipeline"""
        logger.info("=== Starting Knowledge Graph Construction Pipeline ===")
        
        start_time = datetime.now()
        
        try:
            # Phase 0: Data Preparation
            if resume_from_phase <= 0:
                await self._prepare_data()
            
            # Phase 1: Foundation Structure Design (Gemini 2.5 Pro)
            if resume_from_phase <= 1:
                await self._run_phase1()
            
            # Phase 2: Relationship Extraction (GPT-5)
            if resume_from_phase <= 2:
                await self._run_phase2()
            
            # Phase 3: Advanced Refinement (Claude Sonnet 4)
            if resume_from_phase <= 3:
                await self._run_phase3()
            
            # Phase 4: Validation and Optimization (Claude Opus 4.1)
            if resume_from_phase <= 4:
                await self._run_phase4()
            
            # Phase 5: Neo4j Graph Creation
            if resume_from_phase <= 5:
                await self._create_neo4j_graph()
            
            # Phase 6: Final Report Generation
            await self._generate_final_report()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"=== Pipeline Completed Successfully in {duration} ===")
            
            return {
                'status': 'success',
                'duration': str(duration),
                'results': self.results,
                'final_report_path': 'output/final_report.json'
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'partial_results': self.results
            }
    
    async def _prepare_data(self):
        """Phase 0: Prepare data from PostgreSQL"""
        logger.info("Phase 0: Data Preparation")
        
        try:
            # Extract curriculum data
            curriculum_data = self.db_manager.extract_all_curriculum_data()
            
            # Save extracted data
            os.makedirs('output', exist_ok=True)
            with open('output/curriculum_data.json', 'w', encoding='utf-8') as f:
                # Convert DataFrames to dict for JSON serialization
                serializable_data = {}
                for key, df in curriculum_data.items():
                    serializable_data[key] = df.to_dict('records')
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            self.results['curriculum_data'] = curriculum_data
            logger.info("Data preparation completed")
            
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise
    
    async def _run_phase1(self):
        """Phase 1: Foundation Structure Design"""
        logger.info("Phase 1: Foundation Structure Design")
        
        try:
            # Load data if not in memory
            if 'curriculum_data' not in self.results:
                self.results['curriculum_data'] = self.db_manager.extract_all_curriculum_data()
            
            # Run Phase 1
            foundation_design = await run_phase1(self.results['curriculum_data'])
            self.results['foundation_design'] = foundation_design
            
            logger.info("Phase 1 completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            raise
    
    async def _run_phase2(self):
        """Phase 2: Relationship Extraction"""
        logger.info("Phase 2: Relationship Extraction")
        
        try:
            # Load previous results if needed
            if 'foundation_design' not in self.results:
                with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
                    self.results['foundation_design'] = json.load(f)
            
            if 'curriculum_data' not in self.results:
                self.results['curriculum_data'] = self.db_manager.extract_all_curriculum_data()
            
            # Run Phase 2
            relationship_data = await run_phase2(
                self.results['curriculum_data'], 
                self.results['foundation_design']
            )
            self.results['relationship_data'] = relationship_data
            
            logger.info("Phase 2 completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            raise
    
    async def _run_phase3(self):
        """Phase 3: Advanced Refinement"""
        logger.info("Phase 3: Advanced Refinement")
        
        try:
            # Load previous results if needed
            if 'relationship_data' not in self.results:
                with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
                    self.results['relationship_data'] = json.load(f)
            
            if 'foundation_design' not in self.results:
                with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
                    self.results['foundation_design'] = json.load(f)
            
            # Run Phase 3
            refinement_results = await run_phase3(
                self.results['relationship_data'],
                self.results['foundation_design']
            )
            self.results['refinement_results'] = refinement_results
            
            logger.info("Phase 3 completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            raise
    
    async def _run_phase4(self):
        """Phase 4: Validation and Optimization"""
        logger.info("Phase 4: Validation and Optimization")
        
        try:
            # Prepare all previous results
            all_previous_results = {
                'foundation_design': self.results.get('foundation_design'),
                'relationship_data': self.results.get('relationship_data'),
                'refinement_results': self.results.get('refinement_results')
            }
            
            # Load missing results from files
            for key in all_previous_results:
                if all_previous_results[key] is None:
                    file_mapping = {
                        'foundation_design': 'output/phase1_foundation_design.json',
                        'relationship_data': 'output/phase2_relationship_extraction.json',
                        'refinement_results': 'output/phase3_refinement_results.json'
                    }
                    
                    file_path = file_mapping.get(key)
                    if file_path and os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_previous_results[key] = json.load(f)
            
            # Run Phase 4
            validation_results = await run_phase4(all_previous_results)
            self.results['validation_results'] = validation_results
            
            logger.info("Phase 4 completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 4 failed: {e}")
            raise
    
    async def _create_neo4j_graph(self):
        """Phase 5: Create Neo4j Graph"""
        logger.info("Phase 5: Neo4j Graph Creation")
        
        try:
            # Connect to Neo4j
            self.neo4j_manager.connect()
            
            # Clear existing data (optional)
            # self.neo4j_manager.clear_database()
            
            # Create knowledge graph
            self.neo4j_manager.create_knowledge_graph(self.results)
            
            # Get graph statistics
            graph_stats = self.neo4j_manager.get_graph_statistics()
            self.results['graph_statistics'] = graph_stats
            
            # Save graph statistics
            with open('output/graph_statistics.json', 'w', encoding='utf-8') as f:
                json.dump(graph_stats, f, ensure_ascii=False, indent=2)
            
            logger.info("Neo4j graph creation completed")
            
        except Exception as e:
            logger.error(f"Neo4j graph creation failed: {e}")
            # Don't raise - this is optional if Neo4j is not available
            logger.warning("Continuing without Neo4j graph creation")
        
        finally:
            self.neo4j_manager.close()
    
    async def _generate_final_report(self):
        """Generate comprehensive final report"""
        logger.info("Generating final report")
        
        try:
            # Collect usage statistics
            usage_stats = self.ai_manager.get_total_usage_stats()
            
            # Create comprehensive report
            final_report = {
                'project_info': {
                    'name': '2025년 최신 AI 모델을 활용한 지식 그래프 구축',
                    'version': '1.0.0',
                    'completion_date': datetime.now().isoformat(),
                    'total_phases': 5
                },
                'execution_summary': {
                    'phases_completed': len([k for k in self.results.keys() if k.endswith('_results') or k.endswith('_design') or k.endswith('_data')]),
                    'total_cost': usage_stats.get('total_cost', 0.0),
                    'total_tokens': {
                        'input': sum(model.get('input_tokens', 0) for model in usage_stats.get('models', {}).values()),
                        'output': sum(model.get('output_tokens', 0) for model in usage_stats.get('models', {}).values())
                    }
                },
                'phase_results': {
                    'phase1_foundation': self._summarize_phase_results('foundation_design'),
                    'phase2_relationships': self._summarize_phase_results('relationship_data'),
                    'phase3_refinement': self._summarize_phase_results('refinement_results'),
                    'phase4_validation': self._summarize_phase_results('validation_results')
                },
                'quality_assessment': self._extract_quality_assessment(),
                'usage_statistics': usage_stats,
                'graph_statistics': self.results.get('graph_statistics', {}),
                'recommendations': self._generate_recommendations(),
                'next_steps': self._suggest_next_steps()
            }
            
            # Save final report
            with open('output/final_report.json', 'w', encoding='utf-8') as f:
                json.dump(final_report, f, ensure_ascii=False, indent=2)
            
            # Generate human-readable summary
            await self._generate_executive_summary(final_report)
            
            logger.info("Final report generated successfully")
            
        except Exception as e:
            logger.error(f"Final report generation failed: {e}")
            raise
    
    def _summarize_phase_results(self, phase_key: str) -> Dict[str, Any]:
        """Summarize results for a specific phase"""
        phase_data = self.results.get(phase_key, {})
        metadata = phase_data.get('metadata', {})
        
        return {
            'completed': phase_key in self.results,
            'timestamp': metadata.get('timestamp', 'unknown'),
            'key_metrics': {k: v for k, v in metadata.items() if isinstance(v, (int, float))}
        }
    
    def _extract_quality_assessment(self) -> Dict[str, Any]:
        """Extract quality assessment from validation results"""
        validation_results = self.results.get('validation_results', {})
        quality_assessment = validation_results.get('quality_assessment', {})
        
        if quality_assessment:
            overall_eval = quality_assessment.get('quality_assessment', {}).get('overall_evaluation', {})
            return {
                'final_grade': overall_eval.get('final_grade', 'Not assessed'),
                'total_score': overall_eval.get('total_score', 0.0),
                'commercialization_readiness': overall_eval.get('commercialization_readiness', 'unknown'),
                'key_achievements': overall_eval.get('key_achievements', []),
                'critical_next_steps': overall_eval.get('critical_next_steps', [])
            }
        
        return {'status': 'not_available'}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        
        # Check validation results for recommendations
        validation_results = self.results.get('validation_results', {})
        optimization_recs = validation_results.get('optimization_recommendations', {})
        
        if optimization_recs:
            for phase in optimization_recs.get('implementation_roadmap', {}).values():
                if isinstance(phase, list):
                    recommendations.extend(phase)
        
        # Add general recommendations
        recommendations.extend([
            "정기적인 교육과정 업데이트 반영",
            "사용자 피드백 수집 시스템 구축",
            "성능 모니터링 대시보드 개발",
            "교육 현장 파일럿 테스트 실시"
        ])
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _suggest_next_steps(self) -> List[str]:
        """Suggest next steps for the project"""
        return [
            "교육 현장 전문가 검토 및 피드백 수집",
            "실제 수학 문항을 활용한 분류 성능 테스트",
            "사용자 인터페이스 개발 및 사용성 테스트",
            "타 교과목 확장 가능성 연구",
            "상용화를 위한 비즈니스 모델 개발",
            "지속적 업데이트를 위한 운영 체계 구축"
        ]
    
    async def _generate_executive_summary(self, final_report: Dict):
        """Generate executive summary using AI"""
        logger.info("Generating executive summary")
        
        try:
            summary_prompt = f"""
다음 지식 그래프 구축 프로젝트 결과를 바탕으로 경영진용 요약 보고서를 작성하세요.

프로젝트 결과:
{json.dumps(final_report, ensure_ascii=False, indent=2)[:3000]}...

요약 보고서에 포함할 내용:
1. 프로젝트 개요 및 목표
2. 주요 성과와 결과물
3. 기술적 혁신 요소
4. 비용 효율성 분석
5. 품질 평가 결과
6. 상용화 가능성
7. 향후 계획 및 권장사항

간결하고 이해하기 쉬운 언어로 작성하세요.
"""
            
            response = await self.ai_manager.get_completion('claude_sonnet', summary_prompt)
            
            # Save executive summary
            with open('output/executive_summary.md', 'w', encoding='utf-8') as f:
                f.write("# 지식 그래프 구축 프로젝트 경영진 요약 보고서\n\n")
                f.write(response['content'])
            
            logger.info("Executive summary generated")
            
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            # Create fallback summary
            with open('output/executive_summary.md', 'w', encoding='utf-8') as f:
                f.write("# 지식 그래프 구축 프로젝트 요약\n\n")
                f.write("프로젝트가 성공적으로 완료되었습니다. 상세 결과는 final_report.json을 참조하세요.")

# CLI Interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Graph Construction Pipeline')
    parser.add_argument('--resume-from', type=int, default=1, 
                       help='Resume from specific phase (0-5)')
    parser.add_argument('--phase-only', type=int, 
                       help='Run only specific phase')
    
    args = parser.parse_args()
    
    orchestrator = KnowledgeGraphOrchestrator()
    
    if args.phase_only is not None:
        # Run specific phase only
        logger.info(f"Running Phase {args.phase_only} only")
        
        if args.phase_only == 1:
            await orchestrator._run_phase1()
        elif args.phase_only == 2:
            await orchestrator._run_phase2()
        elif args.phase_only == 3:
            await orchestrator._run_phase3()
        elif args.phase_only == 4:
            await orchestrator._run_phase4()
        elif args.phase_only == 5:
            await orchestrator._create_neo4j_graph()
        else:
            logger.error("Invalid phase number")
    else:
        # Run complete pipeline
        result = await orchestrator.run_complete_pipeline(args.resume_from)
        print(f"Pipeline result: {result['status']}")
        if result['status'] == 'success':
            print(f"Results saved to: {result.get('final_report_path')}")

if __name__ == "__main__":
    asyncio.run(main())
