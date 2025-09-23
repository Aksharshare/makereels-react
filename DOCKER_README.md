# 🐳 MakeReels Docker Deployment Guide

This guide explains how to deploy the MakeReels application using Docker containers.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose installed
- At least 2GB of available RAM
- At least 5GB of available disk space

## 🚀 Quick Start

### Local Development
```bash
# Start local development environment
./deploy-local.sh
```

### Production Deployment
```bash
# Start production environment
./deploy.sh
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   (React +      │◄──►│   (Python +     │
│   Nginx)        │    │   Flask)        │
│   Port: 80/443  │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
makereels/
├── automationtool/          # Python Backend
│   ├── Dockerfile          # Backend container
│   ├── app.py              # Flask application
│   ├── config/             # Configuration files
│   ├── input/              # Video input directory
│   └── output/              # Processed videos
├── frontend/               # React Frontend
│   ├── Dockerfile          # Production frontend
│   ├── Dockerfile.local    # Local development
│   ├── nginx.conf          # Production nginx config
│   └── nginx-local.conf    # Local nginx config
├── docker-compose.yml      # Production orchestration
├── docker-compose.local.yml # Local orchestration
├── deploy.sh               # Production deployment script
└── deploy-local.sh         # Local deployment script
```

## 🔧 Configuration

### Environment Variables

Create a `docker.env` file with your configuration:

```bash
# Backend Configuration
BACKEND_URL=http://backend:8000
PORT=8000

# Frontend Configuration
REACT_APP_API_URL=http://backend:8000

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Domain Configuration
DOMAIN=makereels.live
SSL_EMAIL=your-email@example.com
```

### Path Configuration

The application uses these Docker paths:
- **Input**: `/app/input` (mapped to `./automationtool/input`)
- **Output**: `/app/output` (mapped to `./automationtool/output`)
- **Config**: `/app/config` (mapped to `./automationtool/config`)

## 🚀 Deployment Commands

### Local Development
```bash
# Start local environment
docker-compose -f docker-compose.local.yml up --build -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop services
docker-compose -f docker-compose.local.yml down
```

### Production Deployment
```bash
# Start production environment
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔍 Health Checks

- **Frontend**: http://localhost
- **Backend**: http://localhost:8000/health
- **API**: http://localhost/api/health

## 📊 Monitoring

### View Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Resource Usage
```bash
docker stats
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :80
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Permission Issues**
   ```bash
   # Fix directory permissions
   chmod 755 automationtool/input
   chmod 755 automationtool/output
   ```

3. **Service Not Starting**
   ```bash
   # Check logs
   docker-compose logs backend
   docker-compose logs frontend
   ```

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Remove all images
docker system prune -a

# Start fresh
./deploy.sh
```

## 🌐 Production Deployment on Hostinger

1. **Upload your code** to Hostinger VPS
2. **Install Docker** on the VPS
3. **Set up SSL certificates** in `ssl-certs/` directory
4. **Update environment variables** in `docker.env`
5. **Run deployment script**:
   ```bash
   ./deploy.sh
   ```

## 📝 Notes

- The application automatically creates necessary directories
- Health checks ensure services are running properly
- All data is persisted in mounted volumes
- SSL certificates are mounted read-only for security

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all environment variables are set
3. Ensure all required directories exist
4. Check Docker and Docker Compose are properly installed
