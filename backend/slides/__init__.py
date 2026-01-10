"""Slide type implementations."""

from .registry import SlideTypeRegistry
from .pihole_slide import PiHoleSlideType
from .plex_slide import PlexSlideType
from .arm_slide import ARMSlideType
from .system_slide import SystemSlideType
from .weather_slide import WeatherSlideType
from .image_slide import ImageSlideType
from .static_text_slide import StaticTextSlideType
from .custom_slide import CustomSlideType
from .clock_slide import ClockSlideType

# Register all slide types
SlideTypeRegistry.register(PiHoleSlideType)
SlideTypeRegistry.register(PlexSlideType)
SlideTypeRegistry.register(ARMSlideType)
SlideTypeRegistry.register(SystemSlideType)
SlideTypeRegistry.register(WeatherSlideType)
SlideTypeRegistry.register(ImageSlideType)
SlideTypeRegistry.register(StaticTextSlideType)
SlideTypeRegistry.register(CustomSlideType)
SlideTypeRegistry.register(ClockSlideType)

__all__ = [
    'SlideTypeRegistry',
    'PiHoleSlideType',
    'PlexSlideType',
    'ARMSlideType',
    'SystemSlideType',
    'WeatherSlideType',
    'ImageSlideType',
    'StaticTextSlideType',
    'CustomSlideType',
    'ClockSlideType',
]