-- =====================================================
-- 수학과 교육과정 스키마 업데이트 v1.3.0 (Edges & RAG 지원)
-- 적용일: 2025-08-22
-- 변경 요약:
--  1) 브리지/엣지 테이블: standard_terms, representation_types, standard_representations,
--     context_labels, standard_contexts, competencies, standard_competencies,
--     achievement_standard_relations(PREREQUISITE/HORIZONTAL)
--  2) 정렬·제안·검증 뷰: v_std_in_area, v_std_in_category, v_domain_coreideas,
--     v_standard_levels, v_level_alignment, v_standard_meta, v_term_candidates,
--     v_horizontal_suggestions, v_prerequisite_suggestions, rpt_coverage, rpt_dag_health
--  3) 사이클 검출 함수: detect_prerequisite_cycles()
-- 권한: 기존 roles에 신규 테이블 SELECT/CRUD 권한 부여
-- =====================================================

SET search_path TO curriculum, public;

-- -----------------------------
-- 0) 안전 보호
-- -----------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='curriculum') THEN
    RAISE EXCEPTION 'schema curriculum not found. Apply v1.2.0 first.';
  END IF;
END $$;

-- =====================================================
-- 1) 브리지/엣지 테이블
-- =====================================================

-- 1.1 성취기준 ↔ 용어/기호 확정 링크
CREATE TABLE IF NOT EXISTS standard_terms (
  st_id SERIAL PRIMARY KEY,
  standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  term_id INTEGER NOT NULL REFERENCES terms_symbols(term_id) ON DELETE CASCADE,
  relation_type VARCHAR(10) NOT NULL DEFAULT '필수' CHECK (relation_type IN ('필수','참고')),
  method VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
  confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
  evidence_text TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_standard_term UNIQUE (standard_id, term_id)
);

-- 1.2 표현 타입 목록(표/식/그래프/도형/구체물 등)
CREATE TABLE IF NOT EXISTS representation_types (
  rep_code VARCHAR(20) PRIMARY KEY,
  rep_name VARCHAR(40) NOT NULL,
  description TEXT
);

-- 1.3 성취기준 ↔ 표현 연결
CREATE TABLE IF NOT EXISTS standard_representations (
  sr_id SERIAL PRIMARY KEY,
  standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  rep_code VARCHAR(20) NOT NULL REFERENCES representation_types(rep_code) ON DELETE RESTRICT,
  method VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
  confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
  evidence_text TEXT,
  source_type VARCHAR(10) DEFAULT 'standard' CHECK (source_type IN ('standard','explain','terms')),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_standard_rep UNIQUE (standard_id, rep_code)
);

-- 1.4 맥락 라벨
CREATE TABLE IF NOT EXISTS context_labels (
  ctx_code VARCHAR(30) PRIMARY KEY,
  ctx_name VARCHAR(60) NOT NULL,
  description TEXT
);

-- 1.5 성취기준 ↔ 맥락 연결
CREATE TABLE IF NOT EXISTS standard_contexts (
  scx_id SERIAL PRIMARY KEY,
  standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  ctx_code VARCHAR(30) NOT NULL REFERENCES context_labels(ctx_code) ON DELETE RESTRICT,
  method VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
  confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
  evidence_text TEXT,
  CONSTRAINT uq_standard_ctx UNIQUE (standard_id, ctx_code)
);

-- 1.6 역량 마스터(5대 역량)
CREATE TABLE IF NOT EXISTS competencies (
  competency_id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE,
  name VARCHAR(50) NOT NULL,
  description TEXT
);

-- 1.7 성취기준 ↔ 역량(N:M, 가중치)
CREATE TABLE IF NOT EXISTS standard_competencies (
  sc_id SERIAL PRIMARY KEY,
  standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  competency_id INTEGER NOT NULL REFERENCES competencies(competency_id) ON DELETE CASCADE,
  weight NUMERIC(3,2) NOT NULL CHECK (weight BETWEEN 0 AND 1),
  method VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
  CONSTRAINT uq_standard_competency UNIQUE (standard_id, competency_id)
);

-- 1.8 성취기준 간 관계(선수/가로)
CREATE TABLE IF NOT EXISTS achievement_standard_relations (
  asr_id SERIAL PRIMARY KEY,
  from_standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  to_standard_id INTEGER NOT NULL REFERENCES achievement_standards(standard_id) ON DELETE CASCADE,
  relation_type VARCHAR(15) NOT NULL CHECK (relation_type IN ('PREREQUISITE','HORIZONTAL')),
  method VARCHAR(10) NOT NULL DEFAULT 'rule' CHECK (method IN ('rule','llm','human')),
  confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
  evidence_text TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_asr UNIQUE (from_standard_id, to_standard_id, relation_type),
  CONSTRAINT chk_asr_self CHECK (from_standard_id <> to_standard_id)
);

