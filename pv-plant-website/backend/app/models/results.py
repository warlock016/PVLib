"""
Pydantic models for simulation results.

This module contains models for simulation results, metrics,
and analysis data returned by the PV simulation system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

from .common import SuccessResponse, LocationModel


class SummaryMetrics(BaseModel):
    """Summary metrics model."""
    
    annual_energy: float = Field(..., ge=0, description="Annual energy production in kWh")
    specific_yield: float = Field(..., ge=0, description="Specific yield in kWh/kWp")
    performance_ratio: float = Field(..., ge=0, le=1, description="Performance ratio")
    capacity_factor: float = Field(..., ge=0, le=1, description="Capacity factor")
    peak_power: float = Field(..., ge=0, description="Peak power in kW")
    energy_density: float = Field(..., ge=0, description="Energy density in kWh/m²")
    
    @validator('performance_ratio', 'capacity_factor')
    def validate_ratio(cls, v):
        """Validate ratio values are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Ratio must be between 0 and 1')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "annual_energy": 7850.5,
                "specific_yield": 1570.1,
                "performance_ratio": 0.84,
                "capacity_factor": 0.179,
                "peak_power": 4850.2,
                "energy_density": 125.4
            }
        }


class MonthlyData(BaseModel):
    """Monthly data model."""
    
    month: int = Field(..., ge=1, le=12, description="Month number")
    energy: float = Field(..., ge=0, description="Monthly energy in kWh")
    avg_power: float = Field(..., ge=0, description="Average power in kW")
    peak_power: float = Field(..., ge=0, description="Peak power in kW")
    performance_ratio: float = Field(..., ge=0, le=1, description="Monthly performance ratio")
    capacity_factor: float = Field(..., ge=0, le=1, description="Monthly capacity factor")
    ghi_total: float = Field(..., ge=0, description="Total GHI in kWh/m²")
    dni_total: float = Field(..., ge=0, description="Total DNI in kWh/m²")
    dhi_total: float = Field(..., ge=0, description="Total DHI in kWh/m²")
    avg_temperature: float = Field(..., description="Average temperature in °C")
    
    @validator('month')
    def validate_month(cls, v):
        """Validate month number."""
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "month": 7,
                "energy": 850.3,
                "avg_power": 1142.5,
                "peak_power": 4850.2,
                "performance_ratio": 0.86,
                "capacity_factor": 0.228,
                "ghi_total": 180.5,
                "dni_total": 220.8,
                "dhi_total": 85.2,
                "avg_temperature": 25.4
            }
        }


class DailyData(BaseModel):
    """Daily data model."""
    
    date: datetime = Field(..., description="Date")
    energy: float = Field(..., ge=0, description="Daily energy in kWh")
    peak_power: float = Field(..., ge=0, description="Peak power in kW")
    ghi_total: float = Field(..., ge=0, description="Total GHI in kWh/m²")
    dni_total: float = Field(..., ge=0, description="Total DNI in kWh/m²")
    dhi_total: float = Field(..., ge=0, description="Total DHI in kWh/m²")
    avg_temperature: float = Field(..., description="Average temperature in °C")
    avg_wind_speed: float = Field(..., ge=0, description="Average wind speed in m/s")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "date": "2024-07-15T00:00:00Z",
                "energy": 28.5,
                "peak_power": 4850.2,
                "ghi_total": 6.2,
                "dni_total": 7.8,
                "dhi_total": 2.1,
                "avg_temperature": 25.4,
                "avg_wind_speed": 3.2
            }
        }


class HourlyData(BaseModel):
    """Hourly data model."""
    
    timestamp: datetime = Field(..., description="Timestamp")
    ac_power: float = Field(..., ge=0, description="AC power in kW")
    dc_power: float = Field(..., ge=0, description="DC power in kW")
    ghi: float = Field(..., ge=0, description="Global horizontal irradiance in W/m²")
    dni: float = Field(..., ge=0, description="Direct normal irradiance in W/m²")
    dhi: float = Field(..., ge=0, description="Diffuse horizontal irradiance in W/m²")
    poa_irradiance: float = Field(..., ge=0, description="Plane of array irradiance in W/m²")
    cell_temperature: float = Field(..., description="Cell temperature in °C")
    module_temperature: float = Field(..., description="Module temperature in °C")
    temp_air: float = Field(..., description="Air temperature in °C")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "timestamp": "2024-07-15T12:00:00Z",
                "ac_power": 4520.8,
                "dc_power": 4750.2,
                "ghi": 950.5,
                "dni": 850.2,
                "dhi": 120.5,
                "poa_irradiance": 1020.8,
                "cell_temperature": 45.2,
                "module_temperature": 43.8,
                "temp_air": 28.5,
                "wind_speed": 3.2
            }
        }


