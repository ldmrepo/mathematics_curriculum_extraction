"""
Unit tests for data_manager.py module
Tests DatabaseManager and CurriculumDataProcessor classes
"""
import pytest
import pandas as pd
import psycopg2
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_manager import DatabaseManager, CurriculumDataProcessor


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance with mocked connection"""
        with patch('src.data_manager.config') as mock_config:
            mock_config.database.postgresql_url = "postgresql://test:test@localhost/test"
            manager = DatabaseManager()
            manager._connection = Mock()
            return manager
    
    def test_init(self):
        """Test DatabaseManager initialization"""
        with patch('src.data_manager.config') as mock_config:
            mock_config.database.postgresql_url = "postgresql://test:test@localhost/test"
            manager = DatabaseManager()
            assert manager.connection_string == "postgresql://test:test@localhost/test"
            assert manager._connection is None
    
    @patch('psycopg2.connect')
    def test_connect_success(self, mock_connect):
        """Test successful database connection"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        with patch('src.data_manager.config') as mock_config:
            mock_config.database.postgresql_url = "postgresql://test:test@localhost/test"
            manager = DatabaseManager()
            manager.connect()
            
            mock_connect.assert_called_once_with("postgresql://test:test@localhost/test")
            assert manager._connection == mock_connection
    
    @patch('psycopg2.connect')
    def test_connect_failure(self, mock_connect):
        """Test database connection failure"""
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        with patch('src.data_manager.config') as mock_config:
            mock_config.database.postgresql_url = "postgresql://test:test@localhost/test"
            manager = DatabaseManager()
            
            with pytest.raises(psycopg2.OperationalError):
                manager.connect()
    
    def test_disconnect(self, db_manager):
        """Test database disconnection"""
        mock_connection = Mock()
        db_manager._connection = mock_connection
        
        db_manager.disconnect()
        mock_connection.close.assert_called_once()
    
    @patch('pandas.read_sql_query')
    def test_extract_achievement_standards(self, mock_read_sql, db_manager):
        """Test extracting achievement standards"""
        expected_df = pd.DataFrame({
            'standard_id': [1, 2],
            'standard_code': ['2수01-01', '2수01-02'],
            'standard_content': ['Content 1', 'Content 2']
        })
        mock_read_sql.return_value = expected_df
        
        result = db_manager.extract_achievement_standards()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'standard_code' in result.columns
        mock_read_sql.assert_called_once()
    
    @patch('pandas.read_sql_query')
    def test_extract_achievement_levels(self, mock_read_sql, db_manager):
        """Test extracting achievement levels"""
        expected_df = pd.DataFrame({
            'achievement_level_id': [1, 2],
            'standard_id': [1, 1],
            'level_code': ['A', 'B']
        })
        mock_read_sql.return_value = expected_df
        
        result = db_manager.extract_achievement_levels()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'level_code' in result.columns
    
    @patch('pandas.read_sql_query')
    def test_extract_prerequisite_suggestions(self, mock_read_sql, db_manager):
        """Test extracting prerequisite suggestions from view"""
        expected_df = pd.DataFrame({
            'src_standard_id': [1, 2],
            'dst_standard_id': [2, 3],
            'confidence': [0.7, 0.8]
        })
        mock_read_sql.return_value = expected_df
        
        result = db_manager.extract_prerequisite_suggestions()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'confidence' in result.columns
    
    @patch('pandas.read_sql_query')
    def test_extract_empty_table(self, mock_read_sql, db_manager):
        """Test handling empty table/view"""
        mock_read_sql.side_effect = Exception("Table does not exist")
        
        result = db_manager.extract_prerequisite_suggestions()
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    @patch('pandas.read_sql_query')
    def test_check_cycles(self, mock_read_sql, db_manager):
        """Test cycle detection function"""
        # Test no cycles
        mock_read_sql.return_value = pd.DataFrame()
        
        result = db_manager.check_cycles()
        assert result.empty
        
        # Test with cycles
        cycles_df = pd.DataFrame({
            'cycle_path': ['A -> B -> C -> A'],
            'cycle_length': [3]
        })
        mock_read_sql.return_value = cycles_df
        
        result = db_manager.check_cycles()
        assert len(result) == 1
        assert result.iloc[0]['cycle_length'] == 3
    
    @patch.object(DatabaseManager, 'extract_achievement_standards')
    @patch.object(DatabaseManager, 'extract_achievement_levels')
    @patch.object(DatabaseManager, 'extract_content_elements')
    @patch.object(DatabaseManager, 'extract_terms_symbols')
    @patch.object(DatabaseManager, 'extract_prerequisite_suggestions')
    @patch.object(DatabaseManager, 'connect')
    @patch.object(DatabaseManager, 'disconnect')
    def test_extract_all_curriculum_data(self, mock_disconnect, mock_connect,
                                        mock_prereq, mock_terms, mock_elements,
                                        mock_levels, mock_standards, db_manager):
        """Test extracting all curriculum data"""
        # Setup mock returns
        mock_standards.return_value = pd.DataFrame({'standard_id': [1]})
        mock_levels.return_value = pd.DataFrame({'level_id': [1]})
        mock_elements.return_value = pd.DataFrame({'element_id': [1]})
        mock_terms.return_value = pd.DataFrame({'term_id': [1]})
        mock_prereq.return_value = pd.DataFrame({'src_standard_id': [1]})
        
        result = db_manager.extract_all_curriculum_data()
        
        assert isinstance(result, dict)
        assert 'achievement_standards' in result
        assert 'achievement_levels' in result
        assert 'prerequisite_suggestions' in result
        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()


