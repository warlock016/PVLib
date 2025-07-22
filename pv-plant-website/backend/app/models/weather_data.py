"""
Pydantic models for weather data handling.

This module contains models for weather data requests, responses,
and data validation for the weather data integration system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import LocationModel, SuccessResponse


class WeatherDataSource(str, Enum):
    """Weather data source enumeration."""
    NSRDB = "nsrdb"
    PVGIS = "pvgis"
    AUTO = "auto"


class WeatherDataQuality(str, Enum):
    """Weather data quality enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class WeatherDataPoint(BaseModel):
    """Single weather data point model."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    ghi: float = Field(..., ge=0, description="Global horizontal irradiance in W/m²")
    dni: float = Field(..., ge=0, description="Direct normal irradiance in W/m²")
    dhi: float = Field(..., ge=0, description="Diffuse horizontal irradiance in W/m²")
    temp_air: float = Field(..., description="Air temperature in °C")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    relative_humidity: Optional[float] = Field(default=None, ge=0, le=100, description="Relative humidity in %")
    pressure: Optional[float] = Field(default=None, ge=0, description="Atmospheric pressure in mbar")
    
    @validator('ghi', 'dni', 'dhi')
    def validate_irradiance(cls, v):
        """Validate irradiance values are reasonable."""
        if v > 1500:  # Maximum theoretical solar irradiance
            raise ValueError('Irradiance value exceeds maximum theoretical limit')
        return v
    
    @validator('temp_air')
    def validate_temperature(cls, v):
        """Validate temperature is reasonable."""
        if v < -50 or v > 60:
            raise ValueError('Temperature must be between -50°C and 60°C')
        return v
    
    @validator('wind_speed')
    def validate_wind_speed(cls, v):
        """Validate wind speed is reasonable."""
        if v > 100:  # Maximum reasonable wind speed
            raise ValueError('Wind speed exceeds maximum reasonable limit')
        return v


class WeatherDataRequest(BaseModel):
    """Weather data request model."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    year: Optional[int] = Field(default=None, ge=1998, le=2030, description="Specific year for data")
    source: WeatherDataSource = Field(default=WeatherDataSource.AUTO, description="Preferred data source")
    use_cache: bool = Field(default=True, description="Use cached data if available")
    
    @validator('year')
    def validate_year(cls, v):
        """Validate year is within supported range."""
        if v is not None and (v < 1998 or v > 2030):
            raise ValueError('Year must be between 1998 and 2030')
        return v


class WeatherDataQualityInfo(BaseModel):
    """Weather data quality information model."""
    
    total_hours: int = Field(..., description="Total hours in dataset")
    valid_hours: int = Field(..., description="Hours with valid data")
    coverage_percentage: float = Field(..., ge=0, le=100, description="Data coverage percentage")
    missing_hours: int = Field(..., description="Number of missing hours")
    quality_distribution: Dict[str, int] = Field(..., description="Distribution of quality flags")
    
    @property
    def data_quality_score(self) -> float:
        """Calculate overall data quality score."""
        if self.total_hours == 0:
            return 0.0
        
        # Weight quality flags
        weights = {
            WeatherDataQuality.EXCELLENT: 1.0,
            WeatherDataQuality.GOOD: 0.8,
            WeatherDataQuality.FAIR: 0.6,
            WeatherDataQuality.POOR: 0.3
        }
        
        weighted_sum = sum(
            self.quality_distribution.get(quality, 0) * weight
            for quality, weight in weights.items()
        )
        
        return weighted_sum / self.total_hours


class WeatherDataMetadata(BaseModel):
    """Weather data metadata model."""
    
    location: LocationModel = Field(..., description="Data location")
    source: str = Field(..., description="Data source")
    year: Optional[int] = Field(default=None, description="Data year")
    spatial_resolution: Optional[str] = Field(default=None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(default=None, description="Temporal resolution")
    data_version: Optional[str] = Field(default=None, description="Data version")
    retrieval_time: datetime = Field(default_factory=datetime.utcnow, description="Data retrieval time")
    quality_info: WeatherDataQualityInfo = Field(..., description="Data quality information")


class WeatherDataResponse(SuccessResponse):
    """Weather data response model."""
    
    data: Dict[str, Any] = Field(..., description="Weather data and metadata")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Weather data retrieved successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "location": {
                        "latitude": 40.0,
                        "longitude": -105.0,
                        "elevation": 1650,
                        "timezone": "US/Mountain"
                    },
                    "source": "nsrdb",
                    "year": 2020,
                    "data_quality": {
                        "coverage": 99.8,
                        "missing_hours": 18,
                        "quality_flags": {
                            "excellent": 8500,
                            "good": 242,
                            "fair": 18,
                            "poor": 0
                        }
                    },
                    "weather_data": [
                        {
                            "timestamp": "2020-01-01T00:00:00Z",
                            "ghi": 0,
                            "dni": 0,
                            "dhi": 0,
                            "temp_air": -5.2,
                            "wind_speed": 3.1
                        }
                    ]
                }
            }
        }


class WeatherServiceStatus(BaseModel):
    """Weather service status model."""
    
    service_name: str = Field(..., description="Service name")
    available: bool = Field(..., description="Service availability")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")
    last_tested: Optional[datetime] = Field(default=None, description="Last test time")
    error_message: Optional[str] = Field(default=None, description="Error message if unavailable")
    supported_regions: List[str] = Field(default=[], description="Supported geographic regions")
    data_years: List[int] = Field(default=[], description="Available data years")


