# Slide Type Refactoring Plan: Per-Slide Configuration Architecture

## Overview

Refactor the application to move service-specific configurations (ARM, Pi-hole, Plex, System) from the global Config tab into each individual slide's Edit/New dialog. Implement an abstract class pattern so each slide type defines its own configuration schema, data collection, and rendering logic.

## Current Architecture Issues

1. **Global Configuration**: Service configs (ARM, Pi-hole, Plex, System) are stored globally in `data/api_config.json` and managed through a single Config tab
2. **Tight Coupling**: Slides reference global collectors initialized at app startup
3. **Hardcoded Logic**: Slide type handling is scattered across `app.py`, `routes.py`, and `renderer.py` with if/elif chains
4. **Limited Flexibility**: Each slide of the same type shares the same configuration - can't have multiple ARM slides with different endpoints

## Target Architecture

### Core Principles

1. **Per-Slide Configuration**: Each slide instance stores its own service configuration
2. **Self-Contained Slide Types**: Each slide type defines its configuration schema, data collection, and rendering
3. **Abstract Base Classes**: Use abstract classes to define contracts for slide types, collectors, and renderers
4. **Factory Pattern**: Use factories to instantiate collectors and renderers based on slide configuration
5. **Backward Compatibility**: Support migration from global config to per-slide config

## Architecture Components

### 1. Abstract Slide Type Interface

```python
# backend/slides/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
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
            Example:
            {
                "fields": [
                    {
                        "name": "api_url",
                        "type": "url",
                        "label": "API URL",
                        "required": True,
                        "default": "http://localhost:8080",
                        "placeholder": "http://localhost:8080"
                    },
                    {
                        "name": "api_key",
                        "type": "password",
                        "label": "API Key",
                        "required": False,
                        "default": ""
                    },
                    {
                        "name": "poll_interval",
                        "type": "number",
                        "label": "Poll Interval (seconds)",
                        "required": False,
                        "default": 30,
                        "min": 1,
                        "max": 300
                    }
                ],
                "conditional": True,  # Whether this slide type supports conditional display
                "default_conditional": False  # Default conditional value
            }
        """
        pass
    
    @abstractmethod
    def create_collector(self, config: Dict[str, Any]) -> Optional[BaseCollector]:
        """
        Create and return a collector instance for this slide type.
        
        Args:
            config: Slide-specific configuration dictionary
            
        Returns:
            Collector instance or None if this slide type doesn't need data collection
        """
        pass
    
    @abstractmethod
    def should_display(self, collector: Optional[BaseCollector], data: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if this slide should be displayed based on conditional logic.
        
        Args:
            collector: The collector instance (if any)
            data: The collected data (if any)
            
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
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = self.get_config_schema()
        # Default validation logic
        # Can be overridden by specific slide types
        return True, None
```

### 2. Slide Type Registry

```python
# backend/slides/registry.py
from typing import Dict, Type
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
```

### 3. Slide Type Implementations

Each slide type will implement the `SlideType` abstract class:

```python
# backend/slides/pihole_slide.py
from .base import SlideType
from backend.collectors.pihole_collector import PiHoleCollector
from typing import Dict, Any, Optional
from PIL import Image

class PiHoleSlideType(SlideType):
    """Pi-hole statistics slide type."""
    
    @property
    def type_name(self) -> str:
        return "pihole_summary"
    
    @property
    def display_name(self) -> str:
        return "Pi-hole Stats"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "name": "service_config",
                    "type": "group",
                    "label": "Pi-hole Configuration",
                    "fields": [
                        {
                            "name": "api_url",
                            "type": "url",
                            "label": "Pi-hole API URL",
                            "required": True,
                            "default": "http://localhost/admin",
                            "placeholder": "http://localhost/admin",
                            "help": "Base URL for Pi-hole admin interface"
                        },
                        {
                            "name": "api_token",
                            "type": "password",
                            "label": "API Token",
                            "required": False,
                            "default": "",
                            "placeholder": "Enter Pi-hole API token",
                            "help": "Optional API token for authentication"
                        },
                        {
                            "name": "poll_interval",
                            "type": "number",
                            "label": "Poll Interval (seconds)",
                            "required": False,
                            "default": 10,
                            "min": 1,
                            "max": 300,
                            "help": "How often to fetch data from Pi-hole"
                        }
                    ]
                }
            ],
            "conditional": False,
            "default_conditional": False
        }
    
    def create_collector(self, config: Dict[str, Any]) -> Optional[PiHoleCollector]:
        service_config = config.get("service_config", {})
        if not service_config.get("api_url"):
            return None
        
        collector_config = {
            "enabled": True,
            "api_url": service_config.get("api_url"),
            "api_token": service_config.get("api_token", ""),
            "poll_interval": service_config.get("poll_interval", 10)
        }
        return PiHoleCollector(collector_config)
    
    def should_display(self, collector: Optional[PiHoleCollector], 
                      data: Optional[Dict[str, Any]]) -> bool:
        # Pi-hole slides are not conditional - always show if configured
        return collector is not None and data is not None
    
    def render(self, renderer: SlideRenderer, data: Optional[Dict[str, Any]],
              slide_config: Dict[str, Any]) -> Image.Image:
        return renderer.render(
            self.type_name,
            data,
            slide_config.get("title", ""),
            slide_config
        )
```

