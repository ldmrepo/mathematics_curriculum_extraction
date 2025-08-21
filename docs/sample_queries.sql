-- =====================================================
-- 수학과 교육과정 데이터베이스 샘플 쿼리
-- =====================================================
-- 버전: 2.0.0
-- 수정일: 2025-01-21
-- 설명: 자주 사용되는 쿼리 예시 모음

-- =====================================================
-- 1. 기본 조회 쿼리
-- =====================================================

-- 1.1 전체 통계 조회
SELECT 
    '학교급' as category, COUNT(*) as count 
FROM curriculum.school_levels
UNION ALL
SELECT '영역', COUNT(*) FROM curriculum.domains
UNION ALL
SELECT '범주', COUNT(*) FROM curriculum.categories
UNION ALL
SELECT '성취기준', COUNT(*) FROM curriculum.achievement_standards
UNION ALL
SELECT '성취기준 해설', COUNT(*) FROM curriculum.standard_explanations
UNION ALL
SELECT '용어/기호', COUNT(*) FROM curriculum.terms_symbols
ORDER BY 
    CASE category
        WHEN '학교급' THEN 1
        WHEN '영역' THEN 2
        WHEN '범주' THEN 3
        WHEN '성취기준' THEN 4
        WHEN '성취기준 해설' THEN 5
        WHEN '용어/기호' THEN 6
    END;

-- 1.2 학년별 성취기준 개수
SELECT 
    sl.school_type,
    sl.grade_range,
    COUNT(ast.standard_id) as standard_count
FROM curriculum.school_levels sl
    LEFT JOIN curriculum.achievement_standards ast ON sl.level_id = ast.level_id
GROUP BY sl.level_id, sl.school_type, sl.grade_range
ORDER BY sl.level_id;

-- 1.3 영역별 성취기준 분포
SELECT 
    d.domain_name,
    COUNT(ast.standard_id) as standard_count,
    ROUND(COUNT(ast.standard_id) * 100.0 / SUM(COUNT(ast.standard_id)) OVER(), 1) as percentage
FROM curriculum.domains d
    LEFT JOIN curriculum.achievement_standards ast ON d.domain_id = ast.domain_id
GROUP BY d.domain_id, d.domain_name
ORDER BY d.domain_order;

-- =====================================================
-- 2. 성취기준 관련 쿼리
-- =====================================================

-- 2.1 특정 학년의 성취기준 목록
SELECT 
    ast.standard_code,
    d.domain_name,
    ast.standard_title,
    ast.standard_content
FROM curriculum.achievement_standards ast
    JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
    JOIN curriculum.domains d ON ast.domain_id = d.domain_id
WHERE sl.grade_range = '5-6학년'  -- 원하는 학년으로 변경
ORDER BY ast.standard_code;

-- 2.2 성취기준과 해설 조회
SELECT 
    ast.standard_code,
    ast.standard_title,
    ast.standard_content,
    se.explanation_type,
    se.explanation_content
FROM curriculum.achievement_standards ast
    LEFT JOIN curriculum.standard_explanations se ON ast.standard_id = se.standard_id
WHERE ast.standard_code = '6수01-01'  -- 원하는 성취기준 코드로 변경
ORDER BY se.explanation_type, se.explanation_order;

-- 2.3 키워드로 성취기준 검색
SELECT 
    ast.standard_code,
    sl.grade_range,
    d.domain_name,
    ast.standard_title,
    ast.standard_content
FROM curriculum.achievement_standards ast
    JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
    JOIN curriculum.domains d ON ast.domain_id = d.domain_id
WHERE ast.standard_content ILIKE '%분수%'  -- 검색 키워드
ORDER BY ast.standard_code;

-- 2.4 성취기준 검색 함수 사용
SELECT * FROM curriculum.search_achievement_standards('피타고라스')
LIMIT 10;

-- =====================================================
-- 3. 용어 및 기호 관련 쿼리
-- =====================================================

