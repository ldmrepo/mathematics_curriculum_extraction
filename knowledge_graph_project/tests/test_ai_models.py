"""
Unit tests for ai_models.py module
Tests AI model interfaces and manager
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_models import (
    AIModelInterface, 
    OpenAIInterface, 
    ClaudeInterface, 
    GeminiInterface,
    AIModelManager
)


class TestAIModelInterface:
    """Test AIModelInterface base class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock model configuration"""
        config = Mock()
        config.name = "test-model"
        config.api_key = "test-key"
        config.temperature = 0.7
        config.max_tokens = 1000
        config.cost_per_input_token = 0.00001
        config.cost_per_output_token = 0.00002
        return config
    
    @pytest.fixture
    def concrete_model(self, mock_config):
        """Create concrete implementation for testing"""
        class ConcreteModel(AIModelInterface):
            async def generate_completion(self, prompt: str, **kwargs):
                return {"content": "test response"}
        
        return ConcreteModel(mock_config)
    
    def test_init(self, concrete_model, mock_config):
        """Test AIModelInterface initialization"""
        assert concrete_model.config == mock_config
        assert concrete_model.total_cost == 0.0
        assert concrete_model.token_usage == {'input': 0, 'output': 0}
    
    def test_calculate_cost(self, concrete_model):
        """Test cost calculation"""
        cost = concrete_model.calculate_cost(100, 50)
        
        # Cost = 100 * 0.00001 + 50 * 0.00002 = 0.001 + 0.001 = 0.002
        assert cost == 0.002
        assert concrete_model.total_cost == 0.002
        assert concrete_model.token_usage['input'] == 100
        assert concrete_model.token_usage['output'] == 50
        
        # Second calculation should accumulate
        cost2 = concrete_model.calculate_cost(200, 100)
        assert cost2 == 0.004
        assert concrete_model.total_cost == 0.006
        assert concrete_model.token_usage['input'] == 300
        assert concrete_model.token_usage['output'] == 150
    
    def test_get_usage_stats(self, concrete_model):
        """Test usage statistics retrieval"""
        concrete_model.calculate_cost(100, 50)
        
        stats = concrete_model.get_usage_stats()
        
        assert stats['total_cost'] == 0.002
        assert stats['input_tokens'] == 100
        assert stats['output_tokens'] == 50
        assert stats['model_name'] == 'test-model'


class TestOpenAIInterface:
    """Test OpenAIInterface class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock OpenAI configuration"""
        config = Mock()
        config.name = "gpt-5"
        config.api_key = "test-openai-key"
        config.temperature = 0.7
        config.max_tokens = 1000
        config.cost_per_input_token = 0.00001
        config.cost_per_output_token = 0.00002
        return config
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def openai_interface(self, mock_config, mock_openai_client):
        """Create OpenAIInterface with mocked client"""
        with patch('src.ai_models.openai.AsyncOpenAI', return_value=mock_openai_client):
            interface = OpenAIInterface(mock_config)
            interface.client = mock_openai_client
            return interface
    
    @pytest.mark.asyncio
    async def test_generate_completion_success(self, openai_interface, mock_openai_client):
        """Test successful completion generation"""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response content"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Generate completion
        result = await openai_interface.generate_completion("Test prompt")
        
        # Verify API call
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a Korean mathematics curriculum expert."},
                {"role": "user", "content": "Test prompt"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Verify result
        assert result['content'] == "Test response content"
        assert result['model'] == "gpt-5"
        assert result['cost'] == 0.002  # 100 * 0.00001 + 50 * 0.00002
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 50
        assert result['finish_reason'] == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_completion_with_kwargs(self, openai_interface, mock_openai_client):
        """Test completion with additional parameters"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Generate with additional parameters
        await openai_interface.generate_completion(
            "Test prompt",
            top_p=0.9,
            frequency_penalty=0.5
        )
        
        # Verify additional parameters were passed
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs.get('top_p') == 0.9
        assert call_kwargs.get('frequency_penalty') == 0.5
    
    @pytest.mark.asyncio
    async def test_generate_completion_error(self, openai_interface, mock_openai_client):
        """Test error handling in completion generation"""
        from tenacity import RetryError
        
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        # The retry decorator will raise RetryError after failures
        with pytest.raises(RetryError):
            await openai_interface.generate_completion("Test prompt")
    
    @pytest.mark.asyncio
    async def test_create_batch_job(self, openai_interface, mock_openai_client):
        """Test batch job creation"""
        # Mock file and batch responses
        mock_file_response = Mock(id="file-123")
        mock_batch_response = Mock(id="batch-456")
        
        mock_openai_client.files.create = AsyncMock(return_value=mock_file_response)
        mock_openai_client.batches.create = AsyncMock(return_value=mock_batch_response)
        
        # Create batch job
        requests = [
            {"prompt": "test1"},
            {"prompt": "test2"}
        ]
        
        batch_id = await openai_interface.create_batch_job(requests)
        
        # Verify file was created
        mock_openai_client.files.create.assert_called_once()
        
        # Verify batch was created
        mock_openai_client.batches.create.assert_called_once_with(
            input_file_id="file-123",
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        assert batch_id == "batch-456"


class TestClaudeInterface:
    """Test ClaudeInterface class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock Claude configuration"""
        config = Mock()
        config.name = "claude-sonnet-4"
        config.api_key = "test-anthropic-key"
        config.temperature = 0.7
        config.max_tokens = 1000
        config.cost_per_input_token = 0.00001
        config.cost_per_output_token = 0.00002
        return config
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def claude_interface(self, mock_config, mock_claude_client):
        """Create ClaudeInterface with mocked client"""
        with patch('src.ai_models.anthropic.AsyncAnthropic', return_value=mock_claude_client):
            interface = ClaudeInterface(mock_config)
            interface.client = mock_claude_client
            return interface
    
    @pytest.mark.asyncio
    async def test_generate_completion_success(self, claude_interface, mock_claude_client):
        """Test successful completion generation"""
        # Mock response
        mock_content = Mock()
        mock_content.text = "Claude response content"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        
        mock_claude_client.messages.create = AsyncMock(return_value=mock_response)
        
        # Generate completion
        result = await claude_interface.generate_completion("Test prompt")
        
        # Verify API call
        mock_claude_client.messages.create.assert_called_once_with(
            model="claude-sonnet-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Verify result
        assert result['content'] == "Claude response content"
        assert result['model'] == "claude-sonnet-4"
        assert result['stop_reason'] == "end_turn"
        assert 'cost' in result
        assert 'input_tokens' in result
        assert 'output_tokens' in result
    
    @pytest.mark.asyncio
    async def test_generate_completion_with_thinking_budget(self, claude_interface, mock_claude_client):
        """Test completion with thinking budget for Sonnet"""
        mock_content = Mock()
        mock_content.text = "Response with thinking"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        
        mock_claude_client.messages.create = AsyncMock(return_value=mock_response)
        
        # Generate with thinking budget
        await claude_interface.generate_completion(
            "Test prompt",
            thinking_budget=5000
        )
        
        # Verify thinking_budget was passed
        call_kwargs = mock_claude_client.messages.create.call_args[1]
        assert call_kwargs['thinking_budget'] == 5000
    
    @pytest.mark.asyncio
    async def test_generate_completion_opus_no_thinking(self, mock_claude_client):
        """Test that Opus model doesn't use thinking budget"""
        # Create Opus config
        config = Mock()
        config.name = "claude-opus-4.1"
        config.api_key = "test-key"
        config.temperature = 0.7
        config.max_tokens = 1000
        config.cost_per_input_token = 0.00001
        config.cost_per_output_token = 0.00002
        
        with patch('src.ai_models.anthropic.AsyncAnthropic', return_value=mock_claude_client):
            interface = ClaudeInterface(config)
            interface.client = mock_claude_client
        
        mock_content = Mock()
        mock_content.text = "Opus response"
        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        
        mock_claude_client.messages.create = AsyncMock(return_value=mock_response)
        
        # Generate with thinking budget (should be ignored for Opus)
        await interface.generate_completion(
            "Test prompt",
            thinking_budget=5000
        )
        
        # Verify thinking_budget was NOT passed
        call_kwargs = mock_claude_client.messages.create.call_args[1]
        assert 'thinking_budget' not in call_kwargs
    
    @pytest.mark.asyncio
    async def test_generate_completion_error(self, claude_interface, mock_claude_client):
        """Test error handling in completion generation"""
        from tenacity import RetryError
        
        mock_claude_client.messages.create = AsyncMock(
            side_effect=Exception("Claude API Error")
        )
        
        with pytest.raises(RetryError):
            await claude_interface.generate_completion("Test prompt")


class TestGeminiInterface:
    """Test GeminiInterface class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock Gemini configuration"""
        config = Mock()
        config.name = "gemini-2.5-pro"
        config.api_key = "test-google-key"
        config.temperature = 0.7
        config.max_tokens = 1000
        config.cost_per_input_token = 0.00001
        config.cost_per_output_token = 0.00002
        return config
    
    @pytest.fixture
    def mock_gemini_model(self):
        """Create mock Gemini model"""
        model = Mock()
        model.generate_content_async = AsyncMock()
        return model
    
    @pytest.fixture
    def gemini_interface(self, mock_config, mock_gemini_model):
        """Create GeminiInterface with mocked model"""
        with patch('src.ai_models.genai.configure'):
            with patch('src.ai_models.genai.GenerativeModel', return_value=mock_gemini_model):
                interface = GeminiInterface(mock_config)
                interface.model = mock_gemini_model
                return interface
    
    @pytest.mark.asyncio
    async def test_generate_completion_success(self, gemini_interface, mock_gemini_model):
        """Test successful completion generation"""
        # Mock response
        mock_candidate = Mock()
        mock_candidate.finish_reason.name = "STOP"
        mock_response = Mock()
        mock_response.text = "Gemini response content"
        mock_response.candidates = [mock_candidate]
        
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        # Generate completion
        result = await gemini_interface.generate_completion("Test prompt")
        
        # Verify API call
        mock_gemini_model.generate_content_async.assert_called_once()
        call_args = mock_gemini_model.generate_content_async.call_args
        assert call_args[0][0] == "Test prompt"
        
        # Verify result
        assert result['content'] == "Gemini response content"
        assert result['model'] == "gemini-2.5-pro"
        assert result['finish_reason'] == "STOP"
        assert 'cost' in result
        assert 'input_tokens' in result
        assert 'output_tokens' in result
    
    @pytest.mark.asyncio
    async def test_generate_completion_with_kwargs(self, gemini_interface, mock_gemini_model):
        """Test completion with additional parameters"""
        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = []  # Test empty candidates
        
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        # Generate with additional parameters
        await gemini_interface.generate_completion(
            "Test prompt",
            candidate_count=2,
            stop_sequences=["END"]
        )
        
        # Verify generation config was created with additional params
        mock_gemini_model.generate_content_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_completion_error(self, gemini_interface, mock_gemini_model):
        """Test error handling in completion generation"""
        from tenacity import RetryError
        
        mock_gemini_model.generate_content_async = AsyncMock(
            side_effect=Exception("Gemini API Error")
        )
        
        with pytest.raises(RetryError):
            await gemini_interface.generate_completion("Test prompt")


class TestAIModelManager:
    """Test AIModelManager class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock()
        
        # Mock models config
        config.models = {
            'gemini_pro': Mock(
                name='gemini-2.5-pro',
                api_key='test-google-key',
                temperature=0.7,
                max_tokens=1000,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00002
            ),
            'gpt5': Mock(
                name='gpt-5',
                api_key='test-openai-key',
                temperature=0.7,
                max_tokens=1000,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00002
            ),
            'claude_sonnet': Mock(
                name='claude-sonnet-4',
                api_key='test-anthropic-key',
                temperature=0.7,
                max_tokens=1000,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00002
            ),
            'claude_opus': Mock(
                name='claude-opus-4.1',
                api_key='test-anthropic-key',
                temperature=0.7,
                max_tokens=1000,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00002
            )
        }
        
        # Mock processing config
        config.processing = Mock(
            max_daily_cost=100.0,
            cost_alert_threshold=50.0
        )
        
        return config
    
    @pytest.fixture
    def manager(self, mock_config):
        """Create AIModelManager with mocked config"""
        with patch('src.ai_models.config', mock_config):
            with patch('src.ai_models.genai.configure'):
                with patch('src.ai_models.genai.GenerativeModel'):
                    with patch('src.ai_models.openai.AsyncOpenAI'):
                        with patch('src.ai_models.anthropic.AsyncAnthropic'):
                            manager = AIModelManager()
                            
                            # Mock the models
                            for name in manager.models:
                                manager.models[name].generate_completion = AsyncMock(
                                    return_value={
                                        'content': f'Response from {name}',
                                        'cost': 0.001,
                                        'input_tokens': 100,
                                        'output_tokens': 50,
                                        'model': name
                                    }
                                )
                            
                            return manager
    
    @pytest.mark.asyncio
    async def test_get_completion_success(self, manager):
        """Test successful completion from a model"""
        result = await manager.get_completion('gpt5', 'Test prompt')
        
        assert result['content'] == 'Response from gpt5'
        assert result['cost'] == 0.001
        assert manager.total_cost == 0.001
    
    @pytest.mark.asyncio
    async def test_get_completion_unknown_model(self, manager):
        """Test error for unknown model"""
        with pytest.raises(ValueError, match="Unknown model: unknown_model"):
            await manager.get_completion('unknown_model', 'Test prompt')
    
    @pytest.mark.asyncio
    async def test_cost_alert_threshold(self, manager, mock_config):
        """Test cost alert when threshold is reached"""
        # Test the _check_cost_limits method directly
        manager.total_cost = 50.0  # At threshold
        
        with patch('src.ai_models.config', mock_config):
            with patch('src.ai_models.logger.warning') as mock_warning:
                await manager._check_cost_limits()
                mock_warning.assert_called_once()
                assert "Cost alert" in mock_warning.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cost_limit_exceeded(self, manager, mock_config):
        """Test error when daily cost limit is exceeded"""
        # Test the _check_cost_limits method directly
        manager.total_cost = 100.0  # At limit
        
        with patch('src.ai_models.config', mock_config):
            with pytest.raises(Exception, match="Daily cost limit exceeded"):
                await manager._check_cost_limits()
    
    @pytest.mark.asyncio
    async def test_get_total_usage_stats(self, manager):
        """Test getting usage statistics"""
        # Generate some completions
        await manager.get_completion('gpt5', 'Test 1')
        await manager.get_completion('claude_sonnet', 'Test 2')
        
        stats = manager.get_total_usage_stats()
        
        assert stats['total_cost'] == 0.002  # 2 completions at 0.001 each
        assert 'models' in stats
        assert 'gpt5' in stats['models']
        assert 'claude_sonnet' in stats['models']
    
    @pytest.mark.asyncio
    async def test_multiple_models_integration(self, manager):
        """Test using multiple models in sequence"""
        models_to_test = ['gemini_pro', 'gpt5', 'claude_sonnet', 'claude_opus']
        
        for model_name in models_to_test:
            result = await manager.get_completion(model_name, f'Test for {model_name}')
            assert result['content'] == f'Response from {model_name}'
        
        # Check total cost accumulated
        assert manager.total_cost == 0.004  # 4 completions at 0.001 each


if __name__ == "__main__":
    pytest.main([__file__, "-v"])