class TestCurriculumDataProcessor:
    """Test CurriculumDataProcessor class"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample curriculum data for testing"""
        return {
            'achievement_standards': pd.DataFrame({
                'standard_id': [1, 2],
                'standard_code': ['2수01-01', '2수01-02'],
                'standard_title': ['Title 1', 'Title 2'],
                'standard_content': ['Content 1', 'Content 2'],
                'domain_name': ['수와 연산', '수와 연산'],
                'domain_id': [1, 1],
                'level_id': [1, 1],
                'grade_range': ['1-2학년', '1-2학년'],
                'grade_start': [1, 1],
                'grade_end': [2, 2],
                'element_id': [1, 1],
                'element_name': ['Element 1', 'Element 2']
            }),
            'achievement_levels': pd.DataFrame({
                'achievement_level_id': [1, 2],
                'standard_id': [1, 1],
                'level_code': ['A', 'B'],
                'level_name': ['상', '중'],
                'level_description': ['Description A', 'Description B'],
                'standard_code': ['2수01-01', '2수01-01'],
                'standard_content': ['Content 1', 'Content 1']
            }),
            'content_elements': pd.DataFrame({
                'element_id': [1],
                'element_name': ['Element 1']
            }),
            'terms_symbols': pd.DataFrame({
                'term_id': [1],
                'term_name': ['덧셈']
            })
        }
    
    def test_prepare_document_corpus(self, sample_data):
        """Test document corpus preparation"""
        documents = CurriculumDataProcessor.prepare_document_corpus(sample_data)
        
        assert isinstance(documents, list)
        assert len(documents) == 4  # 2 standards + 2 levels
        
        # Check standard document
        standard_doc = documents[0]
        assert standard_doc['type'] == 'achievement_standard'
        assert standard_doc['code'] == '2수01-01'
        assert 'metadata' in standard_doc
        
        # Check level document
        level_doc = documents[2]
        assert level_doc['type'] == 'achievement_level'
        assert level_doc['level_code'] == 'A'
    
    def test_create_context_for_ai(self, sample_data):
        """Test AI context creation"""
        context = CurriculumDataProcessor.create_context_for_ai(sample_data)
        
        assert isinstance(context, str)
        assert '2022 개정 한국 수학과 교육과정' in context
        assert '성취기준: 2개' in context
        assert '성취수준: 2개' in context
        assert '수와 연산' in context
        assert '1-2학년' in context
    
    def test_prepare_document_corpus_with_empty_data(self):
        """Test document corpus with empty dataframes"""
        empty_data = {
            'achievement_standards': pd.DataFrame(),
            'achievement_levels': pd.DataFrame()
        }
        
        documents = CurriculumDataProcessor.prepare_document_corpus(empty_data)
        
        assert isinstance(documents, list)
        assert len(documents) == 0
    
    def test_create_context_with_missing_columns(self):
        """Test context creation with missing columns"""
        incomplete_data = {
            'achievement_standards': pd.DataFrame({
                'standard_id': [1],
                'standard_code': ['2수01-01']
                # Missing domain_name and level_name
            }),
            'achievement_levels': pd.DataFrame(),
            'content_elements': pd.DataFrame(),
            'terms_symbols': pd.DataFrame()
        }
        
        # Should handle missing columns gracefully
        context = CurriculumDataProcessor.create_context_for_ai(incomplete_data)
        assert isinstance(context, str)
        assert '성취기준: 1개' in context


