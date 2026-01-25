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
        "display": {
            "font_scale": 1.0  # Global font scale multiplier (1.0 = default, 1.5 = 50% larger, etc.)
        },
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
    """Save configuration to JSON file.
    
    Raises:
        IOError: If file cannot be written (permission denied, disk full, etc.)
        OSError: If directory cannot be created or other OS-level error occurs
    """
    import stat
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and get current permissions for logging
    file_exists = file_path.exists()
    if file_exists:
        try:
            file_stat = file_path.stat()
            file_perms = stat.filemode(file_stat.st_mode)
            file_owner = file_stat.st_uid
            print(f"DEBUG: Existing file {file_path} - permissions: {file_perms}, owner UID: {file_owner}")
        except OSError as e:
            print(f"DEBUG: Could not stat existing file {file_path}: {e}")
    
    # Check directory permissions
    try:
        dir_stat = file_path.parent.stat()
        dir_perms = stat.filemode(dir_stat.st_mode)
        dir_owner = dir_stat.st_uid
        print(f"DEBUG: Directory {file_path.parent} - permissions: {dir_perms}, owner UID: {dir_owner}")
    except OSError as e:
        print(f"DEBUG: Could not stat directory {file_path.parent}: {e}")
    
    # Get current user info for logging
    try:
        current_uid = os.getuid()
        try:
            import pwd
            current_user = pwd.getpwuid(current_uid).pw_name
            print(f"DEBUG: Current user: {current_user} (UID: {current_uid})")
        except (ImportError, KeyError):
            # pwd not available or user not found
            print(f"DEBUG: Current UID: {current_uid}")
    except AttributeError:
        # Windows - os.getuid() not available
        print(f"DEBUG: Running on Windows")
    
    try:
        # Write to temporary file first, then rename (atomic write)
        temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
        with open(temp_file, 'w') as f:
            json.dump(config, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Verify temp file was written
        if not temp_file.exists() or temp_file.stat().st_size == 0:
            raise IOError(f"Failed to write temporary file {temp_file}")
        
        # Atomic rename (works on Unix, may need different approach on Windows)
        temp_file.replace(file_path)
        
        # Verify final file exists and has content
        if not file_path.exists():
            raise IOError(f"File {file_path} was not created after write")
        
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise IOError(f"File {file_path} was created but is empty")
        
        print(f"DEBUG: Successfully saved config to {file_path} ({file_size} bytes)")
        
    except (IOError, OSError) as e:
        error_msg = f"Error saving config {file_path}: {e}"
        print(f"ERROR: {error_msg}")
        
        # Additional diagnostic info
        if isinstance(e, PermissionError):
            print(f"ERROR: Permission denied - check file and directory permissions")
            print(f"ERROR: File path: {file_path}")
            print(f"ERROR: Directory: {file_path.parent}")
            if file_path.exists():
                print(f"ERROR: File exists but may not be writable")
            else:
                print(f"ERROR: Directory may not be writable")
        
        # Re-raise the exception so API can handle it
        raise


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

