# Facility Data Collection and Validation System

This document describes the comprehensive system for collecting historical facility data from the Ampere API and validating pvlib simulation results against actual facility performance.

## Overview

The system consists of several components that work together to:

1. **Fix existing query issues** in the Ampere API client
2. **Fetch historical facility data** from 2020-2024 for all 313 facilities
3. **Process raw data** with unit validation and standardization
4. **Validate simulation results** against actual facility performance
5. **Generate comprehensive reports** and visualizations

## System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Ampere API        │    │   Raw Data          │    │   Processed Data    │
│   (GraphQL)         │───►│   Files             │───►│   Files             │
│                     │    │   (JSON)            │    │   (JSON)            │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                                                    │
                                                                    ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Validation        │    │   Simulation        │    │   Validation        │
│   Reports           │◄───│   Results           │◄───│   Analysis          │
│   (JSON + Plots)    │    │   (JSON)            │    │   Framework         │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Components

### 1. Fixed Query System (`ampere/queries/facility.py`)

**Fixed Issues:**
- ✅ `execute_get_facility()` now uses `GET_FACILITY_QUERY` instead of `GET_COMPANIES_QUERY`
- ✅ Function signature updated to accept `facility_id` and `date` parameters
- ✅ Proper variable passing to GraphQL query

**Usage:**
```python
from ampere.queries.facility import execute_get_facility
from ampere.client import GraphQLClient

response = execute_get_facility(client, "facility_id", "2022-01-01T00:00:00Z")
```

### 2. Historical Data Fetcher (`ampere/fetch_historical_data.py`)

**Features:**
- Fetches data for all 313 facilities from `pvlib_ready.json`
- Queries multiple years (2020-2024) per facility
- Handles partial/empty responses due to migration timing
- Includes progress tracking and error handling
- Implements rate limiting and retry logic
- Saves data by year: `raw_facility_data_YYYY.json`

**Usage:**
```python
from ampere.fetch_historical_data import FacilityDataFetcher
from ampere.config import Config

config = Config.from_env()
fetcher = FacilityDataFetcher(config)

# Fetch data for all years
results = fetcher.fetch_historical_data(
    year_range=(2020, 2024),
    save_by_year=True,
    max_retries=3,
    delay_between_requests=0.1
)
```

### 3. Raw Data Processor (`ampere/process_raw_data.py`)

**Features:**
- Processes raw facility data with unit validation
- Handles all reading types: Pac, Energy, Irradiation, ET, GO, PacLimitRel, Meter
- Converts units to standard format (kW, kWh, kW/m²)
- Calculates facility-level metrics and statistics
- Validates data quality and completeness
- Saves processed data: `processed_facility_data_YYYY.json`

**Key Unit Conversions:**
- Power: W → kW (divide by 1000)
- Energy: Wh → kWh (divide by 1000)
- Irradiance: W/m² → kW/m² (divide by 1000)
- Power Limit: % → ratio (divide by 100)

### 4. Validation Framework (`nrel/validation_analysis.py`)

**Features:**
- Direct kWh-to-kWh comparison between simulation and actual data
- Comprehensive validation metrics (R², RMSE, MAPE, correlation)
- Facility-level and aggregate analysis
- Statistical validation of annual energy and specific yield
- Automated report generation and visualization

**Key Metrics:**
- **Annual Energy Validation**: Total kWh comparison
- **Specific Yield Validation**: kWh/kWp comparison
- **Performance Ratio**: Actual vs expected performance
- **Capacity Factor**: Utilization analysis

### 5. Main Collection Script (`collect_facility_data.py`)

**Features:**
- Orchestrates the complete data collection pipeline
- Command-line interface with flexible options
- Progress tracking and error handling
- Automated report generation
- Configurable year ranges and validation parameters

**Usage:**
```bash
# Full pipeline with default settings
python collect_facility_data.py

# Custom year range and validation
python collect_facility_data.py --years 2020-2023 --validation-year 2022

# Skip certain steps
python collect_facility_data.py --skip-fetch --validation-year 2022

# Verbose output
python collect_facility_data.py --verbose
```

### 6. Test Suite (`test_facility_pipeline.py`)

**Features:**
- Comprehensive unit tests for all components
- Mock data testing for isolated component verification
- Integration tests for end-to-end functionality
- Unit conversion and validation testing

## Data Flow

