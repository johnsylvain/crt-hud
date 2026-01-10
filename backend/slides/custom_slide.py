"""Custom slide type implementation."""

from typing import Dict, Any, Optional
from PIL import Image
from .base import SlideType
from backend.collectors.generic_collector import GenericCollector
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class CustomSlideType(SlideType):
    """Custom widget slide type."""
    
    @property
    def type_name(self) -> str:
        return "custom"
    
    @property
    def display_name(self) -> str:
        return "Custom Widget"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "api_config",
                    "type": "group",
                    "label": "API Configuration (Optional)",
                    "fields": [
                        {
                            "name": "endpoint",
                            "type": "url",
                            "label": "Endpoint URL",
                            "required": False,
                            "default": "",
                            "placeholder": "https://api.example.com/data",
                            "help": "API endpoint URL for fetching data"
                        },
                        {
                            "name": "method",
                            "type": "select",
                            "label": "HTTP Method",
                            "required": False,
                            "default": "GET",
                            "options": [
                                {"value": "GET", "label": "GET"},
                                {"value": "POST", "label": "POST"},
                                {"value": "PUT", "label": "PUT"},
                                {"value": "DELETE", "label": "DELETE"}
                            ]
                        },
                        {
                            "name": "headers",
                            "type": "textarea",
                            "label": "Headers (JSON)",
                            "required": False,
                            "default": "{}",
                            "rows": 3,
                            "placeholder": '{"Authorization": "Bearer token"}',
                            "help": "HTTP headers as JSON object"
                        },
                        {
                            "name": "body",
                            "type": "textarea",
                            "label": "Request Body (JSON, for POST/PUT)",
                            "required": False,
                            "default": "",
                            "rows": 3,
                            "placeholder": '{"key": "value"}',
                            "help": "Request body for POST/PUT requests"
                        },
                        {
                            "name": "data_path",
                            "type": "text",
                            "label": "Data Path (JSONPath)",
                            "required": False,
                            "default": "$",
                            "placeholder": "$",
                            "help": "JSONPath expression to extract data from response"
                        },
                        {
                            "name": "refresh_interval",
                            "type": "number",
                            "label": "Refresh Interval (seconds)",
                            "required": False,
                            "default": 30,
                            "min": 5,
                            "max": 300,
                            "help": "How often to fetch data from API"
                        }
                    ]
                }
            ],
            "conditional": False,
            "default_conditional": False,
            "note": "Custom slides use widgets defined in the widget designer. API configuration is optional - slides can use static/test data."
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[GenericCollector]:
        """Create Generic collector from slide configuration."""
        # For custom slides, api_config is at root level, not in service_config
        api_config = config.get("api_config")
        if not api_config or not api_config.get("endpoint"):
            return None
        
        # Convert api_config format to generic collector format
        collector_config = {
            "endpoint": api_config.get("endpoint"),
            "method": api_config.get("method", "GET"),
            "headers": api_config.get("headers", {}),
            "body": api_config.get("body"),
            "data_path": api_config.get("data_path", "$"),
            "refresh_interval": api_config.get("refresh_interval", 30),
            "enabled": True
        }
        
        return GenericCollector(collector_config)
    
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """Custom slides are not conditional - always show if widgets are defined."""
        widgets = slide_config.get("widgets", [])
        return len(widgets) > 0
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
               slide_config: Dict[str, Any]) -> Image.Image:
        """Render Custom slide using the renderer."""
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )

