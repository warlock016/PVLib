"""
Database configuration and models for the PV Plant Modeling API.

This module sets up SQLAlchemy database connection and defines
all database models for the application.
"""

import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, create_engine, MetaData, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

from .config import settings

logger = logging.getLogger(__name__)

# Database URL conversion for async
if settings.DATABASE_URL.startswith("sqlite"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
elif settings.DATABASE_URL.startswith("postgresql"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = settings.DATABASE_URL

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create sync session factory
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Base class for all models
Base = declarative_base()
metadata = MetaData()


class SystemConfiguration(Base):
    """Database model for PV system configurations."""
    
    __tablename__ = "system_configurations"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Location information
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    timezone = Column(String, nullable=False)
    
    # System specifications
    dc_capacity = Column(Float, nullable=False)  # kW
    module_type = Column(String, nullable=False)
    inverter_type = Column(String, nullable=False)
    modules_per_string = Column(Integer, nullable=False)
    strings_per_inverter = Column(Integer, nullable=False)
    
    # Array configuration
    mounting_type = Column(String, nullable=False)  # fixed, single_axis, dual_axis
    tilt = Column(Float, nullable=True)
    azimuth = Column(Float, nullable=True)
    tracking_type = Column(String, nullable=True)
    gcr = Column(Float, nullable=True)  # Ground coverage ratio
    
    # Loss parameters (stored as JSON)
    losses = Column(JSON, nullable=False)
    
    # Relationships
    simulations = relationship("Simulation", back_populates="configuration")


class WeatherData(Base):
    """Database model for weather data cache."""
    
    __tablename__ = "weather_data"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Data source and metadata
    source = Column(String, nullable=False)  # nsrdb, pvgis
    year = Column(Integer, nullable=True)
    data_quality = Column(JSON, nullable=True)
    
    # Weather data (stored as JSON)
    data = Column(JSON, nullable=False)
    
    # Indexes
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )


class Simulation(Base):
    """Database model for PV simulations."""
    
    __tablename__ = "simulations"
    
    id = Column(String, primary_key=True, index=True)
    configuration_id = Column(String, ForeignKey("system_configurations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Simulation status
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    progress = Column(Float, default=0.0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Simulation options
    weather_source = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    simulation_options = Column(JSON, nullable=False)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Relationships
    configuration = relationship("SystemConfiguration", back_populates="simulations")
    results = relationship("SimulationResult", back_populates="simulation", uselist=False)


class SimulationResult(Base):
    """Database model for simulation results."""
    
    __tablename__ = "simulation_results"
    
    id = Column(String, primary_key=True, index=True)
    simulation_id = Column(String, ForeignKey("simulations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Summary metrics
    annual_energy = Column(Float, nullable=False)  # kWh/year
    specific_yield = Column(Float, nullable=False)  # kWh/kWp/year
    performance_ratio = Column(Float, nullable=False)
    capacity_factor = Column(Float, nullable=False)
    peak_power = Column(Float, nullable=False)  # kW
    
    # Detailed results (stored as JSON)
    monthly_data = Column(JSON, nullable=False)
    hourly_data = Column(JSON, nullable=True)  # Optional, large dataset
    weather_summary = Column(JSON, nullable=False)
    
    # Metadata
    calculation_time = Column(Float, nullable=True)  # seconds
    data_size = Column(Integer, nullable=True)  # bytes
    
    # Relationships
    simulation = relationship("Simulation", back_populates="results")


class UserSession(Base):
    """Database model for user sessions (future enhancement)."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Session data
    session_data = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Rate limiting
    request_count = Column(Integer, default=0, nullable=False)
    last_request_at = Column(DateTime, nullable=True)


# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Sync database dependency (for migrations)
def get_sync_db():
    """Get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


def create_tables():
    """Create database tables synchronously."""
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully (sync)")


async def drop_tables():
    """Drop all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully")


# Database utility functions
async def cleanup_expired_weather_data():
    """Clean up expired weather data entries."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("DELETE FROM weather_data WHERE expires_at < :now"),
            {"now": datetime.utcnow()}
        )
        await db.commit()
        logger.info(f"Cleaned up {result.rowcount} expired weather data entries")


async def cleanup_old_simulations():
    """Clean up old simulation results."""
    cutoff_date = datetime.utcnow() - timedelta(days=settings.RESULTS_RETENTION_DAYS)
    
    async with AsyncSessionLocal() as db:
        # Delete old simulation results
        result = await db.execute(
            text("DELETE FROM simulation_results WHERE created_at < :cutoff"),
            {"cutoff": cutoff_date}
        )
        
        # Delete old simulations
        result2 = await db.execute(
            text("DELETE FROM simulations WHERE created_at < :cutoff"),
            {"cutoff": cutoff_date}
        )
        
        await db.commit()
        logger.info(f"Cleaned up {result.rowcount} old simulation results and {result2.rowcount} old simulations")


async def get_database_stats():
    """Get database statistics."""
    async with AsyncSessionLocal() as db:
        stats = {}
        
        # Count records in each table
        for table_name in ["system_configurations", "weather_data", "simulations", "simulation_results"]:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            stats[table_name] = result.scalar()
        
        return stats