"""
Data processing utilities for Ampere facility data.

Handles conversion from Ampere data format to pvlib-compatible format,
with support for both dataset variations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add pvlib-python to path if not already available
try:
    import pvlib
except ImportError:
    project_root = Path(__file__).parent.parent
    pvlib_path = project_root / "pvlib-python"
    if pvlib_path.exists():
        sys.path.insert(0, str(pvlib_path))
        import pvlib
    else:
        raise ImportError("pvlib not found. Install with: pip install pvlib-python")

from .config import get_logger

logger = get_logger(__name__)

def load_ampere_facilities(file_path: str) -> List[Dict[str, Any]]:
    """
    Load Ampere facility data from JSON file.
    
    Parameters
    ----------
    file_path : str
        Path to the JSON file containing facility data
        
    Returns
    -------
    List[Dict[str, Any]]
        List of facility dictionaries
        
    Raises
    ------
    FileNotFoundError
        If the specified file doesn't exist
    ValueError
        If the file format is invalid
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Facility data file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different file formats
        if 'facilities' in data:
            facilities = data['facilities']
        elif isinstance(data, list):
            facilities = data
        else:
            raise ValueError("Invalid file format: expected 'facilities' key or list of facilities")
        
        logger.info(f"Loaded {len(facilities)} facilities from {file_path.name}")
        return facilities
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading facility data: {e}")

