"""System stats collector (CPU, Memory, NAS storage)."""

import psutil
from typing import Optional, Dict, Any, List
from .base import BaseCollector
from pathlib import Path


class SystemCollector(BaseCollector):
    """Collector for system statistics (CPU, Memory, Disk)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 5))
        self.nas_mounts = config.get("nas_mounts", [])
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch system statistics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_used = memory.used
            memory_total = memory.total
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Disk usage for NAS mounts
            disk_stats = []
            for mount_path in self.nas_mounts:
                mount = Path(mount_path)
                if mount.exists():
                    try:
                        usage = psutil.disk_usage(str(mount))
                        disk_stats.append({
                            "path": mount_path,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                        })
                    except (PermissionError, OSError):
                        # Skip mounts we can't access
                        continue
            
            # If no NAS mounts specified or accessible, use root filesystem
            if not disk_stats:
                root_usage = psutil.disk_usage("/")
                disk_stats.append({
                    "path": "/",
                    "total": root_usage.total,
                    "used": root_usage.used,
                    "free": root_usage.free,
                    "percent": root_usage.percent,
                })
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "per_core": cpu_per_core,
                    "count": cpu_count,
                },
                "memory": {
                    "used": memory_used,
                    "total": memory_total,
                    "available": memory_available,
                    "percent": memory_percent,
                },
                "disks": disk_stats,
            }
        except Exception as e:
            print(f"System stats collection error: {e}")
            return None

