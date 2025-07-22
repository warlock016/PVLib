"""
System configuration API routes.

This module provides endpoints for PV system configuration,
including modules, inverters, and system setup.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from ..database import get_db
from ..models.system_config import (
    SystemConfigurationRequest, SystemConfigurationResponse,
    ModuleListResponse, InverterListResponse
)
from ..models.common import SuccessResponse

router = APIRouter()


@router.post("/configure", response_model=SystemConfigurationResponse)
async def configure_system(
    config: SystemConfigurationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Configure a new PV system.
    
    Creates a new system configuration with the provided parameters.
    """
    try:
        # TODO: Implement actual configuration logic
        # For now, return a mock response
        
        config_data = {
            "configuration_id": f"conf_{hash(str(config.dict()))}"[:10],
            "location": config.location.dict(),
            "system": config.system.dict(),
            "array": config.array.dict(),
            "losses": config.losses.dict()
        }
        
        return SystemConfigurationResponse(
            data=config_data,
            message="System configured successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules", response_model=ModuleListResponse)
async def get_modules(
    technology: str = None,
    manufacturer: str = None,
    min_power: float = None,
    max_power: float = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get available PV modules from the database.
    
    Returns a list of PV modules with optional filtering.
    """
    try:
        # TODO: Implement actual module database query
        # For now, return mock data
        
        modules = [
            {
                "name": "Canadian_Solar_Inc__CS5P_220M",
                "technology": "c-Si",
                "manufacturer": "Canadian Solar Inc",
                "power_rating": 220,
                "efficiency": 13.4,
                "area": 1.64
            },
            {
                "name": "First_Solar__Inc__FS_6440A",
                "technology": "CdTe",
                "manufacturer": "First Solar Inc",
                "power_rating": 440,
                "efficiency": 18.2,
                "area": 2.42
            }
        ]
        
        return ModuleListResponse(
            data={
                "modules": modules,
                "total_count": len(modules),
                "filtered_count": len(modules)
            },
            message="Modules retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inverters", response_model=InverterListResponse)
async def get_inverters(
    manufacturer: str = None,
    min_power: float = None,
    max_power: float = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get available inverters from the database.
    
    Returns a list of inverters with optional filtering.
    """
    try:
        # TODO: Implement actual inverter database query
        # For now, return mock data
        
        inverters = [
            {
                "name": "SMA_America__SB5000US__240V_",
                "manufacturer": "SMA America",
                "power_rating": 5000,
                "efficiency": 96.5,
                "voltage_ac": 240
            },
            {
                "name": "Fronius_International_GmbH__Fronius_IG_Plus_120_V_3_US_240V_",
                "manufacturer": "Fronius International GmbH",
                "power_rating": 12000,
                "efficiency": 95.8,
                "voltage_ac": 240
            }
        ]
        
        return InverterListResponse(
            data={
                "inverters": inverters,
                "total_count": len(inverters),
                "filtered_count": len(inverters)
            },
            message="Inverters retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))