#!/usr/bin/env python3
"""
하드코딩/목업 데이터 제거 스크립트
신뢰도 낮은 데이터를 식별하고 제거합니다.
"""

import psycopg2
from loguru import logger

class DataCleanup:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="mathematics_curriculum",
            user="postgres",
            password="postgres123"
        )
        self.cursor = self.conn.cursor()
        
    def cleanup_random_contexts(self):
        """랜덤으로 생성된 standard_contexts 제거"""
        logger.info("Cleaning up random context mappings...")
        
        # evidence_text가 'Auto-generated'인 모든 레코드 삭제
        self.cursor.execute("""
            DELETE FROM curriculum.standard_contexts
            WHERE evidence_text = 'Auto-generated context mapping'
        """)
        deleted = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Deleted {deleted} random context mappings")
        
    def cleanup_hardcoded_learning_elements(self):
        """하드코딩된 learning_elements 제거"""
        logger.info("Cleaning up hardcoded learning elements...")
        
        # 하드코딩된 패턴의 학습 요소 삭제
        hardcoded_names = [
            '수와 연산의 이해%',
            '기하학적 사고%',
            '측정과 단위%',
            '자료의 수집과 정리%',
            '확률과 통계%'
        ]
        
        for pattern in hardcoded_names:
            self.cursor.execute("""
                DELETE FROM curriculum.learning_elements
                WHERE element_name LIKE %s
            """, (pattern,))
        
        deleted = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Deleted {deleted} hardcoded learning elements")
        
    def cleanup_fixed_domain_levels(self):
        """고정값으로 생성된 domain_achievement_levels 제거"""
        logger.info("Cleaning up fixed domain achievement levels...")
        
        # 모든 level_code가 'A'인 레코드 삭제
        self.cursor.execute("""
            DELETE FROM curriculum.domain_achievement_levels
            WHERE level_code = 'A' 
            AND level_description LIKE 'Level%Domain%'
        """)
        deleted = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Deleted {deleted} fixed domain levels")
        
    def cleanup_low_confidence_mappings(self):
        """신뢰도 낮은 매핑 제거"""
        logger.info("Cleaning up low confidence mappings...")
        
        # standard_terms에서 confidence < 0.3 제거
        self.cursor.execute("""
            DELETE FROM curriculum.standard_terms
            WHERE confidence < 0.3
        """)
        terms_deleted = self.cursor.rowcount
        
        # standard_competencies에서 confidence < 0.3 제거
        self.cursor.execute("""
            DELETE FROM curriculum.standard_competencies
            WHERE confidence < 0.3
        """)
        comp_deleted = self.cursor.rowcount
        
        # standard_representations에서 기본값(0.5) + evidence가 'Default'인 것 제거
        self.cursor.execute("""
            DELETE FROM curriculum.standard_representations
            WHERE confidence = 0.5 AND evidence_text = 'Default'
        """)
        rep_deleted = self.cursor.rowcount
        
        self.conn.commit()
        logger.info(f"  Deleted {terms_deleted} low confidence term mappings")
        logger.info(f"  Deleted {comp_deleted} low confidence competency mappings")
        logger.info(f"  Deleted {rep_deleted} default representation mappings")
        
    def verify_real_data(self):
        """실제 데이터만 남았는지 확인"""
        logger.info("\n✅ Verifying remaining data...")
        
        tables = [
            'achievement_standard_relations',
            'standard_terms',
            'standard_competencies',
            'standard_representations',
            'standard_contexts',
            'learning_elements',
            'domain_achievement_levels'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM curriculum.{table}")
            count = self.cursor.fetchone()[0]
            
            # method 컬럼이 있는 테이블은 method별로 집계
            if table in ['standard_terms', 'standard_competencies', 'standard_representations', 'standard_contexts']:
                self.cursor.execute(f"""
                    SELECT method, COUNT(*) 
                    FROM curriculum.{table} 
                    GROUP BY method
                """)
                methods = self.cursor.fetchall()
                method_str = ", ".join([f"{m[0]}:{m[1]}" for m in methods])
                logger.info(f"  {table}: {count} records ({method_str})")
            else:
                logger.info(f"  {table}: {count} records")
                
    def generate_cleanup_report(self):
        """제거 결과 보고서"""
        logger.info("\n" + "="*60)
        logger.info("데이터 클린업 완료 보고서")
        logger.info("="*60)
        
        # 남은 데이터 품질 평가
        self.cursor.execute("""
            SELECT 
                'standard_contexts' as table_name,
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence
            FROM curriculum.standard_contexts
            WHERE confidence IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'standard_terms' as table_name,
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence
            FROM curriculum.standard_terms
            WHERE confidence IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'standard_competencies' as table_name,
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence
            FROM curriculum.standard_competencies
            WHERE confidence IS NOT NULL
        """)
        
        logger.info("\n📊 남은 데이터 품질 통계:")
        for row in self.cursor.fetchall():
            if row[1] > 0:  # 데이터가 있는 경우만
                logger.info(f"  {row[0]}:")
                logger.info(f"    - Count: {row[1]}")
                logger.info(f"    - Avg confidence: {row[2]:.3f}")
                logger.info(f"    - Min confidence: {row[3]:.3f}")
                logger.info(f"    - Max confidence: {row[4]:.3f}")
                
    def run_cleanup(self):
        """전체 클린업 실행"""
        try:
            logger.info("Starting data cleanup...")
            
            # 1. 랜덤 생성 데이터 제거
            self.cleanup_random_contexts()
            
            # 2. 하드코딩된 데이터 제거
            self.cleanup_hardcoded_learning_elements()
            
            # 3. 고정값 데이터 제거
            self.cleanup_fixed_domain_levels()
            
            # 4. 저신뢰도 데이터 제거
            self.cleanup_low_confidence_mappings()
            
            # 5. 검증
            self.verify_real_data()
            
            # 6. 보고서
            self.generate_cleanup_report()
            
            logger.info("\n✅ Cleanup completed successfully!")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            self.conn.rollback()
            raise
        finally:
            self.conn.close()

def main():
    print("\n" + "="*60)
    print("하드코딩/목업 데이터 제거")
    print("="*60)
    print("\n다음 작업을 수행합니다:")
    print("1. 랜덤 생성된 컨텍스트 매핑 제거")
    print("2. 하드코딩된 학습 요소 제거")
    print("3. 고정값 도메인 레벨 제거")
    print("4. 신뢰도 < 0.3인 매핑 제거")
    print("5. 기본값으로 생성된 표현 방법 제거")
    
    response = input("\n⚠️  경고: 데이터가 삭제됩니다. 계속하시겠습니까? (y/n): ")
    
    if response.lower() == 'y':
        cleanup = DataCleanup()
        cleanup.run_cleanup()
    else:
        print("작업이 취소되었습니다.")

if __name__ == "__main__":
    main()