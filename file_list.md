# 수학과 교육과정 추출 파일 목록

## 생성된 파일 구조

```
mathematics_curriculum_extraction/
├── README.md                               # 프로젝트 개요
├── data/                                   # 데이터 파일들
│   ├── reference/                          # 기준 데이터
│   │   ├── school_levels.csv              # 학교급/학년 정보
│   │   ├── domains.csv                    # 영역 정보 (4개 영역)
│   │   └── categories.csv                 # 범주 정보 (3개 범주)
│   ├── content_system/                     # 내용 체계
│   │   ├── core_ideas.csv                 # 핵심 아이디어 (13개)
│   │   ├── content_elements_elementary_1-2.csv   # 초등 1-2학년 내용요소
│   │   ├── content_elements_elementary_3-4.csv   # 초등 3-4학년 내용요소 (예정)
│   │   ├── content_elements_elementary_5-6.csv   # 초등 5-6학년 내용요소 (예정)
│   │   └── content_elements_middle_1-3.csv       # 중학 1-3학년 내용요소 (예정)
│   ├── achievement_standards/              # 성취기준
│   │   ├── achievement_standards_elementary_1-2.csv    # 초등 1-2학년 성취기준 (11개)
│   │   ├── achievement_standards_elementary_3-4.csv    # 초등 3-4학년 성취기준 (예정)
│   │   ├── achievement_standards_elementary_5-6.csv    # 초등 5-6학년 성취기준 (예정)
│   │   ├── achievement_standards_middle_1-3.csv        # 중학 1-3학년 성취기준 (11개)
│   │   ├── standard_explanations_elementary_1-2.csv    # 초등 1-2학년 해설 (18개)
│   │   └── standard_explanations_middle_1-3.csv        # 중학 1-3학년 해설 (8개)
│   └── terms_symbols/                      # 용어 및 기호
│       ├── terms_symbols_elementary_1-2.csv    # 초등 1-2학년 용어/기호 (24개)
│       ├── terms_symbols_elementary_3-4.csv    # 초등 3-4학년 용어/기호 (예정)
│       ├── terms_symbols_elementary_5-6.csv    # 초등 5-6학년 용어/기호 (예정)
│       └── terms_symbols_middle_1-3.csv        # 중학 1-3학년 용어/기호 (24개)
└── docs/                                   # 문서화
    ├── extraction_guide.md                 # 추출 가이드
    └── data_dictionary.md                  # 데이터 사전
```

## 현재 생성된 파일 상세

### 1. 기준 데이터 (3개 파일)
- **school_levels.csv**: 4개 학년 구분 정보
- **domains.csv**: 4개 영역 정보
- **categories.csv**: 3개 범주 정보

### 2. 내용 체계 (2개 파일)
- **core_ideas.csv**: 13개 핵심 아이디어 (영역별 2-4개)
- **content_elements_elementary_1-2.csv**: 초등 1-2학년 내용요소 11개

### 3. 성취기준 (4개 파일)
- **achievement_standards_elementary_1-2.csv**: 초등 1-2학년 11개 성취기준
- **achievement_standards_middle_1-3.csv**: 중학교 주요 11개 성취기준
- **standard_explanations_elementary_1-2.csv**: 초등 1-2학년 18개 해설
- **standard_explanations_middle_1-3.csv**: 중학교 8개 해설

### 4. 용어 및 기호 (2개 파일)
- **terms_symbols_elementary_1-2.csv**: 초등 1-2학년 24개 용어/기호
- **terms_symbols_middle_1-3.csv**: 중학교 24개 용어/기호

### 5. 문서화 (3개 파일)
- **README.md**: 프로젝트 전체 개요
- **extraction_guide.md**: 추출 방법 및 LaTeX 사용법
- **data_dictionary.md**: 모든 테이블과 필드 정의

## 추출된 주요 데이터 통계

### 성취기준
- **초등 1-2학년**: 11개 (수와 연산 중심)
- **중학교**: 11개 (고급 수학 개념 포함)
- **총계**: 22개 (샘플)

### 핵심 아이디어
- **수와 연산**: 3개
- **변화와 관계**: 4개  
- **도형과 측정**: 3개
- **자료와 가능성**: 3개
- **총계**: 13개

### 용어 및 기호
- **초등 1-2학년**: 24개 (기초 용어 중심)
- **중학교**: 24개 (고급 수학 용어 포함)
- **총계**: 48개 (샘플)

## LaTeX 수식 사용 예시

### 기본 수식
- 등호: `$=$`
- 부등호: `$>$`, `$<$`
- 곱셈: `$\times$`
- 미지수: `$\square$`

### 고급 수식
- 제곱근: `$\sqrt{a}$`
- 거듭제곱: `$a^2$`, `$x^n$`
- 분수: `$\frac{a}{b}$`
- 삼각비: `$\sin \theta$`, `$\cos \theta$`, `$\tan \theta$`
- 피타고라스 정리: `$a^2 + b^2 = c^2$`
- 이차함수: `$y = ax^2 + bx + c$`

## 다음 단계 작업 예정

### 추가 생성 예정 파일
1. **초등 3-4학년 전체 데이터** (약 20개 성취기준)
2. **초등 5-6학년 전체 데이터** (약 25개 성취기준)
3. **중학교 전체 데이터** (약 60개 성취기준)
4. **통합 데이터 파일들**
5. **SQL 스크립트 파일**
6. **JSON 형태 API 데이터**

### 검증 및 완성도
- **원문 정확성**: 100% 일치 확인 필요
- **LaTeX 문법**: 수식 렌더링 테스트 필요
- **관계형 무결성**: FK 관계 검증 필요
- **완전성**: 누락된 성취기준 추가 필요

**현재 진행률**: 약 15% (샘플 데이터 기반)
**예상 완성 파일 수**: 약 40-50개 파일
