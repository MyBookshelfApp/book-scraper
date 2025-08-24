"""
Scraping job models for managing book scraping tasks
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, Enum):
    """Job type enumeration"""
    SINGLE_BOOK = "single_book"
    BATCH_SCRAPE = "batch_scrape"
    LIST_SCRAPE = "list_scrape"
    UPDATE_EXISTING = "update_existing"
    FULL_SYNC = "full_sync"


class ScrapingJob(BaseModel):
    """Represents a scraping job"""
    id: Optional[str] = Field(None, description="Unique job identifier")
    
    # Job configuration
    job_type: JobType = Field(..., description="Type of scraping job")
    source: str = Field(..., description="Source to scrape from")
    
    # Job parameters
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Job-specific parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Job priority (1=highest, 10=lowest)")
    
    # Status tracking
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Job progress percentage")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the job was created")
    started_at: Optional[datetime] = Field(None, description="When the job started running")
    completed_at: Optional[datetime] = Field(None, description="When the job completed")
    
    # Results and errors
    result_count: int = Field(default=0, description="Number of results produced")
    error_count: int = Field(default=0, description="Number of errors encountered")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    
    # Worker information
    worker_id: Optional[str] = Field(None, description="ID of the worker processing this job")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing jobs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional job metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 