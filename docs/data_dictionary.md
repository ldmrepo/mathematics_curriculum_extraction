# 데이터 사전 (Data Dictionary)

## 테이블 구조 및 필드 정의

### 1. school_levels.csv
학교급 및 학년 정보를 정의합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| level_id | INT | Y | 학년 구분 고유 ID | 1, 2, 3, 4 |
| school_type | VARCHAR(20) | Y | 학교급 | 초등학교, 중학교 |
| grade_range | VARCHAR(20) | Y | 학년 범위 | 1-2학년, 3-4학년 |
| grade_start | INT | Y | 시작 학년 | 1, 3, 5, 1 |
| grade_end | INT | Y | 종료 학년 | 2, 4, 6, 3 |
| level_code | INT | Y | 성취기준용 학년코드 | 2, 4, 6, 9 |

### 2. domains.csv
수학 교육과정의 4개 영역을 정의합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| domain_id | INT | Y | 영역 고유 ID | 1, 2, 3, 4 |
| domain_name | VARCHAR(50) | Y | 영역명 | 수와 연산, 변화와 관계 |
| domain_order | INT | Y | 영역 순서 | 1, 2, 3, 4 |
| domain_code | VARCHAR(2) | Y | 성취기준용 영역코드 | 01, 02, 03, 04 |

### 3. categories.csv
내용 체계의 3개 범주를 정의합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| category_id | INT | Y | 범주 고유 ID | 1, 2, 3 |
| category_name | VARCHAR(20) | Y | 범주명 | 지식·이해, 과정·기능, 가치·태도 |
| category_order | INT | Y | 범주 순서 | 1, 2, 3 |

### 4. core_ideas.csv
각 영역의 핵심 아이디어를 저장합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| idea_id | INT | Y | 핵심아이디어 고유 ID | 1, 2, 3... |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| idea_content | TEXT | Y | 핵심아이디어 내용 | 사물의 양은 자연수, 분수... |
| idea_order | INT | Y | 영역 내 순서 | 1, 2, 3 |

### 5. content_elements_*.csv
학년별 내용 요소를 저장합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| element_id | INT | Y | 내용요소 고유 ID | 1, 2, 3... |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| level_id | INT | Y | 학년 ID (FK) | 1, 2, 3, 4 |
| category_id | INT | Y | 범주 ID (FK) | 1, 2, 3 |
| element_name | VARCHAR(100) | Y | 내용요소명 | 네 자리 이하의 수 |
| element_description | TEXT | N | 내용요소 설명 | 0과 100까지의 수 개념... |
| element_order | INT | Y | 범주 내 순서 | 1, 2, 3... |

### 6. achievement_standards_*.csv
학년별 성취기준을 저장합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| standard_id | INT | Y | 성취기준 고유 ID | 1, 2, 3... |
| standard_code | VARCHAR(10) | Y | 성취기준 코드 | 2수01-01 |
| level_id | INT | Y | 학년 ID (FK) | 1, 2, 3, 4 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| element_id | INT | N | 내용요소 ID (FK) | 1, 2, 3... |
| standard_title | VARCHAR(100) | Y | 성취기준 제목 | 네 자리 이하의 수 |
| standard_content | TEXT | Y | 성취기준 내용 | 수의 필요성을 인식하면서... |
| standard_order | INT | Y | 내용요소 내 순서 | 1, 2, 3... |

### 7. standard_explanations_*.csv
성취기준별 해설 및 고려사항을 저장합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| explanation_id | INT | Y | 해설 고유 ID | 1, 2, 3... |
| standard_id | INT | Y | 성취기준 ID (FK) | 1, 2, 3... |
| explanation_type | VARCHAR(20) | Y | 해설 유형 | 성취기준 해설, 적용시 고려사항 |
| explanation_content | TEXT | Y | 해설 내용 | 덧셈은 두 자리 수의 범위에서... |

### 8. terms_symbols_*.csv
학년별 용어 및 기호를 저장합니다.

| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| term_id | INT | Y | 용어 고유 ID | 1, 2, 3... |
| level_id | INT | Y | 학년 ID (FK) | 1, 2, 3, 4 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| term_type | VARCHAR(10) | Y | 유형 | 용어, 기호 |
| term_name | VARCHAR(50) | Y | 용어/기호명 | 덧셈, $+$ |
| term_description | TEXT | N | 설명 | 두 수를 합하는 연산 |

## 관계형 구조

### 외래키 관계
- `content_elements.domain_id` → `domains.domain_id`
- `content_elements.level_id` → `school_levels.level_id`
- `content_elements.category_id` → `categories.category_id`
- `achievement_standards.level_id` → `school_levels.level_id`
- `achievement_standards.domain_id` → `domains.domain_id`
- `achievement_standards.element_id` → `content_elements.element_id`
- `standard_explanations.standard_id` → `achievement_standards.standard_id`
- `terms_symbols.level_id` → `school_levels.level_id`
- `terms_symbols.domain_id` → `domains.domain_id`

### 계층 구조
```
학교급/학년 (school_levels)
└── 영역 (domains)
    ├── 핵심아이디어 (core_ideas)
    ├── 내용요소 (content_elements)
    │   └── 성취기준 (achievement_standards)
    │       └── 해설 (standard_explanations)
    └── 용어/기호 (terms_symbols)
```

## 데이터 제약 조건

### 필수 제약사항
1. **성취기준 코드 유일성**: `standard_code`는 전체적으로 유일해야 함
2. **순서 일관성**: `*_order` 필드는 같은 그룹 내에서 연속적이어야 함
3. **외래키 무결성**: 모든 FK는 참조 테이블에 존재해야 함
4. **LaTeX 형식**: 수식은 유효한 LaTeX 문법이어야 함

### 권장 사항
1. **표준화된 용어 사용**: 교육과정 원문과 동일한 용어 사용
2. **일관된 수식 표기**: 같은 개념은 동일한 LaTeX 표기 사용
3. **완전한 데이터**: 가능한 모든 필드에 적절한 값 입력

## 예시 데이터

### 성취기준 예시
```csv
standard_id,standard_code,level_id,domain_id,element_id,standard_title,standard_content,standard_order
1,2수01-01,1,1,1,네 자리 이하의 수,"수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.",1
```

### 수식 포함 예시
```csv
term_name,term_description
"$\sqrt{a}$","음이 아닌 수 $a$의 양의 제곱근"
"$a^2 + b^2 = c^2$","피타고라스 정리 (직각삼각형에서)"
```
