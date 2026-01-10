"""Clock slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class ClockSlideType(SlideType):
    """Clock slide type - displays current time and optionally date."""
    
    @property
    def type_name(self) -> str:
        return "clock"
    
    @property
    def display_name(self) -> str:
        return "Clock"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "time_format",
                    "type": "select",
                    "label": "Time Format",
                    "required": False,
                    "default": "24h",
                    "options": [
                        {"value": "12h", "label": "12-hour (AM/PM)"},
                        {"value": "24h", "label": "24-hour"}
                    ],
                    "help": "Time display format"
                },
                {
                    "name": "show_date",
                    "type": "checkbox",
                    "label": "Show Date",
                    "required": False,
                    "default": True,
                    "help": "Display the current date below the time"
                },
                {
                    "name": "date_format",
                    "type": "select",
                    "label": "Date Format",
                    "required": False,
                    "default": "full",
                    "options": [
                        {"value": "full", "label": "Full (e.g., Monday, January 1, 2024)"},
                        {"value": "short", "label": "Short (e.g., Mon, Jan 1, 2024)"},
                        {"value": "numeric", "label": "Numeric (e.g., 2024-01-01)"},
                        {"value": "month_day", "label": "Month Day (e.g., January 1)"}
                    ],
                    "help": "Date display format (only used if Show Date is enabled)"
                },
                {
                    "name": "font_size",
                    "type": "select",
                    "label": "Time Font Size",
                    "required": False,
                    "default": "large",
                    "options": [
                        {"value": "small", "label": "Small"},
                        {"value": "medium", "label": "Medium"},
                        {"value": "large", "label": "Large"}
                    ],
                    "help": "Font size for the time display"
                },
                {
                    "name": "time_align",
                    "type": "select",
                    "label": "Time Alignment",
                    "required": False,
                    "default": "center",
                    "options": [
                        {"value": "left", "label": "Left"},
                        {"value": "center", "label": "Center"},
                        {"value": "right", "label": "Right"}
                    ],
                    "help": "Horizontal alignment for the time"
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
                    ],
                    "help": "Vertical alignment for the clock display"
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """Clock slides don't need a collector - time is obtained at render time."""
        return None
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Clock slides are always displayed."""
        return True
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Clock slide using the renderer."""
        return renderer.render(
            self.type_name,
            None,  # Clock doesn't use data from collector
            slide_config.get("title", ""),
            slide_config
        )

