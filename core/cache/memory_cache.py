"""In-memory LRU cache for Kolibri AI.

Provides lightweight caching with TTL support and automatic eviction.

Principles:
- Легкость: Minimal memory overhead with configurable limits
- Точность: Type-safe cache operations
- Энергоэффективность: Reduces redundant computations
"""

import time
from collections import OrderedDict
from typing import Any, Callable, Optional, TypeVar, Generic, Dict
from functools import wraps
import hashlib
import pickle


T = TypeVar('T')


class CacheEntry(Generic[T]):
    """Represents a cached value with metadata."""
    
    __slots__ = ('value', 'timestamp', 'hit_count')
    
    def __init__(self, value: T) -> None:
        self.value = value
        self.timestamp = time.time()
        self.hit_count = 0
    
    def is_expired(self, ttl: float) -> bool:
        """Check if entry has exceeded TTL."""
        return (time.time() - self.timestamp) > ttl
    
    def record_hit(self) -> None:
        """Record cache hit."""
        self.hit_count += 1


class LRUCache(Generic[T]):
    """LRU cache with TTL support.
    
    Features:
    - Automatic eviction of least recently used items
    - Time-to-live (TTL) expiration
    - Hit/miss statistics
    - Configurable size limits
    
    Note:
        This implementation is NOT thread-safe. Use external synchronization
        (e.g., threading.Lock) if accessing from multiple threads.
    
    Example:
        >>> cache = LRUCache[str](max_size=100, ttl=3600)
        >>> cache.set("key", "value")
        >>> value = cache.get("key")
        >>> print(cache.stats())
    """
    
    def __init__(self, max_size: int = 1000, ttl: float = 3600.0) -> None:
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[T]:
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        if self._ttl > 0 and entry.is_expired(self._ttl):
            del self._cache[key]
            self._misses += 1
            return None
        
        self._cache.move_to_end(key)
        entry.record_hit()
        self._hits += 1
        
        return entry.value
    
    def set(self, key: str, value: T) -> None:
        if key in self._cache:
            del self._cache[key]
        
        self._cache[key] = CacheEntry(value)
        
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
    
    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'ttl': self._ttl,
        }


def make_cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate cache key from function arguments.
    
    Raises:
        TypeError: If arguments cannot be serialized
    """
    try:
        key_data = pickle.dumps((args, sorted(kwargs.items())))
        return hashlib.sha256(key_data).hexdigest()
    except (pickle.PicklingError, TypeError) as e:
        # Cannot pickle - raise error instead of unsafe fallback
        raise TypeError(
            f"Cannot create cache key: arguments are not picklable. "
            f"Error: {e}"
        ) from e


def cached(
    ttl: float = 3600.0,
    max_size: int = 1000,
    key_func: Optional[Callable[..., str]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results."""
    cache: LRUCache[T] = LRUCache(max_size=max_size, ttl=ttl)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func is not None:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        wrapper.cache = cache  # type: ignore
        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_stats = cache.stats  # type: ignore
        
        return wrapper
    
    return decorator
