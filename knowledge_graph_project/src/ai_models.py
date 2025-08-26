"""
AI Model interfaces for different providers
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import openai
import anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from config.settings import config

class AIModelInterface(ABC):
    """Abstract base class for AI model interfaces"""
    
    def __init__(self, model_config):
        self.config = model_config
        self.total_cost = 0.0
        self.token_usage = {'input': 0, 'output': 0}
    
    @abstractmethod
    async def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion from the model"""
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        cost = (input_tokens * self.config.cost_per_input_token + 
                output_tokens * self.config.cost_per_output_token)
        self.total_cost += cost
        self.token_usage['input'] += input_tokens
        self.token_usage['output'] += output_tokens
        return cost
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'total_cost': self.total_cost,
            'input_tokens': self.token_usage['input'],
            'output_tokens': self.token_usage['output'],
            'model_name': self.config.name
        }

class OpenAIInterface(AIModelInterface):
    """OpenAI GPT models interface"""
    
    def __init__(self, model_config):
        super().__init__(model_config)
        self.client = openai.AsyncOpenAI(api_key=model_config.api_key)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using OpenAI API"""
        try:
            # Extract max_tokens from kwargs if provided, otherwise use default
            max_tokens = kwargs.pop('max_tokens', self.config.max_tokens)
            
            # Remove unsupported parameters for all OpenAI models
            kwargs.pop('reasoning_effort', None)
            kwargs.pop('verbosity', None)
            kwargs.pop('thinking_budget', None)
            
            # For GPT-5, use max_completion_tokens only
            if 'gpt-5' in self.config.name.lower():
                # GPT-5 uses max_completion_tokens instead of max_tokens
                kwargs.pop('temperature', None)  # GPT-5 doesn't support temperature
                
                response = await self.client.chat.completions.create(
                    model=self.config.name,
                    messages=[
                        {"role": "system", "content": "You are a Korean mathematics curriculum expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=max_tokens,  # GPT-5 uses this parameter
                    **kwargs
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.config.name,
                    messages=[
                        {"role": "system", "content": "You are a Korean mathematics curriculum expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=max_tokens,  # Other models use this
                    **kwargs
                )
            
            # Calculate cost
            usage = response.usage
            cost = self.calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            
            result = {
                'content': response.choices[0].message.content,
                'model': self.config.name,
                'cost': cost,
                'input_tokens': usage.prompt_tokens,
                'output_tokens': usage.completion_tokens,
                'finish_reason': response.choices[0].finish_reason
            }
            
            logger.info(f"OpenAI completion - Cost: ${cost:.4f}, Tokens: {usage.prompt_tokens}+{usage.completion_tokens}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def create_batch_job(self, requests: List[Dict]) -> str:
        """Create batch job for cost optimization"""
        try:
            # Create JSONL file for batch
            batch_input = "\n".join([json.dumps(req) for req in requests])
            
            # Upload file
            file_response = await self.client.files.create(
                file=batch_input.encode(),
                purpose="batch"
            )
            
            # Create batch job
            batch_response = await self.client.batches.create(
                input_file_id=file_response.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            
            logger.info(f"Created batch job: {batch_response.id}")
            return batch_response.id
            
        except Exception as e:
            logger.error(f"Failed to create batch job: {e}")
            raise

class ClaudeInterface(AIModelInterface):
    """Anthropic Claude models interface"""
    
    def __init__(self, model_config):
        super().__init__(model_config)
        self.client = anthropic.AsyncAnthropic(api_key=model_config.api_key)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using Claude API"""
        try:
            # Extract max_tokens from kwargs if provided, otherwise use default
            max_tokens = kwargs.pop('max_tokens', self.config.max_tokens)
            # Remove unsupported parameters
            kwargs.pop('thinking_budget', None)
            
            params = {
                "model": self.config.name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            response = await self.client.messages.create(**params)
            
            # Calculate cost (approximate token counting)
            input_tokens = len(prompt.split()) * 1.3  # Rough estimation
            output_tokens = len(response.content[0].text.split()) * 1.3
            cost = self.calculate_cost(int(input_tokens), int(output_tokens))
            
            result = {
                'content': response.content[0].text,
                'model': self.config.name,
                'cost': cost,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens),
                'stop_reason': response.stop_reason
            }
            
            logger.info(f"Claude completion - Cost: ${cost:.4f}, Tokens: ~{int(input_tokens)}+{int(output_tokens)}")
            return result
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

