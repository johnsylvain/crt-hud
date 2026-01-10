"""Fallout-style theme for CRT display."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

# Fallout color palette (monochrome for CRT)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY_LIGHT = (200, 200, 200)
COLOR_GRAY_MEDIUM = (128, 128, 128)
COLOR_GRAY_DARK = (64, 64, 64)

# Display dimensions
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 280

# Font settings - increased for better readability on CRT
FONT_SIZE_LARGE = 22
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL = 16
FONT_SIZE_TINY = 14

# Layout constants - adjusted for larger fonts
PADDING = 8
LINE_HEIGHT_LARGE = 28
LINE_HEIGHT_MEDIUM = 22
LINE_HEIGHT_SMALL = 20
LINE_HEIGHT_TINY = 18


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
        self.colors = {
            "background": COLOR_BLACK,
            "text": COLOR_WHITE,
            "text_secondary": COLOR_GRAY_LIGHT,
            "text_muted": COLOR_GRAY_MEDIUM,
            "accent": COLOR_GRAY_LIGHT,
        }
        self.fonts = {
            "large": get_monospace_font(FONT_SIZE_LARGE),
            "medium": get_monospace_font(FONT_SIZE_MEDIUM),
            "small": get_monospace_font(FONT_SIZE_SMALL),
            "tiny": get_monospace_font(FONT_SIZE_TINY),
        }
        self.line_heights = {
            "large": LINE_HEIGHT_LARGE,
            "medium": LINE_HEIGHT_MEDIUM,
            "small": LINE_HEIGHT_SMALL,
            "tiny": LINE_HEIGHT_TINY,
        }
    
    def create_image(self) -> Image.Image:
        """Create a new image with theme background."""
        return Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), self.colors["background"])

