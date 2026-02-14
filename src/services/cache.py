"""
Redis caching service.
Implements cache-aside pattern with graceful degradation.
"""
import json
import logging
from typing import Optional

import redis
from redis.exceptions import RedisError

from src.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with connection pooling and error handling."""
    
    def __init__(self):
        """Initialize Redis connection pool."""
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis with error handling."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        except RedisError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache will be disabled.")
            self.redis_client = None
    
    def _get_cache_key(self, product_id: str) -> str:
        """Generate cache key for a product."""
        return f"product:{product_id}"
    
    def get_product_from_cache(self, product_id: str) -> Optional[dict]:
        """
        Retrieve a product from cache.
        Returns None on cache miss or error.
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(product_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache HIT for product: {product_id}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for product: {product_id}")
                return None
        except RedisError as e:
            logger.error(f"Redis GET error for {product_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for cached product {product_id}: {e}")
            return None
    
    def set_product_in_cache(self, product: dict, ttl_seconds: Optional[int] = None):
        """
        Store a product in cache with TTL.
        Logs errors but doesn't raise exceptions.
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(product["id"])
            ttl = ttl_seconds or settings.cache_ttl_seconds
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(product)
            )
            logger.info(f"Cached product {product['id']} with TTL {ttl}s")
        except RedisError as e:
            logger.error(f"Redis SET error for {product.get('id')}: {e}")
        except (TypeError, KeyError) as e:
            logger.error(f"Invalid product data for caching: {e}")
    
    def invalidate_product_cache(self, product_id: str):
        """
        Invalidate (delete) a product from cache.
        Used after updates or deletions.
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(product_id)
            deleted = self.redis_client.delete(cache_key)
            if deleted:
                logger.info(f"Invalidated cache for product: {product_id}")
            else:
                logger.debug(f"No cache entry to invalidate for product: {product_id}")
        except RedisError as e:
            logger.error(f"Redis DELETE error for {product_id}: {e}")
    
    def health_check(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False


# Global cache service instance
cache_service = CacheService()