class GeminiInterface(AIModelInterface):
    """Google Gemini models interface"""
    
    def __init__(self, model_config):
        super().__init__(model_config)
        genai.configure(api_key=model_config.api_key)
        self.model = genai.GenerativeModel(model_config.name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using Gemini API"""
        try:
            # Extract max_tokens from kwargs if provided, otherwise use default
            max_tokens = kwargs.pop('max_tokens', self.config.max_tokens)
            # For Gemini, also check for max_output_tokens
            max_output_tokens = kwargs.pop('max_output_tokens', max_tokens)
            
            # Debug logging
            logger.debug(f"Gemini max_output_tokens: {max_output_tokens}")
            logger.debug(f"Additional kwargs: {kwargs}")
            
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=max_output_tokens,
                **kwargs
            )
            
            logger.info(f"Gemini generation_config: max_output_tokens={generation_config.max_output_tokens}, "
                       f"temperature={generation_config.temperature}")
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            # Calculate cost (approximate token counting)
            input_tokens = len(prompt.split()) * 1.3  # Rough estimation
            output_tokens = len(response.text.split()) * 1.3
            cost = self.calculate_cost(int(input_tokens), int(output_tokens))
            
            finish_reason = response.candidates[0].finish_reason.name if response.candidates else 'STOP'
            
            result = {
                'content': response.text,
                'model': self.config.name,
                'cost': cost,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens),
                'finish_reason': finish_reason
            }
            
            # Check for truncation
            if finish_reason in ['MAX_TOKENS', 'LENGTH']:
                logger.warning(f"Gemini response may be truncated! Finish reason: {finish_reason}, "
                             f"Max tokens: {self.config.max_tokens}, Output tokens: ~{int(output_tokens)}")
            
            logger.info(f"Gemini completion - Cost: ${cost:.4f}, Tokens: ~{int(input_tokens)}+{int(output_tokens)}, "
                       f"Finish: {finish_reason}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

class AIModelManager:
    """Manages multiple AI model interfaces"""
    
    def __init__(self):
        self.models = {
            'gpt4o': OpenAIInterface(config.models['gpt4o']),  # Best performance
            'gpt4_turbo': OpenAIInterface(config.models['gpt4_turbo']),  # Most capable
            'gemini_pro': GeminiInterface(config.models['gemini_pro']),
            'gpt5': OpenAIInterface(config.models['gpt5']),  # GPT-5 (experimental)
            'claude_sonnet': ClaudeInterface(config.models['claude_sonnet']),
            'claude_opus': ClaudeInterface(config.models['claude_opus'])
        }
        self.total_cost = 0.0
    
    async def get_completion(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Get completion from specified model"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Check cost limits
        await self._check_cost_limits()
        
        model = self.models[model_name]
        result = await model.generate_completion(prompt, **kwargs)
        
        self.total_cost += result['cost']
        return result
    
    async def _check_cost_limits(self):
        """Check if cost limits are exceeded"""
        if self.total_cost >= config.processing.max_daily_cost:
            raise Exception(f"Daily cost limit exceeded: ${self.total_cost:.2f}")
        
        if self.total_cost >= config.processing.cost_alert_threshold:
            logger.warning(f"Cost alert: ${self.total_cost:.2f} / ${config.processing.max_daily_cost:.2f}")
    
    def get_total_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all models"""
        stats = {
            'total_cost': self.total_cost,
            'models': {}
        }
        
        for name, model in self.models.items():
            stats['models'][name] = model.get_usage_stats()
        
        return stats
