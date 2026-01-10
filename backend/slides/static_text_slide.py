"""Static text slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class StaticTextSlideType(SlideType):
    """Static text slide type."""
    
    @property
    def type_name(self) -> str:
        return "static_text"
    
    @property
    def display_name(self) -> str:
        return "Static Text"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "text",
                    "type": "textarea",
                    "label": "Text Content",
                    "required": True,
                    "default": "",
                    "rows": 4,
                    "placeholder": "Enter text content (multi-line supported)",
                    "help": "Enter the text to display. Multiple lines are supported."
                },
                {
                    "name": "font_size",
                    "type": "select",
                    "label": "Font Size",
                    "required": False,
                    "default": "medium",
                    "options": [
                        {"value": "small", "label": "Small"},
                        {"value": "medium", "label": "Medium"},
                        {"value": "large", "label": "Large"}
                    ],
                    "help": "Font size for the text"
                },
                {
                    "name": "text_align",
                    "type": "select",
                    "label": "Horizontal Alignment",
                    "required": False,
                    "default": "left",
                    "options": [
                        {"value": "left", "label": "Left"},
                        {"value": "center", "label": "Center"},
                        {"value": "right", "label": "Right"}
                    ]
                },
                {
                    "name": "vertical_align",
                    "type": "select",
                    "label": "Vertical Alignment",
                    "required": False,
                    "default": "center",
                    "options": [
                        {"value": "top", "label": "Top"},
                        {"value": "center", "label": "Center"},
                        {"value": "bottom", "label": "Bottom"}
                    ]
                },
                {
                    "name": "text_color",
                    "type": "select",
                    "label": "Text Color",
                    "required": False,
                    "default": "text",
                    "options": [
                        {"value": "text", "label": "White (Primary)"},
                        {"value": "text_secondary", "label": "Gray (Secondary)"},
                        {"value": "text_muted", "label": "Dark Gray (Muted)"}
                    ]
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """Static text slides don't need a collector."""
        return None
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Static text slides are not conditional - always show if text exists."""
        return bool(slide_config.get("text"))
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Static Text slide using the renderer."""
        return renderer.render(
            self.type_name,
            None,  # Static text doesn't use data
            slide_config.get("title", ""),
            slide_config
        )