-- 3.1 특정 학년의 용어 목록
SELECT 
    d.domain_name,
    ts.term_type,
    ts.term_name,
    ts.term_description
FROM curriculum.terms_symbols ts
    JOIN curriculum.school_levels sl ON ts.level_id = sl.level_id
    JOIN curriculum.domains d ON ts.domain_id = d.domain_id
WHERE sl.grade_range = '1-2학년'  -- 원하는 학년으로 변경
ORDER BY d.domain_order, ts.term_type, ts.term_name;

-- 3.2 수학 기호만 조회
SELECT 
    sl.grade_range,
    d.domain_name,
    ts.term_name,
    ts.term_description,
    ts.latex_expression
FROM curriculum.terms_symbols ts
    JOIN curriculum.school_levels sl ON ts.level_id = sl.level_id
    JOIN curriculum.domains d ON ts.domain_id = d.domain_id
WHERE ts.term_type = '기호'
    AND ts.latex_expression IS NOT NULL
ORDER BY sl.level_id, d.domain_order;

-- 3.3 용어 검색 함수 사용
SELECT * FROM curriculum.search_terms_symbols('삼각형')
LIMIT 10;

-- 3.4 학년별 용어 통계
SELECT 
    sl.grade_range,
    ts.term_type,
    COUNT(*) as count
FROM curriculum.terms_symbols ts
    JOIN curriculum.school_levels sl ON ts.level_id = sl.level_id
GROUP BY sl.level_id, sl.grade_range, ts.term_type
ORDER BY sl.level_id, ts.term_type;

-- =====================================================
-- 4. 내용 체계 관련 쿼리
-- =====================================================

-- 4.1 핵심 아이디어 조회
SELECT 
    d.domain_name,
    ci.idea_content,
    ci.idea_order
FROM curriculum.core_ideas ci
    JOIN curriculum.domains d ON ci.domain_id = d.domain_id
ORDER BY d.domain_order, ci.idea_order;

-- 4.2 내용 요소 조회
SELECT 
    sl.grade_range,
    d.domain_name,
    cat.category_name,
    ce.element_name,
    ce.element_description
FROM curriculum.content_elements ce
    JOIN curriculum.school_levels sl ON ce.level_id = sl.level_id
    JOIN curriculum.domains d ON ce.domain_id = d.domain_id
    JOIN curriculum.categories cat ON ce.category_id = cat.category_id
WHERE sl.grade_range = '3-4학년'  -- 원하는 학년으로 변경
ORDER BY d.domain_order, cat.category_order, ce.element_order;

-- 4.3 학습 요소 조회
SELECT 
    sl.grade_range,
    d.domain_name,
    cat.category_name,
    le.element_name,
    le.element_description
FROM curriculum.learning_elements le
    JOIN curriculum.school_levels sl ON le.level_id = sl.level_id
    JOIN curriculum.domains d ON le.domain_id = d.domain_id
    JOIN curriculum.categories cat ON le.category_id = cat.category_id
WHERE d.domain_name = '수와 연산'  -- 원하는 영역으로 변경
ORDER BY sl.level_id, cat.category_order, le.element_order;

-- =====================================================
-- 5. 복합 조회 쿼리
-- =====================================================

-- 5.1 성취기준 상세 정보 (뷰 활용)
SELECT 
    standard_code,
    school_type,
    grade_range,
    domain_name,
    standard_title,
    element_name,
    category_name
FROM curriculum.v_achievement_standards_detail
WHERE school_type = '초등학교'
    AND domain_name = '도형과 측정'
ORDER BY standard_code;

-- 5.2 교육과정 전체 통계 (뷰 활용)
SELECT * FROM curriculum.v_curriculum_statistics
ORDER BY school_type, grade_range, domain_name;

-- 5.3 성취기준과 관련 용어 조인
SELECT 
    ast.standard_code,
    ast.standard_title,
    ts.term_name,
    ts.term_type,
    ts.term_description
