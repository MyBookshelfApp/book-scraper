"""
Data models for the Book Scraper service
"""
from .book import Book, BookMetadata, BookSource
from .scraping_job import ScrapingJob, JobStatus, JobType
from .scraping_result import ScrapingResult

__all__ = [
    "Book",
    "BookMetadata", 
    "BookSource",
    "ScrapingJob",
    "JobStatus",
    "JobType",
    "ScrapingResult"
] 