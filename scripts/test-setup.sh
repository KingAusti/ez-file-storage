#!/bin/bash

# Test script for setup.sh functionality
# This script tests the port detection and Docker Compose detection

set -e

echo "🧪 Testing Setup Script Components"
echo "=================================="

# Test 1: Check if setup script exists and is executable
echo "Test 1: Checking setup script..."
if [ -f "./setup.sh" ] && [ -x "./setup.sh" ]; then
    echo "✅ Setup script exists and is executable"
else
    echo "❌ Setup script missing or not executable"
    exit 1
fi

# Test 2: Check Docker detection
echo ""
echo "Test 2: Checking Docker detection..."
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker is installed"
else
    echo "❌ Docker is not installed"
fi

# Test 3: Check Docker Compose detection
echo ""
echo "Test 3: Checking Docker Compose detection..."
if command -v docker-compose >/dev/null 2>&1; then
    echo "✅ docker-compose is available"
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    echo "✅ docker compose is available"
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose is not available"
fi

# Test 4: Check OpenSSL
echo ""
echo "Test 4: Checking OpenSSL..."
if command -v openssl >/dev/null 2>&1; then
    echo "✅ OpenSSL is installed"
else
    echo "❌ OpenSSL is not installed"
fi

# Test 5: Test port checking functions
echo ""
echo "Test 5: Testing port checking functions..."

# Source the setup script to get the functions
source ./setup.sh 2>/dev/null || true

# Test port checking
if check_port 8000; then
    echo "✅ Port 8000 is available"
else
    echo "❌ Port 8000 is in use"
fi

# Test 6: Test IP detection
echo ""
echo "Test 6: Testing IP detection..."
if command -v get_local_ip >/dev/null 2>&1; then
    LOCAL_IP=$(get_local_ip)
    if [ ! -z "$LOCAL_IP" ]; then
        echo "✅ Local IP detected: $LOCAL_IP"
    else
        echo "⚠️  Could not detect local IP"
    fi
else
    echo "⚠️  get_local_ip function not available"
fi

echo ""
echo "🎉 Setup script validation complete!"
echo "=================================="
echo ""
echo "If all tests passed, you can run:"
echo "  ./setup.sh"
echo ""
echo "Or check ports first:"
echo "  ./scripts/check-ports.sh"
