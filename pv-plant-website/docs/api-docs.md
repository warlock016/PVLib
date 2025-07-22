# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, no authentication is required. Future versions may implement API key authentication.

## Response Format
All API responses follow a standard format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Success message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error message",
  "details": { ... },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### System Configuration

#### Configure PV System
Configure a new PV system for simulation.

**Endpoint:** `POST /api/configure`

**Request Body:**
```json
{
  "location": {
    "latitude": 40.0,
    "longitude": -105.0,
    "elevation": 1650,
    "timezone": "US/Mountain"
  },
  "system": {
    "dc_capacity": 5000,
    "module_type": "First_Solar__Inc__FS_6440A",
    "inverter_type": "SMA_America__SB5000US__240V_",
    "modules_per_string": 20,
    "strings_per_inverter": 250
  },
  "array": {
    "mounting_type": "fixed",
    "tilt": 25,
    "azimuth": 180,
    "tracking_type": null,
    "gcr": 0.4
  },
  "losses": {
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
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "configuration_id": "conf_123456",
    "location": { ... },
    "system": { ... },
    "array": { ... },
    "losses": { ... }
  },
  "message": "System configured successfully"
}
```

#### Get Available Modules
Retrieve list of available PV modules from the CEC database.

**Endpoint:** `GET /api/modules`

**Query Parameters:**
- `technology` (optional): Filter by technology type (c-Si, CdTe, CIGS, etc.)
- `manufacturer` (optional): Filter by manufacturer name
- `min_power` (optional): Minimum power rating in watts
- `max_power` (optional): Maximum power rating in watts

**Response:**
```json
{
  "success": true,
  "data": {
    "modules": [
      {
        "name": "Canadian_Solar_Inc__CS5P_220M",
        "technology": "c-Si",
        "manufacturer": "Canadian Solar Inc",
        "power_rating": 220,
        "efficiency": 13.4,
        "area": 1.64,
        "parameters": {
          "alpha_sc": 0.0006,
          "beta_oc": -0.0032,
          "gamma_r": -0.0045,
          "NOCT": 45.0
        }
      }
    ],
    "total_count": 1500
  },
  "message": "Modules retrieved successfully"
}
```

#### Get Available Inverters
Retrieve list of available inverters from the CEC database.

**Endpoint:** `GET /api/inverters`

**Query Parameters:**
- `manufacturer` (optional): Filter by manufacturer name
- `min_power` (optional): Minimum power rating in watts
- `max_power` (optional): Maximum power rating in watts

**Response:**
```json
{
  "success": true,
  "data": {
    "inverters": [
      {
        "name": "SMA_America__SB5000US__240V_",
        "manufacturer": "SMA America",
        "power_rating": 5000,
        "efficiency": 96.5,
        "parameters": {
          "Paco": 5000,
          "Pdco": 5165,
          "Vdco": 310,
          "Pso": 19.7,
          "C0": -0.000008,
          "C1": -0.000002,
          "C2": -0.000001,
          "C3": 0.000021,
          "Pnt": 0.17
        }
      }
    ],
    "total_count": 800
  },
  "message": "Inverters retrieved successfully"
}
```

### Weather Data

#### Get Weather Data
Fetch weather data for a specific location and year.

**Endpoint:** `GET /api/weather/{latitude}/{longitude}`

**Path Parameters:**
- `latitude`: Latitude in decimal degrees (-90 to 90)
- `longitude`: Longitude in decimal degrees (-180 to 180)

**Query Parameters:**
- `year` (optional): Specific year (1998-2020 for NSRDB, current year for PVGIS)
- `source` (optional): Preferred data source ('nsrdb' or 'pvgis')

**Response:**
```json
{
  "success": true,
  "data": {
    "location": {
      "latitude": 40.0,
      "longitude": -105.0,
      "elevation": 1650,
      "timezone": "US/Mountain"
    },
    "source": "nsrdb",
    "year": 2020,
    "data_quality": {
      "coverage": 99.8,
      "missing_hours": 18,
      "quality_flags": {
        "excellent": 8500,
        "good": 242,
        "fair": 18,
        "poor": 0
      }
    },
    "weather_data": [
      {
        "timestamp": "2020-01-01T00:00:00Z",
        "ghi": 0,
        "dni": 0,
        "dhi": 0,
        "temp_air": -5.2,
        "wind_speed": 3.1
      }
    ]
  },
  "message": "Weather data retrieved successfully"
}
```

#### Test Weather Data Connection
Test connection to weather data sources.

**Endpoint:** `GET /api/weather/test`

**Response:**
```json
{
  "success": true,
  "data": {
    "sources": {
      "nsrdb": {
        "available": true,
        "response_time": 1.23,
        "last_tested": "2024-01-01T12:00:00Z"
      },
      "pvgis": {
        "available": true,
        "response_time": 0.89,
        "last_tested": "2024-01-01T12:00:00Z"
      }
    }
  },
  "message": "Weather service status retrieved"
}
```

### Simulation

#### Run PV Simulation
Execute a PV performance simulation.

**Endpoint:** `POST /api/simulate`

**Request Body:**
```json
{
  "configuration_id": "conf_123456",
  "simulation_options": {
    "year": 2020,
    "weather_source": "nsrdb",
    "clear_sky_model": "ineichen",
    "irradiance_model": "perez",
    "dc_model": "cec",
    "ac_model": "sandia",
    "aoi_model": "physical",
    "spectral_model": "no_loss",
    "temperature_model": "sapm"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "configuration_id": "conf_123456",
    "status": "running",
    "progress": 0,
    "estimated_completion": "2024-01-01T12:05:00Z"
  },
  "message": "Simulation started successfully"
}
```

