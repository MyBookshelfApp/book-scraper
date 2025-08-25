"""
Main FastAPI application for the Book Scraper service
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog

from .config import settings
from .core.scraper_engine import ScraperEngine, ScrapingTask
from .models.book import Book, BookSource
from .models.scraping_job import ScrapingJob, JobType, JobStatus
from .models.scraping_result import ScrapingResult
from .api.routes import router as api_router
from .monitoring.metrics import setup_metrics, get_metrics
from .dependencies import set_scraper_engine


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Book Scraper service", version=settings.app_version)
    
    # Initialize scraper engine
    scraper_engine = ScraperEngine()
    await scraper_engine.__aenter__()
    
    # Set the global instance
    set_scraper_engine(scraper_engine)
    
    # Setup metrics
    if settings.enable_metrics:
        setup_metrics()
    
    logger.info("Book Scraper service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Book Scraper service")
    
    if scraper_engine:
        await scraper_engine.__aexit__(None, None, None)
    
    logger.info("Book Scraper service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance book scraping service designed for Kubernetes deployment",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        from .dependencies import get_scraper_engine
        
        # Check if scraper engine is available
        scraper_engine = get_scraper_engine()
        
        # Get basic stats
        stats = scraper_engine.get_stats()
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "uptime_seconds": stats.get("uptime_seconds", 0),
            "total_requests": stats.get("total_requests", 0),
            "success_rate": stats.get("success_rate", 0.0)
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    try:
        from .dependencies import get_scraper_engine
        
        scraper_engine = get_scraper_engine()
        
        # Check if we can process requests
        stats = scraper_engine.get_stats()
        if stats.get("uptime_seconds", 0) < 5:  # Service needs time to warm up
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Service warming up"}
            )
        
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": f"Error: {str(e)}"}
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return get_metrics()


@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": "production" if not settings.debug else "development",
        "kubernetes": {
            "pod_name": settings.pod_name,
            "namespace": settings.namespace
        },
        "configuration": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "rate_limit_per_second": settings.rate_limit_per_second,
            "enabled_sources": settings.enabled_sources,
            "database_type": settings.database_type
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    ) 