"""Helper utility functions."""

import time
from datetime import datetime
from typing import Optional


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string from various formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


def calculate_elapsed_time(start_time_str: str) -> float:
    """Calculate elapsed time in seconds from start_time string."""
    start_dt = parse_datetime(start_time_str)
    if start_dt is None:
        return 0.0
    
    elapsed = datetime.now() - start_dt
    return elapsed.total_seconds()


def draw_progress_bar(width: int, current: float, total: float, filled_char: str = "=", empty_char: str = " ") -> str:
    """Generate ASCII progress bar string."""
    if total == 0:
        ratio = 0.0
    else:
        ratio = min(1.0, max(0.0, current / total))
    
    filled_width = int(width * ratio)
    return f"[{filled_char * filled_width}{empty_char * (width - filled_width)}]"

