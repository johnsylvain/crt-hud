"""Generic API collector for custom endpoints."""

import requests
from typing import Optional, Dict, Any
from .base import BaseCollector
from backend.utils.data_binding import extract_path
import json


class GenericCollector(BaseCollector):
    """Generic collector for arbitrary API endpoints."""
    
    def __init__(self, config: Dict[str, Any], slide_id: Optional[int] = None):
        """
        Initialize generic collector.
        
        Args:
            config: API configuration dictionary with:
                - endpoint: API endpoint URL
                - method: HTTP method (GET, POST) - default GET
                - headers: Dictionary of HTTP headers
                - body: Request body (for POST requests)
                - data_path: JSONPath-like path to extract data (default: "$")
                - timeout: Request timeout in seconds (default: 10)
                - enabled: Whether collector is enabled (default: True)
            slide_id: Optional slide ID for identification
        """
        # Extract poll_interval from config or use default
        poll_interval = config.get("refresh_interval", config.get("poll_interval", 30))
        super().__init__(config, poll_interval)
        
        self.endpoint = config.get("endpoint", "")
        self.method = config.get("method", "GET").upper()
        self.headers = config.get("headers", {})
        self.body = config.get("body")  # Can be dict or string
        self.data_path = config.get("data_path", "$")  # JSONPath for extraction
        self.timeout = config.get("timeout", 10)
        self.slide_id = slide_id
        
        # Ensure enabled is set
        if "enabled" not in config:
            self.enabled = True
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the configured API endpoint.
        
        Returns:
            Dictionary with collected data or None if error
        """
        if not self.endpoint:
            print(f"GenericCollector (slide {self.slide_id}): No endpoint configured")
            return None
        
        try:
            # Prepare request parameters
            request_kwargs = {
                "url": self.endpoint,
                "timeout": self.timeout,
                "headers": self.headers.copy() if self.headers else {}
            }
            
            # Set default content-type for POST if not specified
            if self.method == "POST" and "Content-Type" not in request_kwargs["headers"]:
                if isinstance(self.body, dict):
                    request_kwargs["headers"]["Content-Type"] = "application/json"
                elif isinstance(self.body, str):
                    request_kwargs["headers"]["Content-Type"] = "text/plain"
            
            # Prepare body for POST requests
            if self.method == "POST" and self.body is not None:
                if isinstance(self.body, dict):
                    request_kwargs["json"] = self.body
                else:
                    request_kwargs["data"] = self.body
            
            # Make request
            if self.method == "GET":
                response = requests.get(**request_kwargs)
            elif self.method == "POST":
                response = requests.post(**request_kwargs)
            elif self.method == "PUT":
                response = requests.put(**request_kwargs)
            elif self.method == "DELETE":
                response = requests.delete(**request_kwargs)
            else:
                print(f"GenericCollector (slide {self.slide_id}): Unsupported method {self.method}")
                return None
            
            response.raise_for_status()
            
            # Parse response
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                data = response.json()
            else:
                # Try to parse as JSON anyway, fallback to text
                try:
                    data = response.json()
                except ValueError:
                    data = {"raw_response": response.text}
            
            # Extract data using JSONPath if specified
            if self.data_path and self.data_path != "$":
                extracted = extract_path(data, self.data_path)
                if extracted is not None:
                    return extracted if isinstance(extracted, dict) else {"value": extracted}
                else:
                    print(f"GenericCollector (slide {self.slide_id}): Data path '{self.data_path}' not found")
                    return None
            
            # Return entire response if data_path is "$" or not specified
            return data if isinstance(data, dict) else {"value": data}
            
        except requests.exceptions.Timeout:
            print(f"GenericCollector (slide {self.slide_id}): Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"GenericCollector (slide {self.slide_id}): Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"GenericCollector (slide {self.slide_id}): JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"GenericCollector (slide {self.slide_id}): Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return None

