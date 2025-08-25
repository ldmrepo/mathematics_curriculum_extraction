"""
Phase 2: Relationship Extraction using GPT-5 with batch processing
Stabilized version using database views for suggestions
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
        
        # Use database suggestions as starting point
        prerequisite_suggestions = curriculum_data.get('prerequisite_suggestions', pd.DataFrame())
        horizontal_suggestions = curriculum_data.get('horizontal_suggestions', pd.DataFrame())
        
        logger.info(f"Found {len(prerequisite_suggestions)} prerequisite suggestions from DB")
        logger.info(f"Found {len(horizontal_suggestions)} horizontal suggestions from DB")
        
        # Convert DB suggestions to relationship format
        prerequisite_relations = await self._process_prerequisite_suggestions(
            prerequisite_suggestions, curriculum_data
        )
        horizontal_relations = await self._process_horizontal_suggestions(
            horizontal_suggestions, curriculum_data
        )
        
        # Extract additional relationship types
        similarity_relations = await self._extract_similarity_relationships(curriculum_data)
        domain_bridge_relations = await self._extract_domain_bridge_relationships(curriculum_data)
        grade_progression_relations = await self._extract_grade_progression_relationships(curriculum_data)
        
        # Calculate initial weights
        weighted_relations = await self._calculate_initial_weights(
            prerequisite_relations,
            horizontal_relations,
            similarity_relations,
            domain_bridge_relations,
            grade_progression_relations
        )
        
        relationship_extraction = {
            'prerequisite_relations': prerequisite_relations,
            'horizontal_relations': horizontal_relations,
            'similarity_relations': similarity_relations,
            'domain_bridge_relations': domain_bridge_relations,
            'grade_progression_relations': grade_progression_relations,
            'weighted_relations': weighted_relations,
            'metadata': {
                'extraction_timestamp': asyncio.get_event_loop().time(),
                'total_relations_extracted': len(weighted_relations),
                'relation_types_count': 5,
                'db_suggestions_used': len(prerequisite_suggestions) + len(horizontal_suggestions)
            }
        }
        
        logger.info("Relationship extraction completed")
        return relationship_extraction
    
    async def _process_prerequisite_suggestions(self, suggestions: pd.DataFrame, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Process prerequisite suggestions from database view"""
        if suggestions.empty:
            logger.info("No prerequisite suggestions from database")
            return []
        
        relations = []
        standards_df = curriculum_data['achievement_standards']
        
        # Create ID to code mapping
        id_to_code = dict(zip(standards_df['standard_id'], standards_df['standard_code']))
        id_to_content = dict(zip(standards_df['standard_id'], standards_df['standard_content']))
        
        for _, row in suggestions.iterrows():
            src_id = row['src_standard_id']
            dst_id = row['dst_standard_id']
            
            if src_id in id_to_code and dst_id in id_to_code:
                relations.append({
                    'source_code': id_to_code[src_id],
                    'target_code': id_to_code[dst_id],
                    'source_content': id_to_content[src_id],
                    'target_content': id_to_content[dst_id],
                    'relation_type': 'prerequisite',
                    'strength': float(row['confidence']),
                    'reasoning': row['rationale'],
                    'method': row['method']
                })
        
        logger.info(f"Processed {len(relations)} prerequisite relationships from DB")
        return relations
    
    async def _process_horizontal_suggestions(self, suggestions: pd.DataFrame, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Process horizontal suggestions from database view"""
        if suggestions.empty:
            logger.info("No horizontal suggestions from database")
            return []
        
        relations = []
        standards_df = curriculum_data['achievement_standards']
        
        # Create ID to code mapping
        id_to_code = dict(zip(standards_df['standard_id'], standards_df['standard_code']))
        id_to_content = dict(zip(standards_df['standard_id'], standards_df['standard_content']))
        
        for _, row in suggestions.iterrows():
            src_id = row['src_standard_id']
            dst_id = row['dst_standard_id']
            
            if src_id in id_to_code and dst_id in id_to_code:
                relations.append({
                    'source_code': id_to_code[src_id],
                    'target_code': id_to_code[dst_id],
                    'source_content': id_to_content[src_id],
                    'target_content': id_to_content[dst_id],
                    'relation_type': 'horizontal',
                    'strength': float(row['confidence']),
                    'reasoning': row['rationale'],
                    'method': row['method']
                })
        
        logger.info(f"Processed {len(relations)} horizontal relationships from DB")
        return relations
    
    async def _extract_similarity_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract similarity relationships using batch processing"""
        logger.info("Extracting similarity relationships")
        
        standards = curriculum_data['achievement_standards']
        relations = []
        
        # Limit pairs to same domain for efficiency
        for domain_id in standards['domain_id'].unique():
            domain_standards = standards[standards['domain_id'] == domain_id]
            
            # Create pairs within same domain
            standard_pairs = list(itertools.combinations(domain_standards.head(20).itertuples(), 2))
            
            if len(standard_pairs) > 0:
                batch_relations = await self._process_similarity_batch(standard_pairs)
                relations.extend(batch_relations)
        
        # Filter high-similarity relationships
        filtered_relations = [r for r in relations if r.get('similarity_score', 0) > 0.6]
        
        logger.info(f"Extracted {len(filtered_relations)} similarity relationships")
        return filtered_relations
    
    async def _process_similarity_batch(self, standard_pairs: List[Tuple]) -> List[Dict[str, Any]]:
        """Process a batch of standard pairs for similarity"""
        
        # Limit batch size for stability
        batch_size = min(10, len(standard_pairs))
        standard_pairs = standard_pairs[:batch_size]
        
        pairs_text = ""
        for idx, (std_a, std_b) in enumerate(standard_pairs):
            pairs_text += f"""
쌍 {idx + 1}:
A: [{std_a.standard_code}] {std_a.standard_content[:100]}...
B: [{std_b.standard_code}] {std_b.standard_content[:100]}...
"""
        
        prompt = f"""
다음 성취기준 쌍들의 유사도를 간단히 평가하세요 (0.0~1.0).

{pairs_text}

각 쌍에 대해 JSON 형식으로 응답:
{{
  "pair_1": {{
    "similarity_score": 0.0-1.0,
    "reasoning": "간단한 이유"
  }},
  ...
}}
"""
        
        try:
            response = await self.ai_manager.get_completion(self.model_name, prompt, max_tokens=1000)
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            batch_results = json.loads(json_str)
            
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
                        'reasoning': result.get('reasoning', '')
                    })
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to process similarity batch: {e}")
            return []
    
    async def _extract_domain_bridge_relationships(self, curriculum_data: Dict) -> List[Dict[str, Any]]:
        """Extract relationships that bridge different domains"""
        logger.info("Extracting domain bridge relationships")
        
        standards = curriculum_data['achievement_standards']
        relations = []
        
        # Sample a few cross-domain pairs for efficiency
        domains = standards['domain_id'].unique()
        
        if len(domains) >= 2:
            # Take first two domains
            domain_a_standards = standards[standards['domain_id'] == domains[0]].head(5)
            domain_b_standards = standards[standards['domain_id'] == domains[1]].head(5)
            
            bridge_relations = await self._find_domain_bridges(domain_a_standards, domain_b_standards)
            relations.extend(bridge_relations)
        
        logger.info(f"Extracted {len(relations)} domain bridge relationships")
        return relations
    
    async def _find_domain_bridges(self, standards_a: pd.DataFrame, standards_b: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find bridging relationships between two domains"""
        
        if standards_a.empty or standards_b.empty:
            return []
        
        domain_a_text = f"영역 A ({standards_a.iloc[0]['domain_name']}):\n"
        for _, std in standards_a.iterrows():
            domain_a_text += f"[{std['standard_code']}] {std['standard_content'][:80]}...\n"
        
        domain_b_text = f"영역 B ({standards_b.iloc[0]['domain_name']}):\n"
        for _, std in standards_b.iterrows():
            domain_b_text += f"[{std['standard_code']}] {std['standard_content'][:80]}...\n"
        
        prompt = f"""
두 수학 영역 간 연결 관계를 찾으세요:

{domain_a_text}

{domain_b_text}

가장 명확한 연결 2-3개만 JSON 형식으로:
{{
  "bridge_relations": [
    {{
      "source_code": "영역 A 코드",
      "target_code": "영역 B 코드",
      "strength": 0.0-1.0,
      "reasoning": "연결 이유"
    }}
  ]
}}
"""
        
        try:
            response = await self.ai_manager.get_completion(self.model_name, prompt, max_tokens=800)
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
        
        # Focus on one domain for efficiency
        domain_ids = standards['domain_id'].unique()
        if len(domain_ids) > 0:
            domain_standards = standards[standards['domain_id'] == domain_ids[0]]
            
            # Group by level_id
            level_groups = domain_standards.groupby('level_id')
            
            if len(level_groups) >= 2:
                levels = sorted(level_groups.groups.keys())
                
                # Compare adjacent levels
                for i in range(len(levels) - 1):
                    curr_level = level_groups.get_group(levels[i]).head(3)
                    next_level = level_groups.get_group(levels[i+1]).head(3)
                    
                    level_relations = await self._analyze_level_progression(curr_level, next_level)
                    relations.extend(level_relations)
        
        logger.info(f"Extracted {len(relations)} grade progression relationships")
        return relations
    
    async def _analyze_level_progression(self, curr_level: pd.DataFrame, next_level: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze progression between grade levels"""
        
        if curr_level.empty or next_level.empty:
            return []
        
        prompt = f"""
학년 진행 관계 분석:

현재 학년:
{curr_level[['standard_code', 'standard_content']].head(3).to_string()}

다음 학년:
{next_level[['standard_code', 'standard_content']].head(3).to_string()}

나선형 교육과정 관계 1-2개를 JSON으로:
{{
  "progression_relations": [
    {{
      "lower_grade_code": "하위 코드",
      "higher_grade_code": "상위 코드",
      "strength": 0.0-1.0,
      "reasoning": "진행 관계"
    }}
  ]
}}
"""
        
        try:
            response = await self.ai_manager.get_completion(self.model_name, prompt, max_tokens=600)
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
            if relations:  # Check if not empty
                all_relations.extend(relations)
        
        # Apply base weights by relation type
        base_weights = {
            'prerequisite': 1.0,
            'horizontal': 0.6,
            'similar_to': 0.5,
            'domain_bridge': 0.4,
            'grade_progression': 0.8
        }
        
        weighted_relations = []
        seen_pairs = set()  # Avoid duplicates
        
        for relation in all_relations:
            if not relation.get('source_code') or not relation.get('target_code'):
                continue
            
            pair = (relation['source_code'], relation['target_code'])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            
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
                'method': relation.get('method', 'ai'),
                'metadata': {k: v for k, v in relation.items() 
                           if k not in ['source_code', 'target_code', 'relation_type', 'reasoning', 'method']}
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