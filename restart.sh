#!/bin/bash
# Homelab HUD Service Restart Script
# Restarts the homelab-hud systemd service

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

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if service exists
check_service() {
    SERVICE_NAME="homelab-hud"
    
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        print_error "Service ${SERVICE_NAME} not found!"
        print_info "The service may not be installed yet."
        print_info "Run: sudo ./install.sh to install the service"
        exit 1
    fi
    
    print_success "Service ${SERVICE_NAME} found"
}

# Restart the service
restart_service() {
    SERVICE_NAME="homelab-hud"
    
    print_info "Restarting ${SERVICE_NAME} service..."
    
    # Check current status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "Service is currently running, stopping..."
        systemctl stop "$SERVICE_NAME" || {
            print_error "Failed to stop service"
            exit 1
        }
        sleep 1
    else
        print_warning "Service is not currently running"
    fi
    
    # Start the service
    print_info "Starting ${SERVICE_NAME} service..."
    systemctl start "$SERVICE_NAME" || {
        print_error "Failed to start service"
        print_info "Check logs with: sudo journalctl -u ${SERVICE_NAME} -n 50"
        exit 1
    }
    
    # Wait a moment for service to initialize
    sleep 2
    
    # Check if service started successfully
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service restarted successfully"
    else
        print_error "Service failed to start"
        print_info "Check status with: sudo systemctl status ${SERVICE_NAME}"
        print_info "Check logs with: sudo journalctl -u ${SERVICE_NAME} -f"
        exit 1
    fi
}

# Show service status
show_status() {
    SERVICE_NAME="homelab-hud"
    
    echo ""
    print_info "Service Status:"
    echo ""
    
    # Get service status
    STATUS=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || echo "unknown")
    ENABLED=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo "unknown")
    
    echo "  Status:  $STATUS"
    echo "  Enabled: $ENABLED"
    echo ""
    
    # Show recent logs (last 5 lines)
    print_info "Recent logs (last 5 lines):"
    echo ""
    journalctl -u "$SERVICE_NAME" -n 5 --no-pager || true
    echo ""
    
    # Show useful commands
    echo "Useful commands:"
    echo "  View full logs:    sudo journalctl -u ${SERVICE_NAME} -f"
    echo "  Check status:      sudo systemctl status ${SERVICE_NAME}"
    echo "  Stop service:      sudo systemctl stop ${SERVICE_NAME}"
    echo "  Start service:     sudo systemctl start ${SERVICE_NAME}"
    echo ""
    
    # Show web UI info
    if [ "$STATUS" == "active" ]; then
        IP_ADDRESS=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        echo "Web UI:"
        echo "  http://localhost:8181"
        echo "  http://${IP_ADDRESS}:8181 (from other devices)"
        echo ""
    fi
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "  Homelab HUD Service Restart"
    echo "=========================================="
    echo ""
    
    check_root
    check_service
    restart_service
    show_status
}

# Run main function
main "$@"

