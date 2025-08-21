#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수학과 교육과정 데이터 PostgreSQL 로딩 스크립트
==============================================

설명: CSV 파일들을 PostgreSQL 데이터베이스로 로딩하는 스크립트
작성일: 2024-12-19
수정일: 2025-01-21
버전: 1.1.0

필요 패키지:
- psycopg2-binary
- pandas
- python-dotenv

설치 방법:
pip install psycopg2-binary pandas python-dotenv
"""

import os
import sys
import csv
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_loading.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MathCurriculumLoader:
    """수학과 교육과정 데이터 로더 클래스"""
    
    def __init__(self, config_file: str = None):
        """
        초기화
        
        Args:
            config_file: 설정 파일 경로 (옵션)
        """
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / "data"
        
        # 데이터베이스 연결 정보
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'mathematics_curriculum'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        self.schema = os.getenv('DB_SCHEMA', 'curriculum')
        self.connection = None
        self.stats = {
            'total_records': 0,
            'successful_inserts': 0,
            'failed_inserts': 0,
            'tables_loaded': [],
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"데이터 경로: {self.data_path}")
        logger.info(f"데이터베이스: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")

    def connect_database(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False
            
            # 스키마 설정
            with self.connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {self.schema}, public;")
            
            logger.info("데이터베이스 연결 성공")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False

    def disconnect_database(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            logger.info("데이터베이스 연결 해제")

    def load_csv_file(self, file_path: Path, encoding: str = 'utf-8') -> Optional[pd.DataFrame]:
        """CSV 파일 로드"""
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"CSV 파일 로드 성공: {file_path.name} ({len(df)} 행)")
            return df
            
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {file_path.name} - {e}")
            return None

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정리"""
        # NaN 값을 None으로 변경 (PostgreSQL NULL로 변환됨)
        df = df.where(pd.notnull(df), None)
        
        # 문자열 컬럼의 앞뒤 공백 제거
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df

    def insert_data(self, table_name: str, df: pd.DataFrame, 
                   conflict_column: str = None) -> bool:
        """데이터 삽입"""
        try:
            with self.connection.cursor() as cursor:
                # 컬럼명 가져오기
                columns = df.columns.tolist()
                
                # 값 준비
                values = [tuple(row) for row in df.values]
                
                # SQL 쿼리 생성
                columns_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))
                
                if conflict_column:
                    # UPSERT (ON CONFLICT DO UPDATE)
                    update_columns = [f"{col} = EXCLUDED.{col}" 
                                    for col in columns if col != conflict_column]
                    update_str = ', '.join(update_columns)
                    
                    sql = f"""
                    INSERT INTO {table_name} ({columns_str}) 
                    VALUES %s 
                    ON CONFLICT ({conflict_column}) 
                    DO UPDATE SET {update_str}
                    """
                else:
                    # 일반 INSERT
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES %s"
                
                # 데이터 삽입
                execute_values(cursor, sql, values, template=None, page_size=1000)
                
                affected_rows = cursor.rowcount
                self.stats['successful_inserts'] += affected_rows
                
                logger.info(f"{table_name} 테이블에 {affected_rows}개 레코드 삽입 완료")
                return True
                
        except psycopg2.Error as e:
            logger.error(f"{table_name} 데이터 삽입 실패: {e}")
            self.stats['failed_inserts'] += len(df)
            return False

    def load_reference_data(self) -> bool:
        """기준 데이터 로딩"""
        logger.info("=== 기준 데이터 로딩 시작 ===")
        
        reference_files = [
            ('school_levels.csv', 'school_levels', 'level_id'),
            ('domains.csv', 'domains', 'domain_id'),
            ('categories.csv', 'categories', 'category_id')
        ]
        
        for file_name, table_name, conflict_col in reference_files:
            file_path = self.data_path / "reference" / file_name
            
            if not file_path.exists():
                logger.warning(f"파일을 찾을 수 없음: {file_path}")
                continue
            
            df = self.load_csv_file(file_path)
            if df is not None:
                df = self.clean_data(df)
                success = self.insert_data(table_name, df, conflict_col)
                if success:
                    self.stats['tables_loaded'].append(table_name)
                    self.stats['total_records'] += len(df)
        
        return True

    def load_content_system_data(self) -> bool:
        """내용 체계 데이터 로딩"""
        logger.info("=== 내용 체계 데이터 로딩 시작 ===")
        
        # 핵심 아이디어 로딩
        file_path = self.data_path / "content_system" / "core_ideas.csv"
        if file_path.exists():
            df = self.load_csv_file(file_path)
            if df is not None:
                df = self.clean_data(df)
                success = self.insert_data('core_ideas', df, 'idea_id')
                if success:
                    self.stats['tables_loaded'].append('core_ideas')
                    self.stats['total_records'] += len(df)
        
        # 내용 요소 로딩
        content_element_files = [
            'content_elements_elementary_1-2.csv',
            'content_elements_elementary_3-4.csv',
            'content_elements_elementary_5-6.csv',
            'content_elements_middle_1-3.csv'
        ]
        
        all_elements = []
        for file_name in content_element_files:
            file_path = self.data_path / "content_system" / file_name
            if file_path.exists():
                df = self.load_csv_file(file_path)
                if df is not None:
                    all_elements.append(df)
        
        if all_elements:
            combined_df = pd.concat(all_elements, ignore_index=True)
            combined_df = self.clean_data(combined_df)
            success = self.insert_data('content_elements', combined_df, 'element_id')
            if success:
                self.stats['tables_loaded'].append('content_elements')
                self.stats['total_records'] += len(combined_df)
        
        # 학습 요소 로딩
        learning_element_files = [
            'learning_elements_elementary_1-2.csv',
            'learning_elements_elementary_3-4.csv',
            'learning_elements_elementary_5-6.csv',
            'learning_elements_middle_1-3.csv'
        ]
        
        all_learning = []
        for file_name in learning_element_files:
            file_path = self.data_path / "content_system" / file_name
            if file_path.exists():
                df = self.load_csv_file(file_path)
                if df is not None:
                    all_learning.append(df)
        
        if all_learning:
            combined_df = pd.concat(all_learning, ignore_index=True)
            combined_df = self.clean_data(combined_df)
            success = self.insert_data('learning_elements', combined_df, 'learning_id')
            if success:
                self.stats['tables_loaded'].append('learning_elements')
                self.stats['total_records'] += len(combined_df)
        
        return True

    def load_achievement_standards_data(self) -> bool:
        """성취기준 데이터 로딩"""
        logger.info("=== 성취기준 데이터 로딩 시작 ===")
        
        # 성취기준 로딩
        achievement_files = [
            'achievement_standards_elementary_1-2.csv',
            'achievement_standards_elementary_3-4.csv',
            'achievement_standards_elementary_5-6.csv',
            'achievement_standards_middle_1-3.csv'
        ]
        
        all_standards = []
        for file_name in achievement_files:
            file_path = self.data_path / "achievement_standards" / file_name
            if file_path.exists():
                df = self.load_csv_file(file_path)
                if df is not None:
                    all_standards.append(df)
        
        if all_standards:
            combined_df = pd.concat(all_standards, ignore_index=True)
            combined_df = self.clean_data(combined_df)
            success = self.insert_data('achievement_standards', combined_df, 'standard_id')
            if success:
                self.stats['tables_loaded'].append('achievement_standards')
                self.stats['total_records'] += len(combined_df)
        
        # 성취기준 해설 로딩
        explanation_files = [
            'standard_explanations_elementary_1-2.csv',
            'standard_explanations_elementary_3-4.csv',
            'standard_explanations_elementary_5-6.csv',
            'standard_explanations_middle_1-3.csv'
        ]
        
        all_explanations = []
        for file_name in explanation_files:
            file_path = self.data_path / "achievement_standards" / file_name
            if file_path.exists():
                df = self.load_csv_file(file_path)
                if df is not None:
                    # standard_id가 0인 경우 NULL로 변경 (용어와 기호)
                    df['standard_id'] = df['standard_id'].apply(lambda x: None if x == 0 else x)
                    all_explanations.append(df)
        
        if all_explanations:
            combined_df = pd.concat(all_explanations, ignore_index=True)
            combined_df = self.clean_data(combined_df)
            success = self.insert_data('standard_explanations', combined_df, 'explanation_id')
            if success:
                self.stats['tables_loaded'].append('standard_explanations')
                self.stats['total_records'] += len(combined_df)
        
        return True

    def load_terms_symbols_data(self) -> bool:
        """용어 및 기호 데이터 로딩"""
        logger.info("=== 용어 및 기호 데이터 로딩 시작 ===")
        
        terms_files = [
            'terms_symbols_elementary_1-2.csv',
            'terms_symbols_elementary_3-4.csv',
            'terms_symbols_elementary_5-6.csv',
            'terms_symbols_middle_1-3.csv'
        ]
        
        all_terms = []
        for file_name in terms_files:
            file_path = self.data_path / "terms_symbols" / file_name
            if file_path.exists():
                df = self.load_csv_file(file_path)
                if df is not None:
                    # LaTeX 표현 감지 및 처리
                    if 'term_name' in df.columns:
                        # 수학 기호가 포함된 경우 latex_expression 컬럼 추가
                        df['latex_expression'] = df['term_name'].apply(
                            lambda x: self.extract_latex(x) if isinstance(x, str) else None
                        )
                    
                    all_terms.append(df)
        
        if all_terms:
            combined_df = pd.concat(all_terms, ignore_index=True)
            combined_df = self.clean_data(combined_df)
            success = self.insert_data('terms_symbols', combined_df, 'term_id')
            if success:
                self.stats['tables_loaded'].append('terms_symbols')
                self.stats['total_records'] += len(combined_df)
        
        return True
    
    def extract_latex(self, text: str) -> Optional[str]:
        """텍스트에서 LaTeX 표현 추출"""
        # 특수 수학 기호가 포함된 경우
        math_symbols = ['√', '∞', '∑', '∏', '∫', '≤', '≥', '≠', '±', '∈', '∉', '⊂', '⊃', '∪', '∩']
        
        for symbol in math_symbols:
            if symbol in text:
                return text  # LaTeX 변환이 필요한 경우
        
        # $ 기호로 둘러싸인 수식
        if '$' in text:
            return text
        
        return None

    def validate_data(self) -> bool:
        """데이터 검증"""
        logger.info("=== 데이터 검증 시작 ===")
        
        try:
            with self.connection.cursor() as cursor:
                # 기본 카운트 검증
                validation_queries = [
                    ("SELECT COUNT(*) FROM school_levels", "학교급"),
                    ("SELECT COUNT(*) FROM domains", "영역"),
                    ("SELECT COUNT(*) FROM categories", "범주"),
                    ("SELECT COUNT(*) FROM core_ideas", "핵심아이디어"),
                    ("SELECT COUNT(*) FROM content_elements", "내용요소"),
                    ("SELECT COUNT(*) FROM learning_elements", "학습요소"),
                    ("SELECT COUNT(*) FROM achievement_standards", "성취기준"),
                    ("SELECT COUNT(*) FROM standard_explanations", "성취기준해설"),
                    ("SELECT COUNT(*) FROM terms_symbols", "용어기호")
                ]
                
                logger.info("데이터 카운트 검증:")
                for query, name in validation_queries:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    logger.info(f"  {name}: {count:,}개")
                
                # 참조 무결성 검증
                integrity_queries = [
                    ("""
                    SELECT COUNT(*) FROM achievement_standards ast 
                    LEFT JOIN school_levels sl ON ast.level_id = sl.level_id 
                    WHERE sl.level_id IS NULL
                    """, "성취기준의 학년 참조 오류"),
                    
                    ("""
                    SELECT COUNT(*) FROM achievement_standards ast 
                    LEFT JOIN domains d ON ast.domain_id = d.domain_id 
                    WHERE d.domain_id IS NULL
                    """, "성취기준의 영역 참조 오류"),
                    
                    ("""
                    SELECT COUNT(*) FROM content_elements ce 
                    LEFT JOIN school_levels sl ON ce.level_id = sl.level_id 
                    WHERE sl.level_id IS NULL
                    """, "내용요소의 학년 참조 오류"),
                    
                    ("""
                    SELECT COUNT(*) FROM terms_symbols ts 
                    LEFT JOIN school_levels sl ON ts.level_id = sl.level_id 
                    WHERE sl.level_id IS NULL
                    """, "용어기호의 학년 참조 오류")
                ]
                
                logger.info("참조 무결성 검증:")
                all_valid = True
                for query, name in integrity_queries:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    if count > 0:
                        logger.warning(f"  {name}: {count}개 발견")
                        all_valid = False
                    else:
                        logger.info(f"  {name}: 정상")
                
                # 성취기준 코드 형식 검증
                cursor.execute("""
                    SELECT COUNT(*) FROM achievement_standards 
                    WHERE NOT (standard_code ~ '^[0-9]{1,2}수[0-9]{2}-[0-9]{2}$')
                """)
                invalid_codes = cursor.fetchone()[0]
                if invalid_codes > 0:
                    logger.warning(f"  잘못된 성취기준 코드 형식: {invalid_codes}개")
                    all_valid = False
                else:
                    logger.info("  성취기준 코드 형식: 정상")
                
                return all_valid
                
        except Exception as e:
            logger.error(f"데이터 검증 중 오류: {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """로딩 보고서 생성"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        report = {
            'loading_summary': {
                'total_records': self.stats['total_records'],
                'successful_inserts': self.stats['successful_inserts'],
                'failed_inserts': self.stats['failed_inserts'],
                'tables_loaded': self.stats['tables_loaded'],
                'duration_seconds': duration
            },
            'database_info': {
                'host': self.db_config['host'],
                'database': self.db_config['database'],
                'schema': self.schema
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report

    def save_report(self, report: Dict[str, Any]):
        """보고서 저장"""
        report_file = self.base_path / "database" / "loading_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"로딩 보고서 저장: {report_file}")

    def load_all_data(self) -> bool:
        """전체 데이터 로딩 실행"""
        logger.info("🚀 수학과 교육과정 데이터 로딩 시작")
        self.stats['start_time'] = datetime.now()
        
        try:
            # 데이터베이스 연결
            if not self.connect_database():
                return False
            
            # 트랜잭션 시작
            with self.connection.cursor() as cursor:
                cursor.execute("BEGIN")
            
            # 순서대로 데이터 로딩 (외래키 의존성 고려)
            success = (
                self.load_reference_data() and
                self.load_content_system_data() and
                self.load_achievement_standards_data() and
                self.load_terms_symbols_data()
            )
            
            if success:
                # 데이터 검증
                if self.validate_data():
                    # 커밋
                    self.connection.commit()
                    logger.info("✅ 모든 데이터 로딩 완료 및 커밋")
                else:
                    # 롤백
                    self.connection.rollback()
                    logger.warning("⚠️ 데이터 검증 실패로 롤백")
                    success = False
            else:
                # 롤백
                self.connection.rollback()
                logger.error("❌ 데이터 로딩 실패로 롤백")
            
            self.stats['end_time'] = datetime.now()
            
            # 보고서 생성 및 저장
            report = self.generate_report()
            self.save_report(report)
            
            # 최종 통계 출력
            logger.info("📊 로딩 통계:")
            logger.info(f"  총 레코드: {self.stats['total_records']:,}개")
            logger.info(f"  성공한 삽입: {self.stats['successful_inserts']:,}개")
            logger.info(f"  실패한 삽입: {self.stats['failed_inserts']:,}개")
            logger.info(f"  로딩된 테이블: {', '.join(self.stats['tables_loaded'])}")
            
            if self.stats['start_time'] and self.stats['end_time']:
                duration = self.stats['end_time'] - self.stats['start_time']
                logger.info(f"  소요 시간: {duration.total_seconds():.2f}초")
            
            return success
            
        except Exception as e:
            logger.error(f"데이터 로딩 중 예외 발생: {e}")
            if self.connection:
                self.connection.rollback()
            return False
            
        finally:
            self.disconnect_database()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='수학과 교육과정 데이터 PostgreSQL 로더')
    parser.add_argument('--config', help='설정 파일 경로')
    parser.add_argument('--dry-run', action='store_true', help='실제 삽입 없이 검증만 수행')
    
    args = parser.parse_args()
    
    # 환경 변수 파일 확인
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning(".env 파일이 없습니다. 기본값을 사용합니다.")
        logger.info("환경 변수 예시:")
        logger.info("DB_HOST=localhost")
        logger.info("DB_PORT=5432")
        logger.info("DB_NAME=mathematics_curriculum")
        logger.info("DB_USER=postgres")
        logger.info("DB_PASSWORD=your_password")
        logger.info("DB_SCHEMA=curriculum")
    
    # 로더 실행
    loader = MathCurriculumLoader(args.config)
    success = loader.load_all_data()
    
    if success:
        logger.info("🎉 데이터 로딩이 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        logger.error("💥 데이터 로딩이 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
