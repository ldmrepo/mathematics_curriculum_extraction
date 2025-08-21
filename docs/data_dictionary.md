# 데이터 사전 (Data Dictionary)
**버전**: 2.0.0  
**수정일**: 2025-01-21  
**기준**: 2022 개정 수학과 교육과정

## 📋 목차
1. [개요](#개요)
2. [테이블 구조](#테이블-구조)
3. [관계형 구조](#관계형-구조)
4. [데이터 제약조건](#데이터-제약조건)
5. [코드 체계](#코드-체계)
6. [예시 데이터](#예시-데이터)

## 개요

이 문서는 2022 개정 수학과 교육과정 데이터베이스의 구조와 각 필드의 정의를 설명합니다.

### 데이터 범위
- **학교급**: 초등학교, 중학교
- **학년**: 초1-2, 초3-4, 초5-6, 중1-3
- **영역**: 수와 연산, 변화와 관계, 도형과 측정, 자료와 가능성
- **성취기준**: 총 181개
- **용어 및 기호**: 총 685개

## 테이블 구조

### 1. 기준 테이블 (Reference Tables)

#### 1.1 school_levels (학교급/학년)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| level_id | INT | Y | 학년군 고유 ID | 1, 2, 3, 4 |
| school_type | VARCHAR(20) | Y | 학교급 | 초등학교, 중학교 |
| grade_range | VARCHAR(20) | Y | 학년 범위 | 1-2학년, 3-4학년 |
| grade_start | INT | Y | 시작 학년 | 1, 3, 5, 1 |
| grade_end | INT | Y | 종료 학년 | 2, 4, 6, 3 |
| level_code | INT | Y | 성취기준 코드용 | 2, 4, 6, 9 |

#### 1.2 domains (영역)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| domain_id | INT | Y | 영역 고유 ID | 1, 2, 3, 4 |
| domain_name | VARCHAR(50) | Y | 영역명 | 수와 연산 |
| domain_order | INT | Y | 영역 순서 | 1, 2, 3, 4 |
| domain_code | VARCHAR(2) | Y | 성취기준 코드용 | 01, 02, 03, 04 |
| description | TEXT | N | 영역 설명 | 수 개념과 연산 |

#### 1.3 categories (범주)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| category_id | INT | Y | 범주 고유 ID | 1, 2, 3 |
| category_name | VARCHAR(20) | Y | 범주명 | 지식·이해 |
| category_order | INT | Y | 범주 순서 | 1, 2, 3 |
| description | TEXT | N | 범주 설명 | 수학적 개념 이해 |

### 2. 내용 체계 테이블 (Content System Tables)

#### 2.1 core_ideas (핵심 아이디어)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| idea_id | INT | Y | 핵심아이디어 고유 ID | 1, 2, 3 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| idea_content | TEXT | Y | 핵심아이디어 내용 | 사물의 양은 자연수... |
| idea_order | INT | Y | 영역 내 순서 | 1, 2, 3 |

#### 2.2 content_elements (내용 요소)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| element_id | INT | Y | 내용요소 고유 ID | 1, 2, 3 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| level_id | INT | Y | 학년군 ID (FK) | 1, 2, 3, 4 |
| category_id | INT | Y | 범주 ID (FK) | 1, 2, 3 |
| element_name | VARCHAR(200) | Y | 내용요소명 | 네 자리 이하의 수 |
| element_description | TEXT | N | 내용요소 설명 | 0과 100까지의 수... |
| element_order | INT | Y | 범주 내 순서 | 1, 2, 3 |

#### 2.3 learning_elements (학습 요소)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| learning_id | INT | Y | 학습요소 고유 ID | 1, 2, 3 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| level_id | INT | Y | 학년군 ID (FK) | 1, 2, 3, 4 |
| category_id | INT | Y | 범주 ID (FK) | 1, 2, 3 |
| element_name | VARCHAR(200) | Y | 학습요소명 | 수 세기와 읽기 |
| element_description | TEXT | N | 학습요소 설명 | 구체물을 세고... |
| element_order | INT | Y | 범주 내 순서 | 1, 2, 3 |

### 3. 성취기준 테이블 (Achievement Standards Tables)

#### 3.1 achievement_standards (성취기준)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| standard_id | INT | Y | 성취기준 고유 ID | 1, 2, 3 |
| standard_code | VARCHAR(10) | Y | 성취기준 코드 | 2수01-01, 9수01-01 |
| level_id | INT | Y | 학년군 ID (FK) | 1, 2, 3, 4 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| element_id | INT | N | 내용요소 ID (FK) | 1, 2, 3 |
| standard_title | VARCHAR(200) | Y | 성취기준 제목 | 네 자리 이하의 수 |
| standard_content | TEXT | Y | 성취기준 내용 | 수의 필요성을... |
| standard_order | INT | Y | 영역 내 순서 | 1, 2, 3 |

#### 3.2 standard_explanations (성취기준 해설)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| explanation_id | INT | Y | 해설 고유 ID | 1, 2, 3 |
| standard_id | INT | N | 성취기준 ID (FK) | 1, 2, 3 |
| explanation_type | VARCHAR(30) | Y | 해설 유형 | 성취기준 해설, 적용시 고려사항, 용어와 기호 |
| explanation_content | TEXT | Y | 해설 내용 | 덧셈은 두 자리 수... |
| explanation_order | INT | Y | 유형별 순서 | 1, 2, 3 |

### 4. 용어 및 기호 테이블 (Terms and Symbols)

#### 4.1 terms_symbols (용어 및 기호)
| 필드명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| term_id | INT | Y | 용어 고유 ID | 1, 2, 3 |
| level_id | INT | Y | 학년군 ID (FK) | 1, 2, 3, 4 |
| domain_id | INT | Y | 영역 ID (FK) | 1, 2, 3, 4 |
| term_type | VARCHAR(10) | Y | 유형 | 용어, 기호 |
| term_name | VARCHAR(100) | Y | 용어/기호명 | 덧셈, + |
| term_description | TEXT | N | 설명 | 두 수를 합하는 연산 |
| latex_expression | TEXT | N | LaTeX 표현 | \sqrt{a} |

## 관계형 구조

### ERD (Entity Relationship Diagram)
```
school_levels (1) ─┬─ (N) content_elements
                   ├─ (N) learning_elements
                   ├─ (N) achievement_standards
                   └─ (N) terms_symbols

domains (1) ─┬─ (N) core_ideas
             ├─ (N) content_elements
             ├─ (N) learning_elements
             ├─ (N) achievement_standards
             └─ (N) terms_symbols

categories (1) ─┬─ (N) content_elements
                └─ (N) learning_elements

achievement_standards (1) ─── (N) standard_explanations
```

### 외래키 관계
```sql
-- 내용 요소
content_elements.domain_id → domains.domain_id
content_elements.level_id → school_levels.level_id
content_elements.category_id → categories.category_id

-- 학습 요소
learning_elements.domain_id → domains.domain_id
learning_elements.level_id → school_levels.level_id
learning_elements.category_id → categories.category_id

-- 성취기준
achievement_standards.level_id → school_levels.level_id
achievement_standards.domain_id → domains.domain_id
achievement_standards.element_id → content_elements.element_id (Optional)

-- 성취기준 해설
standard_explanations.standard_id → achievement_standards.standard_id (Optional)

-- 용어 및 기호
terms_symbols.level_id → school_levels.level_id
terms_symbols.domain_id → domains.domain_id
```

## 데이터 제약조건

### 필수 제약사항
1. **유일성 제약**
   - `standard_code`: 전체 테이블에서 유일
   - `(level_id, domain_id, term_name)`: terms_symbols에서 유일
   - `(domain_id, idea_order)`: core_ideas에서 유일

2. **형식 제약**
   - 성취기준 코드: `^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$`
   - level_code: 2, 4, 6, 9 중 하나
   - domain_code: 01, 02, 03, 04 중 하나

3. **참조 무결성**
   - 모든 외래키는 참조 테이블에 존재해야 함
   - 삭제 시 CASCADE 또는 SET NULL 규칙 적용

### 권장 사항
1. **데이터 일관성**
   - 같은 개념은 동일한 용어 사용
   - 순서 필드는 1부터 시작하는 연속된 정수

2. **LaTeX 표현**
   - 수식은 유효한 LaTeX 문법 준수
   - 복잡한 수식은 latex_expression 필드 활용

3. **설명 필드**
   - 명확하고 간결한 설명
   - 교육과정 원문과 일치

## 코드 체계

### 성취기준 코드 구조
```
[학년코드]수[영역코드]-[순번]

예시:
- 2수01-01: 초등 1-2학년, 수와 연산, 첫 번째 성취기준
- 4수02-03: 초등 3-4학년, 변화와 관계, 세 번째 성취기준
- 6수03-15: 초등 5-6학년, 도형과 측정, 15번째 성취기준
- 9수04-06: 중학교 1-3학년, 자료와 가능성, 6번째 성취기준
```

### 학년 코드
| 학년군 | level_code | 설명 |
|--------|------------|------|
| 초1-2 | 2 | 초등학교 2학년 기준 |
| 초3-4 | 4 | 초등학교 4학년 기준 |
| 초5-6 | 6 | 초등학교 6학년 기준 |
| 중1-3 | 9 | 중학교 3학년 기준 |

### 영역 코드
| 영역 | domain_code | 설명 |
|------|-------------|------|
| 수와 연산 | 01 | 수 개념과 연산 |
| 변화와 관계 | 02 | 규칙, 대응, 함수 |
| 도형과 측정 | 03 | 도형, 측정, 공간 |
| 자료와 가능성 | 04 | 통계와 확률 |

## 예시 데이터

### 성취기준 예시
```csv
standard_id,standard_code,level_id,domain_id,element_id,standard_title,standard_content,standard_order
1,2수01-01,1,1,1,네 자리 이하의 수,"수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.",1
122,9수01-01,4,1,54,소인수분해,"소인수분해의 뜻을 알고, 자연수를 소인수분해 할 수 있다.",1
```

### 성취기준 해설 예시
```csv
explanation_id,standard_id,explanation_type,explanation_content
1,87,성취기준 해설,"분수의 나눗셈은 '(분수)÷(자연수)', '(자연수)÷(분수)', '(분수)÷(분수)'를 다룬다."
13,0,용어와 기호,"'수와 연산' 영역에서는 용어와 기호로 '이상, 이하, 초과, 미만'을 다룬다."
```

### 용어 및 기호 예시
```csv
term_id,level_id,domain_id,term_type,term_name,term_description,latex_expression
201,4,1,용어,제곱근,어떤 수를 제곱하여 주어진 수가 되는 수,
214,4,1,기호,√a,a의 제곱근,\sqrt{a}
321,4,3,용어,피타고라스 정리,직각삼각형에서 빗변의 제곱은 나머지 두 변의 제곱의 합과 같다,a^2+b^2=c^2
```

### 수식 표현 예시
| 용어 | LaTeX | 렌더링 |
|------|-------|---------|
| 제곱근 | `\sqrt{a}` | √a |
| 분수 | `\frac{a}{b}` | a/b |
| 거듭제곱 | `a^{n}` | aⁿ |
| 삼각비 | `\sin\theta` | sin θ |
| 부등호 | `\leq, \geq` | ≤, ≥ |

## 데이터 통계 (2025-01-21 기준)

### 전체 레코드 수
| 테이블 | 레코드 수 |
|--------|-----------|
| school_levels | 4 |
| domains | 4 |
| categories | 3 |
| core_ideas | 16 |
| content_elements | 200+ |
| learning_elements | 150+ |
| achievement_standards | 181 |
| standard_explanations | 300+ |
| terms_symbols | 685 |

### 학년별 성취기준 분포
| 학년군 | 성취기준 수 | 비율 |
|--------|------------|------|
| 초1-2 | 29 | 16% |
| 초3-4 | 47 | 26% |
| 초5-6 | 45 | 25% |
| 중1-3 | 60 | 33% |
| **합계** | **181** | **100%** |

### 영역별 용어 분포
| 영역 | 용어 수 | 기호 수 | 합계 |
|------|---------|---------|------|
| 수와 연산 | 180 | 35 | 215 |
| 변화와 관계 | 85 | 15 | 100 |
| 도형과 측정 | 250 | 45 | 295 |
| 자료와 가능성 | 60 | 15 | 75 |
| **합계** | **575** | **110** | **685** |

## 데이터 품질 체크리스트

### 입력 시 확인사항
- [ ] 성취기준 코드 형식 준수
- [ ] 외래키 참조 유효성
- [ ] 필수 필드 입력 완료
- [ ] 순서 필드 연속성
- [ ] LaTeX 문법 유효성

### 검증 쿼리
```sql
-- 성취기준 코드 형식 검증
SELECT * FROM achievement_standards 
WHERE NOT (standard_code ~ '^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$');

-- 외래키 참조 검증
SELECT * FROM achievement_standards ast
LEFT JOIN school_levels sl ON ast.level_id = sl.level_id
WHERE sl.level_id IS NULL;

-- 순서 연속성 검증
SELECT domain_id, array_agg(idea_order ORDER BY idea_order) 
FROM core_ideas 
GROUP BY domain_id;
```

---
**작성자**: AI Assistant  
**최종 수정일**: 2025-01-21  
**문서 버전**: 2.0.0
