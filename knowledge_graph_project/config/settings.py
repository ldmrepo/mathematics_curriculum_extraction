"""
Configuration management for Knowledge Graph Construction Project
"""
import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class ModelConfig(BaseModel):
    """AI Model configuration"""
    name: str
    api_key: str
    max_tokens: int = 4000
    temperature: float = 0.2
    max_retries: int = 3
    cost_per_input_token: float
    cost_per_output_token: float

class DatabaseConfig(BaseModel):
    """Database configuration"""
    postgresql_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL"))
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI"))
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD"))

class ProcessingConfig(BaseModel):
    """Processing configuration"""
    batch_size: int = Field(default_factory=lambda: int(os.getenv("BATCH_SIZE", 10)))
    max_concurrent: int = Field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", 5)))
    max_daily_cost: float = Field(default_factory=lambda: float(os.getenv("MAX_DAILY_COST", 200.0)))
    cost_alert_threshold: float = Field(default_factory=lambda: float(os.getenv("COST_ALERT_THRESHOLD", 150.0)))

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.models = self._get_model_configs()
        self.database = DatabaseConfig()
        self.processing = ProcessingConfig()
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/knowledge_graph.log")
    
    def _get_model_configs(self) -> Dict[str, ModelConfig]:
        """Get AI model configurations"""
        return {
            "gemini_pro": ModelConfig(
                name="gemini-2.5-pro",
                api_key=os.getenv("GOOGLE_API_KEY"),
                max_tokens=4000,
                temperature=0.2,
                cost_per_input_token=1.25e-6,  # $1.25 per 1M tokens
                cost_per_output_token=10e-6    # $10 per 1M tokens
            ),
            "gpt5": ModelConfig(
                name="gpt-5",
                api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=4000,
                temperature=0.1,
                cost_per_input_token=1.25e-6,  # $1.25 per 1M tokens
                cost_per_output_token=10e-6    # $10 per 1M tokens
            ),
            "claude_sonnet": ModelConfig(
                name="claude-sonnet-4-20250514",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                max_tokens=4000,
                temperature=0.2,
                cost_per_input_token=3e-6,     # $3 per 1M tokens
                cost_per_output_token=15e-6    # $15 per 1M tokens
            ),
            "claude_opus": ModelConfig(
                name="claude-opus-4-1-20250514",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                max_tokens=8000,
                temperature=0.2,
                cost_per_input_token=15e-6,    # $15 per 1M tokens
                cost_per_output_token=75e-6    # $75 per 1M tokens
            )
        }

# Global configuration instance
config = Config()
