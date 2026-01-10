"""Slide renderer with Fallout theme."""

from PIL import Image, ImageDraw
from typing import Dict, Any, Optional
from .themes import FalloutTheme, DISPLAY_WIDTH, DISPLAY_HEIGHT, PADDING, LINE_HEIGHT_LARGE, LINE_HEIGHT_MEDIUM, LINE_HEIGHT_SMALL, LINE_HEIGHT_TINY
from ..utils.helpers import format_bytes, format_duration, calculate_elapsed_time, draw_progress_bar


class SlideRenderer:
    """Renderer for creating slide images."""
    
    def __init__(self):
        self.theme = FalloutTheme()
    
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
        
        # User
        draw.text((PADDING, y), f"{user}:", fill=self.theme.colors["text"], font=font_medium)
        y += LINE_HEIGHT_MEDIUM
        
        # Title (truncate if too long for larger font)
        max_title_len = 25
        display_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
        draw.text((PADDING, y), display_title, fill=self.theme.colors["text_secondary"], font=font_small)
        y += LINE_HEIGHT_SMALL + 4
        
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
        
        # CPU
        cpu_data = data.get("cpu", {})
        cpu_percent = cpu_data.get("percent", 0)
        draw.text((PADDING, y), f"CPU: {cpu_percent:.1f}%", fill=self.theme.colors["text"], font=font_medium)
        
        # CPU bar (on the right side)
        bar_width = 25
        cpu_bar = draw_progress_bar(bar_width, cpu_percent, 100.0)
        bar_x = DISPLAY_WIDTH - PADDING - bar_width * 7  # Approximate width for bar string
        draw.text((bar_x, y), cpu_bar, 
                 fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_MEDIUM
        
        # Memory
        mem_data = data.get("memory", {})
        mem_used = mem_data.get("used", 0)
        mem_total = mem_data.get("total", 0)
        mem_percent = mem_data.get("percent", 0)
        
        mem_used_str = format_bytes(mem_used)
        mem_total_str = format_bytes(mem_total)
        draw.text((PADDING, y), f"MEM: {mem_used_str} / {mem_total_str}", 
                 fill=self.theme.colors["text"], font=font_medium)
        
        # Memory bar (on the right side)
        mem_bar = draw_progress_bar(bar_width, mem_percent, 100.0)
        draw.text((bar_x, y), mem_bar, 
                 fill=self.theme.colors["text"], font=font_small)
        y += LINE_HEIGHT_MEDIUM + 4
        
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
            
            # First line: path and usage
            draw.text((PADDING, y), f"{path_label}:", 
                     fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
            
            draw.text((PADDING, y), f"{disk_used_str} / {disk_total_str}", 
                     fill=self.theme.colors["text_secondary"], font=font_small)
            y += LINE_HEIGHT_SMALL
            
            # Percentage bar
            disk_bar = draw_progress_bar(bar_width, disk_percent, 100.0)
            draw.text((PADDING, y), f"{disk_percent:.1f}% {disk_bar}", 
                     fill=self.theme.colors["text"], font=font_small)
            y += LINE_HEIGHT_SMALL
            
            if len(disks) > 1:
                draw.text((PADDING, y), f"+{len(disks) - 1} more disk(s)...", 
                         fill=self.theme.colors["text_muted"], font=font_small)
        
        return y

