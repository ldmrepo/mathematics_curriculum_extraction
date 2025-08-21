"""
Neo4j Graph Database Manager
"""
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import json
from loguru import logger
from config.settings import config

class Neo4jManager:
    """Manages Neo4j graph database operations"""
    
    def __init__(self):
        self.uri = config.database.neo4j_uri
        self.user = config.database.neo4j_user
        self.password = config.database.neo4j_password
        self.driver = None
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def clear_database(self):
        """Clear all data in the database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
    
    def create_knowledge_graph(self, all_results: Dict[str, Any]):
        """Create complete knowledge graph in Neo4j"""
        logger.info("Creating knowledge graph in Neo4j")
        
        with self.driver.session() as session:
            # Create nodes
            self._create_curriculum_nodes(session, all_results)
            
            # Create relationships
            self._create_relationships(session, all_results)
            
            # Create indexes for performance
            self._create_indexes(session)
            
            # Create constraints
            self._create_constraints(session)
        
        logger.info("Knowledge graph created successfully")
    
    def _create_curriculum_nodes(self, session, all_results: Dict):
        """Create all curriculum nodes"""
        logger.info("Creating curriculum nodes")
        
        # Create grade level nodes
        grade_levels = [
            {"code": "ELEM_1_2", "name": "초등 1-2학년군", "grade_start": 1, "grade_end": 2},
            {"code": "ELEM_3_4", "name": "초등 3-4학년군", "grade_start": 3, "grade_end": 4},
            {"code": "ELEM_5_6", "name": "초등 5-6학년군", "grade_start": 5, "grade_end": 6},
            {"code": "MIDDLE", "name": "중학교 1-3학년군", "grade_start": 7, "grade_end": 9}
        ]
        
        for grade in grade_levels:
            session.run("""
                CREATE (g:GradeLevel {
                    code: $code,
                    name: $name,
                    grade_start: $grade_start,
                    grade_end: $grade_end
                })
            """, **grade)
        
        # Create domain nodes
        domains = [
            {"code": "NUMBER_OPERATION", "name": "수와 연산"},
            {"code": "CHANGE_RELATION", "name": "변화와 관계"},
            {"code": "GEOMETRY_MEASUREMENT", "name": "도형과 측정"},
            {"code": "DATA_POSSIBILITY", "name": "자료와 가능성"}
        ]
        
        for domain in domains:
            session.run("""
                CREATE (d:Domain {
                    code: $code,
                    name: $name
                })
            """, **domain)
        
        # Create achievement standard nodes (sample - would use actual data)
        self._create_achievement_standards(session)
        
        # Create achievement level nodes
        self._create_achievement_levels(session)
    
    def _create_achievement_standards(self, session):
        """Create achievement standard nodes"""
        # Sample achievement standards - in real implementation, load from database
        standards = [
            {
                "code": "2수01-01",
                "content": "수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.",
                "grade_code": "ELEM_1_2",
                "domain_code": "NUMBER_OPERATION",
                "difficulty": 2,
                "cognitive_level": "understand"
            },
            {
                "code": "2수01-04",
                "content": "하나의 수를 두 수로 분해하고 두 수를 하나의 수로 합성하는 활동을 통하여 수 감각을 기른다.",
                "grade_code": "ELEM_1_2",
                "domain_code": "NUMBER_OPERATION",
                "difficulty": 3,
                "cognitive_level": "apply"
            },
            {
                "code": "4수01-02",
                "content": "곱셈이 이루어지는 상황을 이해하고, 곱셈의 의미를 설명할 수 있다.",
                "grade_code": "ELEM_3_4",
                "domain_code": "NUMBER_OPERATION",
                "difficulty": 3,
                "cognitive_level": "understand"
            }
        ]
        
        for standard in standards:
            session.run("""
                CREATE (s:AchievementStandard {
                    code: $code,
                    content: $content,
                    grade_code: $grade_code,
                    domain_code: $domain_code,
                    difficulty: $difficulty,
                    cognitive_level: $cognitive_level
                })
            """, **standard)
    
    def _create_achievement_levels(self, session):
        """Create achievement level nodes"""
        # Sample achievement levels
        levels = [
            {
                "id": "2수01-01_A",
                "standard_code": "2수01-01",
                "level": "A",
                "description": "수가 사용되는 여러 가지 실생활 상황에서 수의 필요성을 말하고 0과 50까지 또는 100까지의 수를 10개씩 묶음과 낱개로 나타내며 수를 읽고 쓸 수 있다."
            },
            {
                "id": "2수01-01_B",
                "standard_code": "2수01-01",
                "level": "B",
                "description": "실생활에서 수가 사용되는 상황을 말하고 10개씩 묶음과 낱개를 이용하여 0과 50까지 또는 100까지의 수 개념을 이해하며 수를 읽고 쓸 수 있다."
            },
            {
                "id": "2수01-01_C",
                "standard_code": "2수01-01",
                "level": "C",
                "description": "실생활에서 수가 사용됨을 알고 구체물을 세어 0과 50까지 또는 100까지의 수 개념을 이해하며 수를 읽고 쓸 수 있다."
            }
        ]
        
        for level in levels:
            session.run("""
                CREATE (l:AchievementLevel {
                    id: $id,
                    standard_code: $standard_code,
                    level: $level,
                    description: $description
                })
            """, **level)
    
    def _create_relationships(self, session, all_results: Dict):
        """Create relationships between nodes"""
        logger.info("Creating relationships")
        
        # Create hierarchical relationships
        self._create_hierarchical_relationships(session)
        
        # Create educational relationships from AI analysis
        self._create_educational_relationships(session, all_results)
    
    def _create_hierarchical_relationships(self, session):
        """Create hierarchical relationships"""
        # Grade -> Domain relationships
        session.run("""
            MATCH (g:GradeLevel), (d:Domain)
            CREATE (g)-[:HAS_DOMAIN]->(d)
        """)
        
        # Domain -> Standard relationships
        session.run("""
            MATCH (d:Domain), (s:AchievementStandard)
            WHERE d.code = s.domain_code
            CREATE (d)-[:CONTAINS_STANDARD]->(s)
        """)
        
        # Grade -> Standard relationships
        session.run("""
            MATCH (g:GradeLevel), (s:AchievementStandard)
            WHERE g.code = s.grade_code
            CREATE (g)-[:CONTAINS_STANDARD]->(s)
        """)
        
        # Standard -> Level relationships
        session.run("""
            MATCH (s:AchievementStandard), (l:AchievementLevel)
            WHERE s.code = l.standard_code
            CREATE (s)-[:HAS_LEVEL]->(l)
        """)
    
    def _create_educational_relationships(self, session, all_results: Dict):
        """Create educational relationships from AI analysis"""
        # Extract relationships from refinement results
        refinement_results = all_results.get('refinement_results', {})
        adjusted_weights = refinement_results.get('adjusted_weights', [])
        
        for relation in adjusted_weights:
            source_code = relation.get('source_code')
            target_code = relation.get('target_code')
            relation_type = relation.get('refined_type', relation.get('relation_type'))
            weight = relation.get('adjusted_weight', relation.get('weight', 0.5))
            reasoning = relation.get('reasoning', '')
            
            if source_code and target_code and relation_type:
                # Map relation type to Neo4j relationship
                neo4j_relation = self._map_relation_type(relation_type)
                
                session.run(f"""
                    MATCH (s1:AchievementStandard {{code: $source_code}}),
                          (s2:AchievementStandard {{code: $target_code}})
                    CREATE (s1)-[r:{neo4j_relation} {{
                        weight: $weight,
                        reasoning: $reasoning,
                        relation_type: $relation_type
                    }}]->(s2)
                """, source_code=source_code, target_code=target_code, 
                     weight=weight, reasoning=reasoning, relation_type=relation_type)
    
    def _map_relation_type(self, relation_type: str) -> str:
        """Map AI relation types to Neo4j relationship names"""
        mapping = {
            'prerequisite': 'PREREQUISITE',
            'prerequisite_explicit': 'PREREQUISITE',
            'prerequisite_implicit': 'WEAK_PREREQUISITE',
            'similar_to': 'SIMILAR_TO',
            'similar_conceptual': 'CONCEPTUALLY_SIMILAR',
            'similar_procedural': 'PROCEDURALLY_SIMILAR',
            'domain_bridge': 'BRIDGES_DOMAIN',
            'grade_progression': 'PROGRESSES_TO',
            'corequisite': 'COREQUISITE',
            'extends': 'EXTENDS',
            'applies_to': 'APPLIES_TO'
        }
        return mapping.get(relation_type, 'RELATED_TO')
    
    def _create_indexes(self, session):
        """Create indexes for performance"""
        indexes = [
            "CREATE INDEX standard_code_idx IF NOT EXISTS FOR (s:AchievementStandard) ON (s.code)",
            "CREATE INDEX level_id_idx IF NOT EXISTS FOR (l:AchievementLevel) ON (l.id)",
            "CREATE INDEX grade_code_idx IF NOT EXISTS FOR (g:GradeLevel) ON (g.code)",
            "CREATE INDEX domain_code_idx IF NOT EXISTS FOR (d:Domain) ON (d.code)"
        ]
        
        for index in indexes:
            session.run(index)
        
        logger.info("Indexes created")
    
    def _create_constraints(self, session):
        """Create constraints"""
        constraints = [
            "CREATE CONSTRAINT standard_code_unique IF NOT EXISTS FOR (s:AchievementStandard) REQUIRE s.code IS UNIQUE",
            "CREATE CONSTRAINT level_id_unique IF NOT EXISTS FOR (l:AchievementLevel) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT grade_code_unique IF NOT EXISTS FOR (g:GradeLevel) REQUIRE g.code IS UNIQUE",
            "CREATE CONSTRAINT domain_code_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.code IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                session.run(constraint)
            except Exception as e:
                logger.warning(f"Constraint creation failed (may already exist): {e}")
        
        logger.info("Constraints created")
    
    def query_similar_standards(self, standard_code: str, limit: int = 5) -> List[Dict]:
        """Query similar standards"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s1:AchievementStandard {code: $code})-[r:SIMILAR_TO|CONCEPTUALLY_SIMILAR|PROCEDURALLY_SIMILAR]-(s2:AchievementStandard)
                RETURN s2.code as code, s2.content as content, r.weight as similarity, type(r) as relation_type
                ORDER BY r.weight DESC
                LIMIT $limit
            """, code=standard_code, limit=limit)
            
            return [dict(record) for record in result]
    
    def query_prerequisite_chain(self, standard_code: str) -> List[Dict]:
        """Query prerequisite chain"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (start:AchievementStandard)-[:PREREQUISITE*1..5]->(end:AchievementStandard {code: $code})
                RETURN [node in nodes(path) | {code: node.code, content: node.content}] as chain,
                       length(path) as chain_length
                ORDER BY chain_length
            """, code=standard_code)
            
            return [dict(record) for record in result]
    
    def query_learning_pathway(self, domain_code: str, grade_code: str) -> List[Dict]:
        """Query learning pathway for domain and grade"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:GradeLevel {code: $grade_code})-[:CONTAINS_STANDARD]->(s:AchievementStandard)
                WHERE s.domain_code = $domain_code
                OPTIONAL MATCH (s)-[r:PREREQUISITE]->(next:AchievementStandard)
                RETURN s.code as code, s.content as content, s.difficulty as difficulty,
                       collect({next_code: next.code, weight: r.weight}) as next_steps
                ORDER BY s.difficulty
            """, domain_code=domain_code, grade_code=grade_code)
            
            return [dict(record) for record in result]
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        with self.driver.session() as session:
            # Node counts
            node_stats = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
            """)
            
            # Relationship counts
            rel_stats = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
            """)
            
            # Graph metrics
            metrics = session.run("""
                MATCH (n)
                WITH count(n) as node_count
                MATCH ()-[r]->()
                WITH node_count, count(r) as edge_count
                RETURN node_count, edge_count, 
                       round(edge_count * 2.0 / node_count / (node_count - 1), 4) as density
            """).single()
            
            return {
                'nodes': {record['label']: record['count'] for record in node_stats},
                'relationships': {record['relationship']: record['count'] for record in rel_stats},
                'metrics': dict(metrics) if metrics else {}
            }
