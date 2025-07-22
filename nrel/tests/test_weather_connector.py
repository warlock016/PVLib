"""
Unit tests for the WeatherDataConnector class.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import sys

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add pvlib-python if available
pvlib_path = project_root / "pvlib-python"
if pvlib_path.exists():
    sys.path.insert(0, str(pvlib_path))

from nrel.weather_connector import WeatherDataConnector
from nrel.config import Config

class TestWeatherDataConnector(unittest.TestCase):
    """Test cases for WeatherDataConnector."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config to use temp directory
        self.original_cache_dir = Config().cache_dir
        Config().cache_dir = Path(self.temp_dir)
        
        # Clear any existing cache files in temp directory
        for pattern in ["*.parquet", "*.pkl"]:
            for cache_file in Path(self.temp_dir).glob(pattern):
                cache_file.unlink()
        
        # Create test weather data
        self.test_weather_data = pd.DataFrame({
            'ghi': [100, 200, 300, 400, 500],
            'dni': [150, 250, 350, 450, 550], 
            'dhi': [50, 100, 150, 200, 250],
            'temp_air': [15, 20, 25, 30, 25],
            'wind_speed': [2, 3, 4, 5, 4]
        }, index=pd.date_range('2023-01-01', periods=5, freq='H', tz='UTC'))
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original cache directory
        Config().cache_dir = self.original_cache_dir
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test WeatherDataConnector initialization."""
        connector = WeatherDataConnector()
        
        self.assertEqual(connector.primary_source, 'nsrdb')
        self.assertEqual(connector.fallback_sources, ['pvgis'])
        self.assertTrue(connector.enable_cache)
        self.assertIsNone(connector.last_used_source)
    
    def test_initialization_custom_sources(self):
        """Test initialization with custom sources."""
        connector = WeatherDataConnector(
            primary_source='pvgis',
            fallback_sources=['nsrdb'],
            enable_cache=False
        )
        
        self.assertEqual(connector.primary_source, 'pvgis')
        self.assertEqual(connector.fallback_sources, ['nsrdb'])
        self.assertFalse(connector.enable_cache)
    
    def test_validate_inputs(self):
        """Test input validation."""
        connector = WeatherDataConnector()
        
        # Valid inputs should not raise
        try:
            connector.get_weather_data(40.0, -105.0)
        except ValueError:
            self.fail("Valid coordinates raised ValueError")
        except Exception:
            # Other exceptions are OK (API might fail in tests)
            pass
        
        # Invalid latitude
        with self.assertRaises(ValueError):
            connector.get_weather_data(91.0, -105.0)
        
        with self.assertRaises(ValueError):
            connector.get_weather_data(-91.0, -105.0)
        
        # Invalid longitude
        with self.assertRaises(ValueError):
            connector.get_weather_data(40.0, 181.0)
        
        with self.assertRaises(ValueError):
            connector.get_weather_data(40.0, -181.0)
    
    @patch('nrel.weather_connector.pvlib.iotools.get_psm3')
    def test_nsrdb_data_fetch(self, mock_get_psm3):
        """Test NSRDB data fetching."""
        # Mock successful NSRDB response
        mock_get_psm3.return_value = (self.test_weather_data, {'Station Name': 'Test Station'})
        
        connector = WeatherDataConnector(enable_cache=False)
        
        with patch('nrel.weather_connector.config.is_nrel_available', return_value=True):
            result = connector._get_nsrdb_data(40.0, -105.0, 2023)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)
        mock_get_psm3.assert_called_once()
    
    @patch('nrel.weather_connector.pvlib.iotools.get_pvgis_tmy')
    def test_pvgis_data_fetch(self, mock_get_pvgis):
        """Test PVGIS data fetching."""
        # Mock successful PVGIS response (newer version returns only 2 values)
        mock_get_pvgis.return_value = (
            self.test_weather_data, 
            {'location': 'Test Location'}
        )
        
        connector = WeatherDataConnector()
        result = connector._get_pvgis_data(52.5, 13.4)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)
        mock_get_pvgis.assert_called_once()
    
    def test_data_validation(self):
        """Test weather data validation."""
        connector = WeatherDataConnector()
        
        # Valid data should pass
        valid_data = connector._validate_weather_data(self.test_weather_data, 'test')
        self.assertIsInstance(valid_data, pd.DataFrame)
        
        # Empty data should fail
        with self.assertRaises(ValueError):
            connector._validate_weather_data(pd.DataFrame(), 'test')
        
        # Missing columns should fail
        incomplete_data = self.test_weather_data.drop(columns=['ghi'])
        with self.assertRaises(ValueError):
            connector._validate_weather_data(incomplete_data, 'test')
    
    def test_cache_operations(self):
        """Test cache save and load operations."""
        connector = WeatherDataConnector(enable_cache=True)
        
        # Save to cache
        connector._save_to_cache(self.test_weather_data, 40.0, -105.0, 'test', 2023)
        
        # Load from cache
        cached_data = connector._load_from_cache(40.0, -105.0, 2023)
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 5)
        
        # Compare data content (may have different index/column dtypes after pickle/parquet)
        pd.testing.assert_frame_equal(
            cached_data.reset_index(drop=True), 
            self.test_weather_data.reset_index(drop=True),
            check_dtype=False,
            check_index_type=False
        )
    
    def test_cache_disabled(self):
        """Test behavior when cache is disabled."""
        connector = WeatherDataConnector(enable_cache=False)
        
        # Save should do nothing
        connector._save_to_cache(self.test_weather_data, 40.0, -105.0, 'test', 2023)
        
        # Load should return None
        cached_data = connector._load_from_cache(40.0, -105.0, 2023)
        self.assertIsNone(cached_data)
    
    def test_cache_info(self):
        """Test cache information retrieval."""
        # Clear any existing cache files first
        for pattern in ["*.parquet", "*.pkl"]:
            for cache_file in Path(self.temp_dir).glob(pattern):
                cache_file.unlink()
        
        connector = WeatherDataConnector(enable_cache=True)
        
        # Save some test data
        connector._save_to_cache(self.test_weather_data, 40.0, -105.0, 'nsrdb', 2023)
        connector._save_to_cache(self.test_weather_data, 52.5, 13.4, 'pvgis')
        
        cache_info = connector.get_cache_info()
        
        self.assertTrue(cache_info['cache_enabled'])
        self.assertEqual(cache_info['total_files'], 2)
        self.assertGreater(cache_info['total_size_mb'], 0)
        self.assertIn('nsrdb', cache_info['files_by_source'])
        self.assertIn('pvgis', cache_info['files_by_source'])
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Clear any existing cache files first
        for pattern in ["*.parquet", "*.pkl"]:
            for cache_file in Path(self.temp_dir).glob(pattern):
                cache_file.unlink()
        
        connector = WeatherDataConnector(enable_cache=True)
        
        # Save some test data
        connector._save_to_cache(self.test_weather_data, 40.0, -105.0, 'test1', 2023)
        connector._save_to_cache(self.test_weather_data, 52.5, 13.4, 'test2')
        
        # Verify files exist
        cache_info = connector.get_cache_info()
        self.assertEqual(cache_info['total_files'], 2)
        
        # Clear cache
        removed_count = connector.clear_cache()
        self.assertEqual(removed_count, 2)
        
        # Verify cache is empty
        cache_info = connector.get_cache_info()
        self.assertEqual(cache_info['total_files'], 0)

if __name__ == '__main__':
    unittest.main()