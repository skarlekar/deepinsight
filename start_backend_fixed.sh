#!/bin/bash

# DeepInsight Backend Startup Script (Fixed)

echo "🚀 Starting DeepInsight Backend..."

# Check if we're in the correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found. Please run from project root."
    exit 1
fi

cd backend

# Install email-validator directly with pip (works with any Python environment)
echo "🔧 Installing required packages..."
pip install email-validator pydantic[email] fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart anthropic requests aiofiles python-dateutil PyMuPDF python-docx python-magic

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

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000