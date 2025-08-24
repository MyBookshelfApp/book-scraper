"""
Prometheus metrics for the Book Scraper service
"""
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any

# Request metrics
REQUEST_COUNT = Counter(
    'book_scraper_requests_total',
    'Total number of scraping requests',
    ['source', 'status']
)

REQUEST_DURATION = Histogram(
    'book_scraper_request_duration_seconds',
    'Duration of scraping requests',
    ['source', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Success/failure metrics
SUCCESS_COUNT = Counter(
    'book_scraper_success_total',
    'Total number of successful scrapes',
    ['source']
)

FAILURE_COUNT = Counter(
    'book_scraper_failure_total',
    'Total number of failed scrapes',
    ['source', 'error_type']
)

# Data metrics
BOOKS_EXTRACTED = Counter(
    'book_scraper_books_extracted_total',
    'Total number of books successfully extracted',
    ['source']
)

DATA_SIZE = Histogram(
    'book_scraper_data_size_bytes',
    'Size of scraped data in bytes',
    ['source'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Rate limiting metrics
RATE_LIMIT_DELAYS = Histogram(
    'book_scraper_rate_limit_delay_seconds',
    'Delay due to rate limiting',
    ['domain'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Concurrency metrics
ACTIVE_REQUESTS = Gauge(
    'book_scraper_active_requests',
    'Number of currently active requests'
)

QUEUE_SIZE = Gauge(
    'book_scraper_queue_size',
    'Number of pending scraping tasks'
)

# Performance metrics
REQUESTS_PER_SECOND = Gauge(
    'book_scraper_requests_per_second',
    'Current requests per second rate'
)

SUCCESS_RATE = Gauge(
    'book_scraper_success_rate',
    'Current success rate (0.0 to 1.0)'
)

# Uptime metrics
UPTIME_SECONDS = Gauge(
    'book_scraper_uptime_seconds',
    'Service uptime in seconds'
)

# Memory and resource metrics
MEMORY_USAGE_BYTES = Gauge(
    'book_scraper_memory_usage_bytes',
    'Current memory usage in bytes'
)

CPU_USAGE_PERCENT = Gauge(
    'book_scraper_cpu_usage_percent',
    'Current CPU usage percentage'
)


def setup_metrics():
    """Initialize metrics collection"""
    # Initialize gauges with default values
    ACTIVE_REQUESTS.set(0)
    QUEUE_SIZE.set(0)
    REQUESTS_PER_SECOND.set(0)
    SUCCESS_RATE.set(0)
    UPTIME_SECONDS.set(0)
    MEMORY_USAGE_BYTES.set(0)
    CPU_USAGE_PERCENT.set(0)


def record_request(source: str, status: str, duration: float):
    """Record a scraping request"""
    REQUEST_COUNT.labels(source=source, status=status).inc()
    REQUEST_DURATION.labels(source=source, status=status).observe(duration)


def record_success(source: str):
    """Record a successful scrape"""
    SUCCESS_COUNT.labels(source=source).inc()


def record_failure(source: str, error_type: str):
    """Record a failed scrape"""
    FAILURE_COUNT.labels(source=source, error_type=error_type).inc()


def record_book_extracted(source: str):
    """Record a successfully extracted book"""
    BOOKS_EXTRACTED.labels(source=source).inc()


def record_data_size(source: str, size_bytes: int):
    """Record the size of scraped data"""
    DATA_SIZE.labels(source=source).observe(size_bytes)


def record_rate_limit_delay(domain: str, delay: float):
    """Record rate limiting delay"""
    RATE_LIMIT_DELAYS.labels(domain=domain).observe(delay)


def update_active_requests(count: int):
    """Update the count of active requests"""
    ACTIVE_REQUESTS.set(count)


def update_queue_size(size: int):
    """Update the queue size"""
    QUEUE_SIZE.set(size)


def update_performance_metrics(requests_per_second: float, success_rate: float):
    """Update performance metrics"""
    REQUESTS_PER_SECOND.set(requests_per_second)
    SUCCESS_RATE.set(success_rate)


def update_uptime(uptime_seconds: float):
    """Update uptime metric"""
    UPTIME_SECONDS.set(uptime_seconds)


def update_resource_metrics(memory_bytes: int, cpu_percent: float):
    """Update resource usage metrics"""
    MEMORY_USAGE_BYTES.set(memory_bytes)
    CPU_USAGE_PERCENT.set(cpu_percent)


def get_metrics():
    """Get all metrics in Prometheus format"""
    return generate_latest()


def get_metrics_content_type():
    """Get the content type for metrics"""
    return CONTENT_TYPE_LATEST


class MetricsCollector:
    """Helper class for collecting metrics from the scraper engine"""
    
    def __init__(self):
        self.start_time = None
    
    def start_collection(self):
        """Start metrics collection"""
        import time
        self.start_time = time.time()
    
    def collect_from_stats(self, stats: Dict[str, Any]):
        """Collect metrics from scraper engine statistics"""
        if not stats:
            return
        
        # Update basic metrics
        update_active_requests(stats.get('running_tasks', 0))
        update_queue_size(stats.get('pending_tasks', 0))
        
        # Update performance metrics
        uptime = stats.get('uptime_seconds', 0)
        if uptime > 0:
            update_uptime(uptime)
            
            requests_per_second = stats.get('requests_per_second', 0)
            success_rate = stats.get('success_rate', 0)
            update_performance_metrics(requests_per_second, success_rate)
        
        # Update source-specific metrics
        rate_limiter_stats = stats.get('rate_limiter_stats', {})
        for domain, domain_stats in rate_limiter_stats.items():
            if 'total_requests' in domain_stats:
                # This would need to be tracked per domain in the actual implementation
                pass
        
        # Update HTTP client stats
        http_stats = stats.get('http_client_stats', {})
        if 'httpx_connections' in http_stats:
            # Could track connection pool metrics here
            pass
    
    def collect_resource_metrics(self):
        """Collect system resource metrics"""
        try:
            import psutil
            
            # Memory usage
            memory_info = psutil.virtual_memory()
            update_resource_metrics(memory_info.used, memory_info.percent)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            update_resource_metrics(memory_info.used, cpu_percent)
            
        except ImportError:
            # psutil not available, skip resource metrics
            pass 