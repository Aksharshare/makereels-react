#!/bin/bash

# MakeReels Docker Deployment Script
echo "🚀 Starting MakeReels Docker Deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p automationtool/input
mkdir -p automationtool/output
mkdir -p automationtool/logs
mkdir -p ssl-certs

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 automationtool/input
chmod 755 automationtool/output
chmod 755 automationtool/logs

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Show logs
echo "📋 Service logs:"
docker-compose logs --tail=50

echo "✅ Deployment complete!"
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend: http://localhost:8000"
echo "📊 Health check: http://localhost/health"
