"""
FastAPI application entry point.
High-performance Product API with Redis caching.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.config import settings
from src.api.routes import router, health_router
from src.services.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Product API...")
    init_db()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Shutting down Product API...")


# Create FastAPI application
app = FastAPI(
    title="Product API with Redis Caching",
    description="High-performance RESTful API for product catalog management with Redis caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Product API with Redis Caching",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
        log_level="info"
    )
