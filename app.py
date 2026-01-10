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
from backend.collectors.generic_collector import GenericCollector
from backend.slides import SlideTypeRegistry
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
        self.generic_collectors = {}  # Store generic collectors keyed by slide ID
        self.generic_collectors_lock = threading.Lock()  # Thread-safe access
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
        """Initialize data collectors - now using per-slide collectors."""
        # Collectors are now created per-slide on demand
        # Weather collector uses wttr.in which doesn't require global config
        print("Per-slide collectors will be created on demand")
    
    def _should_display_slide(self, slide: dict) -> bool:
        """Check if slide should be displayed based on conditional logic using slide types."""
        slide_type_name = slide.get("type", "")
        slide_type = SlideTypeRegistry.get(slide_type_name)
        
        if not slide_type:
            # Unknown slide type - default behavior
            return not slide.get("conditional", False)
        
        # Get collector for this slide
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
                # For weather, pass city if available
                if slide_type_name == "weather" and hasattr(collector, "get_data_for_city"):
                    city = slide.get("city")
                    data = collector.get_data_for_city(city) if city else collector.get_data()
                else:
                    data = collector.get_data()
            except Exception as e:
                print(f"Error fetching data for slide {slide.get('id')}: {e}")
                data = None
        
        # Use slide type's should_display method
        return slide_type.should_display(collector, data, slide)
    
    def _get_slide_data(self, slide_type_name: str, slide: dict = None) -> dict:
        """Get data for a slide using per-slide collectors."""
        if not slide:
            return None
        
        slide_type = SlideTypeRegistry.get(slide_type_name)
        if not slide_type:
            return None
        
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
                return None
        
        if not collector:
            return None
        
        # Get data from collector
        try:
            # For weather, pass city if available
            if slide_type_name == "weather" and hasattr(collector, "get_data_for_city"):
                city = slide.get("city")
                return collector.get_data_for_city(city) if city else collector.get_data()
            else:
                return collector.get_data()
        except Exception as e:
            print(f"Error fetching data for slide {slide.get('id')}: {e}")
            return None
    
    def _get_custom_slide_data(self, slide: dict) -> dict:
        """
        Get data for a custom slide using its generic collector.
        
        Args:
            slide: Slide configuration dictionary
        
        Returns:
            Data dictionary from generic collector or None
        """
        slide_id = slide.get("id")
        if not slide_id:
            return None
        
        api_config = slide.get("api_config")
        if not api_config:
            # No API config - return empty dict (widgets may have static data)
            return {}
        
        # Get or create generic collector for this slide
        with self.generic_collectors_lock:
            collector = self.generic_collectors.get(slide_id)
            
            if collector is None:
                # Create new collector
                try:
                    collector = GenericCollector(api_config, slide_id=slide_id)
                    self.generic_collectors[slide_id] = collector
                    print(f"Created generic collector for slide {slide_id}")
                except Exception as e:
                    print(f"Failed to create generic collector for slide {slide_id}: {e}")
                    return None
        
        # Get data from collector
        return collector.get_data()
    
    def _update_generic_collectors(self):
        """
        Update generic collectors based on current slides configuration.
        Removes collectors for deleted slides and updates configs for changed slides.
        """
        from config import get_slides_config
        
        config = get_slides_config()
        slides = config.get("slides", [])
        
        # Get set of current custom slide IDs
        current_custom_slide_ids = {s.get("id") for s in slides if s.get("type") == "custom" and s.get("id")}
        
        with self.generic_collectors_lock:
            # Remove collectors for slides that no longer exist
            to_remove = [sid for sid in self.generic_collectors.keys() if sid not in current_custom_slide_ids]
            for sid in to_remove:
                del self.generic_collectors[sid]
                print(f"Removed generic collector for slide {sid}")
            
            # Update or create collectors for existing custom slides
            for slide in slides:
                if slide.get("type") != "custom":
                    continue
                
                slide_id = slide.get("id")
                if not slide_id:
                    continue
                
                api_config = slide.get("api_config")
                if not api_config:
                    continue
                
                # Check if collector exists and needs update
                collector = self.generic_collectors.get(slide_id)
                if collector is None:
                    # Create new collector
                    try:
                        collector = GenericCollector(api_config, slide_id=slide_id)
                        self.generic_collectors[slide_id] = collector
                        print(f"Created generic collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Failed to create generic collector for slide {slide_id}: {e}")
                else:
                    # Update existing collector config (will use new config on next fetch)
                    # For simplicity, we'll just recreate the collector if config changed
                    # A more sophisticated implementation could update in place
                    try:
                        new_collector = GenericCollector(api_config, slide_id=slide_id)
                        self.generic_collectors[slide_id] = new_collector
                        print(f"Updated generic collector for slide {slide_id}")
                    except Exception as e:
                        print(f"Failed to update generic collector for slide {slide_id}: {e}")
    
    
    def _run_display_loop(self):
        """Main display loop."""
        print("Starting display loop...")
        
        frame_count = 0
        
        while self.running:
            try:
                # Reload configuration (allows runtime updates)
                slides_config = get_slides_config()
                slides = sorted(slides_config.get("slides", []), key=lambda x: x.get("order", 0))
                
                # Update generic collectors for custom slides
                self._update_generic_collectors()
                
                if not slides:
                    print("No slides configured. Waiting...")
                    time.sleep(5)
                    continue
                
                # Cycle through slides
                for slide in slides:
                    if not self.running:
                        break
                    
                    # Get slide configuration
                    slide_type = slide.get("type", "")
                    slide_type_obj = SlideTypeRegistry.get(slide_type)
                    
                    if not slide_type_obj:
                        print(f"Unknown slide type: {slide_type}, skipping")
                        continue
                    
                    # Check conditional display using slide type
                    # Create temporary collector for conditional check
                    temp_collector = None
                    if slide.get("service_config") or slide.get("api_config"):
                        try:
                            config_data = {
                                "service_config": slide.get("service_config", {}),
                                "api_config": slide.get("api_config")
                            }
                            temp_collector = slide_type_obj.create_collector(config_data)
                        except Exception as e:
                            print(f"Error creating collector for conditional check: {e}")
                    
                    # Get temp data for conditional check
                    temp_data = None
                    if temp_collector:
                        try:
                            if slide_type == "weather" and hasattr(temp_collector, "get_data_for_city"):
                                city = slide.get("city")
                                temp_data = temp_collector.get_data_for_city(city) if city else temp_collector.get_data()
                            else:
                                temp_data = temp_collector.get_data()
                        except Exception as e:
                            print(f"Error fetching temp data for conditional check: {e}")
                    
                    # Check if should display
                    if not slide_type_obj.should_display(temp_collector, temp_data, slide):
                        print(f"Skipping slide '{slide.get('title')}' (conditional slide has no data)")
                        with self.current_slide_lock:
                            self.current_slide = None
                        continue
                    
                    title = slide.get("title", "")
                    display_duration = slide.get("duration", 10)  # How long to display the slide
                    refresh_duration = slide.get("refresh_duration", 5)  # How often to refresh data
                    
                    # Use the collector we created for conditional check, or create new one
                    collector = temp_collector
                    if not collector and (slide.get("service_config") or slide.get("api_config")):
                        try:
                            config_data = {
                                "service_config": slide.get("service_config", {}),
                                "api_config": slide.get("api_config")
                            }
                            collector = slide_type_obj.create_collector(config_data)
                        except Exception as e:
                            print(f"Error creating collector for slide {slide.get('id')}: {e}")
                    
                    # Get initial data
                    data = temp_data if temp_data is not None else None
                    if data is None and collector:
                        try:
                            if slide_type == "weather" and hasattr(collector, "get_data_for_city"):
                                city = slide.get("city")
                                data = collector.get_data_for_city(city) if city else collector.get_data()
                            else:
                                data = collector.get_data()
                        except Exception as e:
                            print(f"Error fetching initial data for slide {slide.get('id')}: {e}")
                            data = None
                    
                    # Render using slide type
                    try:
                        image = slide_type_obj.render(self.renderer, data, slide)
                    except Exception as e:
                        print(f"Error rendering slide {slide.get('id')}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                    
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
                            if collector and hasattr(collector, "clear_cache"):
                                collector.clear_cache()
                            
                            # Refresh data using collector
                            if collector:
                                try:
                                    if slide_type == "weather" and hasattr(collector, "get_data_for_city"):
                                        city = slide.get("city")
                                        data = collector.get_data_for_city(city) if city else collector.get_data()
                                    else:
                                        data = collector.get_data()
                                except Exception as e:
                                    print(f"Error refreshing data for slide {slide.get('id')}: {e}")
                                    data = None
                            else:
                                data = None
                            
                            # Re-render using slide type
                            try:
                                image = slide_type_obj.render(self.renderer, data, slide)
                                image_copy = image.copy()
                            except Exception as e:
                                print(f"Error re-rendering slide {slide.get('id')}: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                            
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
                            
                            # Display updated frame
                            if self.export_frames:
                                # Export to file
                                export_dir = DATA_DIR / "preview"
                                export_dir.mkdir(exist_ok=True)
                                filename = export_dir / f"slide_{frame_count:06d}_{slide.get('id')}.png"
                                image.save(filename)
                                print(f"Exported refreshed frame: {filename}")
                            else:
                                # Update the actual display with the new frame
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

