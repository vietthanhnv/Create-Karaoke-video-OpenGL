"""
Audio waveform generation and caching system for timeline visualization.
"""

import os
import subprocess
import json
import tempfile
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import numpy as np
from dataclasses import dataclass

from core.models import AudioAsset, ValidationResult


@dataclass
class WaveformData:
    """Container for waveform visualization data."""
    samples: np.ndarray  # Amplitude values normalized to [-1, 1]
    sample_rate: float   # Samples per second in the waveform data
    duration: float      # Total duration in seconds
    channels: int        # Number of audio channels
    resolution: int      # Number of samples in the waveform array


class WaveformGenerator:
    """
    Generates and caches audio waveform data for timeline visualization.
    
    This class handles:
    - Audio data extraction using FFmpeg
    - Waveform downsampling for different zoom levels
    - Caching of processed waveform data
    - Multi-channel audio processing
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize waveform generator.
        
        Args:
            cache_dir: Directory for caching waveform data (optional)
        """
        self._cache_dir = cache_dir or tempfile.gettempdir()
        self._waveform_cache: Dict[str, WaveformData] = {}
        self._ffmpeg_available = self._check_ffmpeg_availability()
        
        if not self._ffmpeg_available:
            logging.warning("FFmpeg not available - waveform generation will use fallback method")
    
    def generate_waveform(self, audio_asset: AudioAsset, resolution: int = 1000, 
                         channel: Optional[int] = None) -> WaveformData:
        """
        Generate waveform data for an audio asset.
        
        Args:
            audio_asset: Audio asset to process
            resolution: Number of waveform samples to generate
            channel: Specific channel to extract (None for mixed/stereo)
            
        Returns:
            WaveformData containing amplitude samples and metadata
            
        Raises:
            ValueError: If audio asset is invalid
            RuntimeError: If waveform generation fails
        """
        # Validate audio asset
        validation = audio_asset.validate()
        if not validation.is_valid:
            raise ValueError(f"Invalid audio asset: {validation.error_message}")
        
        # Create cache key
        cache_key = self._create_cache_key(audio_asset.path, resolution, channel)
        
        # Return cached data if available
        if cache_key in self._waveform_cache:
            return self._waveform_cache[cache_key]
        
        # Generate waveform data
        if self._ffmpeg_available:
            waveform_data = self._generate_with_ffmpeg(audio_asset, resolution, channel)
        else:
            waveform_data = self._generate_fallback(audio_asset, resolution, channel)
        
        # Cache the result
        self._waveform_cache[cache_key] = waveform_data
        
        return waveform_data
    
    def _generate_with_ffmpeg(self, audio_asset: AudioAsset, resolution: int, 
                             channel: Optional[int]) -> WaveformData:
        """
        Generate waveform using FFmpeg for accurate audio processing.
        
        Args:
            audio_asset: Audio asset to process
            resolution: Number of waveform samples
            channel: Specific channel to extract
            
        Returns:
            WaveformData with extracted audio samples
        """
        try:
            # Create temporary file for raw audio data
            with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as tmp_file:
                raw_audio_path = tmp_file.name
            
            # Build FFmpeg command for audio extraction
            cmd = [
                'ffmpeg',
                '-i', audio_asset.path,
                '-f', 'f32le',  # 32-bit float little-endian
                '-acodec', 'pcm_f32le',
                '-ar', '44100',  # Resample to 44.1kHz for consistency
            ]
            
            # Handle channel selection
            if channel is not None and audio_asset.channels > 1:
                if channel == 0:
                    cmd.extend(['-af', 'pan=mono|c0=0.5*c0+0.5*c1'])  # Left channel
                elif channel == 1:
                    cmd.extend(['-af', 'pan=mono|c0=0.5*c0+0.5*c1'])  # Right channel
                else:
                    cmd.extend(['-ac', '1'])  # Mix to mono
            else:
                cmd.extend(['-ac', '1'])  # Mix to mono for waveform
            
            cmd.extend(['-y', raw_audio_path])
            
            # Execute FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            # Read raw audio data
            if not os.path.exists(raw_audio_path):
                raise RuntimeError("FFmpeg did not produce output file")
            
            # Load audio samples as float32
            audio_samples = np.fromfile(raw_audio_path, dtype=np.float32)
            
            # Clean up temporary file
            os.unlink(raw_audio_path)
            
            # Downsample to target resolution
            if len(audio_samples) > resolution:
                # Calculate samples per waveform point
                samples_per_point = len(audio_samples) // resolution
                
                # Create waveform by taking RMS of chunks
                waveform = np.zeros(resolution)
                for i in range(resolution):
                    start_idx = i * samples_per_point
                    end_idx = min(start_idx + samples_per_point, len(audio_samples))
                    
                    if start_idx < len(audio_samples):
                        chunk = audio_samples[start_idx:end_idx]
                        # Use RMS for better waveform representation
                        waveform[i] = np.sqrt(np.mean(chunk ** 2))
                
                # Apply sign based on average of chunk
                for i in range(resolution):
                    start_idx = i * samples_per_point
                    end_idx = min(start_idx + samples_per_point, len(audio_samples))
                    
                    if start_idx < len(audio_samples):
                        chunk = audio_samples[start_idx:end_idx]
                        avg_sign = np.sign(np.mean(chunk))
                        waveform[i] *= avg_sign
            else:
                # If audio is shorter than resolution, pad with zeros
                waveform = np.zeros(resolution)
                waveform[:len(audio_samples)] = audio_samples[:resolution]
            
            # Normalize to [-1, 1] range
            max_val = np.max(np.abs(waveform))
            if max_val > 0:
                waveform = waveform / max_val
            
            return WaveformData(
                samples=waveform,
                sample_rate=resolution / audio_asset.duration,
                duration=audio_asset.duration,
                channels=1,  # Waveform is always mono
                resolution=resolution
            )
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logging.warning(f"FFmpeg waveform generation failed: {e}")
            # Fall back to placeholder generation
            return self._generate_fallback(audio_asset, resolution, channel)
    
    def _generate_fallback(self, audio_asset: AudioAsset, resolution: int, 
                          channel: Optional[int]) -> WaveformData:
        """
        Generate placeholder waveform when FFmpeg is not available.
        
        Args:
            audio_asset: Audio asset to process
            resolution: Number of waveform samples
            channel: Specific channel (ignored in fallback)
            
        Returns:
            WaveformData with synthetic waveform
        """
        duration = audio_asset.duration
        time_per_sample = duration / resolution
        
        # Generate a more realistic synthetic waveform
        waveform = np.zeros(resolution)
        
        # Create multiple frequency components for realism
        frequencies = [220, 440, 880, 1760]  # Musical notes
        amplitudes = [0.4, 0.3, 0.2, 0.1]
        
        for i in range(resolution):
            t = i * time_per_sample
            
            # Combine multiple sine waves
            sample = 0.0
            for freq, amp in zip(frequencies, amplitudes):
                sample += amp * np.sin(2 * np.pi * freq * t)
            
            # Add envelope (fade in/out)
            envelope = 1.0
            fade_duration = min(duration * 0.1, 2.0)  # 10% of duration or 2 seconds
            
            if t < fade_duration:
                envelope = t / fade_duration
            elif t > duration - fade_duration:
                envelope = (duration - t) / fade_duration
            
            # Add some randomness for realism
            noise = np.random.normal(0, 0.05)
            
            waveform[i] = (sample * envelope + noise) * 0.7
        
        # Apply some variation in amplitude
        for i in range(1, resolution - 1):
            # Simple low-pass filter for smoothing
            waveform[i] = 0.25 * waveform[i-1] + 0.5 * waveform[i] + 0.25 * waveform[i+1]
        
        # Normalize
        max_val = np.max(np.abs(waveform))
        if max_val > 0:
            waveform = waveform / max_val
        
        return WaveformData(
            samples=waveform,
            sample_rate=resolution / duration,
            duration=duration,
            channels=1,
            resolution=resolution
        )
    
    def get_waveform_segment(self, waveform_data: WaveformData, start_time: float, 
                           end_time: float) -> np.ndarray:
        """
        Extract a segment of waveform data for a specific time range.
        
        Args:
            waveform_data: Source waveform data
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Numpy array containing waveform segment
        """
        # Calculate sample indices
        start_sample = int(start_time * waveform_data.sample_rate)
        end_sample = int(end_time * waveform_data.sample_rate)
        
        # Clamp to valid range
        start_sample = max(0, min(start_sample, len(waveform_data.samples)))
        end_sample = max(start_sample, min(end_sample, len(waveform_data.samples)))
        
        return waveform_data.samples[start_sample:end_sample]
    
    def resample_waveform(self, waveform_data: WaveformData, new_resolution: int) -> WaveformData:
        """
        Resample waveform data to a different resolution.
        
        Args:
            waveform_data: Source waveform data
            new_resolution: Target resolution
            
        Returns:
            New WaveformData with different resolution
        """
        if new_resolution == waveform_data.resolution:
            return waveform_data
        
        # Simple linear interpolation resampling
        old_indices = np.linspace(0, len(waveform_data.samples) - 1, len(waveform_data.samples))
        new_indices = np.linspace(0, len(waveform_data.samples) - 1, new_resolution)
        
        resampled = np.interp(new_indices, old_indices, waveform_data.samples)
        
        return WaveformData(
            samples=resampled,
            sample_rate=new_resolution / waveform_data.duration,
            duration=waveform_data.duration,
            channels=waveform_data.channels,
            resolution=new_resolution
        )
    
    def get_peak_levels(self, waveform_data: WaveformData, num_peaks: int = 100) -> List[Tuple[float, float]]:
        """
        Get peak levels for waveform visualization (min/max pairs).
        
        Args:
            waveform_data: Source waveform data
            num_peaks: Number of peak pairs to generate
            
        Returns:
            List of (min, max) tuples for each segment
        """
        samples_per_peak = len(waveform_data.samples) // num_peaks
        peaks = []
        
        for i in range(num_peaks):
            start_idx = i * samples_per_peak
            end_idx = min(start_idx + samples_per_peak, len(waveform_data.samples))
            
            if start_idx < len(waveform_data.samples):
                segment = waveform_data.samples[start_idx:end_idx]
                min_val = np.min(segment)
                max_val = np.max(segment)
                peaks.append((min_val, max_val))
            else:
                peaks.append((0.0, 0.0))
        
        return peaks
    
    def clear_cache(self) -> None:
        """Clear all cached waveform data."""
        self._waveform_cache.clear()
    
    def get_cache_info(self) -> Dict[str, int]:
        """
        Get information about cached waveform data.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_waveforms': len(self._waveform_cache),
            'total_samples': sum(len(wd.samples) for wd in self._waveform_cache.values())
        }
    
    def _create_cache_key(self, audio_path: str, resolution: int, channel: Optional[int]) -> str:
        """Create a unique cache key for waveform data."""
        # Include file modification time for cache invalidation
        try:
            mtime = os.path.getmtime(audio_path)
        except OSError:
            mtime = 0
        
        channel_str = f"_ch{channel}" if channel is not None else "_mixed"
        return f"{audio_path}_{resolution}{channel_str}_{mtime}"
    
    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available for audio processing."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def is_ffmpeg_available(self) -> bool:
        """
        Check if FFmpeg is available for waveform generation.
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        return self._ffmpeg_available


