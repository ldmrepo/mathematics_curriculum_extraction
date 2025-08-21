# 2022 개정 수학과 교육과정 데이터베이스 프로젝트

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Education](https://img.shields.io/badge/교육과정-2022_개정-orange.svg)](https://www.moe.go.kr/)

## 📚 프로젝트 소개

2022 개정 수학과 교육과정의 구조화된 데이터베이스를 구축하는 프로젝트입니다. 교육과정 문서에서 체계적으로 데이터를 추출하여 재사용 가능한 형태로 제공합니다.

### 주요 특징
- 📊 **구조화된 데이터**: 181개 성취기준과 843개 성취수준 포함
- 🎯 **체계적 분류**: 4개 영역, 3개 범주로 내용 체계 구성
- 🔢 **완전한 커버리지**: 초등학교 1학년부터 중학교 3학년까지
- 💾 **다양한 형식 지원**: CSV, SQL, JSON 형식 제공
- 📖 **상세한 문서화**: 데이터 사전 및 활용 가이드 포함

## 🎓 대상 교육과정

### 학교급 및 학년
| 학교급 | 학년군 | 성취기준 수 | 성취수준 수 |
|--------|--------|------------|------------|
| 초등학교 | 1-2학년 | 29개 | 87개 |
| | 3-4학년 | 47개 | 141개 |
| | 5-6학년 | 45개 | 135개 |
| 중학교 | 1-3학년 | 60개 | 300개 |
| **합계** | | **181개** | **843개** |

### 내용 영역
1. **수와 연산** - 수 개념과 사칙연산
2. **변화와 관계** - 규칙성, 비례, 함수
3. **도형과 측정** - 평면도형, 입체도형, 측정
4. **자료와 가능성** - 통계와 확률

## 📁 프로젝트 구조

```
mathematics_curriculum_extraction/
│
├── 📂 data/                           # 데이터 파일
│   ├── 📄 school_levels.csv          # 학교급/학년 정보
│   ├── 📄 domains.csv                # 영역 정보
│   ├── 📄 categories.csv             # 범주 정보
│   ├── 📄 core_ideas.csv             # 핵심 아이디어
│   ├── 📄 content_elements_*.csv     # 내용 요소
│   ├── 📄 learning_elements_*.csv    # 학습 요소
│   ├── 📄 achievement_standards.csv  # 성취기준
│   ├── 📄 standard_explanations.csv  # 성취기준 해설
│   ├── 📄 terms_symbols_*.csv        # 용어 및 기호
│   └── 📂 achievement_levels/        # 성취수준
│       ├── 📄 *_elementary_1-2_*.csv
│       ├── 📄 *_elementary_3-4_*.csv
│       ├── 📄 *_elementary_5-6_*.csv
│       └── 📄 *_middle_*.csv
│
├── 📂 database/                       # 데이터베이스 설정
│   ├── 📄 schema.sql                 # 테이블 스키마
│   ├── 📄 constraints.sql            # 제약조건
│   └── 📄 import.sql                 # 데이터 임포트
│
├── 📂 docs/                          # 문서화
│   ├── 📄 data_dictionary.md        # 데이터 사전
│   ├── 📄 extraction_guide.md       # 추출 가이드
│   └── 📄 sample_queries.sql        # 예제 쿼리
│
├── 📂 scripts/                       # 유틸리티 스크립트
│   ├── 🐍 validate.py               # 데이터 검증
│   ├── 🐍 convert.py                # 형식 변환
│   └── 🐍 import_to_db.py          # DB 임포트
│
└── 📄 README.md                      # 프로젝트 설명서
```

## 🚀 빠른 시작

### 1. 프로젝트 클론
```bash
git clone https://github.com/yourusername/mathematics_curriculum_extraction.git
cd mathematics_curriculum_extraction
```

### 2. 데이터 검증
```bash
python scripts/validate.py data/
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL 데이터베이스 생성
createdb math_curriculum

# 스키마 생성
psql math_curriculum < database/schema.sql

# 데이터 임포트
python scripts/import_to_db.py
```

### 4. 데이터 활용
```sql
-- 초등학교 3-4학년 수와 연산 영역 성취기준 조회
SELECT * FROM achievement_standards 
WHERE level_id = 2 AND domain_id = 1
ORDER BY standard_order;

-- 특정 성취기준의 성취수준 조회
SELECT * FROM achievement_levels
WHERE standard_code = '[4수01-01]'
ORDER BY level_order;
```

## 📊 데이터 통계

### 전체 데이터 규모
- **성취기준**: 181개
- **성취수준**: 843개 (초등 363개, 중등 480개)
- **용어 및 기호**: 685개 (용어 575개, 기호 110개)
- **핵심 아이디어**: 16개
- **내용 요소**: 200개+
- **학습 요소**: 150개+

### 영역별 성취기준 분포
```
수와 연산: ████████████████ 56개 (31%)
변화와 관계: █████ 20개 (11%)
도형과 측정: ████████████████████████ 81개 (45%)
자료와 가능성: ██████ 24개 (13%)
```

## 🔧 기술 스택

- **데이터 형식**: CSV, JSON, SQL
- **데이터베이스**: PostgreSQL 13+
- **프로그래밍**: Python 3.8+
- **문서화**: Markdown
- **수식 표현**: LaTeX

## 📝 성취기준 코드 체계

### 코드 구조
```
[학년코드수영역코드-순번]

예시:
[2수01-01] = 초등 1-2학년 + 수와 연산 + 첫 번째 성취기준
[9수04-06] = 중학교 + 자료와 가능성 + 여섯 번째 성취기준
```

### 코드 매핑
| 학년군 | 코드 | 영역 | 코드 |
|--------|------|------|------|
| 초1-2 | 2 | 수와 연산 | 01 |
| 초3-4 | 4 | 변화와 관계 | 02 |
| 초5-6 | 6 | 도형과 측정 | 03 |
| 중1-3 | 9 | 자료와 가능성 | 04 |

## 🔬 수식 표기 예시

수학 기호와 수식은 LaTeX 형식으로 저장됩니다:

| 개념 | LaTeX | 렌더링 |
|------|-------|--------|
| 분수 | `\frac{a}{b}` | $\frac{a}{b}$ |
| 제곱근 | `\sqrt{a}` | $\sqrt{a}$ |
| 거듭제곱 | `a^{n}` | $a^{n}$ |
| 부등호 | `a \leq b` | $a \leq b$ |
| 피타고라스 | `a^2+b^2=c^2` | $a^2+b^2=c^2$ |

## 📖 문서

- **[데이터 사전](docs/data_dictionary.md)** - 테이블 구조와 필드 정의
- **[추출 가이드](docs/extraction_guide.md)** - 데이터 추출 방법론
- **[샘플 쿼리](docs/sample_queries.sql)** - 활용 예제
- **[데이터베이스 설정](database/DATABASE_SETUP_GUIDE_v1.1.md)** - DB 구축 가이드

## 🤝 기여하기

프로젝트 개선에 참여하실 수 있습니다:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 로드맵

- [x] 초등학교 교육과정 데이터 추출
- [x] 중학교 교육과정 데이터 추출
- [x] 성취수준 데이터 추가
- [ ] 고등학교 공통과목 추가
- [ ] API 서버 구축
- [ ] 웹 인터페이스 개발
- [ ] 교수학습 자료 연계

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

원본 교육과정 문서는 교육부 저작물로, 「공공누리 제1유형」 조건에 따라 이용 가능합니다.

## 🙏 감사의 글

- 교육부 - 2022 개정 교육과정 제공
- 한국교육과정평가원 - 교육과정 연구 자료
- 기여자 여러분 - 데이터 검증 및 개선

## 📞 연락처

프로젝트 관련 문의사항:
- 이슈 트래커: [GitHub Issues](https://github.com/yourusername/mathematics_curriculum_extraction/issues)
- 이메일: your.email@example.com

---

**최종 업데이트**: 2025-01-21  
**버전**: 2.1.0  
**상태**: 🟢 Active Development
