"""
Pydantic models for PV system configuration.

This module contains models for system configuration requests and responses,
including location, system specifications, array configuration, and loss parameters.
"""

from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import LocationModel, SuccessResponse


class MountingType(str, Enum):
    """Mounting type enumeration."""
    FIXED = "fixed"
    SINGLE_AXIS = "single_axis"
    DUAL_AXIS = "dual_axis"


class TrackingType(str, Enum):
    """Tracking type enumeration."""
    NONE = "none"
    SINGLE_AXIS = "single_axis"
    DUAL_AXIS = "dual_axis"


class ModuleTechnology(str, Enum):
    """Module technology enumeration."""
    C_SI = "c-Si"
    CDTE = "CdTe"
    CIGS = "CIGS"
    A_SI = "a-Si"
    PERC = "PERC"
    BIFACIAL = "bifacial"


class SystemSpecification(BaseModel):
    """PV system specification model."""
    
    dc_capacity: float = Field(..., gt=0, description="DC capacity in kW")
    module_type: str = Field(..., description="Module type from CEC database")
    inverter_type: str = Field(..., description="Inverter type from CEC database")
    modules_per_string: int = Field(..., gt=0, description="Number of modules per string")
    strings_per_inverter: int = Field(..., gt=0, description="Number of strings per inverter")
    system_voltage: Optional[float] = Field(default=None, description="System voltage in V")
    
    @validator('dc_capacity')
    def validate_dc_capacity(cls, v):
        """Validate DC capacity is reasonable."""
        if v > 1000000:  # 1 GW limit
            raise ValueError('DC capacity cannot exceed 1,000,000 kW')
        return v
    
    @validator('modules_per_string')
    def validate_modules_per_string(cls, v):
        """Validate modules per string is reasonable."""
        if v > 100:
            raise ValueError('Modules per string cannot exceed 100')
        return v
    
    @validator('strings_per_inverter')
    def validate_strings_per_inverter(cls, v):
        """Validate strings per inverter is reasonable."""
        if v > 1000:
            raise ValueError('Strings per inverter cannot exceed 1000')
        return v


class ArrayConfiguration(BaseModel):
    """Array configuration model."""
    
    mounting_type: MountingType = Field(..., description="Mounting type")
    tilt: Optional[float] = Field(default=None, ge=0, le=90, description="Tilt angle in degrees")
    azimuth: Optional[float] = Field(default=None, ge=0, le=360, description="Azimuth angle in degrees")
    tracking_type: Optional[TrackingType] = Field(default=None, description="Tracking type")
    gcr: Optional[float] = Field(default=None, ge=0.1, le=1.0, description="Ground coverage ratio")
    axis_tilt: Optional[float] = Field(default=0, ge=0, le=90, description="Tracker axis tilt in degrees")
    axis_azimuth: Optional[float] = Field(default=180, ge=0, le=360, description="Tracker axis azimuth in degrees")
    max_angle: Optional[float] = Field(default=60, ge=0, le=90, description="Maximum tracking angle in degrees")
    backtrack: Optional[bool] = Field(default=True, description="Enable backtracking")
    
    @validator('tilt')
    def validate_tilt_for_fixed(cls, v, values):
        """Validate tilt is provided for fixed mounting."""
        if values.get('mounting_type') == MountingType.FIXED and v is None:
            raise ValueError('Tilt angle is required for fixed mounting')
        return v
    
    @validator('azimuth')
    def validate_azimuth_for_fixed(cls, v, values):
        """Validate azimuth is provided for fixed mounting."""
        if values.get('mounting_type') == MountingType.FIXED and v is None:
            raise ValueError('Azimuth angle is required for fixed mounting')
        return v
    
    @validator('gcr')
    def validate_gcr_for_tracking(cls, v, values):
        """Validate GCR is provided for tracking systems."""
        if values.get('mounting_type') in [MountingType.SINGLE_AXIS, MountingType.DUAL_AXIS] and v is None:
            raise ValueError('Ground coverage ratio is required for tracking systems')
        return v


class LossParameters(BaseModel):
    """Loss parameters model."""
    
    soiling: float = Field(default=2.0, ge=0, le=50, description="Soiling losses in %")
    shading: float = Field(default=3.0, ge=0, le=50, description="Shading losses in %")
    snow: float = Field(default=0.0, ge=0, le=50, description="Snow losses in %")
    mismatch: float = Field(default=2.0, ge=0, le=20, description="Module mismatch losses in %")
    wiring: float = Field(default=2.0, ge=0, le=10, description="Wiring losses in %")
    connections: float = Field(default=0.5, ge=0, le=5, description="Connection losses in %")
    lid: float = Field(default=1.5, ge=0, le=10, description="Light-induced degradation in %")
    nameplate_rating: float = Field(default=1.0, ge=0, le=10, description="Nameplate rating losses in %")
    age: float = Field(default=0.0, ge=0, le=50, description="Age-related degradation in %")
    availability: float = Field(default=0.0, ge=0, le=20, description="System availability losses in %")
    
    @validator('soiling', 'shading', 'snow', 'mismatch', 'wiring', 'connections', 'lid', 'nameplate_rating', 'age', 'availability')
    def validate_loss_percentage(cls, v):
        """Validate loss percentages are reasonable."""
        if v < 0 or v > 100:
            raise ValueError('Loss percentage must be between 0 and 100')
        return v
    
    @property
    def total_losses(self) -> float:
        """Calculate total losses (approximate)."""
        return self.soiling + self.shading + self.snow + self.mismatch + \
               self.wiring + self.connections + self.lid + self.nameplate_rating + \
               self.age + self.availability


