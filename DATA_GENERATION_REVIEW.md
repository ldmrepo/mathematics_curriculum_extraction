# 📋 데이터 생성 방법 검토 보고서

## 🔍 검토 대상
PostgreSQL 연결 테이블 데이터 생성 스크립트 분석

---

## 🚨 하드코딩 및 목업 데이터 사용 현황

### 1. **achievement_standard_relations** ✅ 실제 데이터
- **소스**: Neo4j 그래프 데이터베이스
- **방법**: AI가 Phase 2-3에서 추출한 실제 관계 데이터를 PostgreSQL로 동기화
- **품질**: 실제 AI 분석 결과 기반 (148개 관계)

### 2. **standard_terms** ⚠️ 단순 키워드 매칭
```python
# 실제 코드
if term_name and term_name in std_content:
    confidence = min(len(term_name) / 100, 1.0)  # 단순한 길이 기반 계산
```
- **문제점**: 
  - 단순 문자열 포함 여부만 확인
  - 신뢰도 계산이 용어 길이 / 100 으로 무의미
  - 문맥 고려 없음

### 3. **standard_competencies** ⚠️ 하드코딩된 키워드
```python
competency_keywords = {
    1: ['문제', '해결', '전략'],     # 하드코딩된 키워드
    2: ['추론', '논리', '증명'],
    3: ['창의', '융합', '탐구'],
    4: ['의사소통', '표현', '설명'],
    5: ['정보', '공학', '기술']
}
```
- **문제점**:
  - 키워드가 하드코딩되어 있음
  - 교육과정 전문가 검토 없이 임의 설정

### 4. **standard_representations** ⚠️ 하드코딩 + 기본값
```python
if rep_id == 9:  # 기타는 기본으로 추가
    if not found_any:
        mappings.append((
            std_id, rep_id, 
            "Default representation",  # 목업 텍스트
            None, 'rule', 0.5, "Default"
        ))
```
- **문제점**:
  - 매칭 안 되면 무조건 "기타"로 처리
  - 기본값 0.5 신뢰도 임의 설정

### 5. **learning_elements** 🔴 완전 하드코딩
```python
element_names = [
    '수와 연산의 이해',      # 하드코딩된 이름들
    '기하학적 사고',
    '측정과 단위',
    '자료의 수집과 정리',
    '확률과 통계'
]
# 모든 도메인에 동일한 요소명 사용
f"{elem_name} - Level {level_id}"  # 단순 텍스트 조합
```
- **문제점**:
  - 실제 교육과정과 무관한 임의 요소명
  - 도메인별 특성 무시

### 6. **standard_contexts** 🔴 랜덤 생성
```python
# 랜덤으로 맥락 할당
selected_contexts = random.sample(range(1, 5), k=random.randint(1, 2))
confidence = random.uniform(0.6, 0.9)  # 랜덤 신뢰도
```
- **문제점**:
  - 완전 랜덤 할당
  - 실제 성취기준 내용과 무관

### 7. **domain_achievement_levels** 🔴 고정값 사용
```python
'A' as level_code,  -- 임시로 고정값 사용
level_desc = {
    'A': '상 수준 - 심화 학습 가능',  # 하드코딩된 설명
    'B': '중상 수준 - 기본 개념 숙달',
    ...
}
```
- **문제점**:
  - 모든 레코드가 'A' 레벨로 고정
  - 실제 성취수준 분포 무시

---

## 📊 데이터 품질 평가

| 테이블 | 실제 데이터 | 품질 등급 | 문제 수준 |
|--------|------------|-----------|-----------|
| achievement_standard_relations | ✅ Neo4j AI 분석 | **A** | 없음 |
| standard_terms | ⚠️ 키워드 매칭 | **C** | 중간 |
| standard_competencies | ⚠️ 하드코딩 키워드 | **D** | 높음 |
| standard_representations | ⚠️ 하드코딩+기본값 | **D** | 높음 |
| learning_elements | 🔴 완전 하드코딩 | **F** | 매우 높음 |
| standard_contexts | 🔴 랜덤 생성 | **F** | 매우 높음 |
| domain_achievement_levels | 🔴 고정값 | **F** | 매우 높음 |

---

## 🎯 개선 방안

### 즉시 개선 필요 (Priority 1)
1. **learning_elements**: 실제 교육과정 학습요소 추출
2. **standard_contexts**: AI 기반 맥락 분석
3. **domain_achievement_levels**: 실제 성취수준 데이터 집계

### 중기 개선 (Priority 2)
4. **standard_competencies**: 교육 전문가 검증된 키워드
5. **standard_representations**: AI 기반 표현방법 분류

### 장기 개선 (Priority 3)
6. **standard_terms**: NLP 기반 의미적 매칭
7. 전체 데이터 교육 전문가 검증

---

## ⚡ 개선된 구현 예시

### 1. AI 기반 역량 매핑
```python
async def map_competencies_with_ai():
    prompt = f"""
    성취기준: {standard_content}
    
    다음 수학 교과 역량 중 관련된 것을 선택하고 이유를 설명하세요:
    1. 문제해결
    2. 추론
    3. 창의·융합
    4. 의사소통
    5. 정보처리
    6. 태도 및 실천
    """
    response = await ai_model.generate(prompt)
    return parse_competencies(response)
```

### 2. 실제 학습요소 추출
```python
def extract_real_learning_elements():
    # content_elements 테이블에서 실제 데이터 활용
    query = """
        SELECT DISTINCT 
            element_content,
            domain_id,
            level_id
        FROM curriculum.content_elements
        WHERE element_type = '학습요소'
    """
    return cursor.fetchall()
```

### 3. 맥락 분석 기반 매핑
```python
def analyze_context(standard_content):
    contexts = []
    if any(word in standard_content for word in ['생활', '실생활', '일상']):
        contexts.append('일상생활')
    if any(word in standard_content for word in ['과학', '미술', '음악']):
        contexts.append('타교과')
    # ... 규칙 기반 + AI 분석 조합
    return contexts
```

---

## 🔴 결론

### 현재 상태
- **실제 데이터 비율**: 약 20% (1/7 테이블만 실제 데이터)
- **하드코딩/목업 비율**: 약 80%
- **데이터 신뢰도**: 낮음

### 권장사항
1. **즉시**: 프로덕션 사용 전 반드시 개선 필요
2. **단기**: AI 모델 활용한 재생성
3. **장기**: 교육 전문가 검증 프로세스 구축

### 위험도
- 🔴 **높음**: 현재 데이터로 교육 서비스 운영 시 신뢰성 문제
- 🟡 **중간**: 개발/테스트 용도로는 사용 가능
- 🟢 **낮음**: achievement_standard_relations만 신뢰 가능

---

*검토 완료: 2024-12-27*
*권장 조치: 프로덕션 배포 전 데이터 재생성 필수*