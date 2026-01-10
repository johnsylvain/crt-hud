"""Image slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class ImageSlideType(SlideType):
    """Image slide type."""
    
    @property
    def type_name(self) -> str:
        return "image"
    
    @property
    def display_name(self) -> str:
        return "Image"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                # Note: image_path is handled separately via image select/upload UI in the frontend
                # We don't include it here to avoid duplicate file input
            ],
            "conditional": False,
            "default_conditional": False,
            "note": "Use the image select/upload controls above to choose an image. Images will be displayed in black and white with dithering."
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """Image slides don't need a collector."""
        return None
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Image slides are not conditional - always show if image path exists."""
        return bool(slide_config.get("image_path"))
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Image slide using the renderer."""
        return renderer.render(
            self.type_name,
            None,  # Images don't use data
            slide_config.get("title", ""),
            slide_config
        )

