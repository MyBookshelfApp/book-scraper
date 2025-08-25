"""
High-performance async HTTP client for book scraping
"""
import asyncio
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import httpx
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import settings
from ..models.scraping_result import ScrapingResult, ResultStatus


class HTTPClient:
    """High-performance async HTTP client with connection pooling and retry logic"""
    
    def __init__(self):
        self._httpx_client: Optional[httpx.AsyncClient] = None
        self._aiohttp_session: Optional[aiohttp.ClientSession] = None
        self._connection_pool_size = settings.max_concurrent_requests
        self._timeout = settings.request_timeout
        
        # User agent rotation for avoiding detection
        self._user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        
        # Default headers
        self._default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def __aenter__(self):
        await self._initialize_clients()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()
    
    async def _initialize_clients(self):
        """Initialize HTTP clients with connection pooling"""
        # HTTPX client for general requests
        limits = httpx.Limits(
            max_keepalive_connections=self._connection_pool_size,
            max_connections=self._connection_pool_size * 2,
            keepalive_expiry=30.0
        )
        
        self._httpx_client = httpx.AsyncClient(
            limits=limits,
            timeout=self._timeout,
            follow_redirects=True,
            http2=True
        )
        
        # Aiohttp session for more complex scenarios
        connector = aiohttp.TCPConnector(
            limit=self._connection_pool_size,
            limit_per_host=self._connection_pool_size // 4,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self._aiohttp_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers=self._default_headers
        )
    
    async def _cleanup(self):
        """Clean up HTTP clients"""
        if self._httpx_client:
            await self._httpx_client.aclose()
        if self._aiohttp_session:
            await self._aiohttp_session.close()
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection"""
        import random
        return random.choice(self._user_agents)
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=settings.retry_delay, max=60),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, aiohttp.ClientError))
    )
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> ScrapingResult:
        """Perform a GET request with retry logic and result tracking"""
        start_time = time.time()
        
        # Prepare headers
        request_headers = self._default_headers.copy()
        if headers:
            request_headers.update(headers)
        request_headers["User-Agent"] = self._get_random_user_agent()
        
        try:
            # Use HTTPX for better performance
            response = await self._httpx_client.get(url, headers=request_headers, **kwargs)
            response.raise_for_status()
            
            response_time = (time.time() - start_time) * 1000
            content = response.text
            data_size = len(content.encode('utf-8'))
            
            return ScrapingResult(
                status=ResultStatus.SUCCESS,
                url_scraped=url,
                user_agent=request_headers["User-Agent"],
                response_time_ms=response_time,
                data_size_bytes=data_size,
                raw_html=content,
                extracted_data={"status_code": response.status_code, "headers": dict(response.headers)}
            )
            
        except httpx.HTTPStatusError as e:
            response_time = (time.time() - start_time) * 1000
            return ScrapingResult(
                status=ResultStatus.FAILED,
                url_scraped=url,
                user_agent=request_headers["User-Agent"],
                response_time_ms=response_time,
                error_message=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                error_code=f"HTTP_{e.response.status_code}"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ScrapingResult(
                status=ResultStatus.FAILED,
                url_scraped=url,
                user_agent=request_headers["User-Agent"],
                response_time_ms=response_time,
                error_message=str(e),
                error_code=type(e).__name__
            )
    
    async def get_batch(self, urls: List[str], max_concurrent: Optional[int] = None) -> List[ScrapingResult]:
        """Perform multiple GET requests concurrently"""
        if max_concurrent is None:
            max_concurrent = min(len(urls), settings.max_concurrent_requests)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _fetch_with_semaphore(url: str) -> ScrapingResult:
            async with semaphore:
                return await self.get(url)
        
        tasks = [_fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ScrapingResult(
                    status=ResultStatus.FAILED,
                    url_scraped=urls[i],
                    error_message=str(result),
                    error_code=type(result).__name__
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                   json_data: Optional[Dict[str, Any]] = None, 
                   headers: Optional[Dict[str, str]] = None, **kwargs) -> ScrapingResult:
        """Perform a POST request"""
        start_time = time.time()
        
        request_headers = self._default_headers.copy()
        if headers:
            request_headers.update(headers)
        request_headers["User-Agent"] = self._get_random_user_agent()
        
        try:
            response = await self._httpx_client.post(
                url, 
                data=data, 
                json=json_data, 
                headers=request_headers, 
                **kwargs
            )
            response.raise_for_status()
            
            response_time = (time.time() - start_time) * 1000
            content = response.text
            data_size = len(content.encode('utf-8'))
            
            return ScrapingResult(
                status=ResultStatus.SUCCESS,
                url_scraped=url,
                user_agent=request_headers["User-Agent"],
                response_time_ms=response_time,
                data_size_bytes=data_size,
                raw_html=content,
                extracted_data={"status_code": response.status_code, "headers": dict(response.headers)}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ScrapingResult(
                status=ResultStatus.FAILED,
                url_scraped=url,
                user_agent=request_headers["User-Agent"],
                response_time_ms=response_time,
                error_message=str(e),
                error_code=type(e).__name__
            )
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        stats = {
            "httpx_available": True,
            "aiohttp_available": self._aiohttp_session is not None
        }
        
        # Try to get connection pool info if available
        if self._httpx_client and hasattr(self._httpx_client, '_transport'):
            try:
                # Check if we can access connection pool info
                if hasattr(self._httpx_client._transport, '_pool'):
                    pool = self._httpx_client._transport._pool
                    if hasattr(pool, '_num_connections'):
                        stats["httpx_connections"] = pool._num_connections
                    if hasattr(pool, '_num_available_connections'):
                        stats["httpx_available_connections"] = pool._num_available_connections
                    else:
                        stats["httpx_connections"] = "unknown"
                        stats["httpx_available_connections"] = "unknown"
                else:
                    stats["httpx_connections"] = "no_pool"
                    stats["httpx_available_connections"] = "no_pool"
            except Exception:
                stats["httpx_connections"] = "error"
                stats["httpx_available_connections"] = "error"
        
        return stats 