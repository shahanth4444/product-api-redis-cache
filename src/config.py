"""
Configuration management using Pydantic Settings.
Loads environment variables with validation and type safety.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_port: int = Field(default=8080, description="Port for the API server")
    
    # Redis Configuration
    redis_host: str = Field(default="redis", description="Redis server hostname")
    redis_port: int = Field(default=6379, description="Redis server port")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./products.db",
        description="Database connection URL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
