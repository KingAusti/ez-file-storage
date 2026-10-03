#!/bin/bash

# Data Storage App Deployment Script
# This script handles both development and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Copy .env.example to .env if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning "Created .env file from .env.example"
        print_warning "Please update the SECRET_KEY in .env before running in production!"
    fi
    
    # Copy backend .env.example to .env if it doesn't exist
    if [ ! -f backend/.env ]; then
        cp backend/.env.example backend/.env
        print_warning "Created backend/.env file from backend/.env.example"
    fi
    
    print_success "Environment files are ready"
}

# Function to build and start services
start_services() {
    local profile=${1:-""}
    
    print_status "Building and starting services..."
    
    if [ "$profile" = "production" ]; then
        print_status "Starting in production mode with nginx..."
        docker-compose --profile production up --build -d
    else
        print_status "Starting in development mode..."
        docker-compose up --build -d
    fi
    
    print_success "Services started successfully"
}

# Function to show service status
show_status() {
    print_status "Service status:"
    docker-compose ps
    
    echo ""
    print_status "Application URLs:"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    
    if docker-compose ps | grep -q nginx; then
        echo "  Nginx:    http://localhost:80"
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        docker-compose logs -f "$service"
    else
        print_status "Showing logs for all services..."
        docker-compose logs -f
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Data Storage App Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [dev|prod]    Start services (default: dev)"
    echo "  stop               Stop all services"
    echo "  restart [dev|prod] Restart services"
    echo "  status             Show service status"
    echo "  logs [service]     Show logs (optionally for specific service)"
    echo "  cleanup            Stop services and clean up volumes/images"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start           # Start in development mode"
    echo "  $0 start prod      # Start in production mode with nginx"
    echo "  $0 logs backend    # Show backend logs"
    echo "  $0 cleanup         # Clean up everything"
}

# Main script logic
main() {
    case "${1:-start}" in
        "start")
            check_prerequisites
            setup_environment
            start_services "${2:-dev}"
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            check_prerequisites
            setup_environment
            start_services "${2:-dev}"
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
