"""Flask API routes for web UI."""

from flask import Flask, jsonify, request, send_file
from typing import Dict, Any
import io
import sys
from pathlib import Path
# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_slides_config, save_slides_config, get_api_config, save_api_config
from backend.api.models import Slide, APIConfig
from backend.display.renderer import SlideRenderer
from backend.display.video_output import create_video_output


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
        return jsonify(config)
    
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
            "order": data.get("order", len(slides)),
            "conditional": data.get("conditional", False),
        }
        
        if data.get("condition_type"):
            new_slide["condition_type"] = data.get("condition_type")
        
        # Weather-specific fields
        if data.get("type") == "weather":
            if data.get("city"):
                new_slide["city"] = data.get("city")
            new_slide["temp_unit"] = data.get("temp_unit", "C")
        
        slides.append(new_slide)
        config["slides"] = slides
        save_slides_config(config)
        
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
                slides[i].update(data)
                slides[i]["id"] = slide_id  # Ensure ID doesn't change
                config["slides"] = slides
                save_slides_config(config)
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
                save_slides_config(config)
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
        save_slides_config(config)
        
        return jsonify(config)
    
    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Get API configuration."""
        config = get_api_config()
        return jsonify(config)
    
    @app.route("/api/config", methods=["PUT"])
    def update_config():
        """Update API configuration."""
        data = request.get_json()
        save_api_config(data)
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
        """Get Plex collector debug logs."""
        if collectors is None or "plex" not in collectors:
            return jsonify({"error": "Plex collector not available", "logs": []}), 200
        
        plex_collector = collectors["plex"]
        logs = []
        
        if hasattr(plex_collector, "get_debug_logs"):
            logs = plex_collector.get_debug_logs()
        elif hasattr(plex_collector, "debug_logs"):
            logs = plex_collector.debug_logs.copy()
        
        # Format logs with readable timestamps
        from datetime import datetime
        formatted_logs = []
        for log in logs:
            formatted_log = log.copy()
            if "timestamp" in formatted_log:
                formatted_log["timestamp_readable"] = datetime.fromtimestamp(formatted_log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            formatted_logs.append(formatted_log)
        
        return jsonify({
            "collector": "plex",
            "api_url": plex_collector.api_url if hasattr(plex_collector, "api_url") else "",
            "has_token": bool(plex_collector.api_token) if hasattr(plex_collector, "api_token") else False,
            "logs": formatted_logs,
            "log_count": len(formatted_logs)
        })
    
    @app.route("/api/debug/plex/test", methods=["POST"])
    def test_plex_connection():
        """Test Plex API connection by making a request."""
        if collectors is None or "plex" not in collectors:
            return jsonify({"error": "Plex collector not available"}), 500
        
        plex_collector = collectors["plex"]
        
        # Force a fetch (bypasses cache)
        if hasattr(plex_collector, "_fetch_data"):
            # Clear cache first to force fresh fetch
            if hasattr(plex_collector, "clear_cache"):
                plex_collector.clear_cache()
            
            result = plex_collector._fetch_data()
            logs = plex_collector.get_debug_logs() if hasattr(plex_collector, "get_debug_logs") else []
            
            return jsonify({
                "success": result is not None,
                "result": result,
                "result_type": type(result).__name__,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                "has_active_streams": plex_collector.has_active_streams() if hasattr(plex_collector, "has_active_streams") else None,
                "latest_log": logs[-1] if logs else None
            })
        else:
            return jsonify({"error": "Cannot test connection"}), 500
    
    @app.route("/api/debug/plex/data", methods=["GET"])
    def get_plex_data():
        """Get current Plex data (bypassing cache)."""
        if collectors is None or "plex" not in collectors:
            return jsonify({"error": "Plex collector not available"}), 500
        
        plex_collector = collectors["plex"]
        
        # Get cached data first
        cached_data = None
        if hasattr(plex_collector, "get_data"):
            cached_data = plex_collector.get_data()
        
        # Force fresh fetch by clearing cache
        fresh_data = None
        if hasattr(plex_collector, "clear_cache"):
            plex_collector.clear_cache()
        if hasattr(plex_collector, "_fetch_data"):
            fresh_data = plex_collector._fetch_data()
        
        # Check what get_data returns after fresh fetch
        final_data = None
        if hasattr(plex_collector, "get_data"):
            final_data = plex_collector.get_data()
        
        return jsonify({
            "cached_data_before": cached_data,
            "cached_data_type": type(cached_data).__name__ if cached_data is not None else "None",
            "fresh_fetch_result": fresh_data,
            "fresh_data_type": type(fresh_data).__name__ if fresh_data is not None else "None",
            "get_data_after_fresh": final_data,
            "final_data_type": type(final_data).__name__ if final_data is not None else "None",
            "has_active_streams": plex_collector.has_active_streams() if hasattr(plex_collector, "has_active_streams") else None,
        })
    
    @app.route("/api/debug/arm", methods=["GET"])
    def get_arm_debug():
        """Get ARM collector debug logs."""
        if collectors is None or "arm" not in collectors:
            return jsonify({"error": "ARM collector not available", "logs": []}), 200
        
        arm_collector = collectors["arm"]
        logs = []
        
        if hasattr(arm_collector, "get_debug_logs"):
            logs = arm_collector.get_debug_logs()
        elif hasattr(arm_collector, "debug_logs"):
            logs = arm_collector.debug_logs.copy()
        
        # Format logs with readable timestamps
        from datetime import datetime
        formatted_logs = []
        for log in logs:
            formatted_log = log.copy()
            if "timestamp" in formatted_log:
                formatted_log["timestamp_readable"] = datetime.fromtimestamp(formatted_log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            formatted_logs.append(formatted_log)
        
        return jsonify({
            "collector": "arm",
            "api_url": arm_collector.api_url if hasattr(arm_collector, "api_url") else "",
            "has_key": bool(arm_collector.api_key) if hasattr(arm_collector, "api_key") else False,
            "endpoint": arm_collector.endpoint if hasattr(arm_collector, "endpoint") else "",
            "logs": formatted_logs,
            "log_count": len(formatted_logs)
        })
    
    @app.route("/api/debug/arm/test", methods=["POST"])
    def test_arm_connection():
        """Test ARM API connection by making a request."""
        if collectors is None or "arm" not in collectors:
            return jsonify({"error": "ARM collector not available"}), 500
        
        arm_collector = collectors["arm"]
        
        # Force a fetch (bypasses cache)
        if hasattr(arm_collector, "_fetch_data"):
            # Clear cache first to force fresh fetch
            if hasattr(arm_collector, "clear_cache"):
                arm_collector.clear_cache()
            
            result = arm_collector._fetch_data()
            logs = arm_collector.get_debug_logs() if hasattr(arm_collector, "get_debug_logs") else []
            
            return jsonify({
                "success": result is not None,
                "result": result,
                "result_type": type(result).__name__ if result else None,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                "has_active_rip": arm_collector.has_active_rip() if hasattr(arm_collector, "has_active_rip") else None,
                "latest_log": logs[-1] if logs else None
            })
        else:
            return jsonify({"error": "Cannot test connection"}), 500
    
    @app.route("/api/debug/arm/data", methods=["GET"])
    def get_arm_data():
        """Get current ARM data (bypassing cache)."""
        if collectors is None or "arm" not in collectors:
            return jsonify({"error": "ARM collector not available"}), 500
        
        arm_collector = collectors["arm"]
        
        # Get cached data first
        cached_data = None
        if hasattr(arm_collector, "get_data"):
            cached_data = arm_collector.get_data()
        
        # Force fresh fetch by clearing cache
        fresh_data = None
        if hasattr(arm_collector, "clear_cache"):
            arm_collector.clear_cache()
        if hasattr(arm_collector, "_fetch_data"):
            fresh_data = arm_collector._fetch_data()
        
        # Check what get_data returns after fresh fetch
        final_data = None
        if hasattr(arm_collector, "get_data"):
            final_data = arm_collector.get_data()
        
        return jsonify({
            "cached_data_before": cached_data,
            "cached_data_type": type(cached_data).__name__ if cached_data is not None else "None",
            "fresh_fetch_result": fresh_data,
            "fresh_data_type": type(fresh_data).__name__ if fresh_data is not None else "None",
            "get_data_after_fresh": final_data,
            "final_data_type": type(final_data).__name__ if final_data is not None else "None",
            "has_active_rip": arm_collector.has_active_rip() if hasattr(arm_collector, "has_active_rip") else None,
        })
    
    @app.route("/api/preview/<int:slide_id>", methods=["GET"])
    def preview_slide(slide_id):
        """Generate preview image of a slide."""
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
        
        # Get data from collectors if available
        data = None
        slide_type = slide.get("type", "")
        
        if collectors:
            if slide_type == "arm_rip_progress" and "arm" in collectors:
                data = collectors["arm"].get_data()
            elif slide_type == "pihole_summary" and "pihole" in collectors:
                data = collectors["pihole"].get_data()
            elif slide_type == "plex_now_playing" and "plex" in collectors:
                data = collectors["plex"].get_data()
                # Debug logging for Plex data
                print(f"Preview: Plex data for slide {slide_id}: {data}")
                if data is None:
                    print(f"Preview: Plex collector returned None - checking if active streams exist")
                    if hasattr(collectors["plex"], "has_active_streams"):
                        print(f"Preview: has_active_streams() = {collectors['plex'].has_active_streams()}")
            elif slide_type == "system_stats" and "system" in collectors:
                data = collectors["system"].get_data()
            elif slide_type == "weather" and "weather" in collectors:
                # Get city from slide config, fallback to global config
                city = slide.get("city")
                data = collectors["weather"].get_data_for_city(city)
        
        # Debug: Log what we're passing to renderer
        print(f"Preview: Rendering slide {slide_id} type={slide_type}, data is None: {data is None}")
        if data:
            print(f"Preview: Data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        
        # Render slide (pass slide config for weather city/temp_unit)
        image = renderer.render(slide_type, data, slide.get("title", ""), slide)
        
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
                    "condition_met": slide_info.get("conditional", False),
                })
        
        return jsonify({"error": "No current slide", "current": None}), 200
    
    @app.route("/api/preview/render", methods=["GET"])
    def render_all_slides():
        """Render all slides to preview directory (dev mode)."""
        config = get_slides_config()
        slides = config.get("slides", [])
        
        output = create_video_output()
        output.initialize()
        
        rendered_count = 0
        for slide in slides:
            slide_type = slide.get("type", "")
            title = slide.get("title", "")
            
            # Get data from collectors
            data = None
            if collectors:
                if slide_type == "arm_rip_progress" and "arm" in collectors:
                    data = collectors["arm"].get_data()
                elif slide_type == "pihole_summary" and "pihole" in collectors:
                    data = collectors["pihole"].get_data()
                elif slide_type == "plex_now_playing" and "plex" in collectors:
                    data = collectors["plex"].get_data()
                elif slide_type == "system_stats" and "system" in collectors:
                    data = collectors["system"].get_data()
                elif slide_type == "weather" and "weather" in collectors:
                    # Get city from slide config, fallback to global config
                    city = slide.get("city")
                    data = collectors["weather"].get_data_for_city(city)
            
            # Render and save (pass slide config for weather city/temp_unit)
            image = renderer.render(slide_type, data, title, slide)
            if output.display_frame(image):
                rendered_count += 1
        
        output.cleanup()
        
        return jsonify({"success": True, "rendered": rendered_count})
    
    return app

