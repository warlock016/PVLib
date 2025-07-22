import React from 'react';
import { Box, Typography, Card, CardContent, Grid } from '@mui/material';

const AboutPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        About PV Plant Modeling Website
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overview
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                This web application provides a user-friendly interface for modeling and 
                simulating photovoltaic (PV) plants using the PVLib Python library and 
                real weather data from NREL and PVGIS sources.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                The application simplifies the complex process of PV system simulation 
                by providing an intuitive interface for system configuration, weather 
                data integration, and results analysis.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Technology Stack
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Backend:</strong> FastAPI, Python, SQLAlchemy, PVLib
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Frontend:</strong> React, TypeScript, Material-UI
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Data Sources:</strong> NREL NSRDB, PVGIS
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Visualization:</strong> Chart.js, Plotly
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Key Features
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                • <strong>System Configuration:</strong> Easy-to-use interface for configuring PV system parameters
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                • <strong>Weather Data Integration:</strong> Automatic fetching from multiple weather data sources
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                • <strong>PV Simulation:</strong> Advanced simulation using PVLib ModelChain
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                • <strong>Results Visualization:</strong> Interactive charts and comprehensive analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • <strong>Data Export:</strong> Export results in multiple formats (CSV, JSON, PDF)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AboutPage;