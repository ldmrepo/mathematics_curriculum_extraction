# Knowledge Graph Project 실행 가이드

## 📌 프로젝트 개요

2022 개정 수학과 교육과정을 기반으로 AI 모델을 활용하여 지식 그래프를 구축하는 프로젝트입니다.

- **성취기준**: 181개
- **성취수준**: 663개
- **AI 모델**: GPT-5, Claude 4, Gemini 2.5 Pro
- **데이터베이스**: PostgreSQL 16 + Neo4j 4.4

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     PostgreSQL DB                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ achievement  │  │   v1.3.0     │  │    Core      │  │
│  │  standards   │  │    Views     │  │   Tables     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Manager                          │
│         Extract & Process Curriculum Data                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  AI Pipeline Phases                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Phase 1  │→ │ Phase 2  │→ │ Phase 3  │→ │Phase 4 │ │
│  │ Gemini   │  │  GPT-5   │  │ Sonnet 4 │  │Opus 4.1│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      Neo4j Graph                         │
│              Knowledge Graph Database                    │
└─────────────────────────────────────────────────────────┘
```

## 🚀 실행 준비

### 1. 환경 요구사항

- **Python**: 3.8 이상
- **Docker**: 20.10 이상
- **메모리**: 최소 8GB RAM
- **디스크**: 10GB 여유 공간

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
# AI API Keys
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=xxx

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mathematics_curriculum
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123

# Cost Control
MAX_DAILY_COST=200.0
COST_ALERT_THRESHOLD=150.0
BATCH_SIZE=10
MAX_CONCURRENT_REQUESTS=5
```

### 3. 의존성 설치

```bash
cd knowledge_graph_project
pip install -r requirements.txt
```

### 4. 데이터베이스 준비

```bash
# PostgreSQL 시작
cd ../database
docker-compose up -d

# 데이터 로드 확인
docker exec curriculum-postgres psql -U postgres -d mathematics_curriculum \
  -c "SELECT COUNT(*) FROM curriculum.achievement_standards;"
# Expected: 181
```

## 📊 실행 단계별 상세

### Phase 0: 데이터 추출

**목적**: PostgreSQL에서 모든 교육과정 데이터 추출

```python
from src.data_manager import DatabaseManager

db_manager = DatabaseManager()
curriculum_data = db_manager.extract_all_curriculum_data()
```

**추출 데이터**:
- `achievement_standards`: 181개 성취기준
- `achievement_levels`: 663개 성취수준
- `content_elements`: 291개 내용요소
- `terms_symbols`: 362개 용어/기호
- `prerequisite_suggestions`: 선수학습 제안 (v1.3.0 뷰)
- `horizontal_suggestions`: 수평 관계 제안 (v1.3.0 뷰)
- `competencies`: 5개 교과 역량
- `representation_types`: 9개 표상 타입

### Phase 1: 기초 구조 설계 (Gemini 2.5 Pro)

**목적**: 지식 그래프의 전체 구조 설계

**처리 내용**:
1. 노드 타입 정의
   - AchievementStandard (성취기준)
   - AchievementLevel (성취수준)
   - Domain (수학 영역)
   - GradeLevel (학년군)
   - Competency (교과 역량)
   - RepresentationType (표상 타입)

2. 관계 카테고리 설계
   - 구조적 관계
   - 학습 순서 관계
   - 의미적 관계

3. 커뮤니티 클러스터 정의
4. 계층 구조 설계

**비용**: $1-2 (Gemini 2.5 Pro, 1M context)

### Phase 2: 관계 추출 (GPT-5)

**목적**: 성취기준 간 관계 추출

**처리 내용**:
1. **DB 제안 활용** (규칙 기반)
   - prerequisite_suggestions → 선수학습 관계
   - horizontal_suggestions → 수평 관계

2. **AI 추가 추출**
   - 유사도 관계 (similarity)
   - 영역 간 연결 (domain_bridge)
   - 학년 진행 관계 (grade_progression)

**최적화**:
- 배치 크기: 10개씩 처리
- 도메인별 그룹화로 효율성 향상
- DB 제안 우선 활용으로 API 호출 최소화

**비용**: $3-5 (GPT-5)

### Phase 3: 관계 정제 (Claude Sonnet 4)

**목적**: 추출된 관계 정제 및 교육적 메타데이터 추가

**처리 내용**:
1. **관계 타입 세분화**
   ```
   prerequisite → prerequisite_conceptual (개념적)
                → prerequisite_procedural (절차적)
                → prerequisite_cognitive (인지적)
   ```

2. **가중치 조정**
   - 교육적 중요도 반영
   - 학습 필수도 고려

