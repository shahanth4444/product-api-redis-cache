"""
Product data models.
Includes Pydantic models for API validation and SQLAlchemy models for database.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Pydantic Models for API
class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str = Field(..., min_length=1, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    stock_quantity: int = Field(..., ge=0, description="Stock quantity (non-negative)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Example Product",
                "description": "A detailed description of the product.",
                "price": 29.99,
                "stock_quantity": 100
            }
        }
    )


class ProductUpdate(BaseModel):
    """Schema for updating an existing product (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price": 34.99,
                "stock_quantity": 95
            }
        }
    )


class ProductResponse(BaseModel):
    """Schema for product responses."""
    id: str = Field(..., description="Unique product identifier (UUID)")
    name: str
    description: str
    price: float
    stock_quantity: int
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Example Product",
                "description": "A detailed description of the product.",
                "price": 29.99,
                "stock_quantity": 100
            }
        }
    )


# SQLAlchemy ORM Model
class ProductDB(Base):
    """Database model for products."""
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        """Convert database model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity
        }
