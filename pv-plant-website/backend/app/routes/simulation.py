"""
Simulation API routes.

This module provides endpoints for running PV simulations and tracking their status.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database import get_db, Simulation, SimulationResult, SystemConfiguration
from ..models.simulation import (
    SimulationRequest, SimulationResponse, SimulationStatusResponse,
    SimulationListResponse, SimulationCancelRequest, SimulationCancelResponse
)
from ..services.pv_simulation_service import pv_simulation_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/simulate", response_model=SimulationResponse)
async def start_simulation(
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new PV simulation.
    
    Creates and queues a new simulation job with the specified configuration.
    """
    try:
        # Check if PV simulation service is available
        if not pv_simulation_service.pvlib_available:
            raise HTTPException(
                status_code=503, 
                detail="PVLib simulation service not available"
            )
        
        # Get system configuration from database
        logger.info(f"Starting simulation for configuration {request.configuration_id}")
        
        result = await db.execute(
            select(SystemConfiguration).where(
                SystemConfiguration.id == request.configuration_id
            )
        )
        configuration = result.scalar_one_or_none()
        
        if not configuration:
            raise HTTPException(
                status_code=404, 
                detail=f"Configuration {request.configuration_id} not found"
            )
        
        # Run simulation using PV simulation service
        simulation_result = await pv_simulation_service.run_simulation(
            configuration=configuration,
            weather_source=request.weather_source,
            year=request.year,
            db=db
        )
        
        # Prepare response data
        simulation_data = {
            "simulation_id": simulation_result["simulation_id"],
            "configuration_id": request.configuration_id,
            "status": simulation_result["status"],
            "progress": 100,
            "annual_energy": simulation_result["results"]["annual_energy"],
            "performance_ratio": simulation_result["results"]["performance_ratio"],
            "capacity_factor": simulation_result["results"]["capacity_factor"],
            "weather_source": simulation_result["metadata"]["weather_source"],
            "data_points": simulation_result["metadata"]["data_points"]
        }
        
        return SimulationResponse(
            data=simulation_data,
            message="Simulation completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/simulate/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(
    simulation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a running simulation.
    
    Returns the current progress and status of the specified simulation.
    """
    try:
        # Get simulation from database
        result = await db.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise HTTPException(
                status_code=404, 
                detail=f"Simulation {simulation_id} not found"
            )
        
        # Calculate duration if completed
        duration = None
        if simulation.completed_at and simulation.started_at:
            duration = int((simulation.completed_at - simulation.started_at).total_seconds())
        
        status_data = {
            "simulation_id": simulation_id,
            "status": simulation.status,
            "progress": simulation.progress,
            "started_at": simulation.started_at.isoformat() if simulation.started_at else None,
            "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None,
            "duration": duration,
            "error_message": simulation.error_message
        }
        
        return SimulationStatusResponse(
            data=status_data,
            message="Simulation status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving simulation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulate", response_model=SimulationListResponse)
async def get_simulations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of simulations.
    
    Returns paginated list of simulations with their basic information.
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_result = await db.execute(select(Simulation))
        total_count = len(count_result.scalars().all())
        
        # Get paginated simulations with results
        result = await db.execute(
            select(Simulation, SimulationResult)
            .outerjoin(SimulationResult, Simulation.id == SimulationResult.simulation_id)
            .order_by(Simulation.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        simulations = []
        for simulation, result_record in result:
            annual_energy = None
            if result_record and result_record.results:
                annual_energy = result_record.results.get("annual_energy")
            
            simulations.append({
                "simulation_id": simulation.id,
                "configuration_id": simulation.configuration_id,
                "status": simulation.status,
                "created_at": simulation.created_at.isoformat(),
                "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None,
                "annual_energy": annual_energy,
                "weather_source": simulation.weather_source,
                "progress": simulation.progress
            })
        
        simulation_data = {
            "simulations": simulations,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        
        return SimulationListResponse(
            data=simulation_data,
            message="Simulations retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulate/{simulation_id}", response_model=SimulationCancelResponse)
async def cancel_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running simulation.
    
    Cancels the specified simulation if it's currently running.
    """
    try:
        # Get simulation from database
        result = await db.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise HTTPException(
                status_code=404, 
                detail=f"Simulation {simulation_id} not found"
            )
        
        # Check if simulation can be cancelled
        if simulation.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel simulation with status '{simulation.status}'"
            )
        
        # Update simulation status to cancelled
        from sqlalchemy import update
        from datetime import datetime
        
        await db.execute(
            update(Simulation)
            .where(Simulation.id == simulation_id)
            .values(
                status="cancelled",
                completed_at=datetime.now(),
                error_message="Simulation cancelled by user"
            )
        )
        await db.commit()
        
        cancel_data = {
            "simulation_id": simulation_id,
            "previous_status": simulation.status,
            "cancelled_at": datetime.now().isoformat()
        }
        
        return SimulationCancelResponse(
            data=cancel_data,
            message="Simulation cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))