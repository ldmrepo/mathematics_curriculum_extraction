# SQL 쿼리 예제

## 기본 조회 쿼리

### 1. 모든 성취기준 조회
```sql
SELECT 
    s.standard_code,
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    s.standard_title,
    s.standard_content
FROM achievement_standards s
JOIN school_levels sl ON s.level_id = sl.level_id
JOIN domains d ON s.domain_id = d.domain_id
ORDER BY s.standard_code;
```

### 2. 특정 학년의 성취기준 조회
```sql
-- 초등학교 1-2학년 수와 연산 영역
SELECT 
    standard_code,
    standard_title,
    standard_content
FROM achievement_standards s
JOIN school_levels sl ON s.level_id = sl.level_id
JOIN domains d ON s.domain_id = d.domain_id
WHERE sl.grade_range = '1-2학년' 
  AND d.domain_name = '수와 연산'
ORDER BY s.standard_order;
```

### 3. 영역별 성취기준 개수
```sql
SELECT 
    d.domain_name,
    sl.grade_range,
    COUNT(*) as standard_count
FROM achievement_standards s
JOIN domains d ON s.domain_id = d.domain_id
JOIN school_levels sl ON s.level_id = sl.level_id
GROUP BY d.domain_name, sl.grade_range
ORDER BY d.domain_order, sl.level_id;
```

## 복합 조회 쿼리

### 4. 성취기준과 해설 함께 조회
```sql
SELECT 
    s.standard_code,
    s.standard_content,
    e.explanation_type,
    e.explanation_content
FROM achievement_standards s
LEFT JOIN standard_explanations e ON s.standard_id = e.standard_id
WHERE s.standard_code = '2수01-01'
ORDER BY e.explanation_type;
```

### 5. 용어 및 기호 검색
```sql
-- LaTeX 수식이 포함된 용어 검색
SELECT 
    sl.grade_range,
    d.domain_name,
    t.term_type,
    t.term_name,
    t.term_description
FROM terms_symbols t
JOIN school_levels sl ON t.level_id = sl.level_id
JOIN domains d ON t.domain_id = d.domain_id
WHERE t.term_name LIKE '%$%'  -- LaTeX 수식 포함
ORDER BY sl.level_id, d.domain_order;
```

### 6. 핵심 아이디어별 성취기준 매핑
```sql
SELECT 
    d.domain_name,
    ci.idea_content,
    COUNT(s.standard_id) as related_standards
FROM core_ideas ci
JOIN domains d ON ci.domain_id = d.domain_id
LEFT JOIN achievement_standards s ON ci.domain_id = s.domain_id
GROUP BY d.domain_name, ci.idea_content
ORDER BY d.domain_order, ci.idea_order;
```

## 분석 쿼리

### 7. 학년별 수학 용어 복잡도 분석
```sql
-- LaTeX 수식 사용 빈도
SELECT 
    sl.grade_range,
    COUNT(*) as total_terms,
    SUM(CASE WHEN t.term_name LIKE '%$%' THEN 1 ELSE 0 END) as latex_terms,
    ROUND(
        SUM(CASE WHEN t.term_name LIKE '%$%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) as latex_percentage
FROM terms_symbols t
JOIN school_levels sl ON t.level_id = sl.level_id
GROUP BY sl.grade_range, sl.level_id
ORDER BY sl.level_id;
```

### 8. 성취기준 내용 키워드 분석
```sql
-- '이해'라는 키워드가 포함된 성취기준
SELECT 
    sl.grade_range,
    d.domain_name,
    s.standard_code,
    s.standard_content
FROM achievement_standards s
JOIN school_levels sl ON s.level_id = sl.level_id
JOIN domains d ON s.domain_id = d.domain_id
WHERE s.standard_content LIKE '%이해%'
ORDER BY sl.level_id, d.domain_order;
```

### 9. 영역별 핵심 개념 추출
```sql
-- 각 영역의 핵심 아이디어와 주요 용어
SELECT 
    d.domain_name,
    ci.idea_content as core_idea,
    GROUP_CONCAT(DISTINCT t.term_name) as key_terms
FROM domains d
JOIN core_ideas ci ON d.domain_id = ci.domain_id
LEFT JOIN terms_symbols t ON d.domain_id = t.domain_id 
WHERE t.level_id = 4  -- 중학교 수준
GROUP BY d.domain_name, ci.idea_content
ORDER BY d.domain_order, ci.idea_order;
```

## 데이터 무결성 검증 쿼리

### 10. 외래키 무결성 확인
```sql
-- 참조 무결성 검증
SELECT 'achievement_standards' as table_name, 
       COUNT(*) as invalid_refs
FROM achievement_standards s
LEFT JOIN school_levels sl ON s.level_id = sl.level_id
LEFT JOIN domains d ON s.domain_id = d.domain_id
WHERE sl.level_id IS NULL OR d.domain_id IS NULL

UNION ALL

SELECT 'terms_symbols' as table_name,
       COUNT(*) as invalid_refs  
FROM terms_symbols t
LEFT JOIN school_levels sl ON t.level_id = sl.level_id
LEFT JOIN domains d ON t.domain_id = d.domain_id
WHERE sl.level_id IS NULL OR d.domain_id IS NULL;
```

### 11. 성취기준 코드 유일성 확인
```sql
-- 중복된 성취기준 코드 확인
SELECT standard_code, COUNT(*) as duplicate_count
FROM achievement_standards
GROUP BY standard_code
HAVING COUNT(*) > 1;
```

### 12. 누락된 데이터 확인
```sql
-- 해설이 없는 성취기준 조회
SELECT 
    s.standard_code,
    s.standard_title
FROM achievement_standards s
LEFT JOIN standard_explanations e ON s.standard_id = e.standard_id
WHERE e.explanation_id IS NULL
ORDER BY s.standard_code;
```

## 학습 지원 쿼리

### 13. 특정 개념의 학습 경로 추적
```sql
-- '분수' 개념의 학년별 발전 과정
SELECT 
    sl.grade_range,
    s.standard_code,
    s.standard_title,
    s.standard_content
FROM achievement_standards s
JOIN school_levels sl ON s.level_id = sl.level_id
WHERE s.standard_content LIKE '%분수%' 
   OR s.standard_title LIKE '%분수%'
ORDER BY sl.level_id, s.standard_order;
```

### 14. 수학적 역량별 성취기준 분류
```sql
-- '문제해결' 역량 관련 성취기준
SELECT 
    sl.grade_range,
    d.domain_name,
    s.standard_code,
    s.standard_content
FROM achievement_standards s
JOIN school_levels sl ON s.level_id = sl.level_id
JOIN domains d ON s.domain_id = d.domain_id
WHERE s.standard_content LIKE '%문제%해결%'
   OR s.standard_content LIKE '%문제를%해결%'
ORDER BY sl.level_id, d.domain_order;
```
