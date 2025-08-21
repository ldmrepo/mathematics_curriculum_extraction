## 🤖 **LLM 3사 최상위 모델을 활용한 관계 추출 방안**

### **1. 모델별 특성 및 강점**

#### **OpenAI GPT-4 Turbo**
- **강점**: 복잡한 추론, 긴 컨텍스트(128K), Function Calling
- **관계 추출 특화**: 구조화된 출력, JSON 모드

#### **Claude 3.5 Sonnet** 
- **강점**: 교육적 맥락 이해, 정확한 분석, 200K 토큰
- **관계 추출 특화**: 상세한 설명, 논리적 추론

#### **Gemini 1.5 Pro**
- **강점**: 멀티모달, 빠른 처리, 1M 토큰 컨텍스트
- **관계 추출 특화**: 대량 데이터 일괄 처리

---

### **2. 단계별 관계 추출 프로세스**

#### **Phase 1: 전체 교육과정 문서 입력**

##### **Step 1: 대용량 컨텍스트 활용**
```python
# Gemini 1.5 Pro - 전체 문서 분석
prompt_gemini = """
다음은 한국 2022 개정 수학과 교육과정 전체입니다.

[181개 성취기준 전체 입력]
[843개 성취수준 전체 입력]

위 데이터를 분석하여 다음을 추출하세요:
1. 명시적으로 언급된 선수학습 관계
2. 암묵적으로 필요한 선행 개념
3. 학년 간 연계성
4. 영역 간 융합 관계

JSON 형식으로 출력:
{
  "prerequisite_relations": [...],
  "implicit_dependencies": [...],
  "grade_progressions": [...],
  "cross_domain_relations": [...]
}
"""
```

#### **Phase 2: 세부 관계 분석**

##### **Step 2: 성취기준 쌍별 관계 판단**
```python
# Claude 3.5 - 정밀 분석
prompt_claude = """
두 성취기준 간의 관계를 분석하세요.

성취기준 A: [2수01-01] 네 자리 이하의 수
- 내용: 수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해

성취기준 B: [2수01-04] 네 자리 이하의 수  
- 내용: 하나의 수를 두 수로 분해하고 두 수를 하나의 수로 합성

분석할 관계 유형:
1. prerequisite (선수학습 필수): A를 반드시 먼저 학습해야 B 가능
2. corequisite (동시학습 가능): A와 B를 함께 학습 가능
3. extends (심화/확장): A가 B의 심화 내용
4. similar_to (유사 개념): 비슷한 개념 다룸
5. applies_to (응용): A의 개념이 B에 응용됨
6. no_relation (무관): 직접적 관계 없음

출력:
{
  "relation_type": "prerequisite",
  "confidence": 0.95,
  "reasoning": "수 개념 이해가 선행되어야 수의 분해/합성 가능",
  "weight": 0.9
}
"""
```

##### **Step 3: 다중 모델 교차 검증**
```python
# GPT-4 - 구조화된 추출
prompt_gpt4 = """
Function: extract_mathematical_relations

Parameters:
- source_standard: 성취기준 코드
- target_standard: 성취기준 코드  
- source_content: 성취기준 내용
- target_content: 성취기준 내용

Return:
{
  "edges": [
    {
      "source": "[2수01-01]",
      "target": "[2수01-04]", 
      "type": "prerequisite",
      "weight": 0.9,
      "evidence": "수 개념이 분해/합성의 기초",
      "confidence": 0.92
    }
  ]
}

모든 가능한 관계를 추출하고, 각 관계의 타당성을 평가하세요.
"""
```

---

### **3. 앙상블 관계 추출 전략**

#### **3.1 병렬 처리 아키텍처**

```python
async def extract_relations_ensemble(standards_pair):
    """3개 모델 동시 실행"""
    
    # 동시 실행
    tasks = [
        extract_with_gpt4(standards_pair),
        extract_with_claude(standards_pair),
        extract_with_gemini(standards_pair)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 결과 통합
    return merge_results(results)
```

#### **3.2 가중 투표 메커니즘**

```python
def merge_results(model_results):
    """모델별 결과 통합"""
    
    weights = {
        'gpt4': 0.35,     # 구조화 강점
        'claude': 0.40,   # 교육 이해도 높음
        'gemini': 0.25    # 빠른 처리
    }
    
    # 관계 타입별 투표
    relation_votes = {}
    
    for model, result in model_results.items():
        for relation in result['edges']:
            key = f"{relation['source']}-{relation['target']}"
            
            if key not in relation_votes:
                relation_votes[key] = []
            
            relation_votes[key].append({
                'type': relation['type'],
                'weight': relation['weight'],
                'model_weight': weights[model],
                'confidence': relation['confidence']
            })
    
    # 최종 관계 결정
    final_relations = []
    for key, votes in relation_votes.items():
        # 가중 평균으로 최종 관계 결정
        final_relation = determine_final_relation(votes)
        final_relations.append(final_relation)
    
    return final_relations
```

---

### **4. 특수 관계 추출 기법**

