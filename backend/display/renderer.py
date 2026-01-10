"""Slide renderer with Fallout theme."""

from PIL import Image, ImageDraw, ImageOps
from typing import Dict, Any, Optional
from pathlib import Path
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
from .themes import FalloutTheme, DISPLAY_WIDTH, DISPLAY_HEIGHT, PADDING, LINE_HEIGHT_LARGE, LINE_HEIGHT_MEDIUM, LINE_HEIGHT_SMALL, LINE_HEIGHT_TINY
from ..utils.helpers import format_bytes, format_duration, format_time_mmss, calculate_elapsed_time, draw_progress_bar


class SlideRenderer:
    """Renderer for creating slide images."""
    
    def __init__(self):
        self.theme = FalloutTheme()
    
    def _floyd_steinberg_dither(self, img: Image.Image) -> Image.Image:
        """
        Apply Floyd-Steinberg dithering to convert grayscale image to black and white.
        This creates a dithered effect suitable for CRT displays.
        
        Args:
            img: PIL Image in grayscale mode (L) or RGB
            
        Returns:
            Dithered PIL Image in RGB mode (black and white pixels)
        """
        # Convert to grayscale if needed
        if img.mode != "L":
            img = img.convert("L")
        
        if HAS_NUMPY:
            # Fast numpy-based dithering
            img_array = np.array(img, dtype=np.float32)
            height, width = img_array.shape
            
            # Create output array (0 = black, 255 = white)
            output = np.zeros((height, width), dtype=np.uint8)
            
            # Floyd-Steinberg dithering coefficients
            # Error distribution to neighboring pixels
            for y in range(height):
                for x in range(width):
                    old_pixel = img_array[y, x]
                    # Threshold: convert to black (0) or white (255)
                    new_pixel = 255 if old_pixel > 127 else 0
                    output[y, x] = new_pixel
                    
                    # Calculate error
                    error = old_pixel - new_pixel
                    
                    # Distribute error to neighboring pixels (Floyd-Steinberg pattern)
                    if x + 1 < width:
                        img_array[y, x + 1] += error * 7 / 16
                    if y + 1 < height:
                        if x > 0:
                            img_array[y + 1, x - 1] += error * 3 / 16
                        img_array[y + 1, x] += error * 5 / 16
                        if x + 1 < width:
                            img_array[y + 1, x + 1] += error * 1 / 16
            
            # Convert back to PIL Image
            dithered_img = Image.fromarray(output, mode="L")
        else:
            # Fallback: pure Python implementation (slower but works without numpy)
            pixels = list(img.getdata())
            width, height = img.size
            img_data = [float(p) for p in pixels]
            output_data = [0] * len(img_data)
            
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    old_pixel = img_data[idx]
                    new_pixel = 255.0 if old_pixel > 127.0 else 0.0
                    output_data[idx] = int(new_pixel)
                    
                    error = old_pixel - new_pixel
                    
                    # Distribute error
                    if x + 1 < width:
                        img_data[idx + 1] += error * 7 / 16
                    if y + 1 < height:
                        if x > 0:
                            img_data[(y + 1) * width + (x - 1)] += error * 3 / 16
                        img_data[(y + 1) * width + x] += error * 5 / 16
                        if x + 1 < width:
                            img_data[(y + 1) * width + (x + 1)] += error * 1 / 16
            
            dithered_img = Image.new("L", (width, height))
            dithered_img.putdata(output_data)
        
        # Convert to RGB (black and white)
        return dithered_img.convert("RGB")
    
    def _wrap_text(self, text: str, font, max_width: int, draw: ImageDraw.Draw = None) -> list:
        """Wrap text into multiple lines that fit within max_width pixels."""
        # Use draw.textlength() if available, otherwise estimate
        try:
            # PIL 9.0+ has font.getlength(), older versions use draw.textlength()
            if hasattr(font, 'getlength'):
                def text_length_func(txt):
                    return font.getlength(txt)
            elif draw and hasattr(draw, 'textlength'):
                def text_length_func(txt):
                    return draw.textlength(txt, font=font)
            else:
                # Fallback: estimate based on character count (monospace)
                # Approximate: font size * 0.6 for monospace fonts
                char_width = getattr(font, 'size', 16) * 0.6 if hasattr(font, 'size') else 16 * 0.6
                def text_length_func(txt):
                    return len(txt) * char_width
        except Exception:
            # Ultimate fallback: estimate based on character count
            char_width = 16 * 0.6
            def text_length_func(txt):
                return len(txt) * char_width
        
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            # Calculate width of word with a space
            word_text = word + " "
            word_width = text_length_func(word_text)
            
            # If adding this word would exceed max width, start a new line
            if current_line and current_width + word_width > max_width:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = text_length_func(word)
            else:
                current_line.append(word)
                current_width += word_width
        
        # Add the last line
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text]
    
    def render(self, slide_type: str, data: Optional[Dict[str, Any]], title: str = "", slide_config: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Render a slide based on type and data.
        
        Args:
            slide_type: Type of slide (pihole_summary, plex_now_playing, arm_rip_progress, system_stats, weather, static_text, image)
            data: Data dictionary from collector
            title: Slide title
            slide_config: Optional slide configuration (for weather: city, temp_unit; for static_text: text, font_size, text_align, vertical_align, text_color)
        
        Returns:
            PIL Image object
        """
        img = self.theme.create_image()
        draw = ImageDraw.Draw(img)
        
        # For image slides, render full screen without title
        if slide_type == "image":
            self._render_image(img, slide_config)
            return img  # Return early since we've filled the entire canvas
        
        # For static_text slides, handle title separately for better layout control
        if slide_type == "static_text":
            self._render_static_text(img, draw, slide_config or {}, title)
            return img
        
        # Draw title for other slide types
        y = PADDING
        if title:
            draw.text(
                (PADDING, y),
                title.upper(),
                fill=self.theme.colors["text"],
                font=self.theme.fonts["large"]
            )
            y += LINE_HEIGHT_LARGE + 4
        
        # Render based on slide type
        if slide_type == "pihole_summary" and data:
            y = self._render_pihole(draw, data, y)
        elif slide_type == "plex_now_playing":
            # For Plex, always render even if data is None or empty
            # (this allows showing "NO STREAMS" vs "NO DATA AVAILABLE")
            if data is None:
                draw.text((PADDING, y), "NO DATA AVAILABLE", 
                         fill=self.theme.colors["text_muted"], font=self.theme.fonts["medium"])
            else:
                y = self._render_plex(draw, data, y)
        elif slide_type == "arm_rip_progress" and data:
            y = self._render_arm(draw, data, y)
        elif slide_type == "system_stats" and data:
            y = self._render_system(draw, data, y)
        elif slide_type == "weather" and data:
            temp_unit = (slide_config or {}).get("temp_unit", "C")
            y = self._render_weather(draw, data, y, temp_unit)
        else:
            draw.text(
                (PADDING, y),
                "NO DATA AVAILABLE",
                fill=self.theme.colors["text_muted"],
                font=self.theme.fonts["medium"]
            )
        
        return img
    
    def _render_pihole(self, draw: ImageDraw.Draw, data: Dict[str, Any], y: int) -> int:
        """Render Pi-hole stats."""
        font_medium = self.theme.fonts["medium"]
        font_small = self.theme.fonts["small"]
        
        # Queries blocked
        blocked = data.get("ads_blocked_today", 0)
        total = data.get("dns_queries_today", 0)
        percent = data.get("ads_percentage_today", 0.0)
        
        draw.text((PADDING, y), f"BLOCKED: {blocked:,}", fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        draw.text((PADDING, y), f"TOTAL: {total:,}", fill=self.theme.colors["text_secondary"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Percentage bar
        bar_width = 35
        bar = draw_progress_bar(bar_width, percent, 100.0)
        draw.text((PADDING, y), f"{percent:.1f}% {bar}", fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
        # Domains blocked
        domains = data.get("domains_being_blocked", 0)
        draw.text((PADDING, y), f"DOMAINS: {domains:,}", fill=self.theme.colors["text_secondary"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Unique clients
        clients = data.get("unique_clients", 0)
        draw.text((PADDING, y), f"CLIENTS: {clients}", fill=self.theme.colors["text_secondary"], font=font_medium)
        
        return y
    
    def _render_plex(self, draw: ImageDraw.Draw, data: Dict[str, Any], y: int) -> int:
        """Render Plex now playing."""
        font_medium = self.theme.fonts["medium"]
        font_small = self.theme.fonts["small"]
        
        # Debug logging
        print(f"Renderer: _render_plex called with data: {data}")
        if data is None:
            print("Renderer: Data is None, will show 'NO DATA AVAILABLE'")
            return y
        
        sessions = data.get("sessions", [])
        print(f"Renderer: Sessions count: {len(sessions) if sessions else 0}")
        print(f"Renderer: Sessions data: {sessions}")
        
        if not sessions:
            draw.text((PADDING, y), "NO STREAMS", fill=self.theme.colors["text_muted"], font=font_medium)
            return y
        
        # Show up to 1 session with larger fonts (can split into multiple slides if needed)
        session = sessions[0]
        user = session.get("user", "Unknown")
        title = session.get("title", "Unknown")
        progress = session.get("progress", 0)
        transcoding = session.get("transcoding", False)
        media_type = session.get("type", "")
        view_offset = session.get("view_offset", 0)  # milliseconds
        duration = session.get("duration", 0)  # milliseconds
        
        # User
        draw.text((PADDING, y), f"{user}:", fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Title (no truncation - show full title, wrap to multiple lines if needed)
        max_title_width = DISPLAY_WIDTH - (PADDING * 2)
        title_lines = self._wrap_text(title, font_small, max_title_width, draw)
        for line in title_lines:
            draw.text((PADDING, y), line, fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
        y += 4  # Extra spacing after title
        
        # For music tracks, show time/duration
        if media_type == "track" and duration > 0:
            current_time = format_time_mmss(view_offset)
            total_time = format_time_mmss(duration)
            time_str = f"{current_time} / {total_time}"
            draw.text((PADDING, y), time_str, fill=self.theme.colors["text"], font=font_small)
            y += LINE_HEIGHT_SMALL + 2
        
        # Progress bar
        bar_width = 30
        bar = draw_progress_bar(bar_width, progress, 100.0)
        transcode_indicator = " [T]" if transcoding else ""
        draw.text((PADDING, y), f"{progress:.0f}% {bar}{transcode_indicator}", 
                 fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_SMALL
        
        # Show indicator if more sessions exist
        if len(sessions) > 1:
            draw.text((PADDING, y), f"+{len(sessions) - 1} more...", 
                     fill=self.theme.colors["text_muted"], font=font_small)
        
        return y
    
    def _render_arm(self, draw: ImageDraw.Draw, data: Dict[str, Any], y: int) -> int:
        """Render ARM rip progress."""
        font_medium = self.theme.fonts["medium"]
        font_small = self.theme.fonts["small"]
        
        title = data.get("title", "Unknown")
        disctype = data.get("disctype") or data.get("video_type", "")
        start_time = data.get("start_time", "")
        no_of_titles = data.get("no_of_titles", "0")
        year = data.get("year", "")
        
        # Title (truncate if too long for larger font)
        max_title_len = 25
        display_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
        draw.text((PADDING, y), display_title, fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Type and year
        type_year = f"{disctype}"
        if year:
            type_year += f" ({year})"
        draw.text((PADDING, y), type_year, fill=self.theme.colors["text_secondary"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
        # Elapsed time
        if start_time:
            elapsed = calculate_elapsed_time(start_time)
            elapsed_str = format_duration(elapsed)
            draw.text((PADDING, y), f"ELAPSED: {elapsed_str}", fill=self.theme.colors["text"], font=font_small)
            y += LINE_HEIGHT_SMALL
        
        # Number of titles
        if no_of_titles:
            draw.text((PADDING, y), f"TITLES: {no_of_titles}", fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
        
        # Job ID
        job_id = data.get("job_id", "")
        if job_id:
            draw.text((PADDING, y), f"JOB: {job_id}", fill=self.theme.colors["text_muted"], font=font_small)
        
        return y
    
    def _render_system(self, draw: ImageDraw.Draw, data: Dict[str, Any], y: int) -> int:
        """Render system stats (CPU, Memory, NAS storage)."""
        font_medium = self.theme.fonts["medium"]
        font_small = self.theme.fonts["small"]
        bar_width = 30  # Increased for better visibility
        
        # CPU
        cpu_data = data.get("cpu", {})
        cpu_percent = cpu_data.get("percent", 0)
        draw.text((PADDING, y), f"CPU: {cpu_percent:.1f}%", fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # CPU progress bar on separate line
        cpu_bar = draw_progress_bar(bar_width, cpu_percent, 100.0)
        draw.text((PADDING, y), cpu_bar, 
                 fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
        # Memory
        mem_data = data.get("memory", {})
        mem_used = mem_data.get("used", 0)
        mem_total = mem_data.get("total", 0)
        mem_percent = mem_data.get("percent", 0)
        
        mem_used_str = format_bytes(mem_used)
        mem_total_str = format_bytes(mem_total)
        
        # Memory text on one line
        draw.text((PADDING, y), f"MEM: {mem_used_str} / {mem_total_str}", 
                 fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Memory progress bar on separate line
        mem_bar = draw_progress_bar(bar_width, mem_percent, 100.0)
        draw.text((PADDING, y), mem_bar, 
                 fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
        # Disk/NAS storage - show only 1 disk per slide for better readability
        disks = data.get("disks", [])
        if disks:
            disk = disks[0]
            path = disk.get("path", "")
            disk_used = disk.get("used", 0)
            disk_total = disk.get("total", 0)
            disk_percent = disk.get("percent", 0)
            
            # Path label (shorten if needed)
            path_label = path.split("/")[-1] if path != "/" else "ROOT"
            if len(path_label) > 10:
                path_label = path_label[:10] + "..."
            
            disk_used_str = format_bytes(disk_used)
            disk_total_str = format_bytes(disk_total)
            
            # Path label
            draw.text((PADDING, y), f"{path_label}:", 
                     fill=self.theme.colors["text"], font=font_medium)
            y += LINE_HEIGHT_MEDIUM
            
            # Usage on separate line
            draw.text((PADDING, y), f"{disk_used_str} / {disk_total_str}", 
                     fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
            
            # Percentage and bar on separate line
            disk_bar = draw_progress_bar(bar_width, disk_percent, 100.0)
            draw.text((PADDING, y), f"{disk_percent:.1f}% {disk_bar}", 
                     fill=self.theme.colors["text"], font=font_small)
            y += LINE_HEIGHT_SMALL
            
            if len(disks) > 1:
                draw.text((PADDING, y), f"+{len(disks) - 1} more disk(s)...", 
                         fill=self.theme.colors["text_muted"], font=font_small)
        
        return y
    
    def _celsius_to_fahrenheit(self, temp_c: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (temp_c * 9/5) + 32
    
    def _render_weather(self, draw: ImageDraw.Draw, data: Dict[str, Any], y: int, temp_unit: str = "C") -> int:
        """Render weather data."""
        font_medium = self.theme.fonts["medium"]
        font_small = self.theme.fonts["small"]
        
        current = data.get("current", {})
        forecast = data.get("forecast", [])
        
        # Current temperature and condition
        temp_c = current.get("temp_c", 0)
        condition = current.get("condition", "Unknown")
        feelslike_c = current.get("feelslike_c", temp_c)
        
        # Convert temperatures based on unit
        if temp_unit.upper() == "F":
            temp_display = self._celsius_to_fahrenheit(temp_c)
            feelslike_display = self._celsius_to_fahrenheit(feelslike_c)
            temp_symbol = "°F"
        else:
            temp_display = temp_c
            feelslike_display = feelslike_c
            temp_symbol = "°C"
        
        # Temperature line
        draw.text((PADDING, y), f"{temp_display:.0f}{temp_symbol}", fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Condition
        max_condition_width = DISPLAY_WIDTH - (PADDING * 2)
        condition_lines = self._wrap_text(condition, font_small, max_condition_width, draw)
        for line in condition_lines:
            draw.text((PADDING, y), line, fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
        y += 2
        
        # Feels like
        if feelslike_c != temp_c:
            draw.text((PADDING, y), f"FEELS: {feelslike_display:.0f}{temp_symbol}", 
                     fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
        
        # Humidity and wind
        humidity = current.get("humidity", 0)
        wind_kph = current.get("wind_kph", 0)
        draw.text((PADDING, y), f"H: {humidity}% W: {wind_kph:.0f}km/h", 
                 fill=self.theme.colors["text_secondary"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
        # Forecast (show up to 2 days to fit on screen)
        if forecast:
            for i, day in enumerate(forecast[:2]):  # Limit to 2 days to fit
                date_str = day.get("date", "")
                # Format date (YYYY-MM-DD -> MM/DD or just day name if available)
                if len(date_str) >= 10:
                    date_parts = date_str.split("-")
                    if len(date_parts) >= 2:
                        date_display = f"{date_parts[1]}/{date_parts[2]}"
                    else:
                        date_display = date_str[:5]
                else:
                    date_display = date_str
                
                maxtemp_c = day.get("maxtemp_c", 0)
                mintemp_c = day.get("mintemp_c", 0)
                day_condition = day.get("condition", "Unknown")
                chance_rain = day.get("daily_chance_of_rain", 0)
                
                # Convert forecast temps based on unit
                if temp_unit.upper() == "F":
                    maxtemp_display = self._celsius_to_fahrenheit(maxtemp_c)
                    mintemp_display = self._celsius_to_fahrenheit(mintemp_c)
                    temp_symbol = "°F"
                else:
                    maxtemp_display = maxtemp_c
                    mintemp_display = mintemp_c
                    temp_symbol = "°C"
                
                # Format: "MM/DD: H/L°C Condition [Rain%]"
                condition_short = day_condition[:12]  # Truncate long conditions
                forecast_line = f"{date_display}: {maxtemp_display:.0f}/{mintemp_display:.0f}{temp_symbol} {condition_short}"
                if chance_rain > 0:
                    forecast_line += f" [{chance_rain}%]"
                
                draw.text((PADDING, y), forecast_line, 
                         fill=self.theme.colors["text"], font=font_small)
                y += LINE_HEIGHT_SMALL
            
            # Show indicator if more forecast days exist
            if len(forecast) > 2:
                draw.text((PADDING, y), f"+{len(forecast) - 2} more day(s)...", 
                         fill=self.theme.colors["text_muted"], font=font_small)
        
        return y
    
    def _render_image(self, img: Image.Image, slide_config: Optional[Dict[str, Any]] = None) -> None:
        """Render an image slide in black and white."""
        if not slide_config:
            draw = ImageDraw.Draw(img)
            draw.text(
                (PADDING, PADDING),
                "NO IMAGE CONFIGURED",
                fill=self.theme.colors["text_muted"],
                font=self.theme.fonts["medium"]
            )
            return
        
        # Get image path from slide config
        image_path = slide_config.get("image_path", "")
        if not image_path:
            draw = ImageDraw.Draw(img)
            draw.text(
                (PADDING, PADDING),
                "NO IMAGE PATH",
                fill=self.theme.colors["text_muted"],
                font=self.theme.fonts["medium"]
            )
            return
        
        # Resolve image path (relative to data directory or absolute)
        data_dir = Path(__file__).parent.parent.parent / "data"
        if Path(image_path).is_absolute():
            full_path = Path(image_path)
        else:
            full_path = data_dir / image_path
        
        # Check if image exists, try alternative extensions if needed
        if not full_path.exists():
            # Try common alternative extensions (in case of extension mismatch)
            parent_dir = full_path.parent
            filename_stem = full_path.stem
            original_ext = full_path.suffix.lower()
            alternative_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
            
            # Remove the original extension from alternatives
            if original_ext in alternative_extensions:
                alternative_extensions.remove(original_ext)
            
            # Try to find file with alternative extensions
            found_path = None
            for alt_ext in alternative_extensions:
                alt_path = parent_dir / f"{filename_stem}{alt_ext}"
                if alt_path.exists():
                    found_path = alt_path
                    print(f"Image path mismatch: Found {alt_path.name} instead of {full_path.name}, using found file")
                    break
            
            if found_path:
                full_path = found_path
            else:
                # File not found even with alternative extensions
                similar_files = list(parent_dir.glob(f"{filename_stem}.*")) if parent_dir.exists() else []
                
                draw = ImageDraw.Draw(img)
                error_msg = f"NOT FOUND: {Path(image_path).name}"
                if similar_files:
                    # Found similar files - list them for debugging
                    found_names = [f.name for f in similar_files]
                    error_msg = f"NOT FOUND: {Path(image_path).name}\nFound: {', '.join(found_names[:2])}"
                
                draw.text(
                    (PADDING, PADDING),
                    error_msg,
                    fill=self.theme.colors["text_muted"],
                    font=self.theme.fonts["small"]
                )
                
                # Also print to console for debugging
                print(f"Image render error: Image not found - {full_path}")
                if similar_files:
                    print(f"Similar files found: {[str(f.name) for f in similar_files]}")
                
                return
        
        try:
            # Load the image
            loaded_img = Image.open(full_path)
            
            # Handle animated GIFs - extract first frame
            if hasattr(loaded_img, 'is_animated') and loaded_img.is_animated:
                # Seek to first frame and create a new image from it
                loaded_img.seek(0)
                # Create a copy to avoid issues with animated images
                frame = Image.new("RGBA", loaded_img.size)
                frame.paste(loaded_img)
                loaded_img = frame
            
            # Convert to RGB if necessary (handles RGBA, P, GIF, etc.)
            if loaded_img.mode != "RGB":
                # Handle palette mode (common for GIFs) first
                if loaded_img.mode == "P":
                    # Check if there's transparency
                    if "transparency" in loaded_img.info:
                        # Convert palette mode with transparency to RGBA
                        loaded_img = loaded_img.convert("RGBA")
                    else:
                        # Convert palette mode without transparency directly to RGB
                        loaded_img = loaded_img.convert("RGB")
                
                # Now handle RGBA (from GIF with transparency or other sources)
                if loaded_img.mode == "RGBA":
                    # Create a black background for transparency to match theme
                    rgb_img = Image.new("RGB", loaded_img.size, (0, 0, 0))
                    rgb_img.paste(loaded_img, mask=loaded_img.split()[3])  # Use alpha channel as mask
                    loaded_img = rgb_img
                elif loaded_img.mode != "RGB":
                    # Convert any other mode to RGB
                    rgb_img = Image.new("RGB", loaded_img.size, (0, 0, 0))
                    rgb_img.paste(loaded_img)
                    loaded_img = rgb_img
            
            # Convert to grayscale first
            if loaded_img.mode != "L":
                gray_img = ImageOps.grayscale(loaded_img)
            else:
                gray_img = loaded_img
            
            # Crop and resize to fill entire display (before dithering for better quality)
            img_width, img_height = gray_img.size
            display_width = DISPLAY_WIDTH
            display_height = DISPLAY_HEIGHT
            
            # Calculate scaling to cover entire display (crop strategy)
            # Use max scale so image covers entire area, then crop
            scale_w = display_width / img_width
            scale_h = display_height / img_height
            scale = max(scale_w, scale_h)  # Use max to ensure full coverage
            
            # Resize image to cover the display (will be larger than display in one dimension)
            scaled_width = int(img_width * scale)
            scaled_height = int(img_height * scale)
            
            # Resize image before cropping (higher quality)
            resized_img = gray_img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            
            # Calculate crop box to center crop to display dimensions
            # Crop from the center of the scaled image
            left = (scaled_width - display_width) // 2
            top = (scaled_height - display_height) // 2
            right = left + display_width
            bottom = top + display_height
            
            # Crop the image to exact display dimensions
            cropped_img = resized_img.crop((left, top, right, bottom))
            
            # Apply Floyd-Steinberg dithering for CRT-style display
            try:
                dithered_img = self._floyd_steinberg_dither(cropped_img)
            except Exception as e:
                # Fallback to simple threshold if dithering fails
                print(f"Warning: Dithering failed, using simple threshold: {e}")
                # Simple threshold conversion using PIL only
                pixels = list(cropped_img.getdata())
                thresholded_pixels = [255 if p > 127 else 0 for p in pixels]
                dithered_img = Image.new("L", cropped_img.size)
                dithered_img.putdata(thresholded_pixels)
                dithered_img = dithered_img.convert("RGB")
            
            # Paste the dithered image onto the canvas (fills entire display)
            img.paste(dithered_img, (0, 0))
            
        except Exception as e:
            # If image loading fails, show error message
            draw = ImageDraw.Draw(img)
            error_msg = f"ERROR LOADING IMAGE: {str(e)[:40]}"
            draw.text(
                (PADDING, PADDING),
                error_msg,
                fill=self.theme.colors["text_muted"],
                font=self.theme.fonts["small"]
            )
    
    def _render_static_text(self, img: Image.Image, draw: ImageDraw.Draw, slide_config: Dict[str, Any], title: str = "") -> None:
        """Render static text slide with styling options. Title is not displayed for static text slides."""
        # Get text content
        text_content = slide_config.get("text", "")
        if not text_content:
            draw.text(
                (PADDING, PADDING),
                "NO TEXT CONTENT",
                fill=self.theme.colors["text_muted"],
                font=self.theme.fonts["medium"]
            )
            return
        
        # Static text slides don't show title - use full canvas
        # Get styling options
        font_size_key = slide_config.get("font_size", "medium")
        text_align = slide_config.get("text_align", "left")
        vertical_align = slide_config.get("vertical_align", "center")
        text_color_key = slide_config.get("text_color", "text")
        
        # Get font based on size
        font_map = {
            "small": self.theme.fonts["small"],
            "medium": self.theme.fonts["medium"],
            "large": self.theme.fonts["large"]
        }
        font = font_map.get(font_size_key, self.theme.fonts["medium"])
        
        # Get line height based on font size
        line_height_map = {
            "small": LINE_HEIGHT_SMALL,
            "medium": LINE_HEIGHT_MEDIUM,
            "large": LINE_HEIGHT_LARGE
        }
        line_height = line_height_map.get(font_size_key, LINE_HEIGHT_MEDIUM)
        
        # Get text color
        text_color = self.theme.colors.get(text_color_key, self.theme.colors["text"])
        
        # Split text into lines
        text_lines = text_content.split("\n")
        
        # Wrap long lines if needed
        wrapped_lines = []
        max_width = DISPLAY_WIDTH - (PADDING * 2)
        for line in text_lines:
            if line.strip():
                wrapped = self._wrap_text(line, font, max_width, draw)
                wrapped_lines.extend(wrapped)
            else:
                # Preserve empty lines
                wrapped_lines.append("")
        
        # Calculate total height of text
        total_text_height = len(wrapped_lines) * line_height
        
        # Calculate available space (full canvas height minus padding)
        available_height = DISPLAY_HEIGHT - (PADDING * 2)
        
        # Calculate starting Y position based on vertical alignment
        # Vertical alignment uses full canvas (no title)
        if vertical_align == "top":
            start_y = PADDING
        elif vertical_align == "bottom":
            start_y = DISPLAY_HEIGHT - total_text_height - PADDING
        else:  # center (default)
            # Center within full canvas
            start_y = PADDING + max(0, (available_height - total_text_height) // 2)
        
        # Ensure start_y is at least PADDING
        start_y = max(PADDING, start_y)
        
        # Render each line
        current_y = start_y
        for line in wrapped_lines:
            if not line.strip():
                # Empty line - just advance
                current_y += line_height
                continue
            
            # Calculate X position based on horizontal alignment
            if hasattr(font, 'getlength'):
                line_width = font.getlength(line)
            elif hasattr(draw, 'textlength'):
                line_width = draw.textlength(line, font=font)
            else:
                # Fallback: estimate based on character count
                char_width = getattr(font, 'size', 18) * 0.6
                line_width = len(line) * char_width
            
            if text_align == "center":
                x = (DISPLAY_WIDTH - line_width) // 2
            elif text_align == "right":
                x = DISPLAY_WIDTH - line_width - PADDING
            else:  # left (default)
                x = PADDING
            
            # Ensure x is within bounds
            x = max(PADDING, min(x, DISPLAY_WIDTH - PADDING))
            
            # Draw the line
            draw.text((x, current_y), line, fill=text_color, font=font)
            current_y += line_height
            
            # Stop if we've gone beyond the display height
            if current_y > DISPLAY_HEIGHT - PADDING:
                break

