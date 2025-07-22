"""
Weather service for integrating NREL weather data connector.

This service provides an interface between the FastAPI backend and the
NREL weather data connector, handling data transformation and caching.
"""

import sys
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.weather_data import WeatherDataResponse, WeatherDataQuality
from ..config import settings
from ..database import WeatherData, AsyncSessionLocal

logger = logging.getLogger(__name__)

# Import simplified weather connector
try:
    from .nrel_weather_connector import SimpleWeatherConnector
    logger.info("Successfully imported simplified weather connector")
except ImportError as e:
    logger.error(f"Failed to import weather connector: {e}")
    SimpleWeatherConnector = None


class WeatherService:
    """
    Service class for weather data operations.
    
    Provides methods for fetching, caching, and validating weather data
    from multiple sources using the NREL weather connector.
    """
    
    def __init__(self):
        """Initialize the weather service."""
        self.connector = None
        
        # Initialize weather connector if available
        if SimpleWeatherConnector:
            try:
                self.connector = SimpleWeatherConnector()
                logger.info("Weather connector initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize weather connector: {e}")
                self.connector = None
        else:
            logger.warning("Weather connector not available - using mock data")
    
    async def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None,
        source: str = "auto",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Get weather data for a specific location.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float  
            Longitude in decimal degrees
        year : int, optional
            Year for weather data. If None, uses TMY data
        source : str, default "auto"
            Weather data source preference
            
        Returns
        -------
        dict
            Weather data response with metadata
        """
        try:
            # Validate coordinates
            if not -90 <= latitude <= 90:
                raise ValueError("Latitude must be between -90 and 90 degrees")
            if not -180 <= longitude <= 180:
                raise ValueError("Longitude must be between -180 and 180 degrees")
            
            # Check cache first
            cached_data = await self._get_cached_weather_data(
                latitude, longitude, year, db
            )
            if cached_data:
                logger.info("Returning cached weather data")
                cached_data['cache_hit'] = True
                return cached_data
            
            if self.connector is None:
                logger.warning("Weather connector not available, returning mock data")
                return self._get_mock_weather_data(latitude, longitude, year)
            
            # Get weather data from connector
            logger.info(f"Fetching weather data for {latitude}, {longitude}")
            
            if year is None:
                # Use TMY data
                weather_data = self.connector.get_weather_data(
                    latitude=latitude,
                    longitude=longitude,
                    use_tmy=True
                )
            else:
                # Use specific year
                weather_data = self.connector.get_weather_data(
                    latitude=latitude,
                    longitude=longitude,
                    year=year,
                    use_tmy=False
                )
            
            # Transform data to API response format
            response_data = self._transform_weather_data(
                weather_data, latitude, longitude, year
            )
            
            # Cache the data
            await self._cache_weather_data(
                latitude, longitude, year, response_data, db
            )
            
            logger.info(f"Successfully retrieved weather data from {response_data['source']}")
            return response_data
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            logger.info("Falling back to mock data")
            # Return mock data as fallback
            return self._get_mock_weather_data(latitude, longitude, year)
    
    def _transform_weather_data(
        self, 
        weather_data: Dict[str, Any], 
        latitude: float, 
        longitude: float, 
        year: Optional[int]
    ) -> Dict[str, Any]:
        """
        Transform weather connector data to API response format.
        
        Parameters
        ----------
        weather_data : dict
            Raw weather data from connector
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Year for weather data
            
        Returns
        -------
        dict
            Transformed data for API response
        """
        # Extract metadata
        metadata = weather_data.get('metadata', {})
        data_df = weather_data.get('data')
        
        # Calculate data quality metrics
        if data_df is not None:
            total_points = len(data_df)
            valid_points = data_df.dropna().shape[0]
            coverage = (valid_points / total_points * 100) if total_points > 0 else 0
            
            # Calculate average values for quality assessment
            avg_ghi = data_df['ghi'].mean() if 'ghi' in data_df.columns else 0
            avg_temp = data_df['temp_air'].mean() if 'temp_air' in data_df.columns else 0
            avg_wind = data_df['wind_speed'].mean() if 'wind_speed' in data_df.columns else 0
        else:
            coverage = 0
            avg_ghi = avg_temp = avg_wind = 0
        
        # Build response
        response = {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": metadata.get('elevation', 0),
                "timezone": metadata.get('timezone', 'UTC'),
                "country": metadata.get('country', 'Unknown'),
                "state": metadata.get('state', 'Unknown')
            },
            "source": metadata.get('source', 'unknown'),
            "year": year if year else metadata.get('year', 'TMY'),
            "data_quality": {
                "coverage": round(coverage, 1),
                "source_quality": metadata.get('quality', 'unknown'),
                "missing_data_filled": metadata.get('missing_filled', False),
                "validation_passed": coverage > 90  # Consider good if >90% coverage
            },
            "weather_summary": {
                "annual_ghi": round(avg_ghi * 8760, 1) if avg_ghi > 0 else 0,
                "average_temperature": round(avg_temp, 1),
                "average_wind_speed": round(avg_wind, 1),
                "data_points": total_points if data_df is not None else 0
            },
            "last_updated": datetime.now().isoformat(),
            "cache_hit": metadata.get('cache_hit', False)
        }
        
        return response
    
    def _get_mock_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        year: Optional[int]
    ) -> Dict[str, Any]:
        """
        Generate mock weather data when connector is not available.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees  
        year : int, optional
            Year for weather data
            
        Returns
        -------
        dict
            Mock weather data response
        """
        logger.info("Generating mock weather data")
        
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": 1650,
                "timezone": "UTC",
                "country": "Mock",
                "state": "Mock"
            },
            "source": "mock",
            "year": year or "TMY",
            "data_quality": {
                "coverage": 99.8,
                "source_quality": "good",
                "missing_data_filled": False,
                "validation_passed": True
            },
            "weather_summary": {
                "annual_ghi": 1800.0,
                "average_temperature": 15.0,
                "average_wind_speed": 4.2,
                "data_points": 8760
            },
            "last_updated": datetime.now().isoformat(),
            "cache_hit": False
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test weather service connections.
        
        Returns
        -------
        dict
            Connection test results
        """
        results = {
            "connector_available": self.connector is not None,
            "sources": {}
        }
        
        if self.connector:
            try:
                # Test connection to weather sources
                test_results = self.connector.test_connection()
                results["sources"] = test_results
                logger.info("Weather service connection test completed")
            except Exception as e:
                logger.error(f"Weather service connection test failed: {e}")
                results["error"] = str(e)
        else:
            results["sources"] = {
                "nsrdb": "unavailable",
                "pvgis": "unavailable"
            }
            results["error"] = "Weather connector not initialized"
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status.
        
        Returns
        -------
        dict
            Service status information
        """
        return {
            "connector_initialized": self.connector is not None,
            "pvlib_available": bool(self.connector and self.connector.pvlib_available) if self.connector else False,
            "nrel_api_key_configured": bool(
                self.connector and self.connector.nrel_api_key
            ) if self.connector else False,
            "cache_enabled": True,  # Database caching is always enabled
            "cache_directory": "database"
        }
    
    def _generate_cache_key(self, latitude: float, longitude: float, year: Optional[int]) -> str:
        """
        Generate a cache key for weather data.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Year for weather data
            
        Returns
        -------
        str
            Cache key
        """
        # Round coordinates to 4 decimal places (~11m precision)
        lat_rounded = round(latitude, 4)
        lon_rounded = round(longitude, 4)
        year_str = str(year) if year else "TMY"
        
        # Create cache key
        cache_string = f"{lat_rounded}_{lon_rounded}_{year_str}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int],
        db: Optional[AsyncSession] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached weather data from database.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Year for weather data
        db : AsyncSession, optional
            Database session
            
        Returns
        -------
        dict or None
            Cached weather data if found and not expired
        """
        try:
            # Use provided session or create new one
            if db is None:
                async with AsyncSessionLocal() as db:
                    return await self._get_cached_weather_data(latitude, longitude, year, db)
            
            cache_key = self._generate_cache_key(latitude, longitude, year)
            
            # Query for cached data
            from sqlalchemy import select
            result = await db.execute(
                select(WeatherData).where(
                    and_(
                        WeatherData.id == cache_key,
                        WeatherData.expires_at > datetime.utcnow()
                    )
                )
            )
            
            cached_record = result.scalar_one_or_none()
            
            if cached_record:
                logger.info(f"Found cached weather data for {latitude}, {longitude}")
                return cached_record.data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached weather data: {e}")
            return None
    
    async def _cache_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int],
        data: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> None:
        """
        Cache weather data in database.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Year for weather data
        data : dict
            Weather data to cache
        db : AsyncSession, optional
            Database session
        """
        try:
            # Use provided session or create new one
            if db is None:
                async with AsyncSessionLocal() as db:
                    await self._cache_weather_data(latitude, longitude, year, data, db)
                    return
            
            cache_key = self._generate_cache_key(latitude, longitude, year)
            
            # Set expiration time (30 days from now)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Create weather data record
            weather_record = WeatherData(
                id=cache_key,
                latitude=latitude,
                longitude=longitude,
                source=data.get('source', 'unknown'),
                year=year,
                data_quality=data.get('data_quality', {}),
                data=data,
                expires_at=expires_at
            )
            
            # Insert or update cached data
            await db.merge(weather_record)
            await db.commit()
            
            logger.info(f"Cached weather data for {latitude}, {longitude}")
            
        except Exception as e:
            logger.error(f"Error caching weather data: {e}")
            # Don't raise - caching failure shouldn't break the request


# Global weather service instance
weather_service = WeatherService()