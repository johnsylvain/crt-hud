"""Flask API routes for web UI."""

from flask import Flask, jsonify, request, send_file
from typing import Dict, Any
import io
import sys
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image
# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_slides_config, save_slides_config, get_api_config, save_api_config, DATA_DIR
from backend.api.models import Slide, APIConfig
from backend.display.renderer import SlideRenderer
from backend.display.video_output import create_video_output
from backend.slides import SlideTypeRegistry


def create_app(collectors: Dict[str, Any] = None, template_folder: str = None, static_folder: str = None, app_instance: Any = None) -> Flask:
    """
    Create Flask application.
    
    Args:
        collectors: Dictionary of collector instances (for preview/stats endpoints)
        template_folder: Path to templates directory
        static_folder: Path to static files directory
        app_instance: Reference to main HomelabHUD instance (for current slide tracking)
    
    Returns:
        Flask app instance
    """
    import os
    from pathlib import Path
    
    # Default paths
    if template_folder is None:
        template_folder = str(Path(__file__).parent.parent.parent / 'frontend' / 'templates')
    if static_folder is None:
        static_folder = str(Path(__file__).parent.parent.parent / 'frontend' / 'static')
    
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    renderer = SlideRenderer()
    
    # Store app_instance for current slide access
    app.config['APP_INSTANCE'] = app_instance
    
    @app.route("/api/slides", methods=["GET"])
    def get_slides():
        """Get all slides."""
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Ensure all slides have refresh_duration and clean up deprecated fields (backwards compatibility)
        for slide in slides:
            if "refresh_duration" not in slide:
                slide["refresh_duration"] = 5
            # Remove deprecated condition_type if it exists
            if "condition_type" in slide:
                del slide["condition_type"]
        
        config["slides"] = slides
        return jsonify(config)
    
    @app.route("/api/slides", methods=["PUT"])
    def update_all_slides():
        """Update entire slides configuration."""
        data = request.get_json()
        
        # Validate structure
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid configuration: must be a JSON object"}), 400
        
        if "slides" not in data:
            return jsonify({"error": "Invalid configuration: missing 'slides' array"}), 400
        
        if not isinstance(data["slides"], list):
            return jsonify({"error": "Invalid configuration: 'slides' must be an array"}), 400
        
        # Validate each slide
        for slide in data["slides"]:
            if not isinstance(slide, dict):
                return jsonify({"error": "Invalid configuration: each slide must be an object"}), 400
            if "id" not in slide or "type" not in slide:
                return jsonify({"error": "Invalid configuration: each slide must have 'id' and 'type'"}), 400
        
        # Save the configuration
        try:
            save_slides_config(data)
        except (IOError, OSError, PermissionError) as e:
            error_msg = str(e)
            if isinstance(e, PermissionError):
                error_msg = f"Permission denied: Cannot write to slides.json. Check file permissions on the data directory."
            return jsonify({"error": error_msg, "details": f"Failed to save configuration: {e}"}), 500
        
        return jsonify({"success": True, "config": data})
    
    @app.route("/api/slides", methods=["POST"])
    def create_slide():
        """Create a new slide."""
        data = request.get_json()
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Generate new ID
        max_id = max([s.get("id", 0) for s in slides], default=0)
        new_id = max_id + 1
        
        # Create new slide
        new_slide = {
            "id": new_id,
            "type": data.get("type", ""),
            "title": data.get("title", "Untitled"),
            "duration": data.get("duration", 10),
            "refresh_duration": data.get("refresh_duration", 5),
            "order": data.get("order", len(slides)),
            "conditional": data.get("conditional", False),
        }
        
        # Per-slide service configuration (NEW)
        slide_type = data.get("type", "")
        slide_type_obj = SlideTypeRegistry.get(slide_type) if slide_type else None
        
        # Handle service_config if present
        if data.get("service_config") and isinstance(data.get("service_config"), dict):
            # Only include service_config if it has values
            service_config = {k: v for k, v in data.get("service_config", {}).items() if v}
            if service_config:
                new_slide["service_config"] = service_config
        
        # Handle api_config for custom slides
        if slide_type == "custom" and data.get("api_config"):
            api_config = data.get("api_config")
            if isinstance(api_config, dict) and api_config.get("endpoint"):
                new_slide["api_config"] = api_config
        
        # Extract direct fields from data (like city, temp_unit, text, image_path, font_size, etc.)
        # These should be at root level, not in service_config
        if slide_type == "weather":
            if data.get("city"):
                new_slide["city"] = data.get("city")
            if data.get("temp_unit"):
                new_slide["temp_unit"] = data.get("temp_unit", "C")
        
        if slide_type == "image" and data.get("image_path"):
            new_slide["image_path"] = data.get("image_path")
        
        if slide_type == "static_text":
            if data.get("text"):
                new_slide["text"] = data.get("text")
            if data.get("font_size"):
                new_slide["font_size"] = data.get("font_size", "medium")
            if data.get("text_align"):
                new_slide["text_align"] = data.get("text_align", "left")
            if data.get("vertical_align"):
                new_slide["vertical_align"] = data.get("vertical_align", "center")
            if data.get("text_color"):
                new_slide["text_color"] = data.get("text_color", "text")
        
        if slide_type == "custom":
            if data.get("layout"):
                new_slide["layout"] = data.get("layout")
            if data.get("widgets"):
                new_slide["widgets"] = data.get("widgets")
        
        slides.append(new_slide)
        config["slides"] = slides
        
        try:
            save_slides_config(config)
        except (IOError, OSError, PermissionError) as e:
            error_msg = str(e)
            if isinstance(e, PermissionError):
                error_msg = f"Permission denied: Cannot write to slides.json. Check file permissions on the data directory."
            return jsonify({"error": error_msg, "details": f"Failed to save slide: {e}"}), 500
        
        return jsonify(new_slide), 201
    
    @app.route("/api/slides/<int:slide_id>", methods=["PUT"])
    def update_slide(slide_id):
        """Update a slide."""
        data = request.get_json()
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find and update slide
        for i, slide in enumerate(slides):
            if slide.get("id") == slide_id:
                # Update slide with new data
                slides[i].update(data)
                slides[i]["id"] = slide_id  # Ensure ID doesn't change
                
                # Ensure refresh_duration exists
                if "refresh_duration" not in slides[i]:
                    slides[i]["refresh_duration"] = 5
                
                # Remove deprecated condition_type if present
                if "condition_type" in slides[i]:
                    del slides[i]["condition_type"]
                
                config["slides"] = slides
                try:
                    save_slides_config(config)
                except (IOError, OSError, PermissionError) as e:
                    error_msg = str(e)
                    if isinstance(e, PermissionError):
                        error_msg = f"Permission denied: Cannot write to slides.json. Check file permissions on the data directory."
                    return jsonify({"error": error_msg, "details": f"Failed to update slide: {e}"}), 500
                
                return jsonify(slides[i])
        
        return jsonify({"error": "Slide not found"}), 404
    
    @app.route("/api/slides/<int:slide_id>", methods=["DELETE"])
    def delete_slide(slide_id):
        """Delete a slide."""
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find and remove slide
        for i, slide in enumerate(slides):
            if slide.get("id") == slide_id:
                slides.pop(i)
                config["slides"] = slides
                try:
                    save_slides_config(config)
                except (IOError, OSError, PermissionError) as e:
                    error_msg = str(e)
                    if isinstance(e, PermissionError):
                        error_msg = f"Permission denied: Cannot write to slides.json. Check file permissions on the data directory."
                    return jsonify({"error": error_msg, "details": f"Failed to delete slide: {e}"}), 500
                
                return jsonify({"success": True})
        
        return jsonify({"error": "Slide not found"}), 404
    
    @app.route("/api/slides/reorder", methods=["POST"])
    def reorder_slides():
        """Reorder slides based on array of IDs."""
        data = request.get_json()
        slide_ids = data.get("slide_ids", [])
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Create lookup by ID
        slide_dict = {s.get("id"): s for s in slides}
        
        # Reorder slides
        reordered = []
        for i, slide_id in enumerate(slide_ids):
            if slide_id in slide_dict:
                slide = slide_dict[slide_id]
                slide["order"] = i
                reordered.append(slide)
        
        # Add any slides not in the reorder list
        for slide in slides:
            if slide.get("id") not in slide_ids:
                slide["order"] = len(reordered)
                reordered.append(slide)
        
        config["slides"] = sorted(reordered, key=lambda x: x.get("order", 0))
        try:
            save_slides_config(config)
        except (IOError, OSError, PermissionError) as e:
            error_msg = str(e)
            if isinstance(e, PermissionError):
                error_msg = f"Permission denied: Cannot write to slides.json. Check file permissions on the data directory."
            return jsonify({"error": error_msg, "details": f"Failed to reorder slides: {e}"}), 500
        
        return jsonify(config)
    
    @app.route("/api/slides/types/<type_name>/schema", methods=["GET"])
    def get_slide_type_schema(type_name: str):
        """Get configuration schema for a slide type."""
        slide_type = SlideTypeRegistry.get(type_name)
        if not slide_type:
            return jsonify({"error": f"Unknown slide type: {type_name}"}), 404
        
        schema = slide_type.get_config_schema()
        return jsonify(schema)
    
    @app.route("/api/slides/types", methods=["GET"])
    def get_all_slide_types():
        """Get all available slide types with their display names."""
        types = SlideTypeRegistry.get_all_types()
        return jsonify({"types": types})
    
    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Get API configuration (for weather and other global configs)."""
        config = get_api_config()
        return jsonify(config)
    
    @app.route("/api/config", methods=["PUT"])
    def update_config():
        """Update API configuration (for weather and other global configs)."""
        data = request.get_json()
        try:
            save_api_config(data)
        except (IOError, OSError, PermissionError) as e:
            error_msg = str(e)
            if isinstance(e, PermissionError):
                error_msg = f"Permission denied: Cannot write to api_config.json. Check file permissions on the data directory."
            return jsonify({"error": error_msg, "details": f"Failed to save configuration: {e}"}), 500
        
        return jsonify({"success": True})
    
    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Get current stats from all collectors."""
        if collectors is None:
            return jsonify({"error": "Collectors not available"}), 500
        
        stats = {}
        
        if "arm" in collectors:
            stats["arm"] = collectors["arm"].get_data()
        if "pihole" in collectors:
            stats["pihole"] = collectors["pihole"].get_data()
        if "plex" in collectors:
            stats["plex"] = collectors["plex"].get_data()
        if "system" in collectors:
            stats["system"] = collectors["system"].get_data()
        if "weather" in collectors:
            stats["weather"] = collectors["weather"].get_data()
        
        return jsonify(stats)
    
    @app.route("/api/stats/plex/bandwidth", methods=["GET"])
    def get_plex_bandwidth():
        """Get Plex bandwidth statistics."""
        if collectors is None or "plex" not in collectors:
            return jsonify({"error": "Plex collector not available"}), 500
        
        timespan = request.args.get("timespan", 6, type=int)
        plex_collector = collectors["plex"]
        
        # Call the bandwidth stats method
        bandwidth_stats = plex_collector.get_bandwidth_stats(timespan=timespan)
        
        if bandwidth_stats is None:
            return jsonify({"error": "Failed to fetch bandwidth stats"}), 500
        
        return jsonify(bandwidth_stats)
    
    @app.route("/api/debug/plex", methods=["GET"])
    def get_plex_debug():
        """Get Plex collector debug logs from all plex slides."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Try to get collectors from running app instance first
        app_instance = app.config.get('APP_INSTANCE')
        stored_collectors = {}
        if app_instance and hasattr(app_instance, 'slide_collectors'):
            with app_instance.slide_collectors_lock:
                stored_collectors = app_instance.slide_collectors.copy()
        
        # Find all plex_now_playing slides and aggregate their debug logs
        all_logs = []
        plex_slides_info = []
        api_url = ""
        has_token = False
        
        for slide in slides:
            if slide.get("type") == "plex_now_playing":
                slide_id = slide.get("id")
                slide_title = slide.get("title", f"Slide {slide_id}")
                
                collector = None
                logs = []
                
                # Try to get stored collector first (has historical logs from display loop)
                if slide_id in stored_collectors:
                    collector = stored_collectors[slide_id]
                    if hasattr(collector, "get_debug_logs"):
                        logs = collector.get_debug_logs()
                        print(f"Found stored Plex collector for slide {slide_id} with {len(logs)} log entries")
                
                # Create collector if we don't have one yet
                slide_type = SlideTypeRegistry.get("plex_now_playing")
                if not collector and slide_type:
                    try:
                        config_data = {
                            "service_config": slide.get("service_config", {}),
                            "api_config": slide.get("api_config")
                        }
                        collector = slide_type.create_collector(config_data)
                        print(f"Created new Plex collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Error creating Plex collector for slide {slide_id}: {e}")
                        collector = None
                
                # Always force a collection to ensure we have at least one log entry
                if collector and hasattr(collector, "_fetch_data"):
                    try:
                        print(f"Forcing Plex collection for slide {slide_id} to ensure debug logs exist")
                        collector._fetch_data()  # This will populate debug logs via _log_debug
                        
                        # Get logs after forced collection
                        if hasattr(collector, "get_debug_logs"):
                            logs = collector.get_debug_logs()
                            print(f"After forced collection, Plex slide {slide_id} has {len(logs)} log entries")
                    except Exception as e:
                        print(f"Error forcing Plex collection for debug logs: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Store collector in app_instance for future debug log access
                if collector and app_instance and hasattr(app_instance, 'slide_collectors'):
                    with app_instance.slide_collectors_lock:
                        app_instance.slide_collectors[slide_id] = collector
                        print(f"Stored Plex collector for slide {slide_id} in app_instance")
                
                # Extract API info from first collector we find
                if collector and not api_url:
                    api_url = collector.api_url if hasattr(collector, "api_url") else ""
                    has_token = bool(collector.api_token) if hasattr(collector, "api_token") else False
                
                # Add slide info to each log entry
                if logs:
                    for log in logs:
                        log_with_slide = log.copy()
                        log_with_slide["slide_id"] = slide_id
                        log_with_slide["slide_title"] = slide_title
                        all_logs.append(log_with_slide)
                
                plex_slides_info.append({
                    "slide_id": slide_id,
                    "slide_title": slide_title,
                    "log_count": len(logs),
                    "api_url": collector.api_url if collector and hasattr(collector, "api_url") else "",
                    "has_token": bool(collector.api_token) if collector and hasattr(collector, "api_token") else False
                })
        
        # Sort logs by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Format logs with readable timestamps
        from datetime import datetime
        formatted_logs = []
        for log in all_logs:
            formatted_log = log.copy()
            if "timestamp" in formatted_log:
                formatted_log["timestamp_readable"] = datetime.fromtimestamp(formatted_log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            formatted_logs.append(formatted_log)
        
        return jsonify({
            "collector": "plex",
            "plex_slides": plex_slides_info,
            "api_url": api_url,
            "has_token": has_token,
            "logs": formatted_logs,
            "log_count": len(formatted_logs),
            "total_slides": len(plex_slides_info)
        })
    
    @app.route("/api/debug/plex/test", methods=["POST"])
    def test_plex_connection():
        """Test Plex API connection by forcing a collection on the first plex slide."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first plex_now_playing slide for testing
        plex_slide = None
        for slide in slides:
            if slide.get("type") == "plex_now_playing":
                plex_slide = slide
                break
        
        if not plex_slide:
            return jsonify({"error": "No Plex slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("plex_now_playing")
        if not slide_type:
            return jsonify({"error": "Plex slide type not available"}), 500
        
        # Create collector for testing
        collector = None
        try:
            config_data = {
                "service_config": plex_slide.get("service_config", {}),
                "api_config": plex_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            print(f"Error creating Plex collector for test: {e}")
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "Plex collector could not be created"}), 500
        
        # Force a fetch (bypasses cache)
        result = None
        logs = []
        if hasattr(collector, "_fetch_data"):
            if hasattr(collector, "clear_cache"):
                collector.clear_cache()
            result = collector._fetch_data()
            if hasattr(collector, "get_debug_logs"):
                logs = collector.get_debug_logs()
        
        return jsonify({
            "success": result is not None,
            "result": result,
            "result_type": type(result).__name__ if result else None,
            "result_keys": list(result.keys()) if isinstance(result, dict) else None,
            "has_active_streams": collector.has_active_streams() if hasattr(collector, "has_active_streams") else None,
            "latest_log": logs[-1] if logs else None
        })
    
    @app.route("/api/debug/plex/data", methods=["GET"])
    def get_plex_data():
        """Get current Plex data (bypassing cache) from the first plex slide."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first plex_now_playing slide
        plex_slide = None
        for slide in slides:
            if slide.get("type") == "plex_now_playing":
                plex_slide = slide
                break
        
        if not plex_slide:
            return jsonify({"error": "No Plex slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("plex_now_playing")
        if not slide_type:
            return jsonify({"error": "Plex slide type not available"}), 500
        
        # Create collector
        collector = None
        try:
            config_data = {
                "service_config": plex_slide.get("service_config", {}),
                "api_config": plex_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "Plex collector could not be created"}), 500
        
        # Get cached data first
        cached_data = None
        if hasattr(collector, "get_data"):
            cached_data = collector.get_data()
        
        # Force fresh fetch by clearing cache
        fresh_data = None
        if hasattr(collector, "clear_cache"):
            collector.clear_cache()
        if hasattr(collector, "_fetch_data"):
            fresh_data = collector._fetch_data()
        
        # Check what get_data returns after fresh fetch
        final_data = None
        if hasattr(collector, "get_data"):
            final_data = collector.get_data()
        
        return jsonify({
            "cached_data_before": cached_data,
            "cached_data_type": type(cached_data).__name__ if cached_data is not None else "None",
            "fresh_fetch_result": fresh_data,
            "fresh_data_type": type(fresh_data).__name__ if fresh_data is not None else "None",
            "get_data_after_fresh": final_data,
            "final_data_type": type(final_data).__name__ if final_data is not None else "None",
            "has_active_streams": collector.has_active_streams() if hasattr(collector, "has_active_streams") else None,
        })
    
    @app.route("/api/debug/arm", methods=["GET"])
    def get_arm_debug():
        """Get ARM collector debug logs from all ARM slides."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Try to get collectors from running app instance first
        app_instance = app.config.get('APP_INSTANCE')
        stored_collectors = {}
        if app_instance and hasattr(app_instance, 'slide_collectors'):
            with app_instance.slide_collectors_lock:
                stored_collectors = app_instance.slide_collectors.copy()
        
        # Find all arm_rip_progress slides and aggregate their debug logs
        all_logs = []
        arm_slides_info = []
        api_url = ""
        has_key = False
        endpoint = ""
        
        for slide in slides:
            if slide.get("type") == "arm_rip_progress":
                slide_id = slide.get("id")
                slide_title = slide.get("title", f"Slide {slide_id}")
                
                collector = None
                logs = []
                
                # Try to get stored collector first (has historical logs from display loop)
                if slide_id in stored_collectors:
                    collector = stored_collectors[slide_id]
                    if hasattr(collector, "get_debug_logs"):
                        logs = collector.get_debug_logs()
                        print(f"Found stored ARM collector for slide {slide_id} with {len(logs)} log entries")
                
                # Create collector if we don't have one yet
                slide_type = SlideTypeRegistry.get("arm_rip_progress")
                if not collector and slide_type:
                    try:
                        config_data = {
                            "service_config": slide.get("service_config", {}),
                            "api_config": slide.get("api_config")
                        }
                        collector = slide_type.create_collector(config_data)
                        print(f"Created new ARM collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Error creating ARM collector for slide {slide_id}: {e}")
                        collector = None
                
                # Always force a collection to ensure we have at least one log entry
                if collector and hasattr(collector, "_fetch_data"):
                    try:
                        print(f"Forcing ARM collection for slide {slide_id} to ensure debug logs exist")
                        collector._fetch_data()  # This will populate debug logs via _log_debug
                        
                        # Get logs after forced collection
                        if hasattr(collector, "get_debug_logs"):
                            logs = collector.get_debug_logs()
                            print(f"After forced collection, ARM slide {slide_id} has {len(logs)} log entries")
                    except Exception as e:
                        print(f"Error forcing ARM collection for debug logs: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Store collector in app_instance for future debug log access
                if collector and app_instance and hasattr(app_instance, 'slide_collectors'):
                    with app_instance.slide_collectors_lock:
                        app_instance.slide_collectors[slide_id] = collector
                        print(f"Stored ARM collector for slide {slide_id} in app_instance")
                
                # Extract API info from first collector we find
                if collector and not api_url:
                    api_url = collector.api_url if hasattr(collector, "api_url") else ""
                    has_key = bool(collector.api_key) if hasattr(collector, "api_key") else False
                    endpoint = collector.endpoint if hasattr(collector, "endpoint") else ""
                
                # Add slide info to each log entry
                if logs:
                    for log in logs:
                        log_with_slide = log.copy()
                        log_with_slide["slide_id"] = slide_id
                        log_with_slide["slide_title"] = slide_title
                        all_logs.append(log_with_slide)
                
                arm_slides_info.append({
                    "slide_id": slide_id,
                    "slide_title": slide_title,
                    "log_count": len(logs),
                    "api_url": collector.api_url if collector and hasattr(collector, "api_url") else "",
                    "has_key": bool(collector.api_key) if collector and hasattr(collector, "api_key") else False,
                    "endpoint": collector.endpoint if collector and hasattr(collector, "endpoint") else ""
                })
        
        # Sort logs by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Format logs with readable timestamps
        from datetime import datetime
        formatted_logs = []
        for log in all_logs:
            formatted_log = log.copy()
            if "timestamp" in formatted_log:
                formatted_log["timestamp_readable"] = datetime.fromtimestamp(formatted_log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            formatted_logs.append(formatted_log)
        
        return jsonify({
            "collector": "arm",
            "arm_slides": arm_slides_info,
            "api_url": api_url,
            "has_key": has_key,
            "endpoint": endpoint,
            "logs": formatted_logs,
            "log_count": len(formatted_logs),
            "total_slides": len(arm_slides_info)
        })
    
    @app.route("/api/debug/arm/test", methods=["POST"])
    def test_arm_connection():
        """Test ARM API connection by forcing a collection on the first ARM slide."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first arm_rip_progress slide for testing
        arm_slide = None
        for slide in slides:
            if slide.get("type") == "arm_rip_progress":
                arm_slide = slide
                break
        
        if not arm_slide:
            return jsonify({"error": "No ARM slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("arm_rip_progress")
        if not slide_type:
            return jsonify({"error": "ARM slide type not available"}), 500
        
        # Create collector for testing
        collector = None
        try:
            config_data = {
                "service_config": arm_slide.get("service_config", {}),
                "api_config": arm_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            print(f"Error creating ARM collector for test: {e}")
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "ARM collector could not be created"}), 500
        
        # Force a fetch (bypasses cache)
        result = None
        logs = []
        if hasattr(collector, "_fetch_data"):
            if hasattr(collector, "clear_cache"):
                collector.clear_cache()
            result = collector._fetch_data()
            if hasattr(collector, "get_debug_logs"):
                logs = collector.get_debug_logs()
        
        return jsonify({
            "success": result is not None,
            "result": result,
            "result_type": type(result).__name__ if result else None,
            "result_keys": list(result.keys()) if isinstance(result, dict) else None,
            "has_active_rip": collector.has_active_rip() if hasattr(collector, "has_active_rip") else None,
            "latest_log": logs[-1] if logs else None
        })
    
    @app.route("/api/debug/arm/data", methods=["GET"])
    def get_arm_data():
        """Get current ARM data (bypassing cache) from the first ARM slide."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first arm_rip_progress slide
        arm_slide = None
        for slide in slides:
            if slide.get("type") == "arm_rip_progress":
                arm_slide = slide
                break
        
        if not arm_slide:
            return jsonify({"error": "No ARM slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("arm_rip_progress")
        if not slide_type:
            return jsonify({"error": "ARM slide type not available"}), 500
        
        # Create collector
        collector = None
        try:
            config_data = {
                "service_config": arm_slide.get("service_config", {}),
                "api_config": arm_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "ARM collector could not be created"}), 500
        
        # Get cached data first
        cached_data = None
        if hasattr(collector, "get_data"):
            cached_data = collector.get_data()
        
        # Force fresh fetch by clearing cache
        fresh_data = None
        if hasattr(collector, "clear_cache"):
            collector.clear_cache()
        if hasattr(collector, "_fetch_data"):
            fresh_data = collector._fetch_data()
        
        # Check what get_data returns after fresh fetch
        final_data = None
        if hasattr(collector, "get_data"):
            final_data = collector.get_data()
        
        return jsonify({
            "cached_data_before": cached_data,
            "cached_data_type": type(cached_data).__name__ if cached_data is not None else "None",
            "fresh_fetch_result": fresh_data,
            "fresh_data_type": type(fresh_data).__name__ if fresh_data is not None else "None",
            "get_data_after_fresh": final_data,
            "final_data_type": type(final_data).__name__ if final_data is not None else "None",
            "has_active_rip": collector.has_active_rip() if hasattr(collector, "has_active_rip") else None,
        })
    
    @app.route("/api/debug/octopi", methods=["GET"])
    def get_octopi_debug():
        """Get OctoPrint collector debug logs from all OctoPi slides."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Try to get collectors from running app instance first
        app_instance = app.config.get('APP_INSTANCE')
        stored_collectors = {}
        if app_instance and hasattr(app_instance, 'slide_collectors'):
            with app_instance.slide_collectors_lock:
                stored_collectors = app_instance.slide_collectors.copy()
        
        # Find all octopi_print_status slides and aggregate their debug logs
        all_logs = []
        octopi_slides_info = []
        api_url = ""
        has_key = False
        
        for slide in slides:
            if slide.get("type") == "octopi_print_status":
                slide_id = slide.get("id")
                slide_title = slide.get("title", f"Slide {slide_id}")
                
                collector = None
                logs = []
                
                # Try to get stored collector first (has historical logs from display loop)
                if slide_id in stored_collectors:
                    collector = stored_collectors[slide_id]
                    if hasattr(collector, "get_debug_logs"):
                        logs = collector.get_debug_logs()
                        print(f"Found stored OctoPrint collector for slide {slide_id} with {len(logs)} log entries")
                
                # Create collector if we don't have one yet
                slide_type = SlideTypeRegistry.get("octopi_print_status")
                if not collector and slide_type:
                    try:
                        config_data = {
                            "service_config": slide.get("service_config", {}),
                            "api_config": slide.get("api_config")
                        }
                        collector = slide_type.create_collector(config_data)
                        print(f"Created new OctoPrint collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Error creating OctoPrint collector for slide {slide_id}: {e}")
                        collector = None
                
                # Always force a collection to ensure we have at least one log entry
                if collector and hasattr(collector, "_fetch_data"):
                    try:
                        print(f"Forcing OctoPrint collection for slide {slide_id} to ensure debug logs exist")
                        collector._fetch_data()  # This will populate debug logs via _log_debug
                        
                        # Get logs after forced collection
                        if hasattr(collector, "get_debug_logs"):
                            logs = collector.get_debug_logs()
                            print(f"After forced collection, OctoPrint slide {slide_id} has {len(logs)} log entries")
                    except Exception as e:
                        print(f"Error forcing OctoPrint collection for debug logs: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Store collector in app_instance for future debug log access
                if collector and app_instance and hasattr(app_instance, 'slide_collectors'):
                    with app_instance.slide_collectors_lock:
                        app_instance.slide_collectors[slide_id] = collector
                        print(f"Stored OctoPrint collector for slide {slide_id} in app_instance")
                
                # Extract API info from first collector we find
                if collector and not api_url:
                    api_url = collector.api_url if hasattr(collector, "api_url") else ""
                    has_key = bool(collector.api_key) if hasattr(collector, "api_key") else False
                
                # Add slide info to each log entry
                if logs:
                    for log in logs:
                        log_with_slide = log.copy()
                        log_with_slide["slide_id"] = slide_id
                        log_with_slide["slide_title"] = slide_title
                        all_logs.append(log_with_slide)
                
                octopi_slides_info.append({
                    "slide_id": slide_id,
                    "slide_title": slide_title,
                    "log_count": len(logs),
                    "api_url": collector.api_url if collector and hasattr(collector, "api_url") else "",
                    "has_key": bool(collector.api_key) if collector and hasattr(collector, "api_key") else False,
                })
        
        # Sort logs by timestamp (newest first)
        all_logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Format timestamps for display
        from datetime import datetime
        for log in all_logs:
            timestamp = log.get("timestamp", 0)
            if timestamp:
                log["timestamp_readable"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "logs": all_logs,
            "log_count": len(all_logs),
            "slides": octopi_slides_info,
            "api_url": api_url,
            "has_key": has_key,
        })
    
    @app.route("/api/debug/octopi/test", methods=["POST"])
    def test_octopi_connection():
        """Test OctoPrint connection by forcing a fetch."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first octopi_print_status slide
        octopi_slide = None
        for slide in slides:
            if slide.get("type") == "octopi_print_status":
                octopi_slide = slide
                break
        
        if not octopi_slide:
            return jsonify({"error": "No OctoPrint slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("octopi_print_status")
        if not slide_type:
            return jsonify({"error": "OctoPrint slide type not available"}), 500
        
        # Create collector
        collector = None
        try:
            config_data = {
                "service_config": octopi_slide.get("service_config", {}),
                "api_config": octopi_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "OctoPrint collector could not be created"}), 500
        
        # Force fetch
        result = None
        logs = []
        if hasattr(collector, "_fetch_data"):
            result = collector._fetch_data()
            if hasattr(collector, "get_debug_logs"):
                logs = collector.get_debug_logs()
        
        return jsonify({
            "success": result is not None,
            "result": result,
            "result_type": type(result).__name__ if result else None,
            "result_keys": list(result.keys()) if isinstance(result, dict) else None,
            "is_printing": result.get("is_printing", False) if isinstance(result, dict) else None,
            "latest_log": logs[-1] if logs else None
        })
    
    @app.route("/api/debug/octopi/data", methods=["GET"])
    def get_octopi_data():
        """Get current OctoPrint data (bypassing cache) from the first OctoPrint slide."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first octopi_print_status slide
        octopi_slide = None
        for slide in slides:
            if slide.get("type") == "octopi_print_status":
                octopi_slide = slide
                break
        
        if not octopi_slide:
            return jsonify({"error": "No OctoPrint slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("octopi_print_status")
        if not slide_type:
            return jsonify({"error": "OctoPrint slide type not available"}), 500
        
        # Create collector
        collector = None
        try:
            config_data = {
                "service_config": octopi_slide.get("service_config", {}),
                "api_config": octopi_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to create collector: {str(e)}"}), 500
        
        if not collector:
            return jsonify({"error": "OctoPrint collector could not be created"}), 500
        
        # Get cached data first
        cached_data = None
        if hasattr(collector, "get_data"):
            cached_data = collector.get_data()
        
        # Force fresh fetch by clearing cache
        fresh_data = None
        if hasattr(collector, "clear_cache"):
            collector.clear_cache()
        if hasattr(collector, "_fetch_data"):
            fresh_data = collector._fetch_data()
        
        # Check what get_data returns after fresh fetch
        final_data = None
        if hasattr(collector, "get_data"):
            final_data = collector.get_data()
        
        return jsonify({
            "cached_data_before": cached_data,
            "cached_data_type": type(cached_data).__name__ if cached_data is not None else "None",
            "fresh_fetch_result": fresh_data,
            "fresh_data_type": type(fresh_data).__name__ if fresh_data is not None else "None",
            "get_data_after_fresh": final_data,
            "final_data_type": type(final_data).__name__ if final_data is not None else "None",
            "is_printing": final_data.get("is_printing", False) if isinstance(final_data, dict) else None,
        })
    
    @app.route("/api/debug/system", methods=["GET"])
    def get_system_debug():
        """Get System collector debug logs from all system slides."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Try to get collectors from running app instance first
        app_instance = app.config.get('APP_INSTANCE')
        stored_collectors = {}
        if app_instance and hasattr(app_instance, 'slide_collectors'):
            with app_instance.slide_collectors_lock:
                stored_collectors = app_instance.slide_collectors.copy()
        
        # Find all system_stats slides and aggregate their debug logs
        all_logs = []
        system_slides_info = []
        
        for slide in slides:
            if slide.get("type") == "system_stats":
                slide_id = slide.get("id")
                slide_title = slide.get("title", f"Slide {slide_id}")
                
                collector = None
                logs = []
                
                # Try to get stored collector first (has historical logs from display loop)
                if slide_id in stored_collectors:
                    collector = stored_collectors[slide_id]
                    if hasattr(collector, "get_debug_logs"):
                        logs = collector.get_debug_logs()
                        print(f"Found stored collector for slide {slide_id} with {len(logs)} log entries")
                
                # Create collector if we don't have one yet
                slide_type = SlideTypeRegistry.get("system_stats")
                if not collector and slide_type:
                    try:
                        config_data = {
                            "service_config": slide.get("service_config", {}),
                            "api_config": slide.get("api_config")
                        }
                        collector = slide_type.create_collector(config_data)
                        print(f"Created new collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Error creating collector for slide {slide_id}: {e}")
                        collector = None
                
                # Always force a collection to ensure we have at least one log entry
                # This is needed because stored collectors might not have logs if display loop hasn't run
                if collector and hasattr(collector, "_fetch_data"):
                    try:
                        print(f"Forcing collection for slide {slide_id} to ensure debug logs exist")
                        collector._fetch_data()  # This will populate debug logs via _log_debug
                        
                        # Get logs after forced collection
                        if hasattr(collector, "get_debug_logs"):
                            logs = collector.get_debug_logs()
                            print(f"After forced collection, slide {slide_id} has {len(logs)} log entries")
                    except Exception as e:
                        print(f"Error forcing collection for debug logs: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Store collector in app_instance for future debug log access
                if collector and app_instance and hasattr(app_instance, 'slide_collectors'):
                    with app_instance.slide_collectors_lock:
                        app_instance.slide_collectors[slide_id] = collector
                        print(f"Stored collector for slide {slide_id} in app_instance")
                
                # Add slide info to each log entry
                if logs:
                    for log in logs:
                        log_with_slide = log.copy()
                        log_with_slide["slide_id"] = slide_id
                        log_with_slide["slide_title"] = slide_title
                        all_logs.append(log_with_slide)
                
                system_slides_info.append({
                    "slide_id": slide_id,
                    "slide_title": slide_title,
                    "log_count": len(logs),
                    "nas_mounts": slide.get("service_config", {}).get("nas_mounts", ""),
                    "poll_interval": slide.get("service_config", {}).get("poll_interval", 5),
                    "has_stored_collector": slide_id in stored_collectors
                })
        
        # Sort logs by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Format logs with readable timestamps
        from datetime import datetime
        formatted_logs = []
        for log in all_logs:
            formatted_log = log.copy()
            if "timestamp" in formatted_log:
                formatted_log["timestamp_readable"] = datetime.fromtimestamp(formatted_log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            formatted_logs.append(formatted_log)
        
        return jsonify({
            "collector": "system",
            "system_slides": system_slides_info,
            "logs": formatted_logs,
            "log_count": len(formatted_logs),
            "total_slides": len(system_slides_info)
        })
    
    @app.route("/api/debug/system/test", methods=["POST"])
    def test_system_collection():
        """Test system stats collection by forcing a fresh fetch."""
        from config import get_slides_config
        from backend.slides import SlideTypeRegistry
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find first system_stats slide for testing
        system_slide = None
        for slide in slides:
            if slide.get("type") == "system_stats":
                system_slide = slide
                break
        
        if not system_slide:
            return jsonify({"error": "No system stats slides configured"}), 404
        
        slide_type = SlideTypeRegistry.get("system_stats")
        if not slide_type:
            return jsonify({"error": "System slide type not found"}), 500
        
        try:
            config_data = {
                "service_config": system_slide.get("service_config", {}),
                "api_config": system_slide.get("api_config")
            }
            collector = slide_type.create_collector(config_data)
            
            if not collector:
                return jsonify({"error": "Failed to create collector"}), 500
            
            # Force a fresh fetch
            result = collector._fetch_data()
            logs = collector.get_debug_logs() if hasattr(collector, "get_debug_logs") else []
            
            return jsonify({
                "success": result is not None,
                "result": result,
                "result_type": type(result).__name__ if result else None,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                "latest_log": logs[-1] if logs else None,
                "log_count": len(logs)
            })
        except Exception as e:
            return jsonify({"error": f"Error testing system collection: {str(e)}"}), 500
    
    @app.route("/api/upload/image", methods=["POST"])
    def upload_image():
        """Upload an image file for use in image slides."""
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"}), 400
        
        # Validate file size (max 10MB)
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)  # Reset file pointer
        max_size = 10 * 1024 * 1024  # 10MB
        if file_length > max_size:
            return jsonify({"error": f"File too large. Maximum size: {max_size / (1024*1024)}MB"}), 400
        
        try:
            # Validate it's actually an image by opening with PIL
            img = Image.open(file)
            img.verify()  # Verify it's a valid image
            
            # Reset file pointer after verify (verify() consumes the file)
            file.seek(0)
            img = Image.open(file)  # Re-open for actual processing
            
            # Create images directory if it doesn't exist
            images_dir = DATA_DIR / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            base_filename = secure_filename(Path(file.filename).stem)
            unique_id = str(uuid.uuid4())[:8]
            new_filename = f"{base_filename}_{unique_id}{file_ext}"
            filepath = images_dir / new_filename
            
            # Save file
            # For GIFs, preserve the format
            if img.format == 'GIF' or file_ext == '.gif':
                # Save GIF as-is (including animation)
                file.seek(0)
                with open(filepath, 'wb') as f:
                    f.write(file.read())
            else:
                # Convert and save other formats as PNG (better compatibility)
                # Update filename to .png before creating filepath
                new_filename = new_filename.rsplit('.', 1)[0] + '.png'
                filepath = images_dir / new_filename
                
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Preserve transparency
                    img.save(filepath, 'PNG')
                else:
                    # Convert to RGB for standard images
                    rgb_img = img.convert('RGB')
                    rgb_img.save(filepath, 'PNG')
            
            # Return relative path from data directory
            relative_path = f"images/{new_filename}"
            
            return jsonify({
                "success": True,
                "filename": new_filename,
                "path": relative_path,
                "size": file_length,
                "format": img.format,
                "width": img.size[0],
                "height": img.size[1],
                "is_animated": getattr(img, 'is_animated', False) if hasattr(img, 'is_animated') else False
            }), 201
            
        except Exception as e:
            return jsonify({"error": f"Invalid image file: {str(e)}"}), 400
    
    @app.route("/api/images", methods=["GET"])
    def list_images():
        """List all uploaded images."""
        images_dir = DATA_DIR / "images"
        images = []
        
        if images_dir.exists():
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            for filepath in images_dir.iterdir():
                if filepath.is_file() and filepath.suffix.lower() in allowed_extensions:
                    try:
                        # Get image metadata
                        img = Image.open(filepath)
                        images.append({
                            "filename": filepath.name,
                            "path": f"images/{filepath.name}",
                            "size": filepath.stat().st_size,
                            "format": img.format,
                            "width": img.size[0],
                            "height": img.size[1],
                            "is_animated": getattr(img, 'is_animated', False) if hasattr(img, 'is_animated') else False
                        })
                    except Exception:
                        # Skip invalid images
                        continue
        
        return jsonify({"images": sorted(images, key=lambda x: x["filename"])})
    
    @app.route("/api/images/<path:filename>", methods=["GET"])
    def serve_image(filename):
        """Serve uploaded image files."""
        # Security: prevent directory traversal
        filename = os.path.basename(filename)
        image_path = DATA_DIR / "images" / filename
        
        # Verify file exists and is in images directory
        if not image_path.exists() or not str(image_path).startswith(str(DATA_DIR / "images")):
            return jsonify({"error": "Image not found"}), 404
        
        # Validate it's an image file
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        if image_path.suffix.lower() not in allowed_extensions:
            return jsonify({"error": "Invalid file type"}), 400
        
        return send_file(str(image_path))
    
    @app.route("/api/preview/<int:slide_id>", methods=["GET"])
    def preview_slide(slide_id):
        """Generate preview image of a slide using per-slide configuration."""
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find slide
        slide = None
        for s in slides:
            if s.get("id") == slide_id:
                slide = s
                break
        
        if not slide:
            return jsonify({"error": "Slide not found"}), 404
        
        slide_type_name = slide.get("type", "")
        slide_type = SlideTypeRegistry.get(slide_type_name)
        
        if not slide_type:
            return jsonify({"error": f"Unknown slide type: {slide_type_name}"}), 400
        
        # Create collector using slide's service_config
        collector = None
        if slide.get("service_config") or slide.get("api_config"):
            try:
                # For custom slides, use api_config; for others, use service_config
                config_data = {
                    "service_config": slide.get("service_config", {}),
                    "api_config": slide.get("api_config")
                }
                collector = slide_type.create_collector(config_data)
            except Exception as e:
                print(f"Error creating collector for slide {slide_id}: {e}")
                collector = None
        
        # Get data from collector
        data = None
        if collector:
            try:
                # For weather slides, pass city to collector if it supports it
                if slide_type_name == "weather" and hasattr(collector, "get_data_for_city"):
                    city = slide.get("city")
                    data = collector.get_data_for_city(city) if city else collector.get_data()
                else:
                    data = collector.get_data()
            except Exception as e:
                print(f"Error fetching data for slide {slide_id}: {e}")
                import traceback
                traceback.print_exc()
                data = None
        
        # Render using slide type
        try:
            image = slide_type.render(renderer, data, slide)
        except Exception as e:
            print(f"Error rendering slide {slide_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Failed to render slide: {str(e)}"}), 500
        
        # Convert to PNG bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        return send_file(img_bytes, mimetype="image/png")
    
    @app.route("/api/preview/current", methods=["GET"])
    def preview_current():
        """Get current slide being displayed as image."""
        app_instance = app.config.get('APP_INSTANCE')
        
        if app_instance and hasattr(app_instance, 'current_slide'):
            with app_instance.current_slide_lock:
                current = app_instance.current_slide
            
            if current and current.get("image"):
                # Convert PIL image to PNG bytes
                img_bytes = io.BytesIO()
                current["image"].save(img_bytes, format="PNG")
                img_bytes.seek(0)
                return send_file(img_bytes, mimetype="image/png")
        
        # Fallback: return first slide if no current slide
        config = get_slides_config()
        slides = sorted(config.get("slides", []), key=lambda x: x.get("order", 0))
        if slides:
            return preview_slide(slides[0].get("id"))
        return jsonify({"error": "No slides configured"}), 404
    
    @app.route("/api/current-slide", methods=["GET"])
    def get_current_slide_info():
        """Get current slide information (JSON)."""
        app_instance = app.config.get('APP_INSTANCE')
        
        if app_instance and hasattr(app_instance, 'current_slide'):
            with app_instance.current_slide_lock:
                current = app_instance.current_slide
            
            if current:
                slide_info = current.get("slide", {})
                return jsonify({
                    "id": slide_info.get("id"),
                    "title": current.get("title"),
                    "type": current.get("slide_type"),
                    "timestamp": current.get("timestamp"),
                    "has_data": current.get("data") is not None,
                    "conditional": slide_info.get("conditional", False),
                })
        
        return jsonify({"error": "No current slide", "current": None}), 200
    
    @app.route("/api/preview/render", methods=["GET"])
    def render_all_slides():
        """Render all slides to preview directory (dev mode) using per-slide collectors."""
        config = get_slides_config()
        slides = config.get("slides", [])
        
        output = create_video_output()
        output.initialize()
        
        rendered_count = 0
        for slide in slides:
            slide_type_name = slide.get("type", "")
            slide_type = SlideTypeRegistry.get(slide_type_name)
            
            if not slide_type:
                print(f"Skipping slide {slide.get('id')}: Unknown type {slide_type_name}")
                continue
            
            # Create collector for this slide
            collector = None
            if slide.get("service_config") or slide.get("api_config"):
                try:
                    config_data = {
                        "service_config": slide.get("service_config", {}),
                        "api_config": slide.get("api_config")
                    }
                    collector = slide_type.create_collector(config_data)
                except Exception as e:
                    print(f"Error creating collector for slide {slide.get('id')}: {e}")
                    collector = None
            
            # Get data from collector
            data = None
            if collector:
                try:
                    if slide_type_name == "weather" and hasattr(collector, "get_data_for_city"):
                        city = slide.get("city")
                        data = collector.get_data_for_city(city) if city else collector.get_data()
                    else:
                        data = collector.get_data()
                except Exception as e:
                    print(f"Error fetching data for slide {slide.get('id')}: {e}")
                    data = None
            
            # Render using slide type
            try:
                image = slide_type.render(renderer, data, slide)
                if output.display_frame(image):
                    rendered_count += 1
            except Exception as e:
                print(f"Error rendering slide {slide.get('id')}: {e}")
                import traceback
                traceback.print_exc()
        
        output.cleanup()
        
        return jsonify({"success": True, "rendered": rendered_count})
    
    # Widget Designer API Endpoints
    @app.route("/api/widgets/types", methods=["GET"])
    def get_widget_types():
        """Get available widget types and their schemas."""
        widget_types = {
            "text": {
                "name": "Text",
                "description": "Display text with data binding",
                "properties": {
                    "data_binding": {
                        "path": {"type": "string", "description": "Data path (e.g., 'cpu.percent')"},
                        "template": {"type": "string", "description": "Template string (e.g., 'CPU: {value}%')"},
                        "format": {"type": "string", "description": "Format type (bytes, duration, percentage, etc.)", "optional": True}
                    },
                    "style": {
                        "font_size": {"type": "string", "enum": ["large", "medium", "small", "tiny"], "default": "medium"},
                        "color": {"type": "string", "enum": ["text", "text_secondary", "text_muted", "accent"], "default": "text"},
                        "align": {"type": "string", "enum": ["left", "center", "right"], "default": "left"}
                    },
                    "position": {
                        "x": {"type": "number", "description": "X position in container"},
                        "y": {"type": "number", "description": "Y position in container"}
                    },
                    "width": {"type": "number", "description": "Widget width", "optional": True},
                    "height": {"type": "number", "description": "Widget height", "optional": True}
                }
            },
            "progress": {
                "name": "Progress Bar",
                "description": "Display progress bar with percentage",
                "properties": {
                    "data_binding": {
                        "path": {"type": "string", "description": "Data path to value"},
                        "min": {"type": "number", "default": 0},
                        "max": {"type": "number", "default": 100}
                    },
                    "style": {
                        "width": {"type": "number", "default": 30, "description": "Bar width in characters"},
                        "show_label": {"type": "boolean", "default": True},
                        "label_template": {"type": "string", "default": "{value:.1f}%"},
                        "color": {"type": "string", "enum": ["text", "text_secondary", "text_muted", "accent"], "default": "text"}
                    },
                    "position": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    }
                }
            },
            "chart": {
                "name": "Chart",
                "description": "Display line or bar chart",
                "properties": {
                    "chart_config": {
                        "type": {"type": "string", "enum": ["line", "bar"], "default": "line"},
                        "data_path": {"type": "string", "description": "Data path to chart data"}
                    },
                    "position": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    },
                    "width": {"type": "number", "description": "Chart width"},
                    "height": {"type": "number", "description": "Chart height"}
                }
            },
            "conditional": {
                "name": "Conditional Widget",
                "description": "Display widget conditionally based on data",
                "properties": {
                    "condition": {
                        "operator": {"type": "string", "enum": ["==", "!=", ">", "<", ">=", "<=", "exists", "contains", "and", "or", "not"]},
                        "path": {"type": "string", "description": "Data path to evaluate"},
                        "value": {"type": "any", "description": "Value to compare against", "optional": True},
                        "conditions": {"type": "array", "description": "Sub-conditions for and/or operators", "optional": True}
                    },
                    "widget": {
                        "type": {"type": "string", "description": "Widget type to render if condition is met"},
                        "description": "Full widget configuration"
                    },
                    "position": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    }
                }
            }
        }
        return jsonify({"widget_types": widget_types})
    
    @app.route("/api/widgets/test-api", methods=["POST"])
    def test_api():
        """Test custom API configuration."""
        data = request.get_json()
        api_config = data.get("api_config", {})
        
        if not api_config:
            return jsonify({"error": "No API configuration provided"}), 400
        
        try:
            from backend.collectors.generic_collector import GenericCollector
            
            # Create temporary collector for testing
            collector = GenericCollector(api_config)
            result = collector._fetch_data()
            
            return jsonify({
                "success": result is not None,
                "result": result,
                "result_type": type(result).__name__ if result else None,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                "error": collector.get_last_error() if result is None else None
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/widgets/validate", methods=["POST"])
    def validate_widget():
        """Validate widget configuration."""
        data = request.get_json()
        widget = data.get("widget", {})
        
        if not widget:
            return jsonify({"error": "No widget configuration provided"}), 400
        
        errors = []
        warnings = []
        
        # Check required fields
        widget_type = widget.get("type")
        if not widget_type:
            errors.append("Widget type is required")
        
        # Validate based on widget type
        if widget_type == "text":
            data_binding = widget.get("data_binding", {})
            if not data_binding.get("path") and not data_binding.get("template") and not widget.get("text"):
                errors.append("Text widget requires data_binding.path, data_binding.template, or static text")
        elif widget_type == "progress":
            data_binding = widget.get("data_binding", {})
            if not data_binding.get("path"):
                errors.append("Progress widget requires data_binding.path")
        elif widget_type == "chart":
            chart_config = widget.get("chart_config", {})
            if not chart_config.get("data_path"):
                errors.append("Chart widget requires chart_config.data_path")
        elif widget_type == "conditional":
            condition = widget.get("condition", {})
            if not condition:
                errors.append("Conditional widget requires condition")
            child_widget = widget.get("widget", {})
            if not child_widget:
                errors.append("Conditional widget requires child widget configuration")
        
        # Check position
        position = widget.get("position", {})
        if "x" not in position or "y" not in position:
            warnings.append("Widget position (x, y) recommended for proper layout")
        
        return jsonify({
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        })
    
    @app.route("/api/slides/<int:slide_id>/preview", methods=["POST"])
    def preview_slide_with_data(slide_id):
        """Generate preview of a slide with optional test data."""
        data = request.get_json() or {}
        test_data = data.get("test_data")
        slide_override = data.get("slide")  # Optional slide config override
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Find slide or use override
        slide = slide_override
        if not slide:
            for s in slides:
                if s.get("id") == slide_id:
                    slide = s
                    break
        
        # If slide_id is 0 and we have override, use it (for new slides)
        if slide_id == 0 and slide_override:
            slide = slide_override
        elif not slide and slide_id == 0:
            # Create temporary slide for preview
            slide = slide_override or {"type": "custom", "title": "Preview", "widgets": [], "layout": {"type": "mixed", "grid_areas": []}}
        
        if not slide:
            return jsonify({"error": "Slide not found"}), 404
        
        slide_type_name = slide.get("type", "")
        slide_type = SlideTypeRegistry.get(slide_type_name)
        
        if not slide_type:
            return jsonify({"error": f"Unknown slide type: {slide_type_name}"}), 400
        
        # Get data - use test data if provided, otherwise fetch from collector
        data_for_render = test_data
        
        if data_for_render is None:
            # Create collector for this slide
            collector = None
            if slide.get("service_config") or slide.get("api_config"):
                try:
                    config_data = {
                        "service_config": slide.get("service_config", {}),
                        "api_config": slide.get("api_config")
                    }
                    collector = slide_type.create_collector(config_data)
                except Exception as e:
                    print(f"Error creating collector for preview: {e}")
                    collector = None
            
            # Get data from collector
            if collector:
                try:
                    if slide_type_name == "weather" and hasattr(collector, "get_data_for_city"):
                        city = slide.get("city")
                        data_for_render = collector.get_data_for_city(city) if city else collector.get_data()
                    else:
                        data_for_render = collector.get_data()
                except Exception as e:
                    print(f"Error fetching data for preview: {e}")
                    data_for_render = None
        
        # Render using slide type
        try:
            image = slide_type.render(renderer, data_for_render, slide)
            
            # Convert to PNG bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            return send_file(img_bytes, mimetype="image/png")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Failed to render slide: {str(e)}", "traceback": traceback.format_exc()}), 500
    
    return app

