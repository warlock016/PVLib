"""
FastAPI main application for PV Plant Modeling Website.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the PV plant modeling and simulation system.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Parent directory path for shared modules (if needed)
# sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import init_db
from app.routes import (
    system_config,
    weather_data,
    simulation,
    results,
    export,
    info
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting PV Plant Modeling API...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PV Plant Modeling API...")


# Create FastAPI application
app = FastAPI(
    title="PV Plant Modeling API",
    description="API for photovoltaic plant modeling and simulation using PVLib",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "details": {"type": type(exc).__name__} if settings.DEBUG else {}
        }
    )


# Include API routes
app.include_router(system_config.router, prefix="/api", tags=["System Configuration"])
app.include_router(weather_data.router, prefix="/api", tags=["Weather Data"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])
app.include_router(results.router, prefix="/api", tags=["Results"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(info.router, prefix="/api", tags=["System Info"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PV Plant Modeling API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }


# Mount static files for development
if settings.DEBUG:
    static_path = Path(__file__).parent.parent / "frontend" / "build"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )