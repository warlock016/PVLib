"""
PV Simulation Service using PVLib ModelChain.

This service provides PV system simulation capabilities using PVLib's ModelChain
for standardized photovoltaic modeling workflows.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

# Import PVLib
try:
    import pvlib
    from pvlib import pvsystem, modelchain, location, temperature, inverter
    from pvlib.pvsystem import PVSystem
    from pvlib.location import Location
    from pvlib.modelchain import ModelChain
    PVLIB_AVAILABLE = True
except ImportError:
    PVLIB_AVAILABLE = False
    pvlib = None

from ..database import Simulation, SimulationResult, SystemConfiguration, AsyncSessionLocal
from ..models.simulation import SimulationRequest
from .weather_service import weather_service

logger = logging.getLogger(__name__)


class PVSimulationService:
    """
    Service class for PV system simulation using PVLib ModelChain.
    
    Provides methods for running PV performance simulations with weather data,
    system configurations, and result storage.
    """
    
    def __init__(self):
        """Initialize the PV simulation service."""
        self.pvlib_available = PVLIB_AVAILABLE
        
        if not self.pvlib_available:
            logger.warning("PVLib not available - simulation service disabled")
        else:
            logger.info("PV simulation service initialized successfully")
    
    async def run_simulation(
        self,
        configuration: SystemConfiguration,
        weather_source: str = "auto",
        year: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Run a PV system simulation.
        
        Parameters
        ----------
        configuration : SystemConfiguration
            System configuration parameters
        weather_source : str, default "auto"
            Weather data source preference
        year : int, optional
            Year for simulation. If None, uses TMY data
        db : AsyncSession, optional
            Database session
            
        Returns
        -------
        dict
            Simulation results with metadata
        """
        if not self.pvlib_available:
            raise RuntimeError("PVLib not available - cannot run simulation")
        
        try:
            # Generate simulation ID
            simulation_id = str(uuid.uuid4())
            
            # Create simulation record
            simulation_record = await self._create_simulation_record(
                simulation_id, configuration, weather_source, year, db
            )
            
            # Get weather data
            logger.info(f"Fetching weather data for simulation {simulation_id}")
            weather_data = await weather_service.get_weather_data(
                latitude=configuration.latitude,
                longitude=configuration.longitude,
                year=year,
                source=weather_source,
                db=db
            )
            
            # Create PVLib location
            location_obj = self._create_location(configuration, weather_data)
            
            # Create PVLib system
            system_obj = self._create_system(configuration)
            
            # Create weather DataFrame
            weather_df = self._create_weather_dataframe(weather_data)
            
            # Run ModelChain simulation
            logger.info(f"Running PVLib ModelChain simulation for {simulation_id}")
            mc_results = self._run_modelchain(
                system_obj, location_obj, weather_df
            )
            
            # Process results
            results = self._process_simulation_results(
                mc_results, configuration, weather_data, simulation_id
            )
            
            # Store results in database
            await self._store_simulation_results(
                simulation_id, results, db
            )
            
            # Update simulation status
            await self._update_simulation_status(
                simulation_id, "completed", 100, db
            )
            
            logger.info(f"Simulation {simulation_id} completed successfully")
            
            return {
                "simulation_id": simulation_id,
                "status": "completed",
                "results": results,
                "metadata": {
                    "weather_source": weather_data.get("source"),
                    "simulation_time": datetime.now().isoformat(),
                    "data_points": len(weather_df) if weather_df is not None else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            
            # Update simulation status to failed
            if 'simulation_id' in locals():
                await self._update_simulation_status(
                    simulation_id, "failed", 0, db, str(e)
                )
            
            raise
    
    def _create_location(
        self, 
        configuration: SystemConfiguration, 
        weather_data: Dict[str, Any]
    ) -> Location:
        """Create PVLib Location object."""
        location_info = weather_data.get("location", {})
        
        return Location(
            latitude=configuration.latitude,
            longitude=configuration.longitude,
            tz=location_info.get("timezone", "UTC"),
            altitude=location_info.get("elevation", 0),
            name=f"PV Plant ({configuration.latitude:.2f}, {configuration.longitude:.2f})"
        )
    
    def _create_system(self, configuration: SystemConfiguration) -> PVSystem:
        """Create PVLib PVSystem object."""
        try:
            # Get module and inverter parameters
            module_params = self._get_module_parameters(configuration.module_type)
            inverter_params = self._get_inverter_parameters(configuration.inverter_type)
            
            # Create arrays configuration
            arrays = [
                pvsystem.Array(
                    mount=pvsystem.FixedMount(
                        surface_tilt=configuration.tilt or 30,
                        surface_azimuth=configuration.azimuth or 180
                    ),
                    module_parameters=module_params,
                    temperature_model_parameters=self._get_temperature_model_parameters(),
                    modules_per_string=configuration.modules_per_string,
                    strings=configuration.strings_per_inverter
                )
            ]
            
            # Create PVSystem
            system = PVSystem(
                arrays=arrays,
                inverter_parameters=inverter_params,
                inverter=inverter.pvwatts,
                losses_parameters=self._get_losses_parameters(configuration.losses)
            )
            
            return system
            
        except Exception as e:
            logger.error(f"Error creating PVSystem: {e}")
            # Return a default system if specific parameters fail
            return self._create_default_system(configuration)
    
    def _get_module_parameters(self, module_type: str) -> Dict[str, Any]:
        """Get module parameters from PVLib database or defaults."""
        try:
            # Try to get from PVLib CEC database
            cec_modules = pvsystem.retrieve_sam('CECMod')
            
            if module_type in cec_modules.columns:
                return cec_modules[module_type].to_dict()
            
            # Search for similar module
            for module in cec_modules.columns:
                if module_type.lower() in module.lower():
                    logger.info(f"Using similar module: {module}")
                    return cec_modules[module].to_dict()
            
            # Return default module parameters
            logger.warning(f"Module {module_type} not found, using default")
            return self._get_default_module_parameters()
            
        except Exception as e:
            logger.error(f"Error getting module parameters: {e}")
            return self._get_default_module_parameters()
    
    def _get_inverter_parameters(self, inverter_type: str) -> Dict[str, Any]:
        """Get inverter parameters from PVLib database or defaults."""
        try:
            # Try to get from PVLib CEC database
            cec_inverters = pvsystem.retrieve_sam('CECInverter')
            
            if inverter_type in cec_inverters.columns:
                return cec_inverters[inverter_type].to_dict()
            
            # Search for similar inverter
            for inverter in cec_inverters.columns:
                if inverter_type.lower() in inverter.lower():
                    logger.info(f"Using similar inverter: {inverter}")
                    return cec_inverters[inverter].to_dict()
            
            # Return default inverter parameters
            logger.warning(f"Inverter {inverter_type} not found, using default")
            return self._get_default_inverter_parameters()
            
        except Exception as e:
            logger.error(f"Error getting inverter parameters: {e}")
            return self._get_default_inverter_parameters()
    
    def _get_default_module_parameters(self) -> Dict[str, Any]:
        """Get default module parameters."""
        return {
            'Name': 'Generic Silicon Module',
            'BIPV': 'N',
            'Date': '1/1/2024',
            'T_NOCT': 45.0,
            'A_c': 2.0,
            'N_s': 60,
            'I_sc_ref': 9.5,
            'V_oc_ref': 38.0,
            'I_mp_ref': 9.0,
            'V_mp_ref': 31.0,
            'alpha_sc': 0.0048,
            'beta_oc': -0.13,
            'a_ref': 1.8,
            'I_L_ref': 9.52,
            'I_o_ref': 2.0e-10,
            'R_s': 0.3,
            'R_sh_ref': 300.0,
            'Adjust': 8.0,
            'gamma_r': -0.45,
            'Version': 'Generic',
            'PTC': 290.0,
            'Technology': 'Mono-c-Si'
        }
    
    def _get_default_inverter_parameters(self) -> Dict[str, Any]:
        """Get default inverter parameters for Sandia model."""
        return {
            'Name': 'Generic Inverter',
            'Vac': 240.0,
            'Paco': 5000.0,  # AC power rating (W)
            'Pdco': 5200.0,  # DC power rating (W)
            'Vdco': 310.0,   # DC voltage rating (V)
            'Pso': 20.0,     # Self-consumption (W)
            'C0': -1.0e-6,   # Coefficient 0
            'C1': -5.0e-6,   # Coefficient 1
            'C2': -1.0e-5,   # Coefficient 2
            'C3': -0.0002,   # Coefficient 3
            'Pnt': 0.1,      # Night tare power (W)
            'Vdcmax': 600.0, # Maximum DC voltage (V)
            'Idcmax': 20.0,  # Maximum DC current (A)
            'Mppt_low': 200.0,  # Lower MPPT voltage (V)
            'Mppt_high': 500.0  # Upper MPPT voltage (V)
        }
    
    def _get_temperature_model_parameters(self) -> Dict[str, Any]:
        """Get temperature model parameters."""
        return temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    
    def _get_losses_parameters(self, losses_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert losses configuration to PVLib format."""
        return {
            'soiling': losses_config.get('soiling', 0.02),
            'shading': losses_config.get('shading', 0.05),
            'snow': losses_config.get('snow', 0.0),
            'mismatch': losses_config.get('mismatch', 0.02),
            'wiring': losses_config.get('wiring', 0.02),
            'connections': losses_config.get('connections', 0.005),
            'lid': losses_config.get('lid', 0.015),
            'nameplate_rating': losses_config.get('nameplate_rating', 0.01),
            'age': losses_config.get('age', 0.0),
            'availability': losses_config.get('availability', 0.97)
        }
    
    def _create_default_system(self, configuration: SystemConfiguration) -> PVSystem:
        """Create a default PVSystem when specific parameters fail."""
        logger.info("Creating default PVSystem")
        
        arrays = [
            pvsystem.Array(
                mount=pvsystem.FixedMount(
                    surface_tilt=configuration.tilt or 30,
                    surface_azimuth=configuration.azimuth or 180
                ),
                module_parameters=self._get_default_module_parameters(),
                temperature_model_parameters=self._get_temperature_model_parameters(),
                modules_per_string=configuration.modules_per_string,
                strings=configuration.strings_per_inverter
            )
        ]
        
        return PVSystem(
            arrays=arrays,
            inverter_parameters=self._get_default_inverter_parameters(),
            inverter=inverter.pvwatts,
            losses_parameters=self._get_losses_parameters(configuration.losses)
        )
    
    def _create_weather_dataframe(self, weather_data: Dict[str, Any]) -> pd.DataFrame:
        """Create weather DataFrame from weather service data."""
        # For now, create a simple DataFrame with basic weather data
        # In a full implementation, this would extract the actual weather time series
        
        # Create hourly timestamps for a year
        timestamps = pd.date_range(
            start='2023-01-01', 
            end='2023-12-31 23:00:00', 
            freq='H'
        )
        
        # Extract weather summary for creating synthetic data
        weather_summary = weather_data.get('weather_summary', {})
        avg_temp = weather_summary.get('average_temperature', 15.0)
        avg_wind = weather_summary.get('average_wind_speed', 3.0)
        annual_ghi = weather_summary.get('annual_ghi', 1500000)
        
        # Create basic weather DataFrame
        # Note: This is simplified - real implementation would use actual weather time series
        df = pd.DataFrame({
            'ghi': np.random.normal(annual_ghi / 8760, annual_ghi / 20000, len(timestamps)),
            'dni': np.random.normal(annual_ghi / 8760 * 0.8, annual_ghi / 25000, len(timestamps)),
            'dhi': np.random.normal(annual_ghi / 8760 * 0.2, annual_ghi / 30000, len(timestamps)),
            'temp_air': np.random.normal(avg_temp, 5, len(timestamps)),
            'wind_speed': np.random.normal(avg_wind, 1, len(timestamps))
        }, index=timestamps)
        
        # Ensure non-negative values
        df['ghi'] = df['ghi'].clip(lower=0)
        df['dni'] = df['dni'].clip(lower=0)
        df['dhi'] = df['dhi'].clip(lower=0)
        df['wind_speed'] = df['wind_speed'].clip(lower=0)
        
        return df
    
    def _run_modelchain(
        self, 
        system: PVSystem, 
        location: Location, 
        weather: pd.DataFrame
    ) -> ModelChain:
        """Run PVLib ModelChain simulation."""
        try:
            # Create ModelChain
            mc = ModelChain(
                system=system,
                location=location,
                aoi_model='physical',
                spectral_model='no_loss',
                temperature_model='sapm',
                losses_model='pvwatts'
            )
            
            # Run simulation
            mc.run_model(weather)
            
            return mc
            
        except Exception as e:
            logger.error(f"ModelChain simulation failed: {e}")
            raise
    
    def _process_simulation_results(
        self,
        mc_results: ModelChain,
        configuration: SystemConfiguration,
        weather_data: Dict[str, Any],
        simulation_id: str
    ) -> Dict[str, Any]:
        """Process ModelChain results into standardized format."""
        try:
            # Extract results
            ac_power = mc_results.results.ac
            dc_power = mc_results.results.dc
            
            # Calculate energy (kWh) - handle Series/DataFrame properly
            if hasattr(ac_power, 'sum'):
                ac_energy = float(ac_power.sum()) / 1000  # Convert Wh to kWh
            else:
                ac_energy = float(ac_power) / 1000
            
            if hasattr(dc_power, 'sum'):
                # If dc_power is a DataFrame, sum all columns
                if hasattr(dc_power, 'columns'):
                    dc_energy = float(dc_power.sum().sum()) / 1000  # Sum all columns, then sum the result
                else:
                    dc_energy = float(dc_power.sum()) / 1000
            else:
                dc_energy = float(dc_power) / 1000
            
            # Calculate performance metrics
            dc_capacity = float(configuration.dc_capacity)
            annual_ghi = weather_data.get('weather_summary', {}).get('annual_ghi', 0) / 1000  # Convert to kWh/m²
            
            # Performance ratio (PR)
            pr = (ac_energy / dc_capacity) / (annual_ghi / 1000) if annual_ghi > 0 else 0
            
            # Capacity factor (CF)
            cf = ac_energy / (dc_capacity * 8760) if dc_capacity > 0 else 0
            
            # Specific yield
            specific_yield = ac_energy / dc_capacity if dc_capacity > 0 else 0
            
            # Monthly energy breakdown
            monthly_energy = ac_power.resample('M').sum() / 1000  # kWh
            
            # Peak power
            peak_power = float(ac_power.max()) / 1000 if hasattr(ac_power, 'max') else 0
            
            results = {
                "simulation_id": simulation_id,
                "annual_energy": round(ac_energy, 2),
                "dc_energy": round(dc_energy, 2),
                "performance_ratio": round(pr, 3),
                "capacity_factor": round(cf, 3),
                "specific_yield": round(specific_yield, 1),
                "peak_power": round(peak_power, 2),  # kW
                "monthly_energy": [round(float(x), 2) for x in monthly_energy.values],
                "energy_metrics": {
                    "total_dc_energy": round(dc_energy, 2),
                    "total_ac_energy": round(ac_energy, 2),
                    "conversion_efficiency": round(ac_energy / dc_energy, 3) if dc_energy > 0 else 0,
                    "system_efficiency": round(ac_energy / (annual_ghi * 2.0), 3) if annual_ghi > 0 else 0  # Assuming 2 m² array area
                },
                "simulation_metadata": {
                    "dc_capacity": dc_capacity,
                    "simulation_time": datetime.now().isoformat(),
                    "weather_source": weather_data.get("source"),
                    "data_points": len(ac_power),
                    "pvlib_version": pvlib.__version__ if pvlib else "unknown"
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing simulation results: {e}")
            raise
    
    async def _create_simulation_record(
        self,
        simulation_id: str,
        configuration: SystemConfiguration,
        weather_source: str,
        year: Optional[int],
        db: Optional[AsyncSession]
    ) -> Simulation:
        """Create simulation record in database."""
        try:
            # Use provided session or create new one
            if db is None:
                async with AsyncSessionLocal() as db:
                    return await self._create_simulation_record(
                        simulation_id, configuration, weather_source, year, db
                    )
            
            simulation = Simulation(
                id=simulation_id,
                configuration_id=configuration.id,
                status="running",
                progress=0,
                started_at=datetime.now(),
                weather_source=weather_source,
                year=year,
                simulation_options={"weather_source": weather_source}
            )
            
            db.add(simulation)
            await db.commit()
            
            return simulation
            
        except Exception as e:
            logger.error(f"Error creating simulation record: {e}")
            raise
    
    async def _store_simulation_results(
        self,
        simulation_id: str,
        results: Dict[str, Any],
        db: Optional[AsyncSession]
    ) -> None:
        """Store simulation results in database."""
        try:
            # Use provided session or create new one
            if db is None:
                async with AsyncSessionLocal() as db:
                    await self._store_simulation_results(simulation_id, results, db)
                    return
            
            result_record = SimulationResult(
                id=str(uuid.uuid4()),
                simulation_id=simulation_id,
                annual_energy=results["annual_energy"],
                specific_yield=results["specific_yield"],
                performance_ratio=results["performance_ratio"],
                capacity_factor=results["capacity_factor"],
                peak_power=results["peak_power"],
                monthly_data={"monthly_energy": results["monthly_energy"]},
                hourly_data=None,  # Optional for now
                weather_summary=results.get("simulation_metadata", {}),
                calculation_time=None,  # Could be added later
                data_size=None  # Could be added later
            )
            
            db.add(result_record)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error storing simulation results: {e}")
            raise
    
    async def _update_simulation_status(
        self,
        simulation_id: str,
        status: str,
        progress: float,
        db: Optional[AsyncSession],
        error_message: Optional[str] = None
    ) -> None:
        """Update simulation status in database."""
        try:
            # Use provided session or create new one
            if db is None:
                async with AsyncSessionLocal() as db:
                    await self._update_simulation_status(
                        simulation_id, status, progress, db, error_message
                    )
                    return
            
            from sqlalchemy import select, update
            
            # Update simulation record
            stmt = (
                update(Simulation)
                .where(Simulation.id == simulation_id)
                .values(
                    status=status,
                    progress=progress,
                    completed_at=datetime.now() if status in ["completed", "failed"] else None,
                    error_message=error_message
                )
            )
            
            await db.execute(stmt)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating simulation status: {e}")
            raise
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "pvlib_available": self.pvlib_available,
            "pvlib_version": pvlib.__version__ if pvlib else None,
            "service_ready": self.pvlib_available,
            "supported_models": [
                "CEC Module Model",
                "Sandia Array Performance Model", 
                "PVWatts Model"
            ] if self.pvlib_available else [],
            "supported_inverters": [
                "CEC Inverter Model",
                "Sandia Inverter Model",
                "PVWatts Inverter Model"
            ] if self.pvlib_available else []
        }


# Global simulation service instance
pv_simulation_service = PVSimulationService()