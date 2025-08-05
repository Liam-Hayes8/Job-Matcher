#!/bin/bash
set -e

echo "🚀 Setting up Job Matcher for local development..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r local_requirements.txt
python -m spacy download en_core_web_sm

cd ..

# Setup frontend
echo "⚛️ Setting up React frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

cd ..

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p logs

echo "✅ Local setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   Option 1 (Docker): ./run-local.sh"
echo "   Option 2 (Manual): Follow the manual setup instructions in README"
echo ""
echo "📖 For more details, see the Local Development section in README.md"