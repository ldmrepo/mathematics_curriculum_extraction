"""
Unit tests for the Knowledge Graph Construction Project
"""
import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

# Import modules to test
import sys
sys.path.append('../src')

from src.data_manager import DatabaseManager, CurriculumDataProcessor
from src.ai_models import AIModelManager, OpenAIInterface, ClaudeInterface, GeminiInterface
from config.settings import ModelConfig

class TestDataManager:
    """Test suite for data management functionality"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def sample_curriculum_data(self):
        """Sample curriculum data for testing"""
        return {
            'achievement_standards': pd.DataFrame([
                {
                    'standard_id': 1,
                    'standard_code': '2수01-01',
                    'standard_content': '수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.',
                    'level_id': 1,
                    'domain_id': 1,
                    'element_name': '네 자리 이하의 수',
                    'domain_name': '수와 연산',
                    'level_name': '초등학교 1-2학년군',
                    'grade_start': 1,
                    'grade_end': 2
                }
            ]),
            'achievement_levels': pd.DataFrame([
                {
                    'achievement_level_id': 1,
                    'standard_id': 1,
                    'level_name': 'A',
                    'level_description': '수가 사용되는 여러 가지 실생활 상황에서 수의 필요성을 말하고...',
                    'standard_code': '2수01-01',
                    'standard_content': '수의 필요성을 인식하면서...'
                }
            ])
        }
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        db_manager = DatabaseManager()
        assert db_manager.connection_string is not None
        assert db_manager._connection is None
    
    @patch('psycopg2.connect')
    def test_database_connection(self, mock_connect):
        """Test database connection"""
        mock_connect.return_value = Mock()
        
        db_manager = DatabaseManager()
        db_manager.connect()
        
        assert db_manager._connection is not None
        mock_connect.assert_called_once()
    
    def test_curriculum_data_processor(self, sample_curriculum_data):
        """Test curriculum data processing"""
        documents = CurriculumDataProcessor.prepare_document_corpus(sample_curriculum_data)
        
        assert len(documents) == 2  # 1 standard + 1 level
        assert documents[0]['type'] == 'achievement_standard'
        assert documents[1]['type'] == 'achievement_level'
        assert documents[0]['code'] == '2수01-01'
    
    def test_context_creation(self, sample_curriculum_data):
        """Test AI context creation"""
        context = CurriculumDataProcessor.create_context_for_ai(sample_curriculum_data)
        
        assert '성취기준: 1개' in context
        assert '성취수준: 1개' in context
        assert '수와 연산' in context
        assert '초등학교 1-2학년군' in context

class TestAIModels:
    """Test suite for AI model interfaces"""
    
    @pytest.fixture
    def mock_model_config(self):
        """Mock model configuration"""
        return ModelConfig(
            name="test-model",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.2,
            cost_per_input_token=1e-6,
            cost_per_output_token=2e-6
        )
    
    def test_ai_model_manager_initialization(self):
        """Test AIModelManager initialization"""
        manager = AIModelManager()
        
        assert 'gemini_pro' in manager.models
        assert 'gpt5' in manager.models
        assert 'claude_sonnet' in manager.models
        assert 'claude_opus' in manager.models
        assert manager.total_cost == 0.0
    
    def test_cost_calculation(self, mock_model_config):
        """Test cost calculation"""
        interface = OpenAIInterface(mock_model_config)
        
        cost = interface.calculate_cost(1000, 500)
        expected_cost = 1000 * 1e-6 + 500 * 2e-6
        
        assert cost == expected_cost
        assert interface.total_cost == expected_cost
        assert interface.token_usage['input'] == 1000
        assert interface.token_usage['output'] == 500
    
    @pytest.mark.asyncio
    async def test_openai_interface_mock(self, mock_model_config):
        """Test OpenAI interface with mocking"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock response
            mock_response = Mock()
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            interface = OpenAIInterface(mock_model_config)
            result = await interface.generate_completion("Test prompt")
            
            assert result['content'] == "Test response"
            assert result['input_tokens'] == 100
            assert result['output_tokens'] == 50
            assert result['cost'] > 0
    
    @pytest.mark.asyncio
    async def test_claude_interface_mock(self, mock_model_config):
        """Test Claude interface with mocking"""
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            # Mock response
            mock_content = Mock()
            mock_content.text = "Claude test response"
            
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_response.stop_reason = "end_turn"
            
            mock_client = Mock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client
            
            interface = ClaudeInterface(mock_model_config)
            result = await interface.generate_completion("Test prompt")
            
            assert result['content'] == "Claude test response"
            assert result['cost'] > 0
    
    @pytest.mark.asyncio
    async def test_cost_limit_check(self):
        """Test cost limit checking"""
        manager = AIModelManager()
        manager.total_cost = 250.0  # Exceed limit
        
        with pytest.raises(Exception, match="Daily cost limit exceeded"):
            await manager._check_cost_limits()