FROM curriculum.achievement_standards ast
    JOIN curriculum.terms_symbols ts 
        ON ast.level_id = ts.level_id 
        AND ast.domain_id = ts.domain_id
WHERE ast.standard_code LIKE '6수03%'  -- 초5-6 도형과 측정
ORDER BY ast.standard_code, ts.term_type, ts.term_name;

-- =====================================================
-- 6. 분석 쿼리
-- =====================================================

-- 6.1 학년 간 연계성 분석
WITH standard_keywords AS (
    SELECT 
        sl.level_id,
        sl.grade_range,
        ast.standard_content,
        CASE 
            WHEN ast.standard_content ILIKE '%분수%' THEN '분수'
            WHEN ast.standard_content ILIKE '%소수%' THEN '소수'
            WHEN ast.standard_content ILIKE '%도형%' THEN '도형'
            WHEN ast.standard_content ILIKE '%측정%' THEN '측정'
            ELSE '기타'
        END as keyword
    FROM curriculum.achievement_standards ast
        JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
)
SELECT 
    keyword,
    COUNT(CASE WHEN level_id = 1 THEN 1 END) as "초1-2",
    COUNT(CASE WHEN level_id = 2 THEN 1 END) as "초3-4",
    COUNT(CASE WHEN level_id = 3 THEN 1 END) as "초5-6",
    COUNT(CASE WHEN level_id = 4 THEN 1 END) as "중1-3"
FROM standard_keywords
WHERE keyword != '기타'
GROUP BY keyword
ORDER BY keyword;

-- 6.2 성취기준 해설 유형별 통계
SELECT 
    se.explanation_type,
    COUNT(*) as count,
    COUNT(DISTINCT se.standard_id) as unique_standards
FROM curriculum.standard_explanations se
GROUP BY se.explanation_type
ORDER BY count DESC;

-- 6.3 영역별 용어 복잡도 분석
SELECT 
    d.domain_name,
    AVG(LENGTH(ts.term_name)) as avg_term_length,
    COUNT(CASE WHEN ts.latex_expression IS NOT NULL THEN 1 END) as latex_count,
    COUNT(*) as total_terms
FROM curriculum.terms_symbols ts
    JOIN curriculum.domains d ON ts.domain_id = d.domain_id
GROUP BY d.domain_id, d.domain_name
ORDER BY d.domain_order;

-- =====================================================
-- 7. 데이터 검증 쿼리
-- =====================================================

-- 7.1 성취기준 코드 형식 검증
SELECT 
    standard_code,
    CASE 
        WHEN standard_code ~ '^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$' THEN '정상'
        ELSE '오류'
    END as status
FROM curriculum.achievement_standards
WHERE NOT (standard_code ~ '^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$');

-- 7.2 외래키 참조 무결성 검증
SELECT 
    'achievement_standards -> school_levels' as relation,
    COUNT(*) as orphan_count
FROM curriculum.achievement_standards ast
    LEFT JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
WHERE sl.level_id IS NULL
UNION ALL
SELECT 
    'achievement_standards -> domains' as relation,
    COUNT(*) as orphan_count
FROM curriculum.achievement_standards ast
    LEFT JOIN curriculum.domains d ON ast.domain_id = d.domain_id
WHERE d.domain_id IS NULL
UNION ALL
SELECT 
    'standard_explanations -> achievement_standards' as relation,
    COUNT(*) as orphan_count
FROM curriculum.standard_explanations se
    LEFT JOIN curriculum.achievement_standards ast ON se.standard_id = ast.standard_id
WHERE se.standard_id IS NOT NULL AND ast.standard_id IS NULL;

-- 7.3 중복 데이터 검증
SELECT 
    standard_code,
    COUNT(*) as duplicate_count
FROM curriculum.achievement_standards
GROUP BY standard_code
HAVING COUNT(*) > 1;

-- =====================================================
-- 8. 보고서용 쿼리
-- =====================================================

