"""
Pydantic models for PV simulations.

This module contains models for simulation requests, responses,
and status tracking for the PV simulation system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import SuccessResponse


class SimulationStatus(str, Enum):
    """Simulation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DCModel(str, Enum):
    """DC model enumeration."""
    CEC = "cec"
    SAPM = "sapm"
    PVWATTS = "pvwatts"
    SINGLEDIODE = "singlediode"


class ACModel(str, Enum):
    """AC model enumeration."""
    SANDIA = "sandia"
    ADR = "adr"
    PVWATTS = "pvwatts"


class TemperatureModel(str, Enum):
    """Temperature model enumeration."""
    SAPM = "sapm"
    PVSYST = "pvsyst"
    FUENTES = "fuentes"
    NOCT = "noct"


class ClearSkyModel(str, Enum):
    """Clear sky model enumeration."""
    INEICHEN = "ineichen"
    HAURWITZ = "haurwitz"
    SIMPLIFIED_SOLIS = "simplified_solis"


class IrradianceModel(str, Enum):
    """Irradiance model enumeration."""
    PEREZ = "perez"
    HAY_DAVIES = "hay_davies"
    REINDL = "reindl"
    KING = "king"
    KLUCHER = "klucher"
    ISOTROPIC = "isotropic"


class AOIModel(str, Enum):
    """Angle of incidence model enumeration."""
    PHYSICAL = "physical"
    ASHRAE = "ashrae"
    SAPM = "sapm"
    MARTIN_RUIZ = "martin_ruiz"


class SpectralModel(str, Enum):
    """Spectral model enumeration."""
    NO_LOSS = "no_loss"
    FIRST_SOLAR = "first_solar"
    SAPM = "sapm"


class SimulationOptions(BaseModel):
    """Simulation options model."""
    
    year: Optional[int] = Field(default=None, ge=1998, le=2030, description="Specific year for simulation")
    weather_source: str = Field(default="auto", description="Weather data source")
    dc_model: DCModel = Field(default=DCModel.CEC, description="DC model")
    ac_model: ACModel = Field(default=ACModel.SANDIA, description="AC model")
    temperature_model: TemperatureModel = Field(default=TemperatureModel.SAPM, description="Temperature model")
    clear_sky_model: ClearSkyModel = Field(default=ClearSkyModel.INEICHEN, description="Clear sky model")
    irradiance_model: IrradianceModel = Field(default=IrradianceModel.PEREZ, description="Irradiance model")
    aoi_model: AOIModel = Field(default=AOIModel.PHYSICAL, description="Angle of incidence model")
    spectral_model: SpectralModel = Field(default=SpectralModel.NO_LOSS, description="Spectral model")
    
    # Advanced options
    calculate_hourly: bool = Field(default=True, description="Calculate hourly results")
    calculate_daily: bool = Field(default=True, description="Calculate daily results")
    calculate_monthly: bool = Field(default=True, description="Calculate monthly results")
    include_weather_data: bool = Field(default=True, description="Include weather data in results")
    
    @validator('year')
    def validate_year(cls, v):
        """Validate simulation year."""
        if v is not None and (v < 1998 or v > 2030):
            raise ValueError('Year must be between 1998 and 2030')
        return v


class SimulationRequest(BaseModel):
    """Simulation request model."""
    
    configuration_id: str = Field(..., description="System configuration ID")
    simulation_options: SimulationOptions = Field(default_factory=SimulationOptions, description="Simulation options")
    name: Optional[str] = Field(default=None, description="Simulation name")
    description: Optional[str] = Field(default=None, description="Simulation description")
    
    @validator('configuration_id')
    def validate_configuration_id(cls, v):
        """Validate configuration ID format."""
        if not v or len(v) < 5:
            raise ValueError('Configuration ID must be at least 5 characters')
        return v


class SimulationResponse(SuccessResponse):
    """Simulation response model."""
    
    data: Dict[str, Any] = Field(..., description="Simulation data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Simulation started successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "simulation_id": "sim_789012",
                    "configuration_id": "conf_123456",
                    "status": "running",
                    "progress": 0,
                    "estimated_completion": "2024-01-01T12:05:00Z"
                }
            }
        }


class SimulationStatusResponse(SuccessResponse):
    """Simulation status response model."""
    
    data: Dict[str, Any] = Field(..., description="Simulation status data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Simulation status retrieved",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "simulation_id": "sim_789012",
                    "status": "completed",
                    "progress": 100,
                    "started_at": "2024-01-01T12:00:00Z",
                    "completed_at": "2024-01-01T12:03:45Z",
                    "duration": 225
                }
            }
        }


