"""
Configuration settings for the PV Plant Modeling API.

This module defines all configuration settings using Pydantic Settings
for type validation and environment variable loading.
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "PV Plant Modeling API"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development", env="ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./pv_plant_db.sqlite", env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="CORS_ORIGINS"
    )
    
    # NREL API settings
    NREL_API_KEY: str = Field(..., env="NREL_API_KEY")
    NREL_USER_EMAIL: str = Field(..., env="NREL_USER_EMAIL")
    NREL_USER_ID: Optional[str] = Field(default=None, env="NREL_USER_ID")
    
    # Weather data settings
    WEATHER_CACHE_ENABLED: bool = Field(default=True, env="WEATHER_CACHE_ENABLED")
    WEATHER_CACHE_EXPIRY_DAYS: int = Field(default=30, env="WEATHER_CACHE_EXPIRY_DAYS")
    WEATHER_REQUEST_TIMEOUT: int = Field(default=30, env="WEATHER_REQUEST_TIMEOUT")
    WEATHER_MAX_RETRIES: int = Field(default=3, env="WEATHER_MAX_RETRIES")
    
    # Simulation settings
    MAX_CONCURRENT_SIMULATIONS: int = Field(default=5, env="MAX_CONCURRENT_SIMULATIONS")
    SIMULATION_TIMEOUT: int = Field(default=300, env="SIMULATION_TIMEOUT")  # 5 minutes
    RESULTS_RETENTION_DAYS: int = Field(default=30, env="RESULTS_RETENTION_DAYS")
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="simple", env="LOG_FORMAT")  # simple or json
    
    # File paths
    DATA_DIR: Path = Field(default=Path(__file__).parent.parent / "data", env="DATA_DIR")
    CACHE_DIR: Path = Field(default=Path(__file__).parent.parent / "cache", env="CACHE_DIR")
    LOGS_DIR: Path = Field(default=Path(__file__).parent.parent / "logs", env="LOGS_DIR")
    
    # PVLib settings
    PVLIB_MODULE_DATABASE: str = Field(default="cecmod", env="PVLIB_MODULE_DATABASE")
    PVLIB_INVERTER_DATABASE: str = Field(default="cecinverter", env="PVLIB_INVERTER_DATABASE")
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string."""
        if isinstance(v, str):
            return v
        elif isinstance(v, list):
            return ",".join(v)
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()
    
    @validator("DATA_DIR", "CACHE_DIR", "LOGS_DIR")
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL with proper formatting."""
    return settings.DATABASE_URL


def get_cache_dir() -> Path:
    """Get cache directory path."""
    return settings.CACHE_DIR


def get_logs_dir() -> Path:
    """Get logs directory path."""
    return settings.LOGS_DIR


def get_data_dir() -> Path:
    """Get data directory path."""
    return settings.DATA_DIR


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.DEBUG


def is_production() -> bool:
    """Check if running in production mode."""
    return not settings.DEBUG


# Weather data configuration
WEATHER_CONFIG = {
    "nsrdb": {
        "base_url": "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv",
        "api_key": settings.NREL_API_KEY,
        "email": settings.NREL_USER_EMAIL,
        "timeout": settings.WEATHER_REQUEST_TIMEOUT,
        "max_retries": settings.WEATHER_MAX_RETRIES
    },
    "pvgis": {
        "base_url": "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc",
        "timeout": settings.WEATHER_REQUEST_TIMEOUT,
        "max_retries": settings.WEATHER_MAX_RETRIES
    }
}

# PVLib configuration
PVLIB_CONFIG = {
    "module_database": settings.PVLIB_MODULE_DATABASE,
    "inverter_database": settings.PVLIB_INVERTER_DATABASE,
    "default_losses": {
        "soiling": 2.0,
        "shading": 3.0,
        "snow": 0.0,
        "mismatch": 2.0,
        "wiring": 2.0,
        "connections": 0.5,
        "lid": 1.5,
        "nameplate_rating": 1.0,
        "age": 0.0,
        "availability": 0.0
    },
    "temperature_models": {
        "sapm": "sapm",
        "pvsyst": "pvsyst",
        "fuentes": "fuentes",
        "noct": "noct"
    },
    "dc_models": {
        "cec": "cec",
        "sapm": "sapm",
        "pvwatts": "pvwatts",
        "singlediode": "singlediode"
    },
    "ac_models": {
        "sandia": "sandia",
        "adr": "adr",
        "pvwatts": "pvwatts"
    }
}

# Simulation configuration
SIMULATION_CONFIG = {
    "max_concurrent": settings.MAX_CONCURRENT_SIMULATIONS,
    "timeout": settings.SIMULATION_TIMEOUT,
    "default_year": 2020,
    "supported_years": list(range(1998, 2024)),
    "default_weather_source": "nsrdb",
    "fallback_weather_source": "pvgis"
}

# Export configuration
EXPORT_CONFIG = {
    "formats": ["csv", "json", "xlsx"],
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "csv_separator": ",",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "decimal_places": 3
}