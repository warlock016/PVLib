"""
Configuration management for NREL weather data connector.

Handles environment variables, API configurations, and default settings.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for weather data connector."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        
        # NREL API Configuration
        self.nrel_api_key = os.getenv('NREL_API_KEY')
        self.nrel_user_email = os.getenv('NREL_USER_EMAIL')
        self.nrel_user_id = os.getenv('NREL_USER_ID')
        
        # API Endpoints
        self.nrel_base_url = "https://developer.nrel.gov/api/nsrdb"
        self.pvgis_base_url = "https://re.jrc.ec.europa.eu/api/v5_2"
        
        # Default parameters
        self.default_year = 2023
        self.default_interval = 60  # minutes
        self.default_leap_day = True
        
        # Weather data columns
        self.required_columns = ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
        self.optional_columns = ['surface_albedo', 'surface_pressure']
        
        # Rate limiting
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.timeout = 30  # seconds
        
        # Caching
        self.cache_dir = Path(__file__).parent / "cache"
        self.cache_enabled = True
        self.cache_expiry_days = 30
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Validate configuration
        self._validate_config()
        
        # Setup logging
        self._setup_logging()
        
        # Create cache directory
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.nrel_api_key:
            logging.warning("NREL_API_KEY not found in environment. NREL NSRDB will not be available.")
        
        if not self.nrel_user_email:
            logging.warning("NREL_USER_EMAIL not found in environment. NREL NSRDB may not work properly.")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_nrel_config(self) -> Dict[str, Any]:
        """Get NREL API configuration parameters."""
        return {
            'api_key': self.nrel_api_key,
            'email': self.nrel_user_email,
            'names': self.required_columns,
            'interval': self.default_interval,
            'leap_day': self.default_leap_day,
            'timeout': self.timeout
        }
    
    def get_pvgis_config(self) -> Dict[str, Any]:
        """Get PVGIS API configuration parameters."""
        return {
            'outputformat': 'csv',
            'usehorizon': True,
            'startyear': 2005,
            'endyear': 2020,
            'timeout': self.timeout
        }
    
    def is_nrel_available(self) -> bool:
        """Check if NREL API is properly configured."""
        return bool(self.nrel_api_key and self.nrel_user_email)
    
    def get_cache_path(self, latitude: float, longitude: float, 
                      source: str, year: Optional[int] = None) -> Path:
        """Generate cache file path for weather data."""
        lat_str = f"{latitude:.4f}"
        lon_str = f"{longitude:.4f}"
        
        if year:
            filename = f"{source}_{lat_str}_{lon_str}_{year}.parquet"
        else:
            filename = f"{source}_{lat_str}_{lon_str}_tmy.parquet"
        
        return self.cache_dir / filename

# Global configuration instance
config = Config()

def load_config() -> Config:
    """Load and return the global configuration instance."""
    return config

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)