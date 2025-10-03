"""Redis cache service for report caching."""
import json
from typing import Optional, Any
from redis import Redis, ConnectionError as RedisConnectionError
from config import config


class CacheService:
    """Service for Redis caching operations."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = None):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL
            ttl: Default time-to-live for cache entries in seconds
        """
        self.redis_url = redis_url or config.REDIS_URL
        self.ttl = ttl or config.CACHE_TTL
        self.client: Optional[Redis] = None
    
    def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.client = Redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=5)
            # Test connection
            self.client.ping()
        except (RedisConnectionError, Exception) as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            self.client.close()
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            ttl = ttl or self.ttl
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "report:user123:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def invalidate_user_reports(self, user_id: str) -> int:
        """
        Invalidate all cached reports for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of cache entries invalidated
        """
        return self.delete_pattern(f"report:{user_id}:*")
    
    def get_report_cache_key(self, user_id: str, start_date: str, end_date: str) -> str:
        """
        Generate cache key for a report.
        
        Args:
            user_id: User ID
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Cache key
        """
        return f"report:{user_id}:{start_date}:{end_date}"


# Global cache service instance
cache_service = CacheService()
