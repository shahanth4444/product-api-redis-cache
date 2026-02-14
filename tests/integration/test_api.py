"""
Integration tests for API endpoints.
Tests complete request/response cycle with real Redis.
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.cache import cache_service


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    # This will be executed before each test
    yield
    # Cleanup after test - try to flush Redis if available
    if cache_service.redis_client:
        try:
            cache_service.redis_client.flushdb()
        except:
            pass


class TestProductAPI:
    """Integration tests for Product API."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "redis" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_create_product_success(self, client):
        """Test successful product creation."""
        product_data = {
            "name": "Test Product",
            "description": "A test product description",
            "price": 49.99,
            "stock_quantity": 100
        }
        
        response = client.post("/products", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["name"] == product_data["name"]
        assert data["price"] == product_data["price"]
        assert data["stock_quantity"] == product_data["stock_quantity"]
    
    def test_create_product_invalid_data(self, client):
        """Test product creation with invalid data."""
        # Missing required fields
        response = client.post("/products", json={"name": "Test"})
        assert response.status_code == 422
        
        # Negative price
        response = client.post("/products", json={
            "name": "Test",
            "description": "Test",
            "price": -10,
            "stock_quantity": 10
        })
        assert response.status_code == 422
        
        # Negative stock
        response = client.post("/products", json={
            "name": "Test",
            "description": "Test",
            "price": 10,
            "stock_quantity": -5
        })
        assert response.status_code == 422
    
    def test_get_product_success(self, client):
        """Test successful product retrieval."""
        # Create a product first
        product_data = {
            "name": "Get Test Product",
            "description": "Product for GET test",
            "price": 29.99,
            "stock_quantity": 50
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get the product
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == product_data["name"]
    
    def test_get_product_not_found(self, client):
        """Test getting non-existent product."""
        response = client.get("/products/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_cache_hit_behavior(self, client):
        """Test cache hit behavior - critical caching test."""
        # Create a product
        product_data = {
            "name": "Cache Test Product",
            "description": "Testing cache behavior",
            "price": 99.99,
            "stock_quantity": 25
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # First GET - should be cache miss
        response1 = client.get(f"/products/{product_id}")
        assert response1.status_code == 200
        
        # Check if product is now in cache
        if cache_service.redis_client:
            cached = cache_service.get_product_from_cache(product_id)
            assert cached is not None
            assert cached["id"] == product_id
        
        # Second GET - should be cache hit
        response2 = client.get(f"/products/{product_id}")
        assert response2.status_code == 200
        assert response2.json() == response1.json()
    
    def test_update_product_success(self, client):
        """Test successful product update."""
        # Create a product
        product_data = {
            "name": "Update Test Product",
            "description": "Original description",
            "price": 19.99,
            "stock_quantity": 10
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update the product
        update_data = {
            "price": 24.99,
            "stock_quantity": 15
        }
        response = client.put(f"/products/{product_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["price"] == update_data["price"]
        assert data["stock_quantity"] == update_data["stock_quantity"]
        assert data["name"] == product_data["name"]  # Unchanged
    
    def test_update_product_not_found(self, client):
        """Test updating non-existent product."""
        update_data = {"price": 99.99}
        response = client.put("/products/non-existent-id", json=update_data)
        assert response.status_code == 404
    
    def test_cache_invalidation_on_update(self, client):
        """Test cache invalidation after update - critical caching test."""
        # Create and cache a product
        product_data = {
            "name": "Invalidation Test",
            "description": "Testing cache invalidation",
            "price": 50.00,
            "stock_quantity": 20
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # GET to populate cache
        client.get(f"/products/{product_id}")
        
        # Verify it's cached
        if cache_service.redis_client:
            cached_before = cache_service.get_product_from_cache(product_id)
            assert cached_before is not None
        
        # Update the product
        update_data = {"price": 75.00}
        client.put(f"/products/{product_id}", json=update_data)
        
        # Verify cache was invalidated
        if cache_service.redis_client:
            cached_after = cache_service.get_product_from_cache(product_id)
            assert cached_after is None
        
        # GET again should fetch from database and re-cache
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["price"] == 75.00
    
    def test_delete_product_success(self, client):
        """Test successful product deletion."""
        # Create a product
        product_data = {
            "name": "Delete Test Product",
            "description": "Will be deleted",
            "price": 9.99,
            "stock_quantity": 5
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete the product
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_delete_product_not_found(self, client):
        """Test deleting non-existent product."""
        response = client.delete("/products/non-existent-id")
        assert response.status_code == 404
    
    def test_cache_invalidation_on_delete(self, client):
        """Test cache invalidation after delete - critical caching test."""
        # Create and cache a product
        product_data = {
            "name": "Delete Cache Test",
            "description": "Testing cache invalidation on delete",
            "price": 15.00,
            "stock_quantity": 8
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # GET to populate cache
        client.get(f"/products/{product_id}")
        
        # Verify it's cached
        if cache_service.redis_client:
            cached_before = cache_service.get_product_from_cache(product_id)
            assert cached_before is not None
        
        # Delete the product
        client.delete(f"/products/{product_id}")
        
        # Verify cache was invalidated
        if cache_service.redis_client:
            cached_after = cache_service.get_product_from_cache(product_id)
            assert cached_after is None
        
        # GET should return 404
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 404
    
    def test_partial_update(self, client):
        """Test partial product update."""
        # Create a product
        product_data = {
            "name": "Partial Update Test",
            "description": "Original description",
            "price": 100.00,
            "stock_quantity": 50
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update only price
        update_data = {"price": 120.00}
        response = client.put(f"/products/{product_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["price"] == 120.00
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["stock_quantity"] == product_data["stock_quantity"]