class WeatherSummary(BaseModel):
    """Weather summary model."""
    
    location: LocationModel = Field(..., description="Location")
    year: Optional[int] = Field(default=None, description="Data year")
    annual_ghi: float = Field(..., ge=0, description="Annual GHI in kWh/m²")
    annual_dni: float = Field(..., ge=0, description="Annual DNI in kWh/m²")
    annual_dhi: float = Field(..., ge=0, description="Annual DHI in kWh/m²")
    avg_temperature: float = Field(..., description="Average temperature in °C")
    min_temperature: float = Field(..., description="Minimum temperature in °C")
    max_temperature: float = Field(..., description="Maximum temperature in °C")
    avg_wind_speed: float = Field(..., ge=0, description="Average wind speed in m/s")
    peak_irradiance: float = Field(..., ge=0, description="Peak irradiance in W/m²")
    clear_sky_index: float = Field(..., ge=0, le=1, description="Clear sky index")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "location": {
                    "latitude": 40.0,
                    "longitude": -105.0,
                    "elevation": 1650,
                    "timezone": "US/Mountain"
                },
                "year": 2020,
                "annual_ghi": 1650.5,
                "annual_dni": 1950.8,
                "annual_dhi": 580.2,
                "avg_temperature": 12.5,
                "min_temperature": -15.8,
                "max_temperature": 35.2,
                "avg_wind_speed": 4.2,
                "peak_irradiance": 1200.5,
                "clear_sky_index": 0.68
            }
        }


class SystemPerformance(BaseModel):
    """System performance model."""
    
    dc_capacity: float = Field(..., ge=0, description="DC capacity in kW")
    ac_capacity: float = Field(..., ge=0, description="AC capacity in kW")
    dc_ac_ratio: float = Field(..., ge=0, description="DC/AC ratio")
    inverter_efficiency: float = Field(..., ge=0, le=1, description="Average inverter efficiency")
    system_efficiency: float = Field(..., ge=0, le=1, description="Overall system efficiency")
    total_losses: float = Field(..., ge=0, le=1, description="Total system losses")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "dc_capacity": 5000.0,
                "ac_capacity": 4500.0,
                "dc_ac_ratio": 1.11,
                "inverter_efficiency": 0.965,
                "system_efficiency": 0.185,
                "total_losses": 0.158
            }
        }


class SimulationResults(BaseModel):
    """Complete simulation results model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    configuration_id: str = Field(..., description="Configuration ID")
    created_at: datetime = Field(..., description="Results creation time")
    
    # Summary data
    summary: SummaryMetrics = Field(..., description="Summary metrics")
    monthly_data: List[MonthlyData] = Field(..., description="Monthly data")
    weather_summary: WeatherSummary = Field(..., description="Weather summary")
    system_performance: SystemPerformance = Field(..., description="System performance")
    
    # Optional detailed data
    daily_data: Optional[List[DailyData]] = Field(default=None, description="Daily data")
    hourly_data: Optional[List[HourlyData]] = Field(default=None, description="Hourly data")
    
    # Metadata
    calculation_time: float = Field(..., description="Calculation time in seconds")
    data_size: int = Field(..., description="Data size in bytes")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SimulationResultsResponse(SuccessResponse):
    """Simulation results response model."""
    
    data: SimulationResults = Field(..., description="Simulation results")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Results retrieved successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "simulation_id": "sim_789012",
                    "configuration_id": "conf_123456",
                    "created_at": "2024-01-01T12:03:45Z",
                    "summary": {
                        "annual_energy": 7850.5,
                        "specific_yield": 1570.1,
                        "performance_ratio": 0.84,
                        "capacity_factor": 0.179,
                        "peak_power": 4850.2
                    },
                    "monthly_data": [
                        {
                            "month": 1,
                            "energy": 520.3,
                            "performance_ratio": 0.78,
                            "capacity_factor": 0.139
                        }
                    ],
                    "weather_summary": {
                        "annual_ghi": 1650.5,
                        "avg_temperature": 12.5
                    },
                    "calculation_time": 225.5,
                    "data_size": 1048576
                }
            }
        }


class PerformanceAnalysis(BaseModel):
    """Performance analysis model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    analysis_type: str = Field(..., description="Analysis type")
    
    # Performance indicators
    energy_yield_rating: str = Field(..., description="Energy yield rating")
    pr_rating: str = Field(..., description="Performance ratio rating")
    cf_rating: str = Field(..., description="Capacity factor rating")
    
    # Seasonal analysis
    best_month: Dict[str, Any] = Field(..., description="Best performing month")
    worst_month: Dict[str, Any] = Field(..., description="Worst performing month")
    seasonal_variation: float = Field(..., description="Seasonal variation coefficient")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="Performance recommendations")
    optimization_potential: float = Field(..., description="Optimization potential in %")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_789012",
                "analysis_type": "performance_analysis",
                "energy_yield_rating": "good",
                "pr_rating": "excellent",
                "cf_rating": "good",
                "best_month": {
                    "month": 7,
                    "energy": 850.3,
                    "performance_ratio": 0.86
                },
                "worst_month": {
                    "month": 12,
                    "energy": 420.1,
                    "performance_ratio": 0.78
                },
                "seasonal_variation": 0.15,
                "recommendations": [
                    "Consider tracking system for higher yield",
                    "Optimize tilt angle for location"
                ],
                "optimization_potential": 8.5
            }
        }


