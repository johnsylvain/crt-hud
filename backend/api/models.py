"""Data models for API requests and responses."""

from typing import Optional, List, Dict, Any


class Slide:
    """Slide model."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.type = data.get("type")
        self.title = data.get("title", "")
        self.duration = data.get("duration", 10)  # Display duration (backwards compatible)
        self.refresh_duration = data.get("refresh_duration", 5)  # How often to refresh data
        self.order = data.get("order", 0)
        self.conditional = data.get("conditional", False)
        # condition_type is deprecated - conditional now means "hide if no data for this slide"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert slide to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "duration": self.duration,
            "refresh_duration": self.refresh_duration,
            "order": self.order,
            "conditional": self.conditional,
        }
    
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

