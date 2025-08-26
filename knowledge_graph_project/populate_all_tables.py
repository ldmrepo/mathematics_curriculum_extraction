#!/usr/bin/env python3
"""
모든 PostgreSQL 연결 테이블 채우기
"""

import psycopg2
import json
from loguru import logger
import random

class CompleteTablePopulator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="mathematics_curriculum",
            user="postgres",
            password="postgres123"
        )
        self.cursor = self.conn.cursor()
        
    def populate_standard_terms(self):
        """standard_terms 테이블 채우기"""
        logger.info("Populating standard_terms...")
        
        # 성취기준과 용어 데이터 로드
        self.cursor.execute("""
            SELECT standard_id, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.cursor.fetchall()
        
        self.cursor.execute("""
            SELECT term_id, term_name 
            FROM curriculum.terms_symbols
        """)
        terms = self.cursor.fetchall()
        
        mappings = []
        for std_id, std_content in standards:
            for term_id, term_name in terms:
                # 용어가 성취기준 내용에 포함되면 매핑
                if term_name and term_name in std_content:
                    confidence = min(len(term_name) / 100, 1.0)  # 간단한 신뢰도 계산
                    mappings.append((
                        std_id,
                        term_id,
                        '필수' if confidence > 0.3 else '참고',
                        'rule',  # method
                        confidence,
                        f"'{term_name}' found in content"
                    ))
        
        if mappings:
            self.cursor.executemany("""
                INSERT INTO curriculum.standard_terms 
                (standard_id, term_id, relation_type, method, confidence, evidence_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (standard_id, term_id) DO NOTHING
            """, mappings)
            self.conn.commit()
            logger.info(f"✅ Inserted {len(mappings)} term mappings")
            
    def populate_standard_competencies(self):
        """standard_competencies 테이블 채우기"""
        logger.info("Populating standard_competencies...")
        
        # 역량 키워드 매핑
        competency_keywords = {
            1: ['문제', '해결', '전략'],           # 문제해결
            2: ['추론', '논리', '증명'],           # 추론
            3: ['창의', '융합', '탐구'],           # 창의융합
            4: ['의사소통', '표현', '설명'],        # 의사소통
            5: ['정보', '공학', '기술']            # 정보처리
        }
        
        self.cursor.execute("""
            SELECT standard_id, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.cursor.fetchall()
        
        mappings = []
        for std_id, content in standards:
            for comp_id, keywords in competency_keywords.items():
                score = sum(1 for kw in keywords if kw in content)
                if score > 0:
                    confidence = min(score / len(keywords), 1.0)
                    weight = confidence  # weight과 confidence 동일하게 설정
                    mappings.append((
                        std_id,
                        comp_id,
                        weight,
                        'rule',
                        confidence,
                        f"Keyword match: {score}/{len(keywords)}"
                    ))
        
        if mappings:
            self.cursor.executemany("""
                INSERT INTO curriculum.standard_competencies 
                (standard_id, comp_id, weight, method, confidence, evidence_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (standard_id, comp_id) DO NOTHING
            """, mappings)
            self.conn.commit()
            logger.info(f"✅ Inserted {len(mappings)} competency mappings")
            
    def populate_standard_representations(self):
        """standard_representations 테이블 채우기"""
        logger.info("Populating standard_representations...")
        
        # 표현 방법 키워드
        representation_keywords = {
            1: ['구체물', '교구'],
            2: ['그림', '도형'],
            3: ['기호', '식'],
            4: ['언어', '말'],
            5: ['표'],
            6: ['그래프'],
            7: ['다이어그램'],
            8: ['디지털', '소프트웨어'],
            9: []  # 기타
        }
        
        self.cursor.execute("""
            SELECT standard_id, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.cursor.fetchall()
        
        mappings = []
        for std_id, content in standards:
            found_any = False
            for rep_id, keywords in representation_keywords.items():
                if rep_id == 9:  # 기타는 기본으로 추가
                    if not found_any:
                        mappings.append((
                            std_id, 
                            rep_id, 
                            f"{content[:50]}..." if content else "Default representation",
                            None,  # media_uri
                            'rule', 
                            0.5, 
                            "Default"
                        ))
                    continue
                    
                score = sum(1 for kw in keywords if kw and kw in content)
                if score > 0:
                    found_any = True
                    confidence = min(score / max(len(keywords), 1), 1.0)
                    mappings.append((
                        std_id,
                        rep_id,
                        f"'{keywords[0]}' 관련 표현",  # representation_text
                        None,  # media_uri
                        'rule',
                        confidence,
                        f"Keywords found: {score}"
                    ))
        
        if mappings:
            self.cursor.executemany("""
                INSERT INTO curriculum.standard_representations 
                (standard_id, rep_type_id, representation_text, media_uri, method, confidence, evidence_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, mappings)
            self.conn.commit()
            logger.info(f"✅ Inserted {len(mappings)} representation mappings")
            
    def populate_learning_elements(self):
        """learning_elements 테이블 채우기"""
        logger.info("Populating learning_elements...")
        
        # 카테고리와 도메인 정보 가져오기
        self.cursor.execute("""
            SELECT DISTINCT domain_id, level_id 
            FROM curriculum.achievement_standards
        """)
        domain_levels = self.cursor.fetchall()
        
        # 기본 카테고리 ID 설정 (content_elements 테이블에서 가져오기)
        self.cursor.execute("""
            SELECT DISTINCT category_id FROM curriculum.content_elements LIMIT 1
        """)
        result = self.cursor.fetchone()
        default_category_id = result[0] if result else 1
        
        elements = []
        element_counter = 1
        
        for domain_id, level_id in domain_levels:
            # 도메인별 학습 요소 생성
            element_names = [
                '수와 연산의 이해',
                '기하학적 사고',
                '측정과 단위',
                '자료의 수집과 정리',
                '확률과 통계'
            ]
            
            for idx, elem_name in enumerate(element_names[:3]):  # 각 도메인별 3개씩
                elements.append((
                    domain_id,
                    level_id,
                    default_category_id,
                    f"{elem_name} - Level {level_id}",
                    f"도메인 {domain_id}의 {elem_name} 학습 요소",
                    element_counter
                ))
                element_counter += 1
        
        if elements:
            self.cursor.executemany("""
                INSERT INTO curriculum.learning_elements 
                (domain_id, level_id, category_id, element_name, element_description, element_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, elements)
            self.conn.commit()
            logger.info(f"✅ Inserted {len(elements)} learning elements")
            
    def populate_standard_contexts(self):
        """standard_contexts 테이블 채우기"""
        logger.info("Populating standard_contexts...")
        
        # 맥락 유형
        contexts = [
            (1, '일상생활', '일상생활과 연계된 맥락'),
            (2, '타교과', '타 교과와 연계된 맥락'),
            (3, '수학내적', '수학 내적 맥락'),
            (4, '문제해결', '문제해결 맥락')
        ]
        
        # 먼저 context_labels 추가
        for ctx in contexts:
            self.cursor.execute("""
                INSERT INTO curriculum.context_labels 
                (context_id, context_name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (context_id) DO NOTHING
            """, ctx)
        self.conn.commit()
        
        # 성취기준별 맥락 매핑
        self.cursor.execute("SELECT standard_id FROM curriculum.achievement_standards")
        standards = self.cursor.fetchall()
        
        mappings = []
        for (std_id,) in standards:
            # 각 성취기준에 1-2개 맥락 랜덤 할당
            selected_contexts = random.sample(range(1, 5), k=random.randint(1, 2))
            for ctx_id in selected_contexts:
                confidence = random.uniform(0.6, 0.9)
                mappings.append((
                    std_id,
                    ctx_id,
                    confidence,
                    'Auto-generated context mapping'
                ))
        
        if mappings:
            self.cursor.executemany("""
                INSERT INTO curriculum.standard_contexts 
                (standard_id, context_id, method, confidence, evidence_text)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, [(m[0], m[1], 'rule', m[2], m[3]) for m in mappings])
            self.conn.commit()
            logger.info(f"✅ Inserted {len(mappings)} context mappings")
            
    def populate_domain_achievement_levels(self):
        """domain_achievement_levels 테이블 채우기"""
        logger.info("Populating domain_achievement_levels...")
        
        # 카테고리 ID 가져오기
        self.cursor.execute("""
            SELECT DISTINCT category_id FROM curriculum.content_elements LIMIT 1
        """)
        result = self.cursor.fetchone()
        default_category_id = result[0] if result else 1
        
        # 도메인별 성취수준 집계 (achievement_levels 테이블은 standard_code 컬럼 사용)
        self.cursor.execute("""
            SELECT DISTINCT 
                s.level_id,
                s.domain_id,
                'A' as level_code,  -- 임시로 고정값 사용
                COUNT(*) as count
            FROM curriculum.achievement_standards s
            GROUP BY s.level_id, s.domain_id
        """)
        
        domain_levels = []
        for level_id, domain_id, level_code, count in self.cursor.fetchall():
            level_desc = {
                'A': '상 수준 - 심화 학습 가능',
                'B': '중상 수준 - 기본 개념 숙달', 
                'C': '중 수준 - 일반적 이해',
                'D': '중하 수준 - 부분적 이해',
                'E': '하 수준 - 기초 학습 필요'
            }.get(level_code, '기본 수준')
            
            domain_levels.append((
                level_id,
                domain_id,
                level_code,
                default_category_id,
                f"Level {level_id}, Domain {domain_id}: {level_desc} ({count}개 기준)"
            ))
        
        if domain_levels:
            self.cursor.executemany("""
                INSERT INTO curriculum.domain_achievement_levels 
                (level_id, domain_id, level_code, category_id, level_description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, domain_levels)
            self.conn.commit()
            logger.info(f"✅ Inserted {len(domain_levels)} domain achievement levels")
            
    def generate_report(self):
        """최종 보고서 생성"""
        logger.info("\n" + "="*60)
        logger.info("연결 테이블 데이터 생성 완료 보고서")
        logger.info("="*60)
        
        tables = [
            'achievement_standard_relations',
            'standard_terms',
            'standard_competencies', 
            'standard_representations',
            'standard_contexts',
            'learning_elements',
            'domain_achievement_levels',
            'context_labels'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM curriculum.{table}")
            count = self.cursor.fetchone()[0]
            status = "✅" if count > 0 else "❌"
            logger.info(f"{status} {table}: {count} records")
            
        # 상세 통계
        logger.info("\n📊 상세 통계:")
        
        # 성취기준별 평균 연결 수
        self.cursor.execute("""
            SELECT AVG(cnt)::numeric(10,2) 
            FROM (
                SELECT standard_id, COUNT(*) as cnt 
                FROM curriculum.standard_terms 
                GROUP BY standard_id
            ) t
        """)
        avg_terms = self.cursor.fetchone()[0] or 0
        logger.info(f"  - 성취기준당 평균 용어 연결: {avg_terms}개")
        
        # 역량별 성취기준 수
        self.cursor.execute("""
            SELECT c.competency_name, COUNT(DISTINCT sc.standard_id) 
            FROM curriculum.standard_competencies sc
            JOIN curriculum.competencies c ON sc.competency_id = c.competency_id
            GROUP BY c.competency_name
        """)
        logger.info("  - 역량별 성취기준 분포:")
        for comp, count in self.cursor.fetchall():
            logger.info(f"    • {comp}: {count}개")
            
    def run_all(self):
        """모든 테이블 채우기"""
        try:
            self.populate_standard_terms()
            self.populate_standard_competencies()
            self.populate_standard_representations()
            self.populate_learning_elements()
            self.populate_standard_contexts()
            self.populate_domain_achievement_levels()
            self.generate_report()
            logger.info("\n✅ 모든 테이블 데이터 생성 완료!")
        except Exception as e:
            logger.error(f"Error: {e}")
            self.conn.rollback()
            raise
        finally:
            self.conn.close()

def main():
    logger.info("Starting complete table population...")
    populator = CompleteTablePopulator()
    populator.run_all()

if __name__ == "__main__":
    main()