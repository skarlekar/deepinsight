#!/bin/bash

# DeepInsight Frontend Startup Script

echo "🚀 Starting DeepInsight Frontend..."

# Check if we're in the correct directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found. Please run from project root."
    exit 1
fi

cd frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "🔧 Creating .env.local file..."
    cat > .env.local << EOF
# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
GENERATE_SOURCEMAP=false
EOF
fi

# Start the development server
echo "🎯 Starting React development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo ""

npm start