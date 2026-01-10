"""Pi-hole slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.pihole_collector import PiHoleCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class PiHoleSlideType(SlideType):
    """Pi-hole statistics slide type."""
    
    @property
    def type_name(self) -> str:
        return "pihole_summary"
    
    @property
    def display_name(self) -> str:
        return "Pi-hole Stats"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "Pi-hole Configuration",
                    "fields": [
                        {
                            "name": "api_url",
                            "type": "url",
                            "label": "Pi-hole API URL",
                            "required": True,
                            "default": "http://localhost/admin",
                            "placeholder": "http://localhost/admin",
                            "help": "Base URL for Pi-hole admin interface"
                        },
                        {
                            "name": "api_token",
                            "type": "password",
                            "label": "API Token",
                            "required": False,
                            "default": "",
                            "placeholder": "Enter Pi-hole API token",
                            "help": "Optional API token for authentication"
                        },
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 10,
                            "min": 1,
                            "max": 300,
                            "help": "How often to fetch data from Pi-hole"
                        }
                    ]
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[PiHoleCollector]:
        """Create Pi-hole collector from slide configuration."""
        service_config = config.get("service_config", {})
        if not service_config.get("api_url"):
            return None
        
        collector_config = {
            "enabled": True,
            "api_url": service_config.get("api_url"),
            "api_token": service_config.get("api_token", ""),
            "poll_interval": service_config.get("poll_interval", 10)
        }
        return PiHoleCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Pi-hole slides are not conditional - always show if configured."""
        return collector is not None and data is not None
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Pi-hole slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

