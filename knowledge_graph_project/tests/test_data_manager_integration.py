"""
Integration tests for data_manager.py with real database
Requires PostgreSQL to be running with test data
"""
import pytest
import pandas as pd
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_manager import DatabaseManager, CurriculumDataProcessor

# Load environment variables
load_dotenv()

# Skip integration tests if no database connection
SKIP_INTEGRATION = not os.getenv('DATABASE_URL')


@pytest.mark.skipif(SKIP_INTEGRATION, reason="No database connection available")
class TestDatabaseIntegration:
    """Integration tests with real database"""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create real DatabaseManager instance"""
        manager = DatabaseManager()
        yield manager
        # Cleanup
        if manager._connection:
            manager.disconnect()
    
    def test_real_connection(self, db_manager):
        """Test real database connection"""
        try:
            db_manager.connect()
            assert db_manager._connection is not None
            db_manager.disconnect()
        except Exception as e:
            pytest.skip(f"Database connection failed: {e}")
    
    def test_extract_real_achievement_standards(self, db_manager):
        """Test extracting real achievement standards"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_achievement_standards()
            
            # Verify expected structure
            assert not df.empty
            assert 'standard_id' in df.columns
            assert 'standard_code' in df.columns
            assert 'standard_content' in df.columns
            assert 'domain_name' in df.columns
            assert 'grade_range' in df.columns
            
            # Verify data quality
            assert df['standard_code'].notna().all()
            assert df['standard_content'].notna().all()
            
            # Check expected count (should be 181)
            assert len(df) == 181
            
            # Verify sample data
            sample = df[df['standard_code'] == '2수01-01']
            if not sample.empty:
                assert '수와 연산' in sample.iloc[0]['domain_name']
                assert '1-2학년' in sample.iloc[0]['grade_range']
        
        finally:
            db_manager.disconnect()
    
    def test_extract_real_achievement_levels(self, db_manager):
        """Test extracting real achievement levels"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_achievement_levels()
            
            # Verify structure
            assert not df.empty
            assert 'achievement_level_id' in df.columns
            assert 'standard_id' in df.columns
            assert 'level_code' in df.columns
            assert 'level_description' in df.columns
            
            # Check expected count (should be 663)
            assert len(df) == 663
            
            # Verify level codes
            assert set(df['level_code'].unique()).issubset({'A', 'B', 'C', 'D', 'E'})
        
        finally:
            db_manager.disconnect()
    
    def test_extract_prerequisite_suggestions(self, db_manager):
        """Test extracting prerequisite suggestions from view"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_prerequisite_suggestions()
            
            # View might have data
            if not df.empty:
                assert 'src_standard_id' in df.columns
                assert 'dst_standard_id' in df.columns
                assert 'confidence' in df.columns
                assert 'relation_type' in df.columns
                
                # Check relation type
                assert all(df['relation_type'] == 'PREREQUISITE')
                
                # Check confidence range
                assert df['confidence'].between(0, 1).all()
        
        finally:
            db_manager.disconnect()
    
    def test_extract_horizontal_suggestions(self, db_manager):
        """Test extracting horizontal suggestions from view"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_horizontal_suggestions()
            
            # View might have data
            if not df.empty:
                assert 'src_standard_id' in df.columns
                assert 'dst_standard_id' in df.columns
                assert 'confidence' in df.columns
                assert 'relation_type' in df.columns
                
                # Check relation type
                assert all(df['relation_type'] == 'HORIZONTAL')
        
        finally:
            db_manager.disconnect()
    
    def test_extract_competencies(self, db_manager):
        """Test extracting competencies"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_competencies()
            
            # Should have 5 competencies
            assert len(df) == 5
            assert 'comp_code' in df.columns
            assert 'comp_name' in df.columns
            
            # Check expected competencies
            expected_codes = {'PS', 'RS', 'COM', 'CON', 'INF'}
            assert set(df['comp_code']) == expected_codes
        
        finally:
            db_manager.disconnect()
    
    def test_extract_representation_types(self, db_manager):
        """Test extracting representation types"""
        db_manager.connect()
        
        try:
            df = db_manager.extract_representation_types()
            
            # Should have 9 representation types
            assert len(df) == 9
            assert 'type_name' in df.columns
            
            # Check some expected types
            expected_types = {'표', '식', '그래프', '도형', '구체물'}
            actual_types = set(df['type_name'])
            assert expected_types.issubset(actual_types)
        
        finally:
            db_manager.disconnect()
    
    def test_check_cycles_function(self, db_manager):
        """Test cycle detection function"""
        db_manager.connect()
        
        try:
            df = db_manager.check_cycles()
            
            # Should return empty if no cycles
            # (since achievement_standard_relations table is empty)
            assert isinstance(df, pd.DataFrame)
            assert df.empty  # No data means no cycles
        
        finally:
            db_manager.disconnect()
    
    def test_extract_all_curriculum_data_integration(self, db_manager):
        """Test extracting all curriculum data"""
        data = db_manager.extract_all_curriculum_data()
        
        # Verify all expected keys
        expected_keys = [
            'achievement_standards',
            'achievement_levels',
            'content_elements',
            'terms_symbols',
            'standard_relations',
            'standard_terms',
            'competencies',
            'prerequisite_suggestions',
            'horizontal_suggestions',
            'representation_types'
        ]
        
        for key in expected_keys:
            assert key in data
            assert isinstance(data[key], pd.DataFrame)
        
        # Verify counts
        assert len(data['achievement_standards']) == 181
        assert len(data['achievement_levels']) == 663
        assert len(data['content_elements']) == 291
        assert len(data['terms_symbols']) == 362
        assert len(data['competencies']) == 5
        assert len(data['representation_types']) == 9
    
    def test_data_processing_with_real_data(self, db_manager):
        """Test data processing with real curriculum data"""
        # Get real data
        data = db_manager.extract_all_curriculum_data()
        
        # Process documents
        documents = CurriculumDataProcessor.prepare_document_corpus(data)
        
        # Verify document count
        # Should have documents for standards and levels
        assert len(documents) >= 181  # At least all standards
        
        # Check document structure
        for doc in documents[:10]:  # Check first 10
            assert 'id' in doc
            assert 'type' in doc
            assert doc['type'] in ['achievement_standard', 'achievement_level']
            
            if doc['type'] == 'achievement_standard':
                assert 'code' in doc
                assert 'domain' in doc
                assert 'grade_range' in doc
        
        # Create AI context
        context = CurriculumDataProcessor.create_context_for_ai(data)
        
        # Verify context content
        assert '2022 개정 한국 수학과 교육과정' in context
        assert '성취기준: 181개' in context
        assert '성취수준: 663개' in context
        assert '내용 요소: 291개' in context
        assert '용어 및 기호: 362개' in context
        
        # Check domain distribution
        assert '수와 연산' in context
        assert '도형과 측정' in context
        assert '변화와 관계' in context
        assert '자료와 가능성' in context