class SimulationProgress(BaseModel):
    """Simulation progress model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    status: SimulationStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(default=None, description="Current processing step")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    @validator('progress')
    def validate_progress(cls, v):
        """Validate progress percentage."""
        if not 0 <= v <= 100:
            raise ValueError('Progress must be between 0 and 100')
        return v


class SimulationError(BaseModel):
    """Simulation error model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    error_type: str = Field(..., description="Error type")
    error_message: str = Field(..., description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Error occurrence time")
    step: Optional[str] = Field(default=None, description="Step where error occurred")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_789012",
                "error_type": "WEATHER_DATA_ERROR",
                "error_message": "Failed to retrieve weather data for location",
                "error_details": {
                    "location": {"latitude": 40.0, "longitude": -105.0},
                    "year": 2020,
                    "source": "nsrdb"
                },
                "occurred_at": "2024-01-01T12:02:30Z",
                "step": "weather_data_retrieval"
            }
        }


class SimulationSummary(BaseModel):
    """Simulation summary model."""
    
    simulation_id: str = Field(..., description="Simulation ID")
    configuration_id: str = Field(..., description="Configuration ID")
    name: Optional[str] = Field(default=None, description="Simulation name")
    status: SimulationStatus = Field(..., description="Simulation status")
    created_at: datetime = Field(..., description="Creation time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    weather_source: str = Field(..., description="Weather data source")
    year: Optional[int] = Field(default=None, description="Simulation year")
    
    # Summary metrics (only for completed simulations)
    annual_energy: Optional[float] = Field(default=None, description="Annual energy in kWh")
    performance_ratio: Optional[float] = Field(default=None, description="Performance ratio")
    capacity_factor: Optional[float] = Field(default=None, description="Capacity factor")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_789012",
                "configuration_id": "conf_123456",
                "name": "Test Simulation",
                "status": "completed",
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:03:45Z",
                "duration": 225,
                "weather_source": "nsrdb",
                "year": 2020,
                "annual_energy": 7850.5,
                "performance_ratio": 0.84,
                "capacity_factor": 0.179
            }
        }


class SimulationListResponse(SuccessResponse):
    """Simulation list response model."""
    
    data: Dict[str, Any] = Field(..., description="Simulation list data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Simulations retrieved successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "simulations": [
                        {
                            "simulation_id": "sim_789012",
                            "configuration_id": "conf_123456",
                            "status": "completed",
                            "created_at": "2024-01-01T12:00:00Z",
                            "annual_energy": 7850.5
                        }
                    ],
                    "total_count": 25,
                    "page": 1,
                    "page_size": 20
                }
            }
        }


class SimulationValidation(BaseModel):
    """Simulation validation model."""
    
    is_valid: bool = Field(..., description="Whether simulation request is valid")
    validation_errors: List[str] = Field(default=[], description="Validation errors")
    validation_warnings: List[str] = Field(default=[], description="Validation warnings")
    estimated_duration: Optional[float] = Field(default=None, description="Estimated duration in seconds")
    estimated_data_size: Optional[int] = Field(default=None, description="Estimated result size in bytes")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "validation_errors": [],
                "validation_warnings": [
                    "Weather data quality is below optimal for this location"
                ],
                "estimated_duration": 180,
                "estimated_data_size": 1048576
            }
        }


class SimulationQueue(BaseModel):
    """Simulation queue model."""
    
    queue_position: int = Field(..., description="Position in queue")
    total_queue_size: int = Field(..., description="Total queue size")
    estimated_start_time: Optional[datetime] = Field(default=None, description="Estimated start time")
    priority: int = Field(default=0, description="Queue priority")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "queue_position": 3,
                "total_queue_size": 8,
                "estimated_start_time": "2024-01-01T12:10:00Z",
                "priority": 0
            }
        }


class SimulationCancelRequest(BaseModel):
    """Simulation cancel request model."""
    
    simulation_id: str = Field(..., description="Simulation ID to cancel")
    reason: Optional[str] = Field(default=None, description="Cancellation reason")
    
    @validator('simulation_id')
    def validate_simulation_id(cls, v):
        """Validate simulation ID format."""
        if not v or len(v) < 5:
            raise ValueError('Simulation ID must be at least 5 characters')
        return v


class SimulationCancelResponse(SuccessResponse):
    """Simulation cancel response model."""
    
    data: Dict[str, Any] = Field(..., description="Cancellation data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Simulation cancelled successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "simulation_id": "sim_789012",
                    "previous_status": "running",
                    "cancelled_at": "2024-01-01T12:05:00Z"
                }
            }
        }


class SimulationMetrics(BaseModel):
    """Simulation metrics model."""
    
    total_simulations: int = Field(..., description="Total number of simulations")
    completed_simulations: int = Field(..., description="Number of completed simulations")
    failed_simulations: int = Field(..., description="Number of failed simulations")
    running_simulations: int = Field(..., description="Number of running simulations")
    queued_simulations: int = Field(..., description="Number of queued simulations")
    average_duration: float = Field(..., description="Average simulation duration in seconds")
    success_rate: float = Field(..., description="Success rate percentage")
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.total_simulations == 0:
            return 0.0
        return (self.completed_simulations / self.total_simulations) * 100
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_simulations": 1000,
                "completed_simulations": 950,
                "failed_simulations": 30,
                "running_simulations": 5,
                "queued_simulations": 15,
                "average_duration": 180.5,
                "success_rate": 95.0
            }
        }