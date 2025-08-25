"""
Book models for representing book data and metadata
"""
from datetime import datetime, timezone
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


class BookMetadata(BaseModel):
    """Metadata for a book"""
    title: str = Field(..., description="Book title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    isbn: Optional[str] = Field(None, description="ISBN-10")
    isbn13: Optional[str] = Field(None, description="ISBN-13")
    isbn10: Optional[str] = Field(None, description="ISBN-10 (alias for isbn)")
    publisher: Optional[str] = Field(None, description="Publisher name")
    publication_date: Optional[str] = Field(None, description="Publication date")
    description: Optional[str] = Field(None, description="Book description")
    language: Optional[str] = Field(None, description="Book language")
    format: Optional[str] = Field(None, description="Book format (hardcover, paperback, ebook, etc.)")
    pages: Optional[int] = Field(None, description="Number of pages")
    dimensions: Optional[str] = Field(None, description="Physical dimensions")
    weight: Optional[str] = Field(None, description="Physical weight")
    
    # Rating and review information
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average rating (0.0 to 5.0)")
    rating_count: Optional[int] = Field(None, ge=0, description="Number of ratings")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    
    # Cover and media
    cover_image_url: Optional[HttpUrl] = Field(None, description="URL to cover image")
    cover_image_data: Optional[bytes] = Field(None, description="Cover image binary data")
    
    # Categorization
    genres: List[str] = Field(default_factory=list, description="Book genres/categories")
    tags: List[str] = Field(default_factory=list, description="Book tags")
    series: Optional[str] = Field(None, description="Series name if part of a series")
    series_position: Optional[int] = Field(None, description="Position in series")
    
    # Source-specific information
    source_id: Optional[str] = Field(None, description="ID from the source system")
    source_url: Optional[HttpUrl] = Field(None, description="URL to the source page")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw metadata from source")
    
    # Additional fields
    price: Optional[float] = Field(None, ge=0.0, description="Book price")
    currency: Optional[str] = Field(None, description="Price currency")
    availability: Optional[str] = Field(None, description="Availability status")
    
    class Config:
        json_encoders = {
            bytes: lambda v: v.hex() if v else None
        }


class Book(BaseModel):
    """Represents a book with metadata and sources"""
    id: Optional[str] = Field(None, description="Unique book identifier")
    
    # Core book data
    metadata: BookMetadata = Field(..., description="Book metadata")
    
    # Source information
    primary_source: BookSource = Field(..., description="Primary source for this book")
    sources: List[BookSource] = Field(default_factory=list, description="All sources this book was found in")
    
    # Reading progress (if applicable)
    is_owned: bool = Field(False, description="Whether the user owns this book")
    reading_status: Optional[str] = Field(None, description="Current reading status")
    reading_progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Reading progress (0.0 to 1.0)")
    current_page: Optional[int] = Field(None, ge=0, description="Current page number")
    
    # Collection information
    collections: List[str] = Field(default_factory=list, description="Collections this book belongs to")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this book was first created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this book was last updated")
    last_scraped_at: Optional[datetime] = Field(None, description="When this book was last scraped")
    
    # Quality metrics
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in the data quality")
    data_completeness: float = Field(0.0, ge=0.0, le=1.0, description="Completeness of available data")
    
    # Additional metadata
    notes: Optional[str] = Field(None, description="User notes about this book")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom user-defined fields")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 