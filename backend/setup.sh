#!/bin/bash

# Sketch It Backend Setup Script
# This script helps set up the backend development environment

set -e  # Exit on any error

echo "🚀 Setting up Sketch It Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python 3.8+ is installed
check_python() {
    echo "🔍 Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            print_status "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        return 1
    fi
}

# Create virtual environment
create_venv() {
    echo "🔧 Creating virtual environment..."
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    echo "🔌 Activating virtual environment..."
    
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_status "Virtual environment activated"
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        print_status "Virtual environment activated (Windows)"
    else
        print_error "Virtual environment activation script not found"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        print_status "Production dependencies installed"
    else
        print_error "requirements.txt not found"
        return 1
    fi
    
    if [ -f "requirements.dev.txt" ]; then
        pip install -r requirements.dev.txt
        print_status "Development dependencies installed"
    else
        print_warning "requirements.dev.txt not found, skipping development dependencies"
    fi
}

# Set up environment file
setup_env() {
    echo "⚙️ Setting up environment file..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Environment file created from .env.example"
            print_warning "Please update .env with your actual configuration values"
        else
            print_error ".env.example not found"
            return 1
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Create directories
create_directories() {
    echo "📁 Creating necessary directories..."
    
    directories=("logs" "uploads" "storage/original" "storage/sketches" "storage/thumbnails")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
}

# Run tests
run_tests() {
    echo "🧪 Running tests..."
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short
        print_status "Tests completed"
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Start the server
start_server() {
    echo "🌟 Starting development server..."
    
    if command -v uvicorn &> /dev/null; then
        print_status "Starting server at http://localhost:8000"
        print_status "API docs available at http://localhost:8000/docs"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    else
        print_error "uvicorn not found. Please install dependencies first."
        return 1
    fi
}

# Main setup function
main() {
    echo "================================================"
    echo "         Sketch It Backend Setup"
    echo "================================================"
    
    # Check if we're in the right directory
    if [ ! -f "app/main.py" ]; then
        print_error "Please run this script from the backend directory"
        exit 1
    fi
    
    # Run setup steps
    check_python || exit 1
    create_venv || exit 1
    activate_venv || exit 1
    install_dependencies || exit 1
    setup_env || exit 1
    create_directories || exit 1
    
    echo ""
    echo "================================================"
    print_status "Setup completed successfully!"
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "1. Update .env with your Supabase credentials"
    echo "2. Run 'python scripts/init_db.py' to initialize the database"
    echo "3. Run './setup.sh --start' to start the development server"
    echo ""
    
    # Check if user wants to start the server
    if [ "$1" == "--start" ]; then
        echo "🚀 Starting server..."
        start_server
    elif [ "$1" == "--test" ]; then
        echo "🧪 Running tests..."
        run_tests
    else
        echo "Run './setup.sh --start' to start the server"
        echo "Run './setup.sh --test' to run tests"
    fi
}

# Run main function with all arguments
main "$@"