-- 인덱스 최적화
CREATE INDEX IF NOT EXISTS idx_asr_from ON achievement_standard_relations(from_standard_id);
CREATE INDEX IF NOT EXISTS idx_asr_to   ON achievement_standard_relations(to_standard_id);
CREATE INDEX IF NOT EXISTS idx_asr_type ON achievement_standard_relations(relation_type);

-- 타임스탬프 자동 갱신
CREATE OR REPLACE FUNCTION curriculum.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_standard_terms_updated_at
  BEFORE UPDATE ON standard_terms
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_standard_representations_updated_at
  BEFORE UPDATE ON standard_representations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_standard_contexts_updated_at
  BEFORE UPDATE ON standard_contexts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_standard_competencies_updated_at
  BEFORE UPDATE ON standard_competencies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_asr_updated_at
  BEFORE UPDATE ON achievement_standard_relations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 2) 시드 데이터(표현/맥락/역량)
-- =====================================================

-- 표현 타입(존재하지 않을 때만)
INSERT INTO representation_types (rep_code, rep_name, description) VALUES
('table','표','표 형태의 표현'),
('expr','식/기호','수식·기호를 통한 표현'),
('graph','그래프','점·선·막대 등 그래프'),
('shape','도형','평면/입체도형'),
('manip','구체물/도구','쌓기나무, 자, 시계 등 도구')
ON CONFLICT (rep_code) DO NOTHING;

-- 맥락 라벨
INSERT INTO context_labels (ctx_code, ctx_name, description) VALUES
('real_life','실생활','가격, 달력, 시간, 길이 등'),
('data','자료수집·표·그래프','자료 수집/정리/해석'),
('measurement','측정','길이/들이/무게/시간 등'),
('geometry','도형·공간','평면/입체/공간감각'),
('pattern','규칙성','규칙 찾기/표현')
ON CONFLICT (ctx_code) DO NOTHING;

-- 역량(5대)
INSERT INTO competencies (code, name, description) VALUES
('PS','문제해결','수학적 문제 해결'),
('RE','추론','추론과 정당화'),
('CM','의사소통','수학적 의사소통'),
('CN','연결','수학 내/외부 연결'),
('IP','정보처리','자료, 도구와 기술 활용')
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- 3) 정렬/제안/검증 뷰
-- =====================================================

-- 3.1 표준 → 영역
CREATE OR REPLACE VIEW v_std_in_area AS
SELECT ast.standard_id, ast.standard_code, d.domain_id, d.domain_code, d.domain_name
FROM achievement_standards ast
JOIN domains d ON d.domain_id = ast.domain_id;

-- 3.2 표준 → 범주 (content_elements 경유)
CREATE OR REPLACE VIEW v_std_in_category AS
SELECT ast.standard_id, ast.standard_code, cat.category_id, cat.category_name
FROM achievement_standards ast
LEFT JOIN content_elements ce ON ce.element_id = ast.element_id
LEFT JOIN categories cat ON cat.category_id = ce.category_id;

-- 3.3 영역 → 핵심아이디어
CREATE OR REPLACE VIEW v_domain_coreideas AS
SELECT ci.idea_id, d.domain_id, d.domain_name, ci.idea_order, ci.idea_content
FROM core_ideas ci
JOIN domains d ON d.domain_id = ci.domain_id
ORDER BY d.domain_order, ci.idea_order;

-- 3.4 표준별 성취수준(A~E)
CREATE OR REPLACE VIEW v_standard_levels AS
SELECT ast.standard_id, ast.standard_code, al.level_code, al.level_name, sal.level_description
FROM standard_achievement_levels sal
JOIN achievement_standards ast ON ast.standard_id = sal.standard_id
JOIN achievement_levels al ON al.level_code = sal.level_code;

-- 3.5 표준레벨 ↔ 영역레벨×범주 정렬
CREATE OR REPLACE VIEW v_level_alignment AS
SELECT
  ast.standard_id,
  ast.standard_code,
  sl.level_id,
  d.domain_id,
  cat.category_id,
  sal.level_code,
  dal.dal_id IS NOT NULL AS aligned,
  dal.dal_id,
  sal.level_description      AS standard_level_desc,
  dal.level_description      AS domain_level_desc
FROM achievement_standards ast
JOIN school_levels sl ON sl.level_id = ast.level_id
JOIN domains d ON d.domain_id = ast.domain_id
LEFT JOIN content_elements ce ON ce.element_id = ast.element_id
LEFT JOIN categories cat ON cat.category_id = ce.category_id
LEFT JOIN standard_achievement_levels sal ON sal.standard_id = ast.standard_id
LEFT JOIN domain_achievement_levels dal
  ON  dal.level_id = sl.level_id
  AND dal.domain_id = d.domain_id
  AND dal.level_code = sal.level_code
  AND dal.category_id = cat.category_id;

