"""
API routes for the Book Scraper service
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, HttpUrl

from ..core.scraper_engine import ScraperEngine, ScrapingTask
from ..models.book import Book, BookSource
from ..models.scraping_job import ScrapingJob, JobType, JobStatus
from ..models.scraping_result import ScrapingResult
from ..dependencies import get_scraper_engine

router = APIRouter()


class ScrapeRequest(BaseModel):
    """Request model for scraping operations"""
    urls: List[HttpUrl]
    source: BookSource
    priority: int = 5
    metadata: Optional[Dict[str, Any]] = None


class ScrapeResponse(BaseModel):
    """Response model for scraping operations"""
    job_id: str
    task_count: int
    status: str
    message: str


class BookSearchRequest(BaseModel):
    """Request model for book search"""
    query: str
    source: Optional[BookSource] = None
    limit: int = 10


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_books(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Scrape books from multiple URLs"""
    try:
        # Create scraping tasks
        tasks = []
        for url in request.urls:
            task = ScrapingTask(
                url=str(url),
                source=request.source,
                priority=request.priority,
                metadata=request.metadata
            )
            tasks.append(task)
        
        # Add tasks to scraper
        task_ids = await scraper.add_batch_tasks(tasks)
        
        # Start processing in background
        background_tasks.add_task(scraper.start_processing, len(tasks))
        
        return ScrapeResponse(
            job_id=f"batch_{len(task_ids)}",
            task_count=len(tasks),
            status="started",
            message=f"Started scraping {len(tasks)} URLs from {request.source.value}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@router.post("/scrape/single", response_model=ScrapeResponse)
async def scrape_single_book(
    url: HttpUrl,
    source: BookSource,
    priority: int = Query(5, ge=1, le=10),
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Scrape a single book URL"""
    try:
        task = ScrapingTask(
            url=str(url),
            source=source,
            priority=priority
        )
        
        task_id = await scraper.add_task(task)
        
        # Start processing immediately
        await scraper.start_processing(1)
        
        return ScrapeResponse(
            job_id=task_id,
            task_count=1,
            status="started",
            message=f"Started scraping {url} from {source.value}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@router.get("/results", response_model=List[ScrapingResult])
async def get_scraping_results(
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Get all completed scraping results"""
    return scraper.get_results()


@router.get("/results/failed", response_model=List[ScrapingResult])
async def get_failed_results(
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Get all failed scraping results"""
    return scraper.get_failed_results()


@router.get("/stats")
async def get_scraper_stats(
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Get scraper engine statistics"""
    return scraper.get_stats()


@router.delete("/results")
async def clear_results(
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Clear all scraping results"""
    scraper.clear_results()
    return {"message": "All results cleared"}


@router.get("/sources")
async def get_enabled_sources():
    """Get list of enabled book sources"""
    return {
        "enabled_sources": [source.value for source in BookSource],
        "available_sources": [source.value for source in BookSource]
    }


@router.get("/health/detailed")
async def detailed_health_check(
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Detailed health check with component status"""
    try:
        stats = scraper.get_stats()
        
        # Check component health
        components = {
            "scraper_engine": {
                "status": "healthy" if scraper else "unhealthy",
                "uptime_seconds": stats.get("uptime_seconds", 0),
                "total_requests": stats.get("total_requests", 0)
            },
            "rate_limiter": {
                "status": "healthy",
                "stats": stats.get("rate_limiter_stats", {})
            },
            "http_client": {
                "status": "healthy" if stats.get("http_client_stats") else "unhealthy",
                "stats": stats.get("http_client_stats", {})
            }
        }
        
        # Overall health
        overall_healthy = all(
            comp["status"] == "healthy" 
            for comp in components.values()
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "components": components,
            "timestamp": stats.get("uptime_seconds", 0)
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "components": {}
        }


@router.post("/scrape/batch")
async def batch_scrape_books(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Batch scrape books with progress tracking"""
    try:
        # Create scraping tasks
        tasks = []
        for url in request.urls:
            task = ScrapingTask(
                url=str(url),
                source=request.source,
                priority=request.priority,
                metadata=request.metadata
            )
            tasks.append(task)
        
        # Add tasks to scraper
        task_ids = await scraper.add_batch_tasks(tasks)
        
        # Start processing in background
        background_tasks.add_task(scraper.start_processing, len(tasks))
        
        return {
            "job_id": f"batch_{len(task_ids)}",
            "task_count": len(tasks),
            "status": "started",
            "task_ids": task_ids,
            "message": f"Started batch scraping {len(tasks)} URLs from {request.source.value}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch scraping: {str(e)}")


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    scraper: ScraperEngine = Depends(get_scraper_engine)
):
    """Get status of a specific scraping job"""
    # For now, return basic status
    # In a full implementation, you'd track individual jobs
    stats = scraper.get_stats()
    
    return {
        "job_id": job_id,
        "status": "completed",  # Simplified for now
        "total_tasks": stats.get("completed_tasks", 0) + stats.get("failed_tasks", 0),
        "completed_tasks": stats.get("completed_tasks", 0),
        "failed_tasks": stats.get("failed_tasks", 0),
        "success_rate": stats.get("success_rate", 0.0)
    } 