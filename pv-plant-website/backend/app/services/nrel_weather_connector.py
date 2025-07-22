"""
Simplified NREL Weather Data Connector for PV Plant Website.

This is a simplified version of the NREL weather connector specifically
designed for the pv-plant-website project, avoiding relative import issues.
"""

import os
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pvlib
try:
    import pvlib
    from pvlib import iotools
except ImportError:
    pvlib = None
    iotools = None

logger = logging.getLogger(__name__)


class SimpleWeatherConnector:
    """
    Simplified weather data connector for NREL and PVGIS data.
    """
    
    def __init__(self):
        """Initialize the connector."""
        self.nrel_api_key = os.getenv('NREL_API_KEY')
        self.nrel_user_email = os.getenv('NREL_USER_EMAIL')
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Check if pvlib is available
        self.pvlib_available = pvlib is not None
        
        if not self.pvlib_available:
            logger.warning("PVLib not available - weather connector disabled")
        elif not self.nrel_api_key:
            logger.warning("NREL API key not configured")
        else:
            logger.info("Weather connector initialized successfully")
    
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None,
        use_tmy: bool = False
    ) -> Dict[str, Any]:
        """
        Get weather data for a location.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Year for weather data
        use_tmy : bool, default False
            Whether to use TMY data
            
        Returns
        -------
        dict
            Weather data with metadata
        """
        if not self.pvlib_available:
            raise RuntimeError("PVLib not available")
        
        try:
            # Try NREL NSRDB first
            if self.nrel_api_key:
                try:
                    return self._get_nsrdb_data(latitude, longitude, year, use_tmy)
                except Exception as e:
                    logger.warning(f"NREL NSRDB failed: {e}, trying PVGIS")
            
            # Fallback to PVGIS
            return self._get_pvgis_data(latitude, longitude, year, use_tmy)
            
        except Exception as e:
            logger.error(f"All weather sources failed: {e}")
            raise
    
    def _get_nsrdb_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None,
        use_tmy: bool = False
    ) -> Dict[str, Any]:
        """Get data from NREL NSRDB."""
        if use_tmy or year is None:
            # Use TMY data (default is 2014-2020 TMY)
            data, metadata = iotools.get_psm3(
                latitude=latitude,
                longitude=longitude,
                api_key=self.nrel_api_key,
                email=self.nrel_user_email,
                map_variables=True,
                leap_day=True,
                interval=60,
                timeout=self.timeout
            )
        else:
            # Use specific year (limit to available years)
            # PSM3 data is available from 1998-2020
            if year < 1998 or year > 2020:
                logger.warning(f"Year {year} not available in NSRDB, using TMY data")
                year = None
            
            data, metadata = iotools.get_psm3(
                latitude=latitude,
                longitude=longitude,
                names=str(year) if year else 'tmy',
                api_key=self.nrel_api_key,
                email=self.nrel_user_email,
                map_variables=True,
                leap_day=True,
                interval=60,
                timeout=self.timeout
            )
        
        # Add source information
        metadata['source'] = 'nsrdb'
        if year:
            metadata['year'] = year
        
        return {
            'data': data,
            'metadata': metadata
        }
    
    def _get_pvgis_data(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None,
        use_tmy: bool = False
    ) -> Dict[str, Any]:
        """Get data from PVGIS."""
        # PVGIS primarily provides TMY data
        data, _, metadata, _ = iotools.get_pvgis_tmy(
            latitude=latitude,
            longitude=longitude,
            outputformat='json',
            usehorizon=True,
            userhorizon=None,
            startyear=None,
            endyear=None,
            map_variables=True,
            url='https://re.jrc.ec.europa.eu/api/v5_2/',
            timeout=self.timeout
        )
        
        # Add source information
        metadata['source'] = 'pvgis'
        if year:
            metadata['year'] = year
        
        return {
            'data': data,
            'metadata': metadata
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connections to weather data sources.
        
        Returns
        -------
        dict
            Connection test results
        """
        results = {
            'pvlib_available': self.pvlib_available,
            'nsrdb_available': bool(self.nrel_api_key),
            'pvgis_available': True,  # PVGIS doesn't require API key
            'sources': {}
        }
        
        if not self.pvlib_available:
            results['sources']['nsrdb'] = 'unavailable (pvlib not installed)'
            results['sources']['pvgis'] = 'unavailable (pvlib not installed)'
            return results
        
        # Test NSRDB
        if self.nrel_api_key:
            try:
                # Test with a simple request
                start_time = time.time()
                self._get_nsrdb_data(40.0, -105.0, use_tmy=True)
                response_time = time.time() - start_time
                
                results['sources']['nsrdb'] = {
                    'status': 'available',
                    'response_time': round(response_time, 2),
                    'last_tested': datetime.now().isoformat()
                }
            except Exception as e:
                results['sources']['nsrdb'] = {
                    'status': 'error',
                    'error': str(e),
                    'last_tested': datetime.now().isoformat()
                }
        else:
            results['sources']['nsrdb'] = 'unavailable (no API key)'
        
        # Test PVGIS
        try:
            start_time = time.time()
            self._get_pvgis_data(45.0, 8.0, use_tmy=True)
            response_time = time.time() - start_time
            
            results['sources']['pvgis'] = {
                'status': 'available',
                'response_time': round(response_time, 2),
                'last_tested': datetime.now().isoformat()
            }
        except Exception as e:
            results['sources']['pvgis'] = {
                'status': 'error',
                'error': str(e),
                'last_tested': datetime.now().isoformat()
            }
        
        return results


# Global connector instance
weather_connector = SimpleWeatherConnector()