#!/bin/bash

# DeepInsight Backend Startup Script

echo "🚀 Starting DeepInsight Backend..."

# Check if we're in the correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found. Please run from project root."
    exit 1
fi

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/documents data/exports

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using example configuration."
    echo "   Please copy .env.example to .env and configure your API keys."
fi

# Start the server
echo "🎯 Starting FastAPI server..."
echo "   Backend will be available at: http://localhost:8000"
echo "   API docs will be available at: http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000