Similar implementations for:
- `PlexSlideType` (with conditional support)
- `ARMSlideType` (with conditional support)
- `SystemSlideType` (with NAS mounts config)
- `WeatherSlideType` (with city/temp_unit already in slide config)
- `ImageSlideType` (no collector needed)
- `StaticTextSlideType` (no collector needed)
- `CustomSlideType` (uses generic collector with api_config)

### 4. Slide Model Updates

```python
# backend/api/models.py
class Slide:
    """Slide model with per-slide configuration."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.type = data.get("type")
        self.title = data.get("title", "")
        self.duration = data.get("duration", 10)
        self.refresh_duration = data.get("refresh_duration", 5)
        self.order = data.get("order", 0)
        self.conditional = data.get("conditional", False)
        
        # Per-slide service configuration (NEW)
        # Structure depends on slide type
        self.service_config = data.get("service_config", {})
        
        # Slide-specific fields (existing)
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
```

### 5. Collector Management

Instead of global collectors, create collectors on-demand per slide:

```python
# app.py (updated)
class HomelabHUD:
    def __init__(self, ...):
        # Remove global collectors dictionary
        # Instead, create collectors per slide when needed
        
    def _get_collector_for_slide(self, slide: dict) -> Optional[BaseCollector]:
        """Get or create a collector instance for a specific slide."""
        slide_type_name = slide.get("type")
        slide_type = SlideTypeRegistry.get(slide_type_name)
        
        if not slide_type:
            return None
        
        # Get service config from slide
        service_config = slide.get("service_config", {})
        if not service_config:
            return None
        
        # Create collector using slide type
        collector = slide_type.create_collector({
            "service_config": service_config
        })
        
        return collector
```

### 6. Frontend: Slide Modal Updates

The slide Edit/New modal will dynamically render configuration fields based on the selected slide type:

