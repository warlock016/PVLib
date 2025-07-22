import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  LinearProgress,
} from '@mui/material';

const ConfigurationPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleTestConnection = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('/api/info');
      if (response.ok) {
        const data = await response.json();
        setMessage(`Backend connected successfully! API Version: ${data.data?.api_version || 'Unknown'}`);
      } else {
        setMessage('Backend connection failed. Please check if the server is running.');
      }
    } catch (error) {
      setMessage('Error connecting to backend. Please ensure the server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        System Configuration
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Backend Connection Test
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Test the connection to the backend API to ensure everything is working properly.
          </Typography>
          
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          
          {message && (
            <Alert 
              severity={message.includes('successfully') ? 'success' : 'error'} 
              sx={{ mb: 2 }}
            >
              {message}
            </Alert>
          )}
          
          <Button
            variant="contained"
            onClick={handleTestConnection}
            disabled={loading}
          >
            {loading ? 'Testing Connection...' : 'Test Backend Connection'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            PV System Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            System configuration interface coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ConfigurationPage;