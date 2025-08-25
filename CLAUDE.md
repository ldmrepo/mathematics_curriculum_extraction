# 수학 교육과정 지식 그래프 프로젝트

## 프로젝트 개요
2022 개정 수학과 교육과정을 기반으로 한 지식 그래프 구축 시스템입니다.
181개 성취기준과 843개 성취수준을 체계적으로 관리하고 AI 모델을 활용하여 관계를 분석합니다.

## 기술 스택
- **언어**: Python 3.8+
- **데이터베이스**: PostgreSQL 13+, Neo4j 4.4+
- **AI 모델**: OpenAI GPT-5, Anthropic Claude 4, Google Gemini 2.5
- **컨테이너**: Docker, Docker Compose
- **프레임워크**: Streamlit (대시보드)

## 프로젝트 구조
```
mathematics_curriculum_extraction/
├── data/                          # CSV 형태의 교육과정 데이터
│   ├── achievement_levels/        # 성취수준 데이터 (843개)
│   ├── achievement_standards/     # 성취기준 데이터 (181개)
│   ├── content_system/           # 내용 체계
│   └── terms_symbols/            # 용어 및 기호
├── database/                     # PostgreSQL 데이터베이스
│   ├── db/init/                 # 초기화 스크립트
│   └── scripts/                 # 데이터 로드 스크립트
├── knowledge_graph_project/      # AI 기반 지식 그래프
│   ├── src/                     # 핵심 소스 코드
│   └── config/                  # 설정 파일
└── docs/                        # 문서화

```

## 주요 명령어
```bash
# Docker 환경 실행
cd database && docker-compose up -d

# 데이터베이스 초기화
python database/scripts/data_load.py

# 지식 그래프 파이프라인 실행
cd knowledge_graph_project && python main.py

# 대시보드 실행
streamlit run knowledge_graph_project/dashboard.py
```

## 환경 변수 (.env)
- OPENAI_API_KEY: OpenAI API 키
- ANTHROPIC_API_KEY: Anthropic API 키  
- GOOGLE_API_KEY: Google AI API 키
- DATABASE_URL: PostgreSQL 연결 문자열
- NEO4J_URI: Neo4j 연결 URI

## 개발 규칙
1. 모든 데이터 변경은 CSV 파일 기준으로 관리
2. AI 모델 호출 시 캐싱 활용으로 비용 최적화
3. 테스트 코드 작성 필수
4. 타입 힌트 사용
5. Black 포맷터 적용

## 주요 작업 흐름
1. **데이터 추출**: PDF → CSV 변환 및 검증
2. **데이터베이스 구축**: CSV → PostgreSQL 임포트
3. **관계 분석**: AI 모델을 통한 성취기준 간 관계 추출
4. **지식 그래프 생성**: Neo4j에 노드와 엣지 구축
5. **검증 및 최적화**: 순환 참조 검사, 일관성 검증

## 프로젝트 목표
- 교육과정 데이터의 구조화 및 체계화
- AI 기반 자동 관계 추출 시스템 구축
- 교육 현장 활용 가능한 API 제공
- 문항 자동 분류 시스템 개발

## 현재 진행 상황
- ✅ 데이터베이스 스키마 v1.3.0 완성
- ✅ 초등/중등 전체 데이터 추출 완료
- 🔄 AI 모델 파이프라인 구축 중
- ⏳ Neo4j 지식 그래프 구현 예정

## 알려진 이슈
- Docker 환경에서 메모리 설정 필요 (최소 4GB)
- API 키 비용 최적화 필요
- 대량 데이터 처리 시 배치 처리 권장
