from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Application settings
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite:////tmp/deepinsight.db"
    database_echo: bool = False
    
    # Security settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    max_login_attempts: int = 5
    
    # LLM settings
    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 4000
    llm_temperature: float = 0.1
    llm_timeout: int = 60
    
    # File upload settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_directory: str = "/tmp/documents"
    export_directory: str = "/tmp/exports"
    allowed_mime_types: list = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown"
    ]
    
    # Processing settings
    # Chunked ontology generation is now enabled by default for large documents (>8K chars)
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()