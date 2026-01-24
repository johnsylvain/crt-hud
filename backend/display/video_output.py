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
            height = 240 * self.scale  # 240p
            
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
            scaled_image = image.resize((320 * self.scale, 240 * self.scale), Image.NEAREST)
            
            # Convert to pygame surface
            img_str = scaled_image.tobytes()
            pygame_surface = pygame.image.fromstring(img_str, (320 * self.scale, 240 * self.scale), "RGB")
            
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
    """Output to Raspberry Pi framebuffer (/dev/fb0) for composite video."""
    
    def __init__(self, device: str = "/dev/fb0"):
        self.device = device
        self.fb = None
        self._initialized = False
        self.fb_width = 320
        self.fb_height = 240  # 240p for better readability on composite video
        self.fb_bpp = 16  # RGB565 format for composite video
    
    def initialize(self) -> bool:
        """Initialize framebuffer device and disable console output."""
        try:
            import subprocess
            
            # Check if device exists
            if not os.path.exists(self.device):
                print(f"Framebuffer device {self.device} not found")
                return False
            
            # Try to get framebuffer info using fbset if available
            # This detects the actual resolution instead of forcing it
            try:
                result = subprocess.run(['fbset', '-i'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    # Parse fbset output to get actual dimensions
                    for line in result.stdout.split('\n'):
                        if 'geometry' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                self.fb_width = int(parts[1])
                                self.fb_height = int(parts[2])
                                if len(parts) >= 5:
                                    self.fb_bpp = int(parts[4])
                            print(f"Detected framebuffer: {self.fb_width}x{self.fb_height} @ {self.fb_bpp}bpp")
                else:
                    print(f"Using default framebuffer size: {self.fb_width}x{self.fb_height} @ {self.fb_bpp}bpp")
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                # fbset not available or parsing failed, use defaults
                print(f"Using default framebuffer size: {self.fb_width}x{self.fb_height} @ {self.fb_bpp}bpp")
            
            # Disable console cursor and output - use multiple methods for reliability
            print("Disabling console cursor and output...")
            
            # Method 1: Use setterm on current console
            try:
                subprocess.run(
                    ['setterm', '-cursor', 'off', '-blank', '0', '-powerdown', '0'],
                    capture_output=True, timeout=1
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 2: Use setterm on specific TTYs (if they exist)
            for tty in ['tty1', 'tty2', 'tty3', 'tty4', 'tty5', 'tty6', 'tty7']:
                tty_path = f'/dev/{tty}'
                if os.path.exists(tty_path):
                    try:
                        # Use setterm with explicit TTY
                        subprocess.run(
                            ['setterm', '-cursor', 'off', '-blank', '0', '-powerdown', '0'],
                            stdin=open(tty_path, 'wb'),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=1
                        )
                    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
                        # TTY doesn't exist or no permission, continue
                        pass
            
            # Method 3: Try to disable console on framebuffer using con2fbmap
            try:
                # Map console away from framebuffer (to tty2 or disable)
                # This prevents terminal output from appearing on composite video
                subprocess.run(['con2fbmap', '1', '1'], capture_output=True, text=True, timeout=1)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 4: Write escape sequences directly to console to hide cursor
            # ANSI escape code to hide cursor: \033[?25l
            try:
                for tty_path in ['/dev/console', '/dev/tty1']:
                    if os.path.exists(tty_path):
                        try:
                            with open(tty_path, 'wb') as tty:
                                tty.write(b'\033[?25l')  # Hide cursor
                                tty.write(b'\033[2J')    # Clear screen
                                tty.flush()
                        except (PermissionError, OSError):
                            pass
            except Exception:
                pass
            
            # Open framebuffer (requires write permissions)
            self.fb = open(self.device, "wb")
            self._initialized = True
            
            # Clear framebuffer (write black screen) to remove any console output
            self._clear_framebuffer()
            
            print(f"Framebuffer initialized: {self.device} at {self.fb_width}x{self.fb_height} @ {self.fb_bpp}bpp")
            return True
        except PermissionError:
            print(f"Permission denied accessing {self.device}. Try running with sudo or add user to video group.")
            return False
        except Exception as e:
            print(f"Failed to initialize framebuffer: {e}")
            return False
    
    def _clear_framebuffer(self) -> None:
        """Clear the framebuffer by writing black pixels."""
        if not self._initialized or self.fb is None:
            return
        
        try:
            # Calculate framebuffer size in bytes (width * height * bytes_per_pixel)
            bytes_per_pixel = self.fb_bpp // 8
            fb_size = self.fb_width * self.fb_height * bytes_per_pixel
            
            # Write black pixels (all zeros for RGB565)
            black_data = b'\x00' * fb_size
            self.fb.seek(0)
            self.fb.write(black_data)
            self.fb.flush()
        except Exception as e:
            print(f"Warning: Failed to clear framebuffer: {e}")
    
    def _rgb_to_rgb565(self, r: int, g: int, b: int) -> int:
        """Convert RGB888 to RGB565 format."""
        # RGB565: RRRRR GGGGGG BBBBB
        # Red: 5 bits (shift 11), Green: 6 bits (shift 5), Blue: 5 bits
        r5 = (r >> 3) & 0x1F  # 5 bits for red
        g6 = (g >> 2) & 0x3F  # 6 bits for green
        b5 = (b >> 3) & 0x1F  # 5 bits for blue
        return (r5 << 11) | (g6 << 5) | b5
    
    def display_frame(self, image: Image.Image) -> bool:
        """Write frame to framebuffer in RGB565 format."""
        if not self._initialized or self.fb is None:
            print("Framebuffer not initialized")
            return False
        
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize to framebuffer dimensions
            if image.size != (self.fb_width, self.fb_height):
                image = image.resize((self.fb_width, self.fb_height), Image.LANCZOS)
            
            # Convert to RGB565 format
            # Get pixel data
            pixels = image.load()
            rgb565_data = bytearray()
            
            # Convert each pixel to RGB565 (little-endian 16-bit)
            for y in range(self.fb_height):
                for x in range(self.fb_width):
                    r, g, b = pixels[x, y]
                    rgb565 = self._rgb_to_rgb565(r, g, b)
                    # Write as little-endian (low byte first, then high byte)
                    rgb565_data.append(rgb565 & 0xFF)  # Low byte
                    rgb565_data.append((rgb565 >> 8) & 0xFF)  # High byte
            
            # Write to framebuffer
            self.fb.seek(0)
            bytes_written = self.fb.write(rgb565_data)
            self.fb.flush()
            
            # Verify we wrote the expected amount
            expected_bytes = self.fb_width * self.fb_height * 2  # 2 bytes per RGB565 pixel
            if bytes_written != expected_bytes:
                print(f"Warning: Expected to write {expected_bytes} bytes, wrote {bytes_written}")
            
            return True
        except Exception as e:
            print(f"Failed to write to framebuffer: {e}")
            import traceback
            traceback.print_exc()
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

