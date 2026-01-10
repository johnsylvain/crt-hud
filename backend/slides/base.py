"""Abstract base class for slide type implementations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from PIL import Image
from backend.collectors.base import BaseCollector
from backend.display.renderer import SlideRenderer


class SlideType(ABC):
    """Abstract base class for slide type implementations."""
    
    @property
    @abstractmethod
    def type_name(self) -> str:
        """Return the slide type identifier (e.g., 'pihole_summary')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return human-readable name (e.g., 'Pi-hole Stats')."""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return the configuration schema for this slide type.
        
        Returns:
            Dictionary defining config fields with types, defaults, validation rules
        """
        pass
    
    @abstractmethod
    def create_collector(self, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """
        Create and return a collector instance for this slide type.
        
        Args:
            config: Slide-specific configuration dictionary with 'service_config' key
            
        Returns:
            Collector instance or None if this slide type doesn't need data collection
        """
        pass
    
    @abstractmethod
    def should_display(self, collector: Optional[BaseCollector], 
                      data: Optional[Dict[str, Any]], 
                      slide_config: Dict[str, Any]) -> bool:
        """
        Determine if this slide should be displayed based on conditional logic.
        
        Args:
            collector: The collector instance (if any)
            data: The collected data (if any)
            slide_config: Complete slide configuration
            
        Returns:
            True if slide should be displayed, False otherwise
        """
        pass
    
    @abstractmethod
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]], 
               slide_config: Dict[str, Any]) -> Image.Image:
        """
        Render the slide using the provided renderer and data.
        
        Args:
            renderer: The slide renderer instance
            data: Collected data from the collector (if any)
            slide_config: Complete slide configuration including type-specific config
            
        Returns:
            PIL Image object
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate slide configuration.
        
        Args:
            config: Configuration dictionary to validate (contains 'service_config')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = self.get_config_schema()
        service_config = config.get("service_config", {})
        api_config = config.get("api_config", {})
        
        # Validate required fields
        for field_group in schema.get("fields", []):
            if field_group.get("type") == "group":
                # Check if it's service_config or api_config group
                config_dict = service_config if field_group.get("name") == "service_config" else api_config
                
                for field in field_group.get("fields", []):
                    if field.get("required", False):
                        field_name = field.get("name")
                        if not config_dict.get(field_name):
                            return False, f"Field '{field.get('label', field_name)}' is required"
            else:
                # Direct field (like city, temp_unit for weather)
                if field_group.get("required", False):
                    field_name = field_group.get("name")
                    if not config.get(field_name):
                        return False, f"Field '{field_group.get('label', field_name)}' is required"
        
        return True, None