#### Get Simulation Status
Check the status of a running simulation.

**Endpoint:** `GET /api/simulate/{simulation_id}/status`

**Response:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "status": "completed",
    "progress": 100,
    "started_at": "2024-01-01T12:00:00Z",
    "completed_at": "2024-01-01T12:03:45Z",
    "duration": 225
  },
  "message": "Simulation completed successfully"
}
```

#### Get Simulation Results
Retrieve results from a completed simulation.

**Endpoint:** `GET /api/results/{simulation_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "configuration_id": "conf_123456",
    "summary": {
      "annual_energy": 7850.5,
      "specific_yield": 1570.1,
      "performance_ratio": 0.84,
      "capacity_factor": 0.179,
      "peak_power": 4850.2
    },
    "monthly_data": [
      {
        "month": 1,
        "energy": 520.3,
        "avg_power": 697.2,
        "peak_power": 3850.1,
        "performance_ratio": 0.78,
        "capacity_factor": 0.139
      }
    ],
    "weather_summary": {
      "annual_ghi": 1650.5,
      "annual_dni": 1950.8,
      "avg_temperature": 12.5,
      "avg_wind_speed": 4.2
    }
  },
  "message": "Results retrieved successfully"
}
```

### Data Export

#### Export Results as CSV
Export simulation results in CSV format.

**Endpoint:** `GET /api/export/{simulation_id}`

**Query Parameters:**
- `resolution` (optional): Data resolution ('hourly', 'daily', 'monthly', 'annual')
- `format` (optional): Export format ('csv', 'json')

**Response:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="simulation_results.csv"

timestamp,ac_power,dc_power,ghi,dni,dhi,temp_air,wind_speed
2020-01-01T00:00:00Z,0,0,0,0,0,-5.2,3.1
2020-01-01T01:00:00Z,0,0,0,0,0,-5.8,2.9
...
```

#### Generate PDF Report
Generate a PDF report of simulation results.

**Endpoint:** `GET /api/report/{simulation_id}`

**Response:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="pv_simulation_report.pdf"

[PDF binary data]
```

### System Information

#### Get System Info
Get information about the API and system status.

**Endpoint:** `GET /api/info`

**Response:**
```json
{
  "success": true,
  "data": {
    "api_version": "1.0.0",
    "pvlib_version": "0.13.0",
    "python_version": "3.9.12",
    "system_status": "healthy",
    "uptime": 86400,
    "database_status": "connected",
    "weather_services": {
      "nsrdb": "available",
      "pvgis": "available"
    }
  },
  "message": "System information retrieved"
}
```

## Error Codes

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: External service unavailable

### Application Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `WEATHER_SERVICE_ERROR`: Weather data service unavailable
- `SIMULATION_ERROR`: Simulation execution failed
- `DATABASE_ERROR`: Database operation failed
- `EXPORT_ERROR`: Data export failed
- `CONFIGURATION_ERROR`: Invalid system configuration

## Rate Limiting
- **General API**: 100 requests per minute per IP
- **Weather Data**: 10 requests per minute per IP
- **Simulation**: 5 concurrent simulations per IP
- **Export**: 20 requests per minute per IP

## WebSocket API (Future Enhancement)

### Real-time Simulation Updates
Connect to WebSocket for real-time simulation progress updates.

**Endpoint:** `ws://localhost:8000/ws/simulation/{simulation_id}`

**Messages:**
```json
{
  "type": "progress",
  "data": {
    "simulation_id": "sim_789012",
    "progress": 45,
    "current_step": "calculating_irradiance",
    "estimated_completion": "2024-01-01T12:03:00Z"
  }
}
```

## SDK Examples

### Python
```python
import requests

# Configure system
config = {
    "location": {"latitude": 40.0, "longitude": -105.0},
    "system": {"dc_capacity": 5000, "module_type": "..."},
    "array": {"mounting_type": "fixed", "tilt": 25},
    "losses": {"soiling": 2.0, "shading": 3.0}
}

response = requests.post("http://localhost:8000/api/configure", json=config)
config_id = response.json()["data"]["configuration_id"]

# Run simulation
sim_request = {
    "configuration_id": config_id,
    "simulation_options": {"year": 2020}
}

response = requests.post("http://localhost:8000/api/simulate", json=sim_request)
sim_id = response.json()["data"]["simulation_id"]

# Get results
results = requests.get(f"http://localhost:8000/api/results/{sim_id}")
print(results.json()["data"]["summary"])
```

### JavaScript
```javascript
// Configure system
const config = {
  location: { latitude: 40.0, longitude: -105.0 },
  system: { dc_capacity: 5000, module_type: "..." },
  array: { mounting_type: "fixed", tilt: 25 },
  losses: { soiling: 2.0, shading: 3.0 }
};

const configResponse = await fetch('/api/configure', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(config)
});

const { configuration_id } = await configResponse.json();

// Run simulation
const simResponse = await fetch('/api/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    configuration_id,
    simulation_options: { year: 2020 }
  })
});

const { simulation_id } = await simResponse.json();

// Get results
const results = await fetch(`/api/results/${simulation_id}`);
const data = await results.json();
console.log(data.summary);
```