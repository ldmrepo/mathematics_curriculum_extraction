"""
Phase 3: Advanced Refinement using Claude Sonnet 4
"""
import asyncio
import json
from typing import Dict, List, Any, Tuple
from loguru import logger
from src.ai_models import AIModelManager

class RelationshipRefiner:
    """Refines and enhances relationships using Claude Sonnet 4"""
    
    def __init__(self, ai_manager: AIModelManager):
        self.ai_manager = ai_manager
        self.model_name = 'claude_sonnet'  # Using Claude Sonnet 4 for nuanced refinement
    
    async def refine_all_relationships(self, relationship_data: Dict[str, Any], foundation_design: Dict[str, Any]) -> Dict[str, Any]:
        """Refine all extracted relationships with educational context"""
        logger.info("Starting relationship refinement with Claude Sonnet 4")
        
        # Get weighted relations from Phase 2
        weighted_relations = relationship_data.get('weighted_relations', [])
        
        # Refine relationship types
        refined_types = await self._refine_relationship_types(weighted_relations)
        
        # Adjust weights based on educational context
        adjusted_weights = await self._adjust_relationship_weights(refined_types)
        
        # Add educational metadata
        enriched_relations = await self._add_educational_metadata(adjusted_weights)
        
        # Identify missing critical relationships
        missing_relations = await self._identify_missing_relationships(enriched_relations, foundation_design)
        
        # Resolve conflicts and redundancies
        cleaned_relations = await self._resolve_conflicts(enriched_relations + missing_relations)
        
        refinement_results = {
            'refined_types': refined_types,
            'adjusted_weights': adjusted_weights,
            'enriched_relations': enriched_relations,
            'missing_relations': missing_relations,
            'final_relations': cleaned_relations,
            'metadata': {
                'refinement_timestamp': asyncio.get_event_loop().time(),
                'total_relations_refined': len(cleaned_relations),
                'new_relations_added': len(missing_relations),
                'conflicts_resolved': len(enriched_relations) - len(cleaned_relations)
            }
        }
        
        logger.info("Relationship refinement completed")
        return refinement_results
    
    async def _refine_relationship_types(self, relations: List[Dict]) -> List[Dict]:
        """Refine relationship types to be more specific"""
        logger.info("Refining relationship types")
        
        refined_relations = []
        batch_size = 30
        
        for i in range(0, len(relations), batch_size):
            batch = relations[i:i+batch_size]
            refined_batch = await self._process_type_refinement_batch(batch)
            refined_relations.extend(refined_batch)
            
            logger.info(f"Refined types for batch {i//batch_size + 1}/{(len(relations)-1)//batch_size + 1}")
        
        return refined_relations
    
    async def _process_type_refinement_batch(self, relations: List[Dict]) -> List[Dict]:
        """Process a batch of relations for type refinement"""
        
        relations_text = json.dumps(relations, ensure_ascii=False, indent=2)
        
        prompt = f"""
한국 수학 교육과정의 성취기준 간 관계를 더 세밀하게 분류하세요.

현재 관계들:
{relations_text[:3000]}...

각 관계에 대해 다음과 같이 세분화하세요:

1. prerequisite → 
   - prerequisite_conceptual: 개념적 선수학습
   - prerequisite_procedural: 절차적 선수학습
   - prerequisite_cognitive: 인지적 선수학습

2. similar_to →
   - similar_content: 내용 유사
   - similar_method: 방법 유사
   - similar_application: 적용 유사

3. domain_bridge →
   - bridge_conceptual: 개념적 연결
   - bridge_practical: 실용적 연결
   - bridge_methodological: 방법론적 연결

4. grade_progression →
   - progression_spiral: 나선형 심화
   - progression_extension: 확장
   - progression_integration: 통합

각 관계에 대해 교육학적 근거를 포함하여 JSON 형식으로 응답하세요:
{{
  "refined_relations": [
    {{
      "source_code": "원본 코드",
      "target_code": "대상 코드",
      "original_type": "원래 타입",
      "refined_type": "세분화된 타입",
      "educational_rationale": "교육학적 근거",
      "cognitive_demand": "low/medium/high",
      "learning_sequence_priority": 1-10
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name, 
            prompt,
            thinking_budget=3000  # Extended thinking for nuanced analysis
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            result = json.loads(json_str)
            refined = result.get('refined_relations', [])
            
            # Merge with original data
            refined_relations = []
            for rel in relations:
                # Find corresponding refined version
                refined_version = next(
                    (r for r in refined if r['source_code'] == rel.get('source_code') 
                     and r['target_code'] == rel.get('target_code')),
                    None
                )
                
                if refined_version:
                    rel.update(refined_version)
                
                refined_relations.append(rel)
            
            return refined_relations
            
        except Exception as e:
            logger.error(f"Failed to parse refinement results: {e}")
            return relations
    
    async def _adjust_relationship_weights(self, relations: List[Dict]) -> List[Dict]:
        """Adjust relationship weights based on educational importance"""
        logger.info("Adjusting relationship weights")
        
        # Group relations by type for weight adjustment
        type_groups = {}
        for rel in relations:
            rel_type = rel.get('refined_type', rel.get('relation_type'))
            if rel_type not in type_groups:
                type_groups[rel_type] = []
            type_groups[rel_type].append(rel)
        
        adjusted_relations = []
        
        for rel_type, group in type_groups.items():
            adjusted_group = await self._adjust_group_weights(rel_type, group)
            adjusted_relations.extend(adjusted_group)
        
        return adjusted_relations
    
    async def _adjust_group_weights(self, rel_type: str, relations: List[Dict]) -> List[Dict]:
        """Adjust weights for a group of similar relations"""
        
        if not relations:
            return []
        
        sample_relations = relations[:10]  # Sample for prompt
        
        prompt = f"""
