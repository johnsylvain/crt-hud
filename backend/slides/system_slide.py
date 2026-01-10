"""System stats slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.system_collector import SystemCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class SystemSlideType(SlideType):
    """System statistics slide type."""
    
    @property
    def type_name(self) -> str:
        return "system_stats"
    
    @property
    def display_name(self) -> str:
        return "System Stats"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "System Configuration",
                    "fields": [
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 5,
                            "min": 1,
                            "max": 300,
                            "help": "How often to collect system statistics"
                        },
                        {
                            "name": "nas_mounts",
                            "type": "text",
                            "label": "NAS Mount Points",
                            "required": False,
                            "default": "/mnt/nas, /media/nas",
                            "placeholder": "/mnt/nas, /media/nas",
                            "help": "Comma-separated list of mount point paths to monitor. If empty or inaccessible, root filesystem will be used."
                        }
                    ]
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[SystemCollector]:
        """Create System collector from slide configuration."""
        service_config = config.get("service_config", {})
        
        # Parse NAS mounts from comma-separated string
        nas_mounts_str = service_config.get("nas_mounts", "")
        nas_mounts = [m.strip() for m in nas_mounts_str.split(",") if m.strip()] if nas_mounts_str else []
        
        collector_config = {
            "enabled": True,
            "poll_interval": service_config.get("poll_interval", 5),
            "nas_mounts": nas_mounts
        }
        return SystemCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """System slides are not conditional - always show if configured."""
        return collector is not None and data is not None
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render System slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

