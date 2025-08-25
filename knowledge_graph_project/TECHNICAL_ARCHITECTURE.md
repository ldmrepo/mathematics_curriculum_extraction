# Knowledge Graph Project 기술 아키텍처

## 1. 기술 스택

### 1.1 Core Technologies

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Language** | Python | 3.8+ | 메인 개발 언어 |
| **Database** | PostgreSQL | 16 | 교육과정 데이터 저장 |
| **Graph DB** | Neo4j | 4.4+ | 지식 그래프 저장 |
| **Container** | Docker | 20.10+ | 환경 구성 |
| **Cache** | Redis | 7.0 | API 응답 캐싱 |

### 1.2 AI Models

| 모델 | 제공사 | 용도 | 특징 |
|------|--------|------|------|
| **Gemini 2.5 Pro** | Google | Phase 1: 구조 설계 | 1M token context |
| **GPT-5** | OpenAI | Phase 2: 관계 추출 | 배치 처리 최적화 |
| **Claude Sonnet 4** | Anthropic | Phase 3: 관계 정제 | Hybrid reasoning |
| **Claude Opus 4.1** | Anthropic | Phase 4: 검증 | 최고 성능 |

### 1.3 Python Libraries

```python
# requirements.txt
psycopg2-binary==2.9.9      # PostgreSQL 연결
neo4j==5.15.0               # Neo4j 드라이버
pandas==2.1.4               # 데이터 처리
numpy==1.24.3               # 수치 계산
openai==1.6.1               # OpenAI API
anthropic==0.8.1            # Anthropic API
google-generativeai==0.3.2  # Google AI API
loguru==0.7.2               # 로깅
pydantic==2.5.3             # 데이터 검증
python-dotenv==1.0.0        # 환경변수 관리
tenacity==8.2.3             # 재시도 로직
streamlit==1.29.0           # 대시보드
pytest==7.4.3               # 테스트
```

## 2. 데이터베이스 스키마

### 2.1 PostgreSQL Schema (v1.3.0)

```sql
-- Core Tables
curriculum.achievement_standards    -- 181개 성취기준
curriculum.standard_achievement_levels  -- 663개 성취수준
curriculum.content_elements         -- 291개 내용요소
curriculum.terms_symbols            -- 362개 용어/기호

-- v1.3.0 Bridge Tables
curriculum.achievement_standard_relations  -- 성취기준 간 관계
curriculum.standard_terms           -- 성취기준-용어 매핑
curriculum.standard_representations -- 성취기준-표상 매핑
curriculum.standard_competencies    -- 성취기준-역량 매핑

-- v1.3.0 Views
curriculum.v_prerequisite_suggestions  -- 선수학습 제안
curriculum.v_horizontal_suggestions    -- 수평 관계 제안
curriculum.v_standard_meta            -- 메타데이터 요약
curriculum.rpt_coverage              -- 커버리지 리포트

-- Functions
curriculum.detect_prerequisite_cycles()  -- 사이클 검출
```

### 2.2 Neo4j Graph Schema

```cypher
// Node Types
(:AchievementStandard {
  code: String,
  title: String,
  content: String,
  difficulty: Integer,
  standard_order: Integer
})

(:Domain {
  code: String,
  name: String
})

(:GradeLevel {
  code: String,
  name: String,
  grade_start: Integer,
  grade_end: Integer
})

// Relationship Types
[:PREREQUISITE {weight: Float, reasoning: String}]
[:SIMILAR_TO {weight: Float, similarity_score: Float}]
[:HORIZONTAL {weight: Float}]
[:BRIDGES_DOMAIN {weight: Float}]
[:PROGRESSES_TO {weight: Float}]
[:HAS_LEVEL]
[:CONTAINS_STANDARD]
```

## 3. 시스템 아키텍처

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Orchestrator                      │
│                         (main.py)                            │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┬────────────┐
        ▼            ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Phase 1  │ │ Phase 2  │ │ Phase 3  │ │ Phase 4  │ │ Phase 5  │
│Foundation│ │Relations │ │Refinement│ │Validation│ │  Neo4j   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
      │            │            │            │            │
      └────────────┴────────────┴────────────┴────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐       ┌──────────────┐
            │ AI Manager   │       │ DB Manager   │
            │(ai_models.py)│       │(data_manager)│
            └──────────────┘       └──────────────┘
                    │                       │
        ┌───────────┼───────────┐          │
        ▼           ▼           ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │OpenAI  │ │Claude  │ │Gemini  │ │PostgreSQL│
    └────────┘ └────────┘ └────────┘ └────────┘
```

### 3.2 Data Flow

```
PostgreSQL → Data Extraction → Phase 1-4 Processing → Neo4j → API/Dashboard
     ↑                              ↓
     └──────── Feedback Loop ───────┘
```

## 4. 핵심 알고리즘

### 4.1 사이클 검출 (Phase 4)

```python
def detect_cycles(relations: List[Dict]) -> List[List[str]]:
    """DFS 기반 사이클 검출"""
    graph = build_adjacency_list(relations)
    visited = set()
    rec_stack = set()
    cycles = []
    
    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path.copy()):
                    return True
            elif neighbor in rec_stack:
                # 사이클 발견
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles
```

### 4.2 관계 가중치 계산

```python
def calculate_weight(relation: Dict) -> float:
    """관계 가중치 계산"""
    base_weights = {
        'prerequisite': 1.0,
        'horizontal': 0.6,
        'similar_to': 0.5,
        'domain_bridge': 0.4,
        'grade_progression': 0.8
    }
    
    base = base_weights.get(relation['type'], 0.5)
    confidence = relation.get('confidence', 1.0)
    importance = relation.get('educational_importance', 1.0)
    
    return base * confidence * importance