class ComparisonAnalysis(BaseModel):
    """Comparison analysis model."""
    
    base_simulation_id: str = Field(..., description="Base simulation ID")
    comparison_simulation_ids: List[str] = Field(..., description="Comparison simulation IDs")
    
    # Comparison metrics
    energy_comparison: Dict[str, float] = Field(..., description="Energy comparison")
    pr_comparison: Dict[str, float] = Field(..., description="PR comparison")
    cf_comparison: Dict[str, float] = Field(..., description="CF comparison")
    
    # Best and worst performers
    best_performer: Dict[str, Any] = Field(..., description="Best performing configuration")
    worst_performer: Dict[str, Any] = Field(..., description="Worst performing configuration")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="Comparison recommendations")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "base_simulation_id": "sim_789012",
                "comparison_simulation_ids": ["sim_789013", "sim_789014"],
                "energy_comparison": {
                    "sim_789012": 7850.5,
                    "sim_789013": 8150.2,
                    "sim_789014": 7650.8
                },
                "best_performer": {
                    "simulation_id": "sim_789013",
                    "energy": 8150.2,
                    "improvement": 3.8
                },
                "recommendations": [
                    "Configuration sim_789013 shows 3.8% better performance",
                    "Consider single-axis tracking for optimal results"
                ]
            }
        }


class ResultsMetadata(BaseModel):
    """Results metadata model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    version: str = Field(..., description="Results version")
    created_at: datetime = Field(..., description="Creation time")
    pvlib_version: str = Field(..., description="PVLib version used")
    weather_data_source: str = Field(..., description="Weather data source")
    weather_data_year: Optional[int] = Field(default=None, description="Weather data year")
    models_used: Dict[str, str] = Field(..., description="Models used in simulation")
    calculation_settings: Dict[str, Any] = Field(..., description="Calculation settings")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_789012",
                "version": "1.0.0",
                "created_at": "2024-01-01T12:03:45Z",
                "pvlib_version": "0.13.0",
                "weather_data_source": "nsrdb",
                "weather_data_year": 2020,
                "models_used": {
                    "dc_model": "cec",
                    "ac_model": "sandia",
                    "temperature_model": "sapm"
                },
                "calculation_settings": {
                    "resolution": "hourly",
                    "losses_enabled": True
                }
            }
        }


class ResultsExportRequest(BaseModel):
    """Results export request model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    format: str = Field(..., description="Export format")
    resolution: str = Field(default="hourly", description="Data resolution")
    include_weather: bool = Field(default=True, description="Include weather data")
    include_metadata: bool = Field(default=True, description="Include metadata")
    date_range: Optional[Dict[str, datetime]] = Field(default=None, description="Date range filter")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate export format."""
        valid_formats = ['csv', 'json', 'xlsx', 'parquet']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Validate data resolution."""
        valid_resolutions = ['hourly', 'daily', 'monthly', 'annual']
        if v not in valid_resolutions:
            raise ValueError(f'Resolution must be one of: {valid_resolutions}')
        return v