"""System stats collector (CPU, Memory, NAS storage)."""

import psutil
import time
from typing import Optional, Dict, Any, List
from .base import BaseCollector
from pathlib import Path


class SystemCollector(BaseCollector):
    """Collector for system statistics (CPU, Memory, Disk)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 5))
        self.nas_mounts = config.get("nas_mounts", [])
        
        # Debug logging
        self.debug_logs = []  # List of dicts with collection info
        self.debug_log_max_entries = 20  # Keep last 20 collections
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch system statistics."""
        collection_start = time.time()
        errors = []
        mount_checks = []
        
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
            if self.nas_mounts:
                for mount_path in self.nas_mounts:
                    mount = Path(mount_path)
                    mount_check = {
                        "path": mount_path,
                        "exists": mount.exists(),
                        "accessible": False,
                        "error": None
                    }
                    
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
                            mount_check["accessible"] = True
                            mount_check["percent"] = usage.percent
                        except PermissionError as e:
                            mount_check["error"] = f"Permission denied: {str(e)}"
                            errors.append(f"Permission denied accessing {mount_path}: {e}")
                        except OSError as e:
                            mount_check["error"] = f"OS error: {str(e)}"
                            errors.append(f"OS error accessing {mount_path}: {e}")
                    else:
                        mount_check["error"] = "Mount point does not exist"
                        errors.append(f"Mount point does not exist: {mount_path}")
                    
                    mount_checks.append(mount_check)
            else:
                mount_checks.append({
                    "path": "None specified",
                    "exists": False,
                    "accessible": False,
                    "note": "No NAS mounts configured, will use root filesystem"
                })
            
            # If no NAS mounts specified or accessible, use root filesystem
            if not disk_stats:
                try:
                    root_usage = psutil.disk_usage("/")
                    disk_stats.append({
                        "path": "/",
                        "total": root_usage.total,
                        "used": root_usage.used,
                        "free": root_usage.free,
                        "percent": root_usage.percent,
                    })
                    mount_checks.append({
                        "path": "/",
                        "exists": True,
                        "accessible": True,
                        "percent": root_usage.percent,
                        "note": "Using root filesystem (no accessible NAS mounts)"
                    })
                except Exception as e:
                    errors.append(f"Failed to access root filesystem: {e}")
            
            result = {
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
            
            # Log successful collection
            collection_time = time.time() - collection_start
            self._log_debug(
                success=True,
                collection_time=collection_time,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_count=len(disk_stats),
                mount_checks=mount_checks,
                errors=errors if errors else None
            )
            
            return result
        except Exception as e:
            error_msg = f"System stats collection error: {e}"
            print(error_msg)
            errors.append(error_msg)
            
            # Log failed collection
            collection_time = time.time() - collection_start
            self._log_debug(
                success=False,
                collection_time=collection_time,
                errors=errors
            )
            
            return None
    
    def _log_debug(self, success: bool, collection_time: float, cpu_percent: float = None,
                   memory_percent: float = None, disk_count: int = None, 
                   mount_checks: List[Dict] = None, errors: List[str] = None):
        """Log debug information for system stats collection."""
        log_entry = {
            "timestamp": time.time(),
            "success": success,
            "collection_time_ms": round(collection_time * 1000, 2),
            "cpu_percent": round(cpu_percent, 2) if cpu_percent is not None else None,
            "memory_percent": round(memory_percent, 2) if memory_percent is not None else None,
            "disk_count": disk_count,
            "nas_mounts_configured": len(self.nas_mounts),
            "mount_checks": mount_checks or [],
            "errors": errors or [],
        }
        
        # Add to log list (keep only last N entries)
        self.debug_logs.append(log_entry)
        if len(self.debug_logs) > self.debug_log_max_entries:
            self.debug_logs.pop(0)
    
    def get_debug_logs(self) -> List[Dict[str, Any]]:
        """Get debug logs for system stats collection."""
        return self.debug_logs.copy()
    
    def clear_debug_logs(self):
        """Clear all debug logs."""
        self.debug_logs = []

