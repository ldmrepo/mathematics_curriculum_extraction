#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수학과 교육과정 데이터 로딩 스크립트 v1.3.1 (schema-qualified)
- PostgreSQL 스키마 v1.2.0 / 패치 v1.3.0 대응
- 모든 SQL에 스키마 접두어 자동 적용(tbl()) → search_path 의존 제거
- 연결 옵션으로 search_path도 보조 고정
- 성취기준/성취수준/핵심아이디어/내용요소/용어·기호/해설 로드
- 시퀀스 보정(setval) 유틸 + 진단 로깅 강화
"""

import os
import sys
import csv
import logging
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# -----------------------
# 환경 변수 & 상수
# -----------------------
load_dotenv()

DB_SCHEMA = os.getenv("DB_SCHEMA", "curriculum")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "mathematics_curriculum"),
    "user": os.getenv("DB_USER", "curriculum"),
    "password": os.getenv("DB_PASSWORD", "curriculum"),
}

BASE = Path(__file__).resolve().parent.parent  # .../database
DATA_PATH = (BASE.parent / "data").resolve()  # 상위 폴더의 data 디렉토리

ACHIEVEMENT_LEVELS_PATH    = DATA_PATH / "achievement_levels"
ACHIEVEMENT_STANDARDS_PATH = DATA_PATH / "achievement_standards"
CONTENT_SYSTEM_PATH        = DATA_PATH / "content_system"
REFERENCE_PATH             = DATA_PATH / "reference"
TERMS_SYMBOLS_PATH         = DATA_PATH / "terms_symbols"

# -----------------------
# 로깅
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data_load.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("data_loader")


# -----------------------
# 유틸
# -----------------------
def tbl(name: str) -> str:
    """스키마 접두어 적용."""
    return f'{DB_SCHEMA}."{name}"' if not name.startswith(DB_SCHEMA + ".") else name

def _strip_brackets(code: str) -> str:
    """'[2수02-01]' -> '2수02-01'"""
    if not code:
        return code
    code = code.strip()
    if code.startswith("["):
        code = code[1:]
    if code.endswith("]"):
        code = code[:-1]
    return code.strip()

def _read_csv(path: Path):
    """CSV를 utf-8-sig 우선 시도, 실패 시 utf-8 재시도."""
    try:
        return csv.DictReader(open(path, "r", encoding="utf-8-sig"))
    except UnicodeError:
        return csv.DictReader(open(path, "r", encoding="utf-8"))


class DataLoader:
    def __init__(self):
        self.conn = None
        self.cur = None

    # -----------------------
    # 연결/해제 + 진단
    # -----------------------
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                **DB_CONFIG,
                options=f"-c search_path={DB_SCHEMA},public"
            )
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            # 보조 안전망(세션 중간 변경 방지)
            self.cur.execute(f"SET search_path TO {DB_SCHEMA}, public;")
            # 진단
            self.cur.execute("SHOW search_path;")
            logger.info("search_path: %s", self.cur.fetchone()["search_path"])
            self.cur.execute(
                "SELECT to_regclass(%s) AS ok_schema_sl, to_regclass(%s) AS ok_public_sl;",
                (f"{DB_SCHEMA}.school_levels", "school_levels")
            )
            logger.info("to_regclass check: %s", self.cur.fetchone())
            logger.info("데이터베이스 연결 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False

    def disconnect(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("데이터베이스 연결 종료")

    # -----------------------
    # 스키마/핵심 테이블 존재 확인
    # -----------------------
    def ensure_schema_ready(self):
        try:
            self.cur.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name=%s",
                (DB_SCHEMA,),
            )
            if not self.cur.fetchone():
                raise RuntimeError(f"Schema '{DB_SCHEMA}' not found. Apply DB schema v1.2.0 first.")
            # 필수 테이블 존재 확인 (없으면 사용자에게 바로 피드백)
            must_tables = [
                "school_levels", "domains", "categories",
                "content_elements", "achievement_standards",
                "standard_achievement_levels", "standard_explanations",
                "terms_symbols", "core_ideas",
            ]
            missing = []
            for t in must_tables:
                self.cur.execute("SELECT to_regclass(%s) AS reg", (f"{DB_SCHEMA}.{t}",))
                if self.cur.fetchone()["reg"] is None:
                    missing.append(t)
            if missing:
                raise RuntimeError(f"Missing tables: {', '.join(missing)}")
            return True
        except Exception as e:
            logger.error(f"스키마 준비 확인 실패: {e}")
            return False

    # -----------------------
    # 시퀀스 보정
    # -----------------------
    def fix_sequences(self):
        """
        SERIAL/BIGSERIAL(또는 IDENTITY) 시퀀스를 실제 최대 PK값으로 맞추기.
        """
        try:
            logger.info("시퀀스 보정 시작...")

            targets = [
                ("content_elements", "element_id"),
                ("terms_symbols", "term_id"),
                ("core_ideas", "idea_id"),
                ("achievement_standards", "standard_id"),
                ("standard_explanations", "explanation_id"),
            ]

            for table, id_col in targets:
                # seq name 가져오기
                self.cur.execute(
                    "SELECT pg_get_serial_sequence(%s, %s) AS seqname",
                    (f"{DB_SCHEMA}.{table}", id_col)
                )
                row = self.cur.fetchone()
                seqname = row and row.get("seqname")
                if not seqname:
                    # IDENTITY 컬럼이 아니라면 건너뛰기
                    logger.info(f"  시퀀스 없음: {table}.{id_col} (건너뜀)")
                    continue

                # setval: MAX(id) 서브쿼리 사용
                sql = f"""
                    SELECT setval(
                        %s,
                        COALESCE((SELECT MAX({id_col}) FROM {DB_SCHEMA}.{table}), 1),
                        true
                    );
                """
                self.cur.execute(sql, (seqname,))
                logger.info(f"  setval 적용: {seqname}")

            self.conn.commit()
            logger.info("시퀀스 보정 완료")
            return True

        except Exception as e:
            self.conn.rollback()
            logger.warning(f"시퀀스 보정 실패(계속 진행): {e}")
            return False

    # -----------------------
    # 1) 기준 데이터
    # -----------------------
    def load_reference_data(self):
        try:
            logger.info("기준 데이터 로딩...")

            # school_levels
            fp = REFERENCE_PATH / "school_levels.csv"
            reader = _read_csv(fp)
            for row in reader:
                self.cur.execute(f"""
                    INSERT INTO {tbl('school_levels')}
                        (school_type, grade_range, grade_start, grade_end, level_code)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (level_code) DO UPDATE
                    SET school_type = EXCLUDED.school_type,
                        grade_range = EXCLUDED.grade_range,
                        grade_start = EXCLUDED.grade_start,
                        grade_end = EXCLUDED.grade_end;
                """, (
                    row["school_type"],
                    row["grade_range"],
                    int(row["grade_start"]),
                    int(row["grade_end"]),
                    int(row["level_code"]),
                ))

            # domains
            fp = REFERENCE_PATH / "domains.csv"
            reader = _read_csv(fp)
            for row in reader:
                self.cur.execute(f"""
                    INSERT INTO {tbl('domains')}
                        (domain_id, domain_name, domain_order, domain_code, description)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (domain_code) DO UPDATE
                    SET domain_name = EXCLUDED.domain_name,
                        domain_order = EXCLUDED.domain_order,
                        description = EXCLUDED.description;
                """, (
                    int(row.get("domain_id", "0")) or None,
                    row["domain_name"],
                    int(row["domain_order"]),
                    row["domain_code"],
                    row.get("description"),
                ))

            # categories
            fp = REFERENCE_PATH / "categories.csv"
            reader = _read_csv(fp)
            for row in reader:
                self.cur.execute(f"""
                    INSERT INTO {tbl('categories')}
                        (category_id, category_name, category_order, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (category_name) DO UPDATE
                    SET category_order = EXCLUDED.category_order,
                        description = EXCLUDED.description;
                """, (
                    int(row.get("category_id", "0")) or None,
                    row["category_name"],
                    int(row["category_order"]),
                    row.get("description"),
                ))

            self.conn.commit()
            logger.info("기준 데이터 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"기준 데이터 로딩 실패: {e}")
            return False

    # -----------------------
    # 1.5) 핵심 아이디어
    # -----------------------
    def load_core_ideas(self):
        try:
            logger.info("핵심 아이디어 로딩...")
            fp = CONTENT_SYSTEM_PATH / "core_ideas.csv"
            if not fp.exists():
                logger.warning("core_ideas.csv 미존재: 건너뜁니다.")
                return True
            reader = _read_csv(fp)
            for row in reader:
                self.cur.execute(f"""
                    INSERT INTO {tbl('core_ideas')}
                        (idea_id, domain_id, idea_content, idea_order)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (idea_id) DO UPDATE
                    SET domain_id = EXCLUDED.domain_id,
                        idea_content = EXCLUDED.idea_content,
                        idea_order = EXCLUDED.idea_order;
                """, (
                    int(row["idea_id"]),
                    int(row["domain_id"]),
                    row["idea_content"],
                    int(row["idea_order"]),
                ))
            self.conn.commit()
            logger.info("핵심 아이디어 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"핵심 아이디어 로딩 실패: {e}")
            return False

    # -----------------------
    # 2) 내용 요소
    # -----------------------
    def load_content_elements(self):
        try:
            logger.info("내용 요소 로딩...")
            for fp in CONTENT_SYSTEM_PATH.glob("content_elements_*.csv"):
                logger.info(f"  파일: {fp.name}")
                reader = _read_csv(fp)

                id_based = all(
                    k in reader.fieldnames
                    for k in ["element_id", "domain_id", "level_id", "category_id", "element_name", "element_description", "element_order"]
                )

                if id_based:
                    for row in reader:
                        self.cur.execute(f"""
                            INSERT INTO {tbl('content_elements')}
                                (element_id, domain_id, level_id, category_id, element_name, element_description, element_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (element_id) DO UPDATE
                            SET domain_id = EXCLUDED.domain_id,
                                level_id = EXCLUDED.level_id,
                                category_id = EXCLUDED.category_id,
                                element_name = EXCLUDED.element_name,
                                element_description = EXCLUDED.element_description,
                                element_order = EXCLUDED.element_order;
                        """, (
                            int(row["element_id"]),
                            int(row["domain_id"]),
                            int(row["level_id"]),
                            int(row["category_id"]),
                            row["element_name"],
                            row.get("element_description"),
                            int(row["element_order"]),
                        ))
                else:
                    # 한글 헤더 버전
                    element_order = 1
                    for row in reader:
                        self.cur.execute(f"SELECT level_id FROM {tbl('school_levels')} WHERE grade_range = %s", (row["학년(군)"],))
                        lv = self.cur.fetchone()
                        if not lv:
                            logger.warning(f"학교급 미매핑: {row['학년(군)']}")
                            continue

                        self.cur.execute(f"SELECT domain_id FROM {tbl('domains')} WHERE domain_name = %s", (row["영역"],))
                        dm = self.cur.fetchone()
                        if not dm:
                            logger.warning(f"영역 미매핑: {row['영역']}")
                            continue

                        self.cur.execute(f"SELECT category_id FROM {tbl('categories')} WHERE category_name = %s", (row["범주"],))
                        ct = self.cur.fetchone()
                        if not ct:
                            logger.warning(f"범주 미매핑: {row['범주']}")
                            continue

                        self.cur.execute(f"""
                            INSERT INTO {tbl('content_elements')}
                                (domain_id, level_id, category_id, element_name, element_description, element_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (domain_id, level_id, category_id, element_order) DO UPDATE
                            SET element_name = EXCLUDED.element_name,
                                element_description = EXCLUDED.element_description;
                        """, (dm["domain_id"], lv["level_id"], ct["category_id"], row["내용 요소"], row.get("설명"), element_order))
                        element_order += 1

            self.conn.commit()
            logger.info("내용 요소 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"내용 요소 로딩 실패: {e}")
            return False

    # -----------------------
    # 3) 성취기준
    # -----------------------
    def load_achievement_standards(self):
        try:
            logger.info("성취기준 로딩...")
            for fp in ACHIEVEMENT_STANDARDS_PATH.glob("achievement_standards_*.csv"):
                if "all" in fp.name:
                    continue
                logger.info(f"  파일: {fp.name}")
                reader = _read_csv(fp)

                for row in reader:
                    std_code = row["standard_code"].strip()

                    # level_code (2수01-03 → 2)
                    try:
                        level_num = int(std_code.split("수")[0])
                    except Exception:
                        logger.warning(f"[성취기준] level_code 파싱 실패: {std_code}")
                        continue

                    # domain_code (2수01-03 → '01')
                    try:
                        domain_code = std_code.split("수")[1][:2]
                    except Exception:
                        logger.warning(f"[성취기준] domain_code 파싱 실패: {std_code}")
                        continue

                    # FK 조회
                    self.cur.execute(f"SELECT level_id FROM {tbl('school_levels')} WHERE level_code = %s", (level_num,))
                    lv = self.cur.fetchone()
                    if not lv:
                        logger.warning(f"[성취기준] 학교급 미존재: {std_code} (level_code={level_num})")
                        continue

                    self.cur.execute(f"SELECT domain_id FROM {tbl('domains')} WHERE domain_code = %s", (domain_code,))
                    dm = self.cur.fetchone()
                    if not dm:
                        logger.warning(f"[성취기준] 영역 미존재: {std_code} (domain_code={domain_code})")
                        continue

                    element_id = row.get("element_id")
                    element_id = int(element_id) if element_id not in (None, "",) else None

                    # CSV의 standard_order는 무시하고, 표준코드의 뒷자리로 일관 계산
                    try:
                        standard_order = int(std_code.split("-")[1])
                    except Exception:
                        logger.warning(f"[성취기준] standard_order 파생 실패: {std_code} -> 0으로 저장")
                        standard_order = 0

                    self.cur.execute(f"""
                        INSERT INTO {tbl('achievement_standards')}
                          (standard_id, standard_code, level_id, domain_id, element_id, standard_title, standard_content, standard_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (standard_code) DO UPDATE
                        SET level_id = EXCLUDED.level_id,
                            domain_id = EXCLUDED.domain_id,
                            element_id = EXCLUDED.element_id,
                            standard_title = EXCLUDED.standard_title,
                            standard_content = EXCLUDED.standard_content,
                            standard_order = EXCLUDED.standard_order;
                    """, (
                        int(row.get("standard_id", "0")) or None,
                        std_code,
                        lv["level_id"],
                        dm["domain_id"],
                        element_id,
                        row.get("standard_title", ""),
                        row["standard_content"],
                        standard_order,
                    ))

            self.conn.commit()
            logger.info("성취기준 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"성취기준 로딩 실패: {e}")
            return False

    # -----------------------
    # 4) 성취기준별 성취수준
    # -----------------------
    def load_standard_achievement_levels(self):
        try:
            logger.info("성취기준별 성취수준 로딩...")
            for fp in ACHIEVEMENT_LEVELS_PATH.glob("achievement_levels_*.csv"):
                logger.info(f"  파일: {fp.name}")
                reader = _read_csv(fp)

                for row in reader:
                    std_code  = _strip_brackets(row.get("성취기준", "").strip())
                    level_cd  = row.get("수준", "").strip()
                    level_txt = row.get("성취수준", "").strip()

                    if not std_code or not level_cd:
                        logger.warning(f"[성취수준] 누락된 값: {row}")
                        continue

                    self.cur.execute(f"SELECT standard_id FROM {tbl('achievement_standards')} WHERE standard_code = %s", (std_code,))
                    std = self.cur.fetchone()
                    if not std:
                        logger.warning(f"[성취수준] 성취기준 미존재: {std_code}")
                        continue

                    self.cur.execute(f"""
                        INSERT INTO {tbl('standard_achievement_levels')}
                            (standard_id, level_code, level_description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (standard_id, level_code) DO UPDATE
                        SET level_description = EXCLUDED.level_description;
                    """, (std["standard_id"], level_cd, level_txt))

            self.conn.commit()
            logger.info("성취기준별 성취수준 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"성취기준별 성취수준 로딩 실패: {e}")
            return False

    # -----------------------
    # 5) 성취기준 해설/적용시 고려사항
    # -----------------------
    def load_standard_explanations(self):
        try:
            logger.info("성취기준 해설·고려사항 로딩...")
            for fp in ACHIEVEMENT_STANDARDS_PATH.glob("standard_explanations_*.csv"):
                logger.info(f"  파일: {fp.name}")
                reader = _read_csv(fp)

                counters = defaultdict(int)  # (standard_id, explanation_type) -> order
                rows = list(reader)

                for row in rows:
                    try:
                        std_id = int(row.get("standard_id", "0") or "0")
                    except Exception:
                        std_id = 0

                    exp_type = (row.get("explanation_type") or "").strip()
                    exp_text = row.get("explanation_content")

                    if std_id == 0:
                        # 공통/메타는 현재 스킵
                        continue
                    if not exp_type or not exp_text:
                        logger.warning(f"[해설] 필수값 누락: {row}")
                        continue

                    counters[(std_id, exp_type)] += 1
                    exp_order = counters[(std_id, exp_type)]

                    self.cur.execute(f"""
                        INSERT INTO {tbl('standard_explanations')}
                            (standard_id, explanation_type, explanation_content, explanation_order)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (standard_id, explanation_type, explanation_order) DO UPDATE
                        SET explanation_content = EXCLUDED.explanation_content;
                    """, (std_id, exp_type, exp_text, exp_order))

            self.conn.commit()
            logger.info("성취기준 해설·고려사항 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"성취기준 해설·고려사항 로딩 실패: {e}")
            return False

    # -----------------------
    # 6) 용어/기호
    # -----------------------
    def load_terms_symbols(self):
        try:
            logger.info("용어/기호 로딩...")
            for fp in TERMS_SYMBOLS_PATH.glob("terms_symbols_*.csv"):
                logger.info(f"  파일: {fp.name}")
                reader = _read_csv(fp)

                id_based = all(k in reader.fieldnames for k in
                               ["term_id", "level_id", "domain_id", "term_type", "term_name", "term_description"])

                if id_based:
                    for row in reader:
                        self.cur.execute(f"""
                            INSERT INTO {tbl('terms_symbols')}
                              (term_id, level_id, domain_id, term_type, term_name, term_description, latex_expression)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (term_id) DO UPDATE
                            SET level_id = EXCLUDED.level_id,
                                domain_id = EXCLUDED.domain_id,
                                term_type = EXCLUDED.term_type,
                                term_name = EXCLUDED.term_name,
                                term_description = EXCLUDED.term_description,
                                latex_expression = EXCLUDED.latex_expression;
                        """, (
                            int(row["term_id"]),
                            int(row["level_id"]),
                            int(row["domain_id"]),
                            row["term_type"],
                            row["term_name"],
                            row.get("term_description"),
                            row.get("latex_expression"),
                        ))
                else:
                    for row in reader:
                        self.cur.execute(f"SELECT level_id FROM {tbl('school_levels')} WHERE grade_range = %s", (row["학년(군)"],))
                        lv = self.cur.fetchone()
                        if not lv:
                            logger.warning(f"[용어] 학교급 미매핑: {row['학년(군)']}")
                            continue

                        self.cur.execute(f"SELECT domain_id FROM {tbl('domains')} WHERE domain_name = %s", (row["영역"],))
                        dm = self.cur.fetchone()
                        if not dm:
                            logger.warning(f"[용어] 영역 미매핑: {row['영역']}")
                            continue

                        self.cur.execute(f"""
                            INSERT INTO {tbl('terms_symbols')}
                              (level_id, domain_id, term_type, term_name, term_description, latex_expression)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (level_id, domain_id, term_name) DO UPDATE
                            SET term_type = EXCLUDED.term_type,
                                term_description = EXCLUDED.term_description,
                                latex_expression = EXCLUDED.latex_expression;
                        """, (lv["level_id"], dm["domain_id"], row["구분"], row["용어/기호"], row.get("설명"), row.get("latex")))

            self.conn.commit()
            logger.info("용어/기호 로딩 완료")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"용어/기호 로딩 실패: {e}")
            return False

    # -----------------------
    # 7) 검증 리포트
    # -----------------------
    def verify_data(self):
        try:
            logger.info("데이터 검증 시작...")

            tables = [
                "school_levels", "domains", "categories",
                "achievement_standards", "standard_achievement_levels",
                "content_elements", "terms_symbols", "core_ideas",
                "standard_explanations",
            ]
            for t in tables:
                self.cur.execute(f"SELECT COUNT(*) AS cnt FROM {tbl(t)};")
                c = self.cur.fetchone()
                logger.info(f"  {t}: {c['cnt']} rows")

            # 초1-2 성취기준 수
            self.cur.execute(f"""
                SELECT COUNT(*) AS cnt
                FROM {tbl('achievement_standards')} ast
                JOIN {tbl('school_levels')} sl ON ast.level_id = sl.level_id
                WHERE sl.level_code = 2;
            """)
            c = self.cur.fetchone()
            logger.info(f"  초1-2 표준 수: {c['cnt']}")

            # 성취수준 예시 체크
            self.cur.execute(f"""
                SELECT ast.standard_code, sal.level_code, LEFT(sal.level_description, 60) AS preview
                FROM {tbl('achievement_standards')} ast
                JOIN {tbl('standard_achievement_levels')} sal ON sal.standard_id = ast.standard_id
                WHERE ast.standard_code IN ('2수02-01','2수02-02')
                ORDER BY ast.standard_code, sal.level_code;
            """)
            for r in self.cur.fetchall():
                logger.info(f"  성취수준 검증: {r['standard_code']} [{r['level_code']}] {r['preview']}")

            # element_id 누락
            self.cur.execute(f"""
                SELECT COUNT(*) AS missing_element
                FROM {tbl('achievement_standards')}
                WHERE element_id IS NULL;
            """)
            m = self.cur.fetchone()
            logger.info(f"  element_id NULL 개수: {m['missing_element']}")

            logger.info("데이터 검증 완료")
            return True
        except Exception as e:
            logger.error(f"데이터 검증 실패: {e}")
            return False

    # -----------------------
    # 실행
    # -----------------------
    def run(self):
        if not self.connect():
            return False
        try:
            if not self.ensure_schema_ready():
                return False

            if not self.load_reference_data():
                return False

            if not self.load_core_ideas():
                return False

            if not self.load_content_elements():
                return False

            if not self.load_achievement_standards():
                return False

            if not self.load_standard_achievement_levels():
                return False

            if not self.load_standard_explanations():
                return False

            if not self.load_terms_symbols():
                return False

            self.fix_sequences()

            if not self.verify_data():
                return False

            logger.info("모든 데이터 로딩 완료!")
            return True
        finally:
            self.disconnect()


def main():
    loader = DataLoader()
    ok = loader.run()
    if ok:
        logger.info("데이터 로딩 성공")
        sys.exit(0)
    else:
        logger.error("데이터 로딩 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
