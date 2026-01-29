"""Cache service for content-addressed caching."""

import hashlib
import json
from pathlib import Path
from typing import Any

import diskcache

from mldata.models.config import CacheConfig
from mldata.utils.hashing import compute_hash


class CacheService:
    """Content-addressed cache for downloaded data."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize cache service.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self._cache: diskcache.Cache | None = None

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory."""
        return self.config.directory

    @property
    def cache(self) -> diskcache.Cache:
        """Get the cache instance."""
        if self._cache is None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache = diskcache.Cache(str(self.cache_dir), size_limit=self.config.max_size_gb * 1024**3)
        return self._cache

    def get_cache_key(self, source_uri: str, version: str | None = None, params: dict[str, Any] | None = None) -> str:
        """Generate a content-addressed cache key.

        Args:
            source_uri: Source URI of the dataset
            version: Optional version/revision
            params: Optional additional parameters

        Returns:
            SHA-256 hash as hex string
        """
        key_data = {
            "uri": source_uri,
            "version": version,
            "params": params or {},
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"sha256:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        if ttl:
            self.cache.set(key, value, expire=ttl)
        else:
            self.cache[key] = value

    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: Cache key
        """
        del self.cache[key]

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        return key in self.cache

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()

    def prune(self) -> int:
        """Prune expired entries.

        Returns:
            Number of entries pruned
        """
        # diskcache handles expiration automatically
        # This is a no-op but kept for interface consistency
        return 0

    @property
    def size_bytes(self) -> int:
        """Get the current cache size in bytes."""
        return self.cache.size

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size_bytes": self.size_bytes,
            "max_size_gb": self.config.max_size_gb,
            "entries": len(self.cache),
        }

    def close(self) -> None:
        """Close the cache."""
        if self._cache is not None:
            self._cache.close()
            self._cache = None


# Global cache instance
_cache_service: CacheService | None = None


def get_cache() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
