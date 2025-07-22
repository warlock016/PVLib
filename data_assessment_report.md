# PVLib Data Assessment Report: Ampere Dataset Analysis

## Executive Summary

Based on analysis of the Ampere dataset in `/ampere/temp/`, I've evaluated the available data against pvlib-python simulation requirements. The dataset contains **313 PV facilities** with comprehensive system configuration data but **lacks critical weather/irradiance data** required for pvlib simulations.

## Dataset Overview

### Available Files
- **`ampere_data.json`**: Raw facility data (268k lines, 7.2MB)
- **`pvlib_ready.json`**: Processed facility data optimized for pvlib (5k lines, 313 facilities) - uses "tilt"
- **`with_panel_data.json`**: Enhanced data with module specifications (15k lines, 387KB) - uses "elevation" for tilt angle

### Geographic Coverage
- **313 unique facilities** across **282 unique locations**
- Global coverage: Europe (Germany dominant), South America (Brazil), other regions
- Facilities range from 323.4 kW to multi-MW installations

### Data Structure Differences
**Important**: The datasets use different field names for panel tilt angle:
- **`pvlib_ready.json`**: Uses `"tilt"` for panel tilt angle
- **`with_panel_data.json`**: Uses `"elevation"` for panel tilt angle (same concept, different naming)

Both refer to the panel tilt angle in degrees from horizontal, which pvlib calls `surface_tilt`.

## Data Completeness Analysis

### ✅ **AVAILABLE DATA** (Complete for PVLib Requirements)

#### 1. **Location Data** (100% Complete)
```json
{
  "latitude": 49.9643178,
  "longitude": 9.0833321, 
  "timezone": "Europe/Berlin"
}
```
- **Coverage**: All 313 facilities have precise coordinates
- **Quality**: High precision (7+ decimal places)
- **Timezones**: Properly formatted IANA timezone strings

#### 2. **System Configuration** (100% Complete)
```json
{
  "facility_power_kw": 323.4,
  "panel_groups": [
    {
      "name": "Halle 1+4+5 Nordost",
      "azimuth": 52,        // Panel orientation (degrees)
      "tilt": 3,            // Panel tilt angle (degrees) - NOTE: Called "elevation" in with_panel_data.json
      "power_kw": 323.4     // Group power rating
    }
  ]
}
```
- **System sizing**: All facilities have power ratings
- **Array configuration**: Azimuth and tilt angles for all panel groups
- **Multi-array support**: Some facilities have multiple orientations

#### 3. **Module Parameters** (Available in `with_panel_data.json`)
```json
{
  "temperatureCoefficient": -0.4,      // Power temperature coefficient (%/°C)
  "yearlyDegredation": 0.004,          // Annual degradation rate
  "specificYieldPerYear": 947.49,      // kWh/kWp/year
  "monthlyDistribution": [0.0199, 0.0383, ...] // Monthly production profile
}
```
- **Temperature coefficients**: Available for most facilities (-0.29 to -0.43 %/°C)
- **Performance data**: Historical specific yields and monthly distributions

### ❌ **MISSING DATA** (Critical for PVLib Simulations)

#### 1. **Weather Data** (0% Available)
**Required for pvlib simulation:**
- `ghi`: Global Horizontal Irradiance (W/m²)
- `dni`: Direct Normal Irradiance (W/m²)
- `dhi`: Diffuse Horizontal Irradiance (W/m²)
- `temp_air`: Air temperature (°C)
- `wind_speed`: Wind speed (m/s)

**Status**: ❌ **Completely missing** - No weather/irradiance data in any file

#### 2. **Detailed Module Specifications** (Partial)
**Missing pvlib-compatible parameters:**
- Module electrical specifications (Voc, Isc, Vmp, Imp)
- NOCT (Nominal Operating Cell Temperature)
- Module area and cell count
- Specific module model identifiers for SAM database lookup

#### 3. **Inverter Parameters** (0% Available)
**Required for AC power conversion:**
- Inverter efficiency curves
- Power ratings (Paco, Pdco)
- Voltage operating ranges
- Model specifications

#### 4. **Time Series Data** (0% Available)
**Required for temporal simulation:**
- Historical production data
- Weather time series
- Performance monitoring data

## Impact Assessment

### **High Impact Missing Data**
1. **Weather Data**: **CRITICAL** - Cannot run pvlib simulations without irradiance and meteorological data
2. **Inverter Parameters**: **HIGH** - Required for AC power calculations
3. **Detailed Module Specs**: **MEDIUM** - Can use simplified PVWatts model with available data

