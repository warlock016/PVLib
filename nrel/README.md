# NREL Weather Data Connector

A unified weather data connector for PV simulations using pvlib-python, designed to work with the Ampere dataset. Provides automatic fallback between NREL NSRDB and PVGIS data sources with local caching.

## Features

- **Multi-source weather data**: Primary NREL NSRDB with PVGIS fallback
- **Automatic fallback**: Seamlessly switches between data sources
- **Local caching**: Reduces API calls and improves performance  
- **Ampere data support**: Handles both dataset formats (`pvlib_ready.json` and `with_panel_data.json`)
- **Data validation**: Ensures weather data quality and completeness
- **Error handling**: Robust error handling with meaningful messages

## Quick Start

### 1. Installation

Install required dependencies:

```bash
pip install -r nrel/requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root with your NREL API credentials:

```env
NREL_API_KEY=your_api_key_here
NREL_USER_EMAIL=your_email@domain.com
NREL_USER_ID=your_user_id_here
```

Get your free NREL API key at: https://developer.nrel.gov/signup/

### 3. Basic Usage

```python
from nrel.weather_connector import WeatherDataConnector
from nrel.data_utils import load_ampere_facilities, process_facility

# Initialize weather connector
weather = WeatherDataConnector()

# Load facility data
facilities = load_ampere_facilities('ampere/temp/pvlib_ready.json')

# Process a facility
facility = facilities[0]
system, location = process_facility(facility)

# Get weather data (automatic source selection and caching)
weather_data = weather.get_weather_data(
    latitude=location.latitude,
    longitude=location.longitude,
    year=2023
)

print(f"Retrieved weather data from: {weather.last_used_source}")
print(f"Data shape: {weather_data.shape}")
```

### 4. Run Example

```bash
cd /path/to/PVLib
python nrel/example_usage.py
```

## API Reference

### WeatherDataConnector

The main class for fetching weather data from multiple sources.

#### Constructor

```python
WeatherDataConnector(
    primary_source='nsrdb',
    fallback_sources=['pvgis'], 
    enable_cache=True
)
```

**Parameters:**
- `primary_source` (str): Primary data source ('nsrdb' or 'pvgis')
- `fallback_sources` (list): List of fallback sources  
- `enable_cache` (bool): Enable local caching

#### Methods

##### get_weather_data()

```python
get_weather_data(latitude, longitude, year=None, use_tmy=None)
```

Fetch weather data for specified location and time period.

**Parameters:**
- `latitude` (float): Latitude in decimal degrees (-90 to 90)
- `longitude` (float): Longitude in decimal degrees (-180 to 180)
- `year` (int, optional): Specific year for data. If None, uses TMY
- `use_tmy` (bool, optional): Force TMY usage

**Returns:**
- `pd.DataFrame`: Weather data with columns: ghi, dni, dhi, temp_air, wind_speed

##### test_connection()

```python
test_connection(test_lat=40.0, test_lon=-105.0)
```

Test connection to all configured weather data sources.

**Returns:**
- `dict`: Connection status for each source

##### clear_cache()

```python
clear_cache(older_than_days=None)
```

Clear cached weather data files.

**Parameters:**
- `older_than_days` (int, optional): Only clear files older than N days

**Returns:**
- `int`: Number of files removed

##### get_cache_info()

```python
get_cache_info()
```

Get information about the weather data cache.

**Returns:**
- `dict`: Cache statistics (file count, size, etc.)

### Data Utilities

Functions for processing Ampere facility data.

#### load_ampere_facilities()

```python
load_ampere_facilities(file_path)
```

Load facility data from JSON file.

**Parameters:**
- `file_path` (str): Path to JSON file

**Returns:**
- `list`: List of facility dictionaries

#### process_facility()

```python
process_facility(facility)
```

Convert Ampere facility data to pvlib PVSystem and Location objects.

**Parameters:**
- `facility` (dict): Facility data dictionary

**Returns:**
- `tuple`: (PVSystem, Location) objects

#### get_facility_summary()

```python
get_facility_summary(facilities)
```

Generate summary statistics for facility list.

**Parameters:**
- `facilities` (list): List of facility dictionaries

**Returns:**
- `dict`: Summary statistics

## Data Sources

### NREL NSRDB (Primary)

- **Coverage**: Global (best for Americas)
- **Resolution**: Hourly, 4km spatial resolution
- **Data**: PSM3 physical solar model
- **Cost**: Free with API key (daily limits)
- **Years**: 1998-2020 (historical), 2007-2018 (TMY)

### PVGIS (Fallback)

- **Coverage**: Europe (excellent), Asia, Africa, limited Americas  
- **Resolution**: Hourly, varies by region
- **Data**: Satellite-derived and reanalysis
- **Cost**: Free, no registration required
- **Years**: TMY based on 2005-2020 data

## Caching

The connector automatically caches weather data locally to improve performance:

- **Format**: Parquet files with snappy compression
- **Location**: `nrel/cache/` directory
- **Naming**: `{source}_{lat}_{lon}_{year}.parquet`
- **Expiry**: 30 days (configurable)

Cache files are automatically created and managed. You can control caching behavior:

```python
# Disable caching
weather = WeatherDataConnector(enable_cache=False)

# Clear old cache files
weather.clear_cache(older_than_days=7)

# Get cache statistics
info = weather.get_cache_info()
print(f"Cache size: {info['total_size_mb']:.1f} MB")
```

## Error Handling

The connector includes robust error handling:

1. **Input validation**: Validates coordinates and parameters
2. **API errors**: Catches and logs API failures
3. **Automatic fallback**: Tries alternative data sources
4. **Data validation**: Checks weather data quality
5. **Meaningful errors**: Provides clear error messages

Common error scenarios:

```python
try:
    weather_data = weather.get_weather_data(lat, lon, year=2023)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"All weather sources failed: {e}")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover nrel/tests/

# Run specific test file
python -m unittest nrel.tests.test_weather_connector

# Run with verbose output
python -m unittest nrel.tests.test_weather_connector -v
```

## Configuration

Configuration is managed through environment variables and the `config.py` module:

### Environment Variables

- `NREL_API_KEY`: Your NREL API key (required for NSRDB)
- `NREL_USER_EMAIL`: Your email for NREL API (required for NSRDB)
- `NREL_USER_ID`: Your NREL user ID (optional)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Configuration Options

```python
from nrel.config import config

# API settings
config.max_retries = 3
config.timeout = 30
config.retry_delay = 1.0

# Cache settings  
config.cache_enabled = True
config.cache_expiry_days = 30

# Weather data columns
config.required_columns = ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
```

## Limitations

1. **NREL API limits**: Free tier has daily request limits
2. **PVGIS coverage**: Limited coverage in Americas
3. **Data years**: NSRDB historical data ends in 2020
4. **Cache storage**: Local cache can grow large over time

## Troubleshooting

### Common Issues

**"NREL NSRDB not available"**
- Check that `NREL_API_KEY` and `NREL_USER_EMAIL` are set in `.env`
- Verify API key is valid at https://developer.nrel.gov/

**"All weather data sources failed"**
- Check internet connection
- Verify coordinates are in valid ranges
- Check if location is supported by available data sources

**"Cache permission errors"**
- Ensure write permissions for `nrel/cache/` directory
- Try clearing cache: `weather.clear_cache()`

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
# LOG_LEVEL=DEBUG
```

### Test Connections

```python
from nrel.weather_connector import WeatherDataConnector

weather = WeatherDataConnector()
results = weather.test_connection()

for source, status in results.items():
    print(f"{source}: {'✓' if status else '✗'}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

## License

This project follows the same license as the parent PVLib project.