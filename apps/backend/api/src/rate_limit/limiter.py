"""
Rate Limiting Module

Protects Gemini + Vespa from overload with 20 concurrent users.
"""
import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from shared.config.settings import get_config

config = get_config()

@dataclass
class RateLimitState:
    """Track rate limit state per user."""
    request_times: list = field(default_factory=list)
    
    def add_request(self):
        self.request_times.append(time.time())
    
    def count_recent(self, window_seconds: int = 60) -> int:
        cutoff = time.time() - window_seconds
        self.request_times = [t for t in self.request_times if t > cutoff]
        return len(self.request_times)

class RateLimiter:
    """
    Rate limiter for concurrent users.
    
    Limits:
    - Global concurrent requests
    - Per-user requests per minute
    - Gemini API calls per minute
    - Vespa queries per minute
    """
    
    def __init__(self):
        self._semaphore = asyncio.Semaphore(config.rate_limit.max_concurrent_requests)
        self._user_states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._gemini_limiter = TokenBucketLimiter(
            config.rate_limit.gemini_requests_per_minute
        )
        self._vespa_limiter = TokenBucketLimiter(
            config.rate_limit.vespa_requests_per_minute
        )
    
    async def acquire_request(self, user_id: str) -> bool:
        """Acquire permission for a user request."""
        # Check per-user limit
        state = self._user_states[user_id]
        if state.count_recent(60) >= config.rate_limit.max_requests_per_user_per_minute:
            return False
        
        # Acquire global semaphore
        acquired = self._semaphore.locked()
        if acquired and self._semaphore._value == 0:
            return False
        
        await self._semaphore.acquire()
        state.add_request()
        return True
    
    def release_request(self):
        """Release request slot."""
        self._semaphore.release()
    
    async def acquire_gemini(self):
        """Acquire Gemini API slot."""
        await self._gemini_limiter.acquire()
    
    async def acquire_vespa(self):
        """Acquire Vespa query slot."""
        await self._vespa_limiter.acquire()

class TokenBucketLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate_per_minute: int):
        self.rate = rate_per_minute / 60.0  # tokens per second
        self.max_tokens = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a token is available."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    return rate_limiter
