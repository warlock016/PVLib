"""
Unit tests for data processing utilities.
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add pvlib-python if available
pvlib_path = project_root / "pvlib-python"
if pvlib_path.exists():
    sys.path.insert(0, str(pvlib_path))

from nrel.data_utils import (
    load_ampere_facilities, 
    normalize_facility_data,
    process_facility,
    validate_facility_data,
    get_facility_summary
)

class TestDataUtils(unittest.TestCase):
    """Test cases for data processing utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample facility data in pvlib_ready format
        self.pvlib_ready_facility = {
            "id": "test_facility_1",
            "name": "Test Solar Farm",
            "latitude": 40.0,
            "longitude": -105.0,
            "timezone": "America/Denver",
            "facility_power_kw": 1000.0,
            "panel_groups": [
                {
                    "name": "South Array",
                    "azimuth": 180,
                    "tilt": 30,
                    "power_kw": 500.0
                },
                {
                    "name": "East Array", 
                    "azimuth": 90,
                    "tilt": 25,
                    "power_kw": 500.0
                }
            ]
        }
        
        # Sample facility data in with_panel_data format
        self.with_panel_data_facility = {
            "id": "test_facility_2",
            "name": "Test Solar Plant",
            "nominalPower": 2000.0,
            "coordinates": {
                "lat": 52.5,
                "long": 13.4
            },
            "address": {
                "timezone": "Europe/Berlin"
            },
            "panelGroups": [
                {
                    "name": "Main Array",
                    "azimuth": 180,
                    "elevation": 35,  # Note: elevation instead of tilt
                    "nominalPower": 2000.0,
                    "temperatureCoefficient": -0.4,
                    "yearlyDegredation": 0.005,
                    "specificYieldPerYear": 1200.0
                }
            ]
        }
    
    def test_normalize_facility_data_pvlib_ready(self):
        """Test normalization of pvlib_ready format data."""
        normalized = normalize_facility_data(self.pvlib_ready_facility)
        
        # Should preserve existing structure
        self.assertEqual(normalized['id'], 'test_facility_1')
        self.assertEqual(normalized['latitude'], 40.0)
        self.assertEqual(normalized['longitude'], -105.0)
        self.assertEqual(len(normalized['panel_groups']), 2)
        
        # Check panel groups
        for group in normalized['panel_groups']:
            self.assertIn('tilt', group)
            self.assertIn('azimuth', group)
            self.assertIn('power_kw', group)
    
    def test_normalize_facility_data_with_panel_data(self):
        """Test normalization of with_panel_data format data."""
        normalized = normalize_facility_data(self.with_panel_data_facility)
        
        # Should convert coordinates
        self.assertEqual(normalized['latitude'], 52.5)
        self.assertEqual(normalized['longitude'], 13.4)
        
        # Should convert nominalPower to facility_power_kw
        self.assertEqual(normalized['facility_power_kw'], 2000.0)
        
        # Should convert timezone from address
        self.assertEqual(normalized['timezone'], 'Europe/Berlin')
        
        # Should convert panelGroups to panel_groups
        self.assertIn('panel_groups', normalized)
        self.assertEqual(len(normalized['panel_groups']), 1)
        
        # Should convert elevation to tilt
        group = normalized['panel_groups'][0]
        self.assertEqual(group['tilt'], 35)
        self.assertIn('power_kw', group)
    
    def test_process_facility_pvlib_ready(self):
        """Test processing pvlib_ready facility to PVSystem."""
        system, location = process_facility(self.pvlib_ready_facility)
        
        # Check location
        self.assertEqual(location.latitude, 40.0)
        self.assertEqual(location.longitude, -105.0)
        self.assertEqual(str(location.tz), 'America/Denver')
        
        # Check system
        self.assertEqual(len(system.arrays), 2)
        self.assertEqual(system.name, 'Test Solar Farm')
        
        # Check arrays
        array1 = system.arrays[0]
        self.assertEqual(array1.mount.surface_tilt, 30)
        self.assertEqual(array1.mount.surface_azimuth, 180)
        self.assertEqual(array1.module_parameters['pdc0'], 500000)  # 500 kW in W
        
        array2 = system.arrays[1]  
        self.assertEqual(array2.mount.surface_tilt, 25)
        self.assertEqual(array2.mount.surface_azimuth, 90)
    
    def test_process_facility_with_panel_data(self):
        """Test processing with_panel_data facility to PVSystem."""
        system, location = process_facility(self.with_panel_data_facility)
        
        # Check location (should be normalized from coordinates)
        self.assertEqual(location.latitude, 52.5)
        self.assertEqual(location.longitude, 13.4)
        self.assertEqual(str(location.tz), 'Europe/Berlin')
        
        # Check system
        self.assertEqual(len(system.arrays), 1)
        
        # Check array (elevation should be converted to tilt)
        array = system.arrays[0]
        self.assertEqual(array.mount.surface_tilt, 35)
        self.assertEqual(array.mount.surface_azimuth, 180)
    
    def test_validate_facility_data_valid(self):
        """Test validation of valid facility data."""
        issues = validate_facility_data(self.pvlib_ready_facility)
        self.assertEqual(len(issues), 0)
    
    def test_validate_facility_data_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_facility = {
            "name": "Test",
            # Missing id, latitude, longitude
        }
        
        issues = validate_facility_data(invalid_facility)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("Missing required field" in issue for issue in issues))
    
    def test_validate_facility_data_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        invalid_facility = self.pvlib_ready_facility.copy()
        invalid_facility['latitude'] = 91.0  # Invalid latitude
        
        issues = validate_facility_data(invalid_facility)
        self.assertTrue(any("Invalid latitude" in issue for issue in issues))
    
    def test_validate_facility_data_no_panel_groups(self):
        """Test validation with no panel groups."""
        invalid_facility = self.pvlib_ready_facility.copy()
        invalid_facility['panel_groups'] = []
        
        issues = validate_facility_data(invalid_facility)
        self.assertTrue(any("No panel groups found" in issue for issue in issues))
    
    def test_load_ampere_facilities_from_temp_file(self):
        """Test loading facilities from temporary JSON file."""
        # Create temporary file with test data
        test_data = {
            "facilities": [
                self.pvlib_ready_facility,
                self.with_panel_data_facility
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            facilities = load_ampere_facilities(temp_path)
            self.assertEqual(len(facilities), 2)
            self.assertEqual(facilities[0]['id'], 'test_facility_1')
            self.assertEqual(facilities[1]['id'], 'test_facility_2')
        finally:
            Path(temp_path).unlink()
    
    def test_load_ampere_facilities_file_not_found(self):
        """Test loading from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_ampere_facilities('non_existent_file.json')
    
    def test_get_facility_summary(self):
        """Test facility summary generation."""
        facilities = [self.pvlib_ready_facility, self.with_panel_data_facility]
        
        # Normalize the second facility first
        facilities[1] = normalize_facility_data(facilities[1])
        
        summary = get_facility_summary(facilities)
        
        self.assertEqual(summary['total_facilities'], 2)
        self.assertEqual(summary['facilities_with_coordinates'], 2)
        self.assertIsNotNone(summary['latitude_range'])
        self.assertIsNotNone(summary['longitude_range'])
        self.assertEqual(summary['total_power_kw'], 3000.0)  # 1000 + 2000
        self.assertEqual(summary['average_power_kw'], 1500.0)
        self.assertEqual(summary['total_panel_groups'], 3)  # 2 + 1
        self.assertEqual(summary['multi_array_facilities'], 1)  # Only first facility has multiple arrays
    
    def test_get_facility_summary_empty(self):
        """Test summary generation with empty facility list."""
        summary = get_facility_summary([])
        self.assertEqual(summary['total_facilities'], 0)

if __name__ == '__main__':
    unittest.main()