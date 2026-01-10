"""Registry for slide type implementations."""

from typing import Dict, Type, List, Optional
from .base import SlideType


class SlideTypeRegistry:
    """Registry for slide type implementations."""
    
    _types: Dict[str, Type[SlideType]] = {}
    
    @classmethod
    def register(cls, slide_type: Type[SlideType]):
        """Register a slide type class."""
        instance = slide_type()
        cls._types[instance.type_name] = slide_type
    
    @classmethod
    def get(cls, type_name: str) -> Optional[SlideType]:
        """Get a slide type instance by name."""
        if type_name not in cls._types:
            return None
        return cls._types[type_name]()
    
    @classmethod
    def list_all(cls) -> List[SlideType]:
        """List all registered slide types."""
        return [cls() for cls in cls._types.values()]
    
    @classmethod
    def get_all_types(cls) -> Dict[str, str]:
        """Get dictionary of type_name -> display_name for all registered types."""
        return {
            cls().type_name: cls().display_name
            for cls in cls._types.values()
        }
