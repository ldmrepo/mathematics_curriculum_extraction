# Claude Code 환경 설정 가이드

## 🚀 빠른 시작

### 1. 초기 설정
```bash
# 실행 권한 부여
chmod +x init_claude_code.sh

# 초기화 스크립트 실행
./init_claude_code.sh

# Claude Code 시작
claude
```

### 2. Claude Code 내에서 초기화
```bash
# Claude Code 실행 후
/init

# 프로젝트 이해도 확인
"이 프로젝트의 목적은 무엇인가요?"
"어떤 데이터를 다루고 있나요?"
```

## 📂 프로젝트 구조

```
.claude/
├── settings.json         # 환경 설정
├── agents/              # 서브에이전트 (8개)
│   ├── curriculum-analyst.md
│   ├── database-architect.md
│   ├── ai-pipeline-engineer.md
│   ├── knowledge-graph-specialist.md
│   ├── python-data-engineer.md
│   ├── test-quality-engineer.md
│   ├── devops-docker-specialist.md
│   └── math-problem-classifier.md
└── commands/            # 커스텀 명령어 (6개)
    ├── init-database.md
    ├── run-pipeline.md
    ├── validate-data.md
    ├── analyze-graph.md
    ├── run-tests.md
    └── extract-relations.md
```

## 🤖 서브에이전트 활용

### 자동 호출
Claude Code가 작업 내용에 따라 자동으로 적절한 서브에이전트를 선택합니다.

### 명시적 호출
```
"curriculum-analyst를 사용해서 초등 3-4학년 분수 관련 성취기준을 분석해줘"
"database-architect로 쿼리 성능을 최적화해줘"
"ai-pipeline-engineer를 통해 API 비용을 계산해줘"
```

## 📝 커스텀 명령어

| 명령어 | 설명 | 사용 예시 |
|--------|------|-----------|
| `/init-database` | DB 초기화 및 데이터 로드 | `/init-database` |
| `/run-pipeline` | AI 파이프라인 실행 | `/run-pipeline --dry-run` |
| `/validate-data` | 데이터 품질 검증 | `/validate-data` |
| `/analyze-graph` | 지식 그래프 분석 | `/analyze-graph community` |
| `/run-tests` | 테스트 실행 | `/run-tests unit` |
| `/extract-relations` | 관계 추출 | `/extract-relations [2수01-01]` |

## 🔧 환경 설정 특징

### 권한 관리
- ✅ Docker, Python, Git 명령 허용
- ❌ .env 파일 접근 차단 (보안)
- ❌ 위험한 명령 차단 (rm -rf /)

### 자동화 Hook
- Python 파일 저장 시 Black 포맷터 자동 실행
- requirements.txt 변경 시 알림
- Docker 설정 변경 시 재시작 안내

### 프로젝트 설정
- 성취기준: 181개
- 성취수준: 843개
- 용어/기호: 685개
- AI 모델: GPT-5, Claude 4, Gemini 2.5

## 📊 주요 작업 흐름

### 1. 데이터 검증
```bash
/validate-data
# 또는
"데이터 품질을 종합적으로 검증해줘"
```

### 2. 관계 분석
```bash
/extract-relations [2수01-01]
# 또는
"초등 1-2학년 수와 연산 영역의 관계를 분석해줘"
```

### 3. AI 파이프라인
```bash
# 비용 시뮬레이션
/run-pipeline --dry-run

# 실제 실행
/run-pipeline
```

### 4. 결과 시각화
```bash
streamlit run knowledge_graph_project/dashboard.py
```

## 🐳 Docker 관리

### 서비스 시작/중지
```bash
./docker-manage.sh start   # 시작
./docker-manage.sh stop    # 중지
./docker-manage.sh restart # 재시작
./docker-manage.sh health  # 상태 확인
```

### 백업/복원
```bash
./docker-manage.sh backup          # 백업
./docker-manage.sh restore backup.sql  # 복원
```

## 🧪 테스트

### 전체 테스트
```bash
/run-tests
```

### 특정 테스트
```bash
pytest tests/test_knowledge_graph.py -v
```

### 커버리지 확인
```bash
pytest --cov=src --cov-report=html
```

## 💰 비용 최적화

### 예상 비용
- 기본: $475
- 최적화 후: $135 (71% 절감)

### 최적화 전략
1. 프롬프트 캐싱 (90% 할인)
2. 배치 처리 (50% 할인)
3. 적응형 라우팅 (복잡도별 모델 선택)

## 🚨 문제 해결

### API 키 설정
```bash
# .env 파일 확인
cat .env

# 필요한 키:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - GOOGLE_API_KEY
```

### 데이터베이스 연결
```bash
# PostgreSQL 상태
docker exec math_curriculum_db pg_isready

# Neo4j 상태
curl http://localhost:7474
```

### 메모리 부족
```bash
# Docker 메모리 할당 증가 (최소 4GB)
docker update --memory="4g" math_curriculum_db
```

## 📚 추가 문서

- [프로젝트 개요](README.md)
- [데이터 설명서](docs/수학과_교육과정_데이터_설명서_v_1.md)
- [설정 완료 보고서](CLAUDE_CODE_SETUP_REPORT.md)

## 🤝 지원

문제가 발생하면:
1. `/validate-data`로 데이터 검증
2. `/run-tests`로 시스템 테스트
3. `./docker-manage.sh health`로 서비스 상태 확인

Claude Code가 자동으로 적절한 서브에이전트를 활용하여 문제를 해결합니다.