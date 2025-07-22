# PVLib-Python: Requirements for PV Plant Simulation

This document provides comprehensive guidance on the required variables, inputs, and configurations needed to simulate photovoltaic (PV) plant power profiles, energy yield, and performance using pvlib-python.

## Table of Contents
1. [Quick Start Requirements](#quick-start-requirements)
2. [Weather Data Requirements](#weather-data-requirements)
3. [System Parameter Requirements](#system-parameter-requirements)
4. [Location Requirements](#location-requirements)
5. [Simulation Workflows](#simulation-workflows)
6. [PVLib Features & Capabilities](#pvlib-features--capabilities)
7. [Performance Metrics](#performance-metrics)
8. [Data Sources & Integration](#data-sources--integration)
9. [Best Practices](#best-practices)

## Quick Start Requirements

### Minimum Required Variables
To run a basic PV simulation in pvlib-python, you need:

**Weather Data (Time Series):**
- `ghi`: Global Horizontal Irradiance (W/m²)
- `dni`: Direct Normal Irradiance (W/m²) 
- `dhi`: Diffuse Horizontal Irradiance (W/m²)
- `temp_air`: Air temperature (°C)
- `wind_speed`: Wind speed (m/s)

**Location:**
- `latitude`: Decimal degrees
- `longitude`: Decimal degrees
- `timezone`: IANA timezone string (e.g., 'US/Arizona')

**System Configuration:**
- `surface_tilt`: Panel tilt angle (degrees)
- `surface_azimuth`: Panel azimuth angle (degrees, 180=south)
- `module_parameters`: PV module specifications
- `inverter_parameters`: Inverter specifications

### Example Minimum Setup
```python
import pvlib

# Location
location = pvlib.location.Location(32.2, -111.0, tz='US/Arizona', altitude=700)

# System
system = pvlib.pvsystem.PVSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_parameters={'pdc0': 220, 'gamma_pdc': -0.004},  # PVWatts model
    inverter_parameters={'pdc0': 220, 'eta_inv_nom': 0.96}
)

# ModelChain simulation
mc = pvlib.modelchain.ModelChain(system, location, dc_model='pvwatts')
mc.run_model(weather_data)
```

## Weather Data Requirements

### Required Variables
| Variable | Units | Description | Typical Range |
|----------|-------|-------------|---------------|
| `ghi` | W/m² | Global Horizontal Irradiance | 0 - 1200 |
| `dni` | W/m² | Direct Normal Irradiance | 0 - 1000 |
| `dhi` | W/m² | Diffuse Horizontal Irradiance | 0 - 400 |
| `temp_air` | °C | Air temperature | -40 to 50 |
| `wind_speed` | m/s | Wind speed at 10m height | 0 - 25 |

### Optional Variables
| Variable | Units | Description | Default if Missing |
|----------|-------|-------------|-------------------|
| `albedo` | - | Ground reflectance (0-1) | 0.25 |
| `pressure` | Pa | Atmospheric pressure | Standard atmosphere |
| `precipitable_water` | cm | Precipitable water | Estimated from location |

### Data Format Requirements
- **Index**: Pandas DatetimeIndex with timezone information
- **Frequency**: Typically hourly, can be sub-hourly (1-min to 1-hour)
- **Missing Data**: Use NaN, will be handled by interpolation or skipped
- **Time Convention**: Local solar time or UTC with proper timezone conversion

### Example Weather Data Structure
```python
import pandas as pd

weather_data = pd.DataFrame({
    'ghi': [0, 100, 400, 800, 600, 200, 0],
    'dni': [0, 150, 600, 900, 700, 300, 0],
    'dhi': [0, 50, 100, 150, 120, 80, 0],
    'temp_air': [15, 18, 25, 30, 28, 20, 16],
    'wind_speed': [2, 3, 5, 4, 6, 3, 2]
}, index=pd.date_range('2023-01-01', periods=7, freq='H', tz='UTC'))
```

## System Parameter Requirements

### Module Parameters

#### PVWatts Model (Simplified)
```python
module_pvwatts = {
    'pdc0': 220.0,          # DC power rating at STC (W)
    'gamma_pdc': -0.004     # Temperature coefficient (%/°C)
}
```

#### CEC Model (Detailed)
```python
module_cec = {
    'Technology': 'Mono-c-Si',    # Cell technology
    'STC': 220.0,                 # Power at STC (W)
    'PTC': 200.1,                 # Power at PTC (W)
    'A_c': 1.7,                   # Module area (m²)
    'N_s': 96,                    # Cells in series
    'I_sc_ref': 5.1,              # Short circuit current (A)
    'V_oc_ref': 59.4,             # Open circuit voltage (V)
    'I_mp_ref': 4.69,             # Max power current (A)
    'V_mp_ref': 46.9,             # Max power voltage (V)
    'alpha_sc': 0.004539,         # Isc temp coefficient (A/°C)
    'beta_oc': -0.222156,         # Voc temp coefficient (V/°C)
    'gamma_r': -0.476,            # Power temp coefficient (%/°C)
    'T_NOCT': 42.4                # NOCT (°C)
}
```

#### SAPM Model (Sandia Array Performance Model)
```python
module_sapm = {
    'Vintage': 2009,
    'Area': 1.7,                  # Module area (m²)
    'Material': 'c-Si',           # Cell material
    'Cells_in_Series': 96,
    'Parallel_Strings': 1,
    'Isco': 5.10,                 # Short circuit current (A)
    'Voco': 59.4,                 # Open circuit voltage (V)
    'Impo': 4.69,                 # Max power current (A)
    'Vmpo': 46.9,                 # Max power voltage (V)
    'Aisc': 0.004539,             # Isc temp coefficient (A/°C)
    'Aimp': 0.004539,             # Imp temp coefficient (A/°C)
    'C0': 1.0847,                 # SAPM coefficients
    'C1': -0.0847,
    'BVoco': -0.222156,           # Voc temp coefficient (V/°C)
    'Mbvoc': 0,
    'BVmpo': -0.222156,           # Vmp temp coefficient (V/°C)
    'Mbvmp': 0,
    'N': 1.45,                    # Diode ideality factor
    'C2': 0.00073,                # SAPM coefficients
    'C3': -0.00052,
    'A0': 0.928,                  # AOI coefficients
    'A1': 0.068,
    'A2': -0.0046,
    'A3': 0.0001,
    'A4': -0.000001,
    'B0': 1,                      # Spectral coefficients
    'B1': -0.002438,
    'B2': 0.0003103,
    'B3': -0.00001246,
    'B4': 0.000000211,
    'B5': -0.00000000129,
    'DTC': 3                      # Temperature difference (°C)
}
```

### Inverter Parameters

#### PVWatts Inverter
```python
inverter_pvwatts = {
    'pdc0': 220.0,              # DC input power rating (W)
    'eta_inv_nom': 0.96         # Nominal efficiency
}
```

#### CEC Inverter (California Energy Commission)
```python
inverter_cec = {
    'Paco': 250000,             # AC power rating (W)
    'Pdco': 259589,             # DC power rating (W)
    'Vdco': 600,                # DC voltage rating (V)
    'Pso': 2.08961,             # Self-consumption (W)
    'C0': -4.1e-05,             # Curvature coefficient
    'C1': -9.1e-05,             # Curvature coefficient
    'C2': 0.000494,             # Curvature coefficient
    'C3': -0.013171,            # Curvature coefficient
    'Pnt': 0.01                 # Night tare loss (W)
}
```

#### Sandia Inverter
```python
inverter_sandia = {
    'Paco': 250000,             # AC power rating (W)
    'Pdco': 259589,             # DC power rating (W)
    'Vdco': 600,                # DC voltage rating (V)
    'Pso': 2.08961,             # Start-up power (W)
    'Pntare': 0.01,             # Night tare loss (W)
    'C0': -4.1e-05,             # Polynomial coefficients
    'C1': -9.1e-05,
    'C2': 0.000494,
    'C3': -0.013171
}
```

### Array Configuration
```python
array_config = {
    'modules_per_string': 10,    # Modules in series
    'strings': 20,               # Parallel strings
    'module_parameters': module_params,
    'temperature_model_parameters': temp_params
}
```

### Temperature Model Parameters

#### SAPM Temperature Model
```python
temp_sapm = {
    'open_rack_glass_glass': {'a': -3.47, 'b': -0.0594, 'deltaT': 3},
    'close_mount_glass_glass': {'a': -2.98, 'b': -0.0471, 'deltaT': 1},
    'open_rack_glass_polymer': {'a': -3.56, 'b': -0.0750, 'deltaT': 3},
    'insulated_back_glass_polymer': {'a': -2.81, 'b': -0.0455, 'deltaT': 0}
}
```

#### Faiman Temperature Model
```python
temp_faiman = {
    'u0': 25.0,                 # Combined heat loss coefficient (W/m²/K)
    'u1': 6.84                  # Wind-related heat loss coefficient
}
```

#### Pvsyst Temperature Model
```python
temp_pvsyst = {
    'u_c': 29.0,                # Combined heat loss coefficient (W/m²/K)
    'u_v': 0.0,                 # Wind-related heat loss coefficient
    'module_efficiency': 0.2,   # Module efficiency at STC
    'alpha_absorption': 0.9     # Solar absorptance
}
```

## Location Requirements

### Required Parameters
```python
location = pvlib.location.Location(
    latitude=32.2,              # Decimal degrees (-90 to 90)
    longitude=-111.0,           # Decimal degrees (-180 to 180)
    tz='US/Arizona',            # IANA timezone string
    altitude=700,               # Elevation above sea level (m)
    name='Phoenix'              # Optional: Location name
)
```

### Common Timezone Examples
- **US**: 'US/Arizona', 'US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern'
- **Europe**: 'Europe/Berlin', 'Europe/London', 'Europe/Madrid'
- **Asia**: 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata'
- **UTC**: 'UTC' (Coordinated Universal Time)

### Altitude Considerations
- **Sea level**: altitude=0
- **Moderate elevation**: 500-2000m (affects air mass calculations)
- **High elevation**: >2000m (significant impact on irradiance)
- **Default**: If not provided, assumed to be 0m

## Simulation Workflows

### 1. Function-Level Approach (Most Flexible)
```python
# Solar position
solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)

# Extraterrestrial radiation
dni_extra = pvlib.irradiance.get_extra_radiation(times)

# Plane-of-array irradiance
poa_irrad = pvlib.irradiance.get_total_irradiance(
    surface_tilt, surface_azimuth,
    solpos['apparent_zenith'], solpos['azimuth'],
    weather['dni'], weather['ghi'], weather['dhi']
)

# Cell temperature
cell_temp = pvlib.temperature.sapm_cell(
    poa_irrad['poa_global'], weather['temp_air'], 
    weather['wind_speed'], **temp_params
)

# DC power
dc_power = pvlib.pvsystem.sapm(effective_irradiance, cell_temp, module)

# AC power
ac_power = pvlib.inverter.sandia(dc_power['v_mp'], dc_power['p_mp'], inverter)
```

### 2. Class-Level Approach (Object-Oriented)
```python
# Create system and location objects
system = pvlib.pvsystem.PVSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_parameters=module_params,
    inverter_parameters=inverter_params,
    modules_per_string=10,
    strings=20
)

location = pvlib.location.Location(lat, lon, tz='US/Arizona')

# Calculate solar position
solpos = location.get_solarposition(weather.index)

# Run simulation steps
aoi = system.get_aoi(solpos['apparent_zenith'], solpos['azimuth'])
poa_irrad = system.get_irradiance(solpos['apparent_zenith'], solpos['azimuth'],
                                  weather['dni'], weather['ghi'], weather['dhi'])
cell_temp = system.get_cell_temperature(poa_irrad['poa_global'], 
                                       weather['temp_air'], weather['wind_speed'])
dc = system.sapm(poa_irrad['poa_global'], cell_temp)
ac = system.snlinverter(dc['v_mp'], dc['p_mp'])
```

### 3. ModelChain Approach (Recommended for Most Users)
```python
# Define system using new Array/Mount structure
mount = pvlib.pvsystem.FixedMount(surface_tilt=32, surface_azimuth=180)
array = pvlib.pvsystem.Array(
    mount=mount,
    module_parameters=module_params,
    temperature_model_parameters=temp_params,
    modules_per_string=10,
    strings=20
)
system = pvlib.pvsystem.PVSystem(
    arrays=[array],
    inverter_parameters=inverter_params
)

# Create ModelChain with automatic model selection
mc = pvlib.modelchain.ModelChain(
    system, location,
    dc_model='sapm',           # Options: 'sapm', 'cec', 'pvwatts', 'singlediode'
    ac_model='sandia',         # Options: 'sandia', 'pvwatts', 'adr'
    aoi_model='physical',      # Options: 'physical', 'ashrae', 'sapm', 'martin_ruiz'
    spectral_model='sapm',     # Options: 'sapm', 'first_solar', 'no_loss'
    temperature_model='sapm',  # Options: 'sapm', 'pvsyst', 'faiman', 'fuentes'
    losses_model='pvwatts'     # Options: 'pvwatts', 'no_loss', custom function
)

# Run complete simulation
mc.run_model(weather_data)

# Access results
ac_power = mc.results.ac
dc_power = mc.results.dc
cell_temperature = mc.results.cell_temperature
plane_of_array_irradiance = mc.results.plane_of_array_irradiance
```

### 4. Advanced Configurations

#### Single-Axis Tracking System
```python
mount = pvlib.pvsystem.SingleAxisTrackerMount(
    axis_tilt=0,               # Horizontal axis
    axis_azimuth=180,          # North-south axis (180=N-S)
    max_angle=60,              # Maximum rotation angle
    backtrack=True,            # Enable backtracking
    gcr=0.35                   # Ground coverage ratio
)

array = pvlib.pvsystem.Array(
    mount=mount,
    module_parameters=module_params,
    modules_per_string=15,
    strings=1344
)
```

#### Dual-Axis Tracking System
```python
mount = pvlib.pvsystem.DualAxisTrackerMount(
    axis_tilt=0,               # Tilt of primary axis
    axis_azimuth=180,          # Azimuth of primary axis
    max_angle=60,              # Maximum rotation angles
    backtrack=True,
    gcr=0.35
)
```

#### Multi-Array System (Different Orientations)
```python
# South-facing array
array_south = pvlib.pvsystem.Array(
    mount=pvlib.pvsystem.FixedMount(surface_tilt=30, surface_azimuth=180),
    module_parameters=module_params,
    strings=100
)

# East-facing array
array_east = pvlib.pvsystem.Array(
    mount=pvlib.pvsystem.FixedMount(surface_tilt=30, surface_azimuth=90),
    module_parameters=module_params,
    strings=50
)

# Combined system
system = pvlib.pvsystem.PVSystem(
    arrays=[array_south, array_east],
    inverter_parameters=inverter_params
)
```

#### Bifacial System
```python
# Bifacial module parameters (additional parameters)
module_bifacial = module_params.copy()
module_bifacial.update({
    'bifacial': True,
    'bifaciality': 0.75,       # Rear-to-front power ratio
    'row_height': 2.0,         # Height above ground (m)
    'row_width': 2.0           # Row width (m)
})

# Bifacial irradiance calculation using pvfactors
bifacial_irrad = pvlib.bifacial.pvfactors.pvfactors_timeseries(
    solar_azimuth, solar_zenith, surface_azimuth, surface_tilt,
    axis_azimuth, times, dni, dhi, gcr, pvrow_height, pvrow_width, albedo
)
```

## PVLib Features & Capabilities

### Core Modeling Capabilities

#### 1. **Solar Position & Irradiance**
- **Solar position algorithms**: SPA (high precision), NREL SPA, PSA, ephemeris
- **Irradiance models**: 
  - Transposition: Isotropic, Klucher, Hay-Davies, Reindl, King, Perez
  - Clear-sky: Ineichen, Haurwitz, Simplified Solis, REST2, ESRA
  - Decomposition: Erbs, DISC, DIRINT, Boland

#### 2. **PV System Modeling**
- **DC Models**:
  - **PVWatts**: Simple efficiency-based model
  - **CEC**: Detailed single-diode model (California Energy Commission)
  - **SAPM**: Sandia Array Performance Model (empirical)
  - **Single-diode**: Physics-based single-diode model
  - **Two-diode**: Advanced physics-based model

- **AC Models**:
  - **PVWatts**: Simple efficiency-based inverter model
  - **Sandia**: Empirical inverter model with detailed losses
  - **ADR**: Anton Driesse Research model

#### 3. **Temperature Modeling**
- **SAPM**: Sandia Array Performance Model temperature
- **Pvsyst**: Pvsyst temperature model
- **Faiman**: Faiman temperature model
- **Fuentes**: Fuentes temperature model
- **NOCT**: Nominal Operating Cell Temperature model

#### 4. **Tracking Systems**
- **Fixed-tilt**: Stationary systems
- **Single-axis tracking**: Horizontal N-S, tilted, vertical axis
- **Dual-axis tracking**: Full sun-following capability
- **Backtracking**: Minimize shading losses
- **Slope-aware tracking**: Tracking on sloped terrain

#### 5. **Advanced Modeling Features**

##### Bifacial PV Systems
- **pvfactors integration**: Detailed rear-side irradiance modeling
- **Infinite sheds model**: Simplified bifacial calculations
- **View factor models**: Ground and sky view factor calculations

##### Agrivoltaics
- **Crop shading models**: Impact on agricultural activities
- **Ground irradiance**: Light availability for crops
- **PAR calculations**: Photosynthetically Active Radiation

##### Floating PV
- **Enhanced cooling models**: Water cooling effects
- **Reflection models**: Water surface reflectance

##### Spectral Effects
- **Spectral mismatch**: Impact of spectral variations
- **Material-specific models**: Different cell technologies
- **Air mass corrections**: Atmospheric spectral filtering

#### 6. **Loss Models & Effects**

##### Shading
- **Partial shading models**: Module-level shading effects
- **Horizon shading**: Topographic shading
- **Self-shading**: Row-to-row shading in arrays

##### Soiling
- **Hsu soiling model**: Time-varying soiling losses
- **Kimber soiling model**: Rain washing and accumulation

##### Snow
- **Coverage models**: Snow accumulation and melting
- **Sliding models**: Snow sliding off tilted modules

##### Other Losses
- **AOI losses**: Angle-of-incidence effects
- **IAM models**: Incidence Angle Modifier
- **DC/AC losses**: System component losses

### Performance Analysis Tools

#### 1. **Energy Calculations**
```python
# Annual energy yield
annual_energy = ac_power.sum() / 1000  # kWh

# Monthly energy
monthly_energy = ac_power.resample('M').sum() / 1000

# Specific yield (kWh/kWp)
system_size_kw = (modules_per_string * strings * module['STC']) / 1000
specific_yield = annual_energy / system_size_kw

# Capacity factor
capacity_factor = ac_power.mean() / (system_size_kw * 1000) * 100
```

#### 2. **Performance Metrics**
```python
# Performance ratio
poa_global = mc.results.plane_of_array_irradiance['poa_global']
dc_nameplate = system_size_kw * 1000
performance_ratio = ac_power / (poa_global / 1000 * dc_nameplate) * 100

# Final yield (hours)
final_yield = annual_energy / system_size_kw

# Reference yield (hours)
annual_irradiation = poa_global.sum() / 1000  # kWh/m²
reference_yield = annual_irradiation / 1  # kWh/m² / (kW/m²)

# Array yield
array_yield = mc.results.dc.sum() / 1000 / system_size_kw

# System efficiency
module_area = strings * modules_per_string * module['A_c']  # m²
system_efficiency = annual_energy / (annual_irradiation * module_area) * 100
```

#### 3. **Loss Analysis**
```python
# PVWatts losses (applied in ModelChain)
pvwatts_losses = {
    'soiling': 2.0,           # %
    'shading': 3.0,           # %
    'snow': 0.0,              # %
    'mismatch': 2.0,          # %
    'wiring': 2.0,            # %
    'connections': 0.5,       # %
    'lid': 1.5,               # Light-induced degradation
    'nameplate': 1.0,         # %
    'age': 0.5,               # %
    'availability': 3.0       # %
}

# Total system losses
total_losses = 1 - (1 - sum(pvwatts_losses.values())/100)
```

## Data Sources & Integration

### Weather Data Sources

#### 1. **NREL National Solar Radiation Database (NSRDB)**
```python
# PSM3 (Physical Solar Model v3)
weather, metadata = pvlib.iotools.get_psm3(
    latitude=40, longitude=-80,
    api_key='your_api_key',
    email='your_email@example.com',
    names=['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed'],
    leap_day=True,
    interval=60,  # minutes
    attributes=['air_temperature', 'dew_point', 'dhi', 'dni', 'ghi', 
                'surface_albedo', 'surface_pressure', 'wind_direction', 
                'wind_speed'],
    year=2019
)

# TMY (Typical Meteorological Year)
weather, metadata = pvlib.iotools.get_tmy_psm3(
    latitude=40, longitude=-80,
    api_key='your_api_key',
    email='your_email@example.com'
)
```

#### 2. **PVGIS (Photovoltaic Geographical Information System)**
```python
# TMY data from PVGIS
weather, months_selected, inputs, metadata = pvlib.iotools.get_pvgis_tmy(
    latitude=45, longitude=8,
    outputformat='csv',
    usehorizon=True,
    userhorizon=None,
    startyear=2005,
    endyear=2020
)

# Hourly data from PVGIS
weather, inputs, metadata = pvlib.iotools.get_pvgis_hourly(
    latitude=45, longitude=8,
    start=2019, end=2019,
    raddatabase='PVGIS-SARAH2',
    components=True,
    surface_tilt=30,
    surface_azimuth=180,
    outputformat='csv'
)
```

#### 3. **Local/Custom Weather Files**
```python
# TMY2/TMY3 files
weather, metadata = pvlib.iotools.read_tmy3('path/to/file.tm3')
weather, metadata = pvlib.iotools.read_tmy2('path/to/file.tm2')

# EPW (EnergyPlus Weather) files
weather, metadata = pvlib.iotools.read_epw('path/to/file.epw')

# Custom CSV files
weather = pd.read_csv('weather_data.csv', index_col=0, parse_dates=True)
```

### Component Databases

#### 1. **SAM (System Advisor Model) Databases**
```python
# CEC module database
cec_modules = pvlib.pvsystem.retrieve_sam('cecmod')
module = cec_modules['Canadian_Solar_CS5P_220M___2009_']

# Sandia module database
sandia_modules = pvlib.pvsystem.retrieve_sam('sandiamod')
module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']

# CEC inverter database
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
inverter = cec_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

# Sandia inverter database
sandia_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')
inverter = sandia_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
```

#### 2. **ADR (Anton Driesse Research) Database**
```python
# ADR module database with detailed IV curve parameters
adr_modules = pvlib.pvsystem.retrieve_sam('adr_library_cec_modules')

# ADR inverter database
adr_inverters = pvlib.pvsystem.retrieve_sam('adr_library_cec_inverters')
```

### Data Validation & Quality Control

#### 1. **Data Quality Checks**
```python
# Check for missing data
missing_data = weather.isnull().sum()

# Check for physically impossible values
invalid_ghi = weather['ghi'] < 0
invalid_dni = weather['dni'] < 0
invalid_temp = (weather['temp_air'] < -50) | (weather['temp_air'] > 60)

# Check for irradiance consistency
ghi_sum = weather['dhi'] + weather['dni'] * np.cos(np.radians(zenith))
ghi_diff = np.abs(weather['ghi'] - ghi_sum)
inconsistent_irr = ghi_diff > 50  # W/m²

# Clear-sky detection for data validation
clear_sky = location.get_clearsky(weather.index, model='ineichen')
clearness_index = weather['ghi'] / clear_sky['ghi']
```

#### 2. **Data Filling & Interpolation**
```python
# Simple interpolation
weather_filled = weather.interpolate(method='linear', limit=3)

# Clear-sky scaling for missing irradiance
clear_sky = location.get_clearsky(weather.index)
for component in ['ghi', 'dni', 'dhi']:
    missing_mask = weather[component].isnull()
    weather.loc[missing_mask, component] = (
        clear_sky.loc[missing_mask, component] * 
        weather[component].mean() / clear_sky[component].mean()
    )
```

## Best Practices

### 1. **Data Preparation**

#### Weather Data Best Practices
- **Time zones**: Ensure consistent timezone handling across all data
- **Data frequency**: Higher frequency (≤1 hour) provides better accuracy
- **Quality control**: Validate irradiance components and temperature ranges
- **Missing data**: Limit interpolation to small gaps (≤3 hours)
- **Leap years**: Account for February 29th in multi-year simulations

#### System Parameters
- **Use validated databases**: Prefer SAM/CEC databases over manual entry
- **Temperature coefficients**: Ensure proper units (absolute vs. relative)
- **String sizing**: Validate voltage compatibility with inverter MPPT range
- **Array configuration**: Consider electrical and mechanical constraints

### 2. **Model Selection Guidelines**

#### DC Models
- **PVWatts**: Simple studies, preliminary analysis, utility-scale
- **SAPM**: Field-validated empirical model, good for crystalline silicon
- **CEC**: Single-diode physics, good accuracy across technologies
- **Single-diode**: Research applications, custom module modeling

#### Temperature Models
- **SAPM**: Most validated, good for crystalline silicon
- **Pvsyst**: Good for detailed thermal analysis
- **Faiman**: Simple and robust for most applications

#### Irradiance Models
- **Perez**: Most accurate for tilted surfaces, standard for tracking
- **Hay-Davies**: Good compromise between accuracy and simplicity
- **Isotropic**: Simple, conservative estimates

### 3. **Simulation Validation**

#### Cross-Check Results
```python
# Sanity checks
max_theoretical_power = (
    system_size_kw * 1000 * 
    max(weather['ghi']) / 1000 * 
    module_efficiency
)
assert ac_power.max() <= max_theoretical_power

# Performance ratio bounds
assert 0.5 <= performance_ratio.mean() <= 1.2

# Capacity factor bounds
assert 0.1 <= capacity_factor <= 0.4  # Typical range for fixed systems
```

#### Compare with Measured Data
```python
# Statistical validation metrics
def validation_metrics(measured, modeled):
    bias = (modeled - measured).mean()
    rmse = np.sqrt(((modeled - measured) ** 2).mean())
    mae = np.abs(modeled - measured).mean()
    r2 = np.corrcoef(measured, modeled)[0, 1] ** 2
    
    return {
        'bias': bias,
        'rmse': rmse,
        'mae': mae,
        'r_squared': r2,
        'normalized_rmse': rmse / measured.mean() * 100
    }

# Apply to different time aggregations
hourly_metrics = validation_metrics(measured_hourly, modeled_hourly)
daily_metrics = validation_metrics(measured_daily, modeled_daily)
monthly_metrics = validation_metrics(measured_monthly, modeled_monthly)
```

### 4. **Performance Optimization**

#### Computational Efficiency
```python
# Use ModelChain for standard workflows
mc = pvlib.modelchain.ModelChain(system, location)
mc.run_model(weather)  # Optimized computation chain

# Vectorized operations for large datasets
results = []
for chunk in weather_chunks:
    mc.run_model(chunk)
    results.append(mc.results.ac)
combined_results = pd.concat(results)

# Parallel processing for parameter studies
from multiprocessing import Pool

def simulate_tilt(tilt):
    system.surface_tilt = tilt
    mc.run_model(weather)
    return mc.results.ac.sum()

with Pool() as pool:
    annual_yields = pool.map(simulate_tilt, range(0, 61, 5))
```

#### Memory Management
```python
# Process data in chunks for large datasets
chunk_size = 8760  # One year of hourly data
total_energy = 0

for chunk in pd.read_csv('large_weather_file.csv', chunksize=chunk_size):
    mc.run_model(chunk)
    total_energy += mc.results.ac.sum()
```

### 5. **Documentation & Reproducibility**

#### Document System Configuration
```python
# Save system configuration
system_config = {
    'location': {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'timezone': str(location.tz),
        'altitude': location.altitude
    },
    'system': {
        'surface_tilt': system.surface_tilt,
        'surface_azimuth': system.surface_azimuth,
        'modules_per_string': system.modules_per_string,
        'strings': system.strings
    },
    'models': {
        'dc_model': mc.dc_model,
        'ac_model': mc.ac_model,
        'temperature_model': mc.temperature_model
    },
    'weather_source': 'NSRDB PSM3',
    'simulation_date': datetime.now().isoformat()
}

with open('simulation_config.json', 'w') as f:
    json.dump(system_config, f, indent=2)
```

#### Version Control
```python
# Track versions for reproducibility
import pvlib
print(f"PVLib version: {pvlib.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"NumPy version: {np.__version__}")
```

This comprehensive requirements document provides everything needed to successfully simulate PV plant power profiles, energy yield, and performance using pvlib-python. The examples and guidelines ensure accurate, validated, and reproducible simulations for a wide range of PV system configurations and applications.