#### **4.1 Chain-of-Thought 추론**

```python
# 복잡한 관계 추출을 위한 CoT
prompt_cot = """
단계별로 추론하여 관계를 추출하세요.

Step 1: 각 성취기준의 핵심 개념 추출
[2수01-01]: 수 개념, 0-100
[4수01-01]: 큰 수, 만 단위

Step 2: 개념 간 의존성 분석
- 100까지 이해 → 큰 수 학습 가능
- 자리값 개념 확장

Step 3: 학습 순서 판단
- 선행 필수? 예
- 동시 가능? 아니오

Step 4: 관계 타입 결정
- Type: prerequisite
- Weight: 1.0
- Confidence: 0.95
"""
```

#### **4.2 Few-shot Learning**

```python
# 예시 기반 관계 추출
few_shot_examples = """
예시 1:
A: [2수01-01] 100까지의 수
B: [2수01-04] 덧셈과 뺄셈
관계: prerequisite (수를 알아야 연산 가능)

예시 2:
A: [4수01-02] 곱셈
B: [4수01-03] 나눗셈
관계: corequisite (역연산 관계로 함께 학습)

예시 3:
A: [6수02-01] 비와 비율
B: [9수03-02] 일차함수
관계: prerequisite (비례 개념이 함수의 기초)

이제 다음을 분석하세요:
A: [새로운 성취기준]
B: [새로운 성취기준]
관계: ?
"""
```

---

### **5. 대량 처리 최적화**

#### **5.1 배치 처리 전략**

```python
def batch_process_relations():
    """181개 성취기준 → 16,290개 가능한 쌍"""
    
    # 1. 같은 영역 내 관계만 우선 처리
    # 2. 인접 학년 간 관계 처리  
    # 3. 영역 간 융합 관계 처리
    
    batches = {
        'high_priority': [],  # 같은 영역, 인접 학년
        'medium_priority': [],  # 다른 영역, 같은 학년
        'low_priority': []  # 원거리 관계
    }
    
    # Gemini로 대량 스크리닝
    initial_screening = gemini_bulk_process(all_pairs)
    
    # 유의미한 관계만 정밀 분석
    significant_pairs = filter(
        lambda x: x['similarity'] > 0.3, 
        initial_screening
    )
    
    # GPT-4와 Claude로 정밀 분석
    detailed_analysis = parallel_analysis(significant_pairs)
```

#### **5.2 캐싱 및 증분 처리**

```python
class RelationCache:
    def __init__(self):
        self.cache = {}
        
    def get_or_compute(self, pair):
        key = f"{pair[0]}-{pair[1]}"
        
        if key in self.cache:
            return self.cache[key]
        
        # 계산되지 않은 관계만 LLM 호출
        result = extract_relation(pair)
        self.cache[key] = result
        
        return result
```

---

### **6. 품질 보증 프로세스**

#### **6.1 신뢰도 기반 필터링**

```python
def filter_by_confidence(relations):
    """신뢰도 기준 필터링"""
    
    thresholds = {
        'prerequisite': 0.85,  # 중요도 높음
        'extends': 0.75,
        'similar_to': 0.65,
        'applies_to': 0.60
    }
    
    filtered = []
    for relation in relations:
        threshold = thresholds.get(relation['type'], 0.7)
        if relation['confidence'] >= threshold:
            filtered.append(relation)
            
    return filtered
```

#### **6.2 일관성 검증**

```python
def validate_consistency(relations):
    """논리적 일관성 검증"""
    
    issues = []
    
    # 순환 참조 검사
    if has_cycle(relations):
        issues.append("Circular dependency detected")
    
    # 모순 관계 검사
    for r1 in relations:
        for r2 in relations:
            if contradicts(r1, r2):
                issues.append(f"Contradiction: {r1} vs {r2}")
    
    return issues
```

---

### **7. 예상 결과 및 비용**

#### **7.1 처리 규모**
- 총 성취기준 쌍: 16,290개
- 유의미한 관계 예상: ~2,000개
- 최종 선별 관계: ~500개

#### **7.2 API 비용 예상**
```
스크리닝 (Gemini): 
- 16,290 쌍 × $0.0001 = $1.63

정밀 분석 (GPT-4 + Claude):
- 2,000 쌍 × $0.01 = $20.00

총 예상 비용: ~$25
처리 시간: ~3시간
```

#### **7.3 기대 산출물**
```json
{
  "extracted_relations": [
    {
      "source": "[2수01-01]",
      "target": "[4수01-01]",
      "type": "prerequisite",
      "weight": 0.95,
      "confidence": 0.92,
      "evidence": "모델 3개 일치",
      "extracted_by": ["gpt4", "claude", "gemini"]
    }
  ],
  "statistics": {
    "total_relations": 523,
    "prerequisite": 187,
    "corequisite": 89,
    "extends": 134,
    "similar_to": 113
  }
}
```

이 방법으로 3개 최상위 모델의 강점을 활용하여 정확하고 포괄적인 관계 추출이 가능합니다.