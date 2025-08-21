#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
수학과 교육과정 데이터 로딩 스크립트 v1.2
- 성취기준별 성취수준 데이터 추가
- 영역별 성취수준 데이터 추가
"""

import os
import sys
import csv
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_load.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'mathematics_curriculum'),
    'user': os.getenv('DB_USER', 'curriculum_admin'),
    'password': os.getenv('DB_PASSWORD')
}

# 데이터 파일 경로
DATA_PATH = Path('../data')
ACHIEVEMENT_LEVELS_PATH = DATA_PATH / 'achievement_levels'


class DataLoader:
    """데이터 로딩 클래스"""
    
    def __init__(self):
        """초기화"""
        self.conn = None
        self.cur = None
        
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            self.cur.execute("SET search_path TO curriculum, public")
            logger.info("데이터베이스 연결 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 종료"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("데이터베이스 연결 종료")
    
    def load_reference_data(self):
        """기준 데이터 로드"""
        try:
            # 학교급 데이터
            logger.info("학교급 데이터 로딩...")
            with open(DATA_PATH / 'reference' / 'school_levels.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.cur.execute("""
                        INSERT INTO school_levels (school_type, grade_range, grade_start, grade_end, level_code)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (level_code) DO UPDATE
                        SET school_type = EXCLUDED.school_type,
                            grade_range = EXCLUDED.grade_range
                    """, (row['school_type'], row['grade_range'], 
                          row['grade_start'], row['grade_end'], row['level_code']))
            
            # 영역 데이터
            logger.info("영역 데이터 로딩...")
            with open(DATA_PATH / 'reference' / 'domains.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.cur.execute("""
                        INSERT INTO domains (domain_name, domain_order, domain_code, description)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (domain_name) DO UPDATE
                        SET domain_order = EXCLUDED.domain_order,
                            domain_code = EXCLUDED.domain_code
                    """, (row['domain_name'], row['domain_order'], 
                          row['domain_code'], row.get('description')))
            
            # 범주 데이터
            logger.info("범주 데이터 로딩...")
            with open(DATA_PATH / 'reference' / 'categories.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.cur.execute("""
                        INSERT INTO categories (category_name, category_order, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (category_name) DO UPDATE
                        SET category_order = EXCLUDED.category_order
                    """, (row['category_name'], row['category_order'], row.get('description')))
            
            self.conn.commit()
            logger.info("기준 데이터 로딩 완료")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"기준 데이터 로딩 실패: {e}")
            return False
    
    def load_achievement_standards(self):
        """성취기준 데이터 로드"""
        try:
            logger.info("성취기준 데이터 로딩...")
            
            # 모든 성취기준 파일 처리
            for file_path in DATA_PATH.glob('achievement_standards/achievement_standards_*.csv'):
                if 'all' in file_path.name:
                    continue
                    
                logger.info(f"  파일 처리: {file_path.name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 학교급 ID 조회
                        self.cur.execute("""
                            SELECT level_id FROM school_levels 
                            WHERE level_code = %s
                        """, (int(row['standard_code'].split('수')[0]),))
                        level_result = self.cur.fetchone()
                        
                        if not level_result:
                            logger.warning(f"학교급을 찾을 수 없음: {row['standard_code']}")
                            continue
                        
                        # 영역 ID 조회
                        domain_code = row['standard_code'].split('수')[1][:2]
                        self.cur.execute("""
                            SELECT domain_id FROM domains 
                            WHERE domain_code = %s
                        """, (domain_code,))
                        domain_result = self.cur.fetchone()
                        
                        if not domain_result:
                            logger.warning(f"영역을 찾을 수 없음: {domain_code}")
                            continue
                        
                        # 성취기준 삽입
                        self.cur.execute("""
                            INSERT INTO achievement_standards 
                            (standard_code, level_id, domain_id, standard_title, 
                             standard_content, standard_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (standard_code) DO UPDATE
                            SET standard_title = EXCLUDED.standard_title,
                                standard_content = EXCLUDED.standard_content
                        """, (row['standard_code'], level_result['level_id'], 
                              domain_result['domain_id'], row.get('standard_title', ''),
                              row['standard_content'], 
                              int(row['standard_code'].split('-')[1])))
            
            self.conn.commit()
            logger.info("성취기준 데이터 로딩 완료")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"성취기준 데이터 로딩 실패: {e}")
            return False
    
    def load_standard_achievement_levels(self):
        """성취기준별 성취수준 데이터 로드"""
        try:
            logger.info("성취기준별 성취수준 데이터 로딩...")
            
            # 모든 성취수준 파일 처리
            for file_path in ACHIEVEMENT_LEVELS_PATH.glob('achievement_levels_*.csv'):
                logger.info(f"  파일 처리: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 성취기준 ID 조회
                        self.cur.execute("""
                            SELECT standard_id FROM achievement_standards 
                            WHERE standard_code = %s
                        """, (row['성취기준'],))
                        standard_result = self.cur.fetchone()
                        
                        if not standard_result:
                            logger.warning(f"성취기준을 찾을 수 없음: {row['성취기준']}")
                            continue
                        
                        # 성취수준 삽입
                        self.cur.execute("""
                            INSERT INTO standard_achievement_levels 
                            (standard_id, level_code, level_description)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (standard_id, level_code) DO UPDATE
                            SET level_description = EXCLUDED.level_description
                        """, (standard_result['standard_id'], 
                              row['수준'], row['성취수준']))
            
            self.conn.commit()
            logger.info("성취기준별 성취수준 데이터 로딩 완료")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"성취기준별 성취수준 데이터 로딩 실패: {e}")
            return False
    
    def load_content_elements(self):
        """내용 요소 데이터 로드"""
        try:
            logger.info("내용 요소 데이터 로딩...")
            
            # 모든 내용 요소 파일 처리
            for file_path in DATA_PATH.glob('content_system/content_elements_*.csv'):
                logger.info(f"  파일 처리: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    element_order = 1
                    
                    for row in reader:
                        # 학교급 ID 조회
                        self.cur.execute("""
                            SELECT level_id FROM school_levels 
                            WHERE grade_range = %s
                        """, (row['학년(군)'],))
                        level_result = self.cur.fetchone()
                        
                        if not level_result:
                            logger.warning(f"학교급을 찾을 수 없음: {row['학년(군)']}")
                            continue
                        
                        # 영역 ID 조회
                        self.cur.execute("""
                            SELECT domain_id FROM domains 
                            WHERE domain_name = %s
                        """, (row['영역'],))
                        domain_result = self.cur.fetchone()
                        
                        if not domain_result:
                            logger.warning(f"영역을 찾을 수 없음: {row['영역']}")
                            continue
                        
                        # 범주 ID 조회
                        self.cur.execute("""
                            SELECT category_id FROM categories 
                            WHERE category_name = %s
                        """, (row['범주'],))
                        category_result = self.cur.fetchone()
                        
                        if not category_result:
                            logger.warning(f"범주를 찾을 수 없음: {row['범주']}")
                            continue
                        
                        # 내용 요소 삽입
                        self.cur.execute("""
                            INSERT INTO content_elements 
                            (domain_id, level_id, category_id, element_name, 
                             element_description, element_order)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (domain_id, level_id, category_id, element_order) 
                            DO UPDATE
                            SET element_name = EXCLUDED.element_name,
                                element_description = EXCLUDED.element_description
                        """, (domain_result['domain_id'], level_result['level_id'],
                              category_result['category_id'], row['내용 요소'],
                              row.get('설명'), element_order))
                        
                        element_order += 1
            
            self.conn.commit()
            logger.info("내용 요소 데이터 로딩 완료")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"내용 요소 데이터 로딩 실패: {e}")
            return False
    
    def load_terms_symbols(self):
        """용어와 기호 데이터 로드"""
        try:
            logger.info("용어와 기호 데이터 로딩...")
            
            # 모든 용어/기호 파일 처리
            for file_path in DATA_PATH.glob('terms_symbols/terms_symbols_*.csv'):
                logger.info(f"  파일 처리: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        # 학교급 ID 조회
                        self.cur.execute("""
                            SELECT level_id FROM school_levels 
                            WHERE grade_range = %s
                        """, (row['학년(군)'],))
                        level_result = self.cur.fetchone()
                        
                        if not level_result:
                            logger.warning(f"학교급을 찾을 수 없음: {row['학년(군)']}")
                            continue
                        
                        # 영역 ID 조회
                        self.cur.execute("""
                            SELECT domain_id FROM domains 
                            WHERE domain_name = %s
                        """, (row['영역'],))
                        domain_result = self.cur.fetchone()
                        
                        if not domain_result:
                            logger.warning(f"영역을 찾을 수 없음: {row['영역']}")
                            continue
                        
                        # 용어/기호 삽입
                        self.cur.execute("""
                            INSERT INTO terms_symbols 
                            (level_id, domain_id, term_type, term_name, 
                             term_description, latex_expression)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (level_id, domain_id, term_name) 
                            DO UPDATE
                            SET term_type = EXCLUDED.term_type,
                                term_description = EXCLUDED.term_description,
                                latex_expression = EXCLUDED.latex_expression
                        """, (level_result['level_id'], domain_result['domain_id'],
                              row['구분'], row['용어/기호'],
                              row.get('설명'), row.get('latex')))
            
            self.conn.commit()
            logger.info("용어와 기호 데이터 로딩 완료")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"용어와 기호 데이터 로딩 실패: {e}")
            return False
    
    def verify_data(self):
        """데이터 검증"""
        try:
            logger.info("데이터 검증 시작...")
            
            # 각 테이블의 레코드 수 확인
            tables = [
                'school_levels', 'domains', 'categories', 'achievement_levels',
                'achievement_standards', 'standard_achievement_levels',
                'content_elements', 'terms_symbols'
            ]
            
            for table in tables:
                self.cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = self.cur.fetchone()
                logger.info(f"  {table}: {result['count']} 레코드")
            
            # 성취기준별 성취수준 통계
            self.cur.execute("""
                SELECT 
                    sl.grade_range,
                    d.domain_name,
                    COUNT(DISTINCT ast.standard_id) as standard_count,
                    COUNT(DISTINCT sal.sal_id) as level_count
                FROM school_levels sl
                    CROSS JOIN domains d
                    LEFT JOIN achievement_standards ast 
                        ON sl.level_id = ast.level_id AND d.domain_id = ast.domain_id
                    LEFT JOIN standard_achievement_levels sal 
                        ON ast.standard_id = sal.standard_id
                GROUP BY sl.level_id, sl.grade_range, d.domain_id, d.domain_name
                ORDER BY sl.level_id, d.domain_order
            """)
            
            results = self.cur.fetchall()
            logger.info("\n학년별/영역별 성취기준 및 성취수준 통계:")
            for row in results:
                logger.info(f"  {row['grade_range']} - {row['domain_name']}: "
                          f"성취기준 {row['standard_count']}개, "
                          f"성취수준 {row['level_count']}개")
            
            logger.info("데이터 검증 완료")
            return True
            
        except Exception as e:
            logger.error(f"데이터 검증 실패: {e}")
            return False
    
    def run(self):
        """전체 데이터 로딩 프로세스 실행"""
        if not self.connect():
            return False
        
        try:
            # 1. 기준 데이터 로드
            if not self.load_reference_data():
                return False
            
            # 2. 성취기준 로드
            if not self.load_achievement_standards():
                return False
            
            # 3. 성취기준별 성취수준 로드
            if not self.load_standard_achievement_levels():
                return False
            
            # 4. 내용 요소 로드
            if not self.load_content_elements():
                return False
            
            # 5. 용어와 기호 로드
            if not self.load_terms_symbols():
                return False
            
            # 6. 데이터 검증
            if not self.verify_data():
                return False
            
            logger.info("모든 데이터 로딩 완료!")
            return True
            
        finally:
            self.disconnect()


def main():
    """메인 함수"""
    loader = DataLoader()
    success = loader.run()
    
    if success:
        logger.info("데이터 로딩 성공")
        sys.exit(0)
    else:
        logger.error("데이터 로딩 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