```javascript
// frontend/static/js/app.js

// When slide type changes, load its configuration schema
async function loadSlideTypeConfig(typeName) {
    const response = await fetch(`${API_BASE}/slides/types/${typeName}/schema`);
    const schema = await response.json();
    renderSlideConfigFields(schema);
}

function renderSlideConfigFields(schema) {
    const container = document.getElementById('slideServiceConfig');
    
    // Clear existing service config fields
    container.innerHTML = '';
    
    // Render fields based on schema
    schema.fields.forEach(fieldGroup => {
        if (fieldGroup.type === 'group') {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'service-config-group';
            groupDiv.innerHTML = `<h4>${fieldGroup.label}</h4>`;
            
            fieldGroup.fields.forEach(field => {
                const fieldDiv = createConfigFieldElement(field);
                groupDiv.appendChild(fieldDiv);
            });
            
            container.appendChild(groupDiv);
        } else {
            const fieldDiv = createConfigFieldElement(fieldGroup);
            container.appendChild(fieldDiv);
        }
    });
    
    // Update conditional checkbox visibility
    const conditionalCheckbox = document.getElementById('slideConditional');
    const conditionalContainer = conditionalCheckbox.closest('div');
    conditionalContainer.style.display = schema.conditional ? 'block' : 'none';
}

function createConfigFieldElement(field) {
    const div = document.createElement('div');
    div.className = 'config-field';
    
    const label = document.createElement('label');
    label.textContent = field.label;
    if (field.required) {
        label.classList.add('required');
    }
    
    let input;
    switch (field.type) {
        case 'url':
        case 'text':
            input = document.createElement('input');
            input.type = field.type === 'url' ? 'url' : 'text';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.placeholder = field.placeholder || '';
            break;
        case 'password':
            input = document.createElement('input');
            input.type = 'password';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.placeholder = field.placeholder || '';
            break;
        case 'number':
            input = document.createElement('input');
            input.type = 'number';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.min = field.min || '';
            input.max = field.max || '';
            break;
        // ... other field types
    }
    
    if (field.help) {
        const helpText = document.createElement('small');
        helpText.textContent = field.help;
        helpText.className = 'field-help';
        div.appendChild(label);
        div.appendChild(input);
        div.appendChild(helpText);
    } else {
        div.appendChild(label);
        div.appendChild(input);
    }
    
    return div;
}

// When saving slide, include service_config
async function handleSlideSubmit(e) {
    // ... existing code ...
    
    const slideType = document.getElementById('slideType').value;
    const slideTypeSchema = await loadSlideTypeSchema(slideType);
    
    // Collect service config from form
    const serviceConfig = {};
    slideTypeSchema.fields.forEach(fieldGroup => {
        if (fieldGroup.type === 'group') {
            fieldGroup.fields.forEach(field => {
                const input = document.getElementById(`serviceConfig_${field.name}`);
                if (input) {
                    serviceConfig[field.name] = field.type === 'number' 
                        ? parseInt(input.value) || field.default 
                        : input.value.trim();
                }
            });
        }
    });
    
    if (Object.keys(serviceConfig).length > 0) {
        formData.service_config = serviceConfig;
    }
    
    // ... rest of save logic ...
}
```

### 7. API Routes Updates

```python
# backend/api/routes.py

@app.route("/api/slides/types/<type_name>/schema", methods=["GET"])
def get_slide_type_schema(type_name: str):
    """Get configuration schema for a slide type."""
    slide_type = SlideTypeRegistry.get(type_name)
    if not slide_type:
        return jsonify({"error": f"Unknown slide type: {type_name}"}), 404
    
    schema = slide_type.get_config_schema()
    return jsonify(schema)

@app.route("/api/slides/<int:slide_id>/preview", methods=["GET"])
def preview_slide(slide_id):
    """Generate preview using per-slide configuration."""
    # ... existing code ...
    
    slide_type = SlideTypeRegistry.get(slide_type_name)
    if not slide_type:
        return jsonify({"error": "Unknown slide type"}), 400
    
    # Create collector using slide's service_config
    collector = slide_type.create_collector({
        "service_config": slide.get("service_config", {})
    })
    
    # Get data
    data = collector.get_data() if collector else None
    
    # Render using slide type
    image = slide_type.render(renderer, data, slide)
    
    # ... rest of preview logic ...
```

## Migration Strategy

### Phase 1: Add Per-Slide Config Support (Backward Compatible)

1. Update `Slide` model to support `service_config` field
2. Add abstract `SlideType` base class
3. Implement slide types for existing types (Pi-hole, Plex, ARM, System)
4. Update frontend to show service config fields in slide modal
5. **Keep global config as fallback** - if slide doesn't have `service_config`, use global config

### Phase 2: Update All Slides to Use Per-Slide Config

1. Migration script to copy global config to each slide's `service_config`
2. Update existing slides in `data/slides.json`
3. Test each slide type independently

### Phase 3: Remove Global Config

1. Remove global collectors initialization
2. Remove Config tab (or repurpose for application-wide settings like display resolution, theme, etc.)
3. Update all references to use per-slide collectors

### Phase 4: Refactor Renderer

1. Move slide-specific rendering logic into slide type classes
2. Update renderer to use slide type's `render()` method
3. Remove hardcoded if/elif chains from renderer

## Benefits

