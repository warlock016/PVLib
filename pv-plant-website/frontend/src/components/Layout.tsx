import React from 'react';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { styled } from '@mui/material/styles';

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
}));

const NavLink = styled(RouterLink)(({ theme }) => ({
  color: 'white',
  textDecoration: 'none',
  marginLeft: theme.spacing(3),
  fontSize: '1rem',
  fontWeight: 500,
  '&:hover': {
    textDecoration: 'underline',
  },
}));

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <StyledAppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            PV Plant Modeling
          </Typography>
          <nav>
            <NavLink to="/">Home</NavLink>
            <NavLink to="/configure">Configure</NavLink>
            <NavLink to="/simulate">Simulate</NavLink>
            <NavLink to="/results">Results</NavLink>
            <NavLink to="/about">About</NavLink>
          </nav>
        </Toolbar>
      </StyledAppBar>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {children}
      </Container>
    </Box>
  );
};

export default Layout;