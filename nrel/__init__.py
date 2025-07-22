"""
NREL Weather Data Connector for PVLib Simulations

This package provides weather data fetching capabilities for PV simulations using:
- NREL NSRDB (National Solar Radiation Database) as primary source
- PVGIS (Photovoltaic Geographical Information System) as fallback

Main components:
- WeatherDataConnector: Main interface for weather data retrieval
- data_utils: Utilities for processing Ampere facility data
- config: Configuration and environment management
"""

from .weather_connector import WeatherDataConnector
from .data_utils import load_ampere_facilities, process_facility
from .config import load_config

__version__ = "0.1.0"
__all__ = ["WeatherDataConnector", "load_ampere_facilities", "process_facility", "load_config"]