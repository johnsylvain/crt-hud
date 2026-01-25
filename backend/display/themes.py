"""Fallout-style theme for CRT display."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys
from typing import Dict
from config import get_api_config

# Fallout color palette (monochrome for CRT)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY_LIGHT = (200, 200, 200)
COLOR_GRAY_MEDIUM = (128, 128, 128)
COLOR_GRAY_DARK = (64, 64, 64)

# Display dimensions
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 280

# Base font settings (will be scaled by font_scale from config)
BASE_FONT_SIZE_LARGE = 28
BASE_FONT_SIZE_MEDIUM = 22
BASE_FONT_SIZE_SMALL = 18
BASE_FONT_SIZE_TINY = 16

# Base layout constants (will be scaled by font_scale from config)
BASE_PADDING = 12
BASE_LINE_HEIGHT_LARGE = 34
BASE_LINE_HEIGHT_MEDIUM = 26
BASE_LINE_HEIGHT_SMALL = 22
BASE_LINE_HEIGHT_TINY = 20


def get_font_scale() -> float:
    """Get font scale from configuration."""
    try:
        api_config = get_api_config()
        display_config = api_config.get("display", {})
        font_scale = display_config.get("font_scale", 1.0)
        # Ensure font_scale is a valid number between 0.5 and 3.0
        font_scale = float(font_scale)
        if font_scale < 0.5:
            font_scale = 0.5
        elif font_scale > 3.0:
            font_scale = 3.0
        # Always log font scale for debugging
        print(f"[Theme] Font scale from config: {font_scale:.2f} (display_config: {display_config})")
        return font_scale
    except Exception as e:
        print(f"[Theme] Error getting font scale: {e}, using default 1.0")
        return 1.0


def get_padding_config() -> Dict[str, int]:
    """Get padding configuration from config, with defaults."""
    try:
        api_config = get_api_config()
        display_config = api_config.get("display", {})
        padding_config = display_config.get("padding", {})
        
        # Get individual padding values, defaulting to BASE_PADDING scaled by font_scale
        font_scale = get_font_scale()
        default_padding = int(BASE_PADDING * font_scale)
        
        padding = {
            "top": int(padding_config.get("top", default_padding)),
            "bottom": int(padding_config.get("bottom", default_padding)),
            "left": int(padding_config.get("left", default_padding)),
            "right": int(padding_config.get("right", default_padding))
        }
        
        # Ensure padding values are non-negative and reasonable (0-100 pixels)
        for key in padding:
            padding[key] = max(0, min(100, padding[key]))
        
        return padding
    except Exception as e:
        print(f"[Theme] Error getting padding config: {e}, using defaults")
        font_scale = get_font_scale()
        default_padding = int(BASE_PADDING * font_scale)
        return {
            "top": default_padding,
            "bottom": default_padding,
            "left": default_padding,
            "right": default_padding
        }


# Scaled font settings (computed from base values and font_scale)
def _get_scaled_font_sizes() -> tuple:
    """Get scaled font sizes based on configuration."""
    scale = get_font_scale()
    return (
        int(BASE_FONT_SIZE_LARGE * scale),
        int(BASE_FONT_SIZE_MEDIUM * scale),
        int(BASE_FONT_SIZE_SMALL * scale),
        int(BASE_FONT_SIZE_TINY * scale),
    )


def _get_scaled_layout_constants() -> tuple:
    """Get scaled layout constants based on configuration."""
    scale = get_font_scale()
    return (
        int(BASE_PADDING * scale),
        int(BASE_LINE_HEIGHT_LARGE * scale),
        int(BASE_LINE_HEIGHT_MEDIUM * scale),
        int(BASE_LINE_HEIGHT_SMALL * scale),
        int(BASE_LINE_HEIGHT_TINY * scale),
    )


# Export scaled constants for backward compatibility
FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL, FONT_SIZE_TINY = _get_scaled_font_sizes()
PADDING, LINE_HEIGHT_LARGE, LINE_HEIGHT_MEDIUM, LINE_HEIGHT_SMALL, LINE_HEIGHT_TINY = _get_scaled_layout_constants()


# Macintosh Plus-inspired font registry
FONT_REGISTRY = {
    "monaco": {
        "name": "Monaco",
        "description": "Classic Mac monospace font (Macintosh Plus style)",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Monaco.ttf",
                "/System/Library/Fonts/Supplemental/Monaco.ttf",
                "/Library/Fonts/Monaco.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
        }
    },
    "geneva": {
        "name": "Geneva",
        "description": "Classic Mac sans-serif font",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Geneva.ttf",
                "/System/Library/Fonts/Supplemental/Geneva.ttf",
                "/Library/Fonts/Geneva.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
        }
    },
    "chicago": {
        "name": "Chicago",
        "description": "Classic Mac system font (bitmap style)",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Chicago.ttf",
                "/System/Library/Fonts/Supplemental/Chicago.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        }
    },
    "courier": {
        "name": "Courier",
        "description": "Classic monospace typewriter font",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Courier.ttc",
                "/System/Library/Fonts/Supplemental/Courier New.ttf",
                "/Library/Fonts/Courier New.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            ]
        }
    },
    "menlo": {
        "name": "Menlo",
        "description": "Modern Mac monospace font",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/Supplemental/Menlo.ttc",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
        }
    },
    "system": {
        "name": "System Default",
        "description": "System default monospace font",
        "paths": {
            "darwin": [
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/Monaco.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
        }
    }
}


def get_font_family() -> str:
    """Get font family from configuration."""
    try:
        api_config = get_api_config()
        display_config = api_config.get("display", {})
        font_family = display_config.get("font_family", "monaco")
        # Validate font family
        if font_family not in FONT_REGISTRY:
            print(f"[Theme] Invalid font family '{font_family}', using 'monaco'")
            font_family = "monaco"
        print(f"[Theme] Font family from config: {font_family}")
        return font_family
    except Exception as e:
        print(f"[Theme] Error getting font family: {e}, using default 'monaco'")
        return "monaco"


def get_monospace_font(size: int, font_family: str = None) -> ImageFont.FreeTypeFont:
    """
    Get monospace font for given size and font family.
    Macintosh Plus-inspired font selection.
    
    Args:
        size: Font size in pixels
        font_family: Font family name (monaco, geneva, chicago, courier, menlo, system)
                    If None, uses font_family from config
    
    Returns:
        PIL ImageFont object
    """
    if font_family is None:
        font_family = get_font_family()
    
    try:
        # First, try custom fonts in data/fonts directory
        custom_font_paths = [
            Path(__file__).parent.parent.parent / "data" / "fonts" / f"{font_family}.ttf",
            Path(__file__).parent.parent.parent / "data" / "fonts" / "monospace.ttf",
            Path(__file__).parent.parent.parent / "data" / "fonts" / "Courier.ttf",
        ]
        
        for font_path in custom_font_paths:
            if font_path.exists():
                try:
                    font = ImageFont.truetype(str(font_path), size)
                    print(f"[Theme] Loaded custom font from {font_path} at size {size}")
                    return font
                except Exception as e:
                    print(f"[Theme] Failed to load custom font {font_path}: {e}")
                    continue
        
        # Get font paths from registry
        if font_family not in FONT_REGISTRY:
            print(f"[Theme] Font family '{font_family}' not in registry, using 'monaco'")
            font_family = "monaco"
        
        font_info = FONT_REGISTRY[font_family]
        platform = "darwin" if sys.platform == "darwin" else "linux"
        font_paths = font_info["paths"].get(platform, font_info["paths"].get("linux", []))
        
        # Try each font path in order
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    font = ImageFont.truetype(font_path, size)
                    print(f"[Theme] Loaded {font_info['name']} from {font_path} at size {size}")
                    return font
            except Exception as e:
                print(f"[Theme] Failed to load {font_info['name']} from {font_path}: {e}")
                continue
        
        # Final fallback: ImageFont.load_default() doesn't support size scaling
        print(f"[Theme] WARNING: Could not load {font_info['name']}, falling back to default font (size {size} will NOT be applied)")
        return ImageFont.load_default()
    except Exception as e:
        print(f"[Theme] Error in get_monospace_font: {e}")
        return ImageFont.load_default()


class FalloutTheme:
    """Fallout-style theme configuration."""
    
    def __init__(self):
        # Get font scale from config
        self.font_scale = get_font_scale()
        
        # Always log font scale and sizes for debugging
        print(f"[Theme] Creating theme with font_scale: {self.font_scale:.2f}")
        
        # Calculate scaled font sizes
        self.font_size_large = int(BASE_FONT_SIZE_LARGE * self.font_scale)
        self.font_size_medium = int(BASE_FONT_SIZE_MEDIUM * self.font_scale)
        self.font_size_small = int(BASE_FONT_SIZE_SMALL * self.font_scale)
        self.font_size_tiny = int(BASE_FONT_SIZE_TINY * self.font_scale)
        
        print(f"[Theme] Font sizes - Large: {self.font_size_large}, Medium: {self.font_size_medium}, Small: {self.font_size_small}, Tiny: {self.font_size_tiny}")
        
        # Get padding configuration from config
        padding_config = get_padding_config()
        self.padding_top = padding_config["top"]
        self.padding_bottom = padding_config["bottom"]
        self.padding_left = padding_config["left"]
        self.padding_right = padding_config["right"]
        
        # For backward compatibility, keep self.padding as the left padding (most common use case)
        self.padding = self.padding_left
        
        print(f"[Theme] Padding - Top: {self.padding_top}, Bottom: {self.padding_bottom}, Left: {self.padding_left}, Right: {self.padding_right}")
        
        # Calculate scaled layout constants
        self.line_height_large = int(BASE_LINE_HEIGHT_LARGE * self.font_scale)
        self.line_height_medium = int(BASE_LINE_HEIGHT_MEDIUM * self.font_scale)
        self.line_height_small = int(BASE_LINE_HEIGHT_SMALL * self.font_scale)
        self.line_height_tiny = int(BASE_LINE_HEIGHT_TINY * self.font_scale)
        
        self.colors = {
            "background": COLOR_BLACK,
            "text": COLOR_WHITE,
            "text_secondary": COLOR_GRAY_LIGHT,
            "text_muted": COLOR_GRAY_MEDIUM,
            "accent": COLOR_GRAY_LIGHT,
        }
        # Get font family from config
        self.font_family = get_font_family()
        
        # Create fonts with scaled sizes using selected font family
        font_large = get_monospace_font(self.font_size_large, self.font_family)
        font_medium = get_monospace_font(self.font_size_medium, self.font_family)
        font_small = get_monospace_font(self.font_size_small, self.font_family)
        font_tiny = get_monospace_font(self.font_size_tiny, self.font_family)
        
        # Log actual font sizes (check if font supports size attribute)
        print(f"[Theme] Created fonts - Large: {getattr(font_large, 'size', 'N/A')}, Medium: {getattr(font_medium, 'size', 'N/A')}, Small: {getattr(font_small, 'size', 'N/A')}, Tiny: {getattr(font_tiny, 'size', 'N/A')}")
        
        self.fonts = {
            "large": font_large,
            "medium": font_medium,
            "small": font_small,
            "tiny": font_tiny,
        }
        self.line_heights = {
            "large": self.line_height_large,
            "medium": self.line_height_medium,
            "small": self.line_height_small,
            "tiny": self.line_height_tiny,
        }
    
    def create_image(self) -> Image.Image:
        """Create a new image with theme background."""
        return Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), self.colors["background"])

