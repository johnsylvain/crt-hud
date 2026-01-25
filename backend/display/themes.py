"""Fallout-style theme for CRT display."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys
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
        return font_scale
    except Exception:
        return 1.0


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


def get_monospace_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Get monospace font for given size.
    Falls back to default font if custom font not available.
    """
    try:
        # Try to load custom pixel font if available
        font_paths = [
            Path(__file__).parent.parent.parent / "data" / "fonts" / "monospace.ttf",
            Path(__file__).parent.parent.parent / "data" / "fonts" / "Courier.ttf",
        ]
        
        for font_path in font_paths:
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), size)
                except Exception:
                    continue
        
        # Fall back to system monospace font
        try:
            if sys.platform == 'darwin':
                return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
            elif sys.platform == 'linux':
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
        except Exception:
            pass
        
        # Final fallback to default font
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


class FalloutTheme:
    """Fallout-style theme configuration."""
    
    def __init__(self):
        # Get font scale from config
        self.font_scale = get_font_scale()
        
        # Calculate scaled font sizes
        self.font_size_large = int(BASE_FONT_SIZE_LARGE * self.font_scale)
        self.font_size_medium = int(BASE_FONT_SIZE_MEDIUM * self.font_scale)
        self.font_size_small = int(BASE_FONT_SIZE_SMALL * self.font_scale)
        self.font_size_tiny = int(BASE_FONT_SIZE_TINY * self.font_scale)
        
        # Calculate scaled layout constants
        self.padding = int(BASE_PADDING * self.font_scale)
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
        self.fonts = {
            "large": get_monospace_font(self.font_size_large),
            "medium": get_monospace_font(self.font_size_medium),
            "small": get_monospace_font(self.font_size_small),
            "tiny": get_monospace_font(self.font_size_tiny),
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

