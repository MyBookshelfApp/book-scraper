"""
Configuration management for the Book Scraper service
"""
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service configuration
    app_name: str = "book-scraper"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database configuration (abstracted for future flexibility)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_type: str = Field(default="postgresql", env="DATABASE_TYPE")
    
    # Redis configuration for task queue
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Scraping configuration
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    rate_limit_per_second: int = Field(default=10, env="RATE_LIMIT_PER_SECOND")
    
    # Retry configuration
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Kubernetes specific
    pod_name: Optional[str] = Field(default=None, env="POD_NAME")
    namespace: Optional[str] = Field(default=None, env="NAMESPACE")
    
    # Book sources configuration
    enabled_sources: List[str] = Field(
        default=["goodreads", "amazon", "google_books", "openlibrary"],
        env="ENABLED_SOURCES"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 