@pytest.mark.skipif(SKIP_INTEGRATION, reason="No database connection available")
class TestPerformance:
    """Performance tests for data extraction"""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create DatabaseManager instance"""
        return DatabaseManager()
    
    def test_extraction_performance(self, db_manager, benchmark=None):
        """Test performance of full data extraction"""
        import time
        
        start_time = time.time()
        data = db_manager.extract_all_curriculum_data()
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        # Should complete within reasonable time
        assert extraction_time < 10.0  # 10 seconds max
        
        print(f"\nExtraction completed in {extraction_time:.2f} seconds")
        print(f"Total records extracted: {sum(len(df) for df in data.values())}")
    
    def test_document_processing_performance(self, db_manager):
        """Test performance of document processing"""
        import time
        
        # Get data
        data = db_manager.extract_all_curriculum_data()
        
        # Measure document processing
        start_time = time.time()
        documents = CurriculumDataProcessor.prepare_document_corpus(data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should be fast
        assert processing_time < 2.0  # 2 seconds max
        
        print(f"\nDocument processing completed in {processing_time:.2f} seconds")
        print(f"Documents created: {len(documents)}")


if __name__ == "__main__":
    # Run integration tests only if database is available
    if SKIP_INTEGRATION:
        print("Skipping integration tests - no database connection")
        print("Set DATABASE_URL environment variable to run integration tests")
    else:
        pytest.main([__file__, "-v", "-s"])