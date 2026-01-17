"""
Caching Module

Cache embeddings and repeated query rewrites to reduce latency and API costs.
"""
import asyncio
import hashlib
import time
from typing import Optional, Any, Dict, List
from dataclasses import dataclass
import json

from shared.config.settings import get_config

config = get_config()

@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class InMemoryCache:
    """
    Simple in-memory cache with TTL.
    
    For production, replace with Redis.
    """
    
    def __init__(self, max_size_mb: int = None):
        self.max_size_mb = max_size_mb or config.cache.max_cache_size_mb
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry:
                del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        async with self._lock:
            expires_at = time.time() + (ttl or config.cache.embedding_cache_ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            
            # Simple eviction if too many entries
            if len(self._cache) > 10000:
                self._evict_expired()
    
    async def delete(self, key: str):
        async with self._lock:
            self._cache.pop(key, None)
    
    def _evict_expired(self):
        now = time.time()
        self._cache = {
            k: v for k, v in self._cache.items() 
            if v.expires_at > now
        }

class EmbeddingCache:
    """Cache for text embeddings."""
    
    def __init__(self):
        self._cache = InMemoryCache()
    
    def _make_key(self, text: str, model: str) -> str:
        content = f"{model}:{text}"
        return f"emb:{hashlib.sha256(content.encode()).hexdigest()[:32]}"
    
    async def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        key = self._make_key(text, model)
        return await self._cache.get(key)
    
    async def set_embedding(self, text: str, model: str, embedding: List[float]):
        key = self._make_key(text, model)
        await self._cache.set(key, embedding, config.cache.embedding_cache_ttl)
    
    async def get_batch(
        self, 
        texts: List[str], 
        model: str
    ) -> Dict[str, Optional[List[float]]]:
        """Get cached embeddings for multiple texts."""
        results = {}
        for text in texts:
            results[text] = await self.get_embedding(text, model)
        return results

class QueryCache:
    """Cache for query results and rewrites."""
    
    def __init__(self):
        self._cache = InMemoryCache()
    
    def _make_key(self, query: str, user_id: str, params: dict) -> str:
        content = json.dumps({
            "query": query,
            "user_id": user_id,
            "params": sorted(params.items())
        }, sort_keys=True)
        return f"qry:{hashlib.sha256(content.encode()).hexdigest()[:32]}"
    
    async def get_results(
        self, 
        query: str, 
        user_id: str, 
        params: dict
    ) -> Optional[List[dict]]:
        key = self._make_key(query, user_id, params)
        return await self._cache.get(key)
    
    async def set_results(
        self, 
        query: str, 
        user_id: str, 
        params: dict, 
        results: List[dict]
    ):
        key = self._make_key(query, user_id, params)
        await self._cache.set(key, results, config.cache.query_cache_ttl)

# Global cache instances
embedding_cache = EmbeddingCache()
query_cache = QueryCache()

def get_embedding_cache() -> EmbeddingCache:
    return embedding_cache

def get_query_cache() -> QueryCache:
    return query_cache
