#!/usr/bin/env python3
"""
Neo4j 그래프 데이터베이스 포괄적 분석 스크립트
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from collections import defaultdict
import statistics

# Load environment variables
load_dotenv()

class Neo4jGraphAnalyzer:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j123")
        self.driver = None
        
    def connect(self):
        """Neo4j 연결"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            print(f"✅ Neo4j 연결 성공: {self.uri}")
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
    
    def analyze_node_types(self):
        """1. 노드 유형별 수량과 속성 분석"""
        print("\n" + "="*60)
        print("1. 노드 유형별 분석")
        print("="*60)
        
        # 노드 레이블별 수량
        query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) 
        YIELD value
        RETURN label, value.count as count
        ORDER BY count DESC
        """
        
        try:
            results = self.run_query(query)
            node_stats = {}
            total_nodes = 0
            
            print("\n📊 노드 유형별 수량:")
            for record in results:
                label = record['label']
                count = record['count']
                node_stats[label] = count
                total_nodes += count
                print(f"  • {label}: {count:,}개")
            
            print(f"\n📈 전체 노드 수: {total_nodes:,}개")
            
            # 각 노드 유형별 속성 분석
            print("\n🔍 노드 유형별 속성 분석:")
            for label in node_stats.keys():
                self.analyze_node_properties(label)
                
            return node_stats
            
        except Exception as e:
            print(f"❌ APOC 플러그인이 필요합니다. 기본 쿼리로 대체합니다: {e}")
            return self.analyze_node_types_basic()
    
    def analyze_node_types_basic(self):
        """기본 노드 분석 (APOC 없이)"""
        node_stats = {}
        
        # 각 레이블별로 수량 확인
        labels_to_check = ['AchievementStandard', 'AchievementLevel', 'GradeLevel', 'Domain', 'ContentSystem']
        
        for label in labels_to_check:
            query = f"MATCH (n:{label}) RETURN count(n) as count"
            try:
                result = self.run_query(query)
                if result:
                    count = result[0]['count']
                    node_stats[label] = count
                    print(f"  • {label}: {count:,}개")
            except Exception as e:
                print(f"  • {label}: 쿼리 실패 - {e}")
        
        return node_stats
    
    def analyze_node_properties(self, label):
        """노드 속성 분석"""
        query = f"""
        MATCH (n:{label})
        WITH n, keys(n) as props
        UNWIND props as prop
        RETURN prop, count(*) as frequency
        ORDER BY frequency DESC
        LIMIT 10
        """
        
        try:
            results = self.run_query(query)
            if results:
                print(f"\n    📋 {label} 속성:")
                for record in results:
                    prop = record['prop']
                    freq = record['frequency']
                    print(f"      - {prop}: {freq:,}회")
        except Exception as e:
            print(f"      ❌ {label} 속성 분석 실패: {e}")
    
    def analyze_relationships(self):
        """2. 관계 유형별 분포와 연결 패턴 분석"""
        print("\n" + "="*60)
        print("2. 관계 유형별 분석")
        print("="*60)
        
        # 관계 유형별 수량
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(r) as count
        ORDER BY count DESC
        """
        
        results = self.run_query(query)
        rel_stats = {}
        total_relationships = 0
        
        print("\n📊 관계 유형별 수량:")
        for record in results:
            rel_type = record['relationship_type']
            count = record['count']
            rel_stats[rel_type] = count
            total_relationships += count
            print(f"  • {rel_type}: {count:,}개")
        
        print(f"\n📈 전체 관계 수: {total_relationships:,}개")
        
        # 관계별 연결 패턴 분석
        print("\n🔍 관계별 연결 패턴:")
        for rel_type in rel_stats.keys():
            self.analyze_relationship_pattern(rel_type)
        
        return rel_stats
    
    def analyze_relationship_pattern(self, rel_type):
        """관계별 연결 패턴 분석"""
        query = f"""
        MATCH (a)-[r:{rel_type}]->(b)
        RETURN labels(a) as from_labels, labels(b) as to_labels, count(*) as count
        ORDER BY count DESC
        LIMIT 5
        """
        
        try:
            results = self.run_query(query)
            if results:
                print(f"\n    🔗 {rel_type} 연결 패턴:")
                for record in results:
                    from_labels = record['from_labels']
                    to_labels = record['to_labels']
                    count = record['count']
                    print(f"      - {from_labels} → {to_labels}: {count:,}개")
        except Exception as e:
            print(f"      ❌ {rel_type} 패턴 분석 실패: {e}")
    
    def analyze_graph_statistics(self):
        """3. 그래프 통계 분석"""
        print("\n" + "="*60)
        print("3. 그래프 통계 분석")
        print("="*60)
        
        # 노드별 연결 수 분포
        print("\n📈 노드별 연결 수 분석:")
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as degree
        RETURN 
            min(degree) as min_degree,
            max(degree) as max_degree,
            avg(degree) as avg_degree,
            percentileCont(degree, 0.5) as median_degree
        """
        
        try:
            result = self.run_query(query)[0]
            print(f"  • 최소 연결 수: {result['min_degree']}")
            print(f"  • 최대 연결 수: {result['max_degree']}")
            print(f"  • 평균 연결 수: {result['avg_degree']:.2f}")
            print(f"  • 중위 연결 수: {result['median_degree']:.2f}")
        except Exception as e:
            print(f"  ❌ 연결 수 분석 실패: {e}")
        
        # 가장 연결이 많은 노드들
        print("\n🔗 가장 연결이 많은 노드들:")
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]-()
        WITH n, count(r) as degree
        ORDER BY degree DESC
        LIMIT 10
        RETURN labels(n) as labels, n.name as name, n.code as code, degree
        """
        
        try:
            results = self.run_query(query)
            for i, record in enumerate(results, 1):
                labels = record['labels']
                name = record['name'] or record['code'] or 'N/A'
                degree = record['degree']
                print(f"  {i:2d}. {labels} - {name}: {degree}개 연결")
        except Exception as e:
            print(f"  ❌ 최다 연결 노드 분석 실패: {e}")
        
        # 최장 경로 분석
        self.analyze_longest_paths()
    
    def analyze_longest_paths(self):
        """최장 경로 분석"""
        print("\n🛤️ 최장 경로 분석:")
        query = """
        MATCH path = (start)-[*1..6]->(end)
        WHERE NOT (end)-->()
        WITH path, length(path) as path_length
        ORDER BY path_length DESC
        LIMIT 5
        RETURN 
            [node in nodes(path) | coalesce(node.name, node.code, labels(node)[0])] as path_nodes,
            path_length
        """
        
        try:
            results = self.run_query(query)
            for i, record in enumerate(results, 1):
                path_nodes = record['path_nodes']
                path_length = record['path_length']
                path_str = " → ".join(path_nodes)
                print(f"  {i}. 길이 {path_length}: {path_str}")
        except Exception as e:
            print(f"  ❌ 최장 경로 분석 실패: {e}")
    
    def validate_phases_integration(self):
        """4. Phase 1-4 결과 검증"""
        print("\n" + "="*60)
        print("4. Phase 1-4 결과 검증")
        print("="*60)
        
        # Phase별 결과 파일 존재 확인
        phase_files = [
            'output/phase2_relationship_extraction.json',
            'output/phase3_refinement_results.json',
            'output/phase4_validation_results.json'
        ]
        
        print("\n📁 Phase 결과 파일 확인:")
        phase_data = {}
        for phase_file in phase_files:
            file_path = f"/Users/ldm/work/workspace/mathematics_curriculum_extraction/knowledge_graph_project/{phase_file}"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    phase_data[phase_file] = data
                    print(f"  ✅ {phase_file}: {len(data) if isinstance(data, list) else 'OK'}")
            except FileNotFoundError:
                print(f"  ❌ {phase_file}: 파일 없음")
            except Exception as e:
                print(f"  ❌ {phase_file}: 읽기 실패 - {e}")
        
        # Phase 결과가 그래프에 반영되었는지 확인
        if phase_data:
            self.validate_phase_in_graph(phase_data)
    
    def validate_phase_in_graph(self, phase_data):
        """Phase 결과가 그래프에 반영되었는지 확인"""
        print("\n🔍 Phase 결과의 그래프 반영 검증:")
        
        # PREREQUISITE 관계 확인 (Phase 2 결과)
        query = "MATCH ()-[r:PREREQUISITE]->() RETURN count(r) as prerequisite_count"
        try:
            result = self.run_query(query)[0]
            prereq_count = result['prerequisite_count']
            print(f"  • PREREQUISITE 관계: {prereq_count:,}개")
        except Exception as e:
            print(f"  ❌ PREREQUISITE 관계 확인 실패: {e}")
        
        # RELATED_TO 관계 확인
        query = "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as related_count"
        try:
            result = self.run_query(query)[0]
            related_count = result['related_count']
            print(f"  • RELATED_TO 관계: {related_count:,}개")
        except Exception as e:
            print(f"  ❌ RELATED_TO 관계 확인 실패: {e}")
        
        # 관계에 confidence 속성이 있는지 확인 (Phase 3 결과)
        query = """
        MATCH ()-[r]->() 
        WHERE r.confidence IS NOT NULL
        RETURN count(r) as confidence_count, avg(r.confidence) as avg_confidence
        """
        try:
            result = self.run_query(query)[0]
            confidence_count = result['confidence_count']
            avg_confidence = result['avg_confidence']
            print(f"  • Confidence 속성 있는 관계: {confidence_count:,}개 (평균: {avg_confidence:.3f})")
        except Exception as e:
            print(f"  ❌ Confidence 속성 확인 실패: {e}")
    
    def check_isolated_nodes_and_cycles(self):
        """5. 고립된 노드나 순환 참조 문제 확인"""
        print("\n" + "="*60)
        print("5. 고립된 노드 및 순환 참조 확인")
        print("="*60)
        
        # 고립된 노드 확인
        print("\n🏝️ 고립된 노드 확인:")
        query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n) as labels, count(n) as isolated_count
        ORDER BY isolated_count DESC
        """
        
        try:
            results = self.run_query(query)
            if results:
                total_isolated = sum(record['isolated_count'] for record in results)
                print(f"  • 전체 고립된 노드: {total_isolated:,}개")
                for record in results:
                    labels = record['labels']
                    count = record['isolated_count']
                    print(f"    - {labels}: {count:,}개")
            else:
                print("  ✅ 고립된 노드 없음")
        except Exception as e:
            print(f"  ❌ 고립된 노드 확인 실패: {e}")
        
        # 순환 참조 확인 (PREREQUISITE 관계)
        print("\n🔄 순환 참조 확인:")
        query = """
        MATCH (n:AchievementStandard)-[:PREREQUISITE*1..10]->(n)
        RETURN n.code as code, n.name as name
        LIMIT 10
        """
        
        try:
            results = self.run_query(query)
            if results:
                print(f"  ⚠️ 순환 참조 발견: {len(results)}개")
                for record in results:
                    code = record['code']
                    name = record['name']
                    print(f"    - {code}: {name}")
            else:
                print("  ✅ 순환 참조 없음")
        except Exception as e:
            print(f"  ❌ 순환 참조 확인 실패: {e}")
    
    def analyze_grade_connectivity(self):
        """6. 학년 간 연계성 분석"""
        print("\n" + "="*60)
        print("6. 학년 간 연계성 분석")
        print("="*60)
        
        # 학년별 성취기준 수
        print("\n📚 학년별 성취기준 분포:")
        query = """
        MATCH (g:GradeLevel)<-[:CONTAINS_STANDARD]-(as:AchievementStandard)
        RETURN g.name as grade, count(as) as standard_count
        ORDER BY grade
        """
        
        try:
            results = self.run_query(query)
            for record in results:
                grade = record['grade']
                count = record['standard_count']
                print(f"  • {grade}: {count:,}개")
        except Exception as e:
            print(f"  ❌ 학년별 분포 분석 실패: {e}")
        
        # 학년 간 연결 관계
        print("\n🔗 학년 간 PREREQUISITE 연결:")
        query = """
        MATCH (g1:GradeLevel)-[:CONTAINS_STANDARD]->(as1:AchievementStandard),
              (g2:GradeLevel)-[:CONTAINS_STANDARD]->(as2:AchievementStandard),
              (as1)-[:PREREQUISITE]->(as2)
        WHERE g1 <> g2
        RETURN g1.name as from_grade, g2.name as to_grade, count(*) as connections
        ORDER BY connections DESC
        """
        
        try:
            results = self.run_query(query)
            if results:
                for record in results:
                    from_grade = record['from_grade']
                    to_grade = record['to_grade']
                    connections = record['connections']
                    print(f"  • {from_grade} → {to_grade}: {connections:,}개 연결")
            else:
                print("  ℹ️ 학년 간 직접 연결 없음")
        except Exception as e:
            print(f"  ❌ 학년 간 연결 분석 실패: {e}")
    
    def analyze_domain_relationships(self):
        """7. 영역 간 교차 관계 분석"""
        print("\n" + "="*60)
        print("7. 영역 간 교차 관계 분석")
        print("="*60)
        
        # 영역별 성취기준 수
        print("\n📊 영역별 성취기준 분포:")
        query = """
        MATCH (d:Domain)-[:CONTAINS_STANDARD]->(as:AchievementStandard)
        RETURN d.name as domain, count(as) as standard_count
        ORDER BY standard_count DESC
        """
        
        try:
            results = self.run_query(query)
            for record in results:
                domain = record['domain']
                count = record['standard_count']
                print(f"  • {domain}: {count:,}개")
        except Exception as e:
            print(f"  ❌ 영역별 분포 분석 실패: {e}")
        
        # 영역 간 관계 분석
        print("\n🔄 영역 간 관계 연결:")
        query = """
        MATCH (d1:Domain)-[:CONTAINS_STANDARD]->(as1:AchievementStandard),
              (d2:Domain)-[:CONTAINS_STANDARD]->(as2:AchievementStandard),
              (as1)-[r:PREREQUISITE|RELATED_TO]->(as2)
        WHERE d1 <> d2
        RETURN d1.name as from_domain, d2.name as to_domain, 
               type(r) as relationship_type, count(*) as connections
        ORDER BY connections DESC
        """
        
        try:
            results = self.run_query(query)
            if results:
                for record in results:
                    from_domain = record['from_domain']
                    to_domain = record['to_domain']
                    rel_type = record['relationship_type']
                    connections = record['connections']
                    print(f"  • {from_domain} →({rel_type})→ {to_domain}: {connections:,}개")
            else:
                print("  ℹ️ 영역 간 교차 관계 없음")
        except Exception as e:
            print(f"  ❌ 영역 간 관계 분석 실패: {e}")
    
    def generate_summary_report(self):
        """종합 분석 리포트 생성"""
        print("\n" + "="*60)
        print("📋 종합 분석 리포트")
        print("="*60)
        
        # 전체 통계 요약
        query = """
        MATCH (n) 
        WITH count(n) as total_nodes
        MATCH ()-[r]->() 
        WITH total_nodes, count(r) as total_relationships
        RETURN total_nodes, total_relationships
        """
        
        try:
            result = self.run_query(query)[0]
            total_nodes = result['total_nodes']
            total_relationships = result['total_relationships']
            
            print(f"\n📈 전체 그래프 통계:")
            print(f"  • 총 노드 수: {total_nodes:,}개")
            print(f"  • 총 관계 수: {total_relationships:,}개")
            print(f"  • 그래프 밀도: {total_relationships / (total_nodes * (total_nodes - 1)) * 100:.4f}%")
            
            # 현재 시간으로 분석 완료 시간 기록
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n⏰ 분석 완료 시간: {current_time}")
            
        except Exception as e:
            print(f"❌ 종합 통계 생성 실패: {e}")
    
    def run_comprehensive_analysis(self):
        """포괄적 분석 실행"""
        if not self.connect():
            return
        
        try:
            print("🚀 Neo4j 그래프 데이터베이스 포괄적 분석 시작")
            print("=" * 80)
            
            # 각 분석 단계 실행
            self.analyze_node_types()
            self.analyze_relationships()
            self.analyze_graph_statistics()
            self.validate_phases_integration()
            self.check_isolated_nodes_and_cycles()
            self.analyze_grade_connectivity()
            self.analyze_domain_relationships()
            self.generate_summary_report()
            
            print("\n✅ 포괄적 분석 완료!")
            
        except Exception as e:
            print(f"❌ 분석 중 오류 발생: {e}")
        finally:
            self.close()

def main():
    """메인 함수"""
    analyzer = Neo4jGraphAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()