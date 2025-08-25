"""
Scraping job models for managing scraping operations
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

from .book import BookSource


class JobType(str, Enum):
    """Job type enumeration"""
    SINGLE = "single"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ScrapingJob(BaseModel):
    """Represents a scraping job"""
    id: Optional[str] = Field(None, description="Unique job identifier")
    
    # Job configuration
    job_type: JobType = Field(..., description="Type of scraping job")
    source: BookSource = Field(..., description="Source to scrape from")
    urls: List[str] = Field(..., description="URLs to scrape")
    
    # Job settings
    priority: int = Field(5, ge=1, le=10, description="Job priority (1=highest, 10=lowest)")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retry attempts")
    timeout_seconds: int = Field(30, ge=5, le=300, description="Request timeout in seconds")
    
    # Job state
    status: JobStatus = Field(JobStatus.PENDING, description="Current job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Job progress (0.0 to 1.0)")
    
    # Results
    completed_count: int = Field(0, ge=0, description="Number of successfully completed tasks")
    failed_count: int = Field(0, ge=0, description="Number of failed tasks")
    total_count: int = Field(0, ge=0, description="Total number of tasks")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional job metadata")
    tags: List[str] = Field(default_factory=list, description="Job tags for organization")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the job was created")
    started_at: Optional[datetime] = Field(None, description="When the job started processing")
    completed_at: Optional[datetime] = Field(None, description="When the job completed")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the job was last updated")
    
    # Error tracking
    last_error: Optional[str] = Field(None, description="Last error message")
    error_count: int = Field(0, ge=0, description="Number of errors encountered")
    
    # Performance metrics
    total_duration_seconds: Optional[float] = Field(None, description="Total job duration in seconds")
    average_response_time_ms: Optional[float] = Field(None, description="Average response time per request")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 