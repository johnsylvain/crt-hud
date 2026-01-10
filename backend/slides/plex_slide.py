"""Plex slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.plex_collector import PlexCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class PlexSlideType(SlideType):
    """Plex now playing slide type."""
    
    @property
    def type_name(self) -> str:
        return "plex_now_playing"
    
    @property
    def display_name(self) -> str:
        return "Plex Now Playing"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "Plex Configuration",
                    "fields": [
                        {
                            "name": "api_url",
                            "type": "url",
                            "label": "Plex Server URL",
                            "required": True,
                            "default": "http://localhost:32400",
                            "placeholder": "http://localhost:32400",
                            "help": "Base URL for Plex Media Server"
                        },
                        {
                            "name": "api_token",
                            "type": "password",
                            "label": "Plex Token",
                            "required": True,
                            "default": "",
                            "placeholder": "Enter Plex authentication token",
                            "help": "Required for accessing Plex API"
                        },
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 5,
                            "min": 1,
                            "max": 60,
                            "help": "How often to check for active streams (lower = more real-time)"
                        }
                    ]
                }
            ],
            "conditional": True,
            "default_conditional": True
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[PlexCollector]:
        """Create Plex collector from slide configuration."""
        service_config = config.get("service_config", {})
        if not service_config.get("api_url") or not service_config.get("api_token"):
            return None
        
        collector_config = {
            "enabled": True,
            "api_url": service_config.get("api_url"),
            "api_token": service_config.get("api_token"),
            "poll_interval": service_config.get("poll_interval", 5)
        }
        return PlexCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Plex slides are conditional - only show if there are active streams."""
        if not slide_config.get("conditional", True):
            return True  # Always show if not conditional
        
        # Check if there are active streams
        if data is None:
            return False
        
        session_count = data.get("session_count", 0)
        return session_count > 0
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Plex slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

