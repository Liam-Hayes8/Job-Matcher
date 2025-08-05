#!/bin/bash

echo "🚀 Starting Job Matcher - Quick Frontend"

# Start just the frontend container with a timeout
timeout 300 docker-compose -f docker-compose.simple.yml up --build frontend &

# Wait a bit and check status
sleep 30

echo ""
echo "🌟 Job Matcher is starting up!"
echo ""
echo "📱 Available URLs:"
echo "   🎯 Backend API: http://localhost:8000"
echo "   📚 API Documentation: http://localhost:8000/docs"
echo "   🏥 Health Check: http://localhost:8000/health"
echo ""
echo "⏳ Frontend is building... This may take a few minutes."
echo "   Once ready, it will be available at: http://localhost:3000"
echo ""
echo "💡 You can test the backend API right now!"
echo "   Try: curl http://localhost:8000/health"
echo ""
echo "🔍 To check progress: docker-compose -f docker-compose.simple.yml logs -f frontend"