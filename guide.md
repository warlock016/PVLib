# PVLib Validation Study Guide
## Simulating PV Plant Performance for Real-World Validation

This guide provides a comprehensive framework for setting up PVLib simulations to validate against real PV plant performance data from your database.

## Table of Contents
1. [Overview](#overview)
2. [Data Requirements](#data-requirements)
3. [Study Design Framework](#study-design-framework)
4. [Implementation Steps](#implementation-steps)
5. [Example Implementation](#example-implementation)
6. [Validation Metrics](#validation-metrics)
7. [Common Challenges](#common-challenges)
8. [Advanced Considerations](#advanced-considerations)

## Overview

PVLib provides a robust framework for modeling photovoltaic energy systems. This validation study aims to:
- Compare PVLib simulation results against real plant performance data
- Quantify model accuracy across different technologies and geographic locations
- Identify systematic biases and model limitations
- Improve confidence in PVLib for energy forecasting applications

### Key PVLib Components Used
- **ModelChain**: High-level simulation workflow orchestration
- **Location**: Geographic and temporal handling
- **PVSystem**: System configuration and electrical modeling
- **IOTools**: Weather data acquisition from various sources
- **Performance Models**: SAPM, single-diode, PVWatts, etc.

## Data Requirements

### From Your Plant Database
**Essential System Metadata:**
- Geographic coordinates (latitude, longitude, elevation)
- System capacity (DC/AC ratings in kW/MW)
- Module specifications (technology, model, quantity)
- Inverter specifications (model, quantity, topology)
- Array configuration (tilt angle, azimuth, tracking type)
- System commissioning date and operational period

**Performance Timeseries Data:**
- AC power output (preferably 5-15 minute resolution)
- Daily/monthly energy yields
- Operational status indicators (maintenance, outages)

**Optional but Valuable:**
- On-site meteorological measurements (irradiance, temperature, wind)
- DC power measurements
- Module temperature data
- Soiling or curtailment information

### Weather Data Sources for PVLib
**Recommended Primary Source: NSRDB PSM3/PSM4**
- Satellite-derived solar resource data
- 4km spatial resolution, 30-minute temporal resolution
- Available through NREL APIs
- Consistent methodology across all locations

**Alternative Sources:**
- On-site measurements (if available and high quality)
- PVGIS for European locations
- SolarGIS or SolarAnywhere for commercial applications
- Local meteorological stations (with appropriate QC)

## Study Design Framework

### 1. Site Selection Strategy
**Diversity Criteria:**
- **Geographic spread**: Different climate zones and latitudes
- **Technology mix**: c-Si, thin-film, bifacial modules
- **System types**: Fixed-tilt, single-axis tracking, dual-axis tracking
- **Capacity range**: Small residential to utility-scale
- **Data quality**: Prioritize sites with continuous, validated data

**Recommended Minimum:**
- 10-20 sites for statistically meaningful results
- At least 1 full year of overlapping simulation/measurement data
- Mix of 70% crystalline silicon, 20% thin-film, 10% other technologies

### 2. Temporal Analysis Framework
**Multi-scale Validation:**
- **Sub-hourly (5-15 min)**: Capture ramp rates and variability
- **Hourly**: Standard resolution for most analysis
- **Daily**: Smooth out short-term variations
- **Monthly**: Seasonal performance patterns
- **Annual**: Overall energy yield validation

### 3. Model Configuration Strategy
**Standardized Approach:**
- Use ModelChain for consistent methodology
- Apply same loss models across all sites
- Document all assumptions and parameter choices

**Technology-Specific Considerations:**
- **Crystalline Silicon**: Use CEC module database, physical IAM model
- **Thin-film (CdTe, CIGS)**: Include spectral corrections, Sandia model
- **Bifacial**: Enable bifacial modeling with appropriate ground models
- **Tracking Systems**: Include backtracking and GCR effects

## Implementation Steps

### Step 1: Environment Setup
```bash
# Install PVLib with all optional dependencies
pip install pvlib[all]

# Additional packages for data handling and analysis
pip install pandas numpy matplotlib scipy scikit-learn
```

### Step 2: Data Preprocessing
```python
import pvlib
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Load plant metadata from your database
def load_plant_metadata(plant_id):
    """Load plant configuration from database"""
    # Your database query logic here
    return {
        'latitude': 40.1234,
        'longitude': -105.5678,
        'elevation': 1650,
        'timezone': 'US/Mountain',
        'dc_capacity': 5000,  # kW
        'ac_capacity': 4500,  # kW
        'tilt': 25,  # degrees
        'azimuth': 180,  # degrees (south-facing)
        'module_type': 'First_Solar__Inc__FS_6440A',
        'inverter_type': 'SMA_America__SB5000US__240V_',
        'tracking': False,  # or 'single_axis', 'dual_axis'
        'modules_per_string': 20,
        'strings_per_inverter': 250,
        'gcr': 0.4,  # for tracking systems
        'technology': 'CdTe'  # or 'c-Si', 'CIGS', etc.
    }

# Load measured performance data
def load_performance_data(plant_id, start_date, end_date):
    """Load timeseries performance data from database"""
    # Your database query logic here
    # Return DataFrame with datetime index and AC power column
    pass
```

### Step 3: Weather Data Acquisition
```python
def get_weather_data(latitude, longitude, start_year, end_year):
    """Fetch weather data from NSRDB PSM3"""
    # You'll need to register for an API key at https://developer.nrel.gov/
    api_key = 'YOUR_API_KEY'
    email = 'your_email@domain.com'
    
    weather_data = []
    for year in range(start_year, end_year + 1):
        try:
            data, metadata = pvlib.iotools.get_psm3(
                latitude=latitude,
                longitude=longitude,
                api_key=api_key,
                email=email,
                names=year,
                interval=30,  # 30-minute data
                map_variables=True,
                leap_day=True
            )
            weather_data.append(data)
        except Exception as e:
            print(f"Failed to fetch data for {year}: {e}")
    
    return pd.concat(weather_data).sort_index()
```

### Step 4: PVLib Model Setup
```python
def setup_pvlib_model(plant_metadata):
    """Configure PVLib ModelChain for the plant"""
    
    # Create Location object
    location = pvlib.location.Location(
        latitude=plant_metadata['latitude'],
        longitude=plant_metadata['longitude'],
        tz=plant_metadata['timezone'],
        altitude=plant_metadata['elevation']
    )
    
    # Get module and inverter parameters from databases
    module_db = pvlib.pvsystem.retrieve_sam('cecmod')
    inverter_db = pvlib.pvsystem.retrieve_sam('cecinverter')
    
    module_params = module_db[plant_metadata['module_type']]
    inverter_params = inverter_db[plant_metadata['inverter_type']]
    
    # Configure mounting system
    if plant_metadata['tracking'] == 'single_axis':
        mount = pvlib.pvsystem.SingleAxisTrackerMount(
            axis_tilt=0,
            axis_azimuth=180,
            max_angle=60,
            backtrack=True,
            gcr=plant_metadata['gcr']
        )
    else:
        mount = pvlib.pvsystem.FixedMount(
            surface_tilt=plant_metadata['tilt'],
            surface_azimuth=plant_metadata['azimuth']
        )
    
    # Configure Array
    array = pvlib.pvsystem.Array(
        mount=mount,
        module_parameters=module_params,
        temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_polymer'],
        modules_per_string=plant_metadata['modules_per_string'],
        strings=plant_metadata['strings_per_inverter']
    )
    
    # Configure PV System
    system = pvlib.pvsystem.PVSystem(
        arrays=[array],
        inverter_parameters=inverter_params,
        losses_parameters={'soiling': 2, 'shading': 3, 'snow': 0, 'mismatch': 2, 'wiring': 2, 'connections': 0.5, 'lid': 1.5, 'nameplate_rating': 1, 'age': 0, 'availability': 0}
    )
    
    # Configure ModelChain
    # Choose models based on technology
    if plant_metadata['technology'] in ['CdTe', 'CIGS']:
        spectral_model = 'first_solar'
        dc_model = 'sapm'
    else:
        spectral_model = 'no_loss'
        dc_model = 'cec'
    
    mc = pvlib.modelchain.ModelChain(
        system=system,
        location=location,
        dc_model=dc_model,
        ac_model='sandia',
        aoi_model='physical',
        spectral_model=spectral_model,
        temperature_model='sapm',
        losses_model='pvwatts'
    )
    
    return mc
```

### Step 5: Run Simulation
```python
def run_simulation(model_chain, weather_data):
    """Run PVLib simulation"""
    # Ensure weather data has required columns
    required_cols = ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']
    missing_cols = [col for col in required_cols if col not in weather_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required weather columns: {missing_cols}")
    
    # Run the model
    model_chain.run_model(weather_data)
    
    # Extract results
    results = pd.DataFrame({
        'ac_power': model_chain.results.ac,  # AC power in watts
        'dc_power': model_chain.results.dc.values,
        'poa_global': model_chain.results.total_irrad['poa_global'],
        'cell_temperature': model_chain.results.cell_temperature
    }, index=weather_data.index)
    
    return results
```

## Example Implementation

```python
def validate_plant_performance(plant_id, start_date='2022-01-01', end_date='2022-12-31'):
    """Complete validation workflow for a single plant"""
    
    print(f"Starting validation for Plant {plant_id}")
    
    # 1. Load plant metadata
    metadata = load_plant_metadata(plant_id)
    print(f"Plant location: {metadata['latitude']:.3f}, {metadata['longitude']:.3f}")
    print(f"DC capacity: {metadata['dc_capacity']} kW")
    
    # 2. Load measured performance data
    measured_data = load_performance_data(plant_id, start_date, end_date)
    print(f"Loaded {len(measured_data)} measured data points")
    
    # 3. Get weather data
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    weather_data = get_weather_data(
        metadata['latitude'], 
        metadata['longitude'], 
        start_year, 
        end_year
    )
    
    # Filter to study period
    weather_data = weather_data.loc[start_date:end_date]
    print(f"Loaded {len(weather_data)} weather data points")
    
    # 4. Setup and run PVLib model
    model_chain = setup_pvlib_model(metadata)
    simulation_results = run_simulation(model_chain, weather_data)
    
    # 5. Align datasets
    comparison_data = pd.merge(
        simulation_results['ac_power'].to_frame('simulated_ac'),
        measured_data['ac_power'].to_frame('measured_ac'),
        left_index=True,
        right_index=True,
        how='inner'
    )
    
    # Convert to same units (kW)
    comparison_data['simulated_ac'] = comparison_data['simulated_ac'] / 1000
    
    print(f"Aligned {len(comparison_data)} data points for comparison")
    
    return comparison_data, metadata

# Run validation for multiple plants
validation_results = {}
plant_ids = ['PLANT_001', 'PLANT_002', 'PLANT_003']  # Your plant IDs

for plant_id in plant_ids:
    try:
        results, metadata = validate_plant_performance(plant_id)
        validation_results[plant_id] = {
            'data': results,
            'metadata': metadata
        }
        print(f"✓ Completed validation for {plant_id}")
    except Exception as e:
        print(f"✗ Failed validation for {plant_id}: {e}")
```

## Validation Metrics

### Statistical Metrics
```python
def calculate_validation_metrics(simulated, measured):
    """Calculate comprehensive validation metrics"""
    
    # Remove any invalid data points
    valid_data = pd.DataFrame({'sim': simulated, 'meas': measured}).dropna()
    sim = valid_data['sim']
    meas = valid_data['meas']
    
    # Basic statistics
    n_points = len(sim)
    
    # Bias metrics
    mean_bias_error = np.mean(sim - meas)  # MBE
    mean_absolute_error = np.mean(np.abs(sim - meas))  # MAE
    root_mean_square_error = np.sqrt(np.mean((sim - meas)**2))  # RMSE
    
    # Relative metrics
    mean_measured = np.mean(meas)
    relative_bias = mean_bias_error / mean_measured * 100  # %
    relative_mae = mean_absolute_error / mean_measured * 100  # %
    relative_rmse = root_mean_square_error / mean_measured * 100  # %
    
    # Correlation
    correlation_coefficient = np.corrcoef(sim, meas)[0, 1]
    
    # R-squared
    r_squared = correlation_coefficient ** 2
    
    # Slope and intercept of best fit line
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(meas, sim)
    
    return {
        'n_points': n_points,
        'mean_bias_error_kw': mean_bias_error,
        'mean_absolute_error_kw': mean_absolute_error,
        'root_mean_square_error_kw': root_mean_square_error,
        'relative_bias_percent': relative_bias,
        'relative_mae_percent': relative_mae,
        'relative_rmse_percent': relative_rmse,
        'correlation_coefficient': correlation_coefficient,
        'r_squared': r_squared,
        'regression_slope': slope,
        'regression_intercept': intercept,
        'mean_measured_kw': mean_measured,
        'mean_simulated_kw': np.mean(sim)
    }

# Calculate metrics for each plant
for plant_id, results in validation_results.items():
    comparison_data = results['data']
    metrics = calculate_validation_metrics(
        comparison_data['simulated_ac'],
        comparison_data['measured_ac']
    )
    
    print(f"\n=== Validation Metrics for {plant_id} ===")
    print(f"Data points: {metrics['n_points']:,}")
    print(f"Mean measured AC power: {metrics['mean_measured_kw']:.1f} kW")
    print(f"Mean simulated AC power: {metrics['mean_simulated_kw']:.1f} kW")
    print(f"Relative bias: {metrics['relative_bias_percent']:.1f}%")
    print(f"Relative RMSE: {metrics['relative_rmse_percent']:.1f}%")
    print(f"Correlation coefficient: {metrics['correlation_coefficient']:.3f}")
    print(f"R²: {metrics['r_squared']:.3f}")
```

### Time-Series Analysis
```python
def analyze_temporal_patterns(comparison_data, metadata):
    """Analyze validation metrics by time period"""
    
    # Add time-based grouping columns
    df = comparison_data.copy()
    df['hour'] = df.index.hour
    df['month'] = df.index.month
    df['day_of_year'] = df.index.dayofyear
    
    # Calculate bias by hour of day
    hourly_bias = []
    for hour in range(24):
        hour_data = df[df['hour'] == hour]
        if len(hour_data) > 10:  # Minimum data points
            bias = np.mean(hour_data['simulated_ac'] - hour_data['measured_ac'])
            hourly_bias.append({'hour': hour, 'bias_kw': bias})
    
    hourly_bias_df = pd.DataFrame(hourly_bias)
    
    # Calculate bias by month
    monthly_metrics = []
    for month in range(1, 13):
        month_data = df[df['month'] == month]
        if len(month_data) > 100:  # Minimum data points
            metrics = calculate_validation_metrics(
                month_data['simulated_ac'],
                month_data['measured_ac']
            )
            metrics['month'] = month
            monthly_metrics.append(metrics)
    
    monthly_metrics_df = pd.DataFrame(monthly_metrics)
    
    return hourly_bias_df, monthly_metrics_df
```

### Visualization
```python
import matplotlib.pyplot as plt
import seaborn as sns

def create_validation_plots(comparison_data, metadata, plant_id):
    """Create comprehensive validation plots"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Validation Results: {plant_id}', fontsize=16)
    
    # 1. Scatter plot: Measured vs Simulated
    ax1 = axes[0, 0]
    ax1.scatter(comparison_data['measured_ac'], comparison_data['simulated_ac'], 
                alpha=0.5, s=1)
    max_power = max(comparison_data['measured_ac'].max(), 
                   comparison_data['simulated_ac'].max())
    ax1.plot([0, max_power], [0, max_power], 'r--', label='1:1 line')
    ax1.set_xlabel('Measured AC Power (kW)')
    ax1.set_ylabel('Simulated AC Power (kW)')
    ax1.set_title('Measured vs Simulated Power')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Time series (sample period)
    ax2 = axes[0, 1]
    sample_data = comparison_data.loc['2022-07-01':'2022-07-07']  # One week
    ax2.plot(sample_data.index, sample_data['measured_ac'], 
             label='Measured', linewidth=1)
    ax2.plot(sample_data.index, sample_data['simulated_ac'], 
             label='Simulated', linewidth=1)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('AC Power (kW)')
    ax2.set_title('Time Series Comparison (Sample Week)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Residuals vs measured power
    ax3 = axes[0, 2]
    residuals = comparison_data['simulated_ac'] - comparison_data['measured_ac']
    ax3.scatter(comparison_data['measured_ac'], residuals, alpha=0.5, s=1)
    ax3.axhline(y=0, color='r', linestyle='--')
    ax3.set_xlabel('Measured AC Power (kW)')
    ax3.set_ylabel('Residuals (Sim - Meas) (kW)')
    ax3.set_title('Residuals vs Measured Power')
    ax3.grid(True, alpha=0.3)
    
    # 4. Histogram of residuals
    ax4 = axes[1, 0]
    ax4.hist(residuals, bins=50, alpha=0.7, edgecolor='black')
    ax4.axvline(x=np.mean(residuals), color='r', linestyle='--', 
                label=f'Mean: {np.mean(residuals):.1f} kW')
    ax4.set_xlabel('Residuals (Sim - Meas) (kW)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Residuals')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Daily energy comparison
    ax5 = axes[1, 1]
    daily_measured = comparison_data['measured_ac'].resample('D').sum() * 24/1000  # MWh
    daily_simulated = comparison_data['simulated_ac'].resample('D').sum() * 24/1000  # MWh
    ax5.scatter(daily_measured, daily_simulated, alpha=0.7)
    max_energy = max(daily_measured.max(), daily_simulated.max())
    ax5.plot([0, max_energy], [0, max_energy], 'r--', label='1:1 line')
    ax5.set_xlabel('Measured Daily Energy (MWh)')
    ax5.set_ylabel('Simulated Daily Energy (MWh)')
    ax5.set_title('Daily Energy Comparison')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Monthly bias
    ax6 = axes[1, 2]
    monthly_data = comparison_data.groupby(comparison_data.index.month).apply(
        lambda x: np.mean(x['simulated_ac'] - x['measured_ac'])
    )
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax6.bar(range(1, 13), monthly_data.values)
    ax6.axhline(y=0, color='r', linestyle='--')
    ax6.set_xlabel('Month')
    ax6.set_ylabel('Mean Bias (kW)')
    ax6.set_title('Monthly Bias Pattern')
    ax6.set_xticks(range(1, 13))
    ax6.set_xticklabels(months)
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{plant_id}_validation_results.png', dpi=300, bbox_inches='tight')
    plt.show()

# Generate plots for each plant
for plant_id, results in validation_results.items():
    create_validation_plots(results['data'], results['metadata'], plant_id)
```

## Common Challenges

### 1. Data Alignment Issues
**Challenge:** Timestamp mismatches between measured and simulated data
**Solutions:**
- Standardize all data to UTC before comparison
- Use appropriate resampling methods for different temporal resolutions
- Handle daylight saving time transitions carefully
- Account for data logger vs. inverter timestamp conventions

### 2. Weather Data Quality
**Challenge:** Satellite data may not accurately represent site conditions
**Solutions:**
- Compare multiple weather data sources when available
- Validate weather data against nearby ground stations
- Consider local microclimate effects (coastal, urban heat island)
- Use bias-correction techniques for systematic weather data errors

### 3. Module/Inverter Database Limitations
**Challenge:** Exact equipment models may not be in PVLib databases
**Solutions:**
- Use closest equivalent models with similar electrical characteristics
- Develop custom parameter sets using manufacturer datasheets
- Validate key parameters (Pmp, Vmp, temperature coefficients) against specs
- Document all substitutions and their potential impact

### 4. System Configuration Uncertainties
**Challenge:** Incomplete or inaccurate system metadata
**Solutions:**
- Cross-validate system parameters against multiple sources
- Use satellite imagery to verify array orientation and spacing
- Estimate missing parameters from capacity factors and performance ratios
- Sensitivity analysis on uncertain parameters

### 5. Loss Model Accuracy
**Challenge:** PVLib default loss factors may not match real system losses
**Solutions:**
- Calibrate loss factors using historical performance data
- Separate systematic losses (soiling, degradation) from random losses
- Consider site-specific factors (desert dust, marine environment)
- Validate against detailed loss analysis when available

## Advanced Considerations

### Technology-Specific Modeling

**Bifacial Modules:**
```python
# Enable bifacial modeling
array = pvlib.pvsystem.Array(
    mount=mount,
    module_parameters=module_params,
    temperature_model_parameters=temp_params,
    modules_per_string=modules_per_string,
    strings=strings,
    module_type='glass_polymer',  # or 'glass_glass'
    racking_model='open_rack',    # affects albedo visibility
    module_height=1.0,            # height above ground
    albedo=0.25                   # ground reflectance
)

# Use bifacial irradiance models
bifacial_irrad = pvlib.bifacial.pvfactors.pvfactors_timeseries(
    solar_azimuth=solar_position['azimuth'],
    solar_zenith=solar_position['apparent_zenith'],
    surface_azimuth=surface_azimuth,
    surface_tilt=surface_tilt,
    axis_azimuth=axis_azimuth,  # for tracking
    timestamps=weather_data.index,
    dni=weather_data['dni'],
    dhi=weather_data['dhi'],
    gcr=gcr,
    pvrow_height=pvrow_height,
    pvrow_width=pvrow_width,
    albedo=albedo
)
```

**Tracking Systems with Backtracking:**
```python
# Configure single-axis tracker with backtracking
tracker_mount = pvlib.pvsystem.SingleAxisTrackerMount(
    axis_tilt=0,
    axis_azimuth=180,
    max_angle=60,
    backtrack=True,
    gcr=0.35,
    cross_axis_tilt=0
)

# Calculate tracker angles
tracker_data = tracker_mount.get_orientation(
    solar_zenith=solar_position['apparent_zenith'],
    solar_azimuth=solar_position['azimuth']
)
```

**Spectral Modeling for Thin-Film:**
```python
# Enhanced spectral modeling for CdTe modules
mc = pvlib.modelchain.ModelChain(
    system=system,
    location=location,
    dc_model='sapm',
    ac_model='sandia',
    aoi_model='physical',
    spectral_model='first_solar',  # CdTe-specific
    temperature_model='sapm',
    losses_model='pvwatts'
)

# Ensure precipitable water is available in weather data
required_weather_vars = ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 
                        'precipitable_water']  # for spectral model
```

### Advanced Loss Modeling

**Soiling Modeling:**
```python
# Use Kimber soiling model
soiling_info = pvlib.soiling.hsu(
    pm25=weather_data['pm25'],  # if available
    pm10=weather_data['pm10'],  # if available
    depo_veloc=weather_data['depo_veloc'],
    rain=weather_data['precipitation'],
    washing=None,  # manual washing schedule
    rainfall_threshold_daily=1.0  # mm/day
)

# Apply soiling losses
soiled_irradiance = irradiance * (1 - soiling_info['soiling_ratio'])
```

**Snow Modeling:**
```python
# Snow coverage modeling for cold climates
snow_coverage = pvlib.snow.fully_covered_nrel(
    surface_tilt=surface_tilt,
    snow_depth=weather_data['snow_depth'],  # if available
    temp_air=weather_data['temp_air'],
    poa_irrad=poa_irradiance
)

# Apply snow losses
snow_free_irradiance = poa_irradiance * (1 - snow_coverage)
```

### Uncertainty Quantification

**Monte Carlo Analysis:**
```python
def monte_carlo_simulation(n_iterations=100):
    """Quantify simulation uncertainty through parameter variations"""
    
    results = []
    
    for i in range(n_iterations):
        # Vary uncertain parameters within reasonable ranges
        varied_params = {
            'tilt': np.random.normal(metadata['tilt'], 2),  # ±2° uncertainty
            'azimuth': np.random.normal(metadata['azimuth'], 5),  # ±5° uncertainty
            'soiling_loss': np.random.uniform(0.5, 4.0),  # 0.5-4% uncertainty
            'shading_loss': np.random.uniform(1.0, 5.0),  # 1-5% uncertainty
        }
        
        # Run simulation with varied parameters
        mc_results = run_modified_simulation(varied_params)
        results.append(mc_results['annual_energy'])
    
    # Calculate uncertainty bounds
    uncertainty_bounds = {
        'p5': np.percentile(results, 5),
        'p50': np.percentile(results, 50),
        'p95': np.percentile(results, 95),
        'std': np.std(results)
    }
    
    return uncertainty_bounds
```

### Automated Report Generation

```python
def generate_validation_report(validation_results):
    """Generate automated validation report"""
    
    report = f"""
# PVLib Validation Study Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary
Validated {len(validation_results)} PV plants against measured performance data.

## Plant Summary
| Plant ID | Technology | DC Capacity (MW) | Annual CF (%) | RMSE (%) | Bias (%) |
|----------|------------|------------------|---------------|-----------|----------|
"""
    
    for plant_id, results in validation_results.items():
        metadata = results['metadata']
        comparison_data = results['data']
        metrics = calculate_validation_metrics(
            comparison_data['simulated_ac'],
            comparison_data['measured_ac']
        )
        
        # Calculate capacity factor
        annual_cf = (comparison_data['measured_ac'].mean() * 8760) / (metadata['dc_capacity'] * 1000) * 100
        
        report += f"| {plant_id} | {metadata['technology']} | {metadata['dc_capacity']/1000:.1f} | {annual_cf:.1f} | {metrics['relative_rmse_percent']:.1f} | {metrics['relative_bias_percent']:.1f} |\n"
    
    report += f"""
## Overall Performance
- Mean absolute error: {np.mean([calculate_validation_metrics(r['data']['simulated_ac'], r['data']['measured_ac'])['relative_mae_percent'] for r in validation_results.values()]):.1f}%
- Correlation coefficient: {np.mean([calculate_validation_metrics(r['data']['simulated_ac'], r['data']['measured_ac'])['correlation_coefficient'] for r in validation_results.values()]):.3f}

## Methodology
- Weather data: NSRDB PSM3 satellite data
- PV models: Technology-appropriate models from PVLib
- Temporal resolution: 30-minute simulation, hourly comparison
- Loss models: PVWatts with calibrated parameters

"""
    
    # Save report
    with open('pvlib_validation_report.md', 'w') as f:
        f.write(report)
    
    print("Validation report saved to: pvlib_validation_report.md")
```

## Next Steps

1. **Implement the framework** using your specific database structure and plant selection
2. **Validate the methodology** on a small subset of well-characterized plants
3. **Scale up the analysis** to your full plant portfolio
4. **Document findings** and contribute improvements back to PVLib community
5. **Automate the workflow** for ongoing validation studies

This guide provides a comprehensive foundation for your PVLib validation study. Adapt the code examples to your specific database schema and requirements. The framework is designed to be scalable and maintainable for ongoing validation efforts.