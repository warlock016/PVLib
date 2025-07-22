import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const SimulationPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        PV Simulation
      </Typography>
      
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Simulation Interface
          </Typography>
          <Typography variant="body2" color="text.secondary">
            PV simulation interface coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SimulationPage;