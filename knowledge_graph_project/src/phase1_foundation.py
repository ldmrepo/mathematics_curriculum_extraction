"""
Phase 1: Foundation Structure Design using Gemini 2.5 Pro
"""
import asyncio
import json
from typing import Dict, List, Any
from loguru import logger
from src.ai_models import AIModelManager
from src.data_manager import CurriculumDataProcessor

class FoundationDesigner:
    """Designs the foundational structure of the knowledge graph"""
    
    def __init__(self, ai_manager: AIModelManager):
        self.ai_manager = ai_manager
        self.model_name = 'gemini_pro'  # Using Gemini 2.5 Pro for 1M token context
    
    async def design_complete_structure(self, curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
        """Design complete knowledge graph structure"""
        logger.info("Starting foundation structure design with Gemini 2.5 Pro")
        
        # Create comprehensive context
        context = CurriculumDataProcessor.create_context_for_ai(curriculum_data)
        
        # Design node structure
        node_structure = await self._design_node_structure(context, curriculum_data)
        
        # Design relationship categories
        relationship_categories = await self._design_relationship_categories(context)
        
        # Design community clusters
        community_clusters = await self._design_community_clusters(context)
        
        # Design hierarchical structure
        hierarchical_structure = await self._design_hierarchical_structure(context)
        
        foundation_design = {
            'node_structure': node_structure,
            'relationship_categories': relationship_categories,
            'community_clusters': community_clusters,
            'hierarchical_structure': hierarchical_structure,
            'metadata': {
                'design_timestamp': asyncio.get_event_loop().time(),
                'total_nodes_planned': self._count_planned_nodes(node_structure),
                'total_relationships_estimated': self._estimate_relationships(relationship_categories)
            }
        }
        
        logger.info("Foundation structure design completed")
        return foundation_design
    
    async def _design_node_structure(self, context: str, curriculum_data: Dict) -> Dict[str, Any]:
        """Design node types and their attributes"""
        
        # Include sample data for better analysis
        sample_standards = curriculum_data['achievement_standards'].head(10).to_dict('records')
        sample_levels = curriculum_data['achievement_levels'].head(10).to_dict('records')
        
        prompt = f"""
{context}

샘플 성취기준 데이터:
{json.dumps(sample_standards, ensure_ascii=False, indent=2)}

샘플 성취수준 데이터:
{json.dumps(sample_levels, ensure_ascii=False, indent=2)}

위 한국 수학 교육과정 데이터를 분석하여 지식 그래프의 노드 구조를 설계하세요.

요구사항:
1. 노드 타입별 정의 (AchievementStandard, AchievementLevel, Domain, GradeLevel 등)
2. 각 노드 타입의 속성 정의
3. 노드별 특성 (난이도, 인지수준, 학습시간 등) 자동 추출 방법
4. 교육과정의 계열성과 연계성을 반영한 속성 설계

출력 형식:
JSON 형태로 구조화된 노드 설계안
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            # Extract JSON from response
            content = response['content']
            # Find JSON block
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            node_structure = json.loads(json_str)
            logger.info("Node structure designed successfully")
            return node_structure
            
        except Exception as e:
            logger.error(f"Failed to parse node structure: {e}")
            # Return fallback structure
            return self._get_fallback_node_structure()
    
    async def _design_relationship_categories(self, context: str) -> Dict[str, Any]:
        """Design relationship categories and types"""
        
        prompt = f"""
{context}

한국 수학 교육과정의 특성을 고려하여 지식 그래프의 관계(엣지) 체계를 설계하세요.

설계 기준:
1. 교육과정의 계열성 (Sequential Learning)
2. 나선형 교육과정 구조 (Spiral Curriculum)
3. 영역 간 융합 관계 (Cross-domain Integration)
4. 인지적 위계 (Cognitive Hierarchy)

관계 유형 분류:
1. 구조적 관계 (Structural Relations)
   - contains, belongs_to, part_of, has_level

2. 학습 순서 관계 (Learning Sequence Relations)
   - prerequisite, corequisite, follows, extends

3. 의미적 관계 (Semantic Relations)
   - similar_to, contrasts_with, applies_to, generalizes

각 관계 유형별로 다음을 정의하세요:
- 관계명과 설명
- 방향성 (유향/무향)
- 가중치 범위 (0.0~1.0)
- 적용 예시
- 자동 탐지 방법

출력 형식: JSON
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            relationship_categories = json.loads(json_str)
            logger.info("Relationship categories designed successfully")
            return relationship_categories
            
        except Exception as e:
            logger.error(f"Failed to parse relationship categories: {e}")
            return self._get_fallback_relationship_categories()
    
    async def _design_community_clusters(self, context: str) -> Dict[str, Any]:
        """Design community cluster definitions"""
        
        prompt = f"""
{context}

지식 그래프의 커뮤니티 클러스터 체계를 3단계 계층으로 설계하세요.

Level 0 (대분류): Resolution 0.1, 8-12개 클러스터
- 학습 단계별 큰 구분 (예: 초등 기초, 초등 응용, 중등 대수 등)

Level 1 (중분류): Resolution 0.5, 20-30개 클러스터  
- 개념 영역별 세분화 (예: 분수와 소수, 도형의 성질 등)

Level 2 (소분류): Resolution 1.0, 40-60개 클러스터
- 구체적 학습 요소별 (예: 받아올림 덧셈, 삼각형 합동 등)

각 레벨별로 다음을 정의하세요:
1. 예상 클러스터 목록
2. 클러스터 특성 (크기, 밀도, 중심성)
3. 교육적 의미
4. 클러스터 간 연결 관계

출력 형식: JSON
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            community_clusters = json.loads(json_str)
            logger.info("Community clusters designed successfully")
            return community_clusters
            
        except Exception as e:
            logger.error(f"Failed to parse community clusters: {e}")
            return self._get_fallback_community_clusters()
    
    async def _design_hierarchical_structure(self, context: str) -> Dict[str, Any]:
        """Design overall hierarchical structure"""
        
        prompt = f"""
{context}

전체 지식 그래프의 계층적 구조를 설계하세요.

계층 구조:
1. 최상위: 교육과정 전체
2. 2레벨: 학년군 (초1-2, 초3-4, 초5-6, 중1-3)  
3. 3레벨: 영역 (수와 연산, 변화와 관계, 도형과 측정, 자료와 가능성)
4. 4레벨: 성취기준
5. 5레벨: 성취수준

각 계층별로 다음을 정의하세요:
1. 노드 개수와 분포
2. 계층 간 연결 규칙
3. 계층 내 노드 간 관계
4. 탐색 및 추론 전략

추가로 교육과정의 나선형 구조를 반영한 크로스 레벨 연결도 설계하세요.

출력 형식: JSON
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            hierarchical_structure = json.loads(json_str)
            logger.info("Hierarchical structure designed successfully")
            return hierarchical_structure
            
        except Exception as e:
            logger.error(f"Failed to parse hierarchical structure: {e}")
            return self._get_fallback_hierarchical_structure()
    
    def _count_planned_nodes(self, node_structure: Dict) -> int:
        """Count total planned nodes"""
        try:
            total = 0
            for node_type, details in node_structure.get('node_types', {}).items():
                if 'estimated_count' in details:
                    total += details['estimated_count']
            return total
        except:
            return 1024  # Default estimate
    
    def _estimate_relationships(self, relationship_categories: Dict) -> int:
        """Estimate total relationships"""
        try:
            base_relationships = len(relationship_categories.get('relationship_types', {}))
            return base_relationships * 200  # Rough estimate
        except:
            return 3000  # Default estimate
    
    def _get_fallback_node_structure(self) -> Dict[str, Any]:
        """Fallback node structure"""
        return {
            "node_types": {
                "achievement_standard": {
                    "properties": ["code", "content", "difficulty", "cognitive_level"],
                    "estimated_count": 181
                },
                "achievement_level": {
                    "properties": ["level", "description", "complexity"],
                    "estimated_count": 843
                }
            }
        }
    
    def _get_fallback_relationship_categories(self) -> Dict[str, Any]:
        """Fallback relationship categories"""
        return {
            "relationship_types": {
                "prerequisite": {"weight_range": [0.8, 1.0], "directed": True},
                "similar_to": {"weight_range": [0.5, 0.9], "directed": False}
            }
        }
    
    def _get_fallback_community_clusters(self) -> Dict[str, Any]:
        """Fallback community clusters"""
        return {
            "levels": {
                "level_0": {"cluster_count": 10, "resolution": 0.1},
                "level_1": {"cluster_count": 25, "resolution": 0.5},
                "level_2": {"cluster_count": 50, "resolution": 1.0}
            }
        }
    
    def _get_fallback_hierarchical_structure(self) -> Dict[str, Any]:
        """Fallback hierarchical structure"""
        return {
            "levels": {
                "curriculum": {"count": 1},
                "grade_groups": {"count": 4},
                "domains": {"count": 4},
                "standards": {"count": 181},
                "levels": {"count": 843}
            }
        }

# Main execution function for Phase 1
async def run_phase1(curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run Phase 1: Foundation Structure Design"""
    logger.info("=== Phase 1: Foundation Structure Design ===")
    
    ai_manager = AIModelManager()
    designer = FoundationDesigner(ai_manager)
    
    try:
        foundation_design = await designer.design_complete_structure(curriculum_data)
        
        # Save results
        output_path = "output/phase1_foundation_design.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(foundation_design, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Phase 1 completed. Results saved to {output_path}")
        
        # Log usage stats
        stats = ai_manager.get_total_usage_stats()
        logger.info(f"Phase 1 Usage Stats: {stats}")
        
        return foundation_design
        
    except Exception as e:
        logger.error(f"Phase 1 failed: {e}")
        raise

if __name__ == "__main__":
    # Test run
    from src.data_manager import DatabaseManager
    
    async def test_phase1():
        db_manager = DatabaseManager()
        curriculum_data = db_manager.extract_all_curriculum_data()
        result = await run_phase1(curriculum_data)
        print("Phase 1 test completed")
    
    asyncio.run(test_phase1())
