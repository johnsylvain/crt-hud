"""Video output handler for composite video (Raspberry Pi) and preview (Mac)."""

import sys
import os
from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image
from config import IS_DEV, DATA_DIR
from pathlib import Path


class VideoOutput(ABC):
    """Abstract base class for video output."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the output device. Returns True if successful."""
        pass
    
    @abstractmethod
    def display_frame(self, image: Image.Image) -> bool:
        """Display a frame. Returns True if successful."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class FilePreviewOutput(VideoOutput):
    """Save frames to files for preview (dev mode)."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (DATA_DIR / "preview")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.frame_count = 0
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize file output directory."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize file output: {e}")
            return False
    
    def display_frame(self, image: Image.Image) -> bool:
        """Save frame to file."""
        if not self._initialized:
            return False
        
        try:
            filename = self.output_dir / f"frame_{self.frame_count:06d}.png"
            image.save(filename)
            self.frame_count += 1
            return True
        except Exception as e:
            print(f"Failed to save frame: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup (no-op for file output)."""
        pass


class WindowPreviewOutput(VideoOutput):
    """Display frames in pygame window (dev mode)."""
    
    def __init__(self, scale: int = 2):
        self.scale = scale
        self.screen = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize pygame window."""
        try:
            import pygame
            pygame.init()
            
            # Window size (scaled up for visibility)
            width = 320 * self.scale
            height = 280 * self.scale
            
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Homelab HUD Preview")
            self._initialized = True
            return True
        except ImportError:
            print("pygame not available, falling back to file output")
            return False
        except Exception as e:
            print(f"Failed to initialize pygame window: {e}")
            return False
    
    def display_frame(self, image: Image.Image) -> bool:
        """Display frame in pygame window."""
        if not self._initialized or self.screen is None:
            return False
        
        try:
            import pygame
            from pygame import surfarray
            
            # Convert PIL image to pygame surface
            mode = image.mode
            if mode != "RGB":
                image = image.convert("RGB")
            
            # Scale image
            scaled_image = image.resize((320 * self.scale, 280 * self.scale), Image.NEAREST)
            
            # Convert to pygame surface
            img_str = scaled_image.tobytes()
            pygame_surface = pygame.image.fromstring(img_str, (320 * self.scale, 280 * self.scale), "RGB")
            
            self.screen.blit(pygame_surface, (0, 0))
            pygame.display.flip()
            
            # Handle events (prevent window from freezing)
            pygame.event.pump()
            
            return True
        except Exception as e:
            print(f"Failed to display frame in window: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup pygame."""
        if self.screen is not None:
            try:
                import pygame
                pygame.quit()
            except Exception:
                pass
        self._initialized = False


class FramebufferOutput(VideoOutput):
    """Output to Raspberry Pi framebuffer (/dev/fb0)."""
    
    def __init__(self, device: str = "/dev/fb0"):
        self.device = device
        self.fb = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize framebuffer device."""
        try:
            # Check if device exists
            if not os.path.exists(self.device):
                print(f"Framebuffer device {self.device} not found")
                return False
            
            # Open framebuffer (requires write permissions)
            self.fb = open(self.device, "wb")
            self._initialized = True
            return True
        except PermissionError:
            print(f"Permission denied accessing {self.device}. Try running with sudo.")
            return False
        except Exception as e:
            print(f"Failed to initialize framebuffer: {e}")
            return False
    
    def display_frame(self, image: Image.Image) -> bool:
        """Write frame to framebuffer."""
        if not self._initialized or self.fb is None:
            return False
        
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Ensure correct size
            if image.size != (320, 280):
                image = image.resize((320, 280), Image.LANCZOS)
            
            # Write raw RGB data to framebuffer
            # Note: Framebuffer format may vary, this is a basic implementation
            rgb_data = image.tobytes()
            self.fb.seek(0)
            self.fb.write(rgb_data)
            self.fb.flush()
            
            return True
        except Exception as e:
            print(f"Failed to write to framebuffer: {e}")
            return False
    
    def cleanup(self) -> None:
        """Close framebuffer."""
        if self.fb is not None:
            try:
                self.fb.close()
            except Exception:
                pass
        self._initialized = False


def create_video_output(preview_window: bool = False) -> VideoOutput:
    """
    Create appropriate video output based on platform.
    
    Args:
        preview_window: If True and on Mac, use pygame window instead of file output
    
    Returns:
        VideoOutput instance
    """
    if IS_DEV:
        # Development mode (Mac)
        if preview_window:
            output = WindowPreviewOutput()
            if output.initialize():
                return output
            # Fallback to file output if window fails
            return FilePreviewOutput()
        else:
            return FilePreviewOutput()
    else:
        # Production mode (Raspberry Pi)
        return FramebufferOutput()