### **Low Impact Missing Data**
1. **Historical Performance**: **LOW** - Available monthly distributions provide validation data
2. **Precise Module Models**: **LOW** - Temperature coefficients available for basic modeling

## Recommended Data Sources & Connectors

### 1. **Weather Data Sources** (Priority: CRITICAL)

#### **NREL NSRDB (National Solar Radiation Database)**
```python
# Recommended primary source
weather, metadata = pvlib.iotools.get_psm3(
    latitude=facility['latitude'],
    longitude=facility['longitude'], 
    api_key='your_api_key',
    email='your_email@domain.com',
    names=['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed'],
    year=2023
)
```
- **Coverage**: Global, high quality
- **Cost**: Free with registration (daily limits)
- **Resolution**: Hourly, 4km spatial
- **Implementation**: Direct pvlib integration

#### **PVGIS (Photovoltaic Geographical Information System)**
```python
# Free alternative for Europe/Africa/Asia
weather, months, inputs, metadata = pvlib.iotools.get_pvgis_tmy(
    latitude=facility['latitude'],
    longitude=facility['longitude'],
    startyear=2005, endyear=2020
)
```
- **Coverage**: Europe (excellent), Asia, Africa, limited Americas
- **Cost**: Free, no registration required
- **Resolution**: Hourly, varies by region
- **Implementation**: Direct pvlib integration

#### **Open-Meteo**
```python
# Free global weather API
import requests
def get_weather_data(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["temperature_2m", "wind_speed_10m", 
                  "shortwave_radiation", "direct_radiation", 
                  "diffuse_radiation"]
    }
    return requests.get(url, params=params).json()
```
- **Coverage**: Global
- **Cost**: Free (rate limited)
- **Resolution**: Hourly
- **Implementation**: Custom connector needed

### 2. **Module Database Integration** (Priority: HIGH)

#### **SAM Component Database Lookup**
```python
# Map temperature coefficients to SAM database entries
cec_modules = pvlib.pvsystem.retrieve_sam('cecmod')
sandia_modules = pvlib.pvsystem.retrieve_sam('sandiamod')

# Find best match based on power rating and temperature coefficient
def find_module_match(power_kw, temp_coeff):
    candidates = cec_modules[
        (abs(cec_modules['STC'] - power_kw*1000) < 50) &
        (abs(cec_modules['gamma_r'] - temp_coeff) < 0.05)
    ]
    return candidates.iloc[0] if len(candidates) > 0 else default_module
```

#### **Generic Module Parameters**
```python
# Create generic module based on available data
def create_generic_module(power_kw, temp_coeff):
    return {
        'pdc0': power_kw * 1000,           # Convert kW to W
        'gamma_pdc': temp_coeff / 100,     # Convert % to fraction
        'Technology': 'c-Si',              # Assume crystalline silicon
        'Vintage': 2020                    # Default vintage
    }
```

### 3. **Inverter Parameter Estimation** (Priority: MEDIUM)

#### **Power-Based Estimation**
```python
# Estimate inverter parameters from system size
def estimate_inverter_params(system_power_kw):
    return {
        'pdc0': system_power_kw * 1000,    # DC input rating
        'eta_inv_nom': 0.96,               # Typical efficiency
        'Paco': system_power_kw * 1000 * 0.96  # AC output rating
    }
```

#### **SAM Inverter Database Lookup**
```python
# Find inverters by power range
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
suitable_inverters = cec_inverters[
    (cec_inverters['Paco'] >= system_power_kw * 800) &
    (cec_inverters['Paco'] <= system_power_kw * 1200)
]
```

## Implementation Strategy

### **Phase 1: Basic Simulation Framework** (2-3 weeks)

