"""
Dependencies for the Book Scraper service
"""
from fastapi import HTTPException

from .core.scraper_engine import ScraperEngine

# Global scraper engine instance
scraper_engine: ScraperEngine = None


def get_scraper_engine() -> ScraperEngine:
    """Get the global scraper engine instance"""
    if scraper_engine is None:
        raise HTTPException(status_code=503, detail="Scraper engine not available")
    return scraper_engine


def set_scraper_engine(engine: ScraperEngine):
    """Set the global scraper engine instance"""
    global scraper_engine
    scraper_engine = engine 