3. **교육 메타데이터 추가**
   - 난이도 전이 (easy→medium)
   - 인지 수준 (기억, 이해, 적용, 분석)
   - 교수 전략 (직접교수, 탐구학습)
   - 평가 방법 (지필평가, 수행평가)

4. **누락 관계 식별**
5. **중복/충돌 해결**

**비용**: $2-3 (Claude Sonnet 4, thinking_budget: 3000)

### Phase 4: 검증 및 최적화 (Claude Opus 4.1)

**목적**: 전체 그래프 검증 및 품질 평가

**처리 내용**:
1. **사이클 검출**
   - DFS 알고리즘으로 순환 참조 검출
   - DB 함수 `detect_prerequisite_cycles()` 활용

2. **일관성 검증**
   - 구조적 완전성 (고립 노드, 연결성)
   - 교육적 타당성 (교육과정 준수)
   - 논리적 일관성 (모순 관계)

3. **커버리지 분석**
   - 노드 커버리지: 181개 성취기준
   - 관계 커버리지: 예상 대비 실제

4. **품질 평가**
   ```json
   {
     "completeness": 18/25,
     "accuracy": 19/25,
     "usability": 17/25,
     "innovation": 16/25,
     "total_score": 70/100,
     "grade": "B"
   }
   ```

5. **최적화 권장사항**

**비용**: $5-7 (Claude Opus 4.1, thinking_budget: 10000)

### Phase 5: Neo4j 그래프 구축

**목적**: 최종 지식 그래프 데이터베이스 구축

**처리 내용**:
1. 노드 생성
2. 관계 생성
3. 인덱스 생성
4. 제약조건 설정

**쿼리 예시**:
```cypher
// 선수학습 체인 조회
MATCH path = (start:AchievementStandard)-[:PREREQUISITE*1..5]->(end:AchievementStandard {code: $code})
RETURN path

// 유사 성취기준 조회
MATCH (s1:AchievementStandard {code: $code})-[r:SIMILAR_TO]-(s2:AchievementStandard)
RETURN s2.code, r.weight
ORDER BY r.weight DESC
```

## 💻 실행 명령어

### 전체 파이프라인 실행

```bash
cd knowledge_graph_project
python main.py
```

### 특정 단계부터 재시작

```bash
# Phase 3부터 재시작
python main.py --resume-from 3
```

### 개별 단계만 실행

```bash
# Phase 2만 실행
python main.py --phase-only 2
```

### 대시보드 실행

```bash
streamlit run dashboard.py
```

## 📈 예상 성능 지표

| 지표 | 목표 | 현재 |
|------|------|------|
| 성취기준 커버리지 | 100% | 100% |
| 관계 정확도 | 85% | 75% |
| 사이클 없음 | Yes | Yes |
| 처리 시간 | <30분 | 15-22분 |
| API 비용 | <$20 | $11-17 |

## 📁 출력 파일

```
output/
├── curriculum_data.json           # 추출된 데이터
├── phase1_foundation_design.json  # 구조 설계
├── phase2_relationship_extraction.json  # 관계 추출
├── phase3_refinement_results.json # 정제 결과
├── phase4_validation_results.json # 검증 결과
├── graph_statistics.json          # 그래프 통계
├── final_report.json              # 최종 보고서
└── executive_summary.md           # 요약 보고서
```

## 🔍 모니터링

### 로그 확인

```bash
tail -f logs/knowledge_graph_*.log
```

### 비용 모니터링

로그에서 비용 추적:
```
Phase 1 Usage Stats: {'total_cost': 1.25, ...}
Phase 2 Usage Stats: {'total_cost': 3.50, ...}
```

### 진행 상황 확인

```bash
# PostgreSQL 상태
docker exec curriculum-postgres psql -U postgres -d mathematics_curriculum \
  -c "SELECT COUNT(*) FROM curriculum.achievement_standard_relations;"

# Neo4j 상태
curl http://localhost:7474/db/data/
```

## ⚠️ 문제 해결

### API 키 오류
```
Error: Invalid API key
```
**해결**: `.env` 파일의 API 키 확인

### 메모리 부족
```
Error: Out of memory
```
**해결**: Docker 메모리 할당 증가 (최소 4GB)

### 사이클 검출
```
Warning: Found cycles in prerequisite relationships
```
**해결**: Phase 4에서 자동으로 사이클 제거 제안

### 비용 한도 초과
```
Error: Daily cost limit exceeded
```
**해결**: `MAX_DAILY_COST` 증가 또는 다음날 재실행

## 📞 지원

- **GitHub Issues**: https://github.com/your-repo/issues
- **Documentation**: https://docs.your-project.com
- **Email**: support@your-project.com

---

*Last Updated: 2025-08-25*
*Version: 1.0.0*