#### **Core Data Pipeline**
```python
def process_ampere_facility(facility_data):
    """Convert Ampere facility data to pvlib-compatible format"""
    
    # Location setup
    location = pvlib.location.Location(
        latitude=facility_data['latitude'],
        longitude=facility_data['longitude'],
        tz=facility_data['timezone']
    )
    
    # System configuration
    arrays = []
    for group in facility_data['panel_groups']:
        # Handle different naming conventions: "tilt" in pvlib_ready.json, "elevation" in with_panel_data.json
        tilt_angle = group.get('tilt', group.get('elevation', 0))
        
        mount = pvlib.pvsystem.FixedMount(
            surface_tilt=tilt_angle,
            surface_azimuth=group['azimuth']
        )
        
        # Use available temperature coefficient or default
        temp_coeff = facility_data.get('temperatureCoefficient', -0.004)
        
        array = pvlib.pvsystem.Array(
            mount=mount,
            module_parameters={
                'pdc0': group['power_kw'] * 1000,
                'gamma_pdc': temp_coeff / 100
            }
        )
        arrays.append(array)
    
    # System with estimated inverter
    system = pvlib.pvsystem.PVSystem(
        arrays=arrays,
        inverter_parameters={
            'pdc0': facility_data['facility_power_kw'] * 1000,
            'eta_inv_nom': 0.96
        }
    )
    
    return system, location
```

#### **Weather Data Connector Framework**
```python
class WeatherDataConnector:
    """Unified interface for multiple weather data sources"""
    
    def __init__(self, primary_source='nsrdb', fallback_sources=['pvgis', 'open_meteo']):
        self.primary = primary_source
        self.fallbacks = fallback_sources
    
    def get_weather_data(self, latitude, longitude, year=2023):
        """Get weather data with automatic fallback"""
        for source in [self.primary] + self.fallbacks:
            try:
                if source == 'nsrdb':
                    return self._get_nsrdb_data(latitude, longitude, year)
                elif source == 'pvgis':
                    return self._get_pvgis_data(latitude, longitude)
                elif source == 'open_meteo':
                    return self._get_open_meteo_data(latitude, longitude, year)
            except Exception as e:
                print(f"Failed to get data from {source}: {e}")
                continue
        
        raise Exception("All weather data sources failed")
    
    def _get_nsrdb_data(self, lat, lon, year):
        return pvlib.iotools.get_psm3(lat, lon, year=year, **self.nsrdb_config)
    
    def _get_pvgis_data(self, lat, lon):
        weather, _, _, _ = pvlib.iotools.get_pvgis_tmy(lat, lon)
        return weather
    
    def _get_open_meteo_data(self, lat, lon, year):
        # Custom implementation for Open-Meteo API
        return self._convert_open_meteo_format(raw_data)
```

### **Phase 2: Enhanced Simulation** (3-4 weeks)

#### **Advanced Module Matching**
```python
class ModuleParameterEstimator:
    """Estimate detailed module parameters from limited data"""
    
    def __init__(self):
        self.cec_modules = pvlib.pvsystem.retrieve_sam('cecmod')
        self.sandia_modules = pvlib.pvsystem.retrieve_sam('sandiamod')
    
    def find_best_match(self, power_kw, temp_coeff, technology='c-Si'):
        """Find best matching module from databases"""
        
        # Search CEC database first
        candidates = self.cec_modules[
            (abs(self.cec_modules['STC'] - power_kw*1000) < 100) &
            (abs(self.cec_modules['gamma_r'] - temp_coeff) < 0.1) &
            (self.cec_modules['Technology'] == technology)
        ]
        
        if len(candidates) > 0:
            return candidates.iloc[0].to_dict()
        
        # Fallback to synthetic parameters
        return self._create_synthetic_module(power_kw, temp_coeff, technology)
    
    def _create_synthetic_module(self, power_kw, temp_coeff, technology):
        """Create synthetic module parameters"""
        return {
            'Technology': technology,
            'STC': power_kw * 1000,
            'gamma_r': temp_coeff,
            # Estimate other parameters based on typical values
            'V_oc_ref': 45.0,  # Typical for c-Si
            'I_sc_ref': (power_kw * 1000) / 35.0,  # Estimate based on power
            # ... other estimated parameters
        }
```

#### **Performance Validation Framework**
```python
class PerformanceValidator:
    """Validate simulations against available performance data"""
    
    def validate_facility(self, facility_data, simulation_results):
        """Compare simulation with reported performance"""
        
        # Extract available performance metrics
        reported_yield = facility_data.get('specificYieldPerYear')
        monthly_dist = facility_data.get('monthlyDistribution', [])
        
        # Calculate simulation metrics
        simulated_yield = simulation_results.ac.sum() / (facility_data['facility_power_kw'] * 1000)
        simulated_monthly = simulation_results.ac.resample('M').sum() / simulation_results.ac.sum()
        
        # Validation metrics
        yield_error = abs(simulated_yield - reported_yield) / reported_yield * 100
        monthly_rmse = np.sqrt(np.mean((simulated_monthly - monthly_dist) ** 2))
        
        return {
            'yield_error_percent': yield_error,
            'monthly_rmse': monthly_rmse,
            'validation_score': self._calculate_score(yield_error, monthly_rmse)
        }
```

