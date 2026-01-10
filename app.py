#!/usr/bin/env python3
"""
Homelab HUD - Main Application Entry Point

Runs the display loop and Flask web server for Raspberry Pi CRT stats display.
"""

import sys
import time
import signal
import threading
import argparse
from pathlib import Path

from config import get_slides_config, get_api_config, IS_DEV, DATA_DIR
from backend.collectors.arm_collector import ARMCollector
from backend.collectors.pihole_collector import PiHoleCollector
from backend.collectors.plex_collector import PlexCollector
from backend.collectors.system_collector import SystemCollector
from backend.collectors.weather_collector import WeatherCollector
from backend.display.renderer import SlideRenderer
from backend.display.video_output import create_video_output
from backend.api.routes import create_app


class HomelabHUD:
    """Main application class."""
    
    def __init__(self, dev_mode: bool = False, preview_window: bool = False, export_frames: bool = False, port: int = 8181):
        self.dev_mode = dev_mode or IS_DEV
        self.preview_window = preview_window
        self.export_frames = export_frames
        self.port = port
        self.running = False
        self.collectors = {}
        self.renderer = SlideRenderer()
        self.video_output = None
        self.flask_app = None
        self.flask_thread = None
        # Current slide tracking (thread-safe)
        self.current_slide_lock = threading.Lock()
        self.current_slide = None  # Dict with slide info and rendered image
        
        # Load configuration
        self.api_config = get_api_config()
        
        # Initialize collectors
        self._init_collectors()
        
        # Initialize video output
        self.video_output = create_video_output(preview_window=preview_window)
        if not self.video_output.initialize():
            print("Warning: Video output initialization failed. Continuing in preview mode.")
            if not self.dev_mode:
                self.video_output = create_video_output(preview_window=True)
                self.video_output.initialize()
        
        # Initialize Flask app with correct template/static paths
        template_dir = str(Path(__file__).parent / 'frontend' / 'templates')
        static_dir = str(Path(__file__).parent / 'frontend' / 'static')
        
        # Create Flask app with access to this instance for current slide tracking
        self.flask_app = create_app(
            collectors=self.collectors,
            template_folder=template_dir,
            static_folder=static_dir,
            app_instance=self  # Pass app instance for current slide access
        )
        
        # Add route for index
        @self.flask_app.route('/')
        def index():
            from flask import render_template
            return render_template('index.html')
    
    def _init_collectors(self):
        """Initialize data collectors."""
        # ARM Collector
        if self.api_config.get("arm", {}).get("enabled", True):
            try:
                self.collectors["arm"] = ARMCollector(self.api_config.get("arm", {}))
                print("ARM collector initialized")
            except Exception as e:
                print(f"Failed to initialize ARM collector: {e}")
        
        # Pi-hole Collector
        if self.api_config.get("pihole", {}).get("enabled", True):
            try:
                self.collectors["pihole"] = PiHoleCollector(self.api_config.get("pihole", {}))
                print("Pi-hole collector initialized")
            except Exception as e:
                print(f"Failed to initialize Pi-hole collector: {e}")
        
        # Plex Collector
        if self.api_config.get("plex", {}).get("enabled", True):
            try:
                self.collectors["plex"] = PlexCollector(self.api_config.get("plex", {}))
                print("Plex collector initialized")
            except Exception as e:
                print(f"Failed to initialize Plex collector: {e}")
        
        # System Collector
        if self.api_config.get("system", {}).get("enabled", True):
            try:
                self.collectors["system"] = SystemCollector(self.api_config.get("system", {}))
                print("System collector initialized")
            except Exception as e:
                print(f"Failed to initialize System collector: {e}")
        
        # Weather Collector
        if self.api_config.get("weather", {}).get("enabled", True):
            try:
                self.collectors["weather"] = WeatherCollector(self.api_config.get("weather", {}))
                print("Weather collector initialized")
            except Exception as e:
                print(f"Failed to initialize Weather collector: {e}")
    
    def _should_display_slide(self, slide: dict) -> bool:
        """Check if slide should be displayed based on conditional logic.
        
        If conditional is True, only display if the slide has meaningful data.
        Otherwise, always display.
        """
        if not slide.get("conditional", False):
            return True
        
        # For conditional slides, check if this slide has data to display
        slide_type = slide.get("type", "")
        data = self._get_slide_data(slide_type, slide)
        
        # Check if data exists and is meaningful based on slide type
        if data is None:
            return False
        
        # For Plex, check if there are active streams
        if slide_type == "plex_now_playing":
            return data.get("session_count", 0) > 0
        
        # For ARM, if data exists it means there's an active rip
        # (ARM collector returns None if no active jobs)
        if slide_type == "arm_rip_progress":
            return True  # data is not None means there's an active rip
        
        # For other slide types, if data exists, display it
        # (Pi-hole, System, Weather should always have data if collector is working)
        return True
    
    def _get_slide_data(self, slide_type: str, slide: dict = None) -> dict:
        """Get data for a slide type from appropriate collector."""
        # Image and static text slides don't need data from collectors
        if slide_type == "image" or slide_type == "static_text":
            return None
        elif slide_type == "arm_rip_progress" and "arm" in self.collectors:
            return self.collectors["arm"].get_data()
        elif slide_type == "pihole_summary" and "pihole" in self.collectors:
            return self.collectors["pihole"].get_data()
        elif slide_type == "plex_now_playing" and "plex" in self.collectors:
            return self.collectors["plex"].get_data()
        elif slide_type == "system_stats" and "system" in self.collectors:
            return self.collectors["system"].get_data()
        elif slide_type == "weather" and "weather" in self.collectors:
            # Get city from slide config, fallback to global config
            city = (slide or {}).get("city") if slide else None
            return self.collectors["weather"].get_data_for_city(city)
        
        return None
    
    def _get_collector_for_type(self, slide_type: str):
        """Get the collector instance for a given slide type."""
        if slide_type == "arm_rip_progress" and "arm" in self.collectors:
            return self.collectors["arm"]
        elif slide_type == "pihole_summary" and "pihole" in self.collectors:
            return self.collectors["pihole"]
        elif slide_type == "plex_now_playing" and "plex" in self.collectors:
            return self.collectors["plex"]
        elif slide_type == "system_stats" and "system" in self.collectors:
            return self.collectors["system"]
        elif slide_type == "weather" and "weather" in self.collectors:
            return self.collectors["weather"]
        
        return None
    
    def _run_display_loop(self):
        """Main display loop."""
        print("Starting display loop...")
        
        frame_count = 0
        
        while self.running:
            try:
                # Reload configuration (allows runtime updates)
                slides_config = get_slides_config()
                slides = sorted(slides_config.get("slides", []), key=lambda x: x.get("order", 0))
                
                if not slides:
                    print("No slides configured. Waiting...")
                    time.sleep(5)
                    continue
                
                # Cycle through slides
                for slide in slides:
                    if not self.running:
                        break
                    
                    # Check conditional display - skip if conditional and no data
                    # Static text and image slides are never conditional
                    slide_type = slide.get("type", "")
                    if slide_type != "static_text" and slide_type != "image" and not self._should_display_slide(slide):
                        print(f"Skipping slide '{slide.get('title')}' (conditional slide has no data)")
                        # Update current slide to None when skipping
                        with self.current_slide_lock:
                            self.current_slide = None
                        continue
                    
                    # Get slide configuration
                    slide_type = slide.get("type", "")
                    title = slide.get("title", "")
                    display_duration = slide.get("duration", 10)  # How long to display the slide
                    refresh_duration = slide.get("refresh_duration", 5)  # How often to refresh data
                    
                    # Initial data fetch and render
                    data = self._get_slide_data(slide_type, slide)
                    image = self.renderer.render(slide_type, data, title, slide)
                    image_copy = image.copy()
                    
                    with self.current_slide_lock:
                        self.current_slide = {
                            "slide": dict(slide),  # Copy dict to avoid mutations
                            "slide_type": slide_type,
                            "title": title,
                            "data": data,
                            "image": image_copy,
                            "timestamp": time.time()
                        }
                    
                    # Display initial frame
                    if self.export_frames:
                        # Export to file
                        export_dir = DATA_DIR / "preview"
                        export_dir.mkdir(exist_ok=True)
                        filename = export_dir / f"slide_{frame_count:06d}_{slide.get('id')}.png"
                        image.save(filename)
                        print(f"Exported frame: {filename}")
                    else:
                        # Display to output
                        if not self.video_output.display_frame(image):
                            print("Warning: Failed to display frame")
                    
                    frame_count += 1
                    
                    # Display loop: refresh data periodically while displaying for display_duration
                    sleep_interval = 0.1
                    elapsed = 0
                    last_refresh = 0
                    
                    print(f"Displaying slide '{title}' for {display_duration}s, refreshing every {refresh_duration}s")
                    
                    while elapsed < display_duration and self.running:
                        time.sleep(sleep_interval)
                        elapsed += sleep_interval
                        
                        # Check if it's time to refresh data
                        if elapsed - last_refresh >= refresh_duration:
                            print(f"Refreshing slide '{title}' at {elapsed:.1f}s (refresh interval: {refresh_duration}s)")
                            
                            # Clear cache to force fresh data fetch
                            collector = self._get_collector_for_type(slide_type)
                            if collector and hasattr(collector, "clear_cache"):
                                collector.clear_cache()
                            
                            # Refresh data (will now fetch fresh data since cache is cleared)
                            data = self._get_slide_data(slide_type, slide)
                            
                            # Re-render slide with new data
                            image = self.renderer.render(slide_type, data, title, slide)
                            image_copy = image.copy()
                            
                            # Update current slide (thread-safe)
                            with self.current_slide_lock:
                                self.current_slide = {
                                    "slide": dict(slide),
                                    "slide_type": slide_type,
                                    "title": title,
                                    "data": data,
                                    "image": image_copy,
                                    "timestamp": time.time()
                                }
                            
                            # Display updated frame - this is critical for updating the display
                            if self.export_frames:
                                # Export to file
                                export_dir = DATA_DIR / "preview"
                                export_dir.mkdir(exist_ok=True)
                                filename = export_dir / f"slide_{frame_count:06d}_{slide.get('id')}.png"
                                image.save(filename)
                                print(f"Exported refreshed frame: {filename}")
                            else:
                                # CRITICAL: Update the actual display with the new frame
                                if self.video_output.display_frame(image):
                                    print(f"Display updated with refreshed frame at {elapsed:.1f}s")
                                else:
                                    print(f"Warning: Failed to display refreshed frame at {elapsed:.1f}s")
                            
                            frame_count += 1
                            last_refresh = elapsed
                        
                        # Update timestamp periodically so web UI knows slide is still active
                        if elapsed % 1.0 < sleep_interval:  # Every ~1 second
                            with self.current_slide_lock:
                                if self.current_slide:
                                    self.current_slide["timestamp"] = time.time()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in display loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
        
        print("Display loop stopped.")
    
    def _run_flask_server(self):
        """Run Flask web server in separate thread."""
        print(f"Starting Flask server on port {self.port}...")
        try:
            self.flask_app.run(host='0.0.0.0', port=self.port, debug=self.dev_mode, use_reloader=False)
        except Exception as e:
            print(f"Flask server error: {e}")
    
    def start(self):
        """Start the application."""
        if self.running:
            return
        
        self.running = True
        
        # Start Flask server in background thread
        self.flask_thread = threading.Thread(target=self._run_flask_server, daemon=True)
        self.flask_thread.start()
        
        # Give Flask time to start
        time.sleep(1)
        
        print("Homelab HUD started!")
        print(f"Web UI available at: http://localhost:{self.port}")
        print(f"Mode: {'Development' if self.dev_mode else 'Production'}")
        
        # Run main display loop
        try:
            self._run_display_loop()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the application."""
        if not self.running:
            return
        
        self.running = False
        
        if self.video_output:
            self.video_output.cleanup()
        
        print("Homelab HUD stopped.")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\nReceived shutdown signal...")
    sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Homelab HUD - Raspberry Pi CRT Stats Display')
    parser.add_argument('--dev-mode', action='store_true', help='Run in development mode')
    parser.add_argument('--preview', action='store_true', help='Use pygame window preview (dev mode only)')
    parser.add_argument('--export-frames', action='store_true', help='Export frames to files instead of displaying')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--port', '-p', type=int, default=8181, help='Flask web server port (default: 8181)')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start application
    app = HomelabHUD(
        dev_mode=args.dev_mode,
        preview_window=args.preview,
        export_frames=args.export_frames,
        port=args.port
    )
    
    try:
        app.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

