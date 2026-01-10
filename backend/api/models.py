"""Data models for API requests and responses."""

from typing import Optional, List, Dict, Any


class Slide:
    """Slide model with per-slide configuration."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.type = data.get("type")
        self.title = data.get("title", "")
        self.duration = data.get("duration", 10)  # Display duration
        self.refresh_duration = data.get("refresh_duration", 5)  # How often to refresh data
        self.order = data.get("order", 0)
        self.conditional = data.get("conditional", False)
        
        # Per-slide service configuration (NEW)
        self.service_config = data.get("service_config", {})
        
        # Slide-specific fields
        self.city = data.get("city")  # Weather
        self.temp_unit = data.get("temp_unit", "C")  # Weather
        self.image_path = data.get("image_path")  # Image
        self.text = data.get("text")  # Static Text
        self.font_size = data.get("font_size", "medium")  # Static Text
        self.text_align = data.get("text_align", "left")  # Static Text
        self.vertical_align = data.get("vertical_align", "center")  # Static Text
        self.text_color = data.get("text_color", "text")  # Static Text
        
        # Custom slide fields
        self.widgets = data.get("widgets", [])
        self.layout = data.get("layout", {})
        self.api_config = data.get("api_config")  # For custom slides with generic API
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert slide to dictionary."""
        result = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "duration": self.duration,
            "refresh_duration": self.refresh_duration,
            "order": self.order,
            "conditional": self.conditional,
        }
        
        # Include service_config if present
        if self.service_config:
            result["service_config"] = self.service_config
        
        # Include type-specific fields
        if self.city:
            result["city"] = self.city
        if self.temp_unit != "C":
            result["temp_unit"] = self.temp_unit
        if self.image_path:
            result["image_path"] = self.image_path
        if self.text:
            result["text"] = self.text
            result["font_size"] = self.font_size
            result["text_align"] = self.text_align
            result["vertical_align"] = self.vertical_align
            result["text_color"] = self.text_color
        
        # Custom slide fields
        if self.widgets:
            result["widgets"] = self.widgets
        if self.layout:
            result["layout"] = self.layout
        if self.api_config:
            result["api_config"] = self.api_config
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slide":
        """Create slide from dictionary."""
        return cls(data)


class APIConfig:
    """API configuration model."""
    
    def __init__(self, data: Dict[str, Any]):
        self.arm = data.get("arm", {})
        self.pihole = data.get("pihole", {})
        self.plex = data.get("plex", {})
        self.system = data.get("system", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "arm": self.arm,
            "pihole": self.pihole,
            "plex": self.plex,
            "system": self.system,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIConfig":
        """Create config from dictionary."""
        return cls(data)

