"""Plex stats collector."""

import requests
from typing import Optional, Dict, Any, List
from .base import BaseCollector
from config import USE_MOCKS
from pathlib import Path


class PlexCollector(BaseCollector):
    """Collector for Plex now playing statistics and bandwidth."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 5))
        self.api_url = config.get("api_url", "")
        self.api_token = config.get("api_token", "")
        self.bandwidth_data = None  # Cache for bandwidth stats
        self.bandwidth_cache_time = 0
        self.bandwidth_cache_ttl = config.get("bandwidth_cache_ttl", 5)  # Cache for 5 seconds
        
        # Debug logging
        self.debug_logs = []  # List of dicts with request/response info
        self.debug_log_max_entries = 20  # Keep last 20 requests
    
    def _process_plex_response(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Plex API response and extract session information."""
        # Plex JSON response structure can be:
        # Option 1: { "MediaContainer": { "size": int, "Metadata": [...] } } (wrapped - actual Plex API format)
        # Option 2: { "size": int, "Metadata": [...] } (direct - legacy format)
        
        print(f"Plex API: Processing response - data keys = {list(data.keys())}")
        print(f"Plex API: Full response data structure (first 1500 chars): {str(data)[:1500]}")
        
        # Check if response is wrapped in MediaContainer (actual Plex API format)
        media_container = data.get("MediaContainer")
        print(f"Plex API: MediaContainer value: {media_container}, type: {type(media_container)}")
        
        if media_container and isinstance(media_container, dict):
            print(f"Plex API: Found MediaContainer dict with keys: {list(media_container.keys())}")
            if "size" in media_container or "Metadata" in media_container:
                print(f"Plex API: Response is wrapped in MediaContainer - extracting data")
                size = media_container.get("size", 0)
                metadata = media_container.get("Metadata", [])
                print(f"Plex API: Extracted from MediaContainer - size={size}, metadata type={type(metadata)}")
                if isinstance(metadata, list):
                    print(f"Plex API: Metadata list length = {len(metadata)}")
                    if len(metadata) > 0:
                        print(f"Plex API: First metadata item type = {type(metadata[0])}, keys = {list(metadata[0].keys()) if isinstance(metadata[0], dict) else 'not a dict'}")
                elif isinstance(metadata, dict):
                    print(f"Plex API: Metadata is dict with keys: {list(metadata.keys())}")
                    print(f"Plex API: Metadata dict has Player key: {'Player' in metadata if isinstance(metadata, dict) else False}")
                    print(f"Plex API: Metadata dict has User key: {'User' in metadata if isinstance(metadata, dict) else False}")
                else:
                    print(f"Plex API: Metadata is unexpected type: {type(metadata)}, value preview: {str(metadata)[:200]}")
            else:
                print(f"Plex API: MediaContainer found but doesn't have size or Metadata keys")
                # Fall through to direct structure
                size = data.get("size", 0)
                metadata = data.get("Metadata", [])
        else:
            # Try direct structure (legacy format we were expecting)
            print(f"Plex API: Response is in direct format (no MediaContainer wrapper) - extracting from root")
            size = data.get("size", 0)
            metadata = data.get("Metadata", [])
        
        print(f"Plex API: Extracted size = {size}, metadata type = {type(metadata)}")
        
        # If no active sessions, return empty structure instead of None
        # This allows the renderer to show "NO STREAMS" instead of "NO DATA AVAILABLE"
        if size == 0:
            print("Plex API: Size is 0, returning empty structure")
            return {
                "session_count": 0,
                "sessions": [],
            }
        
        print(f"Plex API: Metadata type = {type(metadata)}, length = {len(metadata) if isinstance(metadata, (list, dict)) else 'N/A'}")
        
        # Ensure it's a list (can be single dict if only one session)
        if isinstance(metadata, dict):
            print("Plex API: Metadata is dict, converting to list")
            metadata = [metadata]
        elif not isinstance(metadata, list):
            print(f"Plex API: Metadata is unexpected type: {type(metadata)}, returning empty structure")
            return {
                "session_count": 0,
                "sessions": [],
            }
        
        if not metadata:
            print("Plex API: Metadata is empty, returning empty structure")
            return {
                "session_count": 0,
                "sessions": [],
            }
        
        print(f"Plex API: Processing {len(metadata)} session(s)")
        
        # Process sessions
        active_streams = []
        for i, session in enumerate(metadata):
            print(f"Plex API: Processing session {i+1}/{len(metadata)}")
            print(f"Plex API: Session keys = {list(session.keys())}")
            
            # Extract user information
            user_obj = session.get("User", {})
            print(f"Plex API: User object = {user_obj}, type = {type(user_obj)}")
            if isinstance(user_obj, dict):
                user = user_obj.get("title", "Unknown")
            else:
                user = "Unknown"
            print(f"Plex API: Extracted user = {user}")
            
            # Extract media information
            # Build title with context (e.g., "Artist - Album - Track" or "Series - Episode")
            base_title = session.get("title", "Unknown")
            type_ = session.get("type", "unknown")
            print(f"Plex API: Base title = {base_title}, type = {type_}")
            
            # For tracks (music): include artist and album if available
            if type_ == "track":
                grandparent_title = session.get("grandparentTitle", "")  # Artist
                parent_title = session.get("parentTitle", "")  # Album
                print(f"Plex API: Track - artist = {grandparent_title}, album = {parent_title}")
                if grandparent_title and parent_title:
                    title = f"{grandparent_title} - {parent_title} - {base_title}"
                elif grandparent_title:
                    title = f"{grandparent_title} - {base_title}"
                elif parent_title:
                    title = f"{parent_title} - {base_title}"
                else:
                    title = base_title
            # For episodes (TV shows): include series name
            elif type_ == "episode":
                grandparent_title = session.get("grandparentTitle", "")  # Series name
                if grandparent_title:
                    title = f"{grandparent_title} - {base_title}"
                else:
                    title = base_title
            # For movies or other types, use title as-is
            else:
                title = base_title
            
            print(f"Plex API: Final title = {title}")
            
            # Extract progress information
            view_offset = int(session.get("viewOffset", 0))  # milliseconds
            duration = int(session.get("duration", 0))  # milliseconds
            progress = (view_offset / duration * 100) if duration > 0 else 0
            print(f"Plex API: viewOffset = {view_offset}, duration = {duration}, progress = {progress:.2f}%")
            
            # Extract player state - only include "playing" sessions
            player_obj = session.get("Player", {})
            print(f"Plex API: Player object = {player_obj}, type = {type(player_obj)}")
            
            if isinstance(player_obj, dict):
                player_state = player_obj.get("state", "")
                print(f"Plex API: Player state = '{player_state}' (raw), type = {type(player_state)}")
                
                # Check if state is "playing" (case-insensitive)
                if player_state:
                    player_state_lower = str(player_state).lower().strip()
                    print(f"Plex API: Player state (normalized) = '{player_state_lower}'")
                    
                    # Only include playing sessions (skip paused/stopped/buffering/etc)
                    if player_state_lower != "playing":
                        print(f"Plex API: SKIPPING non-playing session: '{title}' (state: '{player_state}' -> '{player_state_lower}')")
                        print(f"Plex API: All Player keys: {list(player_obj.keys())}")
                        continue
                    else:
                        print(f"Plex API: INCLUDING playing session: '{title}' (state: '{player_state}')")
                else:
                    # If state is empty/missing, include it (might be playing but state not set)
                    print(f"Plex API: Warning: Player state is empty/missing for '{title}', including session anyway")
            else:
                # If no player info, assume playing (legacy behavior)
                print(f"Plex API: No Player object found for '{title}', assuming playing state")
            
            # Check for transcoding
            transcoding = False
            
            session_data = {
                "user": user,
                "title": title,
                "type": type_,
                "progress": progress,
                "view_offset": view_offset,
                "duration": duration,
                "transcoding": transcoding,
            }
            print(f"Plex API: Adding session data: {session_data}")
            active_streams.append(session_data)
        
        print(f"Plex API: Processed {len(metadata)} sessions, {len(active_streams)} active playing sessions")
        
        if not active_streams:
            print("Plex API: No active streams after processing (all filtered out), returning empty structure")
            # Return empty structure instead of None so renderer can display "NO STREAMS"
            return {
                "session_count": 0,
                "sessions": [],
            }
        
        result = {
            "session_count": len(active_streams),
            "sessions": active_streams,
        }
        print(f"Plex API: Returning result with {len(active_streams)} sessions: {result}")
        return result
    
    def _log_debug(self, endpoint: str, method: str, url: str, params: Dict = None, headers: Dict = None, 
                   status_code: int = None, response_text: str = None, error: str = None, response_data: Dict = None):
        """Log debug information for API requests."""
        import time
        import json
        
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
        
        # Mask sensitive information in params
        if log_entry["params"]:
            masked_params = log_entry["params"].copy()
            if "X-Plex-Token" in masked_params:
                masked_params["X-Plex-Token"] = masked_params["X-Plex-Token"][:8] + "..." if len(masked_params["X-Plex-Token"]) > 8 else "***"
            log_entry["params"] = masked_params
        
        self.debug_logs.append(log_entry)
        
        # Keep only last N entries
        if len(self.debug_logs) > self.debug_log_max_entries:
            self.debug_logs = self.debug_logs[-self.debug_log_max_entries:]
    
    def get_debug_logs(self) -> List[Dict[str, Any]]:
        """Get debug logs for this collector."""
        return self.debug_logs.copy()
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch Plex sessions (now playing) from API."""
        if USE_MOCKS:
            return self._fetch_mock_data()
        
        url = ""
        params = {}
        headers = {}
        
        if not self.api_url or not self.api_token:
            self._log_debug("sessions", "GET", "", error="Missing API URL or token")
            return None
        
        try:
            # Plex API endpoint for sessions
            url = f"{self.api_url.rstrip('/')}/status/sessions"
            
            # Plex API requires token and headers as query parameters for JSON response
            params = {
                "X-Plex-Token": self.api_token,
                "X-Plex-Product": "StatusBoard",
                "X-Plex-Version": "1.0",
                "X-Plex-Client-Identifier": "homelab-hud-plex-collector",
                "X-Plex-Platform": "Python",
            }
            
            # Accept JSON format (Plex will return JSON when Accept header is set)
            headers = {
                "Accept": "application/json"
            }
            
            print(f"Plex API: Fetching sessions from {url}")
            
            # Determine SSL verification: disable for local IPs and plex.direct (self-signed certs)
            # For production, you might want to enable verification for public Plex servers
            verify_ssl = False
            
            response = requests.get(url, params=params, headers=headers, timeout=10, verify=verify_ssl)
            status_code = response.status_code
            response_text = response.text
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                print(f"Plex API: Successfully parsed JSON response")
                print(f"Plex API: Response data structure - keys: {list(data.keys())}")
                print(f"Plex API: Response has 'MediaContainer': {'MediaContainer' in data}")
                print(f"Plex API: Response has 'size' at root: {'size' in data}")
                print(f"Plex API: Response has 'Metadata' at root: {'Metadata' in data}")
                
                # Check MediaContainer structure
                if "MediaContainer" in data:
                    mc = data["MediaContainer"]
                    print(f"Plex API: MediaContainer type: {type(mc)}")
                    if isinstance(mc, dict):
                        print(f"Plex API: MediaContainer keys: {list(mc.keys())}")
                        print(f"Plex API: MediaContainer size: {mc.get('size', 'NOT FOUND')}")
                        print(f"Plex API: MediaContainer has Metadata: {'Metadata' in mc}")
                
                # Log debug BEFORE processing
                self._log_debug("sessions", "GET", url, params, headers, status_code, response_text, response_data=data)
            except ValueError as e:
                error_msg = f"Failed to parse JSON: {e}"
                print(f"Plex API: {error_msg}")
                print(f"Plex API: Response content type: {response.headers.get('Content-Type', 'unknown')}")
                print(f"Plex API: Response preview: {response_text[:200]}")
                self._log_debug("sessions", "GET", url, params, headers, status_code, response_text, error=error_msg)
                return None
            
            # Process the response
            print(f"Plex API: About to process response with _process_plex_response()")
            result = self._process_plex_response(data)
            print(f"Plex API: _fetch_data returning result: {result}")
            print(f"Plex API: Result type: {type(result)}")
            if result:
                print(f"Plex API: Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                if isinstance(result, dict):
                    print(f"Plex API: Result session_count: {result.get('session_count', 'NOT FOUND')}")
                    print(f"Plex API: Result sessions length: {len(result.get('sessions', []))}")
            else:
                print(f"Plex API: WARNING - Result is None, data will not be displayed")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"Plex API request failed: {error_msg}")
            self._log_debug("sessions", "GET", url, params, headers, error=error_msg)
            return None
        except (KeyError, ValueError, TypeError) as e:
            error_msg = str(e)
            print(f"Plex API response parse error: {error_msg}")
            import traceback
            traceback.print_exc()
            self._log_debug("sessions", "GET", url, params, headers, error=error_msg)
            return None
    
    def has_active_streams(self) -> bool:
        """Check if there are active streams."""
        data = self.get_data()
        return data is not None and data.get("session_count", 0) > 0
    
    def _fetch_mock_data(self) -> Optional[Dict[str, Any]]:
        """Fetch mock data for testing."""
        mock_file = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "plex_active_response.json"
        if mock_file.exists():
            import json
            try:
                with open(mock_file, 'r') as f:
                    raw_data = json.load(f)
                    # If the mock data is in the raw Plex format, process it
                    if "Metadata" in raw_data:
                        return self._process_plex_response(raw_data)
                    else:
                        # Already in processed format
                        return raw_data
            except Exception as e:
                print(f"Error loading mock data: {e}")
                import traceback
                traceback.print_exc()
        
        # Return None to simulate no active streams
        return None
    
    def _process_bandwidth_response(self, data: Dict[str, Any], timespan: int = 6) -> Optional[Dict[str, Any]]:
        """Process Plex bandwidth API response and aggregate statistics."""
        from collections import defaultdict
        
        # Get device mapping
        devices = {}
        device_array = data.get("Device", [])
        if isinstance(device_array, dict):
            device_array = [device_array]
        
        for device in device_array:
            device_id = device.get("id")
            if device_id:
                devices[device_id] = {
                    "id": device_id,
                    "name": device.get("name", ""),
                    "platform": device.get("platform", ""),
                    "clientIdentifier": device.get("clientIdentifier", ""),
                }
        
        # Get account mapping
        accounts = {}
        account_array = data.get("Account", [])
        if isinstance(account_array, dict):
            account_array = [account_array]
        
        for account in account_array:
            account_id = account.get("id")
            if account_id:
                accounts[account_id] = {
                    "id": account_id,
                    "name": account.get("name", ""),
                }
        
        # Process bandwidth statistics
        bandwidth_array = data.get("StatisticsBandwidth", [])
        if isinstance(bandwidth_array, dict):
            bandwidth_array = [bandwidth_array]
        
        if not bandwidth_array:
            return None
        
        # Aggregate by device
        device_bytes = defaultdict(lambda: {"lan": 0, "wan": 0, "total": 0})
        account_bytes = defaultdict(lambda: {"lan": 0, "wan": 0, "total": 0})
        total_bytes = {"lan": 0, "wan": 0, "total": 0}
        
        # Get most recent timestamp to calculate current rate
        latest_timestamp = 0
        bytes_at_latest = defaultdict(int)
        
        for stat in bandwidth_array:
            account_id = stat.get("accountID")
            device_id = stat.get("deviceID")
            bytes_count = int(stat.get("bytes", 0))
            is_lan = stat.get("lan", False)
            timestamp = int(stat.get("at", 0))
            
            # Update latest timestamp
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
            
            # Aggregate by device
            if device_id:
                if is_lan:
                    device_bytes[device_id]["lan"] += bytes_count
                else:
                    device_bytes[device_id]["wan"] += bytes_count
                device_bytes[device_id]["total"] += bytes_count
                
                # Track bytes at latest timestamp for current rate calculation
                if timestamp == latest_timestamp:
                    bytes_at_latest[device_id] += bytes_count
            
            # Aggregate by account
            if account_id:
                if is_lan:
                    account_bytes[account_id]["lan"] += bytes_count
                else:
                    account_bytes[account_id]["wan"] += bytes_count
                account_bytes[account_id]["total"] += bytes_count
            
            # Total aggregation
            if is_lan:
                total_bytes["lan"] += bytes_count
            else:
                total_bytes["wan"] += bytes_count
            total_bytes["total"] += bytes_count
        
        # Calculate current bandwidth rate (bytes per second)
        # The timespan parameter indicates the time window, so we divide by it
        current_rates = {}
        for device_id, bytes_count in bytes_at_latest.items():
            # Rate is bytes per second (bytes / timespan seconds)
            current_rates[device_id] = bytes_count / timespan if timespan > 0 else 0
        
        # Build device statistics with names
        device_stats = []
        for device_id, stats in device_bytes.items():
            device_info = devices.get(device_id, {})
            device_stats.append({
                "id": device_id,
                "name": device_info.get("name", f"Device {device_id}"),
                "platform": device_info.get("platform", ""),
                "lan_bytes": stats["lan"],
                "wan_bytes": stats["wan"],
                "total_bytes": stats["total"],
                "current_rate_bps": current_rates.get(device_id, 0),  # bytes per second
            })
        
        # Sort by total bytes descending
        device_stats.sort(key=lambda x: x["total_bytes"], reverse=True)
        
        # Build account statistics
        account_stats = []
        for account_id, stats in account_bytes.items():
            account_info = accounts.get(account_id, {})
            account_stats.append({
                "id": account_id,
                "name": account_info.get("name", f"Account {account_id}"),
                "lan_bytes": stats["lan"],
                "wan_bytes": stats["wan"],
                "total_bytes": stats["total"],
            })
        
        # Sort by total bytes descending
        account_stats.sort(key=lambda x: x["total_bytes"], reverse=True)
        
        # Calculate overall current rate (total at latest timestamp / timespan)
        total_at_latest = sum(bytes_at_latest.values())
        overall_current_rate = total_at_latest / timespan if timespan > 0 else 0
        
        print(f"Plex Bandwidth: Total {total_bytes['total']} bytes (LAN: {total_bytes['lan']}, WAN: {total_bytes['wan']})")
        print(f"Plex Bandwidth: Current rate {overall_current_rate:.2f} bytes/sec")
        
        return {
            "timespan": timespan,
            "timestamp": latest_timestamp,
            "total": total_bytes,
            "current_rate_bps": overall_current_rate,  # Overall bytes per second
            "devices": device_stats,
            "accounts": account_stats,
        }
    
    def get_bandwidth_stats(self, timespan: int = 6) -> Optional[Dict[str, Any]]:
        """Fetch and return Plex bandwidth statistics."""
        import time
        
        # Check cache
        current_time = time.time()
        if (self.bandwidth_data is not None and 
            (current_time - self.bandwidth_cache_time) < self.bandwidth_cache_ttl):
            return self.bandwidth_data
        
        if USE_MOCKS:
            return self._fetch_bandwidth_mock_data(timespan)
        
        url = ""
        params = {}
        headers = {}
        
        if not self.api_url or not self.api_token:
            self._log_debug("bandwidth", "GET", "", error="Missing API URL or token")
            return None
        
        try:
            # Plex API endpoint for bandwidth statistics
            url = f"{self.api_url.rstrip('/')}/statistics/bandwidth"
            
            # Plex API requires token and headers as query parameters for JSON response
            params = {
                "timespan": timespan,
                "X-Plex-Token": self.api_token,
                "X-Plex-Product": "StatusBoard",
                "X-Plex-Version": "1.0",
                "X-Plex-Client-Identifier": "homelab-hud-plex-collector",
                "X-Plex-Platform": "Python",
            }
            
            # Accept JSON format
            headers = {
                "Accept": "application/json"
            }
            
            print(f"Plex Bandwidth API: Fetching from {url} (timespan={timespan}s)")
            
            # SSL verification disabled for local IPs and plex.direct
            verify_ssl = False
            
            response = requests.get(url, params=params, headers=headers, timeout=10, verify=verify_ssl)
            status_code = response.status_code
            response_text = response.text
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                self._log_debug("bandwidth", "GET", url, params, headers, status_code, response_text, response_data=data)
            except ValueError as e:
                error_msg = f"Failed to parse JSON: {e}"
                print(f"Plex Bandwidth API: {error_msg}")
                print(f"Plex Bandwidth API: Response content type: {response.headers.get('Content-Type', 'unknown')}")
                print(f"Plex Bandwidth API: Response preview: {response_text[:200]}")
                self._log_debug("bandwidth", "GET", url, params, headers, status_code, response_text, error=error_msg)
                return None
            
            # Process the response
            self.bandwidth_data = self._process_bandwidth_response(data, timespan)
            self.bandwidth_cache_time = current_time
            
            return self.bandwidth_data
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"Plex Bandwidth API request failed: {error_msg}")
            self._log_debug("bandwidth", "GET", url, params, headers, error=error_msg)
            return None
        except (KeyError, ValueError, TypeError) as e:
            error_msg = str(e)
            print(f"Plex Bandwidth API response parse error: {error_msg}")
            import traceback
            traceback.print_exc()
            self._log_debug("bandwidth", "GET", url, params, headers, error=error_msg)
            return None
    
    def _fetch_bandwidth_mock_data(self, timespan: int = 6) -> Optional[Dict[str, Any]]:
        """Fetch mock bandwidth data for testing."""
        mock_file = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "plex_bandwidth_response.json"
        if mock_file.exists():
            import json
            try:
                with open(mock_file, 'r') as f:
                    raw_data = json.load(f)
                    # If the mock data is in the raw Plex format, process it
                    if "StatisticsBandwidth" in raw_data:
                        return self._process_bandwidth_response(raw_data, timespan)
                    else:
                        # Already in processed format
                        return raw_data
            except Exception as e:
                print(f"Error loading mock bandwidth data: {e}")
                import traceback
                traceback.print_exc()
        
        # Return None if no mock data available
        return None

