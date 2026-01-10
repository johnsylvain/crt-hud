"""Pi-hole stats collector."""

import requests
from typing import Optional, Dict, Any
from .base import BaseCollector
from config import USE_MOCKS
from pathlib import Path


class PiHoleCollector(BaseCollector):
    """Collector for Pi-hole statistics."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 10))
        self.api_url = config.get("api_url", "")
        self.api_token = config.get("api_token", "")
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch Pi-hole statistics from API."""
        if USE_MOCKS:
            return self._fetch_mock_data()
        
        if not self.api_url:
            return None
        
        try:
            # Get summary stats
            url = f"{self.api_url.rstrip('/')}/api.php"
            params = {
                "summary": "",
            }
            if self.api_token:
                params["auth"] = self.api_token
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            summary = response.json()
            
            # Get top clients
            params_clients = {"topClients": "10"}
            if self.api_token:
                params_clients["auth"] = self.api_token
            
            clients_response = requests.get(url, params=params_clients, timeout=5)
            clients_response.raise_for_status()
            clients_data = clients_response.json()
            
            # Get top domains (blocked)
            params_domains = {"topBlocked": "10"}
            if self.api_token:
                params_domains["auth"] = self.api_token
            
            domains_response = requests.get(url, params=params_domains, timeout=5)
            domains_response.raise_for_status()
            domains_data = domains_response.json()
            
            return {
                "domains_being_blocked": summary.get("domains_being_blocked", 0),
                "dns_queries_today": summary.get("dns_queries_today", 0),
                "ads_blocked_today": summary.get("ads_blocked_today", 0),
                "ads_percentage_today": summary.get("ads_percentage_today", 0.0),
                "unique_clients": summary.get("unique_clients", 0),
                "status": summary.get("status", "unknown"),
                "top_clients": clients_data.get("topClients", {})[:5] if isinstance(clients_data.get("topClients"), list) else [],
                "top_blocked": domains_data.get("topBlocked", {})[:5] if isinstance(domains_data.get("topBlocked"), list) else [],
            }
        except requests.exceptions.RequestException as e:
            print(f"Pi-hole API request failed: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Pi-hole API response parse error: {e}")
            return None
    
    def _fetch_mock_data(self) -> Optional[Dict[str, Any]]:
        """Fetch mock data for testing."""
        mock_file = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "pihole_response.json"
        if mock_file.exists():
            import json
            try:
                with open(mock_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading mock data: {e}")
        
        # Return default mock data
        return {
            "domains_being_blocked": 100000,
            "dns_queries_today": 50000,
            "ads_blocked_today": 5000,
            "ads_percentage_today": 10.0,
            "unique_clients": 10,
            "status": "enabled",
            "top_clients": [],
            "top_blocked": [],
        }