class WaveformRenderer:
    """
    Renders waveform data for timeline display.
    
    This class handles the visual representation of waveform data,
    including scaling, coloring, and drawing optimizations.
    """
    
    def __init__(self):
        """Initialize waveform renderer."""
        self.background_color = (0.1, 0.1, 0.1, 1.0)  # Dark gray
        self.waveform_color = (0.3, 0.7, 1.0, 0.8)    # Light blue
        self.center_line_color = (0.5, 0.5, 0.5, 0.5) # Gray center line
        self.peak_color = (1.0, 0.4, 0.4, 0.9)        # Red for peaks
    
    def render_waveform_data(self, waveform_data: WaveformData, width: int, height: int,
                           start_time: float = 0.0, end_time: Optional[float] = None) -> np.ndarray:
        """
        Render waveform data to a pixel array for display.
        
        Args:
            waveform_data: Waveform data to render
            width: Output width in pixels
            height: Output height in pixels
            start_time: Start time for visible range
            end_time: End time for visible range (None for full duration)
            
        Returns:
            RGBA pixel array (height, width, 4)
        """
        if end_time is None:
            end_time = waveform_data.duration
        
        # Create output array
        output = np.full((height, width, 4), self.background_color, dtype=np.float32)
        
        # Calculate time range and sample indices
        time_range = end_time - start_time
        if time_range <= 0:
            return output
        
        start_sample = int(start_time * waveform_data.sample_rate)
        end_sample = int(end_time * waveform_data.sample_rate)
        
        # Clamp to valid range
        start_sample = max(0, min(start_sample, len(waveform_data.samples)))
        end_sample = max(start_sample, min(end_sample, len(waveform_data.samples)))
        
        if start_sample >= end_sample:
            return output
        
        # Extract visible waveform segment
        visible_samples = waveform_data.samples[start_sample:end_sample]
        
        # Draw center line
        center_y = height // 2
        output[center_y, :] = self.center_line_color
        
        # Render waveform
        samples_per_pixel = len(visible_samples) / width
        
        for x in range(width):
            # Calculate sample range for this pixel
            sample_start = int(x * samples_per_pixel)
            sample_end = int((x + 1) * samples_per_pixel)
            sample_end = min(sample_end, len(visible_samples))
            
            if sample_start >= len(visible_samples):
                break
            
            # Get min/max for this pixel column
            pixel_samples = visible_samples[sample_start:sample_end]
            if len(pixel_samples) > 0:
                min_val = np.min(pixel_samples)
                max_val = np.max(pixel_samples)
                
                # Convert to pixel coordinates
                min_y = int(center_y + min_val * (height // 2))
                max_y = int(center_y + max_val * (height // 2))
                
                # Clamp to valid range
                min_y = max(0, min(min_y, height - 1))
                max_y = max(0, min(max_y, height - 1))
                
                # Ensure min_y <= max_y
                if min_y > max_y:
                    min_y, max_y = max_y, min_y
                
                # Draw waveform line
                for y in range(min_y, max_y + 1):
                    # Use peak color for extreme values
                    if abs(pixel_samples).max() > 0.8:
                        output[y, x] = self.peak_color
                    else:
                        output[y, x] = self.waveform_color
        
        return output
    
    def set_colors(self, background: Tuple[float, float, float, float] = None,
                   waveform: Tuple[float, float, float, float] = None,
                   center_line: Tuple[float, float, float, float] = None,
                   peak: Tuple[float, float, float, float] = None) -> None:
        """
        Set custom colors for waveform rendering.
        
        Args:
            background: Background color (R, G, B, A)
            waveform: Waveform color (R, G, B, A)
            center_line: Center line color (R, G, B, A)
            peak: Peak highlight color (R, G, B, A)
        """
        if background is not None:
            self.background_color = background
        if waveform is not None:
            self.waveform_color = waveform
        if center_line is not None:
            self.center_line_color = center_line
        if peak is not None:
            self.peak_color = peak