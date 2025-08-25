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
        
        # Extract curriculum data if available
        curriculum_data = all_results.get('curriculum_data', {})
        if not curriculum_data:
            # Try to load from database if not in results
            try:
                from src.data_manager import DatabaseManager
                db_manager = DatabaseManager()
                curriculum_data = db_manager.extract_all_curriculum_data()
            except Exception as e:
                logger.warning(f"Could not load curriculum data: {e}")
        
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
        
        # Create achievement standard nodes from actual data
        self._create_achievement_standards(session, curriculum_data)
        
        # Create achievement level nodes from actual data
        self._create_achievement_levels(session, curriculum_data)
    
    def _create_achievement_standards(self, session, curriculum_data=None):
        """Create achievement standard nodes from actual data"""
        if curriculum_data and 'achievement_standards' in curriculum_data:
            standards_df = curriculum_data['achievement_standards']
            
            # Map grade levels to codes
            grade_map = {
                '1-2': 'ELEM_1_2',
                '3-4': 'ELEM_3_4', 
                '5-6': 'ELEM_5_6',
                '1-3': 'MIDDLE'
            }
            
            # Map domains to codes
            domain_map = {
                '수와 연산': 'NUMBER_OPERATION',
                '변화와 관계': 'CHANGE_RELATION',
                '도형과 측정': 'GEOMETRY_MEASUREMENT',
                '자료와 가능성': 'DATA_POSSIBILITY'
            }
            
            for _, row in standards_df.iterrows():
                # Extract grade code from grade_range
                grade_range = row.get('grade_range', '')
                grade_code = 'UNKNOWN'
                for key, value in grade_map.items():
                    if key in grade_range:
                        grade_code = value
                        break
                
                # Map domain name to code
                domain_code = domain_map.get(row.get('domain_name', ''), 'UNKNOWN')
                
                # Estimate difficulty based on standard order
                difficulty = min(5, max(1, row.get('standard_order', 3) // 3 + 1))
                
                session.run("""
                    CREATE (s:AchievementStandard {
                        code: $code,
                        title: $title,
                        content: $content,
                        grade_code: $grade_code,
                        grade_range: $grade_range,
                        domain_code: $domain_code,
                        domain_name: $domain_name,
                        difficulty: $difficulty,
                        standard_order: $standard_order,
                        level_id: $level_id,
                        domain_id: $domain_id
                    })
                """, 
                    code=row.get('standard_code', ''),
                    title=row.get('standard_title', ''),
                    content=row.get('standard_content', ''),
                    grade_code=grade_code,
                    grade_range=row.get('grade_range', ''),
                    domain_code=domain_code,
                    domain_name=row.get('domain_name', ''),
                    difficulty=difficulty,
                    standard_order=row.get('standard_order', 0),
                    level_id=row.get('level_id', 0),
                    domain_id=row.get('domain_id', 0)
                )
            
            logger.info(f"Created {len(standards_df)} achievement standard nodes")
        else:
            logger.warning("No achievement standards data provided, skipping node creation")
    
    def _create_achievement_levels(self, session, curriculum_data=None):
        """Create achievement level nodes from actual data"""
        if curriculum_data and 'achievement_levels' in curriculum_data:
            levels_df = curriculum_data['achievement_levels']
            
            for _, row in levels_df.iterrows():
                # Create unique ID
                level_id = f"{row.get('standard_code', '')}_{row.get('level_code', '')}"
                
                session.run("""
                    CREATE (l:AchievementLevel {
                        id: $id,
                        achievement_level_id: $achievement_level_id,
                        standard_code: $standard_code,
                        level_code: $level_code,
                        level_name: $level_name,
                        description: $description
                    })
                """,
                    id=level_id,
                    achievement_level_id=row.get('achievement_level_id', 0),
                    standard_code=row.get('standard_code', ''),
                    level_code=row.get('level_code', ''),
                    level_name=row.get('level_name', ''),
                    description=row.get('level_description', '')
                )
            
            logger.info(f"Created {len(levels_df)} achievement level nodes")
        else:
            logger.warning("No achievement levels data provided, skipping node creation")
    
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
