"""Base collector class for data collection."""

import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class BaseCollector(ABC):
    """Abstract base class for data collectors."""
    
    def __init__(self, config: Dict[str, Any], poll_interval: int = 30):
        """
        Initialize collector.
        
        Args:
            config: Service configuration dictionary
            poll_interval: Polling interval in seconds
        """
        self.config = config
        self.poll_interval = poll_interval
        self.enabled = config.get("enabled", True)
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 5  # Cache TTL in seconds
        self._lock = threading.Lock()
        self._last_error: Optional[str] = None
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and fresh, otherwise fetch new data.
        
        Returns:
            Dictionary with collected stats or None if error/disabled
        """
        if not self.enabled:
            return None
        
        with self._lock:
            # Check cache
            if self._cache is not None and self._cache_time is not None:
                age = (datetime.now() - self._cache_time).total_seconds()
                if age < self._cache_ttl:
                    return self._cache.copy()
            
            # Fetch new data
            try:
                data = self._fetch_data()
                # Always update cache, even if None (to mark that we tried and got no data)
                # This ensures we don't return stale None values indefinitely
                self._cache = data
                self._cache_time = datetime.now()
                if data is not None:
                    self._last_error = None
                return data
            except Exception as e:
                self._last_error = str(e)
                print(f"Error in {self.__class__.__name__}: {e}")
                import traceback
                traceback.print_exc()
                # Return cached data if available, even if stale
                return self._cache.copy() if self._cache else None
    
    @abstractmethod
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the service API.
        
        Returns:
            Dictionary with collected stats or None if error
        """
        pass
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        with self._lock:
            self._cache = None
            self._cache_time = None
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error
    
    def is_healthy(self) -> bool:
        """Check if collector is healthy (no recent errors)."""
        return self._last_error is None or (
            self._cache_time is not None and
            (datetime.now() - self._cache_time).total_seconds() < self.poll_interval * 2
        )

