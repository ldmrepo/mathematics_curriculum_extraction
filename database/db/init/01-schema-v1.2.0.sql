-- =====================================================
-- 2022 개정 수학과 교육과정 스키마 v1.2.0 (Base)
-- 작성일: 2025-08-22
-- 설명: 기본 엔터티/뷰/함수/트리거까지 포함. (Edges/RAG는 포함하지 않음)
-- 주의: 이 파일에는 "가드(예외 RAISE)"나 Edge/브리지 테이블이 없어야 합니다.
-- =====================================================

-- 스키마/확장/검색경로
CREATE SCHEMA IF NOT EXISTS curriculum;
SET search_path TO curriculum, public;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. 기준 테이블 (Reference Tables)
-- =====================================================

-- 1.1 학교급/학년
CREATE TABLE IF NOT EXISTS school_levels (
    level_id     SERIAL PRIMARY KEY,
    school_type  VARCHAR(20) NOT NULL CHECK (school_type IN ('초등학교','중학교','고등학교')),
    grade_range  VARCHAR(20) NOT NULL,
    grade_start  INTEGER NOT NULL CHECK (grade_start BETWEEN 1 AND 12),
    grade_end    INTEGER NOT NULL CHECK (grade_end   BETWEEN 1 AND 12),
    level_code   INTEGER NOT NULL UNIQUE CHECK (level_code IN (2,4,6,9,12)),
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_grade_order CHECK (grade_start <= grade_end)
);

-- 1.2 수학 영역
CREATE TABLE IF NOT EXISTS domains (
    domain_id     SERIAL PRIMARY KEY,
    domain_name   VARCHAR(50) NOT NULL UNIQUE,
    domain_order  INTEGER NOT NULL UNIQUE CHECK (domain_order BETWEEN 1 AND 10),
    domain_code   VARCHAR(2) NOT NULL UNIQUE,
    description   TEXT,
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 내용 체계 범주
CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(20) NOT NULL UNIQUE,
    category_order  INTEGER NOT NULL UNIQUE CHECK (category_order BETWEEN 1 AND 5),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.4 성취수준 레벨(A~E)
CREATE TABLE IF NOT EXISTS achievement_levels (
    level_code   CHAR(1) PRIMARY KEY CHECK (level_code IN ('A','B','C','D','E')),
    level_name   VARCHAR(10) NOT NULL,
    level_order  INTEGER NOT NULL UNIQUE CHECK (level_order BETWEEN 1 AND 5),
    description  TEXT,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. 내용 체계 (Content System)
-- =====================================================

-- 2.1 핵심 아이디어
CREATE TABLE IF NOT EXISTS core_ideas (
    idea_id       SERIAL PRIMARY KEY,
    domain_id     INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    idea_content  TEXT NOT NULL,
    idea_order    INTEGER NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_domain_idea_order UNIQUE (domain_id, idea_order)
);

-- 2.2 내용 요소
CREATE TABLE IF NOT EXISTS content_elements (
    element_id          SERIAL PRIMARY KEY,
    domain_id           INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    level_id            INTEGER NOT NULL REFERENCES school_levels(level_id) ON DELETE CASCADE,
    category_id         INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    element_name        VARCHAR(200) NOT NULL,
    element_description TEXT,
    element_order       INTEGER NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_domain_level_category_order UNIQUE (domain_id, level_id, category_id, element_order)
);

-- 2.3 학습 요소 (옵션)
CREATE TABLE IF NOT EXISTS learning_elements (
    learning_id         SERIAL PRIMARY KEY,
    domain_id           INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    level_id            INTEGER NOT NULL REFERENCES school_levels(level_id) ON DELETE CASCADE,
    category_id         INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    element_name        VARCHAR(200) NOT NULL,
    element_description TEXT,
    element_order       INTEGER NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_learning_domain_level_category_order UNIQUE (domain_id, level_id, category_id, element_order)
);

-- =====================================================
-- 3. 성취기준 (Achievement Standards)
-- =====================================================

-- 3.1 성취기준
CREATE TABLE IF NOT EXISTS achievement_standards (
    standard_id      SERIAL PRIMARY KEY,
    standard_code    VARCHAR(10) NOT NULL UNIQUE,
    level_id         INTEGER NOT NULL REFERENCES school_levels(level_id) ON DELETE CASCADE,
    domain_id        INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    element_id       INTEGER REFERENCES content_elements(element_id) ON DELETE SET NULL,
    standard_title   VARCHAR(200) NOT NULL,
    standard_content TEXT NOT NULL,
    standard_order   INTEGER NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_level_domain_order UNIQUE (level_id, domain_id, standard_order),
    CONSTRAINT chk_standard_code_format CHECK (standard_code ~ '^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$')
);

-- 3.2 성취기준 해설/고려사항/용어와 기호
CREATE TABLE IF NOT EXISTS standard_explanations (
    explanation_id     SERIAL PRIMARY KEY,
    standard_id        INTEGER REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    explanation_type   VARCHAR(30) NOT NULL CHECK (explanation_type IN ('성취기준 해설','적용시 고려사항','용어와 기호')),
    explanation_content TEXT NOT NULL,
    explanation_order  INTEGER DEFAULT 1,
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_standard_type_order UNIQUE (standard_id, explanation_type, explanation_order)
);

-- 3.3 성취기준별 성취수준
CREATE TABLE IF NOT EXISTS standard_achievement_levels (
    sal_id           SERIAL PRIMARY KEY,
    standard_id      INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    level_code       CHAR(1) NOT NULL REFERENCES achievement_levels(level_code) ON DELETE CASCADE,
    level_description TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_standard_level UNIQUE (standard_id, level_code)
);

-- 3.4 영역별 성취수준
CREATE TABLE IF NOT EXISTS domain_achievement_levels (
    dal_id           SERIAL PRIMARY KEY,
    level_id         INTEGER NOT NULL REFERENCES school_levels(level_id) ON DELETE CASCADE,
    domain_id        INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    level_code       CHAR(1) NOT NULL REFERENCES achievement_levels(level_code) ON DELETE CASCADE,
    category_id      INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    level_description TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_domain_school_level_category UNIQUE (level_id, domain_id, level_code, category_id)
);

-- =====================================================
-- 4. 용어 및 기호
-- =====================================================
CREATE TABLE IF NOT EXISTS terms_symbols (
    term_id          SERIAL PRIMARY KEY,
    level_id         INTEGER NOT NULL REFERENCES school_levels(level_id) ON DELETE CASCADE,
    domain_id        INTEGER NOT NULL REFERENCES domains(domain_id) ON DELETE CASCADE,
    term_type        VARCHAR(10) NOT NULL CHECK (term_type IN ('용어','기호')),
    term_name        VARCHAR(100) NOT NULL,
    term_description TEXT,
    latex_expression TEXT,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_level_domain_term UNIQUE (level_id, domain_id, term_name)
);

-- =====================================================
-- 5. 인덱스
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_achievement_standards_code   ON achievement_standards(standard_code);
CREATE INDEX IF NOT EXISTS idx_achievement_standards_level  ON achievement_standards(level_id);
CREATE INDEX IF NOT EXISTS idx_achievement_standards_domain ON achievement_standards(domain_id);

CREATE INDEX IF NOT EXISTS idx_content_elements_level_domain  ON content_elements(level_id, domain_id);
CREATE INDEX IF NOT EXISTS idx_learning_elements_level_domain ON learning_elements(level_id, domain_id);
CREATE INDEX IF NOT EXISTS idx_terms_symbols_level_domain     ON terms_symbols(level_id, domain_id);
CREATE INDEX IF NOT EXISTS idx_core_ideas_domain              ON core_ideas(domain_id);

CREATE INDEX IF NOT EXISTS idx_standard_explanations_standard ON standard_explanations(standard_id);
CREATE INDEX IF NOT EXISTS idx_standard_explanations_type     ON standard_explanations(explanation_type);

-- 성취수준 관련
CREATE INDEX IF NOT EXISTS idx_standard_achievement_levels_standard ON standard_achievement_levels(standard_id);
CREATE INDEX IF NOT EXISTS idx_standard_achievement_levels_level    ON standard_achievement_levels(level_code);
CREATE INDEX IF NOT EXISTS idx_domain_achievement_levels_school     ON domain_achievement_levels(level_id);
CREATE INDEX IF NOT EXISTS idx_domain_achievement_levels_domain     ON domain_achievement_levels(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_achievement_levels_level      ON domain_achievement_levels(level_code);

-- 전문검색
CREATE INDEX IF NOT EXISTS idx_achievement_standards_content_search
  ON achievement_standards USING gin(to_tsvector('simple', standard_content));

CREATE INDEX IF NOT EXISTS idx_terms_symbols_name_search
  ON terms_symbols USING gin(to_tsvector('simple', term_name || ' ' || COALESCE(term_description,'')));

CREATE INDEX IF NOT EXISTS idx_standard_achievement_levels_search
  ON standard_achievement_levels USING gin(to_tsvector('simple', level_description));

-- =====================================================
-- 6. 뷰
-- =====================================================

-- 6.1 성취기준 상세
CREATE OR REPLACE VIEW v_achievement_standards_detail AS
SELECT 
    ast.standard_id,
    ast.standard_code,
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    ast.standard_title,
    ast.standard_content,
    ast.standard_order,
    ce.element_name,
    ce.element_description,
    cat.category_name,
    ast.created_at,
    ast.updated_at
FROM achievement_standards ast
JOIN school_levels sl ON ast.level_id = sl.level_id
JOIN domains d        ON ast.domain_id = d.domain_id
LEFT JOIN content_elements ce ON ast.element_id = ce.element_id
LEFT JOIN categories cat      ON ce.category_id = cat.category_id
ORDER BY ast.standard_code;

-- 6.2 성취기준별 성취수준 상세
CREATE OR REPLACE VIEW v_standard_achievement_levels_detail AS
SELECT 
    sal.sal_id,
    ast.standard_code,
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    ast.standard_title,
    al.level_code,
    al.level_name,
    sal.level_description,
    sal.created_at
FROM standard_achievement_levels sal
JOIN achievement_standards ast ON sal.standard_id = ast.standard_id
JOIN achievement_levels   al  ON sal.level_code  = al.level_code
JOIN school_levels        sl  ON ast.level_id    = sl.level_id
JOIN domains              d   ON ast.domain_id   = d.domain_id
ORDER BY ast.standard_code, al.level_order;

-- 6.3 영역별 성취수준 상세
CREATE OR REPLACE VIEW v_domain_achievement_levels_detail AS
SELECT 
    dal.dal_id,
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    c.category_name,
    al.level_code,
    al.level_name,
    dal.level_description,
    dal.created_at
FROM domain_achievement_levels dal
JOIN school_levels sl ON dal.level_id = sl.level_id
JOIN domains d        ON dal.domain_id = d.domain_id
JOIN categories c     ON dal.category_id = c.category_id
JOIN achievement_levels al ON dal.level_code = al.level_code
ORDER BY sl.level_id, d.domain_order, c.category_order, al.level_order;

-- 6.4 용어/기호 상세
CREATE OR REPLACE VIEW v_terms_symbols_detail AS
SELECT 
    ts.term_id,
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    ts.term_type,
    ts.term_name,
    ts.term_description,
    ts.latex_expression,
    ts.created_at
FROM terms_symbols ts
JOIN school_levels sl ON ts.level_id = sl.level_id
JOIN domains d        ON ts.domain_id = d.domain_id
ORDER BY sl.level_id, d.domain_order, ts.term_type, ts.term_name;

-- 6.5 통계
CREATE OR REPLACE VIEW v_curriculum_statistics AS
SELECT 
    sl.school_type,
    sl.grade_range,
    d.domain_name,
    COUNT(DISTINCT ast.standard_id) AS standard_count,
    COUNT(DISTINCT ce.element_id)   AS content_element_count,
    COUNT(DISTINCT le.learning_id)  AS learning_element_count,
    COUNT(DISTINCT ts.term_id)      AS term_count,
    COUNT(DISTINCT sal.sal_id)      AS achievement_level_count
FROM school_levels sl
CROSS JOIN domains d
LEFT JOIN achievement_standards ast ON sl.level_id = ast.level_id AND d.domain_id = ast.domain_id
LEFT JOIN content_elements ce       ON sl.level_id = ce.level_id  AND d.domain_id = ce.domain_id
LEFT JOIN learning_elements le      ON sl.level_id = le.level_id  AND d.domain_id = le.domain_id
LEFT JOIN terms_symbols ts          ON sl.level_id = ts.level_id  AND d.domain_id = ts.domain_id
LEFT JOIN standard_achievement_levels sal ON ast.standard_id = sal.standard_id
GROUP BY sl.level_id, sl.school_type, sl.grade_range, d.domain_id, d.domain_name
ORDER BY sl.level_id, d.domain_order;

-- =====================================================
-- 7. 함수
-- =====================================================

-- 7.1 성취기준 전문검색
CREATE OR REPLACE FUNCTION search_achievement_standards(search_term TEXT)
RETURNS TABLE (
    standard_id     INTEGER,
    standard_code   VARCHAR(10),
    school_type     VARCHAR(20),
    grade_range     VARCHAR(20),
    domain_name     VARCHAR(50),
    standard_title  VARCHAR(200),
    standard_content TEXT,
    rank            REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ast.standard_id,
        ast.standard_code,
        sl.school_type,
        sl.grade_range,
        d.domain_name,
        ast.standard_title,
        ast.standard_content,
        ts_rank(to_tsvector('simple', ast.standard_content), plainto_tsquery('simple', search_term)) AS rank
    FROM achievement_standards ast
    JOIN school_levels sl ON ast.level_id = sl.level_id
    JOIN domains d        ON ast.domain_id = d.domain_id
    WHERE to_tsvector('simple', ast.standard_content) @@ plainto_tsquery('simple', search_term)
    ORDER BY rank DESC;
END; $$ LANGUAGE plpgsql;

-- 7.2 성취수준 전문검색
CREATE OR REPLACE FUNCTION search_achievement_levels(search_term TEXT)
RETURNS TABLE (
    sal_id            INTEGER,
    standard_code     VARCHAR(10),
    school_type       VARCHAR(20),
    grade_range       VARCHAR(20),
    domain_name       VARCHAR(50),
    level_code        CHAR(1),
    level_name        VARCHAR(10),
    level_description TEXT,
    rank              REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sal.sal_id,
        ast.standard_code,
        sl.school_type,
        sl.grade_range,
        d.domain_name,
        al.level_code,
        al.level_name,
        sal.level_description,
        ts_rank(to_tsvector('simple', sal.level_description), plainto_tsquery('simple', search_term)) AS rank
    FROM standard_achievement_levels sal
    JOIN achievement_standards ast ON sal.standard_id = ast.standard_id
    JOIN achievement_levels   al  ON sal.level_code  = al.level_code
    JOIN school_levels        sl  ON ast.level_id    = sl.level_id
    JOIN domains              d   ON ast.domain_id   = d.domain_id
    WHERE to_tsvector('simple', sal.level_description) @@ plainto_tsquery('simple', search_term)
    ORDER BY rank DESC;
END; $$ LANGUAGE plpgsql;

-- 7.3 특정 성취기준의 모든 성취수준
CREATE OR REPLACE FUNCTION get_standard_levels(p_standard_code VARCHAR(10))
RETURNS TABLE (
    level_code       CHAR(1),
    level_name       VARCHAR(10),
    level_description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.level_code,
        al.level_name,
        sal.level_description
    FROM standard_achievement_levels sal
    JOIN achievement_standards ast ON sal.standard_id = ast.standard_id
    JOIN achievement_levels   al  ON sal.level_code  = al.level_code
    WHERE ast.standard_code = p_standard_code
    ORDER BY al.level_order;
END; $$ LANGUAGE plpgsql;

-- 7.4 updated_at 자동 갱신 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- =====================================================
-- 8. 트리거
-- =====================================================
DO $$
BEGIN
    -- 트리거는 IF NOT EXISTS가 없어 Drop 후 생성
    -- school_levels
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_school_levels_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_school_levels_updated_at ON school_levels';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_school_levels_updated_at BEFORE UPDATE ON school_levels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- domains
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_domains_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_domains_updated_at ON domains';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_domains_updated_at BEFORE UPDATE ON domains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- categories
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_categories_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_categories_updated_at ON categories';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- achievement_levels
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_achievement_levels_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_achievement_levels_updated_at ON achievement_levels';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_achievement_levels_updated_at BEFORE UPDATE ON achievement_levels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- core_ideas
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_core_ideas_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_core_ideas_updated_at ON core_ideas';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_core_ideas_updated_at BEFORE UPDATE ON core_ideas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- content_elements
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_content_elements_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_content_elements_updated_at ON content_elements';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_content_elements_updated_at BEFORE UPDATE ON content_elements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- learning_elements
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_learning_elements_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_learning_elements_updated_at ON learning_elements';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_learning_elements_updated_at BEFORE UPDATE ON learning_elements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- achievement_standards
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_achievement_standards_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_achievement_standards_updated_at ON achievement_standards';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_achievement_standards_updated_at BEFORE UPDATE ON achievement_standards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- standard_explanations
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_explanations_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_standard_explanations_updated_at ON standard_explanations';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_explanations_updated_at BEFORE UPDATE ON standard_explanations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- standard_achievement_levels
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_achievement_levels_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_standard_achievement_levels_updated_at ON standard_achievement_levels';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_achievement_levels_updated_at BEFORE UPDATE ON standard_achievement_levels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- domain_achievement_levels
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_domain_achievement_levels_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_domain_achievement_levels_updated_at ON domain_achievement_levels';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_domain_achievement_levels_updated_at BEFORE UPDATE ON domain_achievement_levels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    -- terms_symbols
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_terms_symbols_updated_at') THEN
        EXECUTE 'DROP TRIGGER tr_terms_symbols_updated_at ON terms_symbols';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_terms_symbols_updated_at BEFORE UPDATE ON terms_symbols FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';
END $$;

-- =====================================================
-- 9. 초기 데이터
-- =====================================================
INSERT INTO achievement_levels (level_code, level_name, level_order, description) VALUES
('A','매우 우수',1,'성취기준에 대한 이해와 적용이 매우 우수한 수준'),
('B','우수',   2,'성취기준에 대한 이해와 적용이 우수한 수준'),
('C','보통',   3,'성취기준에 대한 이해와 적용이 보통인 수준'),
('D','기초',   4,'성취기준에 대한 이해와 적용이 기초적인 수준'),
('E','기초 미달',5,'성취기준에 대한 이해와 적용이 기초에 미달하는 수준')
ON CONFLICT (level_code) DO NOTHING;

-- =====================================================
-- 10. 코멘트
-- =====================================================
COMMENT ON SCHEMA curriculum IS '2022 개정 수학과 교육과정 데이터베이스 스키마 v1.2';

COMMENT ON TABLE school_levels                IS '학교급/학년 정보';
COMMENT ON TABLE domains                      IS '수학 영역 (수와 연산, 변화와 관계, 도형과 측정, 자료와 가능성)';
COMMENT ON TABLE categories                   IS '내용 체계 범주 (지식·이해, 과정·기능, 가치·태도)';
COMMENT ON TABLE achievement_levels           IS '성취수준 레벨 (A~E)';
COMMENT ON TABLE core_ideas                   IS '영역별 핵심 아이디어';
COMMENT ON TABLE content_elements             IS '학년군·영역·범주별 내용 요소';
COMMENT ON TABLE learning_elements            IS '학년군·영역·범주별 학습 요소';
COMMENT ON TABLE achievement_standards        IS '성취기준(코드/내용)';
COMMENT ON TABLE standard_explanations        IS '성취기준 해설/적용시 고려사항/용어와 기호';
COMMENT ON TABLE standard_achievement_levels  IS '성취기준별 성취수준';
COMMENT ON TABLE domain_achievement_levels    IS '영역별 성취수준';
COMMENT ON TABLE terms_symbols                IS '수학 용어 및 기호 (LaTeX 포함)';

COMMENT ON COLUMN achievement_standards.standard_code IS '예: 2수01-01, 9수01-01';
COMMENT ON COLUMN terms_symbols.latex_expression      IS 'LaTeX 표현';

-- ============================ END OF v1.2.0 ============================