class TestIntegration:
    """Integration tests for data_manager module"""
    
    @pytest.mark.integration
    @patch('psycopg2.connect')
    def test_full_data_extraction_flow(self, mock_connect):
        """Test complete data extraction workflow"""
        # Setup mock connection and cursor
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        with patch('pandas.read_sql_query') as mock_read_sql:
            # Setup return values for different queries
            mock_read_sql.side_effect = [
                pd.DataFrame({'standard_id': [1, 2]}),  # standards
                pd.DataFrame({'level_id': [1, 2]}),     # levels
                pd.DataFrame({'element_id': [1]}),      # elements
                pd.DataFrame({'term_id': [1]}),         # terms
                pd.DataFrame(),                         # relations (empty)
                pd.DataFrame(),                         # standard_terms (empty)
                pd.DataFrame({'comp_id': [1]}),         # competencies
                pd.DataFrame({'src_standard_id': [1]}), # prerequisite suggestions
                pd.DataFrame({'src_standard_id': [1]}), # horizontal suggestions
                pd.DataFrame({'type_name': ['표']})     # representation types
            ]
            
            with patch('src.data_manager.config') as mock_config:
                mock_config.database.postgresql_url = "postgresql://test:test@localhost/test"
                
                manager = DatabaseManager()
                data = manager.extract_all_curriculum_data()
                
                assert isinstance(data, dict)
                assert len(data) > 0
                assert all(isinstance(v, pd.DataFrame) for v in data.values())
    
    @pytest.mark.integration
    def test_data_processing_pipeline(self):
        """Test data processing pipeline"""
        # Create sample data
        sample_data = {
            'achievement_standards': pd.DataFrame({
                'standard_id': list(range(1, 11)),
                'standard_code': [f'2수01-{i:02d}' for i in range(1, 11)],
                'standard_title': [f'Title {i}' for i in range(1, 11)],
                'standard_content': [f'Content {i}' for i in range(1, 11)],
                'domain_name': ['수와 연산'] * 10,
                'domain_id': [1] * 10,
                'level_id': [1] * 10,
                'grade_range': ['1-2학년'] * 10,
                'grade_start': [1] * 10,
                'grade_end': [2] * 10
            }),
            'achievement_levels': pd.DataFrame({
                'achievement_level_id': list(range(1, 31)),
                'standard_id': [i//3 + 1 for i in range(30)],
                'level_code': ['A', 'B', 'C'] * 10,
                'level_name': ['상', '중', '하'] * 10,
                'level_description': [f'Level desc {i}' for i in range(1, 31)],
                'standard_code': [f'2수01-{i//3 + 1:02d}' for i in range(30)],
                'standard_content': [f'Content {i//3 + 1}' for i in range(30)]
            }),
            'content_elements': pd.DataFrame({
                'element_id': list(range(1, 6)),
                'element_name': [f'Element {i}' for i in range(1, 6)]
            }),
            'terms_symbols': pd.DataFrame({
                'term_id': list(range(1, 11)),
                'term_name': [f'Term {i}' for i in range(1, 11)]
            })
        }
        
        # Process data
        documents = CurriculumDataProcessor.prepare_document_corpus(sample_data)
        context = CurriculumDataProcessor.create_context_for_ai(sample_data)
        
        # Validate results
        assert len(documents) == 40  # 10 standards + 30 levels
        assert '성취기준: 10개' in context
        assert '성취수준: 30개' in context
        
        # Check document structure
        for doc in documents:
            assert 'id' in doc
            assert 'type' in doc
            assert 'content' in doc or 'level_description' in doc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])