1. **Flexibility**: Multiple slides of same type with different configurations
2. **Self-Contained**: Each slide is independent and portable
3. **Extensibility**: Easy to add new slide types by implementing `SlideType`
4. **Maintainability**: Clear separation of concerns
5. **Testability**: Each slide type can be tested independently
6. **User Experience**: Configure each slide individually in its own dialog

## Files to Create

1. `backend/slides/__init__.py`
2. `backend/slides/base.py` - Abstract SlideType class
3. `backend/slides/registry.py` - Slide type registry
4. `backend/slides/pihole_slide.py`
5. `backend/slides/plex_slide.py`
6. `backend/slides/arm_slide.py`
7. `backend/slides/system_slide.py`
8. `backend/slides/weather_slide.py`
9. `backend/slides/image_slide.py`
10. `backend/slides/static_text_slide.py`
11. `backend/slides/custom_slide.py`

## Files to Modify

1. `backend/api/models.py` - Update Slide model
2. `backend/api/routes.py` - Add schema endpoint, update preview/current slide routes
3. `app.py` - Remove global collectors, use per-slide collectors
4. `frontend/static/js/app.js` - Dynamic config field rendering
5. `frontend/templates/index.html` - Add service config container to slide modal
6. `backend/display/renderer.py` - Update to use slide types (Phase 4)
7. `config.py` - Keep global config during migration, remove later

## Configuration Schema Examples

### Pi-hole Slide Config Schema
```json
{
  "fields": [
    {
      "name": "service_config",
      "type": "group",
      "label": "Pi-hole Configuration",
      "fields": [
        {
          "name": "api_url",
          "type": "url",
          "label": "Pi-hole API URL",
          "required": true,
          "default": "http://localhost/admin"
        },
        {
          "name": "api_token",
          "type": "password",
          "label": "API Token",
          "required": false
        },
        {
          "name": "poll_interval",
          "type": "number",
          "label": "Poll Interval (seconds)",
          "default": 10,
          "min": 1,
          "max": 300
        }
      ]
    }
  ],
  "conditional": false
}
```

### Plex Slide Config Schema
```json
{
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
          "required": true,
          "default": "http://localhost:32400"
        },
        {
          "name": "api_token",
          "type": "password",
          "label": "Plex Token",
          "required": true
        },
        {
          "name": "poll_interval",
          "type": "number",
          "label": "Poll Interval (seconds)",
          "default": 5,
          "min": 1,
          "max": 60
        }
      ]
    }
  ],
  "conditional": true,
  "default_conditional": true
}
```

### System Slide Config Schema
```json
{
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
          "default": 5,
          "min": 1,
          "max": 300
        },
        {
          "name": "nas_mounts",
          "type": "text",
          "label": "NAS Mount Points",
          "default": "/mnt/nas, /media/nas",
          "help": "Comma-separated list of mount point paths"
        }
      ]
    }
  ],
  "conditional": false
}
```

## Implementation Order

1. **Week 1: Foundation**
   - Create abstract base classes and registry
   - Implement one slide type (Pi-hole) as proof of concept
   - Update Slide model to support service_config

2. **Week 2: Core Types**
   - Implement Plex, ARM, System slide types
   - Add schema endpoint to API
   - Update frontend to load and render config schemas

3. **Week 3: Migration**
   - Create migration script
   - Update existing slides to use service_config
   - Test backward compatibility

4. **Week 4: Remaining Types**
   - Implement Weather, Image, StaticText, Custom slide types
   - Remove global collector initialization
   - Update renderer to use slide types (optional, can defer)

5. **Week 5: Cleanup**
   - Remove Config tab or repurpose it
   - Remove global config file usage
   - Documentation and testing

## Testing Strategy

1. **Unit Tests**: Test each slide type's config validation, collector creation, rendering
2. **Integration Tests**: Test slide creation, editing, preview with various configurations
3. **Migration Tests**: Verify existing slides work after migration
4. **Edge Cases**: Multiple slides of same type with different configs, missing configs, invalid configs

## Backward Compatibility Notes

- During migration phase, if a slide doesn't have `service_config`, fall back to global config
- Global config tab remains during migration
- Old slides continue to work without changes
- Migration can be done incrementally, one slide at a time