class SystemConfigurationRequest(BaseModel):
    """System configuration request model."""
    
    location: LocationModel = Field(..., description="Geographic location")
    system: SystemSpecification = Field(..., description="System specifications")
    array: ArrayConfiguration = Field(..., description="Array configuration")
    losses: LossParameters = Field(default_factory=LossParameters, description="Loss parameters")
    name: Optional[str] = Field(default=None, description="Configuration name")
    description: Optional[str] = Field(default=None, description="Configuration description")
    
    @validator('location')
    def validate_location(cls, v):
        """Validate location coordinates."""
        if not (-90 <= v.latitude <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        if not (-180 <= v.longitude <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v


class SystemConfigurationResponse(SuccessResponse):
    """System configuration response model."""
    
    data: Dict[str, Any] = Field(..., description="Configuration data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "System configured successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "configuration_id": "conf_123456",
                    "location": {
                        "latitude": 40.0,
                        "longitude": -105.0,
                        "elevation": 1650,
                        "timezone": "US/Mountain"
                    },
                    "system": {
                        "dc_capacity": 5000,
                        "module_type": "First_Solar__Inc__FS_6440A",
                        "inverter_type": "SMA_America__SB5000US__240V_"
                    },
                    "array": {
                        "mounting_type": "fixed",
                        "tilt": 25,
                        "azimuth": 180
                    },
                    "losses": {
                        "soiling": 2.0,
                        "shading": 3.0,
                        "total_losses": 15.0
                    }
                }
            }
        }


class ModuleInfo(BaseModel):
    """Module information model."""
    
    name: str = Field(..., description="Module name")
    technology: str = Field(..., description="Module technology")
    manufacturer: str = Field(..., description="Manufacturer name")
    power_rating: float = Field(..., description="Power rating in watts")
    efficiency: float = Field(..., description="Module efficiency in %")
    area: float = Field(..., description="Module area in m²")
    voltage_oc: float = Field(..., description="Open circuit voltage in V")
    current_sc: float = Field(..., description="Short circuit current in A")
    voltage_mp: float = Field(..., description="Maximum power voltage in V")
    current_mp: float = Field(..., description="Maximum power current in A")
    temperature_coeff_pmp: float = Field(..., description="Power temperature coefficient in %/°C")
    temperature_coeff_oc: float = Field(..., description="Voltage temperature coefficient in %/°C")
    temperature_coeff_sc: float = Field(..., description="Current temperature coefficient in %/°C")
    noct: float = Field(..., description="Nominal operating cell temperature in °C")


class InverterInfo(BaseModel):
    """Inverter information model."""
    
    name: str = Field(..., description="Inverter name")
    manufacturer: str = Field(..., description="Manufacturer name")
    power_rating: float = Field(..., description="AC power rating in watts")
    efficiency: float = Field(..., description="Maximum efficiency in %")
    voltage_ac: float = Field(..., description="AC voltage in V")
    voltage_dc_min: float = Field(..., description="Minimum DC voltage in V")
    voltage_dc_max: float = Field(..., description="Maximum DC voltage in V")
    voltage_dc_mppt_min: float = Field(..., description="Minimum MPPT voltage in V")
    voltage_dc_mppt_max: float = Field(..., description="Maximum MPPT voltage in V")
    current_dc_max: float = Field(..., description="Maximum DC current in A")
    mppt_inputs: int = Field(..., description="Number of MPPT inputs")


class ModuleListResponse(SuccessResponse):
    """Module list response model."""
    
    data: Dict[str, Any] = Field(..., description="Module list data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Modules retrieved successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "modules": [
                        {
                            "name": "Canadian_Solar_Inc__CS5P_220M",
                            "technology": "c-Si",
                            "manufacturer": "Canadian Solar Inc",
                            "power_rating": 220,
                            "efficiency": 13.4
                        }
                    ],
                    "total_count": 1500,
                    "filtered_count": 150
                }
            }
        }


class InverterListResponse(SuccessResponse):
    """Inverter list response model."""
    
    data: Dict[str, Any] = Field(..., description="Inverter list data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Inverters retrieved successfully",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "inverters": [
                        {
                            "name": "SMA_America__SB5000US__240V_",
                            "manufacturer": "SMA America",
                            "power_rating": 5000,
                            "efficiency": 96.5
                        }
                    ],
                    "total_count": 800,
                    "filtered_count": 80
                }
            }
        }


class ConfigurationSummary(BaseModel):
    """Configuration summary model."""
    
    configuration_id: str = Field(..., description="Configuration ID")
    name: Optional[str] = Field(default=None, description="Configuration name")
    location: LocationModel = Field(..., description="Location")
    dc_capacity: float = Field(..., description="DC capacity in kW")
    module_type: str = Field(..., description="Module type")
    inverter_type: str = Field(..., description="Inverter type")
    mounting_type: str = Field(..., description="Mounting type")
    created_at: str = Field(..., description="Creation timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "configuration_id": "conf_123456",
                "name": "Test Configuration",
                "location": {
                    "latitude": 40.0,
                    "longitude": -105.0,
                    "elevation": 1650
                },
                "dc_capacity": 5000,
                "module_type": "First_Solar__Inc__FS_6440A",
                "inverter_type": "SMA_America__SB5000US__240V_",
                "mounting_type": "fixed",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class SystemValidationResult(BaseModel):
    """System validation result model."""
    
    is_valid: bool = Field(..., description="Whether the configuration is valid")
    warnings: List[str] = Field(default=[], description="Configuration warnings")
    errors: List[str] = Field(default=[], description="Configuration errors")
    recommendations: List[str] = Field(default=[], description="Optimization recommendations")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "warnings": ["DC/AC ratio is high (1.35)"],
                "errors": [],
                "recommendations": [
                    "Consider using larger inverter for better performance",
                    "Tilt angle could be optimized for location"
                ]
            }
        }