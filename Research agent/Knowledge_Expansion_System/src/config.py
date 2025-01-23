"""Configuration management for the Knowledge Expansion System."""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    
    # API Keys
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    
    # Database settings
    NEO4J_URI: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field("neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(..., env="NEO4J_PASSWORD")
    ELASTICSEARCH_URL: str = Field("http://localhost:9200", env="ELASTICSEARCH_URL")
    
    # Application settings
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(True, env="DEBUG")
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    
    # File storage settings
    MAX_UPLOAD_SIZE: str = Field("100MB", env="MAX_UPLOAD_SIZE")
    ALLOWED_FILE_TYPES: List[str] = Field(
        ["pdf", "txt", "mp3", "mp4", "wav", "jpg", "png", "html"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # LLM settings
    DEFAULT_MODEL: str = Field("gpt-4", env="DEFAULT_MODEL")
    MAX_TOKENS: int = Field(2000, env="MAX_TOKENS")
    TEMPERATURE: float = Field(0.7, env="TEMPERATURE")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True) 