def normalize_facility_data(facility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize facility data to a consistent format.
    
    Handles different naming conventions between datasets:
    - pvlib_ready.json uses "tilt" 
    - with_panel_data.json uses "elevation"
    
    Parameters
    ----------
    facility : Dict[str, Any]
        Raw facility data dictionary
        
    Returns
    -------
    Dict[str, Any]
        Normalized facility data
    """
    normalized = facility.copy()
    
    # Normalize panel groups
    if 'panel_groups' in facility:
        panel_groups = facility['panel_groups']
    elif 'panelGroups' in facility:
        panel_groups = facility['panelGroups']
    else:
        raise ValueError(f"No panel groups found in facility {facility.get('id', 'unknown')}")
    
    # Normalize each panel group
    normalized_groups = []
    for group in panel_groups:
        normalized_group = group.copy()
        
        # Handle tilt vs elevation naming
        if 'elevation' in group and 'tilt' not in group:
            normalized_group['tilt'] = group['elevation']
            logger.debug(f"Converted 'elevation' to 'tilt' for group {group.get('name', 'unnamed')}")
        
        # Ensure required fields exist
        required_fields = ['name', 'azimuth', 'tilt']
        missing_fields = [field for field in required_fields if field not in normalized_group]
        if missing_fields:
            logger.warning(f"Missing fields in panel group: {missing_fields}")
        
        # Handle power field variations
        if 'power_kw' in group:
            normalized_group['power_kw'] = group['power_kw']
        elif 'nominalPower' in group:
            normalized_group['power_kw'] = group['nominalPower']
        else:
            logger.warning(f"No power rating found for panel group {group.get('name', 'unnamed')}")
        
        normalized_groups.append(normalized_group)
    
    normalized['panel_groups'] = normalized_groups
    
    # Normalize facility-level power
    if 'facility_power_kw' not in normalized and 'nominalPower' in facility:
        normalized['facility_power_kw'] = facility['nominalPower']
    
    # Normalize coordinates
    if 'coordinates' in facility:
        coords = facility['coordinates']
        if 'lat' in coords and 'latitude' not in normalized:
            normalized['latitude'] = coords['lat']
        if 'long' in coords and 'longitude' not in normalized:
            normalized['longitude'] = coords['long']
    
    # Extract timezone from address if needed
    if 'timezone' not in normalized and 'address' in facility:
        address = facility['address']
        if 'timezone' in address:
            normalized['timezone'] = address['timezone']
    
    return normalized

def process_facility(facility: Dict[str, Any]) -> Tuple[pvlib.pvsystem.PVSystem, pvlib.location.Location]:
    """
    Convert Ampere facility data to pvlib PVSystem and Location objects.
    
    Parameters
    ----------
    facility : Dict[str, Any]
        Facility data dictionary (will be normalized automatically)
        
    Returns
    -------
    Tuple[pvlib.pvsystem.PVSystem, pvlib.location.Location]
        PVLib system and location objects
        
    Raises
    ------
    ValueError
        If required facility data is missing
    """
    # Normalize facility data first
    facility = normalize_facility_data(facility)
    
    # Validate required fields
    required_fields = ['latitude', 'longitude', 'panel_groups']
    missing_fields = [field for field in required_fields if field not in facility]
    if missing_fields:
        raise ValueError(f"Missing required fields in facility data: {missing_fields}")
    
    # Create location object
    location_kwargs = {
        'latitude': facility['latitude'],
        'longitude': facility['longitude']
    }
    
    if 'timezone' in facility:
        location_kwargs['tz'] = facility['timezone']
    
    if 'altitude' in facility:
        location_kwargs['altitude'] = facility['altitude']
    elif 'address' in facility and 'altitude' in facility['address']:
        location_kwargs['altitude'] = facility['address']['altitude']
    
    if 'name' in facility:
        location_kwargs['name'] = facility['name']
    
    location = pvlib.location.Location(**location_kwargs)
    
    # For PVWatts, we'll use a simpler approach to create a PVSystem directly
    # rather than using arrays, which can cause issues with temperature models
    
    # Calculate total DC power and weighted average tilt/azimuth if multiple panel groups
    total_dc_power_w = 0
    weighted_tilt = 0
    weighted_azimuth = 0
    
    for group in facility['panel_groups']:
        power_kw = group.get('power_kw', 0)
        power_w = power_kw * 1000
        tilt = group.get('tilt', group.get('elevation', 0))
        azimuth = group.get('azimuth', 180)  # Default south-facing
        
        total_dc_power_w += power_w
        weighted_tilt += tilt * power_w
        weighted_azimuth += azimuth * power_w
    
    # Avoid division by zero
    if total_dc_power_w > 0:
        weighted_tilt = weighted_tilt / total_dc_power_w
        weighted_azimuth = weighted_azimuth / total_dc_power_w
    
    # Get temperature coefficient if available
    temp_coeff = facility.get('temperatureCoefficient', -0.004)  # Default for c-Si
    
    # Convert from %/°C to fraction/°C if needed
    if abs(temp_coeff) > 0.01:  # Likely in %/°C
        temp_coeff = temp_coeff / 100
    
    # For PVWatts with minimal data, create simplified module parameters
    module_parameters = {
        'pdc0': total_dc_power_w,  # Total DC power in watts
        'gamma_pdc': temp_coeff
    }
    
    # Add technology if available
    if 'technology' in facility:
        module_parameters['Technology'] = facility['technology']
    elif 'Technology' in facility:
        module_parameters['Technology'] = facility['Technology']
    
    # Add standard parameters needed for temperature modeling
    # These are consistent with PVWatts model defaults
    temperature_model_parameters = {
        'module_type': 'glass_polymer',  # Standard module type for PVWatts
        'noct': 45  # Nominal operating cell temperature (°C)
    }
    
    # Merge into module parameters
    module_parameters.update(temperature_model_parameters)
    
    # Estimate inverter parameters
    facility_power_w = facility.get('facility_power_kw', total_dc_power_w / 1000) * 1000
    inverter_parameters = {
        'pdc0': facility_power_w,  # DC input rating in watts
        'eta_inv_nom': 0.96  # Typical inverter efficiency
    }
    
    # Create a simpler PVWatts-compatible PVSystem
    system = pvlib.pvsystem.PVSystem(
        surface_tilt=weighted_tilt,
        surface_azimuth=weighted_azimuth,
        module_parameters=module_parameters,
        inverter_parameters=inverter_parameters,
        module_type='glass_polymer',  # For temperature model
        racking_model='open_rack'      # For temperature model
    )
    
    facility_power_kw = total_dc_power_w / 1000
    logger.info(f"Created PVSystem for {facility.get('name', 'Unknown')}: PVWatts-compatible, {facility_power_kw:.1f} kW total")
    
    return system, location

def validate_facility_data(facility: Dict[str, Any]) -> List[str]:
    """
    Validate facility data and return list of issues found.
    
    Parameters
    ----------
    facility : Dict[str, Any]
        Facility data dictionary
        
    Returns
    -------
    List[str]
        List of validation issues (empty if no issues)
    """
    issues = []
    
    # Check required fields
    required_fields = ['id', 'name', 'latitude', 'longitude']
    for field in required_fields:
        if field not in facility:
            issues.append(f"Missing required field: {field}")
    
    # Validate coordinates
    if 'latitude' in facility:
        lat = facility['latitude']
        if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
            issues.append(f"Invalid latitude: {lat}")
    
    if 'longitude' in facility:
        lon = facility['longitude']
        if not isinstance(lon, (int, float)) or not -180 <= lon <= 180:
            issues.append(f"Invalid longitude: {lon}")
    
    # Check panel groups
    panel_groups = facility.get('panel_groups', facility.get('panelGroups', []))
    if not panel_groups:
        issues.append("No panel groups found")
    else:
        for i, group in enumerate(panel_groups):
            group_issues = validate_panel_group(group, i)
            issues.extend(group_issues)
    
    return issues

def validate_panel_group(group: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single panel group.
    
    Parameters
    ----------
    group : Dict[str, Any]
        Panel group data dictionary
    index : int
        Group index for error reporting
        
    Returns
    -------
    List[str]
        List of validation issues for this group
    """
    issues = []
    prefix = f"Panel group {index}"
    
    # Check for tilt/elevation
    tilt = group.get('tilt', group.get('elevation'))
    if tilt is None:
        issues.append(f"{prefix}: Missing tilt/elevation angle")
    elif not isinstance(tilt, (int, float)) or not 0 <= tilt <= 90:
        issues.append(f"{prefix}: Invalid tilt angle: {tilt}")
    
    # Check azimuth
    azimuth = group.get('azimuth')
    if azimuth is None:
        issues.append(f"{prefix}: Missing azimuth angle")
    elif not isinstance(azimuth, (int, float)) or not -180 <= azimuth <= 180:
        issues.append(f"{prefix}: Invalid azimuth angle: {azimuth}")
    
    # Check power rating
    power = group.get('power_kw', group.get('nominalPower'))
    if power is None:
        issues.append(f"{prefix}: Missing power rating")
    elif not isinstance(power, (int, float)) or power <= 0:
        issues.append(f"{prefix}: Invalid power rating: {power}")
    
    return issues

def get_facility_summary(facilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for a list of facilities.
    
    Parameters
    ----------
    facilities : List[Dict[str, Any]]
        List of facility dictionaries
        
    Returns
    -------
    Dict[str, Any]
        Summary statistics
    """
    if not facilities:
        return {'total_facilities': 0}
    
    # Basic counts
    total_facilities = len(facilities)
    
    # Geographic analysis
    latitudes = [f.get('latitude') for f in facilities if f.get('latitude') is not None]
    longitudes = [f.get('longitude') for f in facilities if f.get('longitude') is not None]
    
    # Power analysis
    powers = []
    for facility in facilities:
        power = facility.get('facility_power_kw', facility.get('nominalPower'))
        if power:
            powers.append(power)
    
    # Timezone analysis
    timezones = [f.get('timezone') for f in facilities if f.get('timezone')]
    unique_timezones = list(set(timezones)) if timezones else []
    
    # Panel group analysis
    total_groups = 0
    multi_array_facilities = 0
    for facility in facilities:
        groups = facility.get('panel_groups', facility.get('panelGroups', []))
        group_count = len(groups)
        total_groups += group_count
        if group_count > 1:
            multi_array_facilities += 1
    
    summary = {
        'total_facilities': total_facilities,
        'facilities_with_coordinates': len(latitudes),
        'latitude_range': (min(latitudes), max(latitudes)) if latitudes else None,
        'longitude_range': (min(longitudes), max(longitudes)) if longitudes else None,
        'power_range_kw': (min(powers), max(powers)) if powers else None,
        'total_power_kw': sum(powers) if powers else 0,
        'average_power_kw': sum(powers) / len(powers) if powers else 0,
        'unique_timezones': len(unique_timezones),
        'timezone_list': unique_timezones,
        'total_panel_groups': total_groups,
        'multi_array_facilities': multi_array_facilities,
        'average_groups_per_facility': total_groups / total_facilities if total_facilities > 0 else 0
    }
    
    return summary