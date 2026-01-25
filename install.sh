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

# Configure cmdline.txt to disable console on framebuffer
configure_cmdline() {
    print_info "Configuring cmdline.txt to disable console on framebuffer..."
    
    CMDLINE_FILE="/boot/cmdline.txt"
    CMDLINE_BACKUP="/boot/cmdline.txt.homelab-hud.backup"
    CMDLINE_TEMP="/tmp/cmdline.txt.homelab-hud.tmp"
    
    if [ ! -f "$CMDLINE_FILE" ]; then
        print_warning "Could not find $CMDLINE_FILE, skipping cmdline configuration"
        return
    fi
    
    # Create backup if it doesn't exist
    if [ ! -f "$CMDLINE_BACKUP" ]; then
        cp "$CMDLINE_FILE" "$CMDLINE_BACKUP"
        print_success "Created cmdline backup: $CMDLINE_BACKUP"
    fi
    
    # Read cmdline.txt (it's a single line)
    CMDLINE_CONTENT=$(cat "$CMDLINE_FILE")
    
    # Remove console=tty1 if present (this shows console on framebuffer)
    if echo "$CMDLINE_CONTENT" | grep -q "console=tty1"; then
        CMDLINE_CONTENT=$(echo "$CMDLINE_CONTENT" | sed 's/\bconsole=tty1\b//g')
        print_info "Removed console=tty1 from cmdline.txt"
    fi
    
    # Remove console=ttyAMA0,console=tty1 if present
    if echo "$CMDLINE_CONTENT" | grep -q "console=ttyAMA0,console=tty1"; then
        CMDLINE_CONTENT=$(echo "$CMDLINE_CONTENT" | sed 's/\bconsole=ttyAMA0,console=tty1\b/console=ttyAMA0/g')
        print_info "Removed console=tty1 from combined console setting"
    fi
    
    # Add consoleblank=0 if not present (prevents screen blanking)
    if ! echo "$CMDLINE_CONTENT" | grep -q "consoleblank="; then
        CMDLINE_CONTENT="$CMDLINE_CONTENT consoleblank=0"
        print_info "Added consoleblank=0 to cmdline.txt"
    fi
    
    # Clean up multiple spaces
    CMDLINE_CONTENT=$(echo "$CMDLINE_CONTENT" | sed 's/  */ /g' | sed 's/^ *//' | sed 's/ *$//')
    
    # Write to temp file first
    echo "$CMDLINE_CONTENT" > "$CMDLINE_TEMP"
    
    # Verify temp file is valid (not empty, single line)
    if [ ! -s "$CMDLINE_TEMP" ]; then
        print_error "Temporary cmdline file is empty! Restoring from backup..."
        cp "$CMDLINE_BACKUP" "$CMDLINE_FILE"
        rm -f "$CMDLINE_TEMP"
        return 1
    fi
    
    # Move temp file to actual cmdline
    mv "$CMDLINE_TEMP" "$CMDLINE_FILE"
    chmod 644 "$CMDLINE_FILE"
    
    print_success "cmdline.txt configured to disable console on framebuffer"
    print_info "Console output redirected away from composite video"
}

# Configure composite video output in /boot/config.txt
configure_composite_video() {
    print_info "Configuring composite video output..."
    
    CONFIG_FILE="/boot/config.txt"
    BACKUP_FILE="/boot/config.txt.homelab-hud.backup"
    TEMP_FILE="/tmp/config.txt.homelab-hud.tmp"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Could not find $CONFIG_FILE"
        print_warning "Composite video configuration skipped"
        return
    fi
    
    # Create backup if it doesn't exist
    if [ ! -f "$BACKUP_FILE" ]; then
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        print_success "Created backup: $BACKUP_FILE"
        print_info "You can restore original config with: sudo cp $BACKUP_FILE $CONFIG_FILE"
    else
        print_info "Backup already exists: $BACKUP_FILE"
    fi
    
    # Use a temporary file to avoid corruption
    cp "$CONFIG_FILE" "$TEMP_FILE"
    
    # Check if enable_tvout is already set
    if grep -q "^enable_tvout=" "$TEMP_FILE"; then
        # Update existing setting (only the value, preserve any comments on the line)
        sed -i 's/^enable_tvout=.*/enable_tvout=1/' "$TEMP_FILE"
        print_info "Updated enable_tvout=1 in $CONFIG_FILE"
    elif grep -q "^#.*enable_tvout" "$TEMP_FILE"; then
        # Uncomment and set (be careful to preserve line structure)
        sed -i 's/^#\s*enable_tvout.*/enable_tvout=1/' "$TEMP_FILE"
        print_info "Enabled enable_tvout=1 in $CONFIG_FILE"
    else
        # Add new setting at the end (preserve all existing content)
        echo "" >> "$TEMP_FILE"
        echo "# Homelab HUD - Composite video output" >> "$TEMP_FILE"
        echo "enable_tvout=1" >> "$TEMP_FILE"
        print_info "Added enable_tvout=1 to $CONFIG_FILE"
    fi
    
    # Set framebuffer resolution (320x280)
    # Check if framebuffer settings exist
    if grep -q "^framebuffer_width=" "$TEMP_FILE"; then
        sed -i 's/^framebuffer_width=.*/framebuffer_width=320/' "$TEMP_FILE"
        print_info "Updated framebuffer_width=320"
    else
        echo "framebuffer_width=320" >> "$TEMP_FILE"
        print_info "Added framebuffer_width=320"
    fi
    
    if grep -q "^framebuffer_height=" "$TEMP_FILE"; then
        sed -i 's/^framebuffer_height=.*/framebuffer_height=280/' "$TEMP_FILE"
        print_info "Updated framebuffer_height=280"
    else
        echo "framebuffer_height=280" >> "$TEMP_FILE"
        print_info "Added framebuffer_height=280"
    fi
    
    # Verify the temp file is valid (basic sanity check)
    if [ ! -s "$TEMP_FILE" ]; then
        print_error "Temporary config file is empty! Restoring from backup..."
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        rm -f "$TEMP_FILE"
        return 1
    fi
    
    # Verify critical settings are preserved (SSH, autologin, network)
    # Check for common SSH settings
    if ! grep -q "dtparam=ssh" "$TEMP_FILE" && grep -q "dtparam=ssh" "$BACKUP_FILE"; then
        print_warning "SSH setting may have been removed. Restoring from backup..."
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        rm -f "$TEMP_FILE"
        return 1
    fi
    
    # Check for autologin settings
    if ! grep -q "autologin" "$TEMP_FILE" && grep -q "autologin" "$BACKUP_FILE"; then
        print_warning "Autologin setting may have been removed. Restoring from backup..."
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        rm -f "$TEMP_FILE"
        return 1
    fi
    
    # If all checks pass, move temp file to actual config
    mv "$TEMP_FILE" "$CONFIG_FILE"
    chmod 644 "$CONFIG_FILE"
    
    print_success "Composite video output configured"
    print_info "Modified settings: enable_tvout=1, framebuffer_width=320, framebuffer_height=280"
    print_info "All other settings preserved. Backup available at: $BACKUP_FILE"
    
    # Configure cmdline.txt to disable console on framebuffer
    configure_cmdline
    
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

