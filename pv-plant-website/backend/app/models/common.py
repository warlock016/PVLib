"""
Common Pydantic models used across the application.

This module contains base models and common response structures
used throughout the API.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SuccessResponse(BaseResponse):
    """Success response model."""
    
    success: bool = Field(default=True, description="Always true for success responses")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class ErrorResponse(BaseResponse):
    """Error response model."""
    
    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""
    
    error: str = Field(default="Validation error", description="Error type")
    details: Dict[str, Any] = Field(..., description="Validation error details")


class LocationModel(BaseModel):
    """Geographic location model."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    elevation: Optional[float] = Field(default=None, description="Elevation in meters above sea level")
    timezone: Optional[str] = Field(default=None, description="IANA timezone identifier")


class DateRange(BaseModel):
    """Date range model."""
    
    start_date: datetime = Field(..., description="Start date and time")
    end_date: datetime = Field(..., description="End date and time")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Pagination parameters model."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        """Create paginated response."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )


class HealthStatus(BaseModel):
    """Health status model."""
    
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    uptime: Optional[float] = Field(default=None, description="Uptime in seconds")
    database_status: Optional[str] = Field(default=None, description="Database connection status")
    weather_services: Optional[Dict[str, str]] = Field(default=None, description="Weather service status")


class SystemInfo(BaseModel):
    """System information model."""
    
    api_version: str = Field(..., description="API version")
    pvlib_version: str = Field(..., description="PVLib version")
    python_version: str = Field(..., description="Python version")
    system_status: str = Field(..., description="System status")
    uptime: float = Field(..., description="System uptime in seconds")
    database_status: str = Field(..., description="Database status")
    weather_services: Dict[str, str] = Field(..., description="Weather service status")


class ProgressUpdate(BaseModel):
    """Progress update model for long-running operations."""
    
    operation_id: str = Field(..., description="Operation identifier")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    status: str = Field(..., description="Current status")
    message: str = Field(..., description="Progress message")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")


class FileInfo(BaseModel):
    """File information model."""
    
    filename: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="File creation time")


class ExportRequest(BaseModel):
    """Export request model."""
    
    format: str = Field(..., description="Export format (csv, json, xlsx)")
    resolution: str = Field(default="hourly", description="Data resolution")
    include_weather: bool = Field(default=True, description="Include weather data")
    include_metadata: bool = Field(default=True, description="Include metadata")
    date_range: Optional[DateRange] = Field(default=None, description="Date range filter")


class CacheInfo(BaseModel):
    """Cache information model."""
    
    total_entries: int = Field(..., description="Total cache entries")
    total_size_mb: float = Field(..., description="Total cache size in MB")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    oldest_entry: Optional[datetime] = Field(default=None, description="Oldest cache entry")
    newest_entry: Optional[datetime] = Field(default=None, description="Newest cache entry")


class RateLimitInfo(BaseModel):
    """Rate limit information model."""
    
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Reset time")
    window_seconds: int = Field(..., description="Rate limit window in seconds")


class ApiKey(BaseModel):
    """API key model (future enhancement)."""
    
    key: str = Field(..., description="API key")
    name: str = Field(..., description="API key name")
    permissions: list = Field(default=[], description="API key permissions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")
    is_active: bool = Field(default=True, description="Whether key is active")


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    """Detailed error information model."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field that caused the error")
    value: Optional[Any] = Field(default=None, description="Value that caused the error")


class ValidationError(BaseModel):
    """Validation error model."""
    
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(default=None, description="Invalid value")
    constraint: Optional[str] = Field(default=None, description="Validation constraint")


class MetricValue(BaseModel):
    """Metric value model."""
    
    name: str = Field(..., description="Metric name")
    value: Union[int, float, str] = Field(..., description="Metric value")
    unit: Optional[str] = Field(default=None, description="Value unit")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TimeSeriesPoint(BaseModel):
    """Time series data point model."""
    
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[int, float] = Field(..., description="Data point value")
    quality: Optional[str] = Field(default=None, description="Data quality indicator")


class GeoPoint(BaseModel):
    """Geographic point model."""
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation: Optional[float] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda v: round(v, 6)  # Limit coordinate precision
        }