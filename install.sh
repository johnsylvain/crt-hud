#!/bin/bash
# Homelab HUD Installation Script
# Sets up systemd service and configures composite video output for Raspberry Pi

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

# Check if running on Raspberry Pi
check_raspberry_pi() {
    print_info "Checking if running on Raspberry Pi..."
    
    if [ ! -f /proc/device-tree/model ]; then
        print_warning "Could not detect Raspberry Pi model. Continuing anyway..."
        return
    fi
    
    MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "")
    if [[ "$MODEL" == *"Raspberry Pi"* ]]; then
        print_success "Detected: $MODEL"
    else
        print_warning "Model detection: $MODEL (may not be a Raspberry Pi)"
    fi
}

# Check if running on Linux
check_linux() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script is designed for Linux/Raspberry Pi"
        exit 1
    fi
}

# Get the project directory
get_project_dir() {
    # Try to find the project directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -f "$SCRIPT_DIR/app.py" ]; then
        PROJECT_DIR="$SCRIPT_DIR"
    else
        print_error "Could not find project directory. Please run this script from the project root."
        exit 1
    fi
    
    print_info "Project directory: $PROJECT_DIR"
}

# Check if virtual environment exists
check_venv() {
    print_info "Checking for virtual environment..."
    
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Please run ./setup.sh first to set up the environment"
        exit 1
    fi
    
    if [ ! -f "$PROJECT_DIR/venv/bin/python3" ]; then
        print_error "Python not found in virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment found"
}

# Get Python path from venv
get_python_path() {
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"
    print_info "Python path: $PYTHON_PATH"
}

# Get user who owns the project directory
get_service_user() {
    SERVICE_USER=$(stat -c '%U' "$PROJECT_DIR" 2>/dev/null || echo "pi")
    print_info "Service will run as user: $SERVICE_USER"
}

# Configure composite video output in /boot/config.txt
configure_composite_video() {
    print_info "Configuring composite video output..."
    
    CONFIG_FILE="/boot/config.txt"
    BACKUP_FILE="/boot/config.txt.homelab-hud.backup"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Could not find $CONFIG_FILE"
        print_warning "Composite video configuration skipped"
        return
    fi
    
    # Create backup if it doesn't exist
    if [ ! -f "$BACKUP_FILE" ]; then
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        print_success "Created backup: $BACKUP_FILE"
    fi
    
    # Check if enable_tvout is already set
    if grep -q "^enable_tvout=" "$CONFIG_FILE"; then
        # Update existing setting
        sed -i 's/^enable_tvout=.*/enable_tvout=1/' "$CONFIG_FILE"
        print_info "Updated enable_tvout=1 in $CONFIG_FILE"
    elif grep -q "^#.*enable_tvout" "$CONFIG_FILE"; then
        # Uncomment and set
        sed -i 's/^#.*enable_tvout.*/enable_tvout=1/' "$CONFIG_FILE"
        print_info "Enabled enable_tvout=1 in $CONFIG_FILE"
    else
        # Add new setting
        echo "" >> "$CONFIG_FILE"
        echo "# Homelab HUD - Composite video output" >> "$CONFIG_FILE"
        echo "enable_tvout=1" >> "$CONFIG_FILE"
        print_info "Added enable_tvout=1 to $CONFIG_FILE"
    fi
    
    # Set framebuffer resolution (320x280)
    # Check if framebuffer settings exist
    if grep -q "^framebuffer_width=" "$CONFIG_FILE"; then
        sed -i 's/^framebuffer_width=.*/framebuffer_width=320/' "$CONFIG_FILE"
        print_info "Updated framebuffer_width=320"
    else
        echo "framebuffer_width=320" >> "$CONFIG_FILE"
        print_info "Added framebuffer_width=320"
    fi
    
    if grep -q "^framebuffer_height=" "$CONFIG_FILE"; then
        sed -i 's/^framebuffer_height=.*/framebuffer_height=280/' "$CONFIG_FILE"
        print_info "Updated framebuffer_height=280"
    else
        echo "framebuffer_height=280" >> "$CONFIG_FILE"
        print_info "Added framebuffer_height=280"
    fi
    
    print_success "Composite video output configured"
    print_warning "Reboot required for video configuration to take effect"
}

# Create systemd service file
create_service_file() {
    print_info "Creating systemd service file..."
    
    SERVICE_NAME="homelab-hud"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    # Create service file
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Homelab HUD - Raspberry Pi CRT Stats Display
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HUD_ENV=prod"
ExecStart=$PYTHON_PATH $PROJECT_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Service file created: $SERVICE_FILE"
}

# Set up framebuffer permissions
setup_framebuffer_permissions() {
    print_info "Setting up framebuffer permissions..."
    
    # Add user to video group if it exists
    if getent group video > /dev/null 2>&1; then
        usermod -a -G video "$SERVICE_USER" 2>/dev/null || true
        print_info "Added $SERVICE_USER to video group"
    fi
    
    # Set framebuffer device permissions (if it exists)
    if [ -e /dev/fb0 ]; then
        chmod 666 /dev/fb0 2>/dev/null || {
            # If chmod fails, create udev rule
            print_info "Creating udev rule for framebuffer access..."
            UDEV_RULE="/etc/udev/rules.d/99-homelab-hud-framebuffer.rules"
            cat > "$UDEV_RULE" << EOF
# Homelab HUD - Framebuffer access
KERNEL=="fb0", GROUP="video", MODE="0666"
EOF
            print_success "Created udev rule: $UDEV_RULE"
            print_info "You may need to reboot for udev rules to take effect"
        }
    else
        print_warning "Framebuffer device /dev/fb0 not found (may appear after reboot)"
    fi
}

# Reload systemd and enable service
enable_service() {
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_info "Enabling $SERVICE_NAME service..."
    systemctl enable "$SERVICE_NAME"
    
    print_success "Service enabled (will start on boot)"
}

# Start the service
start_service() {
    print_info "Starting $SERVICE_NAME service..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "Service is already running, restarting..."
        systemctl restart "$SERVICE_NAME"
    else
        systemctl start "$SERVICE_NAME"
    fi
    
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service started successfully"
    else
        print_error "Service failed to start"
        print_info "Check status with: sudo systemctl status $SERVICE_NAME"
        print_info "Check logs with: sudo journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

# Show service status
show_status() {
    echo ""
    print_success "Installation complete!"
    echo ""
    echo "Service Information:"
    echo "  Name: homelab-hud"
    echo "  Status: $(systemctl is-active homelab-hud)"
    echo "  Enabled: $(systemctl is-enabled homelab-hud)"
    echo ""
    echo "Useful commands:"
    echo "  Check status:  sudo systemctl status homelab-hud"
    echo "  View logs:     sudo journalctl -u homelab-hud -f"
    echo "  Restart:       sudo systemctl restart homelab-hud"
    echo "  Stop:          sudo systemctl stop homelab-hud"
    echo ""
    echo "Web UI:"
    echo "  http://localhost:8181"
    echo "  (or http://$(hostname -I | awk '{print $1}'):8181 from another device)"
    echo ""
    print_warning "IMPORTANT: Reboot required for composite video configuration to take effect"
    echo "  Run: sudo reboot"
    echo ""
}

# Main installation function
main() {
    echo ""
    echo "=========================================="
    echo "  Homelab HUD Installation Script"
    echo "=========================================="
    echo ""
    
    check_root
    check_linux
    check_raspberry_pi
    get_project_dir
    check_venv
    get_python_path
    get_service_user
    configure_composite_video
    create_service_file
    setup_framebuffer_permissions
    enable_service
    start_service
    show_status
}

# Run main function
main "$@"

