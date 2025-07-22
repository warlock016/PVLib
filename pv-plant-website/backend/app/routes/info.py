"""
System information API routes.

This module provides endpoints for system status, health checks,
and general API information.
"""

import sys
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, get_database_stats
from ..models.common import SuccessResponse, HealthStatus, SystemInfo
from ..config import settings

router = APIRouter()

# Start time for uptime calculation
start_time = time.time()


@router.get("/info", response_model=SuccessResponse)
async def get_system_info(db: AsyncSession = Depends(get_db)):
    """
    Get system information and status.
    
    Returns comprehensive system information including versions,
    status, and service availability.
    """
    try:
        # Get database statistics
        db_stats = await get_database_stats()
        
        # Check weather services (simplified check)
        weather_services = {
            "nsrdb": "available" if settings.NREL_API_KEY else "unavailable",
            "pvgis": "available"  # PVGIS doesn't require API key
        }
        
        # Get PVLib version
        try:
            import pvlib
            pvlib_version = pvlib.__version__
        except ImportError:
            pvlib_version = "not accessible"
        
        system_info = SystemInfo(
            api_version=settings.VERSION,
            pvlib_version=pvlib_version,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            system_status="healthy",
            uptime=time.time() - start_time,
            database_status="connected",
            weather_services=weather_services
        )
        
        return SuccessResponse(
            data=system_info.dict(),
            message="System information retrieved successfully"
        )
        
    except Exception as e:
        return SuccessResponse(
            data={
                "api_version": settings.VERSION,
                "system_status": "error",
                "error": str(e)
            },
            message="System information retrieved with errors"
        )


@router.get("/health", response_model=SuccessResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status for load balancers and monitoring systems.
    """
    health_status = HealthStatus(
        status="healthy",
        version=settings.VERSION,
        uptime=time.time() - start_time
    )
    
    return SuccessResponse(
        data=health_status.dict(),
        message="System is healthy"
    )


@router.get("/version")
async def get_version():
    """
    Get API version information.
    
    Returns simple version information.
    """
    return {
        "api_version": settings.VERSION,
        "app_name": settings.APP_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats", response_model=SuccessResponse)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """
    Get system statistics.
    
    Returns database statistics and system metrics.
    """
    try:
        db_stats = await get_database_stats()
        
        stats = {
            "database": db_stats,
            "uptime": time.time() - start_time,
            "settings": {
                "debug": settings.DEBUG,
                "max_concurrent_simulations": settings.MAX_CONCURRENT_SIMULATIONS,
                "weather_cache_enabled": settings.WEATHER_CACHE_ENABLED,
                "results_retention_days": settings.RESULTS_RETENTION_DAYS
            }
        }
        
        return SuccessResponse(
            data=stats,
            message="System statistics retrieved successfully"
        )
        
    except Exception as e:
        return SuccessResponse(
            data={"error": str(e)},
            message="Failed to retrieve system statistics"
        )