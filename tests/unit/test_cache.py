"""
Unit tests for cache service.
Tests Redis caching functionality with mocking.
"""
import json
from unittest.mock import Mock, patch

import pytest
from redis.exceptions import RedisError

from src.services.cache import CacheService


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('src.services.cache.redis.Redis') as mock:
        yield mock


class TestCacheService:
    """Test suite for CacheService."""
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        service = CacheService()
        key = service._get_cache_key("test-id-123")
        assert key == "product:test-id-123"
    
    def test_get_product_from_cache_hit(self, mock_redis):
        """Test successful cache hit."""
        # Setup
        service = CacheService()
        product_data = {
            "id": "test-id",
            "name": "Test Product",
            "price": 99.99
        }
        service.redis_client = Mock()
        service.redis_client.get.return_value = json.dumps(product_data)
        
        # Execute
        result = service.get_product_from_cache("test-id")
        
        # Assert
        assert result == product_data
        service.redis_client.get.assert_called_once_with("product:test-id")
    
    def test_get_product_from_cache_miss(self, mock_redis):
        """Test cache miss."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.get.return_value = None
        
        # Execute
        result = service.get_product_from_cache("test-id")
        
        # Assert
        assert result is None
    
    def test_get_product_from_cache_redis_error(self, mock_redis):
        """Test graceful handling of Redis errors."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.get.side_effect = RedisError("Connection failed")
        
        # Execute
        result = service.get_product_from_cache("test-id")
        
        # Assert - should return None, not raise exception
        assert result is None
    
    def test_get_product_from_cache_no_client(self):
        """Test behavior when Redis client is unavailable."""
        # Setup
        service = CacheService()
        service.redis_client = None
        
        # Execute
        result = service.get_product_from_cache("test-id")
        
        # Assert
        assert result is None
    
    def test_set_product_in_cache_success(self, mock_redis):
        """Test successful cache set."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        product_data = {
            "id": "test-id",
            "name": "Test Product",
            "price": 99.99
        }
        
        # Execute
        service.set_product_in_cache(product_data, ttl_seconds=300)
        
        # Assert
        service.redis_client.setex.assert_called_once_with(
            "product:test-id",
            300,
            json.dumps(product_data)
        )
    
    def test_set_product_in_cache_redis_error(self, mock_redis):
        """Test graceful handling of Redis errors on set."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.setex.side_effect = RedisError("Connection failed")
        product_data = {"id": "test-id", "name": "Test"}
        
        # Execute - should not raise exception
        service.set_product_in_cache(product_data)
        
        # No assertion needed - just verify no exception raised
    
    def test_invalidate_product_cache_success(self, mock_redis):
        """Test successful cache invalidation."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.delete.return_value = 1
        
        # Execute
        service.invalidate_product_cache("test-id")
        
        # Assert
        service.redis_client.delete.assert_called_once_with("product:test-id")
    
    def test_invalidate_product_cache_not_found(self, mock_redis):
        """Test invalidation when key doesn't exist."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.delete.return_value = 0
        
        # Execute - should not raise exception
        service.invalidate_product_cache("test-id")
        
        # Assert
        service.redis_client.delete.assert_called_once()
    
    def test_health_check_healthy(self, mock_redis):
        """Test health check when Redis is healthy."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.ping.return_value = True
        
        # Execute
        result = service.health_check()
        
        # Assert
        assert result is True
    
    def test_health_check_unhealthy(self, mock_redis):
        """Test health check when Redis is unhealthy."""
        # Setup
        service = CacheService()
        service.redis_client = Mock()
        service.redis_client.ping.side_effect = RedisError("Connection failed")
        
        # Execute
        result = service.health_check()
        
        # Assert
        assert result is False
    
    def test_health_check_no_client(self):
        """Test health check when Redis client is unavailable."""
        # Setup
        service = CacheService()
        service.redis_client = None
        
        # Execute
        result = service.health_check()
        
        # Assert
        assert result is False
