"""
Book data models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class BookSource(str, Enum):
    """Supported book sources"""
    GOODREADS = "goodreads"
    AMAZON = "amazon"
    GOOGLE_BOOKS = "google_books"
    OPENLIBRARY = "openlibrary"
    UNKNOWN = "unknown"


class BookFormat(str, Enum):
    """Book formats"""
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"
    UNKNOWN = "unknown"


class BookMetadata(BaseModel):
    """Metadata extracted from book sources"""
    title: str = Field(..., description="Book title")
    authors: List[str] = Field(default_factory=list, description="Book authors")
    isbn: Optional[str] = Field(None, description="ISBN (10 or 13)")
    isbn13: Optional[str] = Field(None, description="ISBN-13")
    isbn10: Optional[str] = Field(None, description="ISBN-10")
    
    # Publication details
    publisher: Optional[str] = Field(None, description="Publisher name")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    language: Optional[str] = Field(None, description="Book language")
    format: BookFormat = Field(BookFormat.UNKNOWN, description="Book format")
    
    # Content details
    pages: Optional[int] = Field(None, description="Number of pages")
    description: Optional[str] = Field(None, description="Book description")
    genres: List[str] = Field(default_factory=list, description="Book genres/categories")
    tags: List[str] = Field(default_factory=list, description="User tags")
    
    # Ratings and reviews
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    rating_count: Optional[int] = Field(None, ge=0, description="Number of ratings")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    
    # Media
    cover_image_url: Optional[HttpUrl] = Field(None, description="Cover image URL")
    cover_image_small: Optional[HttpUrl] = Field(None, description="Small cover image URL")
    
    # Additional metadata
    series: Optional[str] = Field(None, description="Series name")
    series_position: Optional[int] = Field(None, description="Position in series")
    awards: List[str] = Field(default_factory=list, description="Awards received")
    
    # Source-specific data
    source_id: Optional[str] = Field(None, description="ID from the source system")
    source_url: Optional[HttpUrl] = Field(None, description="URL to the book on the source")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional source-specific data")


class Book(BaseModel):
    """Complete book information"""
    id: Optional[str] = Field(None, description="Unique book identifier")
    
    # Core metadata
    metadata: BookMetadata
    
    # Source information
    primary_source: BookSource = Field(..., description="Primary source for this book")
    sources: List[BookSource] = Field(default_factory=list, description="All sources this book was found in")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this book was first created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When this book was last updated")
    last_scraped: Optional[datetime] = Field(None, description="When this book was last scraped")
    
    # Quality metrics
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the data quality")
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Completeness of available data")
    
    # Processing flags
    is_processed: bool = Field(default=False, description="Whether this book has been fully processed")
    needs_review: bool = Field(default=False, description="Whether this book needs manual review")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 