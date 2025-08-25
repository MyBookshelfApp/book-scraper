"""
Core scraping engine for high-performance book scraping
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Coroutine
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

from ..config import settings
from ..models.book import Book, BookMetadata, BookSource
from ..models.scraping_result import ScrapingResult, ResultStatus
from .http_client import HTTPClient
from .rate_limiter import GlobalRateLimiter
from .html_parser import HTMLParser


@dataclass
class ScrapingTask:
    """Represents a single scraping task"""
    url: str
    source: BookSource
    priority: int = 5
    metadata: Dict[str, Any] = None
    callback: Optional[Callable[[ScrapingResult], Coroutine[Any, Any, None]]] = None


class ScraperEngine:
    """High-performance book scraping engine with async processing"""
    
    def __init__(self):
        self.rate_limiter = GlobalRateLimiter()
        self.http_client: Optional[HTTPClient] = None
        self.executor = ThreadPoolExecutor(max_workers=settings.workers)
        
        # Task management
        self.pending_tasks: List[ScrapingTask] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[ScrapingResult] = []
        self.failed_tasks: List[ScrapingResult] = []
        
        # Performance metrics
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
    
    async def __aenter__(self):
        """Initialize the scraper engine"""
        self.http_client = HTTPClient()
        await self.http_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the scraper engine"""
        if self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)
        
        # Cancel running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
    
    async def add_task(self, task: ScrapingTask) -> str:
        """Add a scraping task to the queue"""
        task_id = f"{task.source}_{int(time.time() * 1000)}"
        
        # Add to pending tasks with priority sorting
        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda t: t.priority)
        
        self.logger.info(f"Added task {task_id} for {task.url} with priority {task.priority}")
        return task_id
    
    async def add_batch_tasks(self, tasks: List[ScrapingTask]) -> List[str]:
        """Add multiple scraping tasks"""
        task_ids = []
        for task in tasks:
            task_id = await self.add_task(task)
            task_ids.append(task_id)
        return task_ids
    
    async def start_processing(self, max_tasks: Optional[int] = None):
        """Start processing scraping tasks"""
        if max_tasks is None:
            max_tasks = len(self.pending_tasks)
        
        self.logger.info(f"Starting processing of {max_tasks} tasks")
        
        # Process tasks with concurrency control
        tasks_to_process = self.pending_tasks[:max_tasks]
        self.pending_tasks = self.pending_tasks[max_tasks:]
        
        # Create async tasks for each scraping task
        async def process_task(task: ScrapingTask):
            async with self.semaphore:
                return await self._process_single_task(task)
        
        # Process tasks concurrently
        results = await asyncio.gather(
            *[process_task(task) for task in tasks_to_process],
            return_exceptions=True
        )
        
        # Handle results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {i} failed with exception: {result}")
                task = tasks_to_process[i]
                job_id = f"{task.source.value}_{int(time.time() * 1000)}"
                failed_result = ScrapingResult(
                    job_id=job_id,
                    source=task.source.value,
                    status=ResultStatus.FAILED,
                    url_scraped=task.url,
                    error_message=str(result),
                    error_code=type(result).__name__
                )
                self.failed_tasks.append(failed_result)
            else:
                self.completed_tasks.append(result)
        
        self.logger.info(f"Completed processing {len(results)} tasks")
    
    async def _process_single_task(self, task: ScrapingTask) -> ScrapingResult:
        """Process a single scraping task"""
        start_time = time.time()
        job_id = f"{task.source.value}_{int(start_time * 1000)}"
        
        try:
            # Rate limiting
            delay = await self.rate_limiter.acquire(task.url)
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Perform HTTP request
            result = await self.http_client.get(task.url, job_id=job_id, source=task.source.value)
            
            # Update metrics
            self.total_requests += 1
            if result.status == ResultStatus.SUCCESS:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            # Set required fields for the result
            result.job_id = job_id
            result.source = task.source.value
            
            # Parse HTML and extract book data
            if result.status == ResultStatus.SUCCESS and result.raw_html:
                try:
                    book_data = await self._extract_book_data(result.raw_html, task.url, task.source)
                    if book_data:
                        result.book = book_data
                        result.status = ResultStatus.SUCCESS
                    else:
                        result.status = ResultStatus.PARTIAL
                except Exception as e:
                    self.logger.error(f"Book data extraction failed for {task.url}: {e}")
                    result.status = ResultStatus.PARTIAL
                    result.error_message = f"Book data extraction failed: {str(e)}"
            
            # Call callback if provided
            if task.callback:
                try:
                    await task.callback(result)
                except Exception as e:
                    self.logger.error(f"Callback failed for task {task.url}: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task processing failed for {task.url}: {e}")
            self.failed_requests += 1
            
            return ScrapingResult(
                job_id=job_id,
                source=task.source.value,
                status=ResultStatus.FAILED,
                url_scraped=task.url,
                error_message=str(e),
                error_code=type(e).__name__
            )
    
    async def _extract_book_data(self, html: str, url: str, source: BookSource) -> Optional[Book]:
        """Extract book data from HTML content"""
        try:
            self.logger.debug(f"Starting HTML parsing for {url}")
            parser = HTMLParser(html, url)
            
            # Log parser availability
            parser_stats = parser.get_parser_stats()
            self.logger.debug(f"Parser stats: {parser_stats}")
            
            # Extract structured data first (most reliable)
            structured_data = parser.extract_structured_data()
            if structured_data:
                self.logger.debug(f"Found {len(structured_data)} structured data items")
                book = await self._parse_structured_data(structured_data, source)
                if book:
                    self.logger.debug(f"Successfully parsed structured data for {url}")
                    return book
            
            # Fallback to HTML parsing
            self.logger.debug(f"Falling back to HTML parsing for {url}")
            book = await self._parse_html_content(parser, source)
            if book:
                self.logger.debug(f"Successfully parsed HTML content for {url}")
                return book
            
            self.logger.warning(f"Failed to extract book data from {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract book data from {url}: {e}")
            return None
    
    async def _parse_structured_data(self, data: List[Dict[str, Any]], source: BookSource) -> Optional[Book]:
        """Parse structured data (JSON-LD, Microdata)"""
        for item in data:
            if not isinstance(item, dict):
                continue
            
            # Look for Book schema
            if item.get('@type') in ['Book', 'http://schema.org/Book']:
                try:
                    metadata = BookMetadata(
                        title=item.get('name', ''),
                        authors=item.get('author', []) if isinstance(item.get('author'), list) else [item.get('author', '')],
                        isbn=item.get('isbn', ''),
                        isbn13=item.get('isbn13', ''),
                        isbn10=item.get('isbn10', ''),
                        publisher=item.get('publisher', {}).get('name', '') if isinstance(item.get('publisher'), dict) else item.get('publisher', ''),
                        description=item.get('description', ''),
                        rating=float(item.get('aggregateRating', {}).get('ratingValue', 0)) if item.get('aggregateRating') else None,
                        rating_count=int(item.get('aggregateRating', {}).get('ratingCount', 0)) if item.get('aggregateRating') else None,
                        cover_image_url=item.get('image', ''),
                        source_id=item.get('identifier', ''),
                        source_url=item.get('url', ''),
                        source_metadata=item
                    )
                    
                    return Book(
                        metadata=metadata,
                        primary_source=source,
                        sources=[source]
                    )
                    
                except Exception as e:
                    self.logger.debug(f"Failed to parse structured data item: {e}")
                    continue
        
        return None
    
    async def _parse_html_content(self, parser: HTMLParser, source: BookSource) -> Optional[Book]:
        """Parse HTML content for book information"""
        try:
            # Extract basic metadata
            metadata = parser.extract_metadata()
            
            # Extract title
            title = metadata.get('title', '')
            if not title:
                title_elem = parser.find('h1') or parser.find('h2')
                if title_elem:
                    try:
                        title = parser.get_text(title_elem)
                    except Exception as e:
                        self.logger.debug(f"Failed to extract title text: {e}")
                        title = ""
            
            # Extract authors
            authors = []
            author_elements = parser.select('[class*="author"], [class*="Author"], .author, .Author')
            for elem in author_elements:
                try:
                    author_text = parser.get_text(elem)
                    if author_text and len(author_text) < 100:  # Reasonable author name length
                        authors.append(author_text)
                except Exception as e:
                    self.logger.debug(f"Failed to extract author text: {e}")
                    continue
            
            # Extract description
            description = ""
            desc_elements = parser.select('[class*="description"], [class*="Description"], .description, .Description')
            for elem in desc_elements:
                try:
                    desc_text = parser.get_text(elem)
                    if desc_text and len(desc_text) > 20:  # Reasonable description length
                        description = desc_text
                        break
                except Exception as e:
                    self.logger.debug(f"Failed to extract description text: {e}")
                    continue
            
            # Extract cover image
            cover_image = ""
            img_elements = parser.select('img[class*="cover"], img[class*="Cover"], .cover img, .Cover img')
            for img in img_elements:
                try:
                    src = parser.get_attribute(img, 'src')
                    alt = parser.get_attribute(img, 'alt') or ''
                    if src and ('cover' in src.lower() or 'cover' in alt.lower()):
                        cover_image = parser.normalize_url(src)
                        break
                except Exception as e:
                    self.logger.debug(f"Failed to extract image attributes: {e}")
                    continue
            
            # Create book metadata
            book_metadata = BookMetadata(
                title=title,
                authors=authors,
                description=description,
                cover_image_url=cover_image if cover_image else None,
                source_metadata=metadata
            )
            
            # Create book object
            book = Book(
                metadata=book_metadata,
                primary_source=source,
                sources=[source]
            )
            
            return book if title else None
            
        except Exception as e:
            self.logger.error(f"Failed to parse HTML content: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper engine statistics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "requests_per_second": self.total_requests / max(1, uptime),
            "pending_tasks": len(self.pending_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "rate_limiter_stats": self.rate_limiter.get_all_stats(),
            "http_client_stats": self.http_client.get_session_stats() if self.http_client else {}
        }
    
    async def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for all running tasks to complete"""
        if not self.running_tasks:
            return
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.running_tasks.values(), return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for task completion")
    
    def get_results(self) -> List[ScrapingResult]:
        """Get all completed results"""
        return self.completed_tasks.copy()
    
    def get_failed_results(self) -> List[ScrapingResult]:
        """Get all failed results"""
        return self.failed_tasks.copy()
    
    def clear_results(self):
        """Clear all results"""
        self.completed_tasks.clear()
        self.failed_tasks.clear() 