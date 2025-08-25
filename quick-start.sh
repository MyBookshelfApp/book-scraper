#!/bin/bash

# Book Scraper Quick Start Script
set -e

echo "🚀 Book Scraper Quick Start"
echo "============================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use. Please stop the service using that port first."
        return 1
    fi
    return 0
}

echo "🔍 Checking port availability..."
check_port 8000 || exit 1
check_port 9090 || exit 1
check_port 6379 || exit 1

echo "✅ Ports are available"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Build and start core services
echo "🐳 Starting core services..."
docker-compose -f docker-compose.core.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Book Scraper service is healthy"
else
    echo "❌ Book Scraper service is not responding"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.core.yml logs book-scraper
    exit 1
fi

# Check Redis
echo "🔴 Checking Redis..."
if docker exec book-scraper-redis-1 redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding"
    exit 1
fi

echo ""
echo "🎉 Book Scraper is ready!"
echo ""
echo "📊 Service URLs:"
echo "   API:        http://localhost:8000"
echo "   Metrics:    http://localhost:8000/metrics"
echo "   Health:     http://localhost:8000/health"
echo "   Docs:       http://localhost:8000/docs"
echo ""
echo "🔴 Redis:      localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "   View logs:  docker-compose -f docker-compose.core.yml logs -f book-scraper"
echo "   Stop:       docker-compose -f docker-compose.core.yml down"
echo "   Restart:    docker-compose -f docker-compose.core.yml restart book-scraper"
echo ""
echo "🧪 Test the service:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/api/v1/sources"
echo ""
echo "📚 For monitoring, run:"
echo "   docker-compose --profile monitoring up --build" 