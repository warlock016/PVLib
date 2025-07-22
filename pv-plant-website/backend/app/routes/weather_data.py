"""
Weather data API routes.

This module provides endpoints for weather data retrieval and validation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.weather_data import WeatherDataResponse, WeatherServiceTestResponse
from ..models.common import SuccessResponse
from ..services.weather_service import weather_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/weather/{latitude}/{longitude}", response_model=WeatherDataResponse)
async def get_weather_data(
    latitude: float,
    longitude: float,
    year: int = None,
    source: str = "auto",
    db: AsyncSession = Depends(get_db)
):
    """
    Get weather data for a specific location.
    
    Retrieves weather data from NREL NSRDB or PVGIS based on location and availability.
    """
    try:
        # Validate coordinates
        if not -90 <= latitude <= 90:
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
        
        # Get weather data from weather service
        logger.info(f"Requesting weather data for {latitude}, {longitude}")
        
        weather_data = await weather_service.get_weather_data(
            latitude=latitude,
            longitude=longitude,
            year=year,
            source=source,
            db=db
        )
        
        # Determine success message based on data source
        if weather_data.get('source') == 'mock':
            message = "Weather data retrieved successfully (mock data - connector unavailable)"
        else:
            message = f"Weather data retrieved successfully from {weather_data.get('source', 'unknown')}"
        
        return WeatherDataResponse(
            data=weather_data,
            message=message
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in weather data endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching weather data")


@router.get("/weather/test", response_model=WeatherServiceTestResponse)
async def test_weather_services(db: AsyncSession = Depends(get_db)):
    """
    Test weather service connections.
    
    Checks the availability of NREL NSRDB and PVGIS services.
    """
    try:
        # Test weather service connections
        logger.info("Testing weather service connections")
        
        test_results = await weather_service.test_connection()
        service_status = weather_service.get_service_status()
        
        # Build response data
        response_data = {
            "service_status": service_status,
            "connection_tests": test_results
        }
        
        # Determine message based on results
        if test_results.get("connector_available"):
            message = "Weather service connection tests completed"
        else:
            message = "Weather service connection tests completed (connector unavailable)"
        
        return WeatherServiceTestResponse(
            data=response_data,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))