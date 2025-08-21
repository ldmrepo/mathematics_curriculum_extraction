"""
Phase 3: Advanced Refinement using Claude Sonnet 4
"""
import asyncio
import json
from typing import Dict, List, Any
from loguru import logger
from src.ai_models import AIModelManager

class RelationshipRefiner:
    """Refines relationships using Claude Sonnet 4's hybrid reasoning"""
    
    def __init__(self, ai_manager: AIModelManager):
        self.ai_manager = ai_manager
        self.model_name = 'claude_sonnet'  # Using Claude Sonnet 4 for hybrid reasoning
    
    async def refine_all_relationships(self, relationship_data: Dict[str, Any], foundation_design: Dict[str, Any]) -> Dict[str, Any]:
        """Refine and enhance all extracted relationships"""
        logger.info("Starting relationship refinement with Claude Sonnet 4")
        
        # Refine edge types and subcategorization
        refined_edge_types = await self._refine_edge_types(relationship_data, foundation_design)
        
        # Adjust weights with educational context
        adjusted_weights = await self._adjust_weights_with_context(relationship_data, refined_edge_types)
        
        # Identify complex learning pathways
        learning_pathways = await self._identify_learning_pathways(adjusted_weights)
        
        # Detect and resolve conflicts
        conflict_resolution = await self._resolve_relationship_conflicts(adjusted_weights)
        
        # Create hierarchical relationship structure
        hierarchical_structure = await self._create_hierarchical_structure(adjusted_weights, foundation_design)
        
        refinement_results = {
            'refined_edge_types': refined_edge_types,
            'adjusted_weights': adjusted_weights,
            'learning_pathways': learning_pathways,
            'conflict_resolution': conflict_resolution,
            'hierarchical_structure': hierarchical_structure,
            'metadata': {
                'refinement_timestamp': asyncio.get_event_loop().time(),
                'total_refined_relations': len(adjusted_weights),
                'edge_types_refined': len(refined_edge_types)
            }
        }
        
        logger.info("Relationship refinement completed")
        return refinement_results
    
    async def _refine_edge_types(self, relationship_data: Dict, foundation_design: Dict) -> Dict[str, Any]:
        """Refine edge types with educational granularity"""
        logger.info("Refining edge types with educational context")
        
        # Extract current relationships for analysis
        current_relations = relationship_data.get('weighted_relations', [])
        relation_samples = current_relations[:50]  # Sample for analysis
        
        sample_text = ""
        for i, rel in enumerate(relation_samples):
            sample_text += f"""
관계 {i+1}:
- 유형: {rel.get('relation_type', 'unknown')}
- 출발: {rel.get('source_code', '')}
- 도착: {rel.get('target_code', '')}
- 가중치: {rel.get('weight', 0.0)}
- 근거: {rel.get('reasoning', '')[:100]}...
"""
        
        prompt = f"""
현재 추출된 관계들을 분석하여 교육적 의미를 고려한 세분화된 엣지 타입 체계를 설계하세요.

현재 관계 샘플:
{sample_text}

기존 기본 관계 유형:
- similar_to (유사 관계)
- prerequisite (선수학습 관계)  
- domain_bridge (영역 간 연결)
- grade_progression (학년 진행)

세분화 기준:
1. 교육과정 명시성 (명시적/암시적)
2. 학습 필수성 (필수/권장/참고)
3. 인지적 관계 (개념적/절차적/메타인지적)
4. 시간적 순서 (선행/동시/후행)
5. 적용 범위 (도메인 내/도메인 간/전이)

각 기본 유형을 3-4개의 세부 유형으로 확장하고, 다음을 정의하세요:
- 세부 유형명과 설명
- 가중치 조정 계수 (0.5~1.5)
- 탐지 기준
- 교육적 의미

사고 과정을 보여주고, JSON 형식으로 최종 결과를 제시하세요.
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name, 
            prompt, 
            thinking_budget=3000  # Extended thinking for complex analysis
        )
        
        try:
            content = response['content']
            # Extract JSON from response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            refined_edge_types = json.loads(json_str)
            logger.info("Edge types refined successfully")
            return refined_edge_types
            
        except Exception as e:
            logger.error(f"Failed to parse refined edge types: {e}")
            return self._get_fallback_refined_edge_types()
    
    async def _adjust_weights_with_context(self, relationship_data: Dict, refined_edge_types: Dict) -> List[Dict[str, Any]]:
        """Adjust relationship weights considering educational context"""
        logger.info("Adjusting weights with educational context")
        
        current_relations = relationship_data.get('weighted_relations', [])
        adjusted_relations = []
        
        # Process relationships in batches to maintain context
        batch_size = 30
        for i in range(0, len(current_relations), batch_size):
            batch = current_relations[i:i+batch_size]
            batch_adjusted = await self._adjust_batch_weights(batch, refined_edge_types)
            adjusted_relations.extend(batch_adjusted)
            
            logger.info(f"Adjusted weights for batch {i//batch_size + 1}/{(len(current_relations)-1)//batch_size + 1}")
        
        return adjusted_relations
    
    async def _adjust_batch_weights(self, relations_batch: List[Dict], refined_edge_types: Dict) -> List[Dict[str, Any]]:
        """Adjust weights for a batch of relationships"""
        
        batch_text = ""
        for i, rel in enumerate(relations_batch):
            batch_text += f"""
