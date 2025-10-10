#!/bin/bash

# Port Conflict Checker for Data Storage App
# This script checks if the default ports are available and suggests alternatives

set -e

echo "🔍 Data Storage App - Port Conflict Checker"
echo "==========================================="

# Function to check if port is available
check_port() {
    local port=$1
    local service=$2
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        # Windows
        if netstat -an | findstr ":$port " >/dev/null 2>&1; then
            echo "❌ Port $port ($service) is IN USE"
            return 1
        else
            echo "✅ Port $port ($service) is available"
            return 0
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -i :$port >/dev/null 2>&1; then
            echo "❌ Port $port ($service) is IN USE"
            return 1
        else
            echo "✅ Port $port ($service) is available"
            return 0
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an | grep -q ":$port "; then
            echo "❌ Port $port ($service) is IN USE"
            return 1
        else
            echo "✅ Port $port ($service) is available"
            return 0
        fi
    else
        echo "⚠️  Cannot check port $port ($service) - lsof/netstat not found"
        return 0
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while ! check_port $port "alternative" >/dev/null 2>&1; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            echo "❌ Could not find available port starting from $start_port"
            return 1
        fi
    done
    
    echo $port
}

# Check default ports
echo "Checking default ports..."
echo ""

FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Check ports and capture both output and return code
check_port $FRONTEND_PORT "Frontend"
FRONTEND_AVAILABLE=$?

check_port $BACKEND_PORT "Backend"
BACKEND_AVAILABLE=$?

check_port $POSTGRES_PORT "PostgreSQL"
POSTGRES_AVAILABLE=$?

check_port $REDIS_PORT "Redis"
REDIS_AVAILABLE=$?

echo ""
echo "📋 Port Status Summary:"
echo "======================="

if [ $FRONTEND_AVAILABLE -eq 0 ] && [ $BACKEND_AVAILABLE -eq 0 ] && [ $POSTGRES_AVAILABLE -eq 0 ] && [ $REDIS_AVAILABLE -eq 0 ]; then
    echo "🎉 All ports are available! You can run the setup script normally."
    echo ""
    echo "Run: ./setup.sh"
else
    echo "⚠️  Some ports are in use. The setup script will automatically find alternatives."
    echo ""
    echo "Alternative ports that will be used:"
    
    if [ $FRONTEND_AVAILABLE -ne 0 ]; then
        ALT_PORT=$(find_available_port $FRONTEND_PORT)
        echo "  Frontend:  $ALT_PORT (instead of $FRONTEND_PORT)"
    fi
    
    if [ $BACKEND_AVAILABLE -ne 0 ]; then
        ALT_PORT=$(find_available_port $BACKEND_PORT)
        echo "  Backend:   $ALT_PORT (instead of $BACKEND_PORT)"
    fi
    
    if [ $POSTGRES_AVAILABLE -ne 0 ]; then
        ALT_PORT=$(find_available_port $POSTGRES_PORT)
        echo "  PostgreSQL: $ALT_PORT (instead of $POSTGRES_PORT)"
    fi
    
    if [ $REDIS_AVAILABLE -ne 0 ]; then
        ALT_PORT=$(find_available_port $REDIS_PORT)
        echo "  Redis:     $ALT_PORT (instead of $REDIS_PORT)"
    fi
    
    echo ""
    echo "The setup script will handle this automatically."
    echo "Run: ./setup.sh"
fi

echo ""
echo "💡 To see what's using a specific port:"
echo "   lsof -i :PORT_NUMBER"
echo "   netstat -an | grep :PORT_NUMBER"