```

### 4.3 배치 처리 최적화

```python
async def process_in_batches(items: List, batch_size: int = 10):
    """배치 처리로 API 호출 최적화"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        
        # 병렬 처리
        batch_results = await asyncio.gather(*[
            process_item(item) for item in batch
        ])
        
        results.extend(batch_results)
        
        # Rate limiting
        await asyncio.sleep(1)
    
    return results
```

## 5. API 인터페이스

### 5.1 REST API Endpoints (계획)

```python
# FastAPI 기반 (향후 구현)
GET  /api/standards              # 성취기준 목록
GET  /api/standards/{code}       # 특정 성취기준
GET  /api/standards/{code}/prerequisites  # 선수학습
GET  /api/standards/{code}/similar       # 유사 성취기준
GET  /api/learning-path          # 학습 경로 생성
POST /api/classify               # 문항 분류
```

### 5.2 GraphQL Schema (계획)

```graphql
type AchievementStandard {
  code: String!
  title: String!
  content: String!
  domain: Domain!
  gradeLevel: GradeLevel!
  prerequisites: [AchievementStandard]
  similar: [AchievementStandard]
  competencies: [Competency]
}

type Query {
  standard(code: String!): AchievementStandard
  standards(domain: String, grade: String): [AchievementStandard]
  learningPath(start: String!, end: String!): [AchievementStandard]
}
```

## 6. 성능 최적화

### 6.1 캐싱 전략

```python
# Redis 캐싱
CACHE_TTL = 3600  # 1시간

async def get_with_cache(key: str, fetch_func):
    # Redis에서 확인
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    # 없으면 실행 후 캐싱
    result = await fetch_func()
    await redis.setex(key, CACHE_TTL, json.dumps(result))
    return result
```

### 6.2 데이터베이스 인덱스

```sql
-- PostgreSQL 인덱스
CREATE INDEX idx_standards_code ON achievement_standards(standard_code);
CREATE INDEX idx_standards_level_domain ON achievement_standards(level_id, domain_id);
CREATE INDEX idx_relations_src_dst ON achievement_standard_relations(src_standard_id, dst_standard_id);

-- Neo4j 인덱스
CREATE INDEX standard_code_idx FOR (s:AchievementStandard) ON (s.code);
CREATE INDEX domain_code_idx FOR (d:Domain) ON (d.code);
```

## 7. 모니터링 및 로깅

### 7.1 로깅 구성

```python
# loguru 설정
logger.add(
    "logs/knowledge_graph_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
```

### 7.2 메트릭 수집

```python
# 추적 메트릭
metrics = {
    'api_calls': Counter(),
    'api_cost': Gauge(),
    'processing_time': Histogram(),
    'error_rate': Counter(),
    'cache_hit_rate': Gauge()
}
```

## 8. 보안 고려사항

### 8.1 API 키 관리

```python
# 환경 변수로 관리
API_KEYS = {
    'openai': os.getenv('OPENAI_API_KEY'),
    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'google': os.getenv('GOOGLE_API_KEY')
}

# 키 로테이션
KEY_ROTATION_DAYS = 90
```

### 8.2 데이터 보호

```python
# 민감 데이터 마스킹
def mask_sensitive_data(data: str) -> str:
    # 학생 정보, 개인정보 제거
    return re.sub(r'[가-힣]{2,4}', '***', data)
```

## 9. 테스트 전략

### 9.1 단위 테스트

```python
# pytest 기반
def test_cycle_detection():
    relations = [
        {'src': 'A', 'dst': 'B'},
        {'src': 'B', 'dst': 'C'},
        {'src': 'C', 'dst': 'A'}  # 사이클
    ]
    cycles = detect_cycles(relations)
    assert len(cycles) == 1
    assert set(cycles[0]) == {'A', 'B', 'C'}
```

### 9.2 통합 테스트

```python
async def test_full_pipeline():
    # 작은 데이터셋으로 전체 파이프라인 테스트
    test_data = load_test_data()
    results = await run_pipeline(test_data)
    
    assert results['status'] == 'success'
    assert len(results['relations']) > 0
    assert results['quality_score'] > 60
```

## 10. 확장 계획

### 10.1 단기 (3개월)

- [ ] REST API 구현
- [ ] 웹 대시보드 개선
- [ ] 실시간 모니터링
- [ ] 자동 백업

### 10.2 중기 (6개월)

- [ ] GraphQL API
- [ ] 다른 교과목 확장
- [ ] 문항 자동 분류
- [ ] 학습 경로 추천

### 10.3 장기 (1년)

- [ ] AI 모델 파인튜닝
- [ ] 멀티테넌시 지원
- [ ] 국제화 (i18n)
- [ ] 클라우드 배포

---

*Last Updated: 2025-08-25*
*Version: 1.0.0*