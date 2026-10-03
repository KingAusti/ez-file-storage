#!/bin/bash

# Data Storage App Development Startup Script

echo "🚀 Starting Data Storage Application..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update the SECRET_KEY in backend/.env before running in production!"
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
uv sync

# Start backend in background
echo "🌐 Starting FastAPI server on http://localhost:8000..."
uv run python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo ""
echo "✅ Application started successfully!"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping server..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ Server stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
