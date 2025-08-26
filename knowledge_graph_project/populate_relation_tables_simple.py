#!/usr/bin/env python3
"""
간단한 버전 - achievement_standard_relations 테이블만 채우기
"""

import psycopg2
from neo4j import GraphDatabase
from loguru import logger

def populate_achievement_standard_relations():
    """Neo4j 관계를 PostgreSQL로 동기화"""
    
    # PostgreSQL 연결
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="mathematics_curriculum",
        user="postgres",
        password="postgres123"
    )
    pg_cursor = pg_conn.cursor()
    
    # Neo4j 연결
    neo4j_driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "neo4j123")
    )
    
    try:
        # 성취기준 코드를 ID로 매핑
        pg_cursor.execute("""
            SELECT standard_id, standard_code 
            FROM curriculum.achievement_standards
        """)
        code_to_id = {code: sid for sid, code in pg_cursor.fetchall()}
        
        with neo4j_driver.session() as session:
            # Neo4j에서 관계 추출
            result = session.run("""
                MATCH (s1:AchievementStandard)-[r:PREREQUISITE|RELATED_TO|SIMILAR_TO|BRIDGES_DOMAIN]->(s2:AchievementStandard)
                RETURN 
                    s1.code AS from_code,
                    s2.code AS to_code,
                    type(r) AS rel_type,
                    r.weight AS weight,
                    r.reasoning AS reasoning
            """)
            
            relations = []
            for record in result:
                from_id = code_to_id.get(record['from_code'])
                to_id = code_to_id.get(record['to_code'])
                
                if not from_id or not to_id:
                    continue
                
                # 관계 유형 매핑
                neo4j_type = record['rel_type']
                pg_type = 'PREREQUISITE' if neo4j_type == 'PREREQUISITE' else 'HORIZONTAL'
                
                relations.append((
                    from_id,
                    to_id,
                    pg_type,
                    record['reasoning'] or f"AI 추출: {neo4j_type}",
                    'llm',
                    min(record['weight'] or 0.5, 1.0)
                ))
        
        # PostgreSQL에 삽입
        if relations:
            pg_cursor.executemany("""
                INSERT INTO curriculum.achievement_standard_relations 
                (src_standard_id, dst_standard_id, relation_type, rationale, method, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (src_standard_id, dst_standard_id, relation_type) DO UPDATE
                SET confidence = EXCLUDED.confidence
            """, relations)
            pg_conn.commit()
            logger.info(f"✅ Inserted {len(relations)} relations")
            
        # 확인
        pg_cursor.execute("SELECT COUNT(*) FROM curriculum.achievement_standard_relations")
        count = pg_cursor.fetchone()[0]
        logger.info(f"Total relations in table: {count}")
        
    finally:
        pg_conn.close()
        neo4j_driver.close()

if __name__ == "__main__":
    logger.info("Starting simple relation table population...")
    populate_achievement_standard_relations()
    logger.info("✅ Done!")