-- 8.1 학년별 교육과정 요약 보고서
SELECT 
    sl.school_type AS "학교급",
    sl.grade_range AS "학년",
    d.domain_name AS "영역",
    COUNT(DISTINCT ast.standard_id) AS "성취기준 수",
    COUNT(DISTINCT ce.element_id) AS "내용요소 수",
    COUNT(DISTINCT ts.term_id) AS "용어/기호 수"
FROM curriculum.school_levels sl
    CROSS JOIN curriculum.domains d
    LEFT JOIN curriculum.achievement_standards ast 
        ON sl.level_id = ast.level_id AND d.domain_id = ast.domain_id
    LEFT JOIN curriculum.content_elements ce 
        ON sl.level_id = ce.level_id AND d.domain_id = ce.domain_id
    LEFT JOIN curriculum.terms_symbols ts 
        ON sl.level_id = ts.level_id AND d.domain_id = ts.domain_id
GROUP BY sl.level_id, sl.school_type, sl.grade_range, d.domain_id, d.domain_name
ORDER BY sl.level_id, d.domain_order;

-- 8.2 성취기준 전체 목록 (Excel 내보내기용)
SELECT 
    ast.standard_code AS "성취기준 코드",
    sl.school_type AS "학교급",
    sl.grade_range AS "학년",
    d.domain_name AS "영역",
    ast.standard_title AS "제목",
    ast.standard_content AS "내용",
    STRING_AGG(
        CASE WHEN se.explanation_type = '성취기준 해설' 
        THEN se.explanation_content END, ' | '
    ) AS "해설",
    STRING_AGG(
        CASE WHEN se.explanation_type = '적용시 고려사항' 
        THEN se.explanation_content END, ' | '
    ) AS "고려사항"
FROM curriculum.achievement_standards ast
    JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
    JOIN curriculum.domains d ON ast.domain_id = d.domain_id
    LEFT JOIN curriculum.standard_explanations se ON ast.standard_id = se.standard_id
GROUP BY ast.standard_id, ast.standard_code, sl.school_type, sl.grade_range, 
         d.domain_name, ast.standard_title, ast.standard_content
ORDER BY ast.standard_code;

-- =====================================================
-- 9. 성능 모니터링 쿼리
-- =====================================================

-- 9.1 테이블 크기 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'curriculum'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 9.2 인덱스 사용 통계
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'curriculum'
    AND idx_scan > 0
ORDER BY idx_scan DESC;

-- 9.3 느린 쿼리 찾기 (실행 시간 > 100ms)
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%curriculum%'
    AND mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- =====================================================
-- 10. 유용한 함수 활용 예시
-- =====================================================

-- 10.1 성취기준 전문 검색
SELECT 
    standard_code,
    school_type,
    grade_range,
    domain_name,
    standard_title,
    SUBSTRING(standard_content, 1, 100) || '...' as content_preview,
    rank
FROM curriculum.search_achievement_standards('문제해결')
WHERE rank > 0.1
ORDER BY rank DESC
LIMIT 20;

-- 10.2 용어 전문 검색
SELECT 
    school_type,
    grade_range,
    domain_name,
    term_type,
    term_name,
    term_description,
    rank
FROM curriculum.search_terms_symbols('각도')
WHERE rank > 0.1
ORDER BY rank DESC
LIMIT 20;

-- =====================================================
-- 끝
-- =====================================================

/*
사용 방법:
1. PostgreSQL 클라이언트 (psql, pgAdmin, DBeaver 등)에서 실행
2. 필요한 부분만 선택하여 실행
3. 파라미터는 실제 값으로 변경하여 사용

주의사항:
- 스키마 이름이 'curriculum'이 아닌 경우 변경 필요
- 대소문자 구분에 주의 (ILIKE는 대소문자 무시, LIKE는 구분)
- 전문 검색 함수는 PostgreSQL 설정에 따라 동작이 다를 수 있음
*/
