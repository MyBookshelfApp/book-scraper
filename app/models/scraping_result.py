"""
Scraping result models for tracking scraping outcomes
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .book import Book
from .scraping_job import ScrapingJob


class ResultStatus(str, Enum):
    """Result status enumeration"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScrapingResult(BaseModel):
    """Represents the result of a scraping operation"""
    id: Optional[str] = Field(None, description="Unique result identifier")
    
    # Associated entities
    job_id: str = Field(..., description="ID of the scraping job that produced this result")
    source: str = Field(..., description="Source that was scraped")
    
    # Result data
    status: ResultStatus = Field(..., description="Status of the scraping result")
    book: Optional[Book] = Field(None, description="Scraped book data if successful")
    
    # Performance metrics
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    data_size_bytes: Optional[int] = Field(None, description="Size of scraped data in bytes")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if scraping failed")
    error_code: Optional[str] = Field(None, description="Error code if scraping failed")
    
    # Metadata
    url_scraped: Optional[str] = Field(None, description="URL that was scraped")
    user_agent: Optional[str] = Field(None, description="User agent used for scraping")
    ip_address: Optional[str] = Field(None, description="IP address used for scraping")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this result was created")
    processed_at: Optional[datetime] = Field(None, description="When this result was processed")
    
    # Quality metrics
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the result quality")
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Completeness of scraped data")
    
    # Additional data
    raw_html: Optional[str] = Field(None, description="Raw HTML content (for debugging)")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Raw extracted data before processing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 