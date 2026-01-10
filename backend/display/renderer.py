"""Slide renderer with Fallout theme."""

from PIL import Image, ImageDraw
from typing import Dict, Any, Optional
from .themes import FalloutTheme, DISPLAY_WIDTH, DISPLAY_HEIGHT, PADDING, LINE_HEIGHT_LARGE, LINE_HEIGHT_MEDIUM, LINE_HEIGHT_SMALL, LINE_HEIGHT_TINY
from ..utils.helpers import format_bytes, format_duration, format_time_mmss, calculate_elapsed_time, draw_progress_bar


class SlideRenderer:
    """Renderer for creating slide images."""
    
    def __init__(self):
        self.theme = FalloutTheme()
    
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
    
    def render(self, slide_type: str, data: Optional[Dict[str, Any]], title: str = "") -> Image.Image:
        """
        Render a slide based on type and data.
        
        Args:
            slide_type: Type of slide (pihole_summary, plex_now_playing, arm_rip_progress, system_stats)
            data: Data dictionary from collector
            title: Slide title
        
        Returns:
            PIL Image object
        """
        img = self.theme.create_image()
        draw = ImageDraw.Draw(img)
        
        # Draw title
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

