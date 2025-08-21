"""
Phase 2: Relationship Extraction using GPT-5 with batch processing
"""
import asyncio
import json
import itertools
from typing import Dict, List, Any, Tuple
from loguru import logger
import pandas as pd
from src.ai_models import AIModelManager
from src.data_manager import CurriculumDataProcessor

class RelationshipExtractor:
    """Extracts relationships between curriculum elements using GPT-5"""
    
    def __init__(self, ai_manager: AIModelManager):
        self.ai_manager = ai_manager
        self.model_name = 'gpt5'  # Using GPT-5 for cost-efficient batch processing
    
    async def extract_all_relationships(self, curriculum_data: Dict[str, Any], foundation_design: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all relationships between curriculum elements"""
        logger.info("Starting relationship extraction with GPT-5")
        
        # Extract similarity relationships
        similarity_relations = await self._extract_similarity_relationships(curriculum_data)
        
        # Extract prerequisite relationships  
        prerequisite_relations = await self._extract_prerequisite_relationships(curriculum_data)
        
        # Extract domain bridge relationships
        domain_bridge_relations = await self._extract_domain_bridge_relationships(curriculum_data)
        
        # Extract grade progression relationships
        grade_progression_relations = await self._extract_grade_progression_relationships(curriculum_data)
        
        # Calculate initial weights
        weighted_relations = await self._calculate_initial_weights(
            similarity_relations,
            prerequisite_relations, 
            domain_bridge_relations,
            grade_progression_relations
        )
        
        relationship_extraction = {
            'similarity_relations': similarity_relations,
            'prerequisite_relations': prerequisite_relations,
            'domain_bridge_relations': domain_bridge_relations,
            'grade_progression_relations': grade_progression_relations,
            'weighted_relations': weighted_relations,
            'metadata': {
                'extraction_timestamp': asyncio.get_event_loop().time(),
                'total_relations_extracted': len(weighted_relations),
                'relation_types_count': 4
            }
        }
        
        logger.info("Relationship extraction completed")
        return relationship_extraction
    
    async def _extract_similarity_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract similarity relationships using batch processing"""
        logger.info("Extracting similarity relationships")
        
        standards = curriculum_data['achievement_standards']
        relations = []
        
        # Create batches for efficient processing
        standard_pairs = list(itertools.combinations(standards.itertuples(), 2))
        batch_size = 50  # Process 50 pairs at a time
        
        for i in range(0, len(standard_pairs), batch_size):
            batch = standard_pairs[i:i+batch_size]
            batch_relations = await self._process_similarity_batch(batch)
            relations.extend(batch_relations)
            
            logger.info(f"Processed similarity batch {i//batch_size + 1}/{(len(standard_pairs)-1)//batch_size + 1}")
        
        # Filter high-similarity relationships
        filtered_relations = [r for r in relations if r['similarity_score'] > 0.6]
        
        logger.info(f"Extracted {len(filtered_relations)} similarity relationships")
        return filtered_relations
    
    async def _process_similarity_batch(self, standard_pairs: List[Tuple]) -> List[Dict[str, Any]]:
        """Process a batch of standard pairs for similarity"""
        
        # Create batch prompt
        pairs_text = ""
        for idx, (std_a, std_b) in enumerate(standard_pairs):
            pairs_text += f"""
쌍 {idx + 1}:
A: [{std_a.standard_code}] {std_a.standard_content}
B: [{std_b.standard_code}] {std_b.standard_content}
"""
        
        prompt = f"""
다음 성취기준 쌍들의 유사도를 분석하세요. 각 쌍에 대해 0.0~1.0 점수를 부여하고 유사성의 근거를 제시하세요.

{pairs_text}

분석 기준:
1. 수학적 개념의 유사성
2. 요구되는 인지 능력의 유사성  
3. 문제 해결 방법의 유사성
4. 학습 목표의 연관성

각 쌍에 대해 다음 JSON 형식으로 응답하세요:
{{
  "pair_1": {{
    "similarity_score": 0.0-1.0,
    "reasoning": "유사성 판단 근거",
    "common_concepts": ["공통 개념1", "공통 개념2"],
    "difference_aspects": ["차이점1", "차이점2"]
  }},
  ...
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            batch_results = json.loads(json_str)
            
            # Convert to relationship format
            relations = []
            for idx, (std_a, std_b) in enumerate(standard_pairs):
                pair_key = f"pair_{idx + 1}"
                if pair_key in batch_results:
                    result = batch_results[pair_key]
                    relations.append({
                        'source_code': std_a.standard_code,
                        'target_code': std_b.standard_code,
                        'relation_type': 'similar_to',
                        'similarity_score': result.get('similarity_score', 0.0),
                        'reasoning': result.get('reasoning', ''),
                        'common_concepts': result.get('common_concepts', []),
                        'difference_aspects': result.get('difference_aspects', [])
                    })
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse similarity batch results: {e}")
            return []
    
    async def _extract_prerequisite_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract prerequisite relationships"""
        logger.info("Extracting prerequisite relationships")
        
        standards = curriculum_data['achievement_standards'].sort_values(['level_id', 'domain_id'])
        relations = []
        
        # Group by domain for focused analysis
        for domain_id in standards['domain_id'].unique():
            domain_standards = standards[standards['domain_id'] == domain_id]
            domain_relations = await self._analyze_domain_prerequisites(domain_standards)
            relations.extend(domain_relations)
        
        logger.info(f"Extracted {len(relations)} prerequisite relationships")
        return relations
    
    async def _analyze_domain_prerequisites(self, domain_standards: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze prerequisites within a domain"""
        
        standards_text = ""
        for _, std in domain_standards.iterrows():
            standards_text += f"[{std['standard_code']}] {std['standard_content']}\n"
        
        prompt = f"""
다음 수학 영역 내 성취기준들의 선수학습 관계를 분석하세요:

{standards_text}

분석 기준:
1. 개념적 선후 관계 (기초 개념 → 응용 개념)
2. 절차적 선후 관계 (단순 기능 → 복합 기능)  
3. 학년군별 학습 순서
4. 인지적 복잡도 위계

각 선수학습 관계에 대해 다음 JSON 형식으로 응답하세요:
{{
  "prerequisite_relations": [
    {{
      "prerequisite_code": "선수 성취기준 코드",
      "dependent_code": "후행 성취기준 코드", 
      "strength": 0.0-1.0,
      "reasoning": "관계 설정 근거",
      "relationship_type": "conceptual/procedural/cognitive"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            result = json.loads(json_str)
            relations = []
            
            for relation in result.get('prerequisite_relations', []):
                relations.append({
                    'source_code': relation.get('prerequisite_code'),
                    'target_code': relation.get('dependent_code'),
                    'relation_type': 'prerequisite',
                    'strength': relation.get('strength', 0.8),
                    'reasoning': relation.get('reasoning', ''),
                    'relationship_type': relation.get('relationship_type', 'conceptual')
                })
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse prerequisite results: {e}")
            return []
    
    async def _extract_domain_bridge_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract relationships that bridge different domains"""
        logger.info("Extracting domain bridge relationships")
        
        standards = curriculum_data['achievement_standards']
        relations = []
        
        # Find standards that potentially connect different domains
        domain_groups = standards.groupby('domain_id')
        
        for domain_a, domain_b in itertools.combinations(domain_groups, 2):
            domain_a_id, standards_a = domain_a
            domain_b_id, standards_b = domain_b
            
            bridge_relations = await self._find_domain_bridges(standards_a, standards_b)
            relations.extend(bridge_relations)
        
        logger.info(f"Extracted {len(relations)} domain bridge relationships")
        return relations
    
    async def _find_domain_bridges(self, standards_a: pd.DataFrame, standards_b: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find bridging relationships between two domains"""
        
        domain_a_text = f"영역 A ({standards_a.iloc[0]['domain_name']}):\n"
        for _, std in standards_a.head(10).iterrows():  # Limit for prompt size
            domain_a_text += f"[{std['standard_code']}] {std['standard_content']}\n"
        
        domain_b_text = f"영역 B ({standards_b.iloc[0]['domain_name']}):\n"
        for _, std in standards_b.head(10).iterrows():
            domain_b_text += f"[{std['standard_code']}] {std['standard_content']}\n"
        
        prompt = f"""
두 수학 영역 간의 연결 관계를 분석하세요:

{domain_a_text}

{domain_b_text}

다음 관점에서 영역 간 연결점을 찾으세요:
1. 공통으로 사용되는 수학적 개념
2. 한 영역의 지식이 다른 영역 학습에 필요한 경우
3. 통합적 문제 해결에서 함께 사용되는 경우
4. 실생활 적용에서 융합되는 경우

연결 관계를 다음 JSON 형식으로 응답하세요:
{{
  "bridge_relations": [
    {{
      "source_code": "영역 A의 성취기준 코드",
      "target_code": "영역 B의 성취기준 코드",
      "bridge_type": "conceptual/procedural/application",
      "strength": 0.0-1.0,
      "reasoning": "연결 근거"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            result = json.loads(json_str)
            relations = []
            
            for relation in result.get('bridge_relations', []):
                relations.append({
                    'source_code': relation.get('source_code'),
                    'target_code': relation.get('target_code'),
                    'relation_type': 'domain_bridge',
                    'bridge_type': relation.get('bridge_type', 'conceptual'),
                    'strength': relation.get('strength', 0.5),
                    'reasoning': relation.get('reasoning', '')
                })
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse bridge results: {e}")
            return []
    
    async def _extract_grade_progression_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract relationships showing grade-level progression"""
        logger.info("Extracting grade progression relationships")
        
        standards = curriculum_data['achievement_standards']
        relations = []
        
        # Group by domain and find progressions across grade levels
        for domain_id in standards['domain_id'].unique():
            domain_standards = standards[standards['domain_id'] == domain_id]
            grade_progressions = await self._analyze_grade_progressions(domain_standards)
            relations.extend(grade_progressions)
        
        logger.info(f"Extracted {len(relations)} grade progression relationships")
        return relations
    
    async def _analyze_grade_progressions(self, domain_standards: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze progression patterns across grade levels within a domain"""
        
        # Group by grade level
        grade_groups = domain_standards.groupby('level_id')
        
        progression_text = ""
        for level_id, group in grade_groups:
            level_name = group.iloc[0]['level_name']
            progression_text += f"\n{level_name}:\n"
            for _, std in group.iterrows():
                progression_text += f"  [{std['standard_code']}] {std['standard_content']}\n"
        
        prompt = f"""
다음 수학 영역의 학년군별 진행 과정을 분석하세요:

{progression_text}

분석 기준:
1. 나선형 교육과정 구조 (동일 개념의 심화)
2. 개념의 확장 패턴 (구체적 → 추상적)
3. 기능의 발전 패턴 (단순 → 복합)
4. 적용 범위의 확장 (제한적 → 일반적)

학년군 간 진행 관계를 다음 JSON 형식으로 응답하세요:
{{
  "progression_relations": [
    {{
      "lower_grade_code": "하위 학년 성취기준 코드",
      "higher_grade_code": "상위 학년 성취기준 코드",
      "progression_type": "spiral/extension/application",
      "strength": 0.0-1.0,
      "reasoning": "진행 관계 근거"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            result = json.loads(json_str)
            relations = []
            
            for relation in result.get('progression_relations', []):
                relations.append({
                    'source_code': relation.get('lower_grade_code'),
                    'target_code': relation.get('higher_grade_code'),
                    'relation_type': 'grade_progression',
                    'progression_type': relation.get('progression_type', 'spiral'),
                    'strength': relation.get('strength', 0.7),
                    'reasoning': relation.get('reasoning', '')
                })
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse progression results: {e}")
            return []
    
    async def _calculate_initial_weights(self, *relation_lists) -> List[Dict[str, Any]]:
        """Calculate initial weights for all relationships"""
        logger.info("Calculating initial relationship weights")
        
        all_relations = []
        for relations in relation_lists:
            all_relations.extend(relations)
        
        # Apply base weights by relation type
        base_weights = {
            'similar_to': 0.6,
            'prerequisite': 1.0,
            'domain_bridge': 0.4,
            'grade_progression': 0.8
        }
        
        weighted_relations = []
        for relation in all_relations:
            if not relation.get('source_code') or not relation.get('target_code'):
                continue
                
            relation_type = relation.get('relation_type', 'unknown')
            base_weight = base_weights.get(relation_type, 0.5)
            
            # Adjust weight based on specific strength if available
            specific_strength = relation.get('strength', relation.get('similarity_score', 1.0))
            final_weight = base_weight * specific_strength
            
            weighted_relation = {
                'source_code': relation['source_code'],
                'target_code': relation['target_code'],
                'relation_type': relation_type,
                'weight': round(final_weight, 3),
                'base_weight': base_weight,
                'specific_strength': specific_strength,
                'reasoning': relation.get('reasoning', ''),
                'metadata': {k: v for k, v in relation.items() 
                           if k not in ['source_code', 'target_code', 'relation_type', 'reasoning']}
            }
            
            weighted_relations.append(weighted_relation)
        
        logger.info(f"Calculated weights for {len(weighted_relations)} relationships")
        return weighted_relations

# Main execution function for Phase 2
async def run_phase2(curriculum_data: Dict[str, Any], foundation_design: Dict[str, Any]) -> Dict[str, Any]:
    """Run Phase 2: Relationship Extraction"""
    logger.info("=== Phase 2: Relationship Extraction ===")
    
    ai_manager = AIModelManager()
    extractor = RelationshipExtractor(ai_manager)
    
    try:
        relationship_extraction = await extractor.extract_all_relationships(curriculum_data, foundation_design)
        
        # Save results
        output_path = "output/phase2_relationship_extraction.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relationship_extraction, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Phase 2 completed. Results saved to {output_path}")
        
        # Log usage stats
        stats = ai_manager.get_total_usage_stats()
        logger.info(f"Phase 2 Usage Stats: {stats}")
        
        return relationship_extraction
        
    except Exception as e:
        logger.error(f"Phase 2 failed: {e}")
        raise

if __name__ == "__main__":
    # Test run
    async def test_phase2():
        from src.data_manager import DatabaseManager
        from src.phase1_foundation import run_phase1
        
        db_manager = DatabaseManager()
        curriculum_data = db_manager.extract_all_curriculum_data()
        foundation_design = await run_phase1(curriculum_data)
        result = await run_phase2(curriculum_data, foundation_design)
        print("Phase 2 test completed")
    
    asyncio.run(test_phase2())
