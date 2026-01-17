"""
Retry and QoS Module

Handles retries, partial failures, and quality of service for ingestion.
"""
import asyncio
from typing import Callable, Any, List, Dict
from functools import wraps
from dataclasses import dataclass
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass

class RetryableError(IngestionError):
    """Error that should be retried."""
    pass

class PermanentError(IngestionError):
    """Error that should not be retried."""
    pass

@dataclass
class BatchResult:
    batch_id: int
    success: bool
    elements_processed: int
    error: str = None

def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 30
):
    """Decorator for retryable operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(RetryableError)
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class BatchProcessor:
    """Processes batches with partial failure handling."""
    
    def __init__(
        self,
        max_concurrent: int = 3,
        allow_partial_failure: bool = True,
        failure_threshold: float = 0.5
    ):
        self.max_concurrent = max_concurrent
        self.allow_partial_failure = allow_partial_failure
        self.failure_threshold = failure_threshold
    
    async def process_batches(
        self,
        batches: List[Any],
        processor: Callable
    ) -> Dict[str, Any]:
        """
        Process batches with concurrency control and failure handling.
        
        Args:
            batches: List of batch objects
            processor: Async function to process each batch
            
        Returns:
            Results dict with success/failure stats
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results: List[BatchResult] = []
        
        async def process_with_semaphore(batch):
            async with semaphore:
                try:
                    result = await processor(batch)
                    return BatchResult(
                        batch_id=batch.batch_id,
                        success=True,
                        elements_processed=result.get("elements", 0)
                    )
                except Exception as e:
                    return BatchResult(
                        batch_id=batch.batch_id,
                        success=False,
                        elements_processed=0,
                        error=str(e)
                    )
        
        # Process all batches
        tasks = [process_with_semaphore(b) for b in batches]
        results = await asyncio.gather(*tasks)
        
        # Calculate stats
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        failure_rate = len(failed) / len(results) if results else 0
        
        # Check if failure threshold exceeded
        if not self.allow_partial_failure and failed:
            raise IngestionError(f"Batch failures: {[r.error for r in failed]}")
        
        if failure_rate > self.failure_threshold:
            raise IngestionError(
                f"Failure rate {failure_rate:.1%} exceeds threshold {self.failure_threshold:.1%}"
            )
        
        return {
            "total_batches": len(results),
            "successful_batches": len(successful),
            "failed_batches": len(failed),
            "total_elements": sum(r.elements_processed for r in successful),
            "errors": [{"batch_id": r.batch_id, "error": r.error} for r in failed]
        }

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until rate limit allows next call."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait_time = self.last_call + self.interval - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_call = asyncio.get_event_loop().time()

class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if asyncio.get_event_loop().time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise IngestionError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = asyncio.get_event_loop().time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise
