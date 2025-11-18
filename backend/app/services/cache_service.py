"""Simple in-memory cache service for reports and frequently accessed data."""

from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
from loguru import logger


class CacheEntry:
    """Cache entry with value and expiration."""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()


class ReportCache:
    """
    Simple in-memory cache for reports and frequently accessed data.

    Usage:
        cache = ReportCache()

        # Manual caching
        cache.set("report_key", data, ttl_seconds=3600)
        data = cache.get("report_key")

        # Decorator caching
        @cache.cached(ttl_seconds=3600)
        async def get_expensive_report(param1, param2):
            # ... expensive computation
            return result
    """

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, key: str, *args, **kwargs) -> str:
        """
        Generate cache key from function name and arguments.

        Args:
            key: Base key
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        if not args and not kwargs:
            return key

        # Create deterministic key from arguments
        key_data = {
            "base": key,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }

        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()[:8]

        return f"{key}:{key_hash}"

    def get(self, key: str, *args, **kwargs) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            args: Additional arguments for key generation
            kwargs: Additional keyword arguments for key generation

        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._make_key(key, *args, **kwargs)

        entry = self._cache.get(cache_key)

        if entry is None:
            self._misses += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None

        if entry.is_expired():
            self._misses += 1
            logger.debug(f"Cache expired: {cache_key} (age: {entry.age_seconds():.1f}s)")
            del self._cache[cache_key]
            return None

        self._hits += 1
        logger.debug(f"Cache hit: {cache_key} (age: {entry.age_seconds():.1f}s)")
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 3600, *args, **kwargs) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
            args: Additional arguments for key generation
            kwargs: Additional keyword arguments for key generation
        """
        cache_key = self._make_key(key, *args, **kwargs)

        self._cache[cache_key] = CacheEntry(value, ttl_seconds)
        logger.debug(f"Cache set: {cache_key} (TTL: {ttl_seconds}s)")

    def delete(self, key: str, *args, **kwargs) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key
            args: Additional arguments for key generation
            kwargs: Additional keyword arguments for key generation

        Returns:
            True if key was deleted, False if not found
        """
        cache_key = self._make_key(key, *args, **kwargs)

        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug(f"Cache delete: {cache_key}")
            return True

        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests
        }

    def cached(self, ttl_seconds: int = 3600, key_prefix: str = None):
        """
        Decorator for caching function results.

        Args:
            ttl_seconds: Time to live in seconds (default: 1 hour)
            key_prefix: Optional key prefix (defaults to function name)

        Usage:
            @cache.cached(ttl_seconds=3600)
            async def get_report(param1, param2):
                # ... expensive computation
                return result
        """
        def decorator(func: Callable):
            cache_key = key_prefix or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Try to get from cache
                cached_value = self.get(cache_key, *args, **kwargs)
                if cached_value is not None:
                    return cached_value

                # Compute and cache
                result = await func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds, *args, **kwargs)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Try to get from cache
                cached_value = self.get(cache_key, *args, **kwargs)
                if cached_value is not None:
                    return cached_value

                # Compute and cache
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds, *args, **kwargs)
                return result

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator


# Global cache instance
report_cache = ReportCache()


# Cache invalidation helpers
def invalidate_bike_cache(bicycle_id: str) -> None:
    """Invalidate all cache entries related to a specific bike."""
    report_cache.delete(f"bike_detail:{bicycle_id}")
    report_cache.delete(f"bike_cost_summary:{bicycle_id}")
    report_cache.delete(f"bike_history:{bicycle_id}")
    logger.debug(f"Invalidated cache for bike: {bicycle_id}")


def invalidate_report_cache(report_type: str) -> None:
    """Invalidate all cache entries for a specific report type."""
    # For now, clear all - in production, use pattern matching
    report_cache.clear()
    logger.debug(f"Invalidated cache for report: {report_type}")
