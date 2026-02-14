"""
API route definitions.
RESTful endpoints for product management.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

from src.models.product import ProductCreate, ProductUpdate, ProductResponse
from src.services.product import product_service
from src.services.cache import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product with the provided details"
)
async def create_product(product: ProductCreate) -> ProductResponse:
    """Create a new product."""
    try:
        return product_service.create_product(product)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Retrieve a product by its unique identifier. Uses caching for improved performance."
)
async def get_product(product_id: str) -> ProductResponse:
    """Get a product by ID (with caching)."""
    try:
        product = product_service.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product by ID",
    description="Update an existing product. Automatically invalidates cache."
)
async def update_product(product_id: str, product: ProductUpdate) -> ProductResponse:
    """Update a product by ID (invalidates cache)."""
    try:
        updated_product = product_service.update_product(product_id, product)
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        return updated_product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product by ID",
    description="Delete a product. Automatically invalidates cache."
)
async def delete_product(product_id: str):
    """Delete a product by ID (invalidates cache)."""
    try:
        success = product_service.delete_product(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


# Health check router
health_router = APIRouter(tags=["health"])


@health_router.get(
    "/health",
    summary="Health check",
    description="Check API and Redis health status"
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Docker."""
    redis_healthy = cache_service.health_check()
    return {
        "status": "healthy",
        "redis": redis_healthy
    }