### 1. Data Collection
```
Facility IDs (pvlib_ready.json) → API Queries → Raw Data Files
```

### 2. Data Processing
```
Raw Data Files → Unit Validation → Processed Data Files
```

### 3. Validation
```
Processed Data + Simulation Results → Validation Analysis → Reports
```

## File Structure

```
├── ampere/
│   ├── queries/
│   │   └── facility.py                 # Fixed GraphQL query
│   ├── fetch_historical_data.py        # Multi-year data fetcher
│   ├── process_raw_data.py             # Unit-aware data processor
│   └── temp/                           # Data storage
│       ├── raw_facility_data_2020.json
│       ├── raw_facility_data_2021.json
│       ├── ...
│       ├── processed_facility_data_2020.json
│       └── processed_facility_data_2021.json
├── nrel/
│   ├── validation_analysis.py          # Validation framework
│   └── results/                        # Validation outputs
│       ├── validation_report_2022_*.json
│       ├── annual_energy_validation.png
│       └── specific_yield_validation.png
├── collect_facility_data.py            # Main orchestration script
└── test_facility_pipeline.py           # Test suite
```

## Usage Examples

### Basic Data Collection
```bash
# Run complete pipeline
python collect_facility_data.py

# Check results
ls nrel/results/
ls ampere/temp/
```

### Validation Only
```bash
# Skip data collection, run validation
python collect_facility_data.py --skip-fetch --skip-process --validation-year 2022
```

### Custom Configuration
```bash
# Custom year range with slower API requests
python collect_facility_data.py --years 2020-2022 --delay 0.5 --max-retries 5
```

## Expected Outputs

### 1. Raw Data Files
- `ampere/temp/raw_facility_data_YYYY.json`
- Contains complete API responses with all reading types
- Includes metadata about query success/failure

### 2. Processed Data Files
- `ampere/temp/processed_facility_data_YYYY.json`
- Standardized units and validated data
- Facility-level metrics and statistics

### 3. Validation Reports
- `nrel/results/validation_report_YYYY_timestamp.json`
- Comprehensive validation metrics
- Facility-by-facility comparison data

### 4. Visualization Plots
- `nrel/results/annual_energy_validation.png`
- `nrel/results/specific_yield_validation.png`
- Scatter plots and error distributions

## Configuration

### Environment Variables
```bash
# Required for API access
export APOLLO_GATEWAY_URL="https://api.ampere.com/graphql"
export API_TOKEN="your_api_token_here"

# Optional
export TIMEOUT=30
```

### Performance Settings
- **Rate Limiting**: Default 0.1 seconds between requests
- **Retry Logic**: Maximum 3 retries with exponential backoff
- **Batch Processing**: Processes by facility and year
- **Memory Management**: Saves data incrementally by year

## Testing

```bash
# Run all tests
python test_facility_pipeline.py

# Expected output:
# ✓ Facility Query Fix: PASSED
# ✓ Data Fetcher: PASSED
# ✓ Data Processor: PASSED
# ✓ Validation Analyzer: PASSED
# ✓ Unit Conversion: PASSED
```

## Troubleshooting

### Common Issues

1. **API Authentication Errors**
   - Check `APOLLO_GATEWAY_URL` and `API_TOKEN` environment variables
   - Verify API token has correct permissions

2. **Missing Data Files**
   - Ensure `pvlib_ready.json` exists in `ampere/temp/`
   - Check that simulation results exist in `nrel/results/`

3. **Unit Validation Warnings**
   - Review unexpected unit warnings in processor output
   - Check API response format changes

4. **Memory Issues**
   - Reduce year range for large datasets
   - Increase delay between requests to reduce load

### Performance Optimization

1. **For large datasets**: Use `--years 2022-2022` to process single year
2. **For testing**: Use `--skip-fetch` to work with existing data
3. **For API limits**: Increase `--delay` parameter

## Future Enhancements

1. **Database Storage**: Replace JSON files with database storage
2. **Real-time Updates**: Add streaming data collection
3. **Advanced Analytics**: Time-series analysis and forecasting
4. **Web Interface**: Dashboard for interactive validation
5. **Multi-threading**: Parallel data collection for faster processing

## Support

For issues or questions:
1. Check the test suite results
2. Review error messages in collection summary
3. Verify API credentials and network connectivity
4. Check file permissions in temp directories