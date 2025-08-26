#!/usr/bin/env python3
"""
Neo4j 그래프 상세 검증 및 데이터 품질 분석
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class DetailedGraphInspector:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j123")
        self.driver = None
        
    def connect(self):
        """Neo4j 연결"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            return True
        except Exception as e:
            print(f"❌ Neo4j 연결 실패: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query, parameters=None):
        """쿼리 실행"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def inspect_database_schema(self):
        """데이터베이스 스키마 상세 검사"""
        print("🔍 데이터베이스 스키마 상세 검사")
        print("="*60)
        
        # 모든 레이블과 속성
        print("\n📋 각 노드 레이블의 속성 정보:")
        labels = ['AchievementStandard', 'AchievementLevel', 'GradeLevel', 'Domain']
        
        for label in labels:
            print(f"\n  🔹 {label} 노드:")
            
            # 샘플 노드 조회
            query = f"MATCH (n:{label}) RETURN n LIMIT 3"
            results = self.run_query(query)
            
            if results:
                for i, record in enumerate(results, 1):
                    node = record['n']
                    properties = dict(node)
                    print(f"    샘플 {i}: {json.dumps(properties, ensure_ascii=False, indent=6)}")
            else:
                print(f"    ⚠️ {label} 노드가 없습니다.")
        
        # 모든 관계 유형과 속성
        print("\n🔗 각 관계 유형의 속성 정보:")
        query = """
        MATCH ()-[r]->()
        RETURN DISTINCT type(r) as rel_type
        """
        rel_types = [record['rel_type'] for record in self.run_query(query)]
        
        for rel_type in rel_types:
            print(f"\n  🔸 {rel_type} 관계:")
            query = f"MATCH ()-[r:{rel_type}]->() RETURN r LIMIT 3"
            results = self.run_query(query)
            
            if results:
                for i, record in enumerate(results, 1):
                    rel = record['r']
                    properties = dict(rel)
                    if properties:
                        print(f"    샘플 {i} 속성: {json.dumps(properties, ensure_ascii=False, indent=6)}")
                    else:
                        print(f"    샘플 {i}: 속성 없음")
            else:
                print(f"    ⚠️ {rel_type} 관계를 찾을 수 없습니다.")
    
    def analyze_achievement_standards(self):
        """성취기준 상세 분석"""
        print("\n" + "="*60)
        print("📚 성취기준(AchievementStandard) 상세 분석")
        print("="*60)
        
        # 성취기준별 연결 분포
        print("\n📊 성취기준별 관계 연결 분석:")
        query = """
        MATCH (as:AchievementStandard)
        OPTIONAL MATCH (as)-[r1:PREREQUISITE]->()
        OPTIONAL MATCH ()-[r2:PREREQUISITE]->(as)
        OPTIONAL MATCH (as)-[r3:RELATED_TO]->()
        OPTIONAL MATCH ()-[r4:RELATED_TO]->(as)
        OPTIONAL MATCH (as)-[r5:HAS_LEVEL]->()
        RETURN 
            as.code as code,
            as.name as name,
            count(r1) as outgoing_prerequisite,
            count(r2) as incoming_prerequisite,
            count(r3) as outgoing_related,
            count(r4) as incoming_related,
            count(r5) as achievement_levels,
            count(r1) + count(r2) + count(r3) + count(r4) as total_connections
        ORDER BY total_connections DESC
        LIMIT 15
        """
        
        results = self.run_query(query)
        if results:
            print("  상위 연결된 성취기준:")
            for record in results:
                code = record['code']
                name = record['name']
                out_prereq = record['outgoing_prerequisite']
                in_prereq = record['incoming_prerequisite']
                out_rel = record['outgoing_related']
                in_rel = record['incoming_related']
                levels = record['achievement_levels']
                total = record['total_connections']
                
                print(f"    • {code}: {name}")
                print(f"      - 전제관계 (나가는/들어오는): {out_prereq}/{in_prereq}")
                print(f"      - 관련관계 (나가는/들어오는): {out_rel}/{in_rel}")
                print(f"      - 성취수준: {levels}개, 총 연결: {total}개")
                print()
    
    def analyze_prerequisite_chains(self):
        """전제조건 체인 분석"""
        print("\n" + "="*60)
        print("🔗 전제조건 체인 상세 분석")
        print("="*60)
        
        # 가장 긴 전제조건 체인
        print("\n📏 가장 긴 전제조건 체인:")
        query = """
        MATCH path = (start:AchievementStandard)-[:PREREQUISITE*1..5]->(end:AchievementStandard)
        WHERE NOT (start)<-[:PREREQUISITE]-()
        WITH path, length(path) as chain_length
        ORDER BY chain_length DESC
        LIMIT 5
        RETURN 
            [node in nodes(path) | node.code] as codes,
            [node in nodes(path) | node.name] as names,
            chain_length
        """
        
        results = self.run_query(query)
        if results:
            for i, record in enumerate(results, 1):
                codes = record['codes']
                names = record['names']
                length = record['chain_length']
                
                print(f"  {i}. 체인 길이 {length}:")
                for j, (code, name) in enumerate(zip(codes, names)):
                    prefix = "    └─ " if j == len(codes) - 1 else "    ├─ " if j > 0 else "    ┌─ "
                    print(f"{prefix}{code}: {name}")
                print()
        else:
            print("  📝 길이 2 이상의 전제조건 체인이 없습니다.")
        
        # 전제조건 없는 시작점들
        print("\n🏁 전제조건이 없는 시작 성취기준:")
        query = """
        MATCH (as:AchievementStandard)
        WHERE NOT (as)<-[:PREREQUISITE]-()
        AND (as)-[:PREREQUISITE]->()
        RETURN as.code as code, as.name as name
        ORDER BY code
        LIMIT 10
        """
        
        results = self.run_query(query)
        if results:
            for record in results:
                print(f"  • {record['code']}: {record['name']}")
        else:
            print("  📝 전제조건 체인의 시작점이 없습니다.")
    
    def analyze_achievement_levels(self):
        """성취수준 분석"""
        print("\n" + "="*60)
        print("📊 성취수준(AchievementLevel) 분석")
        print("="*60)
        
        # 성취기준별 성취수준 수 분포
        print("\n📈 성취기준별 성취수준 수 분포:")
        query = """
        MATCH (as:AchievementStandard)-[:HAS_LEVEL]->(al:AchievementLevel)
        WITH as, count(al) as level_count
        RETURN level_count, count(as) as standard_count
        ORDER BY level_count
        """
        
        results = self.run_query(query)
        if results:
            total_standards = sum(record['standard_count'] for record in results)
            print(f"  전체 성취기준 수: {total_standards}")
            for record in results:
                level_count = record['level_count']
                standard_count = record['standard_count']
                percentage = (standard_count / total_standards) * 100
                print(f"    • {level_count}개 수준: {standard_count}개 성취기준 ({percentage:.1f}%)")
        
        # 성취수준 구조 샘플
        print("\n🔍 성취수준 구조 샘플:")
        query = """
        MATCH (as:AchievementStandard)-[:HAS_LEVEL]->(al:AchievementLevel)
        RETURN as.code as standard_code, as.name as standard_name,
               collect(al.level) as levels
        ORDER BY standard_code
        LIMIT 5
        """
        
        results = self.run_query(query)
        if results:
            for record in results:
                code = record['standard_code']
                name = record['standard_name']
                levels = record['levels']
                print(f"  • {code}: {name}")
                print(f"    수준: {sorted(levels) if levels else '없음'}")
    
    def verify_data_consistency(self):
        """데이터 일관성 검증"""
        print("\n" + "="*60)
        print("🔍 데이터 일관성 검증")
        print("="*60)
        
        # 중복 성취기준 코드 확인
        print("\n🔍 중복 코드 확인:")
        query = """
        MATCH (as:AchievementStandard)
        WITH as.code as code, count(as) as count_nodes
        WHERE count_nodes > 1
        RETURN code, count_nodes
        """
        
        results = self.run_query(query)
        if results:
            print(f"  ⚠️ 중복 코드 발견: {len(results)}개")
            for record in results:
                print(f"    - {record['code']}: {record['count_nodes']}개 노드")
        else:
            print("  ✅ 중복 코드 없음")
        
        # 누락된 성취수준 확인
        print("\n📊 성취수준 누락 확인:")
        query = """
        MATCH (as:AchievementStandard)
        WHERE NOT (as)-[:HAS_LEVEL]->()
        RETURN count(as) as no_level_count
        """
        
        result = self.run_query(query)[0]
        no_level_count = result['no_level_count']
        if no_level_count > 0:
            print(f"  ⚠️ 성취수준이 없는 성취기준: {no_level_count}개")
            
            # 누락된 성취기준 목록
            query = """
            MATCH (as:AchievementStandard)
            WHERE NOT (as)-[:HAS_LEVEL]->()
            RETURN as.code as code, as.name as name
            LIMIT 10
            """
            results = self.run_query(query)
            for record in results:
                print(f"    - {record['code']}: {record['name']}")
        else:
            print("  ✅ 모든 성취기준에 성취수준 존재")
        
        # 고아 노드 확인 (연결되지 않은 노드)
        print("\n🏝️ 연결되지 않은 노드 확인:")
        for label in ['AchievementStandard', 'AchievementLevel']:
            query = f"""
            MATCH (n:{label})
            WHERE NOT (n)--()
            RETURN count(n) as isolated_count
            """
            result = self.run_query(query)[0]
            isolated_count = result['isolated_count']
            
            if isolated_count > 0:
                print(f"  ⚠️ 고립된 {label}: {isolated_count}개")
            else:
                print(f"  ✅ 모든 {label} 연결됨")
    
    def analyze_phase_integration_details(self):
        """Phase 통합 결과 상세 분석"""
        print("\n" + "="*60)
        print("🔬 Phase 통합 결과 상세 분석")
        print("="*60)
        
        # Phase 2 결과 분석
        print("\n📋 Phase 2 (관계 추출) 결과:")
        query = """
        MATCH (as1:AchievementStandard)-[r:PREREQUISITE|RELATED_TO]->(as2:AchievementStandard)
        RETURN 
            type(r) as relationship_type,
            count(r) as count,
            collect(DISTINCT as1.code)[0..5] as sample_sources
        """
        
        results = self.run_query(query)
        for record in results:
            rel_type = record['relationship_type']
            count = record['count']
            samples = record['sample_sources']
            print(f"  • {rel_type}: {count}개 (샘플: {', '.join(samples)})")
        
        # 가장 많이 연결된 성취기준들
        print("\n🔝 가장 많이 참조되는 성취기준 (허브 노드):")
        query = """
        MATCH (as:AchievementStandard)
        OPTIONAL MATCH ()-[:PREREQUISITE|RELATED_TO]->(as)
        WITH as, count(*) as incoming_connections
        WHERE incoming_connections > 0
        RETURN as.code as code, as.name as name, incoming_connections
        ORDER BY incoming_connections DESC
        LIMIT 10
        """
        
        results = self.run_query(query)
        for record in results:
            code = record['code']
            name = record['name']
            connections = record['incoming_connections']
            print(f"  • {code}: {name} ({connections}개 연결)")
    
    def run_detailed_inspection(self):
        """상세 검사 실행"""
        if not self.connect():
            return
        
        try:
            print("🔍 Neo4j 그래프 상세 검증 및 품질 분석")
            print("=" * 80)
            
            self.inspect_database_schema()
            self.analyze_achievement_standards()
            self.analyze_prerequisite_chains()
            self.analyze_achievement_levels()
            self.verify_data_consistency()
            self.analyze_phase_integration_details()
            
            print("\n" + "="*60)
            print("✅ 상세 검증 완료!")
            print("="*60)
            
        except Exception as e:
            print(f"❌ 검증 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()

def main():
    """메인 함수"""
    inspector = DetailedGraphInspector()
    inspector.run_detailed_inspection()

if __name__ == "__main__":
    main()