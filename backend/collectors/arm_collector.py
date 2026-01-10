"""ARM (Automatic Ripping Machine) stats collector."""

import requests
from typing import Optional, Dict, Any
from .base import BaseCollector
from config import USE_MOCKS
from pathlib import Path


class ARMCollector(BaseCollector):
    """Collector for ARM stats."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 30))
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.endpoint = config.get("endpoint", "/json?mode=joblist")
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch ARM job list from API."""
        if USE_MOCKS:
            return self._fetch_mock_data()
        
        if not self.api_url:
            return None
        
        try:
            url = f"{self.api_url.rstrip('/')}{self.endpoint}"
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success", False):
                return None
            
            results = data.get("results", {})
            
            # Find active jobs
            active_jobs = []
            for job_id, job_data in results.items():
                if job_data.get("status") == "active":
                    active_jobs.append(job_data)
            
            # If no active jobs, return None for conditional display
            if not active_jobs:
                return None
            
            # Return first active job (or merge multiple if needed)
            job = active_jobs[0]
            
            return {
                "job_id": job.get("job_id"),
                "title": job.get("title", "Unknown"),
                "disctype": job.get("disctype", ""),
                "video_type": job.get("video_type", ""),
                "start_time": job.get("start_time", ""),
                "no_of_titles": job.get("no_of_titles", "0"),
                "year": job.get("year", ""),
                "pid": job.get("pid", ""),
                "stage": job.get("stage", ""),
                "label": job.get("label", ""),
                "mountpoint": job.get("mountpoint", ""),
            }
        except requests.exceptions.RequestException as e:
            print(f"ARM API request failed: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"ARM API response parse error: {e}")
            return None
    
    def has_active_rip(self) -> bool:
        """Check if there's an active rip in progress."""
        data = self.get_data()
        return data is not None
    
    def _fetch_mock_data(self) -> Optional[Dict[str, Any]]:
        """Fetch mock data for testing."""
        # Check for mock fixture file
        mock_file = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "arm_active_response.json"
        if mock_file.exists():
            import json
            try:
                with open(mock_file, 'r') as f:
                    mock_data = json.load(f)
                    results = mock_data.get("results", {})
                    for job_id, job_data in results.items():
                        if job_data.get("status") == "active":
                            return {
                                "job_id": job_data.get("job_id"),
                                "title": job_data.get("title", "Mock Title"),
                                "disctype": job_data.get("disctype", ""),
                                "video_type": job_data.get("video_type", ""),
                                "start_time": job_data.get("start_time", ""),
                                "no_of_titles": job_data.get("no_of_titles", "0"),
                                "year": job_data.get("year", ""),
                                "pid": job_data.get("pid", ""),
                                "stage": job_data.get("stage", ""),
                                "label": job_data.get("label", ""),
                                "mountpoint": job_data.get("mountpoint", ""),
                            }
            except Exception as e:
                print(f"Error loading mock data: {e}")
        
        return None

