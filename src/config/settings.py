# src/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600  # 1 hour default
    
    # Model Configuration
    MODEL_NAME: str = "gpt-4"
    TEMPERATURE: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Settings initialized")