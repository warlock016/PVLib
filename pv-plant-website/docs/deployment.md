# Deployment Guide

## Overview

This guide covers deployment options for the PV Plant Modeling Website, from local development to production deployment on cloud platforms.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: 10GB available space
- **Network**: Internet connection for weather data APIs

### Required Accounts
- **NREL API Key**: Free registration at https://developer.nrel.gov/signup/
- **Cloud Provider**: AWS, GCP, or Azure (for production deployment)
- **Domain Name**: For production deployment (optional)

## Local Development Setup

### 1. Environment Setup

#### Clone and Set Up Project Structure
```bash
cd /Users/mode/Documents/Code/PVLib/pv-plant-website
```

#### Create Virtual Environment
```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

#### Install Dependencies
```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Environment Configuration

#### Create Environment File
```bash
# Create .env file in project root
cat > .env << EOF
# NREL API Configuration
NREL_API_KEY=your_nrel_api_key_here
NREL_USER_EMAIL=your_email@domain.com
NREL_USER_ID=your_user_id

# Application Configuration
ENV=development
DEBUG=true
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///./pv_plant_db.sqlite

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=detailed
EOF
```

#### Set Environment Variables
```bash
# Load environment variables
source .env

# Or export manually
export NREL_API_KEY="your_api_key_here"
export NREL_USER_EMAIL="your_email@domain.com"
```

### 3. Database Setup

#### Initialize SQLite Database
```bash
cd backend
python -c "from app.database import create_tables; create_tables()"
```

#### Verify Database
```bash
# Check database file exists
ls -la *.sqlite

# Check table structure
sqlite3 pv_plant_db.sqlite ".schema"
```

### 4. Run Development Servers

#### Start Backend Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend Server
```bash
cd frontend
npm start
```

#### Verify Installation
```bash
# Test backend API
curl http://localhost:8000/api/info

# Test frontend
open http://localhost:3000
```

## Production Deployment

### 1. Server Setup

#### System Requirements
- **CPU**: 2+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: Static IP address
- **OS**: Ubuntu 20.04 LTS or similar

#### Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash pvuser
sudo usermod -aG sudo pvuser
```

### 2. Application Deployment

#### Deploy Application Code
```bash
# Switch to application user
sudo su - pvuser

# Clone application (or copy files)
git clone <repository-url> /home/pvuser/pv-plant-website
cd /home/pvuser/pv-plant-website

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Build frontend
cd frontend
npm install
npm run build
```

#### Configure Environment
```bash
# Create production environment file
cat > .env << EOF
# NREL API Configuration
NREL_API_KEY=your_production_api_key
NREL_USER_EMAIL=your_production_email@domain.com

# Application Configuration
ENV=production
DEBUG=false
SECRET_KEY=your_secure_secret_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/pvplant

# CORS Configuration
CORS_ORIGINS=https://your-domain.com

# Logging Configuration
LOG_LEVEL=WARNING
LOG_FORMAT=json
EOF
```

### 3. Database Setup (PostgreSQL)

#### Install PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE pvplant;
CREATE USER pvuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE pvplant TO pvuser;
\q
```

#### Run Database Migrations
```bash
cd /home/pvuser/pv-plant-website/backend
python -c "from app.database import create_tables; create_tables()"
```

### 4. Process Management (Systemd)

#### Create Backend Service
```bash
sudo tee /etc/systemd/system/pvplant-backend.service > /dev/null << EOF
[Unit]
Description=PV Plant Backend API
After=network.target

[Service]
Type=simple
User=pvuser
Group=pvuser
WorkingDirectory=/home/pvuser/pv-plant-website/backend
Environment=PATH=/home/pvuser/pv-plant-website/venv/bin
EnvironmentFile=/home/pvuser/pv-plant-website/.env
ExecStart=/home/pvuser/pv-plant-website/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Start Services
```bash
# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl start pvplant-backend
sudo systemctl enable pvplant-backend

# Check service status
sudo systemctl status pvplant-backend
```

### 5. Web Server Configuration (Nginx)

#### Install and Configure Nginx
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/pvplant > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend static files
    location / {
        root /home/pvuser/pv-plant-website/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support (future enhancement)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Static file caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pvplant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 6. SSL Certificate (Let's Encrypt)

#### Obtain SSL Certificate
```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

#### Configure Auto-renewal
```bash
# Add renewal cron job
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Monitoring and Logging

#### Set Up Log Rotation
```bash
sudo tee /etc/logrotate.d/pvplant > /dev/null << EOF
/home/pvuser/pv-plant-website/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 pvuser pvuser
    postrotate
        sudo systemctl reload pvplant-backend
    endscript
}
EOF
```

#### Configure Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Set up basic monitoring script
cat > /home/pvuser/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ===" > /tmp/system_status.log
date >> /tmp/system_status.log
echo "CPU Usage:" >> /tmp/system_status.log
top -bn1 | grep "Cpu(s)" >> /tmp/system_status.log
echo "Memory Usage:" >> /tmp/system_status.log
free -h >> /tmp/system_status.log
echo "Disk Usage:" >> /tmp/system_status.log
df -h >> /tmp/system_status.log
echo "Service Status:" >> /tmp/system_status.log
systemctl status pvplant-backend --no-pager >> /tmp/system_status.log
EOF

chmod +x /home/pvuser/monitor.sh
```

