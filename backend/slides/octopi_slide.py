"""OctoPi slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.octopi_collector import OctoPiCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class OctoPiSlideType(SlideType):
    """OctoPi print status slide type."""
    
    @property
    def type_name(self) -> str:
        return "octopi_print_status"
    
    @property
    def display_name(self) -> str:
        return "OctoPi Print Status"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "OctoPrint Configuration",
                    "fields": [
                        {
                            "name": "api_url",
                            "type": "url",
                            "label": "OctoPrint Server URL",
                            "required": True,
                            "default": "http://octopi.local",
                            "placeholder": "http://octopi.local",
                            "help": "Base URL for OctoPrint server"
                        },
                        {
                            "name": "api_key",
                            "type": "password",
                            "label": "API Key",
                            "required": True,
                            "default": "",
                            "placeholder": "Enter OctoPrint API key",
                            "help": "API key for authentication (required). Get it from OctoPrint Settings > API > Generate new API key"
                        },
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 5,
                            "min": 1,
                            "max": 60,
                            "help": "How often to check print status"
                        }
                    ]
                }
            ],
            "conditional": True,
            "default_conditional": True
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[OctoPiCollector]:
        """Create OctoPi collector from slide configuration."""
        service_config = config.get("service_config", {})
        if not service_config.get("api_url"):
            return None
        
        collector_config = {
            "enabled": True,
            "api_url": service_config.get("api_url"),
            "api_key": service_config.get("api_key", ""),
            "poll_interval": service_config.get("poll_interval", 5)
        }
        return OctoPiCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """OctoPi slides are conditional - only show if there is an active print."""
        if not slide_config.get("conditional", True):
            return True  # Always show if not conditional
        
        # Check if there is an active print
        if data is None:
            return False
        
        is_printing = data.get("is_printing", False)
        return is_printing
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render OctoPi slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )
