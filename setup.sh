#!/bin/bash

# Data Storage App - Quick Setup Script
# This script sets up the application with minimal user interaction

set -e

echo "🚀 Data Storage App - Quick Setup"
echo "=================================="

# Check if Docker is installed
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose (both old and new syntax)
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if openssl is available
if ! command -v openssl >/dev/null 2>&1; then
    echo "❌ OpenSSL is not installed. Please install OpenSSL first."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    rm -f docker-compose.override.yml
}
trap cleanup EXIT

# Function to check if port is available
check_port() {
    local port=$1
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        # Windows
        if netstat -an | findstr ":$port " >/dev/null 2>&1; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    elif command -v lsof >/dev/null 2>&1; then
        # macOS/Linux with lsof
        if lsof -i :$port >/dev/null 2>&1; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    elif command -v netstat >/dev/null 2>&1; then
        # Fallback to netstat
        if netstat -an | grep -q ":$port "; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    else
        echo "⚠️  Warning: Cannot check port availability (lsof/netstat not found)"
        return 0
    fi
}

# Better IP detection
get_local_ip() {
    if command -v ip >/dev/null 2>&1; then
        # Linux with ip command
        ip route get 1.1.1.1 | grep -oP 'src \K\S+' 2>/dev/null || echo ""
    elif command -v ifconfig >/dev/null 2>&1; then
        # macOS/Linux with ifconfig
        ifconfig | grep -E 'inet [0-9]' | grep -v '127.0.0.1' | awk '{print $2}' | head -1
    else
        echo ""
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while ! check_port $port; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            echo "❌ Could not find available port starting from $start_port"
            exit 1
        fi
    done
    
    echo $port
}

# Check for port conflicts and find alternatives
echo "🔍 Checking for port conflicts..."

BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Check and find alternative ports if needed
if ! check_port $BACKEND_PORT; then
    echo "⚠️  Port $BACKEND_PORT is in use, finding alternative..."
    BACKEND_PORT=$(find_available_port $BACKEND_PORT)
    echo "✅ Using port $BACKEND_PORT for backend"
fi

if ! check_port $POSTGRES_PORT; then
    echo "⚠️  Port $POSTGRES_PORT is in use, finding alternative..."
    POSTGRES_PORT=$(find_available_port $POSTGRES_PORT)
    echo "✅ Using port $POSTGRES_PORT for PostgreSQL"
fi

if ! check_port $REDIS_PORT; then
    echo "⚠️  Port $REDIS_PORT is in use, finding alternative..."
    REDIS_PORT=$(find_available_port $REDIS_PORT)
    echo "✅ Using port $REDIS_PORT for Redis"
fi

echo "📋 Port configuration:"
echo "   Backend:   $BACKEND_PORT"
echo "   PostgreSQL: $POSTGRES_PORT"
echo "   Redis:     $REDIS_PORT"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    cat > .env << EOF
# Security
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Database
DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@postgres:5432/data_storage
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:$POSTGRES_PASSWORD@postgres:5432/data_storage

# Redis
REDIS_URL=redis://redis:6379

# Email Configuration (optional - leave empty for development)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_SERVER=

# Sentry (optional - leave empty for development)
SENTRY_DSN=

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
    echo "✅ Environment configuration created"
else
    echo "✅ Environment configuration already exists"
fi

# Create temporary docker-compose override file with custom ports
echo "📝 Creating port configuration..."
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  backend:
    ports:
      - "0.0.0.0:$BACKEND_PORT:8000"

  postgres:
    ports:
      - "0.0.0.0:$POSTGRES_PORT:5432"

  redis:
    ports:
      - "0.0.0.0:$REDIS_PORT:6379"
EOF

# Start the application
echo "🐳 Starting the application..."
echo "   This may take a few minutes on first run..."

$DOCKER_COMPOSE up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    # Get local IP address
    LOCAL_IP=$(get_local_ip)
    
    echo ""
    echo "🎉 Setup Complete!"
    echo "================"
    echo ""
    echo "Your application is now running and accessible:"
    echo ""
    echo "📍 Local Access:"
    echo "  🔧 Backend API: http://localhost:$BACKEND_PORT"
    echo "  📚 API Docs:    http://localhost:$BACKEND_PORT/docs"
    echo "  ❤️  Health:      http://localhost:$BACKEND_PORT/health"
    echo ""
    if [ ! -z "$LOCAL_IP" ]; then
        echo "🌍 Network Access (same WiFi):"
        echo "  🔧 Backend API: http://$LOCAL_IP:$BACKEND_PORT"
        echo "  📚 API Docs:    http://$LOCAL_IP:$BACKEND_PORT/docs"
        echo ""
    fi
    echo "Next steps:"
    echo "  1. Open http://localhost:$BACKEND_PORT/docs to explore the API"
    echo "  2. Register a new account via the API"
    echo "  3. Start creating data entries!"
    echo ""
    echo "Useful commands:"
    echo "  📊 View logs:    $DOCKER_COMPOSE logs -f"
    echo "  🛑 Stop app:     $DOCKER_COMPOSE down"
    echo "  🔄 Restart:      $DOCKER_COMPOSE restart"
    echo "  🧹 Clean up:     $DOCKER_COMPOSE down -v"
    echo ""
    echo "🔒 Security Note:"
    echo "  The app is now accessible from your local network."
    echo "  For internet access, consider using Cloudflare Tunnel"
    echo "  or deploying to a cloud server for better security."
    echo ""
    echo "📝 Port Information:"
    echo "  Backend:   $BACKEND_PORT (was 8000)"
    echo "  PostgreSQL: $POSTGRES_PORT (was 5432)"
    echo "  Redis:     $REDIS_PORT (was 6379)"
    echo ""
else
    echo "❌ Failed to start services. Check the logs:"
    echo "   $DOCKER_COMPOSE logs"
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "   - Make sure no other applications are using the required ports"
    echo "   - Try running: $DOCKER_COMPOSE down -v && $DOCKER_COMPOSE up --build"
    echo "   - Check if Docker has enough resources allocated"
    echo "   - Ensure Docker Desktop is running (if on macOS/Windows)"
    exit 1
fi