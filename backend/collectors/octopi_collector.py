"""OctoPrint/OctoPi stats collector."""

import requests
from typing import Optional, Dict, Any, List
from .base import BaseCollector
from config import USE_MOCKS
from pathlib import Path


class OctoPiCollector(BaseCollector):
    """Collector for OctoPrint/OctoPi print status."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 5))
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        
        # Debug logging
        self.debug_logs = []  # List of dicts with request/response info
        self.debug_log_max_entries = 20  # Keep last 20 requests
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch OctoPrint print status from API."""
        if USE_MOCKS:
            return self._fetch_mock_data()
        
        if not self.api_url:
            self._log_debug("connection", "GET", "", error="Missing API URL")
            return None
        
        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        try:
            # Check connection state
            connection_url = f"{self.api_url.rstrip('/')}/api/connection"
            connection_response = requests.get(connection_url, headers=headers, timeout=5, verify=False)
            connection_status = connection_response.status_code
            connection_text = connection_response.text
            
            # Handle 403 Forbidden - authentication required
            if connection_status == 403:
                error_msg = "403 Forbidden: Authentication required. Please configure an API key in the slide settings."
                if not self.api_key:
                    error_msg += " No API key is currently configured."
                else:
                    error_msg += " The configured API key may be invalid."
                self._log_debug("connection", "GET", connection_url, headers, connection_status, connection_text, error=error_msg)
                print(f"OctoPrint API: {error_msg}")
                return None
            
            connection_response.raise_for_status()
            connection_data = connection_response.json()
            
            # Log connection API call
            self._log_debug("connection", "GET", connection_url, headers, connection_status, connection_text, response_data=connection_data)
            
            current_state = connection_data.get("current", {})
            state = current_state.get("state", "").lower()
            
            # Only return data if actively printing
            if state != "printing":
                return {
                    "is_printing": False,
                    "state": state
                }
            
            # Fetch job information
            job_url = f"{self.api_url.rstrip('/')}/api/job"
            job_response = requests.get(job_url, headers=headers, timeout=5, verify=False)
            job_status = job_response.status_code
            job_text = job_response.text
            
            # Handle 403 Forbidden
            if job_status == 403:
                error_msg = "403 Forbidden: Authentication required for job endpoint."
                self._log_debug("job", "GET", job_url, headers, job_status, job_text, error=error_msg)
                print(f"OctoPrint API: {error_msg}")
                return None
            
            job_response.raise_for_status()
            job_data = job_response.json()
            
            # Log job API call
            self._log_debug("job", "GET", job_url, headers, job_status, job_text, response_data=job_data)
            
            # Fetch printer state (temperatures)
            printer_url = f"{self.api_url.rstrip('/')}/api/printer"
            printer_response = requests.get(printer_url, headers=headers, timeout=5, verify=False)
            printer_status = printer_response.status_code
            printer_text = printer_response.text
            
            # Handle 403 Forbidden
            if printer_status == 403:
                error_msg = "403 Forbidden: Authentication required for printer endpoint."
                self._log_debug("printer", "GET", printer_url, headers, printer_status, printer_text, error=error_msg)
                print(f"OctoPrint API: {error_msg}")
                return None
            
            printer_response.raise_for_status()
            printer_data = printer_response.json()
            
            # Log printer API call
            self._log_debug("printer", "GET", printer_url, headers, printer_status, printer_text, response_data=printer_data)
            
            # Extract job information
            job_info = job_data.get("job", {})
            progress_info = job_data.get("progress", {})
            
            # Extract file information
            file_info = job_info.get("file", {})
            filename = file_info.get("name", "Unknown")
            
            # Extract progress
            completion = progress_info.get("completion", 0.0)
            print_time = progress_info.get("printTime", 0)  # seconds
            print_time_left = progress_info.get("printTimeLeft", None)  # seconds, can be None
            
            # Extract printer temperatures
            temp_data = printer_data.get("temperature", {})
            tool0_temp = temp_data.get("tool0", {})
            bed_temp = temp_data.get("bed", {})
            
            tool0_actual = tool0_temp.get("actual", 0.0)
            tool0_target = tool0_temp.get("target", 0.0)
            bed_actual = bed_temp.get("actual", 0.0)
            bed_target = bed_temp.get("target", 0.0)
            
            return {
                "is_printing": True,
                "state": state,
                "filename": filename,
                "progress": completion,
                "print_time": print_time,
                "print_time_left": print_time_left,
                "tool0_actual": tool0_actual,
                "tool0_target": tool0_target,
                "bed_actual": bed_actual,
                "bed_target": bed_target,
            }
            
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (like 403, 404, 500, etc.)
            error_msg = str(e)
            status_code = None
            if hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 403:
                    error_msg = f"403 Forbidden: Authentication required. {'No API key configured.' if not self.api_key else 'API key may be invalid.'}"
            
            print(f"OctoPrint API HTTP error: {error_msg}")
            # Try to determine which endpoint failed
            try:
                if 'connection_response' not in locals():
                    self._log_debug("connection", "GET", connection_url, headers, status_code, error=error_msg)
                elif 'job_response' not in locals():
                    self._log_debug("job", "GET", job_url, headers, status_code, error=error_msg)
                elif 'printer_response' not in locals():
                    self._log_debug("printer", "GET", printer_url, headers, status_code, error=error_msg)
                else:
                    # Fallback - log to connection
                    self._log_debug("connection", "GET", connection_url if 'connection_url' in locals() else "", headers, status_code, error=error_msg)
            except:
                # If we can't determine, just log a generic error
                self._log_debug("unknown", "GET", "", headers, status_code, error=error_msg)
            return None
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"OctoPrint API request failed: {error_msg}")
            # Try to determine which endpoint failed
            try:
                if 'connection_response' not in locals():
                    self._log_debug("connection", "GET", connection_url, headers, error=error_msg)
                elif 'job_response' not in locals():
                    self._log_debug("job", "GET", job_url, headers, error=error_msg)
                elif 'printer_response' not in locals():
                    self._log_debug("printer", "GET", printer_url, headers, error=error_msg)
                else:
                    # Fallback - log to connection
                    self._log_debug("connection", "GET", connection_url if 'connection_url' in locals() else "", headers, error=error_msg)
            except:
                # If we can't determine, just log a generic error
                self._log_debug("unknown", "GET", "", headers, error=error_msg)
            return None
        except (KeyError, ValueError) as e:
            error_msg = str(e)
            print(f"OctoPrint API response parse error: {error_msg}")
            # Try to determine which endpoint had parse error
            try:
                if 'connection_data' in locals():
                    self._log_debug("connection", "GET", connection_url, headers, error=error_msg)
                elif 'job_data' in locals():
                    self._log_debug("job", "GET", job_url, headers, error=error_msg)
                elif 'printer_data' in locals():
                    self._log_debug("printer", "GET", printer_url, headers, error=error_msg)
                else:
                    self._log_debug("unknown", "GET", "", headers, error=error_msg)
            except:
                self._log_debug("unknown", "GET", "", headers, error=error_msg)
            return None
    
    def _fetch_mock_data(self) -> Optional[Dict[str, Any]]:
        """Fetch mock data for testing."""
        # Return mock data simulating an active print
        return {
            "is_printing": True,
            "state": "printing",
            "filename": "test_print.gcode",
            "progress": 45.5,
            "print_time": 1234,
            "print_time_left": 1500,
            "tool0_actual": 210.5,
            "tool0_target": 215.0,
            "bed_actual": 60.0,
            "bed_target": 60.0,
        }
    
    def _log_debug(self, endpoint: str, method: str, url: str, headers: Dict = None, 
                   status_code: int = None, response_text: str = None, error: str = None, response_data: Dict = None):
        """Log debug information for API requests."""
        import time
        import json
        
        log_entry = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "method": method,
            "url": url,
            "headers": headers or {},
            "status_code": status_code,
            "response_preview": response_text[:500] if response_text else None,
            "response_full_length": len(response_text) if response_text else 0,
            "response_data": response_data,
            "error": error,
        }
        
        # Mask sensitive information in headers
        if log_entry["headers"]:
            masked_headers = log_entry["headers"].copy()
            if "X-Api-Key" in masked_headers:
                masked_headers["X-Api-Key"] = masked_headers["X-Api-Key"][:8] + "..." if len(masked_headers["X-Api-Key"]) > 8 else "***"
            log_entry["headers"] = masked_headers
        
        self.debug_logs.append(log_entry)
        
        # Keep only last N entries
        if len(self.debug_logs) > self.debug_log_max_entries:
            self.debug_logs = self.debug_logs[-self.debug_log_max_entries:]
    
    def get_debug_logs(self) -> List[Dict[str, Any]]:
        """Get debug logs for this collector."""
        return self.debug_logs.copy()
