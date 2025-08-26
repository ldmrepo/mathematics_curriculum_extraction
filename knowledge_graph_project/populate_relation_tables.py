#!/usr/bin/env python3
"""
PostgreSQL 연결 테이블 데이터 생성 스크립트
Neo4j 그래프 데이터와 AI 분석 결과를 활용하여 비어있는 연결 테이블을 채웁니다.
"""

import json
import psycopg2
from neo4j import GraphDatabase
import pandas as pd
import re
from typing import List, Dict, Tuple
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

class RelationTablePopulator:
    """PostgreSQL 연결 테이블 데이터 생성기"""
    
    def __init__(self):
        # PostgreSQL 연결
        self.pg_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="mathematics_curriculum",
            user="postgres",
            password="postgres123"
        )
        self.pg_cursor = self.pg_conn.cursor()
        
        # Neo4j 연결
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "neo4j123")
        )
        
    def close_connections(self):
        """연결 종료"""
        self.pg_conn.close()
        self.neo4j_driver.close()
        
    def populate_achievement_standard_relations(self):
        """
        1. achievement_standard_relations 테이블 채우기
        Neo4j의 PREREQUISITE, RELATED_TO, SIMILAR_TO 관계를 PostgreSQL로 동기화
        """
        logger.info("Populating achievement_standard_relations...")
        
        # 성취기준 코드를 standard_id로 매핑하기 위한 딕셔너리 생성
        self.pg_cursor.execute("""
            SELECT standard_id, standard_code 
            FROM curriculum.achievement_standards
        """)
        code_to_id = {code: sid for sid, code in self.pg_cursor.fetchall()}
        
        with self.neo4j_driver.session() as session:
            # Neo4j에서 관계 데이터 추출
            result = session.run("""
                MATCH (s1:AchievementStandard)-[r:PREREQUISITE|RELATED_TO|SIMILAR_TO|BRIDGES_DOMAIN]->(s2:AchievementStandard)
                RETURN 
                    s1.code AS from_standard,
                    s2.code AS to_standard,
                    type(r) AS relation_type,
                    r.weight AS weight,
                    r.reasoning AS reasoning,
                    r.relation_type AS detailed_type
            """)
            
            relations = []
            for record in result:
                # standard_code를 standard_id로 변환
                from_id = code_to_id.get(record['from_standard'])
                to_id = code_to_id.get(record['to_standard'])
                
                if not from_id or not to_id:
                    logger.warning(f"Skipping relation: {record['from_standard']} -> {record['to_standard']} (ID not found)")
                    continue
                
                # PostgreSQL relation_type 매핑 (테이블에 맞게)
                neo4j_type = record['relation_type']
                pg_type = {
                    'PREREQUISITE': 'PREREQUISITE',
                    'RELATED_TO': 'HORIZONTAL',
                    'SIMILAR_TO': 'HORIZONTAL',
                    'BRIDGES_DOMAIN': 'HORIZONTAL'
                }.get(neo4j_type, 'HORIZONTAL')
                
                relations.append((
                    from_id,  # src_standard_id
                    to_id,    # dst_standard_id
                    pg_type,  # relation_type
                    record['reasoning'] or f"AI 추출: {neo4j_type}",  # rationale
                    'llm',    # method
                    min(record['weight'] or 0.5, 1.0)  # confidence (0-1 범위)
                ))
        
        # PostgreSQL에 삽입
        if relations:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.achievement_standard_relations 
                (src_standard_id, dst_standard_id, relation_type, rationale, method, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (src_standard_id, dst_standard_id, relation_type) DO UPDATE
                SET confidence = EXCLUDED.confidence,
                    rationale = EXCLUDED.rationale
            """, relations)
            self.pg_conn.commit()
            logger.info(f"✅ Inserted {len(relations)} relations")
        
    def populate_standard_terms(self):
        """
        2. standard_terms 테이블 채우기
        성취기준 설명에서 용어를 추출하여 자동 매핑
        """
        logger.info("Populating standard_terms...")
        
        # 성취기준과 용어 데이터 로드
        self.pg_cursor.execute("""
            SELECT standard_id, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.pg_cursor.fetchall()
        
        self.pg_cursor.execute("""
            SELECT term_id, term_name, term_description 
            FROM curriculum.terms_symbols
        """)
        terms = self.pg_cursor.fetchall()
        
        # 용어 매칭
        mappings = []
        for std_id, std_desc in standards:
            for term_id, term_name, term_desc in terms:
                # 용어명이 성취기준 설명에 포함되어 있는지 확인
                if term_name and term_name in std_desc:
                    relevance = min(len(term_name) / len(std_desc) * 10, 1.0)  # 0-1 범위로 정규화
                    mappings.append((
                        std_id,  # standard_id
                        term_id,
                        '필수' if relevance > 0.5 else '참고',  # relation_type
                        'llm',  # method
                        relevance,  # confidence
                        f"'{term_name}' 키워드 매칭"  # evidence_text
                    ))
        
        # PostgreSQL에 삽입
        if mappings:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.standard_terms 
                (standard_id, term_id, relation_type, method, confidence, evidence_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (standard_id, term_id) DO UPDATE
                SET confidence = EXCLUDED.confidence,
                    evidence_text = EXCLUDED.evidence_text
            """, mappings)
            self.pg_conn.commit()
            logger.info(f"✅ Created {len(mappings)} term mappings")
            
    def populate_standard_competencies(self):
        """
        3. standard_competencies 테이블 채우기
        성취기준과 수학 교과 역량 연결
        """
        logger.info("Populating standard_competencies...")
        
        # 역량 키워드 매핑
        competency_keywords = {
            1: ['문제', '해결', '전략', '방법', '과정'],  # 문제해결
            2: ['추론', '논리', '증명', '정당화', '설명'],  # 추론
            3: ['창의', '융합', '새로운', '다양한', '탐구'],  # 창의·융합
            4: ['의사소통', '표현', '설명', '토론', '발표'],  # 의사소통
            5: ['정보', '공학', '도구', '기술', '활용'],  # 정보처리
            6: ['태도', '실천', '흥미', '자신감', '가치']  # 태도 및 실천
        }
        
        # 성취기준별 역량 매핑
        self.pg_cursor.execute("""
            SELECT standard_code, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.pg_cursor.fetchall()
        
        competency_mappings = []
        for std_code, std_desc in standards:
            for comp_id, keywords in competency_keywords.items():
                # 키워드 매칭 점수 계산
                score = sum(1 for keyword in keywords if keyword in std_desc)
                if score > 0:
                    relevance = min(score / len(keywords), 1.0)
                    competency_mappings.append((
                        std_code,
                        comp_id,
                        relevance,
                        f"키워드 매칭 점수: {score}/{len(keywords)}"
                    ))
        
        # PostgreSQL에 삽입
        if competency_mappings:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.standard_competencies 
                (standard_code, competency_id, relevance_level, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (standard_code, competency_id) DO UPDATE
                SET relevance_level = EXCLUDED.relevance_level
            """, competency_mappings)
            self.pg_conn.commit()
            logger.info(f"✅ Created {len(competency_mappings)} competency mappings")
            
    def populate_standard_representations(self):
        """
        4. standard_representations 테이블 채우기
        성취기준별 수학적 표현 방법 연결
        """
        logger.info("Populating standard_representations...")
        
        # 표현 방법 키워드
        representation_keywords = {
            1: ['구체물', '교구', '조작'],  # 구체적 조작
            2: ['그림', '도형', '시각'],  # 그림
            3: ['기호', '식', '수식'],  # 기호
            4: ['언어', '말', '설명'],  # 언어
            5: ['표', '차트'],  # 표
            6: ['그래프', '좌표'],  # 그래프
            7: ['다이어그램', '도표'],  # 다이어그램
            8: ['디지털', '소프트웨어', '프로그램'],  # 디지털 도구
            9: ['기타']  # 기타
        }
        
        self.pg_cursor.execute("""
            SELECT standard_code, standard_content 
            FROM curriculum.achievement_standards
        """)
        standards = self.pg_cursor.fetchall()
        
        representation_mappings = []
        for std_code, std_desc in standards:
            for rep_id, keywords in representation_keywords.items():
                score = sum(1 for keyword in keywords if keyword in std_desc)
                if score > 0 or rep_id == 9:  # 기타는 기본으로 추가
                    is_primary = score >= 2  # 2개 이상 키워드 매칭 시 주요 표현
                    representation_mappings.append((
                        std_code,
                        rep_id,
                        is_primary,
                        f"키워드 매칭: {score}개"
                    ))
        
        if representation_mappings:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.standard_representations 
                (standard_code, representation_id, is_primary, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (standard_code, representation_id) DO UPDATE
                SET is_primary = EXCLUDED.is_primary
            """, representation_mappings)
            self.pg_conn.commit()
            logger.info(f"✅ Created {len(representation_mappings)} representation mappings")
            
    def populate_learning_elements(self):
        """
        5. learning_elements 테이블 채우기
        성취기준별 학습 요소 생성
        """
        logger.info("Populating learning_elements...")
        
        # Phase 3 결과에서 학습 요소 추출
        try:
            with open('output/phase3_refinement_results.json', 'r', encoding='utf-8') as f:
                phase3_data = json.load(f)
        except:
            phase3_data = {}
        
        self.pg_cursor.execute("""
            SELECT s.standard_code, s.standard_content, d.domain_name_korean 
            FROM curriculum.achievement_standards s
            JOIN curriculum.domains d ON s.domain_id = d.domain_id
        """)
        standards = self.pg_cursor.fetchall()
        
        learning_elements = []
        element_types = ['개념', '원리', '절차', '응용', '문제해결']
        
        for std_code, std_desc, domain in standards:
            # 성취기준별로 2-3개의 학습 요소 생성
            words = std_desc.split()[:10]  # 처음 10단어 사용
            
            for i, elem_type in enumerate(element_types[:3]):
                element_name = f"{domain}_{elem_type}_{std_code}"
                element_desc = f"{std_code}의 {elem_type} 학습"
                
                learning_elements.append((
                    element_name,
                    elem_type,
                    element_desc,
                    std_code,
                    i + 1,  # sequence_order
                    json.dumps({
                        'auto_generated': True,
                        'source': 'achievement_standard'
                    })
                ))
        
        if learning_elements:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.learning_elements 
                (element_name, element_type, description, standard_code, sequence_order, metadata)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (element_name) DO UPDATE
                SET description = EXCLUDED.description
            """, learning_elements)
            self.pg_conn.commit()
            logger.info(f"✅ Created {len(learning_elements)} learning elements")
            
    def populate_domain_achievement_levels(self):
        """
        6. domain_achievement_levels 테이블 채우기
        영역별 성취수준 요약 생성
        """
        logger.info("Populating domain_achievement_levels...")
        
        # 영역별 성취수준 집계
        self.pg_cursor.execute("""
            WITH domain_stats AS (
                SELECT 
                    d.domain_name_korean as domain,
                    gl.level_name as grade_level,
                    l.level_code,
                    COUNT(*) as count,
                    STRING_AGG(DISTINCT LEFT(l.level_content, 100), '; ') as sample_desc
                FROM curriculum.achievement_standards s
                JOIN curriculum.achievement_levels l ON s.standard_code = l.standard_code
                JOIN curriculum.domains d ON s.domain_id = d.domain_id
                JOIN curriculum.grade_levels gl ON s.level_id = gl.level_id
                GROUP BY d.domain_name_korean, gl.level_name, l.level_code
            )
            SELECT 
                domain,
                grade_level,
                level_code,
                sample_desc
            FROM domain_stats
        """)
        
        domain_levels = []
        for domain, grade, level, desc in self.pg_cursor.fetchall():
            level_mapping = {
                'A': '상', 'B': '중상', 'C': '중', 
                'D': '중하', 'E': '하'
            }.get(level, level)
            
            domain_levels.append((
                f"{domain}_{grade}_{level}",  # level_id
                domain,
                level_mapping,  # level_name
                desc[:500],  # description
                {'grade_level': grade, 'original_code': level}  # metadata
            ))
        
        if domain_levels:
            self.pg_cursor.executemany("""
                INSERT INTO curriculum.domain_achievement_levels 
                (level_id, domain, level_name, description, metadata)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (level_id) DO UPDATE
                SET description = EXCLUDED.description
            """, domain_levels)
            self.pg_conn.commit()
            logger.info(f"✅ Created {len(domain_levels)} domain achievement levels")
            
    def generate_summary_report(self):
        """생성 결과 요약 리포트"""
        logger.info("\n" + "="*60)
        logger.info("연결 테이블 데이터 생성 완료")
        logger.info("="*60)
        
        tables = [
            'achievement_standard_relations',
            'standard_terms',
            'standard_competencies',
            'standard_representations',
            'learning_elements',
            'domain_achievement_levels'
        ]
        
        for table in tables:
            self.pg_cursor.execute(f"SELECT COUNT(*) FROM curriculum.{table}")
            count = self.pg_cursor.fetchone()[0]
            status = "✅" if count > 0 else "❌"
            logger.info(f"{status} {table}: {count} records")
            
    def run_all(self):
        """모든 테이블 데이터 생성 실행"""
        try:
            logger.info("Starting relation tables population...")
            
            # 1. Neo4j 관계를 PostgreSQL로 동기화
            self.populate_achievement_standard_relations()
            
            # 2. 용어-성취기준 자동 매핑
            self.populate_standard_terms()
            
            # 3. 역량-성취기준 매핑
            self.populate_standard_competencies()
            
            # 4. 표현방법-성취기준 매핑
            self.populate_standard_representations()
            
            # 5. 학습 요소 생성
            self.populate_learning_elements()
            
            # 6. 영역별 성취수준 생성
            self.populate_domain_achievement_levels()
            
            # 요약 리포트
            self.generate_summary_report()
            
            logger.info("\n✅ All relation tables populated successfully!")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.pg_conn.rollback()
            raise
        finally:
            self.close_connections()

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("PostgreSQL 연결 테이블 데이터 생성")
    print("="*60)
    print("\n다음 작업을 수행합니다:")
    print("1. Neo4j 관계 데이터를 PostgreSQL로 동기화")
    print("2. 성취기준-용어 자동 매핑")
    print("3. 성취기준-역량 자동 매핑")
    print("4. 성취기준-표현방법 자동 매핑")
    print("5. 학습 요소 자동 생성")
    print("6. 영역별 성취수준 요약 생성")
    
    response = input("\n진행하시겠습니까? (y/n): ")
    
    if response.lower() == 'y':
        populator = RelationTablePopulator()
        populator.run_all()
        print("\n✅ 완료! PostgreSQL 연결 테이블이 채워졌습니다.")
    else:
        print("취소되었습니다.")

if __name__ == "__main__":
    main()