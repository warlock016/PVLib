import React, { useState, useEffect } from 'react';
import { Box, Typography, Container, Card, CardContent, Button, Alert, CircularProgress } from '@mui/material';

const App: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'connected' | 'error'>('loading');
  const [backendInfo, setBackendInfo] = useState<any>(null);

  const testConnection = async () => {
    setStatus('loading');
    try {
      const response = await fetch('/api/info');
      if (response.ok) {
        const data = await response.json();
        setBackendInfo(data.data);
        setStatus('connected');
      } else {
        setStatus('error');
      }
    } catch (error) {
      setStatus('error');
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          PV Plant Modeling Website
        </Typography>
        
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Backend Connection Status
            </Typography>
            
            {status === 'loading' && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CircularProgress size={20} />
                <Typography>Testing connection...</Typography>
              </Box>
            )}
            
            {status === 'connected' && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Backend connected successfully!
                {backendInfo && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2">
                      API Version: {backendInfo.api_version}
                    </Typography>
                    <Typography variant="body2">
                      PVLib Version: {backendInfo.pvlib_version}
                    </Typography>
                    <Typography variant="body2">
                      System Status: {backendInfo.system_status}
                    </Typography>
                  </Box>
                )}
              </Alert>
            )}
            
            {status === 'error' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Unable to connect to backend. Please ensure the backend server is running on port 8000.
              </Alert>
            )}
            
            <Button variant="contained" onClick={testConnection} disabled={status === 'loading'}>
              Test Connection
            </Button>
          </CardContent>
        </Card>
        
        <Typography variant="body1" sx={{ mt: 3 }}>
          🎉 Frontend is working with TypeScript and Material-UI!
        </Typography>
      </Box>
    </Container>
  );
};

export default App;