"""Weather slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.weather_collector import WeatherCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class WeatherSlideType(SlideType):
    """Weather slide type."""
    
    @property
    def type_name(self) -> str:
        return "weather"
    
    @property
    def display_name(self) -> str:
        return "Weather"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "city",
                    "type": "text",
                    "label": "City",
                    "required": True,
                    "default": "",
                    "placeholder": "e.g., New York",
                    "help": "City name for weather data (weather API uses wttr.in, no API key required)"
                },
                {
                    "name": "temp_unit",
                    "type": "select",
                    "label": "Temperature Unit",
                    "required": False,
                    "default": "C",
                    "options": [
                        {"value": "C", "label": "Celsius (°C)"},
                        {"value": "F", "label": "Fahrenheit (°F)"}
                    ],
                    "help": "Temperature unit for display"
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[WeatherCollector]:
        """Create Weather collector from slide configuration."""
        # Weather collector uses wttr.in which doesn't require API key
        # City is stored in slide config directly (not in service_config)
        # We'll create collector with a default city, but slide.city will override it
        collector_config = {
            "enabled": True,
            "city": "New York",  # Default, will be overridden by slide.city when calling get_data_for_city()
            "poll_interval": 600  # 10 minutes (weather doesn't change that often)
        }
        return WeatherCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Weather slides are not conditional - always show if configured."""
        return collector is not None and data is not None
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Weather slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

