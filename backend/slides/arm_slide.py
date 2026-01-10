"""ARM (Automatic Ripping Machine) slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.arm_collector import ARMCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class ARMSlideType(SlideType):
    """ARM rip progress slide type."""
    
    @property
    def type_name(self) -> str:
        return "arm_rip_progress"
    
    @property
    def display_name(self) -> str:
        return "ARM Rip Progress"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "ARM Configuration",
                    "fields": [
                        {
                            "name": "api_url",
                            "type": "url",
                            "label": "ARM API URL",
                            "required": True,
                            "default": "http://localhost:8080",
                            "placeholder": "http://localhost:8080",
                            "help": "Base URL for ARM web interface"
                        },
                        {
                            "name": "api_key",
                            "type": "password",
                            "label": "API Key",
                            "required": False,
                            "default": "",
                            "placeholder": "Enter ARM API key (if required)",
                            "help": "Optional API key for authentication"
                        },
                        {
                            "name": "endpoint",
                            "type": "text",
                            "label": "API Endpoint",
                            "required": False,
                            "default": "/json?mode=joblist",
                            "placeholder": "/json?mode=joblist",
                            "help": "API endpoint path for job list"
                        },
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 30,
                            "min": 1,
                            "max": 300,
                            "help": "How often to check for active rips"
                        }
                    ]
                }
            ],
            "conditional": True,
            "default_conditional": True
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[ARMCollector]:
        """Create ARM collector from slide configuration."""
        service_config = config.get("service_config", {})
        if not service_config.get("api_url"):
            return None
        
        collector_config = {
            "enabled": True,
            "api_url": service_config.get("api_url"),
            "api_key": service_config.get("api_key", ""),
            "endpoint": service_config.get("endpoint", "/json?mode=joblist"),
            "poll_interval": service_config.get("poll_interval", 30)
        }
        return ARMCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """ARM slides are conditional - only show if there's an active rip."""
        if not slide_config.get("conditional", True):
            return True  # Always show if not conditional
        
        # ARM collector returns None if no active jobs
        # If data exists, it means there's an active rip
        return data is not None
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render ARM slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

