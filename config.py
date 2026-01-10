"""
Configuration management for Homelab HUD.
Handles environment detection, configuration loading, and defaults.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FONTS_DIR = BASE_DIR / "data" / "fonts"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)
(DATA_DIR / "preview").mkdir(exist_ok=True)

# Configuration files
SLIDES_CONFIG_FILE = DATA_DIR / "slides.json"
API_CONFIG_FILE = DATA_DIR / "api_config.json"

# Display settings
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 280
DISPLAY_FPS = 30

# Environment detection
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform == 'linux'
IS_DEV = os.getenv('HUD_ENV') == 'dev' or IS_MAC
USE_MOCKS = os.getenv('HUD_USE_MOCKS', 'false').lower() == 'true'


def get_default_slides_config() -> Dict[str, Any]:
    """Return default slide configuration."""
    return {
        "slides": [
            {
                "id": 1,
                "type": "pihole_summary",
                "title": "Pi-hole Stats",
                "duration": 10,
                "refresh_duration": 5,
                "order": 0,
                "conditional": False
            },
            {
                "id": 2,
                "type": "plex_now_playing",
                "title": "Now Playing",
                "duration": 15,
                "refresh_duration": 1,
                "order": 1,
                "conditional": True
            },
            {
                "id": 3,
                "type": "arm_rip_progress",
                "title": "ARM Rip Progress",
                "duration": 15,
                "refresh_duration": 2,
                "order": 2,
                "conditional": True
            },
            {
                "id": 4,
                "type": "system_stats",
                "title": "System Stats",
                "duration": 10,
                "refresh_duration": 5,
                "order": 3,
                "conditional": False
            }
        ]
    }


def get_default_api_config() -> Dict[str, Any]:
    """Return default API configuration."""
    return {
        "arm": {
            "enabled": True,
            "api_url": "http://localhost:8080",
            "api_key": "",
            "poll_interval": 30,
            "conditional": True,
            "endpoint": "/json?mode=joblist"
        },
        "pihole": {
            "enabled": True,
            "api_url": "http://localhost/admin",
            "api_token": "",
            "poll_interval": 10,
            "conditional": False
        },
        "plex": {
            "enabled": True,
            "api_url": "http://localhost:32400",
            "api_token": "",
            "poll_interval": 5,
            "conditional": True
        },
        "system": {
            "enabled": True,
            "poll_interval": 5,
            "nas_mounts": [
                "/mnt/nas",
                "/media/nas"
            ],
            "conditional": False
        }
    }


def load_config(file_path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration from JSON file, creating with defaults if it doesn't exist."""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config {file_path}: {e}. Using defaults.")
    
    # Create config file with defaults
    save_config(file_path, default)
    return default


def save_config(file_path: Path, config: Dict[str, Any]) -> None:
    """Save configuration to JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Error saving config {file_path}: {e}")


def get_slides_config() -> Dict[str, Any]:
    """Get current slides configuration."""
    return load_config(SLIDES_CONFIG_FILE, get_default_slides_config())


def save_slides_config(config: Dict[str, Any]) -> None:
    """Save slides configuration."""
    save_config(SLIDES_CONFIG_FILE, config)


def get_api_config() -> Dict[str, Any]:
    """Get current API configuration."""
    return load_config(API_CONFIG_FILE, get_default_api_config())


def save_api_config(config: Dict[str, Any]) -> None:
    """Save API configuration."""
    save_config(API_CONFIG_FILE, config)

