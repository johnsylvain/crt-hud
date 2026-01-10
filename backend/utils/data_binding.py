"""Data binding utilities for widget rendering."""

from typing import Any, Dict, Optional, List
import re


def extract_path(data: Dict[str, Any], path: str) -> Any:
    """
    Extract value from nested dictionary using dot notation or JSONPath-like syntax.
    
    Supports:
    - Dot notation: "cpu.percent" -> data["cpu"]["percent"]
    - Root: "$" -> entire data
    - Array access: "items[0]" -> data["items"][0]
    - Nested arrays: "items[0].value" -> data["items"][0]["value"]
    
    Args:
        data: Dictionary to extract from
        path: Path string (e.g., "cpu.percent", "$", "items[0].name")
    
    Returns:
        Extracted value or None if path not found
    """
    if not path or not isinstance(data, dict):
        return None
    
    # Root path returns entire data
    if path == "$" or path == "":
        return data
    
    # Remove leading dot or dollar sign
    path = path.lstrip("$.").lstrip(".")
    
    if not path:
        return data
    
    try:
        current = data
        
        # Split by dots but handle array notation
        parts = re.split(r'\.(?![^\[]*\])', path)  # Split by . but not inside []
        
        for part in parts:
            # Handle array notation like "items[0]" or "[0]"
            array_match = re.match(r'^(.+?)\[(\d+)\]$', part)
            if array_match:
                key = array_match.group(1)
                index = int(array_match.group(2))
                
                if key:
                    current = current.get(key)
                else:
                    # Handle standalone [0] (current is already a list)
                    pass
                
                if isinstance(current, (list, tuple)) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                # Regular dictionary access
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            
            if current is None:
                return None
        
        return current
    except (KeyError, TypeError, AttributeError, IndexError):
        return None


def format_template(template: str, values: Dict[str, Any]) -> str:
    """
    Format template string with placeholders.
    
    Supports:
    - Simple placeholders: "CPU: {value}%"
    - Nested access: "Status: {data.status}"
    - Default values: "Count: {count|0}"
    
    Args:
        template: Template string with {placeholder} syntax
        values: Dictionary of values to substitute
    
    Returns:
        Formatted string
    """
    if not template:
        return ""
    
    def replace_placeholder(match):
        placeholder = match.group(1)
        
        # Handle default values: "value|default"
        if "|" in placeholder:
            key, default = placeholder.split("|", 1)
            key = key.strip()
            default = default.strip()
        else:
            key = placeholder.strip()
            default = ""
        
        # Extract value using dot notation if needed
        value = extract_path(values, key) if "." in key else values.get(key)
        
        if value is None:
            return default
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value)
        else:
            return str(value)
    
    # Replace {placeholder} or {placeholder|default} patterns
    pattern = r'\{([^}]+)\}'
    return re.sub(pattern, replace_placeholder, template)


def evaluate_condition(data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    """
    Evaluate conditional expression against data.
    
    Supports:
    - Comparison: {"path": "cpu.percent", "operator": ">", "value": 50}
    - Equality: {"path": "status", "operator": "==", "value": "active"}
    - Existence: {"path": "data", "operator": "exists"}
    - Logical operators: {"operator": "and", "conditions": [...]}
    
    Args:
        data: Data dictionary to evaluate against
        condition: Condition dictionary with operator and operands
    
    Returns:
        True if condition is met, False otherwise
    """
    if not isinstance(condition, dict):
        return False
    
    operator = condition.get("operator", "").lower()
    
    # Logical operators
    if operator == "and":
        conditions = condition.get("conditions", [])
        return all(evaluate_condition(data, c) for c in conditions)
    elif operator == "or":
        conditions = condition.get("conditions", [])
        return any(evaluate_condition(data, c) for c in conditions)
    elif operator == "not":
        sub_condition = condition.get("condition", {})
        return not evaluate_condition(data, sub_condition)
    
    # Comparison operators
    path = condition.get("path")
    if path is None:
        return False
    
    value = extract_path(data, path)
    compare_value = condition.get("value")
    
    if operator == "==":
        return value == compare_value
    elif operator == "!=":
        return value != compare_value
    elif operator == ">":
        try:
            return float(value) > float(compare_value)
        except (ValueError, TypeError):
            return False
    elif operator == ">=":
        try:
            return float(value) >= float(compare_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<":
        try:
            return float(value) < float(compare_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<=":
        try:
            return float(value) <= float(compare_value)
        except (ValueError, TypeError):
            return False
    elif operator == "exists":
        return value is not None
    elif operator == "not_exists":
        return value is None
    elif operator == "contains":
        if isinstance(value, str) and isinstance(compare_value, str):
            return compare_value in value
        elif isinstance(value, (list, tuple)) and compare_value in value:
            return True
        return False
    
    # Default: check if value exists and is truthy
    return bool(value)


def format_value(value: Any, format_type: Optional[str] = None) -> str:
    """
    Format a value according to format type.
    
    Args:
        value: Value to format
        format_type: Format type (bytes, duration, percentage, integer, float, etc.)
    
    Returns:
        Formatted string
    """
    if value is None:
        return ""
    
    if format_type == "bytes":
        from .helpers import format_bytes
        try:
            return format_bytes(int(value))
        except (ValueError, TypeError):
            return str(value)
    elif format_type == "duration":
        from .helpers import format_duration
        try:
            return format_duration(float(value))
        except (ValueError, TypeError):
            return str(value)
    elif format_type == "percentage":
        try:
            return f"{float(value):.1f}%"
        except (ValueError, TypeError):
            return str(value)
    elif format_type == "integer":
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return str(value)
    elif format_type == "float":
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)
    elif format_type == "currency":
        try:
            return f"${float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)
    else:
        return str(value)

