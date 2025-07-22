# User Guide

## Getting Started

### Overview
The PV Plant Modeling Website allows you to simulate the performance of photovoltaic (PV) systems anywhere in the world. Simply configure your system parameters, and the application will calculate energy production, performance metrics, and provide detailed analysis of your PV plant.

### Quick Start
1. **Enter Location**: Specify the location of your PV plant
2. **Configure System**: Set up your PV system specifications
3. **Run Simulation**: Execute the performance simulation
4. **View Results**: Analyze the generated reports and charts
5. **Export Data**: Download results for further analysis

## Step-by-Step Guide

### Step 1: Location Configuration

#### Method 1: Coordinate Input
- Enter **Latitude** and **Longitude** in decimal degrees
- Latitude range: -90° to 90° (negative for southern hemisphere)
- Longitude range: -180° to 180° (negative for western hemisphere)
- Example: San Francisco, CA = 37.7749° N, -122.4194° W

#### Method 2: Address Lookup
- Enter a street address, city, or landmark
- The system will automatically convert to coordinates
- Verify the location on the map before proceeding

#### Additional Location Settings
- **Elevation**: Automatically detected or manually entered (meters above sea level)
- **Timezone**: Automatically determined based on coordinates
- **Weather Data Source**: Choose NREL NSRDB (Americas) or PVGIS (Europe/Asia)

### Step 2: System Configuration

#### Basic System Parameters
- **DC Capacity**: Total DC power rating of your system (kW)
- **Module Type**: Select from the CEC database of certified modules
- **Inverter Type**: Choose from the CEC database of certified inverters
- **System Voltage**: Typical values are 600V, 1000V, or 1500V

#### Array Configuration
- **Mounting Type**: 
  - *Fixed Tilt*: Static mounting at fixed angle
  - *Single-Axis Tracking*: Tracks sun east-west
  - *Dual-Axis Tracking*: Tracks sun in all directions
- **Tilt Angle**: Angle from horizontal (0° = flat, 90° = vertical)
- **Azimuth**: Direction panels face (180° = south, 270° = west)
- **Ground Coverage Ratio**: For tracking systems (typical: 0.3-0.4)

#### Module and String Configuration
- **Modules per String**: Number of modules connected in series
- **Strings per Inverter**: Number of strings connected to each inverter
- **Total Modules**: Automatically calculated from above parameters

### Step 3: Loss Parameters

#### System Losses
Configure the following loss factors (typical values in parentheses):

- **Soiling Losses** (2%): Dust, dirt, and debris on modules
- **Shading Losses** (3%): Shadows from nearby objects
- **Snow Losses** (0-5%): Snow coverage (climate dependent)
- **Module Mismatch** (2%): Variations between individual modules
- **Wiring Losses** (2%): Resistance losses in DC and AC wiring
- **Connection Losses** (0.5%): Losses at electrical connections
- **Light-Induced Degradation** (1.5%): Initial power reduction in c-Si modules
- **Nameplate Rating** (1%): Difference between rated and actual power
- **Age/Degradation** (0%): Annual degradation rate
- **System Availability** (0%): Maintenance and outage downtime

#### Advanced Loss Models
- **Soiling Model**: Use location-specific soiling rates
- **Spectral Losses**: For thin-film modules (CdTe, CIGS)
- **Thermal Losses**: Advanced temperature modeling

### Step 4: Weather Data

#### Data Source Selection
- **NREL NSRDB**: Best for North/South America
  - High accuracy satellite data
  - 4 km spatial resolution
  - Years 1998-2020 available
- **PVGIS**: Best for Europe, Asia, Africa
  - Good European coverage
  - TMY data based on 2005-2020

#### Data Quality Indicators
- **Coverage**: Percentage of hours with valid data
- **Missing Hours**: Number of hours with no data
- **Quality Flags**: Data quality ratings (excellent/good/fair/poor)

### Step 5: Simulation Options

#### Modeling Parameters
- **Year**: Select specific year or use TMY data
- **DC Model**: Choose calculation method (CEC, SAPM, PVWatts)
- **AC Model**: Inverter modeling approach (Sandia, CEC)
- **Temperature Model**: Cell temperature calculation (SAPM, Pvsyst)
- **Clear Sky Model**: Reference irradiance calculation

#### Simulation Execution
- Click "Run Simulation" to start the calculation
- Monitor progress in real-time
- Typical simulation time: 30-60 seconds
- Results are automatically saved

### Step 6: Results Analysis

#### Summary Metrics
- **Annual Energy**: Total energy production (kWh/year)
- **Specific Yield**: Energy per unit capacity (kWh/kWp/year)
- **Performance Ratio**: Actual vs. theoretical performance
- **Capacity Factor**: Average power / rated power
- **Peak Power**: Maximum instantaneous power output

#### Monthly Analysis
- **Monthly Energy**: Energy production by month
- **Seasonal Patterns**: Identify peak and low production periods
- **Performance Trends**: Monthly performance ratio variations

#### Detailed Results
- **Hourly Data**: 8,760 hours of simulation data
- **Daily Profiles**: Average generation patterns
- **Weather Correlation**: Performance vs. weather conditions

### Step 7: Data Export

#### Export Options
- **CSV Format**: Raw data for analysis in Excel/Python/R
- **JSON Format**: Structured data for web applications
- **PDF Report**: Professional summary document
- **Chart Images**: PNG/SVG format for presentations

