from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class APICache:
    def __init__(self, cache_duration_seconds: int = 60):
        self.cache: Dict[str, Any] = {}
        self.last_updated: Dict[str, datetime] = {}
        self.cache_duration = timedelta(seconds=cache_duration_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and is not expired."""
        if key in self.cache and key in self.last_updated:
            if datetime.now() - self.last_updated[key] < self.cache_duration:
                logger.debug(f"Cache hit for {key}")
                return self.cache[key]
            else:
                logger.debug(f"Cache expired for {key}")
                self.invalidate(key)
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache with current timestamp."""
        self.cache[key] = value
        self.last_updated[key] = datetime.now()
        logger.debug(f"Cache set for {key}")
    
    def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        self.cache.pop(key, None)
        self.last_updated.pop(key, None)
        logger.debug(f"Cache invalidated for {key}")
    
    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()
        self.last_updated.clear()
        logger.debug("Cache cleared")
    
    def get_last_updated(self, key: str) -> Optional[datetime]:
        """Get the last updated time for a key."""
        return self.last_updated.get(key)

# Create a global cache instance with 60 seconds duration
api_cache = APICache(60)  # Cache for 1 minute 