class WeatherServiceTestResponse(SuccessResponse):
    """Weather service test response model."""
    
    data: Dict[str, WeatherServiceStatus] = Field(..., description="Service status information")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Weather service status retrieved",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "nsrdb": {
                        "service_name": "NREL NSRDB",
                        "available": True,
                        "response_time": 1.23,
                        "last_tested": "2024-01-01T12:00:00Z",
                        "supported_regions": ["North America", "South America"],
                        "data_years": [1998, 1999, 2000, 2020]
                    },
                    "pvgis": {
                        "service_name": "PVGIS",
                        "available": True,
                        "response_time": 0.89,
                        "last_tested": "2024-01-01T12:00:00Z",
                        "supported_regions": ["Europe", "Asia", "Africa"],
                        "data_years": [2005, 2006, 2020]
                    }
                }
            }
        }


class WeatherDataSummary(BaseModel):
    """Weather data summary statistics model."""
    
    location: LocationModel = Field(..., description="Location")
    year: Optional[int] = Field(default=None, description="Data year")
    annual_ghi: float = Field(..., description="Annual global horizontal irradiance in kWh/m²")
    annual_dni: float = Field(..., description="Annual direct normal irradiance in kWh/m²")
    annual_dhi: float = Field(..., description="Annual diffuse horizontal irradiance in kWh/m²")
    avg_temperature: float = Field(..., description="Average air temperature in °C")
    min_temperature: float = Field(..., description="Minimum air temperature in °C")
    max_temperature: float = Field(..., description="Maximum air temperature in °C")
    avg_wind_speed: float = Field(..., description="Average wind speed in m/s")
    peak_irradiance: float = Field(..., description="Peak irradiance in W/m²")
    clear_sky_index: float = Field(..., description="Average clear sky index")
    
    @property
    def solar_resource_quality(self) -> str:
        """Determine solar resource quality based on annual GHI."""
        if self.annual_ghi >= 2000:
            return "excellent"
        elif self.annual_ghi >= 1600:
            return "good"
        elif self.annual_ghi >= 1200:
            return "fair"
        else:
            return "poor"


class WeatherDataCache(BaseModel):
    """Weather data cache model."""
    
    cache_key: str = Field(..., description="Cache key")
    location: LocationModel = Field(..., description="Location")
    source: str = Field(..., description="Data source")
    year: Optional[int] = Field(default=None, description="Data year")
    cached_at: datetime = Field(..., description="Cache timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    data_size: int = Field(..., description="Data size in bytes")
    access_count: int = Field(default=0, description="Number of times accessed")
    last_accessed: Optional[datetime] = Field(default=None, description="Last access timestamp")


class WeatherDataValidation(BaseModel):
    """Weather data validation results model."""
    
    is_valid: bool = Field(..., description="Whether data is valid")
    validation_errors: List[str] = Field(default=[], description="Validation errors")
    validation_warnings: List[str] = Field(default=[], description="Validation warnings")
    data_gaps: List[Dict[str, Any]] = Field(default=[], description="Data gaps information")
    outliers: List[Dict[str, Any]] = Field(default=[], description="Outlier detection results")
    consistency_checks: Dict[str, bool] = Field(default={}, description="Consistency check results")
    
    @property
    def validation_score(self) -> float:
        """Calculate validation score (0-1)."""
        score = 1.0
        
        # Deduct for errors
        score -= len(self.validation_errors) * 0.1
        
        # Deduct for warnings
        score -= len(self.validation_warnings) * 0.05
        
        # Deduct for data gaps
        score -= len(self.data_gaps) * 0.05
        
        # Deduct for outliers
        score -= len(self.outliers) * 0.02
        
        return max(0.0, score)


class WeatherDataFilter(BaseModel):
    """Weather data filter model."""
    
    start_date: Optional[datetime] = Field(default=None, description="Start date filter")
    end_date: Optional[datetime] = Field(default=None, description="End date filter")
    min_ghi: Optional[float] = Field(default=None, description="Minimum GHI filter")
    max_ghi: Optional[float] = Field(default=None, description="Maximum GHI filter")
    min_temperature: Optional[float] = Field(default=None, description="Minimum temperature filter")
    max_temperature: Optional[float] = Field(default=None, description="Maximum temperature filter")
    quality_threshold: Optional[str] = Field(default=None, description="Minimum quality threshold")
    
    @validator('start_date', 'end_date')
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if 'start_date' in values and 'end_date' in values:
            if values['start_date'] and v and values['start_date'] > v:
                raise ValueError('Start date must be before end date')
        return v


class WeatherDataAggregation(BaseModel):
    """Weather data aggregation model."""
    
    aggregation_type: str = Field(..., description="Aggregation type (hourly, daily, monthly)")
    location: LocationModel = Field(..., description="Location")
    year: Optional[int] = Field(default=None, description="Data year")
    data_points: List[Dict[str, Any]] = Field(..., description="Aggregated data points")
    statistics: Dict[str, float] = Field(..., description="Summary statistics")
    
    @validator('aggregation_type')
    def validate_aggregation_type(cls, v):
        """Validate aggregation type."""
        valid_types = ['hourly', 'daily', 'monthly', 'annual']
        if v not in valid_types:
            raise ValueError(f'Aggregation type must be one of: {valid_types}')
        return v