### **Phase 3: Production System** (2-3 weeks)

#### **Batch Processing Framework**
```python
class AmpereSimulationEngine:
    """Production-ready simulation engine for Ampere dataset"""
    
    def __init__(self, weather_connector, module_estimator, validator):
        self.weather = weather_connector
        self.modules = module_estimator
        self.validator = validator
        
    def simulate_all_facilities(self, facilities_data, year=2023):
        """Simulate all facilities with progress tracking"""
        
        results = []
        failed_facilities = []
        
        for i, facility in enumerate(facilities_data):
            try:
                print(f"Processing facility {i+1}/{len(facilities_data)}: {facility['name']}")
                
                # Get weather data
                weather = self.weather.get_weather_data(
                    facility['latitude'], 
                    facility['longitude'], 
                    year
                )
                
                # Set up system
                system, location = process_ampere_facility(facility)
                
                # Run simulation
                mc = pvlib.modelchain.ModelChain(
                    system, location,
                    dc_model='pvwatts',
                    ac_model='pvwatts'
                )
                mc.run_model(weather)
                
                # Validate results
                validation = self.validator.validate_facility(facility, mc.results)
                
                # Store results
                results.append({
                    'facility_id': facility['id'],
                    'facility_name': facility['name'],
                    'annual_energy_kwh': mc.results.ac.sum() / 1000,
                    'capacity_factor': mc.results.ac.mean() / (facility['facility_power_kw'] * 1000) * 100,
                    'specific_yield': mc.results.ac.sum() / (facility['facility_power_kw'] * 1000),
                    'validation': validation,
                    'weather_source': self.weather.last_used_source
                })
                
            except Exception as e:
                print(f"Failed to process {facility['name']}: {e}")
                failed_facilities.append({'facility': facility, 'error': str(e)})
        
        return results, failed_facilities
    
    def export_results(self, results, filename='ampere_simulation_results.csv'):
        """Export results to CSV for analysis"""
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        return df
```

## Cost & Implementation Estimates

### **Data Acquisition Costs**
- **NREL NSRDB**: Free (313 facilities × 1 year = ~313 API calls)
- **PVGIS**: Free, unlimited for European facilities
- **Open-Meteo**: Free with rate limits
- **Development Time**: 1-2 weeks for robust connector framework

### **Development Timeline**
- **Phase 1** (Basic Framework): 2-3 weeks
- **Phase 2** (Enhanced Features): 3-4 weeks  
- **Phase 3** (Production System): 2-3 weeks
- **Total**: 7-10 weeks for complete implementation

### **Technical Requirements**
- **Dependencies**: pvlib-python, pandas, requests, numpy
- **API Keys**: NREL NSRDB (free registration)
- **Compute**: Standard workstation (313 facilities × 8760 hours = ~2.7M data points)

## Recommendations

### **Immediate Actions** (Week 1-2)
1. **Register for NREL NSRDB API key** (free, required for US/global coverage)
2. **Implement basic weather data connector** with PVGIS fallback
3. **Create facility data processor** to convert Ampere format to pvlib format
4. **Run pilot simulation** on 5-10 facilities to validate approach

### **Short-term Goals** (Week 3-6)
1. **Implement comprehensive weather data framework** with multiple sources
2. **Develop module parameter estimation** using available temperature coefficients
3. **Create validation framework** using monthly distribution data
4. **Process full dataset** (313 facilities) with basic PVWatts model

### **Medium-term Enhancements** (Week 7-10)
1. **Advanced module matching** using SAM databases
2. **Inverter parameter estimation** and optimization
3. **Performance benchmarking** against reported yields
4. **Automated data pipeline** for regular updates

### **Success Metrics**
- **Simulation Coverage**: Target 95%+ of facilities successfully simulated
- **Validation Accuracy**: <15% error vs. reported specific yields
- **Processing Speed**: <5 minutes per facility including weather data fetch
- **Data Completeness**: All critical parameters estimated or sourced

The Ampere dataset provides an excellent foundation for pvlib simulations, with comprehensive system configuration data. The main challenge is sourcing weather data, which can be effectively addressed through the recommended multi-source connector approach.