# Homelab HUD - Raspberry Pi CRT Stats Display

A Tidbyt-like application for Raspberry Pi that displays real-time stats (ARM, Pi-hole, Plex, System) on a 5-inch black and white CRT via composite output. Features a Fallout-themed minimal UI at 320x280 resolution with a web-based slide editor.

## Features

- **Real-time Stats Display**: ARM rip progress, Pi-hole stats, Plex now playing, system stats (CPU, Memory, NAS storage)
- **Conditional Display**: ARM and Plex slides only appear when active (rip in progress / streaming)
- **Web UI**: Admin interface for creating, editing, and reordering slides
- **Fallout Aesthetic**: Minimal, high-contrast monochrome design optimized for CRT
- **Cross-platform Development**: Fully testable on Mac before deploying to Raspberry Pi

## Setup

### Prerequisites

- Python 3.9+
- Raspberry Pi with composite video output capability
- CRT display connected via composite cable

### Installation

**Quick Setup (Recommended):**

1. Clone the repository:
```bash
git clone <repository-url>
cd homelab-hud
```

2. Run the setup script:
```bash
./setup.sh
```

The setup script will:
- Check Python 3.9+ installation
- Create a virtual environment
- Install all dependencies
- Set up necessary directories
- Create environment file
- Verify installation

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Configure APIs via web UI (accessible at `http://localhost:8181`)

**Manual Installation:**

If you prefer to install manually:

1. Ensure Python 3.9+ is installed
2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Create necessary directories:
```bash
mkdir -p data/fonts data/preview tests/fixtures
```

### Raspberry Pi Configuration

1. Enable composite video output in `/boot/config.txt`:
```
enable_tvout=1
```

2. Set framebuffer resolution (if using framebuffer method):
```bash
sudo fbset -xres 320 -yres 280
```

### Raspberry Pi Service Installation (Run on Boot)

To install Homelab HUD as a systemd service that runs automatically on boot:

1. **Complete the basic setup first:**
   ```bash
   ./setup.sh
   ```

2. **Run the installation script:**
   ```bash
   sudo ./install.sh
   ```

The installation script will:
- Configure composite video output in `/boot/config.txt` (creates backup automatically)
- Set framebuffer resolution to 320x280
- Create a systemd service file (`homelab-hud.service`)
- Set up framebuffer permissions and udev rules
- Enable and start the service

3. **Reboot to apply composite video configuration:**
   ```bash
   sudo reboot
   ```

After reboot, the service will start automatically and display will appear on your CRT monitor.

**Service Management Commands:**

```bash
# Check service status
sudo systemctl status homelab-hud

# View service logs
sudo journalctl -u homelab-hud -f

# Restart service
sudo systemctl restart homelab-hud

# Stop service
sudo systemctl stop homelab-hud

# Start service
sudo systemctl start homelab-hud
```

**Web UI Access:**

Once the service is running, access the web UI at:
- `http://localhost:8181` (on the Pi)
- `http://<pi-ip-address>:8181` (from another device on your network)

**Uninstallation:**

To remove the service and optionally revert configuration changes:

```bash
sudo ./uninstall.sh
```

The uninstallation script will:
- Stop and disable the service
- Remove the systemd service file
- Remove udev rules
- Optionally restore `/boot/config.txt` from backup (with confirmation)
- **Note:** Project files, virtual environment, and configuration data are NOT deleted

## Usage

### Quick Start (Recommended)

Use the run script for easy execution:

**Development Mode (Mac):**
```bash
./run.sh --dev-mode --preview
```

**Production Mode (Raspberry Pi):**
```bash
./run.sh --prod
```

**Auto-detect Mode (default):**
```bash
./run.sh
```
Auto-detects Mac (dev) or Linux/Pi (prod) mode.

**Export frames to files:**
```bash
./run.sh --dev-mode --export-frames
```

See all options:
```bash
./run.sh --help
```

### Manual Execution

If you prefer to run directly:

**Development Mode (Mac):**

1. Activate virtual environment:
```bash
source venv/bin/activate
```

2. Run in development mode:
```bash
python app.py --dev-mode
```

3. For pygame window preview:
```bash
python app.py --dev-mode --preview
```

4. Access web UI at `http://localhost:8181`

**Production Mode (Raspberry Pi):**

1. Activate virtual environment:
```bash
source venv/bin/activate
```

2. Run in production mode:
```bash
python app.py
```

The application will:
- Start Flask web server on port 8181
- Begin cycling through configured slides on composite output
- Display slides based on conditional logic (ARM/Plex only when active)

## Configuration

Configuration is managed via the web UI. API endpoints and credentials are stored in `data/api_config.json`, and slide configuration is in `data/slides.json`.

## Development

See the plan file for detailed architecture and implementation details.

## Project Structure

```
homelab-hud/
├── app.py                 # Main application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── backend/               # Backend components
│   ├── api/              # Flask API routes and models
│   ├── collectors/       # Data collectors (ARM, Pi-hole, Plex, System)
│   ├── display/          # Display engine (renderer, themes, video output)
│   └── utils/            # Utility functions
├── frontend/             # Web UI
│   ├── static/           # CSS and JavaScript
│   └── templates/        # HTML templates
├── data/                 # Configuration and preview data
│   ├── slides.json       # Slide configuration (auto-generated)
│   ├── api_config.json   # API configuration (auto-generated)
│   └── preview/          # Preview frames (dev mode)
└── tests/                # Test fixtures for mock data
    └── fixtures/         # Mock JSON responses
```

## Quick Start

1. **Install dependencies:**
   ```bash
   ./setup.sh  # Or manually: pip install -r requirements.txt
   ```

2. **Development Mode (Mac):**
   ```bash
   ./run.sh --dev-mode --preview
   # Or: python app.py --dev-mode --preview
   ```
   This will:
   - Start Flask web UI at http://localhost:8181
   - Display slides in a pygame window (or save to files)
   - Use file-based preview output

3. **Production Mode (Raspberry Pi):**
   
   **Option A: Install as a service (recommended for production):**
   ```bash
   sudo ./install.sh
   sudo reboot  # Required for composite video configuration
   ```
   Service will start automatically on boot.

   **Option B: Manual run:**
   ```bash
   ./run.sh --prod
   # Or: python app.py
   ```
   This will:
   - Start Flask web UI
   - Display slides on composite video output
   - Use framebuffer output for CRT display

4. **Configure APIs via web UI:**
   - Navigate to http://localhost:8181 (or http://<pi-ip>:8181)
   - Configure ARM, Pi-hole, Plex API endpoints
   - Create and reorder slides
   - Preview slides

## Features Implemented

✅ **Data Collectors:**
- ARM collector (conditional: only shows when rip active)
- Pi-hole collector (always shows)
- Plex collector (conditional: only shows when streaming)
- System collector (CPU, Memory, NAS storage - always shows)

✅ **Display Engine:**
- Fallout-themed monochrome design (320x280)
- PIL/Pillow-based rendering
- Progress bars, ASCII graphics
- Platform-aware output (Mac: preview, Pi: composite video)

✅ **Web UI:**
- Slide management (create, edit, delete, reorder)
- API configuration
- Live preview
- Drag-and-drop slide reordering

✅ **Conditional Display:**
- ARM slides only appear when rip is active
- Plex slides only appear when someone is streaming
- System/Pi-hole slides always display

✅ **Development Tools:**
- Mac development mode with preview
- Mock data support for testing
- Frame export functionality
- Debug logging

