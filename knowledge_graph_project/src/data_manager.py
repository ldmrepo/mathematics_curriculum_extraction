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
            s.standard_content,
            s.level_id,
            s.domain_id,
            s.element_name,
            d.domain_name,
            l.level_name,
            l.grade_start,
            l.grade_end
        FROM achievement_standards s
        JOIN domains d ON s.domain_id = d.domain_id
        JOIN school_levels l ON s.level_id = l.level_id
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
            al.level_id as achievement_level_id,
            al.standard_id,
            al.level_name,
            al.level_description,
            s.standard_code,
            s.standard_content
        FROM achievement_levels al
        JOIN achievement_standards s ON al.standard_id = s.standard_id
        ORDER BY s.standard_code, al.level_name
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
            ce.element_content,
            ce.element_order,
            d.domain_name,
            l.level_name
        FROM content_elements ce
        JOIN domains d ON ce.domain_id = d.domain_id
        JOIN school_levels l ON ce.level_id = l.level_id
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
            ts.term_content,
            ts.term_type,
            d.domain_name,
            l.level_name
        FROM terms_symbols ts
        JOIN domains d ON ts.domain_id = d.domain_id
        JOIN school_levels l ON ts.level_id = l.level_id
        ORDER BY ts.level_id, ts.domain_id, ts.term_content
        """
        
        try:
            df = pd.read_sql_query(query, self._connection)
            logger.info(f"Extracted {len(df)} terms and symbols")
            return df
        except Exception as e:
            logger.error(f"Failed to extract terms and symbols: {e}")
            raise
    
    def extract_all_curriculum_data(self) -> Dict[str, pd.DataFrame]:
        """Extract all curriculum data"""
        self.connect()
        
        try:
            data = {
                'achievement_standards': self.extract_achievement_standards(),
                'achievement_levels': self.extract_achievement_levels(),
                'content_elements': self.extract_content_elements(),
                'terms_symbols': self.extract_terms_symbols()
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
                'content': row['standard_content'],
                'domain': row['domain_name'],
                'level': row['level_name'],
                'grade_range': f"{row['grade_start']}-{row['grade_end']}",
                'metadata': {
                    'domain_id': row['domain_id'],
                    'level_id': row['level_id'],
                    'element_name': row['element_name']
                }
            }
            documents.append(doc)
        
        # Achievement Levels
        for _, row in data['achievement_levels'].iterrows():
            doc = {
                'id': f"level_{row['achievement_level_id']}",
                'type': 'achievement_level',
                'standard_code': row['standard_code'],
                'level_name': row['level_name'],
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
        
        # Domain distribution
        domain_dist = data['achievement_standards']['domain_name'].value_counts()
        
        # Grade level distribution
        grade_dist = data['achievement_standards']['level_name'].value_counts()
        
        context = f"""
2022 개정 한국 수학과 교육과정 데이터:

=== 전체 현황 ===
- 성취기준: {stats['standards_count']}개
- 성취수준: {stats['levels_count']}개  
- 내용 요소: {stats['elements_count']}개
- 용어 및 기호: {stats['terms_count']}개

=== 영역별 분포 ===
{domain_dist.to_string()}

=== 학년군별 분포 ===
{grade_dist.to_string()}

=== 핵심 특징 ===
- 학년군: 초등 1-2학년군, 3-4학년군, 5-6학년군, 중학교 1-3학년군
- 영역: 수와 연산, 변화와 관계, 도형과 측정, 자료와 가능성
- 성취수준: 초등(A, B, C), 중등(A, B, C, D, E)
- 나선형 교육과정 구조 적용
"""
        
        return context.strip()
