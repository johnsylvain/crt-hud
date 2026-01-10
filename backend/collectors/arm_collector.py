"""ARM (Automatic Ripping Machine) stats collector."""

import requests
import time
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
        
        # Debug logging
        self.debug_logs = []  # List of dicts with request/response info
        self.debug_log_max_entries = 20  # Keep last 20 requests
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch ARM job list from API."""
        url = ""
        params = {}
        headers = {}
        status_code = None
        response_text = None
        
        if USE_MOCKS:
            print("ARM API: Using mock data")
            result = self._fetch_mock_data()
            self._log_debug("joblist", "GET", "MOCK", {}, {}, 200, "Mock data", response_data=result)
            return result
        
        if not self.api_url:
            error_msg = "Missing API URL"
            print(f"ARM API: {error_msg}")
            self._log_debug("joblist", "GET", "", params, headers, error=error_msg)
            return None
        
        try:
            url = f"{self.api_url.rstrip('/')}{self.endpoint}"
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            print(f"ARM API: Fetching job list from {url}")
            print(f"ARM API: Params (masked): {self._mask_api_key(params)}")
            
            response = requests.get(url, params=params, timeout=5)
            status_code = response.status_code
            response_text = response.text
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                print(f"ARM API: Successfully parsed JSON response")
                print(f"ARM API: Response data structure - keys: {list(data.keys())}")
                print(f"ARM API: Response success field: {data.get('success', 'NOT FOUND')}")
                
                # Log debug BEFORE processing
                self._log_debug("joblist", "GET", url, self._mask_api_key(params), headers, status_code, response_text, response_data=data)
            except ValueError as e:
                error_msg = f"Failed to parse JSON: {e}"
                print(f"ARM API: {error_msg}")
                print(f"ARM API: Response content type: {response.headers.get('Content-Type', 'unknown')}")
                print(f"ARM API: Response preview: {response_text[:200]}")
                self._log_debug("joblist", "GET", url, self._mask_api_key(params), headers, status_code, response_text, error=error_msg)
                return None
            
            if not data.get("success", False):
                print(f"ARM API: Response indicates failure (success=False)")
                self._log_debug("joblist", "GET", url, self._mask_api_key(params), headers, status_code, response_text, response_data=data, error="API returned success=False")
                return None
            
            results = data.get("results", {})
            print(f"ARM API: Results type = {type(results)}, length = {len(results) if isinstance(results, dict) else 'N/A'}")
            
            # Find active or ripping jobs
            active_jobs = []
            for job_id, job_data in results.items():
                job_status = job_data.get("status", "")
                print(f"ARM API: Job {job_id} status = '{job_status}'")
                # Include both 'active' and 'ripping' status jobs
                if job_status in ["active", "ripping"]:
                    print(f"ARM API: Found {job_status} job {job_id}: {job_data.get('title', 'Unknown')}")
                    # Log available fields for debugging
                    print(f"ARM API: Job {job_id} fields: {list(job_data.keys())}")
                    if "poster_url" in job_data:
                        print(f"ARM API: Job {job_id} poster_url = '{job_data.get('poster_url')}'")
                    if "progress" in job_data:
                        print(f"ARM API: Job {job_id} progress = '{job_data.get('progress')}'")
                    active_jobs.append(job_data)
            
            print(f"ARM API: Found {len(active_jobs)} active/ripping job(s)")
            
            # If no active jobs, return None for conditional display
            if not active_jobs:
                print("ARM API: No active jobs found, returning None for conditional display")
                return None
            
            # Return all active jobs as a list (limit to 3 for display)
            jobs_list = []
            for job in active_jobs[:3]:  # Limit to 3 jobs for display
                job_data = {
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
                    "poster_url": job.get("poster_url") or job.get("poster_url_auto") or job.get("poster_url_manual"),
                    "progress": job.get("progress", "0"),
                    "progress_round": job.get("progress_round", "0"),
                    "status": job.get("status", ""),
                }
                jobs_list.append(job_data)
                print(f"ARM API: Added job {job_data.get('job_id')} - {job_data.get('title', 'Unknown')}")
            
            result = {
                "jobs": jobs_list,
                "job_count": len(jobs_list),
                "total_found": len(active_jobs)
            }
            print(f"ARM API: Returning {len(jobs_list)} job(s) for display")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"ARM API request failed: {error_msg}")
            import traceback
            traceback.print_exc()
            self._log_debug("joblist", "GET", url, self._mask_api_key(params), headers, status_code, response_text, error=error_msg)
            return None
        except (KeyError, ValueError) as e:
            error_msg = str(e)
            print(f"ARM API response parse error: {error_msg}")
            import traceback
            traceback.print_exc()
            self._log_debug("joblist", "GET", url, self._mask_api_key(params), headers, status_code, response_text, error=error_msg)
            return None
    
    def has_active_rip(self) -> bool:
        """Check if there's an active rip in progress."""
        data = self.get_data()
        return data is not None
    
    def _log_debug(self, endpoint: str, method: str, url: str, params: Dict = None, headers: Dict = None, 
                   status_code: int = None, response_text: str = None, error: str = None, response_data: Dict = None):
        """Log debug information for API requests."""
        
        log_entry = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "method": method,
            "url": url,
            "params": params or {},
            "headers": headers or {},
            "status_code": status_code,
            "response_preview": response_text[:500] if response_text else None,
            "response_full_length": len(response_text) if response_text else 0,
            "response_data": response_data,
            "error": error,
        }
        
        # Add to log list (keep only last N entries)
        self.debug_logs.append(log_entry)
        if len(self.debug_logs) > self.debug_log_max_entries:
            self.debug_logs.pop(0)
    
    def _mask_api_key(self, params: Dict) -> Dict:
        """Mask API key in params for logging."""
        if not params:
            return {}
        masked = params.copy()
        if "api_key" in masked:
            masked["api_key"] = "***MASKED***" if masked["api_key"] else ""
        return masked
    
    def get_debug_logs(self) -> list:
        """Get debug logs for API requests."""
        return self.debug_logs.copy()
    
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
                    mock_jobs = []
                    for job_id, job_data in results.items():
                        if job_data.get("status") in ["active", "ripping"]:
                            mock_jobs.append({
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
                                "poster_url": job_data.get("poster_url") or job_data.get("poster_url_auto") or job_data.get("poster_url_manual"),
                                "progress": job_data.get("progress", "0"),
                                "progress_round": job_data.get("progress_round", "0"),
                                "status": job_data.get("status", ""),
                            })
                    if mock_jobs:
                        return {
                            "jobs": mock_jobs[:3],  # Limit to 3 jobs
                            "job_count": len(mock_jobs[:3]),
                            "total_found": len(mock_jobs)
                        }
            except Exception as e:
                print(f"Error loading mock data: {e}")
        
        return None