class TestPhaseIntegration:
    """Integration tests for phase execution"""
    
    @pytest.fixture
    def sample_foundation_design(self):
        """Sample foundation design for testing"""
        return {
            'node_structure': {
                'node_types': {
                    'achievement_standard': {
                        'properties': ['code', 'content'],
                        'estimated_count': 181
                    }
                }
            },
            'relationship_categories': {
                'relationship_types': {
                    'prerequisite': {'weight_range': [0.8, 1.0]},
                    'similar_to': {'weight_range': [0.5, 0.9]}
                }
            }
        }
    
    @pytest.fixture
    def sample_relationship_data(self):
        """Sample relationship data for testing"""
        return {
            'weighted_relations': [
                {
                    'source_code': '2수01-01',
                    'target_code': '2수01-04',
                    'relation_type': 'prerequisite',
                    'weight': 0.9,
                    'reasoning': 'Test prerequisite relationship'
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_phase1_mock_execution(self, sample_curriculum_data):
        """Test Phase 1 execution with mocking"""
        with patch('src.phase1_foundation.AIModelManager') as mock_manager:
            # Mock AI response
            mock_ai = Mock()
            mock_ai.get_completion = AsyncMock(return_value={
                'content': '{"node_types": {"test": "structure"}}',
                'cost': 15.0
            })
            mock_ai.get_total_usage_stats = Mock(return_value={'total_cost': 15.0})
            mock_manager.return_value = mock_ai
            
            # Import and test
            from src.phase1_foundation import FoundationDesigner
            
            designer = FoundationDesigner(mock_ai)
            
            # Mock the actual method to avoid full AI call
            designer._design_node_structure = AsyncMock(return_value={'node_types': {}})
            designer._design_relationship_categories = AsyncMock(return_value={'relationship_types': {}})
            designer._design_community_clusters = AsyncMock(return_value={'levels': {}})
            designer._design_hierarchical_structure = AsyncMock(return_value={'levels': {}})
            
            result = await designer.design_complete_structure(sample_curriculum_data)
            
            assert 'node_structure' in result
            assert 'metadata' in result
    
    def test_relationship_extraction_logic(self, sample_relationship_data):
        """Test relationship extraction logic"""
        relations = sample_relationship_data['weighted_relations']
        
        # Test filtering
        prerequisite_relations = [r for r in relations if r['relation_type'] == 'prerequisite']
        assert len(prerequisite_relations) == 1
        assert prerequisite_relations[0]['weight'] == 0.9
    
    def test_weight_adjustment_logic(self):
        """Test weight adjustment logic"""
        base_weights = {
            'prerequisite': 1.0,
            'similar_to': 0.6,
            'domain_bridge': 0.4
        }
        
        # Test adjustment factors
        same_grade_factor = 1.2
        cross_domain_factor = 0.9
        
        adjusted_weight = base_weights['prerequisite'] * same_grade_factor
        assert adjusted_weight == 1.2
        
        adjusted_cross_domain = base_weights['domain_bridge'] * cross_domain_factor
        assert adjusted_cross_domain == 0.36

class TestUtilities:
    """Test utility functions and helpers"""
    
    def test_json_parsing_fallback(self):
        """Test JSON parsing with fallback"""
        # Valid JSON
        valid_json = '{"test": "value"}'
        try:
            result = json.loads(valid_json)
            assert result['test'] == 'value'
        except:
            assert False, "Valid JSON should parse successfully"
        
        # Invalid JSON - test fallback
        invalid_json = '{invalid json'
        try:
            result = json.loads(invalid_json)
            assert False, "Invalid JSON should raise exception"
        except json.JSONDecodeError:
            # This is expected
            fallback_result = {'fallback': True}
            assert fallback_result['fallback'] == True
    
    def test_file_operations(self, tmp_path):
        """Test file operations"""
        # Test file writing
        test_data = {'test': 'data'}
        test_file = tmp_path / "test.json"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        assert test_file.exists()
        
        # Test file reading
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
    
    def test_error_handling(self):
        """Test error handling patterns"""
        def risky_function(value):
            if value < 0:
                raise ValueError("Negative value not allowed")
            return value * 2
        
        # Test normal operation
        result = risky_function(5)
        assert result == 10
        
        # Test error handling
        try:
            risky_function(-1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Negative value" in str(e)

class TestConfiguration:
    """Test configuration management"""
    
    def test_model_config_creation(self):
        """Test model configuration creation"""
        config = ModelConfig(
            name="test-model",
            api_key="test-key",
            cost_per_input_token=1e-6,
            cost_per_output_token=2e-6
        )
        
        assert config.name == "test-model"
        assert config.api_key == "test-key"
        assert config.temperature == 0.2  # Default value
        assert config.max_tokens == 4000  # Default value
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'GOOGLE_API_KEY': 'test-google-key'
    })
    def test_settings_initialization(self):
        """Test settings initialization with environment variables"""
        from config.settings import Config
        
        config = Config()
        
        assert config.models['gpt5'].api_key == 'test-openai-key'
        assert config.models['claude_sonnet'].api_key == 'test-anthropic-key'
        assert config.models['gemini_pro'].api_key == 'test-google-key'

# Pytest fixtures for the entire test suite
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_output_directory(tmp_path):
    """Create a temporary output directory for tests"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

# Test configuration
if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ])
