"""Chart rendering for widgets using PIL."""

from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw
import math

from ..themes import FalloutTheme


def _normalize_data(data: List[float], min_val: Optional[float] = None, max_val: Optional[float] = None) -> List[float]:
    """
    Normalize data to 0-1 range.
    
    Args:
        data: List of numeric values
        min_val: Minimum value (if None, uses min of data)
        max_val: Maximum value (if None, uses max of data)
    
    Returns:
        List of normalized values (0.0 to 1.0)
    """
    if not data:
        return []
    
    # Remove None values
    clean_data = [d for d in data if d is not None]
    if not clean_data:
        return [0.0] * len(data)
    
    # Calculate min/max
    data_min = min(clean_data) if min_val is None else min_val
    data_max = max(clean_data) if max_val is None else max_val
    
    if data_max == data_min:
        return [0.5] * len(data)  # Return middle value if no range
    
    # Normalize
    normalized = []
    for value in data:
        if value is None:
            normalized.append(0.0)
        else:
            norm_val = (value - data_min) / (data_max - data_min)
            normalized.append(max(0.0, min(1.0, norm_val)))  # Clamp to 0-1
    
    return normalized


def render_line_chart(data: Any, bounds: Tuple[int, int], theme: FalloutTheme) -> Optional[Image.Image]:
    """
    Render a line chart.
    
    Args:
        data: Chart data - can be:
            - List of numbers: [1, 2, 3, 4, 5]
            - List of dicts with value key: [{"value": 1}, {"value": 2}]
            - Dict with "values" key: {"values": [1, 2, 3]}
        bounds: Chart bounds (width, height)
        theme: Theme instance
    
    Returns:
        PIL Image with chart or None on error
    """
    width, height = bounds
    
    if not data:
        return None
    
    try:
        # Extract values from various data formats
        if isinstance(data, dict):
            values = data.get("values", data.get("data", []))
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # List of dicts - extract "value" or first numeric key
                values = []
                for item in data:
                    if isinstance(item, dict):
                        val = item.get("value", item.get("y", None))
                        if val is None:
                            # Try to find first numeric value
                            for v in item.values():
                                if isinstance(v, (int, float)):
                                    val = v
                                    break
                        values.append(val)
                    else:
                        values.append(item)
            else:
                values = data
        else:
            return None
        
        # Convert to floats
        try:
            values = [float(v) if v is not None else 0.0 for v in values]
        except (ValueError, TypeError):
            return None
        
        if not values:
            return None
        
        # Normalize data
        normalized = _normalize_data(values)
        
        # Create image
        img = Image.new("RGB", (width, height), theme.colors["background"])
        draw = ImageDraw.Draw(img)
        
        # Chart padding
        padding = 8
        chart_width = width - (padding * 2)
        chart_height = height - (padding * 2)
        
        # Draw axes
        axes_color = theme.colors["text_muted"]
        draw.line([(padding, padding), (padding, height - padding)], fill=axes_color, width=1)
        draw.line([(padding, height - padding), (width - padding, height - padding)], fill=axes_color, width=1)
        
        # Draw line
        if len(normalized) > 1:
            line_color = theme.colors["text"]
            points = []
            
            for i, norm_val in enumerate(normalized):
                x = padding + int((i / (len(normalized) - 1)) * chart_width) if len(normalized) > 1 else padding
                y = height - padding - int(norm_val * chart_height)
                points.append((x, y))
            
            # Draw line segments
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill=line_color, width=2)
            
            # Draw points
            for point in points:
                draw.ellipse([point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2], fill=line_color)
        elif len(normalized) == 1:
            # Single point
            x = padding + chart_width // 2
            y = height - padding - int(normalized[0] * chart_height)
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=theme.colors["text"])
        
        return img
    
    except Exception as e:
        print(f"Error rendering line chart: {e}")
        import traceback
        traceback.print_exc()
        return None


def render_bar_chart(data: Any, bounds: Tuple[int, int], theme: FalloutTheme) -> Optional[Image.Image]:
    """
    Render a bar chart.
    
    Args:
        data: Chart data - can be:
            - List of numbers: [1, 2, 3, 4, 5]
            - List of dicts with value/label: [{"label": "A", "value": 1}, {"label": "B", "value": 2}]
            - Dict with "values" or "data" key: {"values": [1, 2, 3]}
        bounds: Chart bounds (width, height)
        theme: Theme instance
    
    Returns:
        PIL Image with chart or None on error
    """
    width, height = bounds
    
    if not data:
        return None
    
    try:
        # Extract values and labels from various data formats
        if isinstance(data, dict):
            values = data.get("values", data.get("data", []))
            labels = data.get("labels", [])
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # List of dicts - extract value and label
                values = []
                labels = []
                for item in data:
                    if isinstance(item, dict):
                        val = item.get("value", item.get("y", None))
                        if val is None:
                            # Try to find first numeric value
                            for v in item.values():
                                if isinstance(v, (int, float)):
                                    val = v
                                    break
                        values.append(val)
                        labels.append(item.get("label", item.get("name", "")))
                    else:
                        values.append(item)
                        labels.append("")
            else:
                values = data
                labels = [""] * len(data)
        else:
            return None
        
        # Convert to floats
        try:
            values = [float(v) if v is not None else 0.0 for v in values]
        except (ValueError, TypeError):
            return None
        
        if not values:
            return None
        
        # Normalize data
        normalized = _normalize_data(values)
        
        # Create image
        img = Image.new("RGB", (width, height), theme.colors["background"])
        draw = ImageDraw.Draw(img)
        
        # Chart padding
        padding = 8
        chart_width = width - (padding * 2)
        chart_height = height - (padding * 2)
        
        # Draw axes
        axes_color = theme.colors["text_muted"]
        draw.line([(padding, padding), (padding, height - padding)], fill=axes_color, width=1)
        draw.line([(padding, height - padding), (width - padding, height - padding)], fill=axes_color, width=1)
        
        # Draw bars
        bar_color = theme.colors["text"]
        num_bars = len(normalized)
        
        if num_bars > 0:
            bar_width = max(1, (chart_width // num_bars) - 2)  # Space between bars
            bar_spacing = 2
            
            for i, norm_val in enumerate(normalized):
                bar_height = int(norm_val * chart_height)
                x_start = padding + int((i * chart_width) / num_bars) + bar_spacing
                x_end = x_start + bar_width
                y_start = height - padding - bar_height
                y_end = height - padding
                
                # Draw bar
                draw.rectangle([x_start, y_start, x_end, y_end], fill=bar_color, outline=axes_color, width=1)
                
                # Draw label if space permits (only for small number of bars)
                if num_bars <= 5 and labels and i < len(labels) and labels[i]:
                    label = labels[i][:5]  # Truncate long labels
                    font = theme.fonts["tiny"]
                    label_color = theme.colors["text_secondary"]
                    # Try to fit label above bar
                    if y_start > padding + 10:
                        draw.text((x_start + 2, y_start - 10), label, fill=label_color, font=font)
        
        return img
    
    except Exception as e:
        print(f"Error rendering bar chart: {e}")
        import traceback
        traceback.print_exc()
        return None

