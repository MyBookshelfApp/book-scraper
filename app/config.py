"""
Configuration management for the Book Scraper service
"""
from typing import Optional, List
from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    """Application settings loaded from environment variables"""
    
    # Service configuration
    app_name: str = "book-scraper"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)
    
    # Server configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    
    # Database configuration (abstracted for future flexibility)
    database_url: Optional[str] = Field(default=None)
    database_type: str = Field(default="postgresql")
    
    # Redis configuration for task queue
    redis_url: str = Field(default="redis://localhost:6379")
    
    # Scraping configuration
    max_concurrent_requests: int = Field(default=100)
    request_timeout: int = Field(default=30)
    rate_limit_per_second: int = Field(default=10)
    
    # Retry configuration
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
    
    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Kubernetes specific
    pod_name: Optional[str] = Field(default=None)
    namespace: Optional[str] = Field(default=None)
    
    # Book sources configuration
    enabled_sources: List[str] = Field(
        default=["goodreads", "amazon", "google_books", "openlibrary"]
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables"""
        # Service configuration
        if os.getenv('DEBUG'):
            self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Server configuration
        if os.getenv('HOST'):
            self.host = os.getenv('HOST')
        if os.getenv('PORT'):
            self.port = int(os.getenv('PORT'))
        if os.getenv('WORKERS'):
            self.workers = int(os.getenv('WORKERS'))
        
        # Database configuration
        if os.getenv('DATABASE_URL'):
            self.database_url = os.getenv('DATABASE_URL')
        if os.getenv('DATABASE_TYPE'):
            self.database_type = os.getenv('DATABASE_TYPE')
        
        # Redis configuration
        if os.getenv('REDIS_URL'):
            self.redis_url = os.getenv('REDIS_URL')
        
        # Scraping configuration
        if os.getenv('MAX_CONCURRENT_REQUESTS'):
            self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS'))
        if os.getenv('REQUEST_TIMEOUT'):
            self.request_timeout = int(os.getenv('REQUEST_TIMEOUT'))
        if os.getenv('RATE_LIMIT_PER_SECOND'):
            self.rate_limit_per_second = int(os.getenv('RATE_LIMIT_PER_SECOND'))
        
        # Retry configuration
        if os.getenv('MAX_RETRIES'):
            self.max_retries = int(os.getenv('MAX_RETRIES'))
        if os.getenv('RETRY_DELAY'):
            self.retry_delay = float(os.getenv('RETRY_DELAY'))
        
        # Monitoring
        if os.getenv('ENABLE_METRICS'):
            self.enable_metrics = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        if os.getenv('METRICS_PORT'):
            self.metrics_port = int(os.getenv('METRICS_PORT'))
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            self.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FORMAT'):
            self.log_format = os.getenv('LOG_FORMAT')
        
        # Kubernetes specific
        if os.getenv('POD_NAME'):
            self.pod_name = os.getenv('POD_NAME')
        if os.getenv('NAMESPACE'):
            self.namespace = os.getenv('NAMESPACE')
        
        # Book sources configuration
        if os.getenv('ENABLED_SOURCES'):
            self.enabled_sources = os.getenv('ENABLED_SOURCES').split(',')


# Global settings instance
settings = Settings() 