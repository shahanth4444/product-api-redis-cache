"""
Product business logic service.
Orchestrates database and cache operations.
"""
import logging
from typing import Optional

from src.models.product import ProductCreate, ProductUpdate, ProductResponse
from src.services import database
from src.services.cache import cache_service

logger = logging.getLogger(__name__)


class ProductService:
    """Business logic for product operations."""
    
    @staticmethod
    def get_product(product_id: str) -> Optional[ProductResponse]:
        """
        Get a product by ID using cache-aside pattern.
        1. Check cache first
        2. On miss, query database
        3. Store in cache
        4. Return product
        """
        # Try cache first
        cached_product = cache_service.get_product_from_cache(product_id)
        if cached_product:
            return ProductResponse(**cached_product)
        
        # Cache miss - query database
        db_product = database.get_product_by_id(product_id)
        if not db_product:
            return None
        
        # Convert to response model
        product_dict = db_product.to_dict()
        
        # Store in cache for future requests
        cache_service.set_product_in_cache(product_dict)
        
        return ProductResponse(**product_dict)
    
    @staticmethod
    def create_product(product_data: ProductCreate) -> ProductResponse:
        """
        Create a new product.
        No caching on creation (will be cached on first GET).
        """
        db_product = database.create_product(product_data)
        return ProductResponse(**db_product.to_dict())
    
    @staticmethod
    def update_product(product_id: str, product_data: ProductUpdate) -> Optional[ProductResponse]:
        """
        Update a product and invalidate cache.
        1. Update database
        2. Invalidate cache entry
        3. Return updated product
        """
        db_product = database.update_product(product_id, product_data)
        if not db_product:
            return None
        
        # Invalidate cache to ensure consistency
        cache_service.invalidate_product_cache(product_id)
        
        return ProductResponse(**db_product.to_dict())
    
    @staticmethod
    def delete_product(product_id: str) -> bool:
        """
        Delete a product and invalidate cache.
        1. Delete from database
        2. Invalidate cache entry
        """
        success = database.delete_product(product_id)
        if success:
            # Invalidate cache
            cache_service.invalidate_product_cache(product_id)
        
        return success


# Global service instance
product_service = ProductService()
