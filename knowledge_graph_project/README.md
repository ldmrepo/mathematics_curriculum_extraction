# 🧠 지식 그래프 구축 프로젝트

2025년 최신 AI 모델을 활용한 한국 수학 교육과정 지식 그래프 구축 프로젝트

## 📋 프로젝트 개요

본 프로젝트는 한국의 2022 개정 수학과 교육과정을 기반으로 지식 그래프를 구축하는 것을 목표로 합니다. 2025년 최신 AI 모델들(GPT-5, Claude 4, Gemini 2.5)을 활용하여 성취기준 간 관계를 자동으로 추출하고 분석합니다.

### 🎯 주요 목표
- 181개 성취기준과 843개 성취수준을 포함한 종합적 지식 그래프 구축
- AI 모델별 특성을 활용한 최적화된 처리 파이프라인 구현
- 교육적 맥락을 고려한 관계 추출 및 검증
- Neo4j 기반 그래프 데이터베이스 구축

## 🏗️ 프로젝트 구조

```
knowledge_graph_project/
├── src/                          # 소스 코드
│   ├── data_manager.py          # 데이터베이스 연결 및 데이터 추출
│   ├── ai_models.py             # AI 모델 인터페이스
│   ├── phase1_foundation.py     # Phase 1: 기반 구조 설계
│   ├── phase2_relationships.py  # Phase 2: 관계 추출
│   ├── phase3_refinement.py     # Phase 3: 고도화 정제
│   ├── phase4_validation.py     # Phase 4: 검증 최적화
│   └── neo4j_manager.py         # Neo4j 데이터베이스 관리
├── config/                      # 설정 파일
│   └── settings.py              # 프로젝트 설정
├── data/                        # 데이터 디렉토리
├── output/                      # 출력 결과 저장
├── logs/                        # 로그 파일
├── tests/                       # 테스트 파일
├── main.py                      # 메인 실행 파일
├── dashboard.py                 # Streamlit 대시보드
├── requirements.txt             # 패키지 의존성
└── README.md                    # 이 파일
```

## 🚀 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
`.env.example` 파일을 `.env`로 복사하고 다음 정보를 입력하세요:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mathematics_curriculum
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 3. 데이터베이스 설정
- PostgreSQL: 기존 교육과정 데이터베이스 연결
- Neo4j: 지식 그래프 저장용 (선택사항)

## 🤖 AI 모델 활용 전략

### Phase 1: Gemini 2.5 Pro ($1.25/$10)
- **역할**: 거시적 구조 설계
- **특징**: 1M 토큰 컨텍스트, 네이티브 멀티모달
- **담당**: 전체 노드 체계 설계, 커뮤니티 클러스터 정의

### Phase 2: GPT-5 ($1.25/$10)  
- **역할**: 효율적 대량 처리
- **특징**: 뛰어난 수학 성능 (94.6%), 비용 효율성
- **담당**: 성취기준 간 유사도 계산, 기본 관계 추출

### Phase 3: Claude Sonnet 4 ($3/$15)
- **역할**: 세밀한 관계 분석
- **특징**: 하이브리드 추론, 교육적 해석
- **담당**: 엣지 타입 세분화, 교육적 맥락 고려

### Phase 4: Claude Opus 4.1 ($15/$75)
- **역할**: 최종 검증 전문가
- **특징**: 최고 성능, 장시간 지속 작업
- **담당**: 전체 그래프 품질 검증, 일관성 검사

## 📊 실행 방법

### 1. 전체 파이프라인 실행
```bash
python main.py
```

### 2. 특정 단계부터 재개
```bash
python main.py --resume-from 2
```

### 3. 특정 단계만 실행
```bash
python main.py --phase-only 1
```

### 4. 대시보드 실행
```bash
streamlit run dashboard.py
```

## 💰 비용 최적화

### 캐싱 전략
- **Claude 모델**: 90% 할인 (프롬프트 캐싱)
- **OpenAI 모델**: 75% 할인 (프롬프트 캐싱)
- **배치 처리**: 추가 50% 할인

### 예상 비용
- **기본 예상**: $475
- **최적화 후**: $135 (71% 절감)
- **단계별 분배**: Phase 1 ($15) + Phase 2 ($50) + Phase 3 ($20) + Phase 4 ($50)

## 📈 예상 산출물

### 지식 그래프 구성 요소
- **노드**: 1,024개 (성취기준 181개 + 성취수준 843개)
- **엣지**: 2,500-4,000개 (12가지 관계 유형)
- **커뮤니티**: 80개 (3레벨 계층 구조)

### 관계 유형
1. **구조적 관계**: contains, belongs_to, part_of, has_level
2. **학습 순서 관계**: prerequisite, corequisite, follows, extends  
3. **의미적 관계**: similar_to, contrasts_with, applies_to, generalizes

### 품질 목표
- **분류 정확도**: >90%
- **커버리지**: 100% (모든 성취기준 연결)
- **일관성**: 순환 참조 0건
- **처리 시간**: <2초/쿼리

## 🔍 주요 기능

### 1. 적응형 복잡도 라우팅
```python
def adaptive_routing(problem_text):
    complexity = analyze_complexity(problem_text)
    
    if complexity < 0.3:  # 단순 문항
        return use_rule_based_classifier()
    elif complexity < 0.7:  # 중간 복잡도
        return use_hybrid_ensemble()
    else:  # 복잡한 문항
        return use_full_llm_pipeline()
```

