# 수학과 교육과정 데이터 추출 가이드

**버전**: 2.0.0  
**수정일**: 2025-01-21  
**기준**: 2022 개정 수학과 교육과정

## 📋 목차
1. [개요](#개요)
2. [데이터 구조](#데이터-구조)
3. [추출 절차](#추출-절차)
4. [데이터 형식](#데이터-형식)
5. [검증 방법](#검증-방법)
6. [자동화 도구](#자동화-도구)
7. [문제 해결](#문제-해결)

## 개요

이 가이드는 2022 개정 수학과 교육과정 문서에서 구조화된 데이터를 추출하는 방법을 설명합니다.

### 목적
- 교육과정 PDF 문서를 구조화된 CSV 형식으로 변환
- 데이터베이스 적재를 위한 표준 형식 유지
- 데이터 일관성과 정확성 보장

### 범위
- **학교급**: 초등학교, 중학교
- **데이터 유형**: 
  - 내용 체계 (핵심 아이디어, 내용 요소, 학습 요소)
  - 성취기준 및 해설
  - 용어와 기호

## 데이터 구조

### 계층 구조
```
교육과정
├── 학교급 (초등/중학교)
│   ├── 학년군 (1-2, 3-4, 5-6, 중1-3)
│   │   ├── 영역 (4개)
│   │   │   ├── 핵심 아이디어
│   │   │   ├── 내용 요소 (3개 범주)
│   │   │   ├── 학습 요소 (3개 범주)
│   │   │   ├── 성취기준
│   │   │   │   └── 해설 및 고려사항
│   │   │   └── 용어와 기호
```

### 파일 구조
```
data/
├── reference/               # 기준 데이터
│   ├── school_levels.csv
│   ├── domains.csv
│   └── categories.csv
├── content_system/          # 내용 체계
│   ├── core_ideas.csv
│   ├── content_elements_*.csv
│   └── learning_elements_*.csv
├── achievement_standards/   # 성취기준
│   ├── achievement_standards_*.csv
│   └── standard_explanations_*.csv
└── terms_symbols/          # 용어와 기호
    └── terms_symbols_*.csv
```

## 추출 절차

### 1단계: 문서 준비
1. 교육과정 PDF 파일 확보
2. PDF를 텍스트로 변환 (OCR 필요시)
3. 페이지별로 섹션 구분

### 2단계: 기준 데이터 설정
```csv
# school_levels.csv 예시
level_id,school_type,grade_range,grade_start,grade_end,level_code
1,초등학교,1-2학년,1,2,2
2,초등학교,3-4학년,3,4,4
3,초등학교,5-6학년,5,6,6
4,중학교,1-3학년,1,3,9
```

### 3단계: 내용 체계 추출

#### 3.1 핵심 아이디어
- **위치**: 각 영역의 시작 부분
- **형식**: 문장 형태의 설명
- **추출 방법**:
  ```python
  # 예시 패턴
  pattern = r"핵심 아이디어\s*([가-힣\s,.\(\)]+)"
  ```

#### 3.2 내용 요소
- **위치**: 내용 체계 표의 첫 번째 섹션
- **범주**: 지식·이해
- **추출 항목**:
  - 영역별 주요 개념
  - 학년별 세부 내용

#### 3.3 학습 요소
- **위치**: 내용 체계 표의 두 번째, 세 번째 섹션
- **범주**: 과정·기능, 가치·태도
- **추출 항목**:
  - 수학적 과정과 기능
  - 태도와 가치관

### 4단계: 성취기준 추출

#### 4.1 성취기준 코드 패턴
```regex
^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$

예시:
- 2수01-01: 초등 1-2학년, 수와 연산, 첫 번째
- 9수04-06: 중학교, 자료와 가능성, 여섯 번째
```

#### 4.2 성취기준 구조
```csv
# achievement_standards_elementary_1-2.csv 예시
standard_id,standard_code,level_id,domain_id,element_id,standard_title,standard_content,standard_order
1,2수01-01,1,1,1,네 자리 이하의 수,"수의 필요성을 인식하면서...",1
```

#### 4.3 성취기준 해설
- **유형**: 
  - 성취기준 해설
  - 적용시 고려사항
  - 용어와 기호 (영역별)
- **매칭**: standard_id로 연결 (용어와 기호는 NULL)

### 5단계: 용어와 기호 추출

#### 5.1 추출 위치
- 각 학년군 성취기준 해설의 마지막 부분
- "용어와 기호" 섹션

#### 5.2 분류 방법
```python
def classify_term(text):
    if any(symbol in text for symbol in ['+', '-', '×', '÷', '=', '<', '>']):
        return '기호'
    elif text.startswith('$') or '\\' in text:
        return '기호'  # LaTeX
    else:
        return '용어'
```

#### 5.3 LaTeX 처리
```python
# 특수 기호 매핑
latex_map = {
    '√': r'\sqrt{}',
    '≤': r'\leq',
    '≥': r'\geq',
    '≠': r'\neq',
    '∈': r'\in',
    '∉': r'\notin'
}
```

## 데이터 형식

### CSV 인코딩
- **문자 인코딩**: UTF-8 (BOM 없음)
- **구분자**: 쉼표 (,)
- **인용 부호**: 큰따옴표 (")
- **줄 바꿈**: LF (\n)

### 필드 규칙

#### 텍스트 필드
- 앞뒤 공백 제거
- 줄 바꿈은 공백으로 치환
- 큰따옴표는 이스케이프 ("")

#### 숫자 필드
- 정수만 사용 (소수점 없음)
- NULL은 빈 문자열로 표현

#### 외래키
- 참조 테이블에 반드시 존재
- 0은 사용하지 않음 (NULL 사용)

### 예시 데이터

#### 올바른 형식
```csv
1,2수01-01,1,1,1,"네 자리 이하의 수","수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.",1
```

#### 잘못된 형식
```csv
1, 2수01-01 ,1,1,1,네 자리 이하의 수,수의 필요성을 인식하면서
0과 100까지의 수 개념을 이해하고,
수를 세고 읽고 쓸 수 있다.,1
```

## 검증 방법

### 1. 데이터 완전성 검증

#### 성취기준 개수 확인
| 학년군 | 예상 개수 | 허용 범위 |
|--------|----------|-----------|
| 초1-2 | 29 | ±2 |
| 초3-4 | 47 | ±3 |
| 초5-6 | 45 | ±3 |
| 중1-3 | 60 | ±5 |

#### 용어 개수 확인
| 학년군 | 최소 개수 |
|--------|----------|
| 초1-2 | 30 |
| 초3-4 | 100 |
| 초5-6 | 150 |
| 중1-3 | 300 |

### 2. 형식 검증

#### Python 검증 스크립트
```python
import pandas as pd
import re

def validate_achievement_standards(file_path):
    df = pd.read_csv(file_path)
    
    # 성취기준 코드 형식 검증
    pattern = r'^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$'
    invalid_codes = df[~df['standard_code'].str.match(pattern)]
    
    if not invalid_codes.empty:
        print(f"잘못된 코드: {invalid_codes['standard_code'].tolist()}")
    
    # 중복 검증
    duplicates = df[df.duplicated(['standard_code'])]
    if not duplicates.empty:
        print(f"중복 코드: {duplicates['standard_code'].tolist()}")
    
    # 순서 연속성 검증
    for domain_id in df['domain_id'].unique():
        domain_df = df[df['domain_id'] == domain_id]
        orders = sorted(domain_df['standard_order'].tolist())
        expected = list(range(1, len(orders) + 1))
        if orders != expected:
            print(f"Domain {domain_id}: 순서 불연속")
    
    return len(invalid_codes) == 0 and duplicates.empty

# 사용 예시
is_valid = validate_achievement_standards('achievement_standards_elementary_1-2.csv')
```

### 3. 참조 무결성 검증

#### SQL 검증 쿼리
```sql
-- 외래키 참조 검증
SELECT COUNT(*) as orphan_count
FROM achievement_standards ast
LEFT JOIN school_levels sl ON ast.level_id = sl.level_id
WHERE sl.level_id IS NULL;

-- 결과가 0이어야 정상
```

## 자동화 도구

### 1. PDF 텍스트 추출
```python
import PyPDF2
import pdfplumber

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
```

### 2. 성취기준 파서
```python
class AchievementStandardParser:
    def __init__(self):
        self.pattern = re.compile(
            r'([0-9]{1,2}수[0-9]{2}-[0-9]{2})\s+'
            r'(.+?)\s+'
            r'([가-힣].+?)(?=[0-9]{1,2}수|$)',
            re.DOTALL
        )
    
    def parse(self, text):
        standards = []
        for match in self.pattern.finditer(text):
            standards.append({
                'standard_code': match.group(1),
                'standard_title': self.extract_title(match.group(2)),
                'standard_content': self.clean_content(match.group(3))
            })
        return standards
    
    def extract_title(self, text):
        # 제목 추출 로직
        lines = text.strip().split('\n')
        return lines[0] if lines else ""
    
    def clean_content(self, text):
        # 내용 정리 로직
        return ' '.join(text.split())
```

### 3. 배치 처리 스크립트
```bash
#!/bin/bash
# process_all.sh

# 디렉토리 설정
DATA_DIR="./data"
OUTPUT_DIR="./output"

# 학년별 처리
for grade in "elementary_1-2" "elementary_3-4" "elementary_5-6" "middle_1-3"; do
    echo "Processing $grade..."
    
    # 성취기준 추출
    python extract_standards.py \
        --input "$DATA_DIR/raw/$grade.txt" \
        --output "$OUTPUT_DIR/achievement_standards_$grade.csv"
    
    # 용어 추출
    python extract_terms.py \
        --input "$DATA_DIR/raw/$grade.txt" \
        --output "$OUTPUT_DIR/terms_symbols_$grade.csv"
    
    # 검증
    python validate.py "$OUTPUT_DIR/*_$grade.csv"
done

echo "Complete!"
```

## 문제 해결

### 일반적인 문제

#### 1. 인코딩 오류
**문제**: UnicodeDecodeError 발생  
**해결**:
```python
# UTF-8로 저장
df.to_csv('file.csv', encoding='utf-8', index=False)

# 읽을 때도 UTF-8 지정
df = pd.read_csv('file.csv', encoding='utf-8')
```

#### 2. 줄 바꿈 처리
**문제**: 텍스트에 줄 바꿈이 포함됨  
**해결**:
```python
# 줄 바꿈을 공백으로 치환
text = text.replace('\n', ' ').replace('\r', '')
```

#### 3. 특수 문자 처리
**문제**: 수식이나 특수 기호 깨짐  
**해결**:
```python
# 특수 문자 매핑
special_chars = {
    '²': '^2',
    '³': '^3',
    '°': '도',
    '·': '·'
}

for old, new in special_chars.items():
    text = text.replace(old, new)
```

#### 4. 외래키 불일치
**문제**: 참조 테이블에 키가 없음  
**해결**:
1. 기준 데이터 먼저 로드
2. 참조 관계 확인
3. 누락된 데이터 추가

### 데이터 품질 체크리스트

- [ ] 모든 성취기준 코드가 유일한가?
- [ ] 코드 형식이 정규식과 일치하는가?
- [ ] 외래키가 모두 유효한가?
- [ ] 순서 필드가 연속적인가?
- [ ] 텍스트 필드에 불필요한 공백이 없는가?
- [ ] LaTeX 표현이 유효한가?
- [ ] 인코딩이 UTF-8인가?
- [ ] 파일명이 규칙을 따르는가?

## 추가 리소스

### 관련 문서
- [데이터 사전](data_dictionary.md)
- [샘플 쿼리](sample_queries.sql)
- [데이터베이스 설정 가이드](../database/DATABASE_SETUP_GUIDE_v1.1.md)

### 유용한 도구
- **PDF 처리**: pdfplumber, PyPDF2
- **데이터 처리**: pandas, numpy
- **검증**: pytest, schema
- **데이터베이스**: PostgreSQL, psycopg2

### 참고 자료
- [2022 개정 교육과정 총론](https://www.moe.go.kr/)
- [수학과 교육과정 원문](https://www.moe.go.kr/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)

---
**작성자**: AI Assistant  
**최종 수정일**: 2025-01-21  
**문서 버전**: 2.0.0