관계 {i+1}:
- 출발: {rel.get('source_code', '')}
- 도착: {rel.get('target_code', '')}
- 현재 유형: {rel.get('relation_type', '')}
- 현재 가중치: {rel.get('weight', 0.0)}
- 근거: {rel.get('reasoning', '')}
"""
        
        refined_types_text = json.dumps(refined_edge_types, ensure_ascii=False, indent=2)
        
        prompt = f"""
다음 관계들의 유형을 세분화하고 가중치를 교육적 맥락에 맞게 조정하세요.

관계 목록:
{batch_text}

세분화된 엣지 타입 체계:
{refined_types_text}

조정 기준:
1. 교육과정에서의 중요도
2. 학습 효과에 미치는 영향
3. 인지적 부하 고려
4. 실제 교수학습에서의 활용도
5. 평가에서의 중요성

각 관계에 대해 다음을 결정하세요:
- 새로운 세분화된 유형
- 조정된 가중치 (0.0~1.0)
- 조정 근거
- 교육적 권장사항

JSON 형식으로 응답하세요:
{{
  "adjusted_relations": [
    {{
      "relation_id": 1,
      "refined_type": "세분화된 유형명",
      "adjusted_weight": 0.0-1.0,
      "adjustment_reasoning": "조정 근거",
      "educational_significance": "교육적 의미"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=2000
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            result = json.loads(json_str)
            adjusted_batch = []
            
            for i, adjustment in enumerate(result.get('adjusted_relations', [])):
                if i < len(relations_batch):
                    original_rel = relations_batch[i]
                    adjusted_rel = original_rel.copy()
                    adjusted_rel.update({
                        'refined_type': adjustment.get('refined_type', original_rel.get('relation_type')),
                        'adjusted_weight': adjustment.get('adjusted_weight', original_rel.get('weight')),
                        'adjustment_reasoning': adjustment.get('adjustment_reasoning', ''),
                        'educational_significance': adjustment.get('educational_significance', '')
                    })
                    adjusted_batch.append(adjusted_rel)
            
            return adjusted_batch
            
        except Exception as e:
            logger.error(f"Failed to adjust batch weights: {e}")
            return relations_batch  # Return original if parsing fails
    
    async def _identify_learning_pathways(self, adjusted_relations: List[Dict]) -> Dict[str, Any]:
        """Identify complex learning pathways and sequences"""
        logger.info("Identifying learning pathways")
        
        # Extract prerequisite chains
        prerequisite_relations = [r for r in adjusted_relations 
                                if 'prerequisite' in r.get('refined_type', r.get('relation_type', ''))]
        
        # Sample for analysis
        pathway_sample = prerequisite_relations[:100]
        
        pathway_text = ""
        for rel in pathway_sample:
            pathway_text += f"{rel.get('source_code', '')} → {rel.get('target_code', '')} (가중치: {rel.get('adjusted_weight', rel.get('weight', 0.0))})\n"
        
        prompt = f"""
다음 선수학습 관계들을 분석하여 학습 경로와 시퀀스를 식별하세요.

선수학습 관계:
{pathway_text}

분석 과제:
1. 핵심 학습 경로 식별 (5-7개)
2. 각 경로의 단계별 구성
3. 경로 간 교차점과 분기점
4. 필수 경로 vs 선택적 경로 구분
5. 학습 효율성 관점에서의 최적 순서

교육과정 특성을 고려하여 분석하세요:
- 나선형 교육과정 구조
- 학년군별 인지 발달 수준
- 영역 간 통합적 학습
- 개별 학습자 차이

JSON 형식으로 학습 경로를 제시하세요:
{{
  "learning_pathways": [
    {{
      "pathway_id": "pathway_1",
      "pathway_name": "경로명",
      "description": "경로 설명",
      "pathway_type": "essential/recommended/optional",
      "steps": [
        {{
          "step_order": 1,
          "achievement_code": "성취기준 코드",
          "step_description": "단계 설명",
          "estimated_duration": "예상 학습 시간"
        }}
      ],
      "learning_outcomes": "예상 학습 성과",
      "teaching_recommendations": "교수학습 권장사항"
    }}
  ],
  "pathway_intersections": [
    {{
      "intersection_point": "교차점 성취기준",
      "connecting_pathways": ["연결되는 경로들"],
      "educational_significance": "교육적 의미"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=4000
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            learning_pathways = json.loads(json_str)
            logger.info("Learning pathways identified successfully")
            return learning_pathways
            
        except Exception as e:
            logger.error(f"Failed to parse learning pathways: {e}")
            return self._get_fallback_learning_pathways()
    
    async def _resolve_relationship_conflicts(self, adjusted_relations: List[Dict]) -> Dict[str, Any]:
        """Detect and resolve conflicts in relationships"""
        logger.info("Resolving relationship conflicts")
        
        # Identify potential conflicts
        conflicts = self._detect_conflicts(adjusted_relations)
        
        if not conflicts:
            return {'conflicts_detected': 0, 'resolutions': []}
        
        conflicts_text = ""
        for i, conflict in enumerate(conflicts[:20]):  # Limit for prompt size
            conflicts_text += f"""
충돌 {i+1}:
- 유형: {conflict['conflict_type']}
- 관련 관계: {conflict['relations']}
- 설명: {conflict['description']}
"""
        
        prompt = f"""
다음 관계 충돌들을 분석하고 해결 방안을 제시하세요.

발견된 충돌:
{conflicts_text}

해결 원칙:
1. 교육과정 문서의 명시적 내용 우선
2. 학습자 인지 발달 수준 고려
3. 실제 교수학습 경험 반영
4. 평가 및 측정 가능성 고려
5. 전체 교육과정의 일관성 유지

각 충돌에 대해 다음을 제시하세요:
- 충돌 원인 분석
- 해결 방안 (관계 수정/삭제/가중치 조정)
- 해결 근거
- 대안적 해석 가능성

JSON 형식으로 응답하세요:
{{
  "conflict_resolutions": [
    {{
      "conflict_id": 1,
      "resolution_type": "modify/remove/adjust_weight",
      "resolution_action": "구체적 해결 행동",
      "reasoning": "해결 근거",
      "impact_assessment": "해결이 미치는 영향"
    }}
  ]
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=3000
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            conflict_resolution = json.loads(json_str)
            conflict_resolution['conflicts_detected'] = len(conflicts)
            
            logger.info(f"Resolved {len(conflicts)} relationship conflicts")
            return conflict_resolution
            
        except Exception as e:
            logger.error(f"Failed to parse conflict resolution: {e}")
            return {'conflicts_detected': len(conflicts), 'resolutions': []}
    
    def _detect_conflicts(self, relations: List[Dict]) -> List[Dict[str, Any]]:
        """Detect various types of conflicts in relationships"""
        conflicts = []
        
        # Create lookup for efficient searching
        relation_map = {}
        for rel in relations:
            source = rel.get('source_code', '')
            target = rel.get('target_code', '')
            if source and target:
                key = f"{source}->{target}"
                if key not in relation_map:
                    relation_map[key] = []
                relation_map[key].append(rel)
        
        # Detect duplicate relationships with different types
        for key, rels in relation_map.items():
            if len(rels) > 1:
                types = [r.get('refined_type', r.get('relation_type', '')) for r in rels]
                if len(set(types)) > 1:
                    conflicts.append({
                        'conflict_type': 'duplicate_with_different_types',
                        'relations': key,
                        'description': f"Same relationship with different types: {types}"
                    })
        
        # Detect circular dependencies in prerequisites
        prerequisite_map = {}
        for rel in relations:
            if 'prerequisite' in rel.get('refined_type', rel.get('relation_type', '')):
                source = rel.get('source_code', '')
                target = rel.get('target_code', '')
                if source and target:
                    if target not in prerequisite_map:
                        prerequisite_map[target] = []
                    prerequisite_map[target].append(source)
        
        # Simple cycle detection
        for node, prerequisites in prerequisite_map.items():
            for prereq in prerequisites:
                if prereq in prerequisite_map and node in prerequisite_map[prereq]:
                    conflicts.append({
                        'conflict_type': 'circular_prerequisite',
                        'relations': f"{node} <-> {prereq}",
                        'description': "Circular prerequisite dependency detected"
                    })
        
        return conflicts
    
    async def _create_hierarchical_structure(self, adjusted_relations: List[Dict], foundation_design: Dict) -> Dict[str, Any]:
        """Create hierarchical relationship structure"""
        logger.info("Creating hierarchical relationship structure")
        
        # Group relations by type
        relations_by_type = {}
        for rel in adjusted_relations:
            rel_type = rel.get('refined_type', rel.get('relation_type', 'unknown'))
            if rel_type not in relations_by_type:
                relations_by_type[rel_type] = []
            relations_by_type[rel_type].append(rel)
        
        type_summary = ""
        for rel_type, rels in relations_by_type.items():
            count = len(rels)
            avg_weight = sum(r.get('adjusted_weight', r.get('weight', 0.0)) for r in rels) / count if count > 0 else 0
            type_summary += f"- {rel_type}: {count}개 관계, 평균 가중치: {avg_weight:.3f}\n"
        
        hierarchy_info = foundation_design.get('hierarchical_structure', {})
        
        prompt = f"""
다음 관계 정보를 바탕으로 계층적 관계 구조를 설계하세요.

관계 유형별 현황:
{type_summary}

기본 계층 구조:
{json.dumps(hierarchy_info, ensure_ascii=False, indent=2)}

설계 요구사항:
1. 5단계 계층 구조 구성
   - Level 1: 교육과정 전체
   - Level 2: 학년군
   - Level 3: 영역
   - Level 4: 성취기준
   - Level 5: 성취수준

2. 각 계층 내/간 관계 규칙 정의
3. 계층 간 탐색 최적화 전략
4. 교육적 의미를 반영한 가중치 시스템
5. 동적 구조 변경 지원 방안

JSON 형식으로 응답하세요:
{{
  "hierarchical_structure": {{
    "levels": {{
      "level_1": {{
        "name": "교육과정",
        "node_count": 1,
        "internal_relations": [],
        "external_relations": ["contains"]
      }}
    }},
    "traversal_rules": {{
      "upward_navigation": "하위에서 상위로의 탐색 규칙",
      "downward_navigation": "상위에서 하위로의 탐색 규칙",
      "cross_level_connections": "계층 간 연결 규칙"
    }},
    "optimization_strategies": [
      "성능 최적화 전략들"
    ]
  }}
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=2500
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            hierarchical_structure = json.loads(json_str)
            logger.info("Hierarchical structure created successfully")
            return hierarchical_structure
            
        except Exception as e:
            logger.error(f"Failed to parse hierarchical structure: {e}")
            return self._get_fallback_hierarchical_structure()
    
    def _get_fallback_refined_edge_types(self) -> Dict[str, Any]:
        """Fallback refined edge types"""
        return {
            "edge_types": {
                "prerequisite_explicit": {"weight_multiplier": 1.0, "description": "명시적 선수학습"},
                "prerequisite_implicit": {"weight_multiplier": 0.8, "description": "암시적 선수학습"},
                "similar_conceptual": {"weight_multiplier": 0.7, "description": "개념적 유사성"},
                "similar_procedural": {"weight_multiplier": 0.6, "description": "절차적 유사성"}
            }
        }
    
    def _get_fallback_learning_pathways(self) -> Dict[str, Any]:
        """Fallback learning pathways"""
        return {
            "learning_pathways": [
                {
                    "pathway_id": "basic_number",
                    "pathway_name": "기본 수 개념 경로",
                    "pathway_type": "essential",
                    "steps": []
                }
            ],
            "pathway_intersections": []
        }
    
    def _get_fallback_hierarchical_structure(self) -> Dict[str, Any]:
        """Fallback hierarchical structure"""
        return {
            "hierarchical_structure": {
                "levels": {
                    "level_1": {"name": "교육과정", "node_count": 1},
                    "level_2": {"name": "학년군", "node_count": 4},
                    "level_3": {"name": "영역", "node_count": 4},
                    "level_4": {"name": "성취기준", "node_count": 181},
                    "level_5": {"name": "성취수준", "node_count": 843}
                }
            }
        }

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
    async def test_phase3():
        # Load previous phase results
        with open("output/phase1_foundation_design.json", 'r', encoding='utf-8') as f:
            foundation_design = json.load(f)
        
        with open("output/phase2_relationship_extraction.json", 'r', encoding='utf-8') as f:
            relationship_data = json.load(f)
        
        result = await run_phase3(relationship_data, foundation_design)
        print("Phase 3 test completed")
    
    asyncio.run(test_phase3())
