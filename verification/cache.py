"""
Thread-Safe Async LRU Cache for verification results.

Caches NLI verification results so repeated facts (common in multi-caller
scenarios where callers confirm the same information) return instantly
without re-running Gemini NLI calls.

Thread-safe via asyncio.Lock for concurrent agent access.
"""
import time
import logging
import asyncio
from collections import OrderedDict
from typing import Optional

from verification.models import VerificationResult, CacheStats

logger = logging.getLogger("nexus911.verifylayer.cache")


class AsyncLRUCache:
    """
    Thread-safe async LRU cache for VerificationResult objects.

    Key: fact content hash (fact_id)
    Value: VerificationResult

    Uses asyncio.Lock to ensure thread safety when multiple
    concurrent agents verify facts simultaneously.
    """

    def __init__(self, max_size: int = 1024, ttl_seconds: float = 300.0):
        """
        Args:
            max_size: Maximum number of cached verification results.
            ttl_seconds: Time-to-live for cache entries. Default 5 minutes.
        """
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[VerificationResult, float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    async def get(self, fact_id: str) -> Optional[VerificationResult]:
        """
        Retrieve a cached verification result.

        Returns None on miss or expired entry. Moves hit to end (most recent).
        """
        async with self._lock:
            if fact_id not in self._cache:
                self._stats["misses"] += 1
                return None

            result, cached_at = self._cache[fact_id]

            # Check TTL expiry
            if time.time() - cached_at > self._ttl:
                del self._cache[fact_id]
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(fact_id)
            self._stats["hits"] += 1

            # Mark as cache hit
            cached_result = result.model_copy()
            cached_result.from_cache = True
            return cached_result

    async def put(self, fact_id: str, result: VerificationResult):
        """
        Store a verification result in cache.

        Evicts oldest entry if at capacity.
        """
        async with self._lock:
            # If already exists, update and move to end
            if fact_id in self._cache:
                self._cache.move_to_end(fact_id)
                self._cache[fact_id] = (result, time.time())
                return

            # Evict if at capacity
            while len(self._cache) >= self._max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                self._stats["evictions"] += 1
                logger.debug(f"Cache eviction: {evicted_key}")

            self._cache[fact_id] = (result, time.time())

    async def invalidate(self, fact_id: str) -> bool:
        """Remove a specific entry from cache. Returns True if found."""
        async with self._lock:
            if fact_id in self._cache:
                del self._cache[fact_id]
                return True
            return False

    async def invalidate_incident(self, incident_id: str) -> int:
        """
        Remove all cached results for an incident.
        Returns count of invalidated entries.
        """
        async with self._lock:
            to_remove = [
                key for key, (result, _) in self._cache.items()
                if result.fact.incident_id == incident_id
            ]
            for key in to_remove:
                del self._cache[key]
            return len(to_remove)

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    async def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        async with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0.0
            return CacheStats(
                hits=self._stats["hits"],
                misses=self._stats["misses"],
                size=len(self._cache),
                max_size=self._max_size,
                hit_rate=round(hit_rate, 4),
                evictions=self._stats["evictions"],
            )

    async def cleanup_expired(self):
        """Remove all expired entries. Call periodically."""
        async with self._lock:
            now = time.time()
            expired = [
                key for key, (_, cached_at) in self._cache.items()
                if now - cached_at > self._ttl
            ]
            for key in expired:
                del self._cache[key]
            if expired:
                logger.debug(f"Cleaned up {len(expired)} expired cache entries")
            return len(expired)