다음 '{rel_type}' 타입 관계들의 가중치를 교육적 중요도에 따라 조정하세요.

샘플 관계들:
{json.dumps(sample_relations, ensure_ascii=False, indent=2)}

가중치 조정 기준:
1. 학습 필수도 (0.8-1.0: 필수, 0.5-0.8: 권장, 0.2-0.5: 선택)
2. 인지적 거리 (가까울수록 높은 가중치)
3. 교육과정 명시도 (명시적일수록 높은 가중치)
4. 평가 빈도 (자주 평가될수록 높은 가중치)

각 관계에 대해 조정된 가중치와 근거를 제시하세요:
{{
  "weight_adjustments": [
    {{
      "source_code": "코드",
      "target_code": "코드",
      "original_weight": 0.0-1.0,
      "adjusted_weight": 0.0-1.0,
      "adjustment_reason": "조정 이유",
      "educational_importance": "critical/high/medium/low"
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
            adjustments = result.get('weight_adjustments', [])
            
            # Apply adjustments
            adjustment_map = {
                (adj['source_code'], adj['target_code']): adj 
                for adj in adjustments
            }
            
            for rel in relations:
                key = (rel.get('source_code'), rel.get('target_code'))
                if key in adjustment_map:
                    adj = adjustment_map[key]
                    rel['original_weight'] = rel.get('weight', 0.5)
                    rel['adjusted_weight'] = adj.get('adjusted_weight', rel['weight'])
                    rel['weight'] = rel['adjusted_weight']
                    rel['adjustment_reason'] = adj.get('adjustment_reason', '')
                    rel['educational_importance'] = adj.get('educational_importance', 'medium')
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse weight adjustments: {e}")
            return relations
    
    async def _add_educational_metadata(self, relations: List[Dict]) -> List[Dict]:
        """Add educational metadata to relationships"""
        logger.info("Adding educational metadata")
        
        enriched_relations = []
        batch_size = 20
        
        for i in range(0, len(relations), batch_size):
            batch = relations[i:i+batch_size]
            enriched_batch = await self._enrich_batch_with_metadata(batch)
            enriched_relations.extend(enriched_batch)
        
        return enriched_relations
    
    async def _enrich_batch_with_metadata(self, relations: List[Dict]) -> List[Dict]:
        """Enrich a batch of relations with educational metadata"""
        
        prompt = f"""
다음 수학 교육과정 관계들에 교육적 메타데이터를 추가하세요.

관계들:
{json.dumps(relations[:5], ensure_ascii=False, indent=2)}

각 관계에 대해 다음 메타데이터를 추가하세요:
1. 학습 난이도 전이 (difficulty_transition): easy→easy, easy→medium, medium→hard 등
2. 개념 범주 (concept_category): 수 개념, 연산, 도형, 측정, 통계, 확률 등
3. 인지 수준 (cognitive_level): 기억, 이해, 적용, 분석, 평가, 창조
4. 교수 전략 (teaching_strategy): 직접교수, 탐구학습, 협동학습, 문제기반학습 등
5. 평가 방법 (assessment_method): 지필평가, 수행평가, 관찰평가, 포트폴리오 등

JSON 형식으로 응답하세요:
{{
  "enriched_relations": [
    {{
      "source_code": "코드",
      "target_code": "코드",
      "difficulty_transition": "전이 유형",
      "concept_category": "개념 범주",
      "cognitive_level": "인지 수준",
      "teaching_strategy": "추천 교수 전략",
      "assessment_method": "적합한 평가 방법",
      "learning_time_hours": 예상 학습 시간
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
            enrichments = result.get('enriched_relations', [])
            
            # Merge enrichments with original relations
            enrichment_map = {
                (e['source_code'], e['target_code']): e 
                for e in enrichments
            }
            
            for rel in relations:
                key = (rel.get('source_code'), rel.get('target_code'))
                if key in enrichment_map:
                    enrichment = enrichment_map[key]
                    rel['educational_metadata'] = {
                        'difficulty_transition': enrichment.get('difficulty_transition'),
                        'concept_category': enrichment.get('concept_category'),
                        'cognitive_level': enrichment.get('cognitive_level'),
                        'teaching_strategy': enrichment.get('teaching_strategy'),
                        'assessment_method': enrichment.get('assessment_method'),
                        'learning_time_hours': enrichment.get('learning_time_hours', 2)
                    }
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to parse enrichments: {e}")
            return relations
    
    async def _identify_missing_relationships(self, existing_relations: List[Dict], foundation_design: Dict) -> List[Dict]:
        """Identify critical missing relationships"""
        logger.info("Identifying missing critical relationships")
        
        # Extract existing relation pairs
        existing_pairs = set()
        for rel in existing_relations:
            pair = (rel.get('source_code'), rel.get('target_code'))
            if pair[0] and pair[1]:
                existing_pairs.add(pair)
        
        prompt = f"""
한국 수학 교육과정의 구조를 고려하여, 현재 누락된 중요한 관계를 식별하세요.

현재 관계 수: {len(existing_pairs)}개
주요 관계 타입: prerequisite, similar_to, domain_bridge, grade_progression

교육과정 구조:
- 초등 1-2학년군: 기초 수 개념, 간단한 연산
- 초등 3-4학년군: 곱셈/나눗셈, 분수, 도형
- 초등 5-6학년군: 소수, 비와 비율, 입체도형
- 중학교: 대수, 함수, 기하, 확률통계

누락되었을 가능성이 높은 중요 관계들을 제안하세요:
1. 학년 간 핵심 개념 연결 (예: 초2 덧셈 → 초3 곱셈)
2. 영역 간 통합 관계 (예: 수와 연산 + 도형과 측정)
3. 나선형 교육과정 관계 (동일 개념의 학년별 심화)

JSON 형식으로 10-20개의 중요 누락 관계를 제안하세요:
{{
  "missing_relations": [
    {{
      "source_code": "성취기준 코드 (예: 2수01-01)",
      "target_code": "성취기준 코드",
      "relation_type": "관계 타입",
      "importance": "critical/high/medium",
      "rationale": "관계가 중요한 이유"
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
            missing = result.get('missing_relations', [])
            
            # Filter out already existing relations
            new_relations = []
            for rel in missing:
                pair = (rel.get('source_code'), rel.get('target_code'))
                if pair not in existing_pairs and pair[0] and pair[1]:
                    rel['is_inferred'] = True
                    rel['weight'] = 0.7 if rel.get('importance') == 'critical' else 0.5
                    new_relations.append(rel)
            
            logger.info(f"Identified {len(new_relations)} missing critical relationships")
            return new_relations
            
        except Exception as e:
            logger.error(f"Failed to identify missing relationships: {e}")
            return []
    
    async def _resolve_conflicts(self, relations: List[Dict]) -> List[Dict]:
        """Resolve conflicts and remove redundancies"""
        logger.info("Resolving conflicts and removing redundancies")
        
        # Group by source-target pair
        relation_groups = {}
        for rel in relations:
            key = (rel.get('source_code'), rel.get('target_code'))
            if key not in relation_groups:
                relation_groups[key] = []
            relation_groups[key].append(rel)
        
        # Resolve conflicts for each pair
        cleaned_relations = []
        for key, group in relation_groups.items():
            if len(group) == 1:
                cleaned_relations.append(group[0])
            else:
                # Multiple relations for same pair - merge them
                merged = await self._merge_duplicate_relations(group)
                cleaned_relations.append(merged)
        
        logger.info(f"Resolved {len(relations) - len(cleaned_relations)} conflicts/duplicates")
        return cleaned_relations
    
    async def _merge_duplicate_relations(self, relations: List[Dict]) -> Dict:
        """Merge duplicate relations into one"""
        
        # Take the relation with highest weight/confidence
        best_rel = max(relations, key=lambda r: r.get('weight', 0) * r.get('confidence', 1))
        
        # Merge metadata from all relations
        merged_metadata = {}
        for rel in relations:
            if 'educational_metadata' in rel:
                merged_metadata.update(rel['educational_metadata'])
        
        if merged_metadata:
            best_rel['educational_metadata'] = merged_metadata
        
        # Collect all relation types
        all_types = list(set(rel.get('refined_type', rel.get('relation_type')) for rel in relations))
        if len(all_types) > 1:
            best_rel['alternative_types'] = all_types
        
        return best_rel

# Main execution function for Phase 3
async def run_phase3(relationship_data: Dict[str, Any], foundation_design: Dict[str, Any]) -> Dict[str, Any]:
    """Run Phase 3: Advanced Refinement"""
    logger.info("=== Phase 3: Advanced Refinement ===")
    
    ai_manager = AIModelManager()
    refiner = RelationshipRefiner(ai_manager)
    
    try:
        refinement_results = await refiner.refine_all_relationships(relationship_data, foundation_design)
        
        # Save results
        output_path = "output/phase3_refinement_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(refinement_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Phase 3 completed. Results saved to {output_path}")
        
        # Log usage stats
        stats = ai_manager.get_total_usage_stats()
        logger.info(f"Phase 3 Usage Stats: {stats}")
        
        return refinement_results
        
    except Exception as e:
        logger.error(f"Phase 3 failed: {e}")
        raise

if __name__ == "__main__":
    # Test run
    import asyncio
    
    async def test_phase3():
        # Load test data
        with open('output/phase2_relationship_extraction.json', 'r', encoding='utf-8') as f:
            relationship_data = json.load(f)
        
        with open('output/phase1_foundation_design.json', 'r', encoding='utf-8') as f:
            foundation_design = json.load(f)
        
        result = await run_phase3(relationship_data, foundation_design)
        print("Phase 3 test completed")
    
    # Run test if sample data exists
    import os
    if os.path.exists('output/phase2_relationship_extraction.json'):
        asyncio.run(test_phase3())
    else:
        print("Please run Phase 1 and 2 first to generate test data")
