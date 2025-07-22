"""
Example usage of the Weather Data Connector for Ampere facilities.

This script demonstrates how to:
1. Load Ampere facility data
2. Process facilities for pvlib simulation
3. Fetch weather data with automatic fallback
4. Run basic PV simulations
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nrel.weather_connector import WeatherDataConnector
from nrel.data_utils import load_ampere_facilities, process_facility, get_facility_summary
from nrel.config import get_logger
import pvlib

# Setup logging
logger = get_logger(__name__)

def get_region(facility):
    """Determine the region based on latitude and longitude."""
    lat = facility.get('latitude', 0)
    lon = facility.get('longitude', 0)
    
    if lat > 35 and lon > -30:
        return 'EU'
    elif lat > 35 and lon < -30:
        return 'NA'
    else:
        return 'SA'

def main():
    """Main example function."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate simulation results for Ampere facilities')
    parser.add_argument('--year', type=int, default=2023, help='Year to generate simulations for (default: 2023)')
    parser.add_argument('--pilot-only', action='store_true', help='Process only pilot facilities (default: process all)')
    args = parser.parse_args()
    
    print("=== NREL Weather Data Connector Example ===\n")
    
    # Whether to process all facilities or just pilot facilities
    process_all = not args.pilot_only  # Set to False to run only on pilot facilities
    
    # Create output directory for results if processing all
    if process_all:
        results_dir = Path(project_root) / "nrel" / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for the results file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"simulation_results_{args.year}_{timestamp}.json"
    
    # 1. Initialize the weather connector
    print("1. Initializing Weather Data Connector...")
    weather_connector = WeatherDataConnector(
        primary_source='nsrdb',
        fallback_sources=['pvgis'],
        enable_cache=True
    )
    
    # Test connections
    print("   Testing API connections...")
    connection_results = weather_connector.test_connection()
    for source, status in connection_results.items():
        status_str = "✓" if status else "✗"
        print(f"   {status_str} {source.upper()}: {'Connected' if status else 'Failed'}")
    
    print()
    
    # 2. Load Ampere facility data
    print("2. Loading Ampere facility data...")
    try:
        # Try both datasets
        pvlib_ready_path = project_root / "ampere" / "temp" / "pvlib_ready.json"
        with_panel_data_path = project_root / "ampere" / "temp" / "with_panel_data.json"
        
        if pvlib_ready_path.exists():
            facilities = load_ampere_facilities(str(pvlib_ready_path))
            dataset_name = "pvlib_ready.json"
        elif with_panel_data_path.exists():
            facilities = load_ampere_facilities(str(with_panel_data_path))
            dataset_name = "with_panel_data.json"
        else:
            raise FileNotFoundError("No Ampere facility data found")
        
        print(f"   Loaded {len(facilities)} facilities from {dataset_name}")
        
        # Generate summary
        summary = get_facility_summary(facilities)
        print(f"   Geographic range: {summary['latitude_range']} lat, {summary['longitude_range']} lon")
        print(f"   Power range: {summary['power_range_kw']} kW")
        print(f"   Total power: {summary['total_power_kw']:.1f} kW")
        print(f"   Unique timezones: {summary['unique_timezones']}")
        
    except Exception as e:
        print(f"   Error loading facility data: {e}")
        return
    
    print()
    
    # 3. Process a few pilot facilities
    print("3. Processing pilot facilities...")
    
    # Select 3 diverse facilities for testing
    pilot_facilities = []
    
    # Try to get one from each continent if possible
    for facility in facilities[:10]:  # Check first 10
        lat = facility.get('latitude', 0)
        
        # Europe
        lon = facility.get('longitude', 0)
        if not any(f.get('continent') == 'EU' for f in pilot_facilities) and 35 <= lat <= 65 and -10 <= lon <= 50:
            facility['continent'] = 'EU'
            pilot_facilities.append(facility)
        # South America  
        
    if process_all:
        print(f"   Processing {len(facilities)} facilities. Results will be saved to: {results_file}")
        print("   This may take a while. Progress will be reported every 10 facilities.")
    else:
        print("3. Processing pilot facilities...")
        
        # Select a few representative sites for pilot testing
        # One from each major region
        regions = {
            'EU': [f for f in facilities if f.get('latitude', 0) > 35 and f.get('longitude', 0) > -30],
            'NA': [f for f in facilities if f.get('latitude', 0) > 35 and f.get('longitude', 0) < -30],
            'SA': [f for f in facilities if f.get('latitude', 0) < 35]
        }
        
        pilot_facilities = []
        for region_name, region_facilities in regions.items():
            if region_facilities:
                pilot_facilities.append(region_facilities[0])
        
        print(f"   Selected {len(pilot_facilities)} pilot facilities:")
        for i, facility in enumerate(pilot_facilities):
            lat = facility.get('latitude', 0)
            lon = facility.get('longitude', 0)
            power = facility.get('facility_power_kw', 0)
            print(f"   {i+1}. {facility.get('name', 'Unknown')} ({get_region(facility)}): {lat:.2f}, {lon:.2f}, {power:.1f} kW")
    
    # 4. Run simulations on facilities
    facilities_to_process = facilities if process_all else pilot_facilities
    
    print(f"\n4. Running simulations on {len(facilities_to_process)} facilities...\n")
    
    metrics = {}
    successful = 0
    failed = 0
    start_time = time.time()
    
    # For large datasets, we'll report progress periodically
    progress_interval = 10  # Report every 10 facilities
    
    for i, facility in enumerate(facilities_to_process):
        facility_name = facility.get('name', f'Facility_{i+1}')
        # Only print detailed progress for pilot facilities or at intervals
        if not process_all or (i % progress_interval == 0):
            print(f"   Processing: {facility_name} ({i+1}/{len(facilities_to_process)})")
        
        try:
            # Convert to pvlib format
            system, location = process_facility(facility)
            print(f"   ✓ Created PVSystem with {len(system.arrays)} arrays")
            
            # Get weather data
            # For years beyond NSRDB range (1998-2022), use TMY data
            if args.year > 2022:
                weather_data = weather_connector.get_weather_data(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    use_tmy=True  # Use TMY data for recent years
                )
            else:
                weather_data = weather_connector.get_weather_data(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    year=args.year  # Using specified year for validation analysis
                )
            
            source = weather_connector.last_used_source
            print(f"   ✓ Retrieved weather data from {source} ({len(weather_data)} records)")
            
            # Quick data quality check
            missing_data = weather_data[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']].isnull().sum()
            if missing_data.any():
                print(f"   ⚠ Missing data: {missing_data[missing_data > 0].to_dict()}")
            
            # With our new PVWatts-compatible PVSystem, no need for these parameter updates
            # The PVSystem already has the necessary parameters for temperature modeling
            
            # Run basic PV simulation
            mc = pvlib.modelchain.ModelChain(
                system, location,
                dc_model='pvwatts',
                ac_model='pvwatts',
                aoi_model='physical',  # Explicitly set AOI model to avoid inference error
                temperature_model='sapm'  # Use SAPM temperature model to match the parameters in PVSystem
            )
            
            mc.run_model(weather_data)
            
            # Calculate metrics - PVLib ModelChain results.ac is in Watts, need to convert to kWh
            # First convert from Watts to kWh (divide by 1000)
            annual_energy_kwh = mc.results.ac.sum() / 1000  # Convert from Wh to kWh
            
            # Get system size from facility data since we're using direct PVSystem now
            system_size_kw = facility.get('facility_power_kw', sum(group.get('power_kw', 0) for group in facility['panel_groups']))
            specific_yield = annual_energy_kwh / system_size_kw if system_size_kw > 0 else 0  # kWh/kWp
            capacity_factor = annual_energy_kwh / (8760 * system_size_kw) * 100 if system_size_kw > 0 else 0  # %
            
            # Get reference specific yield from facility data if available
            reference_yield = None
            weighted_reference_yield = 0
            total_ref_power = 0
            
            for group in facility['panel_groups']:
                group_power = group.get('power_kw', 0)
                group_yield = group.get('specific_yield_per_year')
                
                if group_yield is not None and group_power > 0:
                    weighted_reference_yield += group_yield * group_power
                    total_ref_power += group_power
            
            if total_ref_power > 0:
                reference_yield = weighted_reference_yield / total_ref_power
            
            # Calculate yield comparison if reference data exists
            yield_difference = None
            if reference_yield is not None:
                yield_difference = ((specific_yield / reference_yield) - 1) * 100  # % difference
                
            # Only print detailed results for pilot facilities or at intervals
            if not process_all or (i % progress_interval == 0):
                print(f"   ✓ Simulation completed:")
                print(f"     - Annual energy: {annual_energy_kwh:.1f} kWh")
                print(f"     - Simulated specific yield: {specific_yield:.1f} kWh/kWp")
                if reference_yield is not None:
                    print(f"     - Reference specific yield: {reference_yield:.1f} kWh/kWp")
                    print(f"     - Yield difference: {yield_difference:+.1f}%")
                else:
                    print(f"     - Reference specific yield: Not available")
                print(f"     - Capacity factor: {capacity_factor:.1f}%")
            
            successful += 1
            
            # Store results
            metrics[facility.get('id', '')] = {
                'facility_name': facility_name,
                'region': get_region(facility),
                'success': True,
                'annual_energy_kwh': annual_energy_kwh,
                'specific_yield': specific_yield,
                'reference_yield': reference_yield,
                'yield_difference': yield_difference,
                'capacity_factor': capacity_factor,
                'weather_source': source
            }
            
        except Exception as e:
            # Only print detailed errors for pilot facilities or at intervals
            if not process_all or (i % progress_interval == 0):
                print(f"   ✗ Simulation failed: {str(e)}")
            
            metrics[facility.get('id', '')] = {
                'facility_name': facility_name,
                'region': get_region(facility),
                'success': False,
                'error': str(e)
            }
            
            failed += 1
        
        print()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # 5. Print summary results
    print("\n5. Summary Results:")
    print("=" * 50)
    
    print(f"Processed {len(facilities_to_process)} facilities in {elapsed_time:.1f} seconds ({elapsed_time/len(facilities_to_process):.2f} sec/facility)")
    print(f"Successful simulations: {successful}/{len(facilities_to_process)} ({successful/len(facilities_to_process)*100:.1f}%)")
    print(f"Failed simulations: {failed}/{len(facilities_to_process)} ({failed/len(facilities_to_process)*100:.1f}%)")
    
    if successful > 0:
        # Calculate averages for successful simulations
        successful_metrics = [m for m in metrics.values() if m.get('success', False)]
        avg_yield = sum(m.get('specific_yield', 0) for m in successful_metrics) / successful
        avg_cf = sum(m.get('capacity_factor', 0) for m in successful_metrics) / successful
        
        # Calculate average yield difference where reference exists
        yield_diffs = [m.get('yield_difference', 0) for m in successful_metrics if m.get('yield_difference') is not None]
        avg_yield_diff = sum(yield_diffs) / len(yield_diffs) if yield_diffs else None
        
        print("\nAverage Performance:")
        print(f"  Simulated Specific Yield: {avg_yield:.1f} kWh/kWp")
        print(f"  Capacity Factor: {avg_cf:.1f}%")
        if avg_yield_diff is not None:
            print(f"  Average Yield Difference: {avg_yield_diff:+.1f}% compared to reference")
    
    if not process_all and failed > 0:
        print("\nFailed Simulations:")
        for facility_id, metric in metrics.items():
            if not metric.get('success', False):
                name = metric.get('facility_name', 'Unknown')
                error = metric.get('error', 'Unknown error')
                print(f"  • {name}: {error}")
    
    # Export results to JSON if processing all facilities
    if process_all:
        # Add summary statistics to the metrics
        summary = {
            'total_facilities': len(facilities_to_process),
            'successful': successful,
            'failed': failed,
            'success_rate': successful/len(facilities_to_process)*100 if len(facilities_to_process) > 0 else 0,
            'processing_time_seconds': elapsed_time,
            'average_yield': avg_yield if successful > 0 else 0,
            'average_capacity_factor': avg_cf if successful > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Export results
        export_data = {
            'summary': summary,
            'facilities': metrics
        }
        
        with open(results_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to: {results_file}")

    print("\n6. Cache Information:")
    print("=" * 30)
    cache_info = weather_connector.get_cache_info()
    print(f"Cache enabled: {cache_info['cache_enabled']}")
    print(f"Cache directory: {cache_info['cache_dir']}")
    print(f"Cached files: {cache_info['total_files']}")
    print(f"Cache size: {cache_info['total_size_mb']:.2f} MB")
    if cache_info['files_by_source']:
        print("Files by source:")
        for source, count in cache_info['files_by_source'].items():
            print(f"  {source}: {count} files")
    
    print("\n=== Example completed successfully! ===")

if __name__ == "__main__":
    main()