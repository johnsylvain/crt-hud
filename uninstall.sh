#!/bin/bash
# Homelab HUD Uninstallation Script
# Removes systemd service and optionally reverts composite video configuration

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

# Stop and disable service
stop_service() {
    print_info "Stopping homelab-hud service..."
    
    SERVICE_NAME="homelab-hud"
    
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl stop "$SERVICE_NAME"
        print_success "Service stopped"
    else
        print_info "Service was not running"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME"
        print_success "Service disabled"
    else
        print_info "Service was not enabled"
    fi
}

# Remove service file
remove_service_file() {
    print_info "Removing systemd service file..."
    
    SERVICE_FILE="/etc/systemd/system/homelab-hud.service"
    
    if [ -f "$SERVICE_FILE" ]; then
        rm -f "$SERVICE_FILE"
        print_success "Service file removed"
    else
        print_info "Service file not found (already removed?)"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    print_info "Systemd daemon reloaded"
}

# Remove udev rule
remove_udev_rule() {
    print_info "Removing udev rule..."
    
    UDEV_RULE="/etc/udev/rules.d/99-homelab-hud-framebuffer.rules"
    
    if [ -f "$UDEV_RULE" ]; then
        rm -f "$UDEV_RULE"
        print_success "Udev rule removed"
        print_info "You may need to reboot for changes to take effect"
    else
        print_info "Udev rule not found"
    fi
}

# Revert composite video configuration
revert_composite_video() {
    print_info "Checking composite video configuration..."
    
    CONFIG_FILE="/boot/config.txt"
    BACKUP_FILE="/boot/config.txt.homelab-hud.backup"
    CMDLINE_FILE="/boot/cmdline.txt"
    CMDLINE_BACKUP="/boot/cmdline.txt.homelab-hud.backup"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "Config file not found, skipping revert"
        return
    fi
    
    # Ask user if they want to revert config.txt changes
    echo ""
    read -p "Do you want to revert /boot/config.txt changes? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping config.txt changes (backup available at $BACKUP_FILE)"
    else
        if [ -f "$BACKUP_FILE" ]; then
            print_info "Restoring config.txt from backup..."
            cp "$BACKUP_FILE" "$CONFIG_FILE"
            print_success "Config file restored from backup"
        else
            print_warning "No config.txt backup file found. Manual cleanup may be needed."
            print_info "Look for these lines in $CONFIG_FILE and remove if desired:"
            echo "  - enable_tvout=1"
            echo "  - framebuffer_width=320"
            echo "  - framebuffer_height=280"
        fi
    fi
    
    # Ask user if they want to revert cmdline.txt changes
    echo ""
    read -p "Do you want to revert /boot/cmdline.txt changes? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping cmdline.txt changes (backup available at $CMDLINE_BACKUP)"
    else
        if [ -f "$CMDLINE_BACKUP" ]; then
            print_info "Restoring cmdline.txt from backup..."
            cp "$CMDLINE_BACKUP" "$CMDLINE_FILE"
            print_success "cmdline.txt restored from backup"
        else
            print_warning "No cmdline.txt backup file found."
            print_info "You may need to manually restore console=tty1 if it was removed"
        fi
    fi
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Reboot required for changes to take effect"
        
        # Ask if user wants to keep backup files
        echo ""
        read -p "Keep backup files? (Y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            [ -f "$BACKUP_FILE" ] && rm -f "$BACKUP_FILE" && print_info "Config backup removed"
            [ -f "$CMDLINE_BACKUP" ] && rm -f "$CMDLINE_BACKUP" && print_info "cmdline backup removed"
        else
            [ -f "$BACKUP_FILE" ] && print_info "Config backup kept at: $BACKUP_FILE"
            [ -f "$CMDLINE_BACKUP" ] && print_info "cmdline backup kept at: $CMDLINE_BACKUP"
        fi
    fi
}

# Show uninstallation summary
show_summary() {
    echo ""
    print_success "Uninstallation complete!"
    echo ""
    echo "Removed:"
    echo "  - Systemd service (homelab-hud.service)"
    echo "  - Udev rule (if present)"
    echo ""
    echo "Note:"
    echo "  - Project files in the installation directory were NOT removed"
    echo "  - Virtual environment was NOT removed"
    echo "  - Configuration files (data/*.json) were NOT removed"
    echo ""
    
    if [ -f "/boot/config.txt.homelab-hud.backup" ]; then
        echo "  - Config backup available at: /boot/config.txt.homelab-hud.backup"
    fi
    
    echo ""
    print_warning "If you reverted config.txt changes, reboot may be required"
    echo ""
}

# Main uninstallation function
main() {
    echo ""
    echo "=========================================="
    echo "  Homelab HUD Uninstallation Script"
    echo "=========================================="
    echo ""
    
    check_root
    stop_service
    remove_service_file
    remove_udev_rule
    revert_composite_video
    show_summary
}

# Run main function
main "$@"

