"""Widget rendering system for custom slides."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw

from .themes import FalloutTheme, DISPLAY_WIDTH, DISPLAY_HEIGHT, PADDING, LINE_HEIGHT_LARGE, LINE_HEIGHT_MEDIUM, LINE_HEIGHT_SMALL, LINE_HEIGHT_TINY
from ..utils.data_binding import extract_path, format_template, format_value, evaluate_condition
from ..utils.helpers import draw_progress_bar


class WidgetRenderer(ABC):
    """Abstract base class for widget renderers."""
    
    def __init__(self, theme: FalloutTheme):
        """
        Initialize widget renderer.
        
        Args:
            theme: Theme instance for styling
        """
        self.theme = theme
    
    @abstractmethod
    def render(
        self,
        widget: Dict[str, Any],
        data: Dict[str, Any],
        draw: ImageDraw.Draw,
        bounds: Tuple[int, int, int, int]  # (x, y, width, height)
    ) -> None:
        """
        Render widget on the image.
        
        Args:
            widget: Widget configuration dictionary
            data: Data dictionary to bind to widget
            draw: PIL ImageDraw instance
            bounds: Bounding box (x, y, width, height) for widget
        """
        pass
    
    def resolve_data_path(self, data: Dict[str, Any], path: str) -> Any:
        """
        Resolve data path using dot notation.
        
        Args:
            data: Data dictionary
            path: Path string (e.g., "cpu.percent")
        
        Returns:
            Extracted value or None
        """
        return extract_path(data, path)
    
    def get_style_value(self, widget: Dict[str, Any], key: str, default: Any) -> Any:
        """
        Get style value from widget config with fallback.
        
        Args:
            widget: Widget configuration
            key: Style key
            default: Default value
        
        Returns:
            Style value or default
        """
        style = widget.get("style", {})
        return style.get(key, default)
    
    def get_font(self, size: str) -> Any:
        """
        Get font based on size name.
        
        Args:
            size: Font size name (large, medium, small, tiny)
        
        Returns:
            PIL Font object
        """
        return self.theme.fonts.get(size, self.theme.fonts["medium"])
    
    def get_color(self, color_name: str) -> Tuple[int, int, int]:
        """
        Get color from theme.
        
        Args:
            color_name: Color name (text, text_secondary, text_muted, accent)
        
        Returns:
            RGB tuple
        """
        return self.theme.colors.get(color_name, self.theme.colors["text"])


class TextWidgetRenderer(WidgetRenderer):
    """Renderer for text widgets."""
    
    def render(
        self,
        widget: Dict[str, Any],
        data: Dict[str, Any],
        draw: ImageDraw.Draw,
        bounds: Tuple[int, int, int, int]
    ) -> None:
        """Render text widget."""
        x, y, width, height = bounds
        
        # Get data binding
        data_binding = widget.get("data_binding", {})
        path = data_binding.get("path", "")
        template = data_binding.get("template", "")
        format_type = data_binding.get("format", None)
        
        # Get text value
        if template:
            # Use template formatting
            text = format_template(template, data)
        elif path:
            # Extract value and optionally format
            value = self.resolve_data_path(data, path)
            if format_type:
                text = format_value(value, format_type)
            else:
                text = str(value) if value is not None else ""
        else:
            # Fallback to static text
            text = widget.get("text", "")
        
        if not text:
            return
        
        # Get style
        font_size = self.get_style_value(widget, "font_size", "medium")
        color_name = self.get_style_value(widget, "color", "text")
        align = self.get_style_value(widget, "align", "left")
        
        font = self.get_font(font_size)
        color = self.get_color(color_name)
        
        # Handle alignment
        if align == "center":
            # Calculate text width for centering
            if hasattr(font, 'getlength'):
                text_width = font.getlength(text)
            elif hasattr(draw, 'textlength'):
                text_width = draw.textlength(text, font=font)
            else:
                # Estimate based on character count
                char_width = getattr(font, 'size', 16) * 0.6
                text_width = len(text) * char_width
            
            x = x + (width - int(text_width)) // 2
        elif align == "right":
            # Calculate text width for right alignment
            if hasattr(font, 'getlength'):
                text_width = font.getlength(text)
            elif hasattr(draw, 'textlength'):
                text_width = draw.textlength(text, font=font)
            else:
                char_width = getattr(font, 'size', 16) * 0.6
                text_width = len(text) * char_width
            
            x = x + width - int(text_width)
        
        # Wrap text if needed
        max_width = width - PADDING
        lines = self._wrap_text(text, font, max_width, draw)
        
        # Draw lines
        line_height = self.theme.line_heights.get(font_size, LINE_HEIGHT_MEDIUM)
        current_y = y
        
        for line in lines:
            if current_y + line_height > y + height:
                break  # Don't overflow bounds
            draw.text((x, current_y), line, fill=color, font=font)
            current_y += line_height
    
    def _wrap_text(self, text: str, font: Any, max_width: int, draw: ImageDraw.Draw) -> list:
        """Wrap text into lines that fit within max_width."""
        try:
            if hasattr(font, 'getlength'):
                def text_length_func(txt):
                    return font.getlength(txt)
            elif hasattr(draw, 'textlength'):
                def text_length_func(txt):
                    return draw.textlength(txt, font=font)
            else:
                char_width = getattr(font, 'size', 16) * 0.6
                def text_length_func(txt):
                    return len(txt) * char_width
        except Exception:
            char_width = 16 * 0.6
            def text_length_func(txt):
                return len(txt) * char_width
        
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_text = word + " "
            word_width = text_length_func(word_text)
            
            if current_line and current_width + word_width > max_width:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = text_length_func(word)
            else:
                current_line.append(word)
                current_width += word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text]


class ProgressWidgetRenderer(WidgetRenderer):
    """Renderer for progress bar widgets."""
    
    def render(
        self,
        widget: Dict[str, Any],
        data: Dict[str, Any],
        draw: ImageDraw.Draw,
        bounds: Tuple[int, int, int, int]
    ) -> None:
        """Render progress bar widget."""
        x, y, width, height = bounds
        
        # Get data binding
        data_binding = widget.get("data_binding", {})
        path = data_binding.get("path", "")
        max_value = data_binding.get("max", 100)
        min_value = data_binding.get("min", 0)
        
        # Get value
        value = self.resolve_data_path(data, path)
        if value is None:
            value = 0
        
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0
        
        # Clamp value
        value = max(min_value, min(max_value, value))
        
        # Calculate percentage
        if max_value == min_value:
            percent = 0.0
        else:
            percent = ((value - min_value) / (max_value - min_value)) * 100.0
        
        # Get style
        bar_width = self.get_style_value(widget, "width", 30)
        show_label = self.get_style_value(widget, "show_label", True)
        label_template = self.get_style_value(widget, "label_template", "{value:.1f}%")
        color_name = self.get_style_value(widget, "color", "text")
        
        font = self.get_font("small")
        color = self.get_color(color_name)
        
        # Generate progress bar
        bar = draw_progress_bar(bar_width, percent, 100.0)
        
        # Draw label if enabled
        if show_label:
            label_text = format_template(label_template, {"value": percent, "current": value, "max": max_value})
            # Combine label and bar
            text = f"{label_text} {bar}"
        else:
            text = bar
        
        draw.text((x, y), text, fill=color, font=font)


class ChartWidgetRenderer(WidgetRenderer):
    """Renderer for chart widgets."""
    
    def render(
        self,
        widget: Dict[str, Any],
        data: Dict[str, Any],
        draw: ImageDraw.Draw,
        bounds: Tuple[int, int, int, int]
    ) -> None:
        """Render chart widget."""
        x, y, width, height = bounds
        
        # Get chart configuration
        chart_config = widget.get("chart_config", {})
        chart_type = chart_config.get("type", "line")
        data_path = chart_config.get("data_path", "")
        
        # Get chart data
        chart_data = self.resolve_data_path(data, data_path)
        if chart_data is None:
            # Draw placeholder
            font = self.get_font("small")
            color = self.get_color("text_muted")
            draw.text((x, y), "NO DATA", fill=color, font=font)
            return
        
        # Import chart renderer
        try:
            from .widgets.chart_renderer import render_line_chart, render_bar_chart
            
            # Render chart based on type
            chart_image = None
            if chart_type == "line":
                chart_image = render_line_chart(chart_data, (width, height), self.theme)
            elif chart_type == "bar":
                chart_image = render_bar_chart(chart_data, (width, height), self.theme)
            else:
                # Unknown chart type
                font = self.get_font("small")
                color = self.get_color("text_muted")
                draw.text((x, y), f"Unknown chart type: {chart_type}", fill=color, font=font)
                return
            
            # Paste chart onto main image
            if chart_image:
                # Get the main image from draw
                img = draw.im
                img.paste(chart_image, (x, y))
            else:
                # Chart renderer returned None
                font = self.get_font("small")
                color = self.get_color("text_muted")
                draw.text((x, y), "No chart data", fill=color, font=font)
        
        except ImportError as e:
            # Chart renderer not available - draw placeholder
            font = self.get_font("small")
            color = self.get_color("text_muted")
            draw.text((x, y), "Chart rendering unavailable", fill=color, font=font)
            print(f"Chart renderer import error: {e}")
        except Exception as e:
            print(f"Error rendering chart: {e}")
            import traceback
            traceback.print_exc()
            font = self.get_font("small")
            color = self.get_color("text_muted")
            draw.text((x, y), f"Chart error: {str(e)[:20]}", fill=color, font=font)


class ConditionalWidgetRenderer(WidgetRenderer):
    """Renderer for conditional widgets (wraps other widgets)."""
    
    def __init__(self, theme: FalloutTheme, widget_renderer_registry_getter):
        """
        Initialize conditional widget renderer.
        
        Args:
            theme: Theme instance
            widget_renderer_registry_getter: Function that returns registry dict or registry dict itself
        """
        super().__init__(theme)
        # Support both function and dict for flexibility
        if callable(widget_renderer_registry_getter):
            self._registry_getter = widget_renderer_registry_getter
        else:
            self._registry_getter = lambda: widget_renderer_registry_getter
    
    def _get_registry(self) -> Dict[str, WidgetRenderer]:
        """Get widget renderer registry."""
        return self._registry_getter()
    
    def render(
        self,
        widget: Dict[str, Any],
        data: Dict[str, Any],
        draw: ImageDraw.Draw,
        bounds: Tuple[int, int, int, int]
    ) -> None:
        """Render conditional widget (renders child widget if condition is met)."""
        # Get condition
        condition = widget.get("condition", {})
        
        # Evaluate condition
        if condition and not evaluate_condition(data, condition):
            return  # Don't render if condition is not met
        
        # Get child widget configuration
        child_widget = widget.get("widget", {})
        child_type = child_widget.get("type", "")
        
        # Get appropriate renderer for child widget
        registry = self._get_registry()
        renderer = registry.get(child_type)
        if renderer:
            renderer.render(child_widget, data, draw, bounds)
        else:
            # Fallback: draw placeholder
            font = self.get_font("small")
            color = self.get_color("text_muted")
            draw.text((bounds[0], bounds[1]), f"Unknown widget: {child_type}", fill=color, font=font)


class WidgetRendererRegistry:
    """Registry for widget renderers."""
    
    def __init__(self, theme: FalloutTheme):
        """Initialize registry with default renderers."""
        self.theme = theme
        self.renderers: Dict[str, WidgetRenderer] = {}
        
        # Register default renderers
        self.register("text", TextWidgetRenderer(theme))
        self.register("progress", ProgressWidgetRenderer(theme))
        self.register("chart", ChartWidgetRenderer(theme))
        
        # Conditional renderer needs access to registry - register after base renderers
        # Use a lambda to delay access to self.renderers
        conditional_renderer = ConditionalWidgetRenderer(theme, lambda: self.renderers)
        self.register("conditional", conditional_renderer)
    
    def register(self, widget_type: str, renderer: WidgetRenderer) -> None:
        """Register a widget renderer."""
        self.renderers[widget_type] = renderer
    
    def get(self, widget_type: str) -> Optional[WidgetRenderer]:
        """Get widget renderer by type."""
        return self.renderers.get(widget_type)