-- 3.6 표준 메타 집계(JSON)
CREATE OR REPLACE VIEW v_standard_meta AS
SELECT
  ast.standard_id,
  ast.standard_code,
  JSONB_BUILD_OBJECT(
    '성취기준 해설', COALESCE((
      SELECT JSONB_AGG(se.explanation_content ORDER BY se.explanation_order)
      FROM standard_explanations se
      WHERE se.standard_id = ast.standard_id AND se.explanation_type='성취기준 해설'
    ), '[]'::JSONB),
    '적용시 고려사항', COALESCE((
      SELECT JSONB_AGG(se.explanation_content ORDER BY se.explanation_order)
      FROM standard_explanations se
      WHERE se.standard_id = ast.standard_id AND se.explanation_type='적용시 고려사항'
    ), '[]'::JSONB)
  ) AS meta_json
FROM achievement_standards ast;

-- 3.7 용어/기호 후보(동일 학년군×영역)
CREATE OR REPLACE VIEW v_term_candidates AS
SELECT
  ast.standard_id, ast.standard_code, ts.term_id, ts.term_type, ts.term_name,
  (st.st_id IS NOT NULL) AS confirmed
FROM achievement_standards ast
JOIN terms_symbols ts
  ON ts.level_id = ast.level_id AND ts.domain_id = ast.domain_id
LEFT JOIN standard_terms st
  ON st.standard_id = ast.standard_id AND st.term_id = ts.term_id;

-- 3.8 가로 연계 제안(룰: 동일 level/domain/element, 인접 order)
CREATE OR REPLACE VIEW v_horizontal_suggestions AS
SELECT DISTINCT
  LEAST(a.standard_id, b.standard_id) AS from_standard_id,
  GREATEST(a.standard_id, b.standard_id) AS to_standard_id,
  'HORIZONTAL'::VARCHAR(15) AS relation_type,
  'rule'::VARCHAR(10) AS method,
  0.60::NUMERIC(3,2) AS confidence,
  'same(level,domain,element) & adjacent order' AS evidence_text
FROM achievement_standards a
JOIN achievement_standards b
  ON a.level_id = b.level_id
 AND a.domain_id = b.domain_id
 AND COALESCE(a.element_id, -1) = COALESCE(b.element_id, -1)
 AND ABS(a.standard_order - b.standard_order) = 1
 AND a.standard_id <> b.standard_id
LEFT JOIN achievement_standard_relations asr
  ON asr.from_standard_id = LEAST(a.standard_id, b.standard_id)
 AND asr.to_standard_id   = GREATEST(a.standard_id, b.standard_id)
 AND asr.relation_type='HORIZONTAL'
WHERE asr.asr_id IS NULL;

-- 3.9 선수 제안(룰: 같은 domain/element에서 상위 학년군 순서↑)
CREATE OR REPLACE VIEW v_prerequisite_suggestions AS
WITH base AS (
  SELECT ast.standard_id, ast.standard_code, ast.domain_id, ast.element_id,
         sl.level_code, ast.standard_order
  FROM achievement_standards ast
  JOIN school_levels sl ON sl.level_id = ast.level_id
)
SELECT
  a.standard_id AS from_standard_id,
  b.standard_id AS to_standard_id,
  'PREREQUISITE'::VARCHAR(15) AS relation_type,
  'rule'::VARCHAR(10) AS method,
  0.65::NUMERIC(3,2) AS confidence,
  'same(domain,element) & higher grade band' AS evidence_text
FROM base a
JOIN base b
  ON a.domain_id = b.domain_id
 AND COALESCE(a.element_id,-1) = COALESCE(b.element_id,-1)
 AND b.level_code > a.level_code
 AND (b.level_code - a.level_code) IN (2,3) -- 초등 1-2→3-4→5-6, 초등→중 등
LEFT JOIN achievement_standard_relations asr
  ON asr.from_standard_id=a.standard_id
 AND asr.to_standard_id=b.standard_id
 AND asr.relation_type='PREREQUISITE'
WHERE asr.asr_id IS NULL;

-- 3.10 커버리지 리포트
CREATE OR REPLACE VIEW rpt_coverage AS
SELECT
  sl.school_type, sl.grade_range, d.domain_name,
  COUNT(DISTINCT ast.standard_id) AS standards,
  COUNT(DISTINCT sal.sal_id)      AS std_levels,
  SUM(CASE WHEN ast.element_id IS NULL THEN 1 ELSE 0 END) AS missing_element,
  COUNT(DISTINCT st.st_id)        AS confirmed_terms,
  COUNT(DISTINCT sr.sr_id)        AS rep_links,
  COUNT(DISTINCT scx.scx_id)      AS ctx_links
