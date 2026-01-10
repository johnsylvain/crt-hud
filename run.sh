#!/bin/bash
# Homelab HUD Run Script
# Convenient script to run the application with virtual environment

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

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        OS="unknown"
    fi
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Please run ./setup.sh first to set up the environment"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Check if app.py exists
check_app() {
    if [ ! -f "app.py" ]; then
        print_error "app.py not found!"
        exit 1
    fi
}

# Detect mode based on OS if not specified
detect_mode() {
    detect_os
    if [ -z "$MODE" ]; then
        if [ "$OS" == "macos" ]; then
            MODE="dev"
        else
            MODE="prod"
        fi
    fi
}

# Parse command line arguments
parse_args() {
    MODE=""
    PREVIEW=false
    EXPORT=false
    VERBOSE=false
    PORT=8181
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev-mode|--dev)
                MODE="dev"
                shift
                ;;
            --prod|--production)
                MODE="prod"
                shift
                ;;
            --preview)
                PREVIEW=true
                shift
                ;;
            --export-frames|--export)
                EXPORT=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --port|-p)
                PORT="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Auto-detect mode if not specified
    detect_mode
}

# Show help message
show_help() {
    cat << EOF
Homelab HUD Run Script

Usage: ./run.sh [OPTIONS]

Options:
    --dev-mode, --dev        Run in development mode (Mac default)
    --prod, --production     Run in production mode (Linux/Raspberry Pi default)
    --preview                Use pygame window preview (dev mode only)
    --export-frames, --export Export frames to files instead of displaying
    --verbose, -v            Enable verbose logging
    --port, -p PORT          Set Flask web server port (default: 8181)
    --help, -h               Show this help message

Examples:
    ./run.sh                          # Auto-detect mode (dev on Mac, prod on Linux)
    ./run.sh --dev-mode --preview     # Development mode with pygame window
    ./run.sh --dev-mode --export      # Development mode, export frames to files
    ./run.sh --prod                   # Production mode (Raspberry Pi)
    ./run.sh --dev-mode --verbose     # Development mode with verbose logging

Environment Variables:
    HUD_ENV=dev|prod          Override mode detection
    HUD_USE_MOCKS=true        Use mock data instead of real APIs

Web UI:
    Once running, access the web UI at: http://localhost:8181
    (or http://localhost:<port> if using --port option)

EOF
}

# Build command arguments
build_args() {
    ARGS=""
    
    if [ "$MODE" == "dev" ]; then
        ARGS="$ARGS --dev-mode"
    fi
    
    if [ "$PREVIEW" == true ]; then
        ARGS="$ARGS --preview"
    fi
    
    if [ "$EXPORT" == true ]; then
        ARGS="$ARGS --export-frames"
    fi
    
    if [ "$VERBOSE" == true ]; then
        ARGS="$ARGS --verbose"
    fi
    
    # Add port argument
    ARGS="$ARGS --port $PORT"
}

# Main run function
run_app() {
    print_info "Starting Homelab HUD..."
    print_info "Mode: $MODE"
    print_info "OS: $OS"
    
    if [ "$PREVIEW" == true ]; then
        print_info "Preview window: enabled"
    fi
    
    if [ "$EXPORT" == true ]; then
        print_info "Frame export: enabled"
    fi
    
    if [ "$VERBOSE" == true ]; then
        print_info "Verbose logging: enabled"
    fi
    
    print_info "Web UI will be available at: http://localhost:$PORT"
    echo ""
    
    # Port will be passed to app.py via --port argument
    
    # Run the application
    exec python app.py $ARGS
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "  Homelab HUD - Run Script"
    echo "=========================================="
    echo ""
    
    check_venv
    check_app
    parse_args "$@"
    activate_venv
    build_args
    run_app
}

# Run main function with all arguments
main "$@"

