"""
Rate limiting and request throttling for book scraping
"""
import asyncio
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from collections import defaultdict
import random


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float
    burst_size: int = 1
    jitter: float = 0.1  # Random jitter to avoid detection


class RateLimiter:
    """Rate limiter with token bucket algorithm and jitter"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_refill = time.time()
        self.refill_rate = config.requests_per_second
        
        # Per-domain rate limiting
        self.domain_limits: Dict[str, RateLimiter] = {}
        
        # Request tracking for analytics
        self.request_count = 0
        self.blocked_count = 0
        self.last_request_time = 0
    
    def _refill_tokens(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _add_jitter(self, delay: float) -> float:
        """Add random jitter to delay to avoid detection"""
        jitter_range = delay * self.config.jitter
        jitter = random.uniform(-jitter_range, jitter_range)
        return max(0, delay + jitter)
    
    async def acquire(self, domain: Optional[str] = None) -> float:
        """Acquire permission to make a request, returns delay if needed"""
        # Check domain-specific rate limit first
        if domain and domain in self.domain_limits:
            domain_delay = await self.domain_limits[domain].acquire()
            if domain_delay > 0:
                return domain_delay
        
        # Check global rate limit
        self._refill_tokens()
        
        if self.tokens >= 1:
            self.tokens -= 1
            self.request_count += 1
            self.last_request_time = time.time()
            return 0
        else:
            self.blocked_count += 1
            # Calculate delay needed
            delay = (1 - self.tokens) / self.refill_rate
            return self._add_jitter(delay)
    
    def add_domain_limit(self, domain: str, config: RateLimitConfig):
        """Add domain-specific rate limiting"""
        self.domain_limits[domain] = RateLimiter(config)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "tokens_available": self.tokens,
            "requests_per_second": self.refill_rate,
            "burst_size": self.config.burst_size,
            "total_requests": self.request_count,
            "blocked_requests": self.blocked_count,
            "success_rate": self.request_count / max(1, self.request_count + self.blocked_count),
            "domain_limits": len(self.domain_limits)
        }


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on response patterns"""
    
    def __init__(self, config: RateLimitConfig):
        super().__init__(config)
        self.response_times: list = []
        self.error_rates: list = []
        self.adaptation_factor = 1.0
        
        # Adaptation thresholds
        self.max_response_time = 5.0  # seconds
        self.max_error_rate = 0.1  # 10%
        self.min_requests_per_second = 0.1
    
    def record_response(self, response_time: float, success: bool):
        """Record response metrics for adaptation"""
        self.response_times.append(response_time)
        self.error_rates.append(0 if success else 1)
        
        # Keep only recent history
        if len(self.response_times) > 100:
            self.response_times.pop(0)
            self.error_rates.pop(0)
        
        # Adapt rate based on performance
        self._adapt_rate()
    
    def _adapt_rate(self):
        """Adapt rate based on performance metrics"""
        if len(self.response_times) < 10:
            return
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        avg_error_rate = sum(self.error_rates) / len(self.error_rates)
        
        # Calculate adaptation factor
        response_factor = min(1.0, self.max_response_time / max(avg_response_time, 0.1))
        error_factor = 1.0 - avg_error_rate / self.max_error_rate
        
        # Combine factors
        new_factor = (response_factor + error_factor) / 2
        
        # Smooth adaptation
        self.adaptation_factor = 0.7 * self.adaptation_factor + 0.3 * new_factor
        
        # Apply adaptation
        new_rate = self.config.requests_per_second * self.adaptation_factor
        new_rate = max(self.min_requests_per_second, new_rate)
        
        self.refill_rate = new_rate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adaptive rate limiter statistics"""
        base_stats = super().get_stats()
        base_stats.update({
            "adaptation_factor": self.adaptation_factor,
            "current_rate": self.refill_rate,
            "avg_response_time": sum(self.response_times) / max(1, len(self.response_times)),
            "avg_error_rate": sum(self.error_rates) / max(1, len(self.error_rates))
        })
        return base_stats


class GlobalRateLimiter:
    """Global rate limiter managing multiple domains and sources"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.default_config = RateLimitConfig(requests_per_second=10)
        
        # Initialize default limiters
        self._init_default_limiters()
    
    def _init_default_limiters(self):
        """Initialize default rate limiters for common book sources"""
        # Goodreads - conservative rate limiting
        self.add_limiter("goodreads.com", RateLimitConfig(
            requests_per_second=2,
            burst_size=3,
            jitter=0.2
        ))
        
        # Amazon - very conservative
        self.add_limiter("amazon.com", RateLimitConfig(
            requests_per_second=1,
            burst_size=2,
            jitter=0.3
        ))
        
        # Google Books - more permissive
        self.add_limiter("books.google.com", RateLimitConfig(
            requests_per_second=5,
            burst_size=5,
            jitter=0.1
        ))
        
        # OpenLibrary - permissive
        self.add_limiter("openlibrary.org", RateLimitConfig(
            requests_per_second=8,
            burst_size=10,
            jitter=0.1
        ))
    
    def add_limiter(self, domain: str, config: RateLimitConfig):
        """Add a rate limiter for a specific domain"""
        self.limiters[domain] = RateLimiter(config)
    
    def get_limiter(self, domain: str) -> RateLimiter:
        """Get rate limiter for a domain, create default if not exists"""
        if domain not in self.limiters:
            self.limiters[domain] = RateLimiter(self.default_config)
        return self.limiters[domain]
    
    async def acquire(self, url: str) -> float:
        """Acquire permission to make a request to a URL"""
        from urllib.parse import urlparse
        
        try:
            domain = urlparse(url).netloc
            limiter = self.get_limiter(domain)
            return await limiter.acquire()
        except Exception:
            # Fallback to default limiter
            default_limiter = self.get_limiter("default")
            return await default_limiter.acquire()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all rate limiters"""
        return {domain: limiter.get_stats() for domain, limiter in self.limiters.items()} 