FROM school_levels sl
CROSS JOIN domains d
LEFT JOIN achievement_standards ast ON ast.level_id=sl.level_id AND ast.domain_id=d.domain_id
LEFT JOIN standard_achievement_levels sal ON sal.standard_id=ast.standard_id
LEFT JOIN standard_terms st ON st.standard_id=ast.standard_id
LEFT JOIN standard_representations sr ON sr.standard_id=ast.standard_id
LEFT JOIN standard_contexts scx ON scx.standard_id=ast.standard_id
GROUP BY sl.level_id, sl.school_type, sl.grade_range, d.domain_id, d.domain_name
ORDER BY sl.level_id, d.domain_id;

-- 3.11 DAG 헬스(정점/엣지/평균 out-degree)
CREATE OR REPLACE VIEW rpt_dag_health AS
SELECT
  COUNT(DISTINCT ast.standard_id) AS vertices,
  COUNT(*) FILTER (WHERE asr.relation_type='PREREQUISITE') AS edges_prereq,
  ROUND( (COUNT(*) FILTER (WHERE asr.relation_type='PREREQUISITE'))::numeric
        / NULLIF(COUNT(DISTINCT ast.standard_id),0), 3) AS avg_out_degree
FROM achievement_standards ast
LEFT JOIN achievement_standard_relations asr
  ON asr.from_standard_id = ast.standard_id
;

-- =====================================================
-- 4) 사이클 검출 함수 (PREREQUISITE 전용)
-- =====================================================
CREATE OR REPLACE FUNCTION detect_prerequisite_cycles()
RETURNS TABLE (cycle_path TEXT) AS $$
WITH RECURSIVE walk AS (
  -- 시작 간선
  SELECT
    from_standard_id,
    to_standard_id,
    ARRAY[from_standard_id] AS path,
    from_standard_id AS start_id
  FROM achievement_standard_relations
  WHERE relation_type='PREREQUISITE'
  UNION ALL
  -- 확장
  SELECT
    w.from_standard_id,
    asr.to_standard_id,
    path || asr.to_standard_id,
    start_id
  FROM walk w
  JOIN achievement_standard_relations asr
    ON asr.from_standard_id = w.to_standard_id
  WHERE asr.relation_type='PREREQUISITE'
    AND NOT (asr.to_standard_id = ANY(path)) -- 아직 방문 안함
),
cycles AS (
  SELECT path
  FROM walk
  WHERE to_standard_id = start_id -- 시작점으로 되돌아옴 => 사이클
)
SELECT
  (SELECT string_agg(ast.standard_code, ' -> ' ORDER BY idx)
   FROM (
     SELECT unnest(path) WITH ORDINALITY AS sid, ordinality AS idx
   ) q
   JOIN achievement_standards ast ON ast.standard_id = q.sid
  ) AS cycle_path
FROM cycles
$$ LANGUAGE sql;

-- =====================================================
-- 5) 권한(기존 롤에 신규 테이블 권한 부여)
-- =====================================================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_reader') THEN
    GRANT SELECT ON standard_terms, representation_types, standard_representations,
                 context_labels, standard_contexts, competencies, standard_competencies,
                 achievement_standard_relations TO curriculum_reader;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_writer') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON standard_terms, representation_types, standard_representations,
                 context_labels, standard_contexts, competencies, standard_competencies,
                 achievement_standard_relations TO curriculum_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='curriculum_admin') THEN
    GRANT ALL PRIVILEGES ON TABLE standard_terms, representation_types, standard_representations,
                           context_labels, standard_contexts, competencies, standard_competencies,
                           achievement_standard_relations TO curriculum_admin;
  END IF;
END $$;

-- 코멘트
COMMENT ON TABLE standard_terms IS '성취기준 ↔ 용어/기호 확정 링크(필수/참고, 근거/신뢰도)';
COMMENT ON TABLE standard_representations IS '성취기준 ↔ 표현(표/식/그래프/도형/구체물) 연결';
COMMENT ON TABLE standard_contexts IS '성취기준 ↔ 맥락(실생활/측정/자료/규칙 등) 연결';
COMMENT ON TABLE competencies IS '수학 교과 역량 마스터';
COMMENT ON TABLE standard_competencies IS '성취기준 ↔ 역량 가중치 매핑';
COMMENT ON TABLE achievement_standard_relations IS '성취기준 간 관계(DAG: PREREQUISITE, 가로: HORIZONTAL)';

-- 버전 메모
COMMENT ON SCHEMA curriculum IS '2022 개정 수학과 교육과정 스키마 v1.3 (Edges & RAG 지원)';
-- =====================================================