### 2. 동적 학습 시스템
- 사용자 피드백으로 실시간 모델 개선
- 학교/지역별 출제 경향 학습
- 시간에 따른 교육과정 해석 변화 추적

### 3. 설명 가능한 분류 근거
```
분류 결과: [4수02-03] 비와 비율
근거:
1. 핵심 키워드: "비율", "백분율" 검출
2. 유사 문항 3개와 85% 일치
3. 선수 개념: 분수, 나눗셈 확인
4. 문제 구조: 비교 관계 표현
신뢰도: 92%
```

## 🛠️ 개발 가이드

### 코드 구조
```python
# AI 모델 사용 예시
ai_manager = AIModelManager()
result = await ai_manager.get_completion(
    model_name='claude_sonnet',
    prompt=analysis_prompt,
    thinking_budget=3000  # 확장된 사고 모드
)
```

### 데이터베이스 쿼리
```python
# PostgreSQL에서 데이터 추출
db_manager = DatabaseManager()
curriculum_data = db_manager.extract_all_curriculum_data()

# Neo4j에서 유사 표준 검색
neo4j_manager = Neo4jManager()
similar_standards = neo4j_manager.query_similar_standards("2수01-01")
```

### 배치 처리
```python
# GPT-5 배치 API 활용
batch_job = await openai_interface.create_batch_job(requests)
# 50% 비용 절감 효과
```

## 📊 모니터링 및 로깅

### 실시간 모니터링 지표
- API 응답 시간 (P50, P95, P99)
- 모델 정확도 트렌드
- 비용 추적 (모델별, 시간대별)
- 에러율 및 재시도율

### 알림 조건
- 정확도 하락 > 5%
- 응답 시간 > 2초
- 비용 급증 > 150%
- 에러율 > 1%

## 🧪 테스트

### 단위 테스트 실행
```bash
pytest tests/
```

### 통합 테스트
```bash
python -m pytest tests/integration/
```

### 성능 테스트
```bash
python tests/performance_test.py
```

## 📚 활용 시나리오

### 1. 교육 현장 활용
- **시험지 분석**: 교육과정 커버리지 분석
- **개인화 학습**: 학생별 취약점 진단
- **학습 경로 설계**: 최적 학습 순서 제안

### 2. 교육 콘텐츠 개발
- **문항 뱅크 관리**: 자동 태깅 시스템
- **출제 지원**: 균형잡힌 평가지 구성
- **품질 관리**: 교육과정 정합성 검증

### 3. 교육 연구 지원
- **빅데이터 분석**: 문항 트렌드 분석
- **국제 비교**: 교육과정 비교 연구
- **정책 지원**: 교육과정 개정 근거 제공

## 🚨 문제 해결

### 일반적인 문제들

#### 1. API 키 오류
```bash
# .env 파일 확인
cat .env
# API 키 유효성 검증
python -c "from config.settings import config; print(config.models)"
```

#### 2. 데이터베이스 연결 실패
```bash
# PostgreSQL 연결 테스트
python -c "from src.data_manager import DatabaseManager; db = DatabaseManager(); db.connect()"
```

#### 3. 메모리 부족
```bash
# 배치 크기 줄이기
export BATCH_SIZE=20
python main.py
```

#### 4. 비용 초과
```bash
# 비용 한도 설정
export MAX_DAILY_COST=100
python main.py
```

### 로그 확인
```bash
# 최신 로그 확인
tail -f logs/knowledge_graph_*.log

# 에러 로그 필터링
grep "ERROR" logs/knowledge_graph_*.log
```

## 🤝 기여 가이드

### 코드 스타일
- Black 포맷터 사용
- Type hints 필수
- Docstring 작성

### 커밋 메시지
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 업데이트
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
```

### Pull Request
1. 기능 브랜치 생성
2. 테스트 작성 및 실행
3. 문서 업데이트
4. PR 생성 및 리뷰 요청

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

### 문의 채널
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Discussion**: 일반적인 질문 및 토론
- **Email**: 긴급 문의 및 지원

### FAQ

**Q: Neo4j 없이도 실행 가능한가요?**
A: 네, Neo4j는 선택사항입니다. JSON 파일로도 결과를 저장할 수 있습니다.

**Q: 다른 교과목에도 적용 가능한가요?**
A: 네, 구조를 수정하여 다른 교과목에도 적용 가능합니다.

**Q: 비용을 더 절약할 수 있는 방법이 있나요?**
A: 캐싱 활용, 배치 처리, 오픈소스 모델 혼용을 통해 추가 절약 가능합니다.

**Q: 실시간 업데이트가 가능한가요?**
A: 네, 새로운 교육과정이 추가되면 점진적 업데이트가 가능합니다.

---

## 🎉 성공 사례

이 시스템을 통해 달성할 수 있는 교육적 가치:
- 교사의 문항 분류 시간 50% 절감
- 평가 품질 개선 효과
- 맞춤형 학습 실현
- 교육과정 일관성 향상

**프로젝트가 성공적으로 완료되면 한국 수학 교육의 디지털 전환에 중요한 기여를 할 것입니다.**
