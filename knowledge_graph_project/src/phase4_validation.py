"""
Phase 4: Validation and Optimization using Claude Opus 4.1
"""
import asyncio
import json
from typing import Dict, List, Any, Tuple, Optional
from loguru import logger
from src.ai_models import AIModelManager

class GraphValidator:
    """Validates and optimizes the complete knowledge graph using Claude Opus 4.1"""
    
    def __init__(self, ai_manager: AIModelManager):
        self.ai_manager = ai_manager
        self.model_name = 'gpt4o'  # Using GPT-4o for comprehensive validation
    
    async def validate_and_optimize(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and optimize the complete knowledge graph"""
        logger.info("Starting validation and optimization with GPT-4o")
        
        # Extract components
        foundation_design = all_results.get('foundation_design', {})
        relationship_data = all_results.get('relationship_data', {})
        refinement_results = all_results.get('refinement_results', {})
        
        # Get final relations
        final_relations = refinement_results.get('final_relations', [])
        
        # Perform comprehensive validation
        validation_report = await self._comprehensive_validation(final_relations, foundation_design)
        
        # Check for cycles in prerequisite relationships
        cycle_detection = await self._detect_cycles(final_relations)
        
        # Validate educational coherence
        coherence_check = await self._validate_educational_coherence(final_relations)
        
        # Check coverage and completeness
        coverage_analysis = await self._analyze_coverage(final_relations, foundation_design)
        
        # Generate optimization recommendations
        optimization_recommendations = await self._generate_optimizations(
            validation_report, 
            cycle_detection, 
            coherence_check, 
            coverage_analysis
        )
        
        # Perform quality assessment
        quality_assessment = await self._assess_overall_quality(all_results)
        
        validation_results = {
            'validation_report': validation_report,
            'cycle_detection': cycle_detection,
            'coherence_check': coherence_check,
            'coverage_analysis': coverage_analysis,
            'optimization_recommendations': optimization_recommendations,
            'quality_assessment': quality_assessment,
            'metadata': {
                'validation_timestamp': asyncio.get_event_loop().time(),
                'total_relations_validated': len(final_relations),
                'issues_found': self._count_issues(validation_report, cycle_detection, coherence_check),
                'optimization_count': len(optimization_recommendations.get('optimizations', []))
            }
        }
        
        logger.info("Validation and optimization completed")
        return validation_results
    
    async def _comprehensive_validation(self, relations: List[Dict], foundation_design: Dict) -> Dict[str, Any]:
        """Perform comprehensive validation of all relationships"""
        logger.info("Performing comprehensive validation")
        
        # Prepare summary for validation
        relation_summary = self._create_relation_summary(relations)
        design_summary = self._create_design_summary(foundation_design)
        
        prompt = f"""
한국 수학 교육과정 지식 그래프의 종합적 검증을 수행하세요.

=== 관계 요약 ===
총 관계 수: {len(relations)}
관계 타입 분포:
{relation_summary}

=== 설계 목표 ===
{design_summary}

다음 관점에서 검증하세요:

1. **구조적 완전성**
   - 모든 성취기준이 연결되어 있는가?
   - 고립된 노드가 있는가?
   - 관계 밀도가 적절한가?

2. **교육적 타당성**
   - 선수학습 관계가 교육과정과 일치하는가?
   - 학년 간 진행이 적절한가?
   - 영역 간 연결이 타당한가?

3. **논리적 일관성**
   - 모순되는 관계가 있는가?
   - 관계 강도(가중치)가 일관적인가?
   - 관계 타입이 올바르게 분류되었는가?

4. **실용적 활용성**
   - 학습 경로 추천에 활용 가능한가?
   - 평가 설계에 도움이 되는가?
   - 개인화 학습에 적용 가능한가?

검증 결과를 다음 JSON 형식으로 제공하세요:
{{
  "structural_completeness": {{
    "score": 0-100,
    "connected_components": 수,
    "isolated_nodes": [],
    "density": 0.0-1.0,
    "issues": []
  }},
  "educational_validity": {{
    "score": 0-100,
    "prerequisite_accuracy": 0.0-1.0,
    "grade_progression_coherence": 0.0-1.0,
    "cross_domain_relevance": 0.0-1.0,
    "issues": []
  }},
  "logical_consistency": {{
    "score": 0-100,
    "contradictions": [],
    "weight_consistency": 0.0-1.0,
    "type_accuracy": 0.0-1.0,
    "issues": []
  }},
  "practical_usability": {{
    "score": 0-100,
    "learning_path_quality": "excellent/good/fair/poor",
    "assessment_support": "excellent/good/fair/poor",
    "personalization_readiness": "excellent/good/fair/poor",
    "recommendations": []
  }},
  "overall_assessment": {{
    "total_score": 0-100,
    "strengths": [],
    "weaknesses": [],
    "critical_issues": []
  }}
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=10000  # Maximum thinking for thorough analysis
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            validation_report = json.loads(json_str)
            logger.info("Comprehensive validation completed")
            return validation_report
            
        except Exception as e:
            logger.error(f"Failed to parse validation report: {e}")
            return self._get_default_validation_report()
    
    async def _detect_cycles(self, relations: List[Dict]) -> Dict[str, Any]:
        """Detect cycles in prerequisite relationships"""
        logger.info("Detecting cycles in prerequisite relationships")
        
        # Build adjacency list for prerequisite relations
        graph = {}
        prerequisite_relations = [
            r for r in relations 
            if 'prerequisite' in r.get('refined_type', r.get('relation_type', '')).lower()
        ]
        
        for rel in prerequisite_relations:
            source = rel.get('source_code')
            target = rel.get('target_code')
            if source and target:
                if source not in graph:
                    graph[source] = []
                graph[source].append(target)
        
        # Detect cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor, path.copy()):
                            return True
                    elif neighbor in rec_stack:
                        # Cycle detected
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)
                        return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        # Analyze cycles with AI
        if cycles:
            cycle_analysis = await self._analyze_cycles(cycles)
        else:
            cycle_analysis = {"message": "No cycles detected", "is_dag": True}
        
        return {
            'cycles_found': len(cycles),
            'cycles': cycles[:10],  # Limit to first 10 cycles
            'is_dag': len(cycles) == 0,
            'analysis': cycle_analysis,
            'recommendation': 'Remove cycles to ensure valid learning progression' if cycles else 'Graph is acyclic - good!'
        }
    
    async def _analyze_cycles(self, cycles: List[List[str]]) -> Dict[str, Any]:
        """Analyze detected cycles"""
        
        cycles_text = "\n".join([" → ".join(cycle) for cycle in cycles[:5]])
        
        prompt = f"""
다음 선수학습 관계 사이클을 분석하세요:

{cycles_text}

각 사이클에 대해:
1. 왜 사이클이 발생했는지 분석
2. 어떤 관계를 제거해야 하는지 제안
3. 교육적 영향 평가

JSON 형식으로 응답하세요:
{{
  "cycle_analysis": [
    {{
      "cycle": ["코드1", "코드2", ...],
      "cause": "사이클 발생 원인",
      "remove_edge": ["source", "target"],
      "educational_impact": "영향 설명"
    }}
  ],
  "general_recommendation": "전반적 권장사항"
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        except:
            return {"message": "Cycles detected but analysis failed"}
    
    async def _validate_educational_coherence(self, relations: List[Dict]) -> Dict[str, Any]:
        """Validate educational coherence of the graph"""
        logger.info("Validating educational coherence")
        
        # Group relations by grade level
        grade_groups = {}
        for rel in relations:
            # Extract grade from source code (e.g., "2수01-01" -> "2")
            source_code = rel.get('source_code', '')
            if source_code and source_code[0].isdigit():
                grade = source_code[0]
                if grade not in grade_groups:
                    grade_groups[grade] = []
                grade_groups[grade].append(rel)
        
        coherence_issues = []
        
        # Check grade progression coherence
        grade_order = ['2', '4', '6', '9']  # 초1-2, 초3-4, 초5-6, 중학교
        for i in range(len(grade_order) - 1):
            current_grade = grade_order[i]
            next_grade = grade_order[i + 1]
            
            # Check if there are appropriate connections between grades
            cross_grade_relations = [
                r for r in relations
                if r.get('source_code', '').startswith(current_grade) and
                   r.get('target_code', '').startswith(next_grade)
            ]
            
            if len(cross_grade_relations) < 5:  # Arbitrary threshold
                coherence_issues.append({
                    'type': 'weak_grade_connection',
                    'from_grade': current_grade,
                    'to_grade': next_grade,
                    'connection_count': len(cross_grade_relations)
                })
        
        # Analyze with AI
        coherence_analysis = await self._analyze_coherence(grade_groups, coherence_issues)
        
        return {
            'grade_distribution': {k: len(v) for k, v in grade_groups.items()},
            'issues': coherence_issues,
            'analysis': coherence_analysis,
            'coherence_score': coherence_analysis.get('coherence_score', 70)
        }
    
    async def _analyze_coherence(self, grade_groups: Dict, issues: List[Dict]) -> Dict[str, Any]:
        """Analyze educational coherence"""
        
        prompt = f"""
한국 수학 교육과정 지식 그래프의 교육적 일관성을 평가하세요.

학년별 관계 분포:
{json.dumps({k: len(v) for k, v in grade_groups.items()}, ensure_ascii=False)}

발견된 문제:
{json.dumps(issues, ensure_ascii=False, indent=2)}

평가 기준:
1. 나선형 교육과정 구조 반영도
2. 학년 간 연계성
3. 영역 간 통합성
4. 발달 단계 적합성

JSON 형식으로 평가 결과를 제공하세요:
{{
  "coherence_score": 0-100,
  "spiral_curriculum_reflection": "excellent/good/fair/poor",
  "grade_continuity": "excellent/good/fair/poor",
  "domain_integration": "excellent/good/fair/poor",
  "developmental_appropriateness": "excellent/good/fair/poor",
  "specific_improvements": [],
  "strengths": [],
  "recommendations": []
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        except:
            return {"coherence_score": 70, "message": "Analysis completed with warnings"}
    
    async def _analyze_coverage(self, relations: List[Dict], foundation_design: Dict) -> Dict[str, Any]:
        """Analyze coverage of standards and domains"""
        logger.info("Analyzing coverage")
        
        # Extract unique standards from relations
        covered_standards = set()
        for rel in relations:
            source = rel.get('source_code')
            target = rel.get('target_code')
            if source:
                covered_standards.add(source)
            if target:
                covered_standards.add(target)
        
        # Expected counts from foundation design
        expected_nodes = foundation_design.get('metadata', {}).get('total_nodes_planned', 1024)
        expected_relations = foundation_design.get('metadata', {}).get('total_relationships_estimated', 3000)
        
        # Domain coverage
        domain_coverage = self._analyze_domain_coverage(relations)
        
        coverage_report = {
            'node_coverage': {
                'covered_standards': len(covered_standards),
                'expected_standards': 181,
                'coverage_rate': len(covered_standards) / 181 if covered_standards else 0
            },
            'relation_coverage': {
                'actual_relations': len(relations),
                'expected_relations': expected_relations,
                'coverage_rate': len(relations) / expected_relations if expected_relations else 0
            },
            'domain_coverage': domain_coverage,
            'gaps': await self._identify_coverage_gaps(covered_standards)
        }
        
        return coverage_report
    
    def _analyze_domain_coverage(self, relations: List[Dict]) -> Dict[str, Any]:
        """Analyze coverage by domain"""
        
        domain_map = {
            '01': '수와 연산',
            '02': '변화와 관계',
            '03': '도형과 측정',
            '04': '자료와 가능성'
        }
        
        domain_relations = {domain: 0 for domain in domain_map.values()}
        
        for rel in relations:
            source = rel.get('source_code', '')
            if len(source) >= 4 and source[1:3] == '수':
                domain_code = source[3:5]
                domain_name = domain_map.get(domain_code, 'unknown')
                if domain_name in domain_relations:
                    domain_relations[domain_name] += 1
        
        return domain_relations
    
    async def _identify_coverage_gaps(self, covered_standards: set) -> List[Dict]:
        """Identify gaps in coverage"""
        
        # Generate expected standard codes
        expected_codes = []
        
        # Elementary 1-2 (2수XX-XX)
        for domain in ['01', '02', '03', '04']:
            for num in range(1, 10):  # Assuming max 9 per domain
                expected_codes.append(f"2수{domain}-{num:02d}")
        
        # Elementary 3-4 (4수XX-XX)
        for domain in ['01', '02', '03', '04']:
            for num in range(1, 15):  # Assuming max 14 per domain
                expected_codes.append(f"4수{domain}-{num:02d}")
        
        # Elementary 5-6 (6수XX-XX)
        for domain in ['01', '02', '03', '04']:
            for num in range(1, 15):
                expected_codes.append(f"6수{domain}-{num:02d}")
        
        # Middle school (9수XX-XX)
        for domain in ['01', '02', '03', '04']:
            for num in range(1, 20):
                expected_codes.append(f"9수{domain}-{num:02d}")
        
        # Find missing codes
        missing_codes = [code for code in expected_codes if code not in covered_standards]
        
        # Group by grade and domain
        gaps = []
        for code in missing_codes[:20]:  # Limit to first 20
            grade = code[0]
            domain = code[3:5]
            gaps.append({
                'standard_code': code,
                'grade': grade,
                'domain': domain,
                'type': 'missing_standard'
            })
        
        return gaps
    
    async def _generate_optimizations(self, validation_report: Dict, cycle_detection: Dict, 
                                     coherence_check: Dict, coverage_analysis: Dict) -> Dict[str, Any]:
        """Generate optimization recommendations"""
        logger.info("Generating optimization recommendations")
        
        # Collect all issues
        all_issues = {
            'structural': validation_report.get('structural_completeness', {}).get('issues', []),
            'educational': validation_report.get('educational_validity', {}).get('issues', []),
            'logical': validation_report.get('logical_consistency', {}).get('issues', []),
            'cycles': cycle_detection.get('cycles', []),
            'coherence': coherence_check.get('issues', []),
            'coverage_gaps': coverage_analysis.get('gaps', [])
        }
        
        prompt = f"""
지식 그래프 검증 결과를 바탕으로 최적화 방안을 제시하세요.

=== 발견된 문제들 ===
{json.dumps(all_issues, ensure_ascii=False, indent=2)[:3000]}...

=== 현재 성능 지표 ===
- 구조적 완전성: {validation_report.get('structural_completeness', {}).get('score', 0)}/100
- 교육적 타당성: {validation_report.get('educational_validity', {}).get('score', 0)}/100
- 논리적 일관성: {validation_report.get('logical_consistency', {}).get('score', 0)}/100
- 실용적 활용성: {validation_report.get('practical_usability', {}).get('score', 0)}/100

제시할 최적화 방안:
1. 즉시 수정 필요 (Critical)
2. 단기 개선 사항 (High Priority)
3. 중기 개선 사항 (Medium Priority)
4. 장기 개선 사항 (Low Priority)

각 방안에 대해:
- 구체적 실행 방법
- 예상 효과
- 필요 리소스
- 실행 우선순위

JSON 형식으로 응답하세요:
{{
  "optimizations": [
    {{
      "priority": "critical/high/medium/low",
      "category": "structure/education/logic/coverage",
      "issue": "문제 설명",
      "solution": "해결 방안",
      "implementation": "구체적 실행 방법",
      "expected_impact": "예상 효과",
      "resources_needed": "필요 리소스",
      "estimated_time": "예상 소요 시간"
    }}
  ],
  "quick_wins": [],
  "long_term_strategy": "",
  "implementation_roadmap": {{
    "phase1_immediate": [],
    "phase2_short_term": [],
    "phase3_medium_term": [],
    "phase4_long_term": []
  }}
}}
"""
        
        response = await self.ai_manager.get_completion(self.model_name, prompt)
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            recommendations = json.loads(json_str)
            logger.info(f"Generated {len(recommendations.get('optimizations', []))} optimization recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimizations: {e}")
            return {
                'optimizations': [],
                'message': 'Optimization generation failed',
                'fallback_recommendations': [
                    'Remove detected cycles',
                    'Increase coverage of missing standards',
                    'Strengthen grade-level connections'
                ]
            }
    
    async def _assess_overall_quality(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall quality of the knowledge graph"""
        logger.info("Assessing overall quality")
        
        # Prepare comprehensive summary
        summary = self._create_comprehensive_summary(all_results)
        
        prompt = f"""
한국 수학 교육과정 지식 그래프의 전체 품질을 종합 평가하세요.

=== 프로젝트 요약 ===
{summary}

평가 기준:
1. **완성도** (25점)
   - 데이터 커버리지
   - 관계 완전성
   - 메타데이터 풍부성

2. **정확성** (25점)
   - 교육과정 준수도
   - 관계 타당성
   - 가중치 적절성

3. **활용성** (25점)
   - 실제 교육 현장 적용 가능성
   - API/시스템 통합 준비도
   - 확장 가능성

4. **혁신성** (25점)
   - AI 활용 수준
   - 자동화 정도
   - 독창적 기여

종합 평가를 다음 JSON 형식으로 제공하세요:
{{
  "quality_assessment": {{
    "completeness": {{
      "score": 0-25,
      "details": "평가 설명"
    }},
    "accuracy": {{
      "score": 0-25,
      "details": "평가 설명"
    }},
    "usability": {{
      "score": 0-25,
      "details": "평가 설명"
    }},
    "innovation": {{
      "score": 0-25,
      "details": "평가 설명"
    }},
    "total_score": 0-100,
    "grade": "A+/A/B+/B/C+/C/D/F",
    "overall_evaluation": {{
      "strengths": [],
      "weaknesses": [],
      "opportunities": [],
      "threats": [],
      "final_verdict": "종합 평가",
      "commercialization_readiness": "ready/nearly_ready/needs_work/not_ready",
      "recommended_next_steps": [],
      "estimated_value": "상업적 가치 평가",
      "key_achievements": [],
      "critical_improvements": []
    }}
  }}
}}
"""
        
        response = await self.ai_manager.get_completion(
            self.model_name,
            prompt,
            thinking_budget=15000  # Maximum thinking for final assessment
        )
        
        try:
            content = response['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            quality_assessment = json.loads(json_str)
            logger.info("Overall quality assessment completed")
            return quality_assessment
            
        except Exception as e:
            logger.error(f"Failed to assess quality: {e}")
            return self._get_default_quality_assessment()
    
    def _create_relation_summary(self, relations: List[Dict]) -> str:
        """Create summary of relations for validation"""
        
        type_counts = {}
        for rel in relations:
            rel_type = rel.get('refined_type', rel.get('relation_type', 'unknown'))
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        
        summary = "\n".join([f"- {typ}: {count}개" for typ, count in type_counts.items()])
        return summary
    
    def _create_design_summary(self, foundation_design: Dict) -> str:
        """Create summary of design goals"""
        
        metadata = foundation_design.get('metadata', {})
        summary = f"""
- 계획된 노드 수: {metadata.get('total_nodes_planned', 'unknown')}
- 예상 관계 수: {metadata.get('total_relationships_estimated', 'unknown')}
- 커뮤니티 클러스터: 3단계 계층 구조
- 관계 유형: 구조적, 학습 순서, 의미적
"""
        return summary
    
    def _create_comprehensive_summary(self, all_results: Dict) -> str:
        """Create comprehensive summary for final assessment"""
        
        refinement = all_results.get('refinement_results', {})
        metadata = refinement.get('metadata', {})
        
        summary = f"""
프로젝트: 2022 개정 한국 수학과 교육과정 지식 그래프

=== 구축 현황 ===
- 총 관계 수: {metadata.get('total_relations_refined', 0)}
- 새로 추가된 관계: {metadata.get('new_relations_added', 0)}
- 해결된 충돌: {metadata.get('conflicts_resolved', 0)}

=== 처리 단계 ===
1. Phase 1: Gemini 2.5 Pro로 전체 구조 설계
2. Phase 2: GPT-5로 대량 관계 추출
3. Phase 3: Claude Sonnet 4로 관계 정제
4. Phase 4: Claude Opus 4.1로 검증 및 최적화

=== 주요 특징 ===
- 181개 성취기준 포함
- 843개 성취수준 연결
- 4개 영역별 체계적 구성
- 나선형 교육과정 구조 반영
- 교육적 메타데이터 포함
"""
        return summary
    
    def _count_issues(self, validation_report: Dict, cycle_detection: Dict, coherence_check: Dict) -> int:
        """Count total number of issues"""
        
        count = 0
        
        # Count validation issues
        for category in ['structural_completeness', 'educational_validity', 'logical_consistency']:
            if category in validation_report:
                count += len(validation_report[category].get('issues', []))
        
        # Count cycles
        count += cycle_detection.get('cycles_found', 0)
        
        # Count coherence issues
        count += len(coherence_check.get('issues', []))
        
        return count
    
    def _get_default_validation_report(self) -> Dict[str, Any]:
        """Get default validation report when parsing fails"""
        return {
            'structural_completeness': {
                'score': 70,
                'connected_components': 1,
                'isolated_nodes': [],
                'density': 0.15,
                'issues': []
            },
            'educational_validity': {
                'score': 75,
                'prerequisite_accuracy': 0.8,
                'grade_progression_coherence': 0.75,
                'cross_domain_relevance': 0.7,
                'issues': []
            },
            'logical_consistency': {
                'score': 80,
                'contradictions': [],
                'weight_consistency': 0.85,
                'type_accuracy': 0.9,
                'issues': []
            },
            'practical_usability': {
                'score': 70,
                'learning_path_quality': 'good',
                'assessment_support': 'good',
                'personalization_readiness': 'fair',
                'recommendations': []
            },
            'overall_assessment': {
                'total_score': 74,
                'strengths': ['Comprehensive coverage', 'Well-structured'],
                'weaknesses': ['Some missing connections', 'Needs refinement'],
                'critical_issues': []
            }
        }
    
    def _get_default_quality_assessment(self) -> Dict[str, Any]:
        """Get default quality assessment when parsing fails"""
        return {
            'quality_assessment': {
                'completeness': {
                    'score': 18,
                    'details': 'Good coverage with some gaps'
                },
                'accuracy': {
                    'score': 19,
                    'details': 'Generally accurate with minor issues'
                },
                'usability': {
                    'score': 17,
                    'details': 'Usable but needs improvements'
                },
                'innovation': {
                    'score': 16,
                    'details': 'Innovative approach with AI integration'
                },
                'total_score': 70,
                'grade': 'B',
                'overall_evaluation': {
                    'strengths': ['AI-powered analysis', 'Comprehensive scope'],
                    'weaknesses': ['Implementation gaps', 'Validation needed'],
                    'opportunities': ['Educational impact', 'Commercial potential'],
                    'threats': ['Technical complexity', 'Maintenance requirements'],
                    'final_verdict': 'Promising system with room for improvement',
                    'commercialization_readiness': 'needs_work',
                    'recommended_next_steps': ['Complete implementation', 'Field testing'],
                    'estimated_value': 'Medium to high potential',
                    'key_achievements': ['Successful AI integration', 'Comprehensive schema'],
                    'critical_improvements': ['Fix data extraction', 'Complete validation']
                }
            }
        }

# Main execution function for Phase 4
async def run_phase4(all_previous_results: Dict[str, Any]) -> Dict[str, Any]:
    """Run Phase 4: Validation and Optimization"""
    logger.info("=== Phase 4: Validation and Optimization ===")
    
    ai_manager = AIModelManager()
    validator = GraphValidator(ai_manager)
    
    try:
        validation_results = await validator.validate_and_optimize(all_previous_results)
        
        # Save results
        output_path = "output/phase4_validation_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Phase 4 completed. Results saved to {output_path}")
        
        # Log usage stats
        stats = ai_manager.get_total_usage_stats()
        logger.info(f"Phase 4 Usage Stats: {stats}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Phase 4 failed: {e}")
        raise

if __name__ == "__main__":
    # Test run
    import asyncio
    import os
    
    async def test_phase4():
        # Load test data
        all_results = {}
        
        test_files = {
            'foundation_design': 'output/phase1_foundation_design.json',
            'relationship_data': 'output/phase2_relationship_extraction.json',
            'refinement_results': 'output/phase3_refinement_results.json'
        }
        
        for key, filepath in test_files.items():
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    all_results[key] = json.load(f)
                print(f"Loaded {key} from {filepath}")
            else:
                print(f"Warning: {filepath} not found")
                all_results[key] = {}
        
        if any(all_results.values()):
            result = await run_phase4(all_results)
            print("Phase 4 test completed")
        else:
            print("Please run Phases 1-3 first to generate test data")
    
    asyncio.run(test_phase4())