## Docker Deployment

### 1. Docker Configuration

#### Create Dockerfile for Backend
```dockerfile
# Create backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Create Dockerfile for Frontend
```dockerfile
# Create frontend/Dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Create Docker Compose Configuration
```yaml
# Create docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NREL_API_KEY=${NREL_API_KEY}
      - NREL_USER_EMAIL=${NREL_USER_EMAIL}
      - DATABASE_URL=postgresql://pvuser:password@db:5432/pvplant
    depends_on:
      - db
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=pvplant
      - POSTGRES_USER=pvuser
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Docker Deployment

#### Build and Run
```bash
# Build and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

#### Production Docker Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### 1. AWS Deployment

#### EC2 Instance Setup
```bash
# Launch EC2 instance (Ubuntu 20.04)
# Configure security groups (ports 80, 443, 22)
# Associate Elastic IP

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Follow server setup steps from above
```

#### Load Balancer Configuration
```bash
# Create Application Load Balancer
# Configure target groups
# Set up health checks
# Configure SSL termination
```

### 2. Google Cloud Platform

#### Cloud Run Deployment
```bash
# Build and push container
gcloud builds submit --tag gcr.io/your-project/pvplant-backend ./backend
gcloud builds submit --tag gcr.io/your-project/pvplant-frontend ./frontend

# Deploy to Cloud Run
gcloud run deploy pvplant-backend \
  --image gcr.io/your-project/pvplant-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy pvplant-frontend \
  --image gcr.io/your-project/pvplant-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Azure Deployment

#### Container Instances
```bash
# Create resource group
az group create --name pvplant-rg --location eastus

# Deploy container
az container create \
  --resource-group pvplant-rg \
  --name pvplant-backend \
  --image your-registry/pvplant-backend:latest \
  --ports 8000 \
  --environment-variables NREL_API_KEY=your-key
```

## Maintenance and Updates

### 1. Application Updates

#### Update Process
```bash
# Pull latest code
git pull origin main

# Update backend
cd backend
pip install -r requirements.txt
sudo systemctl restart pvplant-backend

# Update frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### 2. Database Maintenance

#### Backup Database
```bash
# PostgreSQL backup
pg_dump -U pvuser -h localhost pvplant > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite backup
cp pv_plant_db.sqlite backup_$(date +%Y%m%d_%H%M%S).sqlite
```

#### Database Cleanup
```bash
# Clean old simulation results
psql -U pvuser -d pvplant -c "DELETE FROM simulations WHERE created_at < NOW() - INTERVAL '30 days';"
```

### 3. System Monitoring

#### Health Checks
```bash
# Check system health
curl -f http://localhost:8000/api/info || echo "Backend down"
curl -f http://localhost:3000/ || echo "Frontend down"

# Check disk space
df -h | grep -E "(/$|/var)" | awk '{print $5 " " $6}'

# Check memory usage
free -h | grep Mem | awk '{print $3 "/" $2}'
```

#### Log Monitoring
```bash
# Monitor application logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
journalctl -u pvplant-backend -f
```

## Security Considerations

### 1. API Security
- Use HTTPS in production
- Implement rate limiting
- Validate all inputs
- Use secure headers
- Regular security updates

### 2. Database Security
- Use strong passwords
- Limit database access
- Regular backups
- Encrypt sensitive data
- Monitor access logs

### 3. Server Security
- Keep OS updated
- Use firewall rules
- Disable unnecessary services
- Regular security audits
- Monitor system logs

## Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check logs
journalctl -u pvplant-backend -n 50

# Check Python environment
source venv/bin/activate
python -c "import app.main"

# Check dependencies
pip check
```

#### Frontend Build Failures
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version
npm --version
```

#### Database Connection Issues
```bash
# Test database connection
psql -U pvuser -h localhost -d pvplant

# Check database status
sudo systemctl status postgresql
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect your-domain.com:443
```

### Performance Optimization

#### Backend Performance
- Use async/await for I/O operations
- Implement caching for weather data
- Optimize database queries
- Use connection pooling

#### Frontend Performance
- Minimize bundle size
- Use code splitting
- Implement lazy loading
- Optimize images

#### Database Performance
- Add database indexes
- Regular VACUUM operations
- Monitor query performance
- Use connection pooling

This deployment guide provides comprehensive instructions for deploying the PV Plant Modeling Website in various environments, from local development to production cloud deployment.