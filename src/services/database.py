"""
Database service layer.
Handles all database operations with SQLAlchemy.
"""
import logging
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings
from src.models.product import Base, ProductDB, ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables and seed initial data."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Seed initial products if database is empty
    with get_db_session() as session:
        count = session.query(ProductDB).count()
        if count == 0:
            logger.info("Seeding initial products...")
            initial_products = [
                ProductDB(
                    name="Wireless Headphones",
                    description="High-quality wireless headphones with noise cancellation",
                    price=99.99,
                    stock_quantity=50
                ),
                ProductDB(
                    name="Smart Watch",
                    description="Fitness tracking smartwatch with heart rate monitor",
                    price=199.99,
                    stock_quantity=30
                ),
                ProductDB(
                    name="Laptop Stand",
                    description="Ergonomic aluminum laptop stand for better posture",
                    price=49.99,
                    stock_quantity=100
                ),
                ProductDB(
                    name="USB-C Hub",
                    description="7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader",
                    price=39.99,
                    stock_quantity=75
                ),
                ProductDB(
                    name="Mechanical Keyboard",
                    description="RGB mechanical keyboard with blue switches",
                    price=129.99,
                    stock_quantity=40
                )
            ]
            session.add_all(initial_products)
            session.commit()
            logger.info(f"Seeded {len(initial_products)} products")
        else:
            logger.info(f"Database already contains {count} products")


def get_product_by_id(product_id: str) -> Optional[ProductDB]:
    """Retrieve a product by ID from the database."""
    with get_db_session() as session:
        return session.query(ProductDB).filter(ProductDB.id == product_id).first()


def create_product(product_data: ProductCreate) -> ProductDB:
    """Create a new product in the database."""
    with get_db_session() as session:
        db_product = ProductDB(**product_data.model_dump())
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        logger.info(f"Created product: {db_product.id}")
        return db_product


def update_product(product_id: str, product_data: ProductUpdate) -> Optional[ProductDB]:
    """Update an existing product in the database."""
    with get_db_session() as session:
        db_product = session.query(ProductDB).filter(ProductDB.id == product_id).first()
        if not db_product:
            return None
        
        # Update only provided fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        session.commit()
        session.refresh(db_product)
        logger.info(f"Updated product: {product_id}")
        return db_product


def delete_product(product_id: str) -> bool:
    """Delete a product from the database."""
    with get_db_session() as session:
        db_product = session.query(ProductDB).filter(ProductDB.id == product_id).first()
        if not db_product:
            return False
        
        session.delete(db_product)
        session.commit()
        logger.info(f"Deleted product: {product_id}")
        return True