#### Data Resolutions
- **Hourly**: Complete 8,760-hour dataset
- **Daily**: Daily energy totals
- **Monthly**: Monthly summaries
- **Annual**: Single-year totals

## Understanding Results

### Performance Metrics Explained

#### Performance Ratio (PR)
- **Definition**: Actual energy / Theoretical energy
- **Typical Values**: 0.75-0.85 for well-designed systems
- **Factors**: Losses, weather, system design
- **Interpretation**: Higher PR = better system performance

#### Capacity Factor (CF)
- **Definition**: Average power / Rated power
- **Typical Values**: 0.15-0.25 for fixed systems, 0.20-0.30 for tracking
- **Factors**: Solar resource, system design, losses
- **Interpretation**: Higher CF = better resource utilization

#### Specific Yield
- **Definition**: Annual energy / Installed capacity (kWh/kWp/year)
- **Typical Values**: 1,000-2,000 kWh/kWp/year (climate dependent)
- **Factors**: Solar resource, system performance
- **Interpretation**: Higher yield = better energy production

### Weather Impact Analysis

#### Solar Resource Quality
- **Global Horizontal Irradiance (GHI)**: Total solar energy on horizontal surface
- **Direct Normal Irradiance (DNI)**: Direct solar energy (important for tracking)
- **Diffuse Horizontal Irradiance (DHI)**: Scattered solar energy

#### Temperature Effects
- **Cell Temperature**: Affects module efficiency
- **Ambient Temperature**: Influences cooling
- **Temperature Coefficient**: Module-specific temperature response

#### Other Weather Factors
- **Wind Speed**: Improves module cooling
- **Cloud Cover**: Affects irradiance variability
- **Precipitation**: Natural module cleaning

## Best Practices

### System Design Guidelines

#### Location Considerations
- **Solar Resource**: Use high-quality weather data
- **Shading**: Minimize obstructions
- **Accessibility**: Consider maintenance access
- **Grid Connection**: Evaluate utility requirements

#### System Sizing
- **Load Matching**: Size system to match energy needs
- **Inverter Sizing**: DC/AC ratio typically 1.1-1.3
- **String Configuration**: Optimize for MPPT range
- **Safety Margins**: Include degradation and soiling

#### Technology Selection
- **Module Technology**: c-Si for high efficiency, thin-film for high temperatures
- **Inverter Technology**: String vs. power optimizers vs. microinverters
- **Mounting System**: Balance cost, performance, and durability

### Simulation Accuracy

#### Input Data Quality
- **Accurate Coordinates**: Verify location precision
- **Correct System Parameters**: Use actual equipment specifications
- **Realistic Losses**: Use site-specific loss values
- **Weather Data**: Choose appropriate data source

#### Validation Methods
- **Compare Sources**: Cross-check weather data sources
- **Sensitivity Analysis**: Test parameter variations
- **Benchmark Results**: Compare with similar systems
- **Expert Review**: Have experienced engineer review

### Common Pitfalls

#### Configuration Errors
- **Wrong Timezone**: Affects solar position calculations
- **Incorrect Tilt/Azimuth**: Significantly impacts performance
- **Over/Under-sizing**: Improper DC/AC ratio
- **Loss Assumptions**: Using generic vs. site-specific values

#### Data Interpretation
- **Weather Year Selection**: TMY vs. specific year impacts
- **Seasonal Variations**: Don't rely on single month data
- **Uncertainty**: Understand model limitations
- **Validation**: Compare predictions with measurements when possible

## Troubleshooting

### Common Issues

#### Weather Data Problems
- **No Data Available**: Try different year or data source
- **Poor Data Quality**: Check quality flags and coverage
- **Service Unavailable**: Weather service may be down
- **API Limits**: Daily request limits may be exceeded

#### Simulation Errors
- **Invalid Configuration**: Check parameter ranges
- **Missing Parameters**: Ensure all required fields are filled
- **Calculation Failure**: May indicate incompatible parameters
- **Timeout**: Large systems may require longer processing

#### Results Issues
- **Unexpectedly Low Performance**: Check loss parameters and system design
- **Unrealistic Results**: Verify input parameters and units
- **Missing Data**: May indicate simulation failure
- **Export Problems**: Check file format and browser settings

### Getting Help

#### Documentation
- **API Documentation**: Detailed endpoint reference
- **Feature Specifications**: Complete feature descriptions
- **Deployment Guide**: Installation and setup instructions

#### Support Resources
- **PVLib Documentation**: Core modeling library reference
- **NREL Resources**: Weather data and modeling guidance
- **Community Forums**: User discussions and help

#### Contact Information
- **Technical Issues**: Create issue in project repository
- **Feature Requests**: Submit enhancement proposals
- **General Questions**: Community forums and documentation

## Advanced Features

### Custom Parameters
- **Module Parameters**: Define custom module characteristics
- **Inverter Parameters**: Specify custom inverter models
- **Loss Models**: Implement site-specific loss calculations

### Batch Processing
- **Multiple Locations**: Compare performance across sites
- **Parameter Sweeps**: Analyze design variations
- **Automated Reports**: Generate multiple simulations

### Integration
- **API Access**: Programmatic access to simulation engine
- **Data Import**: Bulk configuration import
- **External Tools**: Integration with other software

### Validation
- **Measured Data**: Compare against actual performance
- **Uncertainty Analysis**: Quantify prediction uncertainty
- **Model Comparison**: Compare different modeling approaches