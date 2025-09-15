"""
Timeline engine implementation for temporal state management and keyframe operations.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .interfaces import ITimelineEngine
from .models import (
    Keyframe, SubtitleTrack, VideoAsset, AudioAsset, InterpolationType, 
    EasingType, ValidationResult
)
from ..audio.waveform_generator import WaveformGenerator, WaveformData


class TimelineEngine(ITimelineEngine):
    """
    Core timeline engine that manages temporal state, keyframes, and synchronization.
    
    This class handles:
    - Keyframe creation, editing, and interpolation
    - Timeline synchronization with video playback
    - Audio waveform generation for timing reference
    - Temporal state management across subtitle tracks
    """
    
    def __init__(self, video_asset: Optional[VideoAsset] = None):
        """Initialize timeline engine with optional video asset."""
        self._video_asset = video_asset
        self._audio_asset: Optional[AudioAsset] = None
        self._subtitle_tracks: Dict[str, SubtitleTrack] = {}
        self._current_time = 0.0
        self._playback_speed = 1.0
        self._is_playing = False
        
        # Waveform generator for audio visualization
        self._waveform_generator = WaveformGenerator()
        self._cached_waveform_data: Optional[WaveformData] = None
        
        # Timeline bounds
        self._start_time = 0.0
        self._end_time = self._video_asset.duration if video_asset else 0.0
    
    @property
    def current_time(self) -> float:
        """Get current timeline position."""
        return self._current_time
    
    @current_time.setter
    def current_time(self, time: float) -> None:
        """Set current timeline position with bounds checking."""
        self._current_time = max(self._start_time, min(time, self._end_time))
    
    @property
    def duration(self) -> float:
        """Get total timeline duration."""
        return self._end_time - self._start_time
    
    @property
    def video_asset(self) -> Optional[VideoAsset]:
        """Get associated video asset."""
        return self._video_asset
    
    @video_asset.setter
    def video_asset(self, asset: VideoAsset) -> None:
        """Set video asset and update timeline bounds."""
        self._video_asset = asset
        self._end_time = asset.duration
        # Clamp current time to new bounds
        self.current_time = self._current_time
    
    @property
    def audio_asset(self) -> Optional[AudioAsset]:
        """Get associated audio asset."""
        return self._audio_asset
    
    @audio_asset.setter
    def audio_asset(self, asset: Optional[AudioAsset]) -> None:
        """Set audio asset and clear waveform cache."""
        self._audio_asset = asset
        self._cached_waveform_data = None
    
    def add_subtitle_track(self, track: SubtitleTrack) -> None:
        """Add a subtitle track to the timeline."""
        self._subtitle_tracks[track.id] = track
    
    def remove_subtitle_track(self, track_id: str) -> bool:
        """Remove a subtitle track from the timeline."""
        if track_id in self._subtitle_tracks:
            del self._subtitle_tracks[track_id]
            return True
        return False
    
    def get_subtitle_track(self, track_id: str) -> Optional[SubtitleTrack]:
        """Get a subtitle track by ID."""
        return self._subtitle_tracks.get(track_id)
    
    def get_all_tracks(self) -> List[SubtitleTrack]:
        """Get all subtitle tracks."""
        return list(self._subtitle_tracks.values())
    
    def add_track(self, track: SubtitleTrack) -> None:
        """Add a track to the timeline (alias for add_subtitle_track)."""
        self.add_subtitle_track(track)
    
    def get_current_time(self) -> float:
        """Get current timeline time."""
        return self._current_time
    
    def set_video_source(self, video_path: str) -> None:
        """
        Set video source for the timeline.
        
        Args:
            video_path: Path to video file
        """
        # This would normally create a VideoAsset from the path
        # For now, just store the path
        self._video_source_path = video_path
    
    def get_active_elements_at_time(self, time: float) -> List[Tuple[str, List]]:
        """
        Get active subtitle elements at specified time.
        
        Args:
            time: Timeline time in seconds
            
        Returns:
            List of tuples (track_id, elements) for active elements
        """
        active_elements = []
        
        for track_id, track in self._subtitle_tracks.items():
            track_elements = []
            
            # Check each element in the track
            for element in track.elements:
                # For now, assume elements are active during their time range
                # This would normally check keyframes and timing
                if hasattr(element, 'start_time') and hasattr(element, 'end_time'):
                    if element.start_time <= time <= element.end_time:
                        track_elements.append(element)
                else:
                    # If no timing info, assume always active
                    track_elements.append(element)
            
            if track_elements:
                active_elements.append((track_id, track_elements))
        
        return active_elements
    
    def add_keyframe(self, track_id: str, time: float, properties: Dict[str, Any]) -> bool:
        """
        Add a keyframe to the specified track.
        
        Args:
            track_id: ID of the subtitle track
            time: Time position for the keyframe
            properties: Dictionary of properties to animate
            
        Returns:
            True if keyframe was added successfully, False otherwise
        """
        track = self._subtitle_tracks.get(track_id)
        if not track:
            return False
        
        # Validate time bounds
        if not (track.start_time <= time <= track.end_time):
            return False
        
        # Create new keyframe
        keyframe = Keyframe(
            time=time,
            properties=properties.copy(),
            interpolation_type=InterpolationType.LINEAR
        )
        
        # Insert keyframe in chronological order
        insert_index = 0
        for i, existing_kf in enumerate(track.keyframes):
            if existing_kf.time > time:
                insert_index = i
                break
            elif existing_kf.time == time:
                # Replace existing keyframe at same time
                track.keyframes[i] = keyframe
                return True
            insert_index = i + 1
        
        track.keyframes.insert(insert_index, keyframe)
        return True
    
    def remove_keyframe(self, track_id: str, time: float, tolerance: float = 0.001) -> bool:
        """
        Remove a keyframe at the specified time.
        
        Args:
            track_id: ID of the subtitle track
            time: Time position of keyframe to remove
            tolerance: Time tolerance for matching keyframes
            
        Returns:
            True if keyframe was removed, False otherwise
        """
        track = self._subtitle_tracks.get(track_id)
        if not track:
            return False
        
        for i, keyframe in enumerate(track.keyframes):
            if abs(keyframe.time - time) <= tolerance:
                track.keyframes.pop(i)
                return True
        
        return False
    
    def get_keyframes_at_time(self, track_id: str, time: float, tolerance: float = 0.001) -> List[Keyframe]:
        """Get all keyframes at the specified time within tolerance."""
        track = self._subtitle_tracks.get(track_id)
        if not track:
            return []
        
        return [kf for kf in track.keyframes if abs(kf.time - time) <= tolerance]
    
    def interpolate_properties(self, track_id: str, time: float) -> Dict[str, Any]:
        """
        Interpolate properties at the given time for a specific track.
        
        Args:
            track_id: ID of the subtitle track
            time: Time position to interpolate at
            
        Returns:
            Dictionary of interpolated property values
        """
        track = self._subtitle_tracks.get(track_id)
        if not track or not track.keyframes:
            return {}
        
        # Find surrounding keyframes
        prev_kf = None
        next_kf = None
        
        for keyframe in track.keyframes:
            if keyframe.time <= time:
                prev_kf = keyframe
            elif keyframe.time > time and next_kf is None:
                next_kf = keyframe
                break
        
        # If no surrounding keyframes, return empty dict
        if prev_kf is None and next_kf is None:
            return {}
        
        # If only one keyframe, return its properties
        if prev_kf is not None and next_kf is None:
            return prev_kf.properties.copy()
        
        if prev_kf is None and next_kf is not None:
            return next_kf.properties.copy()
        
        # Interpolate between keyframes
        return self._interpolate_between_keyframes(prev_kf, next_kf, time)
    
    def _interpolate_between_keyframes(self, kf1: Keyframe, kf2: Keyframe, time: float) -> Dict[str, Any]:
        """
        Interpolate properties between two keyframes.
        
        Args:
            kf1: First keyframe (earlier in time)
            kf2: Second keyframe (later in time)
            time: Time position to interpolate at
            
        Returns:
            Dictionary of interpolated values
        """
        if kf1.time == kf2.time:
            return kf2.properties.copy()
        
        # Calculate interpolation factor (0.0 to 1.0)
        t = (time - kf1.time) / (kf2.time - kf1.time)
        t = max(0.0, min(1.0, t))  # Clamp to valid range
        
        # Apply easing based on interpolation type
        if kf2.interpolation_type == InterpolationType.STEP:
            t = 0.0 if t < 1.0 else 1.0
        elif kf2.interpolation_type == InterpolationType.BEZIER:
            # Simple cubic bezier easing (ease-in-out)
            t = t * t * (3.0 - 2.0 * t)
        # LINEAR is default, no modification needed
        
        # Interpolate each property
        result = {}
        
        # Get all unique property keys
        all_keys = set(kf1.properties.keys()) | set(kf2.properties.keys())
        
        for key in all_keys:
            val1 = kf1.properties.get(key)
            val2 = kf2.properties.get(key)
            
            # If property exists in both keyframes, interpolate
            if val1 is not None and val2 is not None:
                result[key] = self._interpolate_value(val1, val2, t)
            # If property only exists in one keyframe, use that value
            elif val1 is not None:
                result[key] = val1
            elif val2 is not None:
                result[key] = val2
        
        return result
    
    def _interpolate_value(self, val1: Any, val2: Any, t: float) -> Any:
        """
        Interpolate between two values based on their types.
        
        Args:
            val1: First value
            val2: Second value
            t: Interpolation factor (0.0 to 1.0)
            
        Returns:
            Interpolated value
        """
        # Handle numeric types
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return val1 + (val2 - val1) * t
        
        # Handle tuples/lists (colors, positions, etc.)
        if isinstance(val1, (tuple, list)) and isinstance(val2, (tuple, list)):
            if len(val1) == len(val2):
                result = []
                for v1, v2 in zip(val1, val2):
                    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                        result.append(v1 + (v2 - v1) * t)
                    else:
                        result.append(v2 if t >= 0.5 else v1)
                return type(val1)(result)
        
        # Handle boolean and string types (step interpolation)
        if isinstance(val1, (bool, str)) or isinstance(val2, (bool, str)):
            return val2 if t >= 0.5 else val1
        
        # Default: return second value if t >= 0.5, otherwise first
        return val2 if t >= 0.5 else val1
    
    def copy_keyframes(self, track_id: str, keyframes: List[Keyframe]) -> List[Keyframe]:
        """
        Create copies of keyframes for paste operations.
        
        Args:
            track_id: ID of the source track
            keyframes: List of keyframes to copy
            
        Returns:
            List of copied keyframes
        """
        copied = []
        for kf in keyframes:
            copied_kf = Keyframe(
                time=kf.time,
                properties=kf.properties.copy(),
                interpolation_type=kf.interpolation_type
            )
            copied.append(copied_kf)
        
        return copied
    
    def paste_keyframes(self, track_id: str, keyframes: List[Keyframe], offset_time: float = 0.0) -> bool:
        """
        Paste keyframes to a track with optional time offset.
        
        Args:
            track_id: ID of the target track
            keyframes: List of keyframes to paste
            offset_time: Time offset to apply to pasted keyframes
            
        Returns:
            True if keyframes were pasted successfully
        """
        track = self._subtitle_tracks.get(track_id)
        if not track:
            return False
        
        for kf in keyframes:
            new_time = kf.time + offset_time
            # Only paste if within track bounds
            if track.start_time <= new_time <= track.end_time:
                self.add_keyframe(track_id, new_time, kf.properties)
        
        return True
    
    def get_waveform_data(self, audio_asset: Optional[AudioAsset] = None, 
                         resolution: int = 1000) -> Optional[WaveformData]:
        """
        Generate waveform data for audio visualization.
        
        Args:
            audio_asset: Audio asset to process (uses timeline audio if None)
            resolution: Number of waveform samples to generate
            
        Returns:
            WaveformData object or None if no audio available
        """
        # Use provided asset or timeline's audio asset
        target_asset = audio_asset or self._audio_asset
        if not target_asset:
            return None
        
        # Check if we have cached data for this asset and resolution
        if (self._cached_waveform_data and 
            self._cached_waveform_data.resolution == resolution and
            hasattr(target_asset, 'path')):
            return self._cached_waveform_data
        
        try:
            # Generate new waveform data
            waveform_data = self._waveform_generator.generate_waveform(
                target_asset, resolution
            )
            
            # Cache the result if it's for the timeline's audio asset
            if target_asset == self._audio_asset:
                self._cached_waveform_data = waveform_data
            
            return waveform_data
            
        except (ValueError, RuntimeError) as e:
            # Log error and return None
            import logging
            logging.warning(f"Failed to generate waveform data: {e}")
            return None
    
    def get_waveform_segment(self, start_time: float, end_time: float, 
                           resolution: int = 1000) -> Optional[np.ndarray]:
        """
        Get a segment of waveform data for a specific time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            resolution: Target resolution for the segment
            
        Returns:
            Numpy array of waveform samples or None if no audio
        """
        waveform_data = self.get_waveform_data(resolution=resolution)
        if not waveform_data:
            return None
        
        return self._waveform_generator.get_waveform_segment(
            waveform_data, start_time, end_time
        )
    
    def get_waveform_peaks(self, num_peaks: int = 100) -> Optional[List[Tuple[float, float]]]:
        """
        Get peak levels for waveform visualization.
        
        Args:
            num_peaks: Number of peak pairs to generate
            
        Returns:
            List of (min, max) tuples or None if no audio
        """
        waveform_data = self.get_waveform_data()
        if not waveform_data:
            return None
        
        return self._waveform_generator.get_peak_levels(waveform_data, num_peaks)
    
    def sync_to_video_frame(self, frame_number: int) -> float:
        """
        Convert video frame number to timeline time.
        
        Args:
            frame_number: Video frame number (0-based)
            
        Returns:
            Timeline time in seconds
        """
        if not self._video_asset:
            return 0.0
        
        return frame_number / self._video_asset.fps
    
    def get_frame_from_time(self, time: float) -> int:
        """
        Convert timeline time to video frame number.
        
        Args:
            time: Timeline time in seconds
            
        Returns:
            Video frame number (0-based)
        """
        if not self._video_asset:
            return 0
        
        return int(time * self._video_asset.fps)
    
    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed multiplier."""
        self._playback_speed = max(0.1, min(speed, 10.0))  # Clamp to reasonable range
    
    def get_playback_speed(self) -> float:
        """Get current playback speed multiplier."""
        return self._playback_speed
    
    def play(self) -> None:
        """Start timeline playback."""
        self._is_playing = True
    
    def pause(self) -> None:
        """Pause timeline playback."""
        self._is_playing = False
    
    def stop(self) -> None:
        """Stop timeline playback and reset to start."""
        self._is_playing = False
        self.current_time = self._start_time
    
    def is_playing(self) -> bool:
        """Check if timeline is currently playing."""
        return self._is_playing
    
    def update(self, delta_time: float) -> None:
        """
        Update timeline state during playback.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        if self._is_playing:
            new_time = self._current_time + (delta_time * self._playback_speed)
            
            # Handle end of timeline
            if new_time >= self._end_time:
                self.current_time = self._end_time
                self.pause()  # Auto-pause at end
            else:
                self.current_time = new_time
    
    def seek(self, time: float) -> None:
        """
        Seek to a specific time position.
        
        Args:
            time: Target time in seconds
        """
        self.current_time = time
    
    def get_active_elements_at_time(self, time: float) -> List[Tuple[str, List[Any]]]:
        """
        Get all active subtitle elements at the specified time.
        
        Args:
            time: Time position to query
            
        Returns:
            List of tuples containing (track_id, active_elements)
        """
        active_elements = []
        
        for track_id, track in self._subtitle_tracks.items():
            if track.start_time <= time <= track.end_time:
                # Get interpolated properties for this time
                properties = self.interpolate_properties(track_id, time)
                
                # Apply properties to track elements
                elements_with_properties = []
                for element in track.elements:
                    # Create a copy of the element with interpolated properties applied
                    modified_element = element  # In a real implementation, apply properties here
                    elements_with_properties.append(modified_element)
                
                if elements_with_properties:
                    active_elements.append((track_id, elements_with_properties))
        
        return active_elements
    
    def validate_timeline(self) -> ValidationResult:
        """
        Validate the current timeline state.
        
        Returns:
            ValidationResult indicating any issues found
        """
        errors = []
        warnings = []
        
        # Check video asset
        if not self._video_asset:
            warnings.append("No video asset associated with timeline")
        
        # Check timeline bounds
        if self._start_time >= self._end_time:
            errors.append("Invalid timeline bounds: start >= end")
        
        # Validate each track
        for track_id, track in self._subtitle_tracks.items():
            track_validation = track.validate()
            if not track_validation.is_valid:
                errors.append(f"Track {track_id}: {track_validation.error_message}")
            
            # Check for overlapping keyframes
            keyframe_times = [kf.time for kf in track.keyframes]
            if len(keyframe_times) != len(set(keyframe_times)):
                warnings.append(f"Track {track_id} has overlapping keyframes")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )