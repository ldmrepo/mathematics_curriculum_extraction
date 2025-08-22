-- =====================================================
-- 수학과 교육과정 스키마 업데이트 v1.3.0 (Edges & RAG)
-- 적용일: 2025-08-22
-- 변경 요약:
--  - 브리지/엣지 테이블: standard_terms, representation_types, standard_representations,
--    context_labels, standard_contexts, competencies, standard_competencies,
--    achievement_standard_relations(PREREQUISITE/HORIZONTAL)
--  - 제안/정렬/검증 뷰: v_std_in_area, v_std_in_category, v_domain_coreideas, v_standard_levels,
--    v_level_alignment, v_standard_meta, v_term_candidates, v_horizontal_suggestions,
--    v_prerequisite_suggestions, rpt_coverage, rpt_dag_health
--  - 사이클 검출 함수: detect_prerequisite_cycles()
-- =====================================================

SET search_path TO curriculum, public;

-- 스키마 존재 가드 (v1.2.0 선적용 필수)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='curriculum') THEN
    RAISE EXCEPTION 'schema curriculum not found. Apply v1.2.0 first.';
  END IF;
END $$;

-- =====================================================
-- 1) 브리지/엣지 테이블
-- =====================================================

-- 1.1 표상 타입
CREATE TABLE IF NOT EXISTS representation_types (
    rep_type_id  SERIAL PRIMARY KEY,
    type_name    VARCHAR(40) NOT NULL UNIQUE,   -- 예: 표, 식, 그래프, 도형, 구체물, 말, 그림, 기호, 행동
    description  TEXT,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 성취기준-표상 매핑
CREATE TABLE IF NOT EXISTS standard_representations (
    sr_id              SERIAL PRIMARY KEY,
    standard_id        INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    rep_type_id        INTEGER NOT NULL REFERENCES representation_types(rep_type_id) ON DELETE RESTRICT,
    representation_text TEXT,         -- 예: "수직선", "막대그래프"
    media_uri          TEXT,
    method             VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
    confidence         NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    evidence_text      TEXT,
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 컨텍스트 라벨
CREATE TABLE IF NOT EXISTS context_labels (
    context_id   SERIAL PRIMARY KEY,
    context_name VARCHAR(80) NOT NULL UNIQUE,
    description  TEXT,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.4 성취기준-컨텍스트 매핑
CREATE TABLE IF NOT EXISTS standard_contexts (
    scx_id        SERIAL PRIMARY KEY,
    standard_id   INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    context_id    INTEGER NOT NULL REFERENCES context_labels(context_id) ON DELETE RESTRICT,
    scope_note    TEXT,
    method        VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
    confidence    NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    evidence_text TEXT,
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.5 교과 역량 마스터
CREATE TABLE IF NOT EXISTS competencies (
    comp_id     SERIAL PRIMARY KEY,
    comp_code   VARCHAR(20) NOT NULL UNIQUE,
    comp_name   VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.6 성취기준-역량 매핑 (가중치)
CREATE TABLE IF NOT EXISTS standard_competencies (
    sc_id        SERIAL PRIMARY KEY,
    standard_id  INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    comp_id      INTEGER NOT NULL REFERENCES competencies(comp_id) ON DELETE RESTRICT,
    weight       NUMERIC(3,2) NOT NULL CHECK (weight BETWEEN 0 AND 1),
    method       VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
    confidence   NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    evidence_text TEXT,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_std_comp UNIQUE (standard_id, comp_id)
);

-- 1.7 성취기준-용어/기호 매핑
CREATE TABLE IF NOT EXISTS standard_terms (
    st_id         SERIAL PRIMARY KEY,
    standard_id   INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    term_id       INTEGER NOT NULL REFERENCES terms_symbols(term_id) ON DELETE CASCADE,
    relation_type VARCHAR(10) NOT NULL DEFAULT '필수' CHECK (relation_type IN ('필수','참고')),
    method        VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
    confidence    NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    evidence_text TEXT,
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_standard_term UNIQUE (standard_id, term_id)
);

-- 1.8 성취기준 간 관계 (Prerequisite / Horizontal)
CREATE TABLE IF NOT EXISTS achievement_standard_relations (
    rel_id           SERIAL PRIMARY KEY,
    src_standard_id  INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    dst_standard_id  INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
    relation_type    VARCHAR(15) NOT NULL CHECK (relation_type IN ('PREREQUISITE','HORIZONTAL')),
    rationale        TEXT,
    method           VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
    confidence       NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_asr UNIQUE (src_standard_id, dst_standard_id, relation_type),
    CONSTRAINT chk_no_self_loop CHECK (src_standard_id <> dst_standard_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_std_reps_std   ON standard_representations(standard_id);
CREATE INDEX IF NOT EXISTS idx_std_reps_rep   ON standard_representations(rep_type_id);
CREATE INDEX IF NOT EXISTS idx_std_contexts_std ON standard_contexts(standard_id);
CREATE INDEX IF NOT EXISTS idx_std_contexts_ctx ON standard_contexts(context_id);
CREATE INDEX IF NOT EXISTS idx_std_comp_std   ON standard_competencies(standard_id);
CREATE INDEX IF NOT EXISTS idx_std_comp_comp  ON standard_competencies(comp_id);
CREATE INDEX IF NOT EXISTS idx_std_terms_std  ON standard_terms(standard_id);
CREATE INDEX IF NOT EXISTS idx_std_terms_term ON standard_terms(term_id);
CREATE INDEX IF NOT EXISTS idx_asr_src        ON achievement_standard_relations(src_standard_id);
CREATE INDEX IF NOT EXISTS idx_asr_dst        ON achievement_standard_relations(dst_standard_id);
CREATE INDEX IF NOT EXISTS idx_asr_type       ON achievement_standard_relations(relation_type);

-- [추가] 표현식 기반 고유 제약은 UNIQUE INDEX로 생성
CREATE UNIQUE INDEX IF NOT EXISTS uq_std_rep_idx
  ON standard_representations (standard_id, rep_type_id, COALESCE(representation_text, ''));

CREATE UNIQUE INDEX IF NOT EXISTS uq_std_context_idx
  ON standard_contexts (standard_id, context_id, COALESCE(scope_note, ''));

-- 타임스탬프 트리거
DO $$
BEGIN
  PERFORM 1 FROM pg_proc WHERE proname='update_updated_at_column' AND pg_function_is_visible(oid);
  IF FOUND THEN
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_representations_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_standard_representations_updated_at ON standard_representations';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_representations_updated_at BEFORE UPDATE ON standard_representations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_context_labels_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_context_labels_updated_at ON context_labels';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_context_labels_updated_at BEFORE UPDATE ON context_labels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_contexts_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_standard_contexts_updated_at ON standard_contexts';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_contexts_updated_at BEFORE UPDATE ON standard_contexts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_competencies_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_competencies_updated_at ON competencies';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_competencies_updated_at BEFORE UPDATE ON competencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_competencies_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_standard_competencies_updated_at ON standard_competencies';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_competencies_updated_at BEFORE UPDATE ON standard_competencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_standard_terms_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_standard_terms_updated_at ON standard_terms';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_standard_terms_updated_at BEFORE UPDATE ON standard_terms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';

    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='tr_achievement_standard_relations_updated_at') THEN
      EXECUTE 'DROP TRIGGER tr_achievement_standard_relations_updated_at ON achievement_standard_relations';
    END IF;
    EXECUTE 'CREATE TRIGGER tr_achievement_standard_relations_updated_at BEFORE UPDATE ON achievement_standard_relations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()';
  END IF;
END $$;

-- =====================================================
-- 2) 시드 데이터(선택)
-- =====================================================
INSERT INTO competencies (comp_code, comp_name, description) VALUES
('PS','문제해결','문제 파악·계획·수행·반성'),
('RS','추론','수학적 추론과 정당화'),
('COM','의사소통','표현·해석·소통'),
('CON','연결','수학 내·외부 연결'),
('INF','정보처리','자료/도구/기술 활용')
ON CONFLICT (comp_code) DO NOTHING;

INSERT INTO representation_types (type_name, description) VALUES
('표','표 형태의 표현'),
('식','수식/방정식 표현'),
('그래프','그래프/도표'),
('도형','평면/입체 도형'),
('구체물','교구/실물'),
('말','자연어 설명'),
('그림','스케치/도식'),
('기호','수학 기호/기호화'),
('행동','조작/행동 기반 표현')
ON CONFLICT (type_name) DO NOTHING;

-- =====================================================
-- 3) 정렬/메타/제안 뷰
-- =====================================================

-- 3.1 영역 내 성취기준
CREATE OR REPLACE VIEW v_std_in_area AS
SELECT ast.standard_id, ast.standard_code, d.domain_name, ast.standard_order
FROM achievement_standards ast
JOIN domains d ON ast.domain_id = d.domain_id;

-- 3.2 범주 내 성취기준 (내용 요소 통해)
CREATE OR REPLACE VIEW v_std_in_category AS
SELECT ast.standard_id, ast.standard_code, cat.category_name
FROM achievement_standards ast
LEFT JOIN content_elements ce ON ast.element_id = ce.element_id
LEFT JOIN categories cat ON ce.category_id = cat.category_id;

-- 3.3 도메인-핵심아이디어
CREATE OR REPLACE VIEW v_domain_coreideas AS
SELECT d.domain_name, ci.idea_order, ci.idea_content
FROM core_ideas ci
JOIN domains d ON ci.domain_id = d.domain_id
ORDER BY d.domain_order, ci.idea_order;

-- 3.4 성취기준-성취수준
CREATE OR REPLACE VIEW v_standard_levels AS
SELECT ast.standard_id, ast.standard_code, al.level_code, al.level_name, sal.level_description
FROM standard_achievement_levels sal
JOIN achievement_standards ast ON sal.standard_id = ast.standard_id
JOIN achievement_levels al ON sal.level_code = al.level_code;

-- 3.5 영역 성취수준 정렬(성취기준 정렬 지원용)
CREATE OR REPLACE VIEW v_level_alignment AS
SELECT 
  ast.standard_id, ast.standard_code, ast.level_id, ast.domain_id,
  dal.level_code, dal.category_id, dal.level_description AS area_level_desc
FROM achievement_standards ast
JOIN domain_achievement_levels dal
  ON dal.level_id = ast.level_id AND dal.domain_id = ast.domain_id;

-- 3.6 성취기준 메타 요약(용어/표상/컨텍스트/역량 개수)
CREATE OR REPLACE VIEW v_standard_meta AS
SELECT
  ast.standard_id,
  ast.standard_code,
  COALESCE(t.cnt,0)   AS term_count,
  COALESCE(r.cnt,0)   AS representation_count,
  COALESCE(cx.cnt,0)  AS context_count,
  COALESCE(sc.cnt,0)  AS competency_count
FROM achievement_standards ast
LEFT JOIN (SELECT standard_id, COUNT(*) cnt FROM standard_terms GROUP BY standard_id) t  ON t.standard_id  = ast.standard_id
LEFT JOIN (SELECT standard_id, COUNT(*) cnt FROM standard_representations GROUP BY standard_id) r ON r.standard_id = ast.standard_id
LEFT JOIN (SELECT standard_id, COUNT(*) cnt FROM standard_contexts GROUP BY standard_id) cx ON cx.standard_id = ast.standard_id
LEFT JOIN (SELECT standard_id, COUNT(*) cnt FROM standard_competencies GROUP BY standard_id) sc ON sc.standard_id = ast.standard_id;

-- 3.7 용어 후보 뷰(도메인/레벨 기준)
CREATE OR REPLACE VIEW v_term_candidates AS
SELECT 
  ast.standard_id, ast.standard_code, d.domain_name, sl.grade_range,
  ts.term_id, ts.term_type, ts.term_name
FROM achievement_standards ast
JOIN school_levels sl ON ast.level_id = sl.level_id
JOIN domains d ON ast.domain_id = d.domain_id
JOIN terms_symbols ts ON ts.level_id = sl.level_id AND ts.domain_id = d.domain_id;

-- 3.8 가로 연계 제안(HORIZONTAL) - 같은 레벨/영역, 내용요소가 같고 주문(순서) 인접
CREATE OR REPLACE VIEW v_horizontal_suggestions AS
WITH base AS (
  SELECT ast.standard_id, ast.standard_code, ast.level_id, ast.domain_id, ast.element_id, ast.standard_order
  FROM achievement_standards ast
)
SELECT 
  b1.standard_id AS src_standard_id,
  b2.standard_id AS dst_standard_id,
  'HORIZONTAL'::VARCHAR(15) AS relation_type,
  'same level/domain & same element; order distance<=1'::TEXT AS rationale,
  'rule'::VARCHAR(10) AS method,
  0.40::NUMERIC(3,2) AS confidence
FROM base b1
JOIN base b2
  ON b1.level_id=b2.level_id
 AND b1.domain_id=b2.domain_id
 AND b1.element_id IS NOT NULL
 AND b1.element_id=b2.element_id
 AND b1.standard_id<b2.standard_id
 AND abs(b1.standard_order - b2.standard_order) <= 1
LEFT JOIN achievement_standard_relations asr
  ON asr.src_standard_id=b1.standard_id AND asr.dst_standard_id=b2.standard_id AND asr.relation_type='HORIZONTAL'
WHERE asr.rel_id IS NULL;

-- 3.9 선수 제안(PREREQUISITE) - 같은 레벨/영역/내용요소, 순서가 앞선 항목을 선수로
CREATE OR REPLACE VIEW v_prerequisite_suggestions AS
WITH base AS (
  SELECT ast.standard_id, ast.standard_code, ast.level_id, ast.domain_id, ast.element_id, ast.standard_order
  FROM achievement_standards ast
)
SELECT 
  prior.standard_id AS src_standard_id,
  later.standard_id AS dst_standard_id,
  'PREREQUISITE'::VARCHAR(15) AS relation_type,
  'same level/domain & same element; order asc'::TEXT AS rationale,
  'rule'::VARCHAR(10) AS method,
  CASE WHEN (later.standard_order - prior.standard_order) >= 2 THEN 0.70 ELSE 0.55 END::NUMERIC(3,2) AS confidence
FROM base prior
JOIN base later
  ON prior.level_id=later.level_id
 AND prior.domain_id=later.domain_id
 AND prior.element_id IS NOT NULL
 AND prior.element_id=later.element_id
 AND prior.standard_order < later.standard_order
LEFT JOIN achievement_standard_relations asr
  ON asr.src_standard_id=prior.standard_id AND asr.dst_standard_id=later.standard_id AND asr.relation_type='PREREQUISITE'
WHERE asr.rel_id IS NULL;

-- 3.10 커버리지 리포트
CREATE OR REPLACE VIEW rpt_coverage AS
SELECT
  sl.grade_range,
  d.domain_name,
  COUNT(DISTINCT ast.standard_id) AS standards,
  COUNT(DISTINCT asr.rel_id) FILTER (WHERE asr.relation_type='PREREQUISITE') AS prereq_edges,
  COUNT(DISTINCT asr.rel_id) FILTER (WHERE asr.relation_type='HORIZONTAL')   AS horizontal_edges,
  COUNT(DISTINCT st.st_id) AS term_links,
  COUNT(DISTINCT sr.sr_id) AS representation_links,
  COUNT(DISTINCT scx.scx_id) AS context_links,
  COUNT(DISTINCT scon.sc_id) AS competency_links
FROM school_levels sl
CROSS JOIN domains d
LEFT JOIN achievement_standards ast ON ast.level_id=sl.level_id AND ast.domain_id=d.domain_id
LEFT JOIN achievement_standard_relations asr ON asr.src_standard_id=ast.standard_id
LEFT JOIN standard_terms st ON st.standard_id=ast.standard_id
LEFT JOIN standard_representations sr ON sr.standard_id=ast.standard_id
LEFT JOIN standard_contexts scx ON scx.standard_id=ast.standard_id
LEFT JOIN standard_competencies scon ON scon.standard_id=ast.standard_id
GROUP BY sl.grade_range, d.domain_name
ORDER BY sl.grade_range, d.domain_name;

-- 3.11 DAG 헬스 리포트(에지/노드/사이클 유무)
CREATE OR REPLACE VIEW rpt_dag_health AS
WITH nodes AS (
  SELECT COUNT(*) AS n FROM achievement_standards
),
edges AS (
  SELECT COUNT(*) AS e FROM achievement_standard_relations WHERE relation_type='PREREQUISITE'
),
cycle_check AS (
  SELECT EXISTS (
    WITH RECURSIVE walk(src, dst, path) AS (
      SELECT src_standard_id, dst_standard_id, ARRAY[src_standard_id, dst_standard_id]
      FROM achievement_standard_relations WHERE relation_type='PREREQUISITE'
      UNION ALL
      SELECT w.src, r.dst_standard_id, path || r.dst_standard_id
      FROM walk w
      JOIN achievement_standard_relations r
        ON w.dst = r.src_standard_id AND r.relation_type='PREREQUISITE'
      WHERE NOT r.dst_standard_id = ANY(path)
    )
    SELECT 1 FROM walk w
    JOIN achievement_standard_relations r
      ON w.dst = r.src_standard_id AND r.dst_standard_id = w.src AND r.relation_type='PREREQUISITE'
    LIMIT 1
  ) AS has_cycle
)
SELECT n AS nodes, e AS prereq_edges, has_cycle FROM nodes, edges, cycle_check;

-- =====================================================
-- 4) 사이클 검출 함수
-- =====================================================
CREATE OR REPLACE FUNCTION detect_prerequisite_cycles()
RETURNS TABLE (cycle_path TEXT, cycle_length INTEGER) AS $$
WITH RECURSIVE walk (start_id, curr_id, path, depth) AS (
  SELECT r.src_standard_id, r.dst_standard_id, ARRAY[r.src_standard_id, r.dst_standard_id], 1
  FROM achievement_standard_relations r
  WHERE r.relation_type='PREREQUISITE'
  UNION ALL
  SELECT w.start_id, r.dst_standard_id, w.path || r.dst_standard_id, depth+1
  FROM walk w
  JOIN achievement_standard_relations r
    ON w.curr_id = r.src_standard_id AND r.relation_type='PREREQUISITE'
  WHERE NOT r.dst_standard_id = ANY(w.path)
),
closed AS (
  SELECT path || w.start_id AS full_cycle
  FROM walk w
  JOIN achievement_standard_relations r
    ON w.curr_id = r.src_standard_id AND r.dst_standard_id = w.start_id AND r.relation_type='PREREQUISITE'
)
SELECT array_to_string(ARRAY(
         SELECT ast.standard_code
         FROM unnest(full_cycle) AS sid
         JOIN achievement_standards ast ON ast.standard_id=sid
       ), ' -> ') AS cycle_path,
       cardinality(full_cycle) AS cycle_length
FROM closed;
$$ LANGUAGE sql STABLE;

-- =====================================================
-- 5) 권한 부여(역할이 존재할 때만)
-- =====================================================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_reader') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA curriculum TO curriculum_reader';
    EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA curriculum TO curriculum_reader';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_writer') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA curriculum TO curriculum_writer';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA curriculum TO curriculum_writer';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_admin') THEN
    EXECUTE 'GRANT ALL PRIVILEGES ON SCHEMA curriculum TO curriculum_admin';
    EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA curriculum TO curriculum_admin';
  END IF;
END $$;

-- =====================================================
-- 6) 코멘트
-- =====================================================
COMMENT ON TABLE representation_types          IS '표상(표, 식, 그래프, 도형, 구체물, 말, 그림, 기호, 행동)';
COMMENT ON TABLE standard_representations      IS '성취기준-표상 매핑';
COMMENT ON TABLE context_labels                IS '콘텍스트 라벨(실생활/타교과 등)';
COMMENT ON TABLE standard_contexts             IS '성취기준-콘텍스트 매핑';
COMMENT ON TABLE competencies                  IS '교과 역량 마스터';
COMMENT ON TABLE standard_competencies         IS '성취기준-역량 매핑(가중치)';
COMMENT ON TABLE standard_terms                IS '성취기준-용어/기호 매핑';
COMMENT ON TABLE achievement_standard_relations IS '성취기준 간 관계(PREREQUISITE/HORIZONTAL)';

-- ============================ END OF v1.3.0 ============================
