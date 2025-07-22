# PV Plant Modeling Website

A web application for modeling and simulating photovoltaic (PV) plants using the PVLib Python library and NREL weather data services.

## Overview

This application provides a user-friendly interface for:
- Configuring PV plant parameters (location, system specifications, array configuration)
- Fetching weather data from NREL NSRDB and PVGIS services
- Running PV performance simulations using PVLib ModelChain
- Visualizing results and exporting data

## Architecture

```
pv-plant-website/
├── docs/                    # Development documentation
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── models/         # Pydantic data models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # PVLib integration services
│   │   └── utils/          # Helper functions
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── utils/          # Helper functions
│   ├── package.json
│   └── public/
└── shared/                 # Shared configuration
    └── pvlib_integration/  # PVLib wrapper services
```

## Technology Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **Pydantic** - Data validation and serialization
- **PVLib Python** - Photovoltaic system modeling
- **SQLite** - Simple file-based database for results storage

### Frontend
- **React** - Component-based UI framework
- **Chart.js** - Data visualization
- **Material-UI** - Pre-built UI components
- **Axios** - HTTP client for API calls

### Integration
- **NREL Weather Connector** - Multi-source weather data fetching
- **PVLib ModelChain** - Standardized PV simulation workflow

## Features

### Core Features
- **Location Selection**: Input coordinates or use address lookup
- **System Configuration**: Specify DC capacity, module type, inverter type
- **Array Configuration**: Set tilt, azimuth, and mounting type (fixed/tracking)
- **Loss Parameters**: Configure soiling, shading, and other loss factors
- **Weather Data**: Automatic fetching from NREL NSRDB with PVGIS fallback
- **PV Simulation**: Annual and monthly energy yield calculations
- **Results Visualization**: Charts showing monthly energy production
- **Data Export**: Download results in CSV format

### Performance Metrics
- Annual energy yield (kWh/year)
- Monthly energy production
- Performance ratio (PR)
- Capacity factor (CF)
- Specific yield (kWh/kWp/year)

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- NREL API key (free registration at https://developer.nrel.gov/signup/)

### Installation

1. **Clone the repository**
   ```bash
   cd /Users/mode/Documents/Code/PVLib/pv-plant-website
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file in project root
   echo "NREL_API_KEY=your_api_key_here" > .env
   echo "NREL_USER_EMAIL=your_email@domain.com" >> .env
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm start
   ```

3. **Open your browser**
   Navigate to `http://localhost:3000`

## API Endpoints

### System Configuration
- `POST /api/configure` - Configure PV system parameters
- `GET /api/weather/{lat}/{lon}` - Fetch weather data for location
- `POST /api/simulate` - Run PV simulation
- `GET /api/results/{simulation_id}` - Retrieve simulation results

### Data Management
- `GET /api/modules` - List available PV modules
- `GET /api/inverters` - List available inverters
- `GET /api/export/{simulation_id}` - Export results as CSV

## Development

### Backend Development
```bash
cd backend
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration

### Environment Variables
- `NREL_API_KEY` - NREL API key for weather data access
- `NREL_USER_EMAIL` - Email address for NREL API
- `DATABASE_URL` - Database connection string (default: SQLite)
- `CORS_ORIGINS` - Allowed CORS origins for API access

### PVLib Integration
The application uses the existing PVLib and NREL weather connector infrastructure:
- Weather data fetching via `nrel/weather_connector.py`
- PV modeling via `pvlib-python/` ModelChain workflow
- Module/inverter databases from PVLib SAM databases

## Deployment

### Production Deployment
1. Build the frontend: `npm run build`
2. Configure environment variables
3. Deploy backend as WSGI application
4. Serve frontend as static files
5. Set up reverse proxy (nginx/Apache)

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project uses the same license as the parent PVLib project.

## Support

For issues and questions:
- Check the [User Guide](user-guide.md)
- Review the [API Documentation](api-docs.md)
- Create an issue in the project repository

## Related Projects

- [PVLib Python](https://github.com/pvlib/pvlib-python) - Core PV modeling library
- [NREL NSRDB](https://nsrdb.nrel.gov/) - National Solar Radiation Database
- [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/) - European solar resource data