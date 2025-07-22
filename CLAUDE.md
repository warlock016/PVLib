# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pvlib-python is a community-developed toolbox for simulating photovoltaic energy systems. It provides functions and classes for modeling solar irradiance, PV system performance, and related tasks. The core mission is to provide open, reliable, interoperable, and benchmark implementations of PV system models.

## Development Commands

### Testing
```bash
# Run all tests
pytest tests

# Run tests for a specific module  
pytest tests/test_clearsky.py

# Run a single test
pytest tests/test_clearsky.py::test_ineichen_nans

# Run tests with network-dependent functionality
pytest tests --remote-data

# Run tests excluding iotools (standard CI approach)
pytest tests --ignore=tests/iotools

# Debug test failures
pytest tests --pdb
```

### Linting
```bash
# Code style checking (configured in setup.cfg)
flake8

# Line length: 79 characters max
# Ignores: E201, E241, E226, W503, W504
```

### Documentation
```bash
# Build documentation (from docs/sphinx/ directory)
cd docs/sphinx
make html

# Clean documentation build
make clean

# Check documentation links
make linkcheck
```

### Installation for Development
```bash
# Install with test dependencies
pip install .[test]

# Install with all optional dependencies
pip install .[all]

# Install in development mode
pip install -e .
```

## Code Architecture

### Core Module Structure
- **pvlib/__init__.py**: Main package imports organized by functional area
- **Functions layer**: Core computational functions (irradiance.py, solarposition.py, clearsky.py, etc.)
- **Classes layer**: PVSystem and Location wrapper classes providing convenience methods
- **ModelChain layer**: High-level simulation workflow orchestration

### Key Modules
- **irradiance.py**: Solar irradiance modeling and transposition
- **solarposition.py**: Solar position calculations 
- **clearsky.py**: Clear-sky irradiance models
- **pvsystem.py**: PV system modeling (PVSystem class)
- **location.py**: Geographic location handling (Location class)
- **modelchain.py**: End-to-end simulation workflows (ModelChain class)
- **iotools/**: Data input/output for various weather data sources
- **ivtools/**: Current-voltage curve analysis and parameter extraction
- **bifacial/**: Bifacial PV modeling
- **spectrum/**: Spectral irradiance and mismatch modeling

### Testing Architecture
The test suite follows a three-layer approach:
1. **Function tests**: Test core computational functions independently
2. **PVSystem/Location tests**: Test class methods wrap functions correctly (uses pytest-mock)
3. **ModelChain tests**: Test workflow orchestration and model selection

## Dependencies

### Core Dependencies
- numpy >= 1.19.3
- pandas >= 1.3.0  
- scipy >= 1.6.0
- pytz, requests, h5py

### Optional Dependencies
- cython, numba: Performance optimization
- ephem: Alternative solar position calculations
- nrel-pysam: NREL System Advisor Model integration
- statsmodels: Statistical modeling

### Test Dependencies
- pytest, pytest-cov, pytest-mock, pytest-timeout, pytest-rerunfailures, pytest-remotedata
- requests-mock: Mock HTTP requests in tests

## Development Notes

### Code Style
- Max line length: 79 characters
- No print() or logging calls in core code (rare exceptions)
- Use pytest's --pdb for debugging rather than print statements

### Testing Best Practices  
- Test functions independently of other pvlib functions
- Test all reasonable input types (floats, arrays, Series, etc.)
- Use pytest-mock for testing class method delegation to functions
- Mark network-dependent tests with @pytest.mark.remote_data
- Write tests that cover full algorithm validity range

### Build System
- Uses setuptools with pyproject.toml configuration
- Optional C extension (spa_c_files) for high-precision solar position
- GitHub Actions CI for multiple Python versions (3.9-3.13) and platforms
- Conda and bare pip installation testing

### Documentation
- Sphinx-based documentation with example galleries
- ReadTheDocs integration
- Examples organized by topic in docs/examples/