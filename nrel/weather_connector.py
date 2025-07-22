"""
Weather Data Connector for PVLib Simulations.

Provides unified interface for fetching weather data from multiple sources:
- NREL NSRDB (National Solar Radiation Database) - Primary source
- PVGIS (Photovoltaic Geographical Information System) - Fallback source

Includes caching, error handling, and automatic fallback logic.
"""

import time
import pandas as pd
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Add pvlib-python to path if not already available
try:
    import pvlib
except ImportError:
    project_root = Path(__file__).parent.parent
    pvlib_path = project_root / "pvlib-python"
    if pvlib_path.exists():
        sys.path.insert(0, str(pvlib_path))
        import pvlib
    else:
        raise ImportError("pvlib not found. Install with: pip install pvlib-python")

from .config import config, get_logger

logger = get_logger(__name__)

class WeatherDataConnector:
    """
    Unified weather data connector with multiple source support.
    
    Provides automatic fallback from NREL NSRDB to PVGIS, with local caching
    to improve performance and reduce API calls.
    """
    
    def __init__(self, 
                 primary_source: str = 'nsrdb',
                 fallback_sources: list = None,
                 enable_cache: bool = True):
        """
        Initialize the weather data connector.
        
        Parameters
        ----------
        primary_source : str, default 'nsrdb'
            Primary weather data source ('nsrdb' or 'pvgis')
        fallback_sources : list, optional
            List of fallback sources. Default is ['pvgis'] if primary is 'nsrdb'
        enable_cache : bool, default True
            Whether to enable local caching of weather data
        """
        self.primary_source = primary_source
        
        if fallback_sources is None:
            if primary_source == 'nsrdb':
                self.fallback_sources = ['pvgis']
            else:
                self.fallback_sources = ['nsrdb']
        else:
            self.fallback_sources = fallback_sources
        
        self.enable_cache = enable_cache
        self.last_used_source = None
        self.last_request_time = 0
        
        # Validate configuration
        self._validate_sources()
        
        logger.info(f"WeatherDataConnector initialized: primary={primary_source}, "
                   f"fallbacks={self.fallback_sources}, cache={enable_cache}")
    
    def _validate_sources(self) -> None:
        """Validate that the configured sources are available."""
        if self.primary_source == 'nsrdb' and not config.is_nrel_available():
            logger.warning("NREL NSRDB not properly configured. Check NREL_API_KEY and NREL_USER_EMAIL.")
    
    def get_weather_data(self, 
                        latitude: float, 
                        longitude: float, 
                        year: Optional[int] = None,
                        use_tmy: bool = None) -> pd.DataFrame:
        """
        Get weather data for specified location and time period.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Specific year for weather data. If None, TMY data is used
        use_tmy : bool, optional
            Force TMY data usage. If None, determined by year parameter
            
        Returns
        -------
        pd.DataFrame
            Weather data with columns: ghi, dni, dhi, temp_air, wind_speed
            
        Raises
        ------
        Exception
            If all weather data sources fail
        """
        # Validate inputs
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
        
        # Determine if using TMY
        if use_tmy is None:
            use_tmy = year is None
        
        # Check cache first
        if self.enable_cache:
            cached_data = self._load_from_cache(latitude, longitude, year)
            if cached_data is not None:
                logger.info(f"Loaded weather data from cache for {latitude:.4f}, {longitude:.4f}")
                self.last_used_source = 'cache'
                return cached_data
        
        # Try each source in order
        sources_to_try = [self.primary_source] + self.fallback_sources
        
        for source in sources_to_try:
            try:
                logger.info(f"Attempting to fetch weather data from {source} for "
                           f"{latitude:.4f}, {longitude:.4f}")
                
                # Rate limiting
                self._enforce_rate_limit()
                
                if source == 'nsrdb':
                    weather_data = self._get_nsrdb_data(latitude, longitude, year, use_tmy)
                elif source == 'pvgis':
                    weather_data = self._get_pvgis_data(latitude, longitude)
                else:
                    logger.warning(f"Unknown weather data source: {source}")
                    continue
                
                # Validate the returned data
                validated_data = self._validate_weather_data(weather_data, source)
                
                # Cache the data
                if self.enable_cache:
                    self._save_to_cache(validated_data, latitude, longitude, source, year)
                
                self.last_used_source = source
                logger.info(f"Successfully retrieved weather data from {source}")
                return validated_data
                
            except Exception as e:
                logger.warning(f"Failed to get weather data from {source}: {str(e)}")
                continue
        
        # If all sources failed
        raise Exception(f"All weather data sources failed for location {latitude:.4f}, {longitude:.4f}")
    
    def _get_nsrdb_data(self, 
                       latitude: float, 
                       longitude: float, 
                       year: Optional[int] = None,
                       use_tmy: bool = False) -> pd.DataFrame:
        """
        Fetch weather data from NREL NSRDB.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees  
        year : int, optional
            Specific year for data
        use_tmy : bool
            Whether to use TMY data
            
        Returns
        -------
        pd.DataFrame
            Weather data from NSRDB
        """
        if not config.is_nrel_available():
            raise Exception("NREL NSRDB not available - check API configuration")
        
        nrel_config = config.get_nrel_config()
        
        try:
            if use_tmy or year is None:
                # Get TMY data
                nrel_config_tmy = nrel_config.copy()
                nrel_config_tmy['names'] = 'tmy'
                weather, metadata = pvlib.iotools.get_psm3(
                    latitude=latitude,
                    longitude=longitude,
                    **nrel_config_tmy
                )
                logger.debug(f"Retrieved TMY data from NSRDB: {len(weather)} records")
            else:
                # Get specific year data
                nrel_config_year = nrel_config.copy()
                nrel_config_year['names'] = str(year)
                weather, metadata = pvlib.iotools.get_psm3(
                    latitude=latitude,
                    longitude=longitude,
                    **nrel_config_year
                )
                logger.debug(f"Retrieved {year} data from NSRDB: {len(weather)} records")
            
            # Log metadata
            if metadata:
                logger.debug(f"NSRDB metadata: {metadata.get('Station Name', 'Unknown')} "
                           f"({metadata.get('Distance (km)', 'Unknown')} km)")
            
            return weather
            
        except Exception as e:
            raise Exception(f"NREL NSRDB API error: {str(e)}")
    
    def _get_pvgis_data(self, latitude: float, longitude: float) -> pd.DataFrame:
        """
        Fetch TMY weather data from PVGIS.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
            
        Returns
        -------
        pd.DataFrame
            Weather data from PVGIS
        """
        try:
            pvgis_config = config.get_pvgis_config()
            
            weather, metadata = pvlib.iotools.get_pvgis_tmy(
                latitude=latitude,
                longitude=longitude,
                **pvgis_config
            )
            
            logger.debug(f"Retrieved TMY data from PVGIS: {len(weather)} records")
            
            # Log metadata
            if metadata:
                logger.debug(f"PVGIS metadata: {metadata.get('location', 'Unknown')}")
            
            return weather
            
        except Exception as e:
            raise Exception(f"PVGIS API error: {str(e)}")
    
    def _validate_weather_data(self, data: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Validate weather data and ensure required columns are present.
        
        Parameters
        ----------
        data : pd.DataFrame
            Raw weather data
        source : str
            Data source name for logging
            
        Returns
        -------
        pd.DataFrame
            Validated weather data
        """
        if data is None or data.empty:
            raise ValueError(f"Empty weather data received from {source}")
        
        required_columns = config.required_columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns from {source}: {missing_columns}")
        
        # Check for reasonable data ranges
        validation_ranges = {
            'ghi': (0, 1500),
            'dni': (0, 1200), 
            'dhi': (0, 500),
            'temp_air': (-50, 60),
            'wind_speed': (0, 50)
        }
        
        for column, (min_val, max_val) in validation_ranges.items():
            if column in data.columns:
                out_of_range = ((data[column] < min_val) | (data[column] > max_val)).sum()
                if out_of_range > 0:
                    logger.warning(f"{source}: {out_of_range} out-of-range values in {column}")
        
        # Check for missing data
        missing_data = data[required_columns].isnull().sum()
        if missing_data.any():
            logger.warning(f"{source}: Missing data counts: {missing_data.to_dict()}")
        
        logger.debug(f"Weather data validation passed for {source}: "
                    f"{len(data)} records, {len(data.columns)} columns")
        
        return data
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < config.retry_delay:
            sleep_time = config.retry_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _load_from_cache(self, 
                        latitude: float, 
                        longitude: float, 
                        year: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Load weather data from cache if available and not expired.
        
        Parameters
        ----------
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        year : int, optional
            Specific year
            
        Returns
        -------
        pd.DataFrame or None
            Cached weather data if available, None otherwise
        """
        if not self.enable_cache:
            return None
        
        # Try to find cached data from any source
        for source in ['nsrdb', 'pvgis']:
            # Try both parquet and pickle extensions
            for ext in ['.parquet', '.pkl']:
                cache_path = config.get_cache_path(latitude, longitude, source, year)
                cache_path = cache_path.with_suffix(ext)
                
                if cache_path.exists():
                    try:
                        # Check if cache is expired
                        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                        if cache_age.days > config.cache_expiry_days:
                            logger.debug(f"Cache expired for {cache_path.name}")
                            cache_path.unlink()  # Delete expired cache
                            continue
                        
                        # Load cached data
                        if ext == '.parquet':
                            cached_data = pd.read_parquet(cache_path)
                        else:
                            cached_data = pd.read_pickle(cache_path)
                        logger.debug(f"Loaded cached data from {cache_path.name}")
                        return cached_data
                        
                    except Exception as e:
                        logger.warning(f"Failed to load cache from {cache_path}: {e}")
                        continue
        
        return None
    
    def _save_to_cache(self, 
                      data: pd.DataFrame, 
                      latitude: float, 
                      longitude: float, 
                      source: str,
                      year: Optional[int] = None) -> None:
        """
        Save weather data to cache.
        
        Parameters
        ----------
        data : pd.DataFrame
            Weather data to cache
        latitude : float
            Latitude in decimal degrees
        longitude : float
            Longitude in decimal degrees
        source : str
            Data source name
        year : int, optional
            Specific year
        """
        if not self.enable_cache:
            return
        
        try:
            cache_path = config.get_cache_path(latitude, longitude, source, year)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try parquet first, fall back to pickle if pyarrow not available
            try:
                data.to_parquet(cache_path, compression='snappy')
            except ImportError:
                # Fall back to pickle if pyarrow not available
                cache_path = cache_path.with_suffix('.pkl')
                data.to_pickle(cache_path)
            
            logger.debug(f"Saved weather data to cache: {cache_path.name}")
            
        except Exception as e:
            logger.warning(f"Failed to save weather data to cache: {e}")
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cached weather data.
        
        Parameters
        ----------
        older_than_days : int, optional
            Only clear cache files older than this many days.
            If None, clear all cache files.
            
        Returns
        -------
        int
            Number of cache files removed
        """
        if not config.cache_dir.exists():
            return 0
        
        removed_count = 0
        cutoff_time = None
        
        if older_than_days is not None:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
        
        # Clear both parquet and pickle cache files
        for pattern in ["*.parquet", "*.pkl"]:
            for cache_file in config.cache_dir.glob(pattern):
                try:
                    if cutoff_time is None:
                        # Remove all files
                        cache_file.unlink()
                        removed_count += 1
                    else:
                        # Check file age
                        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if file_time < cutoff_time:
                            cache_file.unlink()
                            removed_count += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {removed_count} cache files")
        return removed_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the weather data cache.
        
        Returns
        -------
        Dict[str, Any]
            Cache information including file count, total size, etc.
        """
        if not config.cache_dir.exists():
            return {'cache_enabled': False, 'cache_dir': str(config.cache_dir)}
        
        cache_files = list(config.cache_dir.glob("*.parquet")) + list(config.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        # Analyze cache files by source
        sources = {}
        for cache_file in cache_files:
            source = cache_file.name.split('_')[0]
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        
        info = {
            'cache_enabled': self.enable_cache,
            'cache_dir': str(config.cache_dir),
            'total_files': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'files_by_source': sources,
            'cache_expiry_days': config.cache_expiry_days
        }
        
        return info
    
    def test_connection(self, test_lat: float = 40.0, test_lon: float = -105.0) -> Dict[str, bool]:
        """
        Test connection to all configured weather data sources.
        
        Parameters
        ----------
        test_lat : float, default 40.0
            Test latitude (NREL, Colorado)
        test_lon : float, default -105.0
            Test longitude (NREL, Colorado)
            
        Returns
        -------
        Dict[str, bool]
            Connection test results for each source
        """
        results = {}
        
        # Test NSRDB
        if 'nsrdb' in [self.primary_source] + self.fallback_sources:
            try:
                if config.is_nrel_available():
                    # Try a small request
                    self._get_nsrdb_data(test_lat, test_lon, use_tmy=True)
                    results['nsrdb'] = True
                    logger.info("NSRDB connection test: SUCCESS")
                else:
                    results['nsrdb'] = False
                    logger.warning("NSRDB connection test: FAILED (not configured)")
            except Exception as e:
                results['nsrdb'] = False
                logger.warning(f"NSRDB connection test: FAILED ({e})")
        
        # Test PVGIS
        if 'pvgis' in [self.primary_source] + self.fallback_sources:
            try:
                # Try a small request (European location for better PVGIS coverage)
                self._get_pvgis_data(52.5, 13.4)  # Berlin
                results['pvgis'] = True
                logger.info("PVGIS connection test: SUCCESS")
            except Exception as e:
                results['pvgis'] = False
                logger.warning(f"PVGIS connection test: FAILED ({e})")
        
        return results