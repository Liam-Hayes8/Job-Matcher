#!/bin/bash
set -e

echo "🚀 Starting Job Matcher locally..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

echo "🧹 Cleaning up any previous containers..."
docker-compose -f docker-compose.simple.yml down -v 2>/dev/null || true

echo "📦 Building and starting services..."
docker-compose -f docker-compose.simple.yml up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if services are running
if docker-compose -f docker-compose.simple.yml ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   🎯 Frontend: http://localhost:3000"
    echo "   🚀 Backend API: http://localhost:8000"
    echo "   📚 API Docs: http://localhost:8000/docs"
    echo "   🏥 Health Check: http://localhost:8000/health"
    echo ""
    echo "📋 Useful Commands:"
    echo "   View logs: docker-compose -f docker-compose.simple.yml logs -f"
    echo "   Stop app: docker-compose -f docker-compose.simple.yml down"
    echo ""
    echo "🎉 Ready to test! Open http://localhost:3000 in your browser"
else
    echo "❌ Some services failed to start. Check logs with:"
    echo "   docker-compose -f docker-compose.simple.yml logs"
    exit 1
fi