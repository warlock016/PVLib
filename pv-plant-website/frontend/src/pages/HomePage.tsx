import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Container,
  Paper,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import {
  SolarPower,
  Assessment,
  TrendingUp,
  CloudDownload,
} from '@mui/icons-material';

const HomePage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      {/* Hero Section */}
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          mb: 6,
        }}
      >
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          sx={{
            fontWeight: 600,
            color: 'primary.main',
            mb: 3,
          }}
        >
          PV Plant Modeling Website
        </Typography>
        <Typography
          variant="h5"
          color="text.secondary"
          paragraph
          sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
        >
          Simulate photovoltaic energy systems using PVLib with real weather data
          from NREL and PVGIS sources.
        </Typography>
        <Button
          component={RouterLink}
          to="/configure"
          variant="contained"
          size="large"
          sx={{
            py: 2,
            px: 4,
            fontSize: '1.1rem',
            borderRadius: 2,
          }}
        >
          Get Started
        </Button>
      </Box>

      {/* Features Section */}
      <Grid container spacing={4} sx={{ mb: 8 }}>
        <Grid item xs={12} md={6} lg={3}>
          <Card
            sx={{
              height: '100%',
              textAlign: 'center',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <SolarPower
                sx={{
                  fontSize: 48,
                  color: 'primary.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom>
                System Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Configure PV system parameters including modules, inverters,
                and mounting systems with our intuitive interface.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card
            sx={{
              height: '100%',
              textAlign: 'center',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <CloudDownload
                sx={{
                  fontSize: 48,
                  color: 'primary.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom>
                Weather Data
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Access high-quality weather data from NREL NSRDB and PVGIS
                with automatic source selection and caching.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card
            sx={{
              height: '100%',
              textAlign: 'center',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Assessment
                sx={{
                  fontSize: 48,
                  color: 'primary.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom>
                PV Simulation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Run accurate PV simulations using PVLib ModelChain with
                industry-standard models and calculations.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card
            sx={{
              height: '100%',
              textAlign: 'center',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <TrendingUp
                sx={{
                  fontSize: 48,
                  color: 'primary.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom>
                Results Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Visualize and analyze simulation results with interactive
                charts and detailed performance metrics.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Stats Section */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          bgcolor: 'grey.50',
          borderRadius: 2,
          mb: 8,
        }}
      >
        <Typography
          variant="h4"
          component="h2"
          gutterBottom
          sx={{ textAlign: 'center', mb: 4 }}
        >
          Key Features
        </Typography>
        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" gutterBottom>
                1500+
              </Typography>
              <Typography variant="h6" color="text.secondary">
                PV Modules Supported
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" gutterBottom>
                800+
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Inverters Available
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary" gutterBottom>
                Global
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Weather Data Coverage
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Getting Started Section */}
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Ready to Start?
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          paragraph
          sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
        >
          Configure your PV system, run simulations, and analyze results
          in just a few simple steps.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            component={RouterLink}
            to="/configure"
            variant="contained"
            size="large"
          >
            Configure System
          </Button>
          <Button
            component={RouterLink}
            to="/about"
            variant="outlined"
            size="large"
          >
            Learn More
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default HomePage;