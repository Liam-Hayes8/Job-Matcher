from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import functools
import logging

logger = logging.getLogger(__name__)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_database_connections',
    'Number of active database connections'
)

resume_parsing_duration = Histogram(
    'resume_parsing_duration_seconds',
    'Time taken to parse a resume',
    ['status']
)

job_matching_duration = Histogram(
    'job_matching_duration_seconds',
    'Time taken to find job matches',
    ['status']
)

def track_request_metrics(func):
    """Decorator to track HTTP request metrics."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "unknown"
        endpoint = func.__name__
        status = "unknown"
        
        try:
            # Try to extract request info if available
            if args and hasattr(args[0], 'method'):
                method = args[0].method
                endpoint = args[0].url.path
            
            result = await func(*args, **kwargs)
            status = "success"
            return result
            
        except Exception as e:
            status = "error"
            logger.error(f"Request failed: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return wrapper

def track_resume_parsing(func):
    """Decorator to track resume parsing metrics."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            logger.error(f"Resume parsing failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            resume_parsing_duration.labels(status=status).observe(duration)
    
    return wrapper

def track_job_matching(func):
    """Decorator to track job matching metrics."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            logger.error(f"Job matching failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            job_matching_duration.labels(status=status).observe(duration)
    
    return wrapper

def get_metrics():
    """Get Prometheus metrics in text format."""
    return generate_latest()