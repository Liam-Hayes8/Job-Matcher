#!/bin/bash
set -e

echo "🚀 Starting Job Matcher locally..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

echo "📦 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are starting up!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Database: postgresql://job_matcher_user:local_dev_password@localhost:5432/job_matcher"
    echo ""
    echo "📋 To view logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 To stop:"
    echo "   docker-compose down"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi