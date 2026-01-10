#!/bin/bash
# Homelab HUD Setup Script
# Sets up the environment for Mac/Linux

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        OS="unknown"
    fi
    print_info "Detected OS: $OS"
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python 3 not found. Please install Python 3.9 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Found Python: $PYTHON_VERSION"
    
    # Check version (need 3.9+)
    VERSION_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    VERSION_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$VERSION_MAJOR" -lt 3 ] || ([ "$VERSION_MAJOR" -eq 3 ] && [ "$VERSION_MINOR" -lt 9 ]); then
        print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python version OK"
}

# Check for pip
check_pip() {
    print_info "Checking pip installation..."
    
    if ! command_exists pip3 && ! command_exists pip; then
        print_error "pip not found. Installing pip..."
        $PYTHON_CMD -m ensurepip --upgrade
    fi
    
    if command_exists pip3; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    print_success "Found pip"
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
        print_info "To recreate, delete 'venv' directory and run this script again."
    else
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    print_info "Activating virtual environment..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Upgrade pip
upgrade_pip() {
    print_info "Upgrading pip..."
    $PIP_CMD install --upgrade pip setuptools wheel
    print_success "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies from requirements.txt..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    $PIP_CMD install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p data/fonts
    mkdir -p data/preview
    mkdir -p tests/fixtures
    
    print_success "Directories created"
}

# Install system dependencies (if needed)
install_system_deps() {
    print_info "Checking for system dependencies..."
    
    # Check for pygame dependencies on Linux
    if [ "$OS" == "linux" ]; then
        if ! command_exists apt-get 2>/dev/null && ! command_exists yum 2>/dev/null && ! command_exists dnf 2>/dev/null; then
            print_warning "Could not detect package manager. Skipping system dependency checks."
            return
        fi
        
        # Check for SDL dependencies for pygame
        if ! pkg-config --exists sdl2 2>/dev/null; then
            print_warning "SDL2 not found. pygame may not work properly."
            print_info "On Ubuntu/Debian, install with: sudo apt-get install libsdl2-dev"
            print_info "On Fedora/RHEL, install with: sudo dnf install SDL2-devel"
        fi
    fi
    
    # Check for fontconfig on Linux (for font loading)
    if [ "$OS" == "linux" ]; then
        if ! command_exists fc-list 2>/dev/null; then
            print_warning "fontconfig not found. Font loading may be limited."
            print_info "On Ubuntu/Debian, install with: sudo apt-get install fontconfig"
        fi
    fi
}

# Set up permissions
set_permissions() {
    print_info "Setting up permissions..."
    
    # Make app.py executable
    chmod +x app.py
    
    # Make this script executable (if it isn't already)
    chmod +x setup.sh
    
    print_success "Permissions set"
}

# Create .env file if it doesn't exist
create_env_file() {
    print_info "Setting up environment file..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Homelab HUD Environment Variables
# Set HUD_ENV=dev for development mode (auto-detected on Mac)
# Set HUD_ENV=prod for production mode (auto-detected on Linux/Raspberry Pi)
# HUD_ENV=dev

# Set HUD_USE_MOCKS=true to use mock data instead of real APIs
# HUD_USE_MOCKS=false
EOF
        print_success ".env file created"
    else
        print_info ".env file already exists, skipping"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Check if we can import key modules
    if $PYTHON_CMD -c "import flask, PIL, requests, psutil, pygame" 2>/dev/null; then
        print_success "All required Python packages are installed"
    else
        print_error "Some Python packages failed to import"
        print_info "Try running: $PIP_CMD install -r requirements.txt"
        exit 1
    fi
    
    # Check if config.py can be imported
    if $PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); import config; print('Config OK')" 2>/dev/null; then
        print_success "Configuration module loads correctly"
    else
        print_error "Configuration module failed to load"
        exit 1
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    print_success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run in development mode (Mac):"
    echo "   python app.py --dev-mode --preview"
    echo ""
    echo "3. Access the web UI at:"
    echo "   http://localhost:8181"
    echo ""
    echo "4. Configure your APIs via the web UI"
    echo ""
    echo "5. For production on Raspberry Pi:"
    echo "   python app.py"
    echo ""
    echo "Note: On Raspberry Pi, make sure to:"
    echo "  - Enable composite video output in /boot/config.txt"
    echo "  - Set framebuffer resolution if needed"
    echo ""
}

# Main setup function
main() {
    echo ""
    echo "=========================================="
    echo "  Homelab HUD Setup Script"
    echo "=========================================="
    echo ""
    
    detect_os
    check_python
    check_pip
    create_venv
    activate_venv
    upgrade_pip
    install_dependencies
    create_directories
    install_system_deps
    set_permissions
    create_env_file
    verify_installation
    print_next_steps
}

# Run main function
main

