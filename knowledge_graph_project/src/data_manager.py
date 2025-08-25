"""
Database connection and data extraction utilities
"""
import psycopg2
import pandas as pd
from typing import List, Dict, Any
from loguru import logger
from config.settings import config

class DatabaseManager:
    """PostgreSQL database manager for curriculum data"""
    
    def __init__(self):
        self.connection_string = config.database.postgresql_url
        self._connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self._connection = psycopg2.connect(self.connection_string)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            logger.info("Disconnected from database")
    
    def extract_achievement_standards(self) -> pd.DataFrame:
        """Extract all achievement standards"""
        query = """
        SELECT 
            s.standard_id,
            s.standard_code,
            s.standard_title,
            s.standard_content,
            s.level_id,
            s.domain_id,
            s.element_id,
            s.standard_order,
            ce.element_name,
            ce.element_description,
            d.domain_name,
            d.domain_code,
            sl.school_type,
            sl.grade_range,
            sl.grade_start,
            sl.grade_end,
            sl.level_code
        FROM curriculum.achievement_standards s
        JOIN curriculum.domains d ON s.domain_id = d.domain_id
        JOIN curriculum.school_levels sl ON s.level_id = sl.level_id
        LEFT JOIN curriculum.content_elements ce ON s.element_id = ce.element_id
        ORDER BY s.standard_code
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} achievement standards")
            return df
        except Exception as e:
            logger.error(f"Failed to extract achievement standards: {e}")
            raise
    
    def extract_achievement_levels(self) -> pd.DataFrame:
        """Extract all achievement levels"""
        query = """
        SELECT 
            sal.sal_id as achievement_level_id,
            sal.standard_id,
            sal.level_code,
            al.level_name,
            sal.level_description,
            s.standard_code,
            s.standard_content
        FROM curriculum.standard_achievement_levels sal
        JOIN curriculum.achievement_levels al ON sal.level_code = al.level_code
        JOIN curriculum.achievement_standards s ON sal.standard_id = s.standard_id
        ORDER BY s.standard_code, al.level_order
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} achievement levels")
            return df
        except Exception as e:
            logger.error(f"Failed to extract achievement levels: {e}")
            raise
    
    def extract_content_elements(self) -> pd.DataFrame:
        """Extract content elements"""
        query = """
        SELECT 
            ce.element_id,
            ce.level_id,
            ce.domain_id,
            ce.category_id,
            ce.element_name,
            ce.element_description,
            ce.element_order,
            d.domain_name,
            d.domain_code,
            sl.school_type,
            sl.grade_range,
            c.category_name
        FROM curriculum.content_elements ce
        JOIN curriculum.domains d ON ce.domain_id = d.domain_id
        JOIN curriculum.school_levels sl ON ce.level_id = sl.level_id
        JOIN curriculum.categories c ON ce.category_id = c.category_id
        ORDER BY ce.level_id, ce.domain_id, ce.element_order
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} content elements")
            return df
        except Exception as e:
            logger.error(f"Failed to extract content elements: {e}")
            raise
    
    def extract_terms_symbols(self) -> pd.DataFrame:
        """Extract terms and symbols"""
        query = """
        SELECT 
            ts.term_id,
            ts.level_id,
            ts.domain_id,
            ts.term_name,
            ts.term_description,
            ts.term_type,
            ts.latex_expression,
            d.domain_name,
            d.domain_code,
            sl.school_type,
            sl.grade_range
        FROM curriculum.terms_symbols ts
        JOIN curriculum.domains d ON ts.domain_id = d.domain_id
        JOIN curriculum.school_levels sl ON ts.level_id = sl.level_id
        ORDER BY ts.level_id, ts.domain_id, ts.term_name
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} terms and symbols")
            return df
        except Exception as e:
            logger.error(f"Failed to extract terms and symbols: {e}")
            raise
    
    def extract_standard_relations(self) -> pd.DataFrame:
        """Extract achievement standard relations from v1.3.0 schema"""
        query = """
        SELECT 
            asr.rel_id,
            asr.src_standard_id,
            asr.dst_standard_id,
            asr.relation_type,
            asr.rationale,
            asr.method,
            asr.confidence,
            s1.standard_code as src_code,
            s2.standard_code as dst_code,
            s1.standard_content as src_content,
            s2.standard_content as dst_content
        FROM curriculum.achievement_standard_relations asr
        JOIN curriculum.achievement_standards s1 ON asr.src_standard_id = s1.standard_id
        JOIN curriculum.achievement_standards s2 ON asr.dst_standard_id = s2.standard_id
        ORDER BY asr.relation_type, asr.confidence DESC
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} standard relations")
            return df
        except Exception as e:
            logger.warning(f"No standard relations found or table doesn't exist: {e}")
            return pd.DataFrame()
    
    def extract_standard_terms(self) -> pd.DataFrame:
        """Extract standard-term mappings from v1.3.0 schema"""
        query = """
        SELECT 
            st.st_id,
            st.standard_id,
            st.term_id,
            st.relation_type,
            st.method,
            st.confidence,
            s.standard_code,
            ts.term_name,
            ts.term_type
        FROM curriculum.standard_terms st
        JOIN curriculum.achievement_standards s ON st.standard_id = s.standard_id
        JOIN curriculum.terms_symbols ts ON st.term_id = ts.term_id
        ORDER BY s.standard_code, ts.term_name
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} standard-term mappings")
            return df
        except Exception as e:
            logger.warning(f"No standard-term mappings found or table doesn't exist: {e}")
            return pd.DataFrame()
    
    def extract_competencies(self) -> pd.DataFrame:
        """Extract competencies and standard mappings from v1.3.0 schema"""
        query = """
        SELECT 
            c.comp_id,
            c.comp_code,
            c.comp_name,
            c.description
        FROM curriculum.competencies c
        ORDER BY c.comp_code
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} competencies")
            return df
        except Exception as e:
            logger.warning(f"No competencies found or table doesn't exist: {e}")
            return pd.DataFrame()
    
    def extract_prerequisite_suggestions(self) -> pd.DataFrame:
        """Extract prerequisite suggestions from v1.3.0 view"""
        query = """
        SELECT 
            src_standard_id,
            dst_standard_id,
            relation_type,
            rationale,
            method,
            confidence
        FROM curriculum.v_prerequisite_suggestions
        ORDER BY confidence DESC
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} prerequisite suggestions")
            return df
        except Exception as e:
            logger.warning(f"Could not extract prerequisite suggestions: {e}")
            return pd.DataFrame()
    
    def extract_horizontal_suggestions(self) -> pd.DataFrame:
        """Extract horizontal suggestions from v1.3.0 view"""
        query = """
        SELECT 
            src_standard_id,
            dst_standard_id,
            relation_type,
            rationale,
            method,
            confidence
        FROM curriculum.v_horizontal_suggestions
        ORDER BY confidence DESC
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} horizontal suggestions")
            return df
        except Exception as e:
            logger.warning(f"Could not extract horizontal suggestions: {e}")
            return pd.DataFrame()
    
    def extract_representation_types(self) -> pd.DataFrame:
        """Extract representation types from v1.3.0 schema"""
        query = """
        SELECT 
            rep_type_id,
            type_name,
            description
        FROM curriculum.representation_types
        ORDER BY rep_type_id
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} representation types")
            return df
        except Exception as e:
            logger.warning(f"Could not extract representation types: {e}")
            return pd.DataFrame()
    
    def check_cycles(self) -> pd.DataFrame:
        """Check for cycles using v1.3.0 function"""
        query = "SELECT * FROM curriculum.detect_prerequisite_cycles()"
        
        try:
            df = pd.read_sql_query(query, self._connection)
            if len(df) > 0:
                logger.warning(f"Found {len(df)} cycles in prerequisite relationships")
            else:
                logger.info("No cycles detected in prerequisite relationships")
            return df
        except Exception as e:
            logger.error(f"Could not check cycles: {e}")
            return pd.DataFrame()
    
    def extract_all_curriculum_data(self) -> Dict[str, pd.DataFrame]:
        """Extract all curriculum data including v1.3.0 tables"""
        self.connect()
        
        try:
            data = {
                'achievement_standards': self.extract_achievement_standards(),
                'achievement_levels': self.extract_achievement_levels(),
                'content_elements': self.extract_content_elements(),
                'terms_symbols': self.extract_terms_symbols(),
                # v1.3.0 tables
                'standard_relations': self.extract_standard_relations(),
                'standard_terms': self.extract_standard_terms(),
                'competencies': self.extract_competencies(),
                # v1.3.0 views for suggestions
                'prerequisite_suggestions': self.extract_prerequisite_suggestions(),
                'horizontal_suggestions': self.extract_horizontal_suggestions(),
                'representation_types': self.extract_representation_types()
            }
            
            logger.info("Successfully extracted all curriculum data")
            return data
            
        finally:
            self.disconnect()

class CurriculumDataProcessor:
    """Process and prepare curriculum data for AI models"""
    
    @staticmethod
    def prepare_document_corpus(data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Prepare document corpus for embedding and analysis"""
        documents = []
        
        # Achievement Standards
        for _, row in data['achievement_standards'].iterrows():
            doc = {
                'id': f"standard_{row['standard_id']}",
                'type': 'achievement_standard',
                'code': row['standard_code'],
                'title': row.get('standard_title', ''),
                'content': row['standard_content'],
                'domain': row['domain_name'],
                'school_type': row.get('school_type', ''),
                'grade_range': row['grade_range'],
                'metadata': {
                    'domain_id': row['domain_id'],
                    'level_id': row['level_id'],
                    'element_id': row.get('element_id'),
                    'element_name': row.get('element_name')
                }
            }
            documents.append(doc)
        
        # Achievement Levels
        for _, row in data['achievement_levels'].iterrows():
            doc = {
                'id': f"level_{row['achievement_level_id']}",
                'type': 'achievement_level',
                'standard_code': row['standard_code'],
                'level_code': row['level_code'],
                'content': row['level_description'],
                'metadata': {
                    'standard_id': row['standard_id'],
                    'parent_standard': row['standard_content']
                }
            }
            documents.append(doc)
        
        logger.info(f"Prepared {len(documents)} documents for processing")
        return documents
    
    @staticmethod
    def create_context_for_ai(data: Dict[str, pd.DataFrame]) -> str:
        """Create comprehensive context for AI models"""
        
        # Count statistics
        stats = {
            'standards_count': len(data['achievement_standards']),
            'levels_count': len(data['achievement_levels']),
            'elements_count': len(data['content_elements']),
            'terms_count': len(data['terms_symbols'])
        }
        
        # Domain distribution (handle missing column)
        if 'domain_name' in data['achievement_standards'].columns:
            domain_dist = data['achievement_standards']['domain_name'].value_counts()
            domain_section = f"=== 영역별 분포 ===\n{domain_dist.to_string()}"
        else:
            domain_section = "=== 영역별 분포 ===\n(영역 정보 없음)"
        
        # Grade level distribution (handle missing column)
        if 'grade_range' in data['achievement_standards'].columns:
            grade_dist = data['achievement_standards']['grade_range'].value_counts()
            grade_section = f"=== 학년군별 분포 ===\n{grade_dist.to_string()}"
        else:
            grade_section = "=== 학년군별 분포 ===\n(학년 정보 없음)"
        
        context = f"""
2022 개정 한국 수학과 교육과정 데이터:

=== 전체 현황 ===
- 성취기준: {stats['standards_count']}개
- 성취수준: {stats['levels_count']}개  
- 내용 요소: {stats['elements_count']}개
- 용어 및 기호: {stats['terms_count']}개

{domain_section}

{grade_section}

=== 핵심 특징 ===
- 학년군: 초등 1-2학년군, 3-4학년군, 5-6학년군, 중학교 1-3학년군
- 영역: 수와 연산, 변화와 관계, 도형과 측정, 자료와 가능성
- 성취수준: 초등(A, B, C), 중등(A, B, C, D, E)
- 나선형 교육과정 구조 적용
"""
        
        return context.strip()
