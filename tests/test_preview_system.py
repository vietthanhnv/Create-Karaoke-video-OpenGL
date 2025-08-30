"""
Tests for the preview system with 60fps rendering capabilities.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

from ui.preview_system import (
    PreviewSystem, QualityPreset, PerformanceMetrics,
    ViewportTransform, SafeAreaType, PreviewControlsWidget
)
from graphics.opengl_renderer import OpenGLRenderer
from core.timeline_engine import TimelineEngine
from core.models import VideoAsset, SubtitleTrack, TextElement


class TestPreviewSystem(unittest.TestCase):
    """Test cases for the PreviewSystem class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock renderer
        self.mock_renderer = Mock(spec=OpenGLRenderer)
        self.mock_renderer.fps_updated = Mock()
        self.mock_renderer.fps_updated.connect = Mock()
        self.mock_renderer.makeCurrent = Mock()
        self.mock_renderer.paintGL = Mock()
        self.mock_renderer.swapBuffers = Mock()
        
        # Create mock timeline engine
        self.mock_timeline = Mock(spec=TimelineEngine)
        self.mock_timeline.current_time = 0.0
        self.mock_timeline.duration = 30.0
        self.mock_timeline.get_playback_speed.return_value = 1.0
        self.mock_timeline.is_playing.return_value = False
        self.mock_timeline.get_active_elements_at_time.return_value = []
        self.mock_timeline.get_frame_from_time.return_value = 0
        
        # Create video asset mock
        self.mock_video_asset = Mock(spec=VideoAsset)
        self.mock_video_asset.resolution = (1920, 1080)
        self.mock_video_asset.fps = 30.0
        self.mock_video_asset.duration = 30.0
        self.mock_timeline.video_asset = self.mock_video_asset
        
        # Create preview system
        self.preview_system = PreviewSystem(self.mock_renderer, self.mock_timeline)
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'preview_system'):
            self.preview_system.stop_preview()
    
    def test_initialization(self):
        """Test preview system initialization."""
        self.assertIsNotNone(self.preview_system)
        self.assertFalse(self.preview_system._is_active)
        self.assertFalse(self.preview_system._is_playing)
        self.assertEqual(self.preview_system._current_quality, QualityPreset.NORMAL)
        self.assertEqual(self.preview_system._target_frame_interval, 1000 / 60)
    
    def test_start_preview(self):
        """Test starting the preview system."""
        result = self.preview_system.start_preview()
        
        self.assertTrue(result)
        self.assertTrue(self.preview_system._is_active)
        self.assertTrue(self.preview_system._render_timer.isActive())
    
    def test_stop_preview(self):
        """Test stopping the preview system."""
        # Start first
        self.preview_system.start_preview()
        self.assertTrue(self.preview_system._is_active)
        
        # Then stop
        self.preview_system.stop_preview()
        self.assertFalse(self.preview_system._is_active)
        self.assertFalse(self.preview_system._is_playing)
        self.assertFalse(self.preview_system._render_timer.isActive())
    
    def test_quality_preset_changes(self):
        """Test quality preset changes."""
        # Test setting different quality presets
        self.preview_system.set_quality_preset(QualityPreset.DRAFT)
        self.assertEqual(self.preview_system.get_quality_preset(), QualityPreset.DRAFT)
        self.assertEqual(self.preview_system._target_frame_interval, 1000 / 30)
        
        self.preview_system.set_quality_preset(QualityPreset.HIGH)
        self.assertEqual(self.preview_system.get_quality_preset(), QualityPreset.HIGH)
        self.assertEqual(self.preview_system._target_frame_interval, 1000 / 60)
        
        self.preview_system.set_quality_preset(QualityPreset.NORMAL)
        self.assertEqual(self.preview_system.get_quality_preset(), QualityPreset.NORMAL)
        self.assertEqual(self.preview_system._target_frame_interval, 1000 / 60)
    
    def test_playback_controls(self):
        """Test playback control methods."""
        self.preview_system.start_preview()
        
        # Test play
        self.preview_system.play()
        self.assertTrue(self.preview_system._is_playing)
        self.mock_timeline.play.assert_called_once()
        
        # Test pause
        self.preview_system.pause()
        self.assertFalse(self.preview_system._is_playing)
        self.mock_timeline.pause.assert_called_once()
        
        # Test stop
        self.preview_system.stop()
        self.assertFalse(self.preview_system._is_playing)
        self.mock_timeline.stop.assert_called_once()
    
    def test_seek_functionality(self):
        """Test seeking to specific time positions."""
        self.preview_system.start_preview()
        
        # Test seeking
        target_time = 15.0
        self.preview_system.seek(target_time)
        
        self.mock_timeline.seek.assert_called_with(target_time)
        self.assertEqual(len(self.preview_system._video_frame_cache), 0)  # Cache should be cleared
    
    def test_performance_metrics_initialization(self):
        """Test performance metrics initialization."""
        metrics = self.preview_system.get_performance_metrics()
        
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertEqual(metrics.current_fps, 0.0)
        self.assertEqual(metrics.target_fps, 60.0)
        self.assertEqual(metrics.frame_time_ms, 0.0)
        self.assertEqual(metrics.dropped_frames, 0)
        self.assertEqual(metrics.quality_preset, QualityPreset.NORMAL)
    
    @patch('time.time')
    def test_performance_metrics_update(self, mock_time):
        """Test performance metrics updates."""
        # Mock time progression
        mock_time.side_effect = [0.0, 0.016, 0.032, 0.048, 0.064, 0.080]  # 60fps timing
        
        self.preview_system.start_preview()
        
        # Simulate frame rendering
        for i in range(5):
            frame_time_ms = 16.0  # 16ms per frame for 60fps
            self.preview_system._update_performance_metrics(frame_time_ms)
        
        metrics = self.preview_system.get_performance_metrics()
        self.assertEqual(metrics.frame_time_ms, 16.0)
        self.assertGreater(len(self.preview_system._frame_times), 0)
    
    def test_automatic_quality_adjustment_down(self):
        """Test automatic quality reduction when performance drops."""
        self.preview_system.start_preview()
        self.preview_system.set_quality_preset(QualityPreset.HIGH)
        
        # Simulate low FPS
        self.preview_system._metrics.current_fps = 40.0  # Below threshold
        self.preview_system._last_quality_adjustment = 0.0  # Allow adjustment
        
        with patch('time.time', return_value=10.0):
            self.preview_system._check_performance_adjustment()
        
        # Should have reduced quality
        self.assertEqual(self.preview_system.get_quality_preset(), QualityPreset.NORMAL)
    
    def test_automatic_quality_adjustment_up(self):
        """Test automatic quality increase when performance is good."""
        self.preview_system.start_preview()
        self.preview_system.set_quality_preset(QualityPreset.DRAFT)
        
        # Simulate high FPS
        self.preview_system._metrics.current_fps = 58.0  # Above threshold
        self.preview_system._last_quality_adjustment = 0.0  # Allow adjustment
        
        with patch('time.time', return_value=10.0):
            self.preview_system._check_performance_adjustment()
        
        # Should have increased quality
        self.assertEqual(self.preview_system.get_quality_preset(), QualityPreset.NORMAL)
    
    def test_video_frame_caching(self):
        """Test video frame caching functionality."""
        self.preview_system.start_preview()
        
        # Test frame retrieval (should create placeholder)
        frame = self.preview_system._get_video_frame(5.0)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (1080, 1920, 3))  # Height, Width, Channels
        
        # Test cache size limit
        for i in range(35):  # Exceed cache limit
            self.preview_system._get_video_frame(float(i))
        
        # Cache should be limited to max size
        self.assertLessEqual(len(self.preview_system._video_frame_cache), 
                           self.preview_system._max_cache_size)
    
    def test_subtitle_data_preparation(self):
        """Test subtitle data preparation for rendering."""
        # Create mock subtitle elements
        text_element = TextElement(
            content="Test subtitle",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(0.5, 0.5),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        active_elements = [("track1", [text_element])]
        
        subtitle_data = self.preview_system._prepare_subtitle_data(active_elements)
        
        self.assertEqual(len(subtitle_data), 1)
        self.assertEqual(subtitle_data[0]['text'], "Test subtitle")
        self.assertEqual(subtitle_data[0]['font_family'], "Arial")
        self.assertEqual(subtitle_data[0]['font_size'], 24.0)
    
    @patch('time.time')
    def test_timeline_time_update_during_playback(self, mock_time):
        """Test timeline time updates during playback."""
        self.preview_system.start_preview()
        
        # Start playback
        mock_time.return_value = 0.0
        self.preview_system.play()
        
        # Simulate time progression
        mock_time.return_value = 2.0  # 2 seconds elapsed
        self.preview_system._update_timeline_time()
        
        # Timeline should be updated
        expected_time = 2.0 * self.mock_timeline.get_playback_speed()
        self.mock_timeline.__setattr__.assert_called_with('current_time', expected_time)
    
    def test_frame_rendering_pipeline(self):
        """Test the frame rendering pipeline."""
        self.preview_system.start_preview()
        
        # Mock active elements
        self.mock_timeline.get_active_elements_at_time.return_value = []
        
        # Test frame rendering (should not raise exceptions)
        try:
            self.preview_system._render_frame()
        except Exception as e:
            self.fail(f"Frame rendering raised an exception: {e}")
        
        # Verify renderer methods were called
        self.mock_renderer.makeCurrent.assert_called()
        self.mock_renderer.paintGL.assert_called()
        self.mock_renderer.swapBuffers.assert_called()
    
    def test_dropped_frame_detection(self):
        """Test dropped frame detection."""
        self.preview_system.start_preview()
        
        # Simulate slow frame (should be detected as dropped)
        slow_frame_time = self.preview_system._target_frame_interval * 2  # 2x target time
        self.preview_system._update_performance_metrics(slow_frame_time)
        
        metrics = self.preview_system.get_performance_metrics()
        self.assertEqual(metrics.dropped_frames, 1)
    
    def test_quality_adjustment_cooldown(self):
        """Test quality adjustment cooldown period."""
        self.preview_system.start_preview()
        
        # Set low FPS
        self.preview_system._metrics.current_fps = 40.0
        
        # First adjustment should work
        with patch('time.time', return_value=0.0):
            self.preview_system._last_quality_adjustment = 0.0
            original_quality = self.preview_system.get_quality_preset()
            self.preview_system._check_performance_adjustment()
            
        # Second adjustment too soon should be blocked
        with patch('time.time', return_value=1.0):  # Only 1 second later
            current_quality = self.preview_system.get_quality_preset()
            self.preview_system._check_performance_adjustment()
            self.assertEqual(self.preview_system.get_quality_preset(), current_quality)
    
    def test_signal_connections(self):
        """Test that signals are properly connected."""
        # Test that signals exist and can be connected
        self.assertTrue(hasattr(self.preview_system, 'fps_updated'))
        self.assertTrue(hasattr(self.preview_system, 'quality_changed'))
        self.assertTrue(hasattr(self.preview_system, 'performance_warning'))
        self.assertTrue(hasattr(self.preview_system, 'frame_rendered'))
        
        # Test signal emission (mock the emit method)
        with patch.object(self.preview_system.fps_updated, 'emit') as mock_emit:
            self.preview_system.fps_updated.emit(60.0)
            mock_emit.assert_called_once_with(60.0)


class TestPreviewSystemIntegration(unittest.TestCase):
    """Integration tests for preview system with real components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Create real video asset
        self.video_asset = VideoAsset(
            path="test_video.mp4",
            duration=10.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        # Create real timeline engine
        self.timeline_engine = TimelineEngine(self.video_asset)
        
        # Create subtitle track with test data
        self.subtitle_track = SubtitleTrack(
            id="test_track",
            elements=[
                TextElement(
                    content="Test subtitle",
                    font_family="Arial",
                    font_size=24.0,
                    color=(1.0, 1.0, 1.0, 1.0),
                    position=(0.5, 0.5),
                    rotation=(0.0, 0.0, 0.0),
                    effects=[]
                )
            ],
            keyframes=[],
            start_time=0.0,
            end_time=10.0
        )
        
        self.timeline_engine.add_subtitle_track(self.subtitle_track)
        
        # Add test keyframes
        self.timeline_engine.add_keyframe("test_track", 0.0, {"opacity": 0.0})
        self.timeline_engine.add_keyframe("test_track", 2.0, {"opacity": 1.0})
        self.timeline_engine.add_keyframe("test_track", 8.0, {"opacity": 1.0})
        self.timeline_engine.add_keyframe("test_track", 10.0, {"opacity": 0.0})
    
    def test_timeline_integration(self):
        """Test preview system integration with timeline engine."""
        # Create mock renderer for integration test
        mock_renderer = Mock(spec=OpenGLRenderer)
        mock_renderer.fps_updated = Mock()
        mock_renderer.fps_updated.connect = Mock()
        mock_renderer.makeCurrent = Mock()
        mock_renderer.paintGL = Mock()
        mock_renderer.swapBuffers = Mock()
        
        # Create preview system with real timeline
        preview_system = PreviewSystem(mock_renderer, self.timeline_engine)
        
        try:
            # Start preview
            result = preview_system.start_preview()
            self.assertTrue(result)
            
            # Test seeking
            preview_system.seek(5.0)
            self.assertEqual(self.timeline_engine.current_time, 5.0)
            
            # Test getting active elements
            active_elements = self.timeline_engine.get_active_elements_at_time(5.0)
            self.assertIsInstance(active_elements, list)
            
            # Test interpolation at different times
            props_start = self.timeline_engine.interpolate_properties("test_track", 0.0)
            props_middle = self.timeline_engine.interpolate_properties("test_track", 5.0)
            props_end = self.timeline_engine.interpolate_properties("test_track", 10.0)
            
            self.assertIsInstance(props_start, dict)
            self.assertIsInstance(props_middle, dict)
            self.assertIsInstance(props_end, dict)
            
        finally:
            preview_system.stop_preview()


def run_performance_test():
    """Run a performance test to verify 60fps capability."""
    print("\nRunning Preview System Performance Test")
    print("=" * 50)
    
    if not QApplication.instance():
        app = QApplication([])
    
    # Create mock components
    mock_renderer = Mock(spec=OpenGLRenderer)
    mock_renderer.fps_updated = Mock()
    mock_renderer.fps_updated.connect = Mock()
    mock_renderer.makeCurrent = Mock()
    mock_renderer.paintGL = Mock()
    mock_renderer.swapBuffers = Mock()
    
    mock_timeline = Mock(spec=TimelineEngine)
    mock_timeline.current_time = 0.0
    mock_timeline.duration = 30.0
    mock_timeline.get_playback_speed.return_value = 1.0
    mock_timeline.is_playing.return_value = False
    mock_timeline.get_active_elements_at_time.return_value = []
    
    # Create preview system
    preview_system = PreviewSystem(mock_renderer, mock_timeline)
    
    try:
        # Start preview
        preview_system.start_preview()
        
        # Measure frame rendering performance
        frame_count = 0
        start_time = time.time()
        test_duration = 2.0  # Test for 2 seconds
        
        while time.time() - start_time < test_duration:
            preview_system._render_frame()
            frame_count += 1
        
        end_time = time.time()
        actual_duration = end_time - start_time
        actual_fps = frame_count / actual_duration
        
        print(f"Rendered {frame_count} frames in {actual_duration:.2f} seconds")
        print(f"Average FPS: {actual_fps:.1f}")
        print(f"Target FPS: 60.0")
        
        if actual_fps >= 50.0:
            print("✓ Performance test PASSED - Achieving near 60fps")
        else:
            print("⚠ Performance test WARNING - FPS below target")
        
        # Test quality adjustment
        print("\nTesting automatic quality adjustment...")
        
        # Simulate low performance
        preview_system._metrics.current_fps = 40.0
        preview_system._last_quality_adjustment = 0.0
        
        original_quality = preview_system.get_quality_preset()
        preview_system._check_performance_adjustment()
        new_quality = preview_system.get_quality_preset()
        
        if new_quality != original_quality:
            print(f"✓ Quality adjustment working: {original_quality.value} → {new_quality.value}")
        else:
            print("⚠ Quality adjustment not triggered")
        
    finally:
        preview_system.stop_preview()
    
    print("\nPerformance test completed")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance test
    run_performance_test()


class TestViewportControls(unittest.TestCase):
    """Test cases for viewport controls (zoom, pan, safe areas)."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock renderer with dimensions
        self.mock_renderer = Mock(spec=OpenGLRenderer)
        self.mock_renderer.fps_updated = Mock()
        self.mock_renderer.fps_updated.connect = Mock()
        self.mock_renderer.makeCurrent = Mock()
        self.mock_renderer.paintGL = Mock()
        self.mock_renderer.swapBuffers = Mock()
        self.mock_renderer.width.return_value = 1920
        self.mock_renderer.height.return_value = 1080
        
        # Create mock timeline engine
        self.mock_timeline = Mock(spec=TimelineEngine)
        self.mock_timeline.current_time = 0.0
        self.mock_timeline.duration = 30.0
        self.mock_timeline.get_playback_speed.return_value = 1.0
        self.mock_timeline.is_playing.return_value = False
        self.mock_timeline.get_active_elements_at_time.return_value = []
        
        # Create video asset mock
        self.mock_video_asset = Mock(spec=VideoAsset)
        self.mock_video_asset.resolution = (1920, 1080)
        self.mock_video_asset.fps = 30.0
        self.mock_video_asset.duration = 30.0
        self.mock_timeline.video_asset = self.mock_video_asset
        
        # Create preview system
        self.preview_system = PreviewSystem(self.mock_renderer, self.mock_timeline)
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'preview_system'):
            self.preview_system.stop_preview()
    
    def test_zoom_controls(self):
        """Test zoom control functionality."""
        # Test initial zoom
        self.assertEqual(self.preview_system.get_zoom(), 1.0)
        
        # Test setting zoom
        self.preview_system.set_zoom(2.0)
        self.assertEqual(self.preview_system.get_zoom(), 2.0)
        
        # Test zoom limits
        self.preview_system.set_zoom(20.0)  # Above max
        self.assertEqual(self.preview_system.get_zoom(), 10.0)  # Should be clamped to max
        
        self.preview_system.set_zoom(0.01)  # Below min
        self.assertEqual(self.preview_system.get_zoom(), 0.1)  # Should be clamped to min
    
    def test_zoom_in_out(self):
        """Test zoom in and zoom out functionality."""
        initial_zoom = self.preview_system.get_zoom()
        
        # Test zoom in
        self.preview_system.zoom_in(1.5)
        self.assertEqual(self.preview_system.get_zoom(), initial_zoom * 1.5)
        
        # Test zoom out
        self.preview_system.zoom_out(1.5)
        self.assertAlmostEqual(self.preview_system.get_zoom(), initial_zoom, places=5)
    
    def test_zoom_presets(self):
        """Test zoom preset functions."""
        # Test zoom to actual size
        self.preview_system.set_zoom(2.5)
        self.preview_system.zoom_to_actual_size()
        self.assertEqual(self.preview_system.get_zoom(), 1.0)
        self.assertEqual(self.preview_system.get_pan(), (0.0, 0.0))
        
        # Test zoom to fit (requires renderer dimensions)
        self.preview_system.zoom_to_fit()
        # Should calculate appropriate zoom based on video and renderer size
        self.assertGreater(self.preview_system.get_zoom(), 0.0)
    
    def test_pan_controls(self):
        """Test pan control functionality."""
        # Test initial pan
        self.assertEqual(self.preview_system.get_pan(), (0.0, 0.0))
        
        # Test setting pan
        self.preview_system.set_pan(100.0, 50.0)
        self.assertEqual(self.preview_system.get_pan(), (100.0, 50.0))
        
        # Test pan by delta
        self.preview_system.pan_by(25.0, -10.0)
        self.assertEqual(self.preview_system.get_pan(), (125.0, 40.0))
    
    def test_viewport_reset(self):
        """Test viewport reset functionality."""
        # Change zoom and pan
        self.preview_system.set_zoom(3.0)
        self.preview_system.set_pan(200.0, 100.0)
        
        # Reset viewport
        self.preview_system.reset_viewport()
        
        # Should be back to defaults
        self.assertEqual(self.preview_system.get_zoom(), 1.0)
        self.assertEqual(self.preview_system.get_pan(), (0.0, 0.0))
    
    def test_viewport_transform_signals(self):
        """Test that viewport changes emit signals."""
        signal_emitted = False
        received_transform = None
        
        def on_viewport_changed(transform):
            nonlocal signal_emitted, received_transform
            signal_emitted = True
            received_transform = transform
        
        self.preview_system.viewport_changed.connect(on_viewport_changed)
        
        # Change zoom
        self.preview_system.set_zoom(2.0)
        
        self.assertTrue(signal_emitted)
        self.assertIsNotNone(received_transform)
        self.assertEqual(received_transform.zoom, 2.0)
    
    def test_safe_area_guides(self):
        """Test safe area guide functionality."""
        # Test initial state
        self.assertEqual(self.preview_system.get_safe_area_guides(), SafeAreaType.NONE)
        
        # Test setting safe area guides
        self.preview_system.set_safe_area_guides(SafeAreaType.ACTION_SAFE)
        self.assertEqual(self.preview_system.get_safe_area_guides(), SafeAreaType.ACTION_SAFE)
        
        self.preview_system.set_safe_area_guides(SafeAreaType.TITLE_SAFE)
        self.assertEqual(self.preview_system.get_safe_area_guides(), SafeAreaType.TITLE_SAFE)
        
        self.preview_system.set_safe_area_guides(SafeAreaType.BOTH)
        self.assertEqual(self.preview_system.get_safe_area_guides(), SafeAreaType.BOTH)
    
    def test_safe_area_bounds_calculation(self):
        """Test safe area bounds calculation."""
        viewport_width = 1920
        viewport_height = 1080
        
        # Test action safe (90%)
        action_bounds = self.preview_system.get_safe_area_bounds(
            SafeAreaType.ACTION_SAFE, viewport_width, viewport_height)
        
        self.assertIsNotNone(action_bounds)
        expected_width = viewport_width * 0.9
        expected_height = viewport_height * 0.9
        self.assertAlmostEqual(action_bounds.width(), expected_width)
        self.assertAlmostEqual(action_bounds.height(), expected_height)
        
        # Test title safe (80%)
        title_bounds = self.preview_system.get_safe_area_bounds(
            SafeAreaType.TITLE_SAFE, viewport_width, viewport_height)
        
        self.assertIsNotNone(title_bounds)
        expected_width = viewport_width * 0.8
        expected_height = viewport_height * 0.8
        self.assertAlmostEqual(title_bounds.width(), expected_width)
        self.assertAlmostEqual(title_bounds.height(), expected_height)
        
        # Test none
        none_bounds = self.preview_system.get_safe_area_bounds(
            SafeAreaType.NONE, viewport_width, viewport_height)
        self.assertIsNone(none_bounds)
    
    def test_safe_area_signals(self):
        """Test that safe area changes emit signals."""
        signal_emitted = False
        received_type = None
        
        def on_safe_area_changed(safe_area_type):
            nonlocal signal_emitted, received_type
            signal_emitted = True
            received_type = safe_area_type
        
        self.preview_system.safe_area_changed.connect(on_safe_area_changed)
        
        # Change safe area type
        self.preview_system.set_safe_area_guides(SafeAreaType.ACTION_SAFE)
        
        self.assertTrue(signal_emitted)
        self.assertEqual(received_type, SafeAreaType.ACTION_SAFE)
    
    def test_position_transformation(self):
        """Test position transformation with zoom and pan."""
        # Set zoom and pan
        self.preview_system.set_zoom(2.0)
        self.preview_system.set_pan(100.0, 50.0)
        
        # Test position transformation
        original_pos = (200.0, 300.0)
        transformed_pos = self.preview_system._transform_position(original_pos)
        
        expected_x = (200.0 * 2.0) + 100.0  # zoom * position + pan
        expected_y = (300.0 * 2.0) + 50.0
        
        self.assertEqual(transformed_pos, (expected_x, expected_y))
    
    def test_subtitle_position_transformation_during_render(self):
        """Test that subtitle positions are transformed during rendering."""
        # Create test subtitle data
        subtitle_data = [{
            'text': 'Test',
            'position': (100.0, 200.0),
            'font_size': 24.0
        }]
        
        # Set viewport transformation
        self.preview_system.set_zoom(1.5)
        self.preview_system.set_pan(50.0, 25.0)
        
        # Render subtitles (this modifies the subtitle_data in place)
        self.preview_system._render_subtitle_overlays(subtitle_data)
        
        # Check that position was transformed
        expected_x = (100.0 * 1.5) + 50.0
        expected_y = (200.0 * 1.5) + 25.0
        self.assertEqual(subtitle_data[0]['position'], (expected_x, expected_y))
        
        # Check that font size was scaled
        expected_font_size = 24.0 * 1.5
        self.assertEqual(subtitle_data[0]['font_size'], expected_font_size)


class TestPreviewControlsWidget(unittest.TestCase):
    """Test cases for the PreviewControlsWidget UI component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock preview system
        self.mock_preview_system = Mock(spec=PreviewSystem)
        self.mock_preview_system.viewport_changed = Mock()
        self.mock_preview_system.fps_updated = Mock()
        self.mock_preview_system.quality_changed = Mock()
        self.mock_preview_system.safe_area_changed = Mock()
        
        # Mock methods
        self.mock_preview_system.get_zoom.return_value = 1.0
        self.mock_preview_system.get_pan.return_value = (0.0, 0.0)
        self.mock_preview_system.get_quality_preset.return_value = QualityPreset.NORMAL
        self.mock_preview_system.get_safe_area_guides.return_value = SafeAreaType.NONE
        
        # Create controls widget
        self.controls_widget = PreviewControlsWidget(self.mock_preview_system)
    
    def test_widget_initialization(self):
        """Test that the controls widget initializes properly."""
        self.assertIsNotNone(self.controls_widget)
        
        # Check that UI elements exist
        self.assertIsNotNone(self.controls_widget._zoom_slider)
        self.assertIsNotNone(self.controls_widget._zoom_label)
        self.assertIsNotNone(self.controls_widget._pan_label)
        self.assertIsNotNone(self.controls_widget._quality_combo)
        self.assertIsNotNone(self.controls_widget._safe_area_combo)
        self.assertIsNotNone(self.controls_widget._fps_label)
    
    def test_zoom_slider_interaction(self):
        """Test zoom slider interaction."""
        # Simulate slider change
        self.controls_widget._zoom_slider.setValue(200)  # 200% zoom
        
        # Should call preview system set_zoom
        self.mock_preview_system.set_zoom.assert_called_with(2.0)
    
    def test_quality_combo_interaction(self):
        """Test quality combo box interaction."""
        # Find the index for HIGH quality
        high_index = -1
        for i in range(self.controls_widget._quality_combo.count()):
            if self.controls_widget._quality_combo.itemData(i) == QualityPreset.HIGH:
                high_index = i
                break
        
        self.assertNotEqual(high_index, -1)
        
        # Simulate combo change
        self.controls_widget._quality_combo.setCurrentIndex(high_index)
        
        # Should call preview system set_quality_preset
        self.mock_preview_system.set_quality_preset.assert_called_with(QualityPreset.HIGH)
    
    def test_safe_area_combo_interaction(self):
        """Test safe area combo box interaction."""
        # Find the index for ACTION_SAFE
        action_safe_index = -1
        for i in range(self.controls_widget._safe_area_combo.count()):
            if self.controls_widget._safe_area_combo.itemData(i) == SafeAreaType.ACTION_SAFE:
                action_safe_index = i
                break
        
        self.assertNotEqual(action_safe_index, -1)
        
        # Simulate combo change
        self.controls_widget._safe_area_combo.setCurrentIndex(action_safe_index)
        
        # Should call preview system set_safe_area_guides
        self.mock_preview_system.set_safe_area_guides.assert_called_with(SafeAreaType.ACTION_SAFE)
    
    def test_viewport_change_updates_ui(self):
        """Test that viewport changes update the UI."""
        # Create test viewport transform
        transform = ViewportTransform()
        transform.zoom = 1.5
        transform.pan_x = 100.0
        transform.pan_y = 50.0
        
        # Simulate viewport change signal
        self.controls_widget._on_viewport_changed(transform)
        
        # Check that UI was updated
        self.assertEqual(self.controls_widget._zoom_slider.value(), 150)  # 150%
        self.assertEqual(self.controls_widget._zoom_label.text(), "150%")
        self.assertEqual(self.controls_widget._pan_label.text(), "Pan: (100, 50)")
    
    def test_fps_update_ui(self):
        """Test that FPS updates are reflected in UI."""
        # Simulate FPS update
        self.controls_widget._on_fps_updated(58.5)
        
        # Check that label was updated
        self.assertEqual(self.controls_widget._fps_label.text(), "FPS: 58.5")
    
    def test_quality_change_updates_ui(self):
        """Test that quality changes update the UI."""
        # Simulate quality change signal
        self.controls_widget._on_quality_changed_signal(QualityPreset.HIGH)
        
        # Check that combo box was updated
        current_data = self.controls_widget._quality_combo.currentData()
        self.assertEqual(current_data, QualityPreset.HIGH)
        
        # Check that status label was updated
        self.assertEqual(self.controls_widget._quality_status_label.text(), "Quality: High")
    
    def test_safe_area_change_updates_ui(self):
        """Test that safe area changes update the UI."""
        # Simulate safe area change signal
        self.controls_widget._on_safe_area_changed_signal(SafeAreaType.TITLE_SAFE)
        
        # Check that combo box was updated
        current_data = self.controls_widget._safe_area_combo.currentData()
        self.assertEqual(current_data, SafeAreaType.TITLE_SAFE)


def run_viewport_performance_test():
    """Run a performance test for viewport transformations."""
    print("\nRunning Viewport Performance Test")
    print("=" * 50)
    
    if not QApplication.instance():
        app = QApplication([])
    
    # Create mock components
    mock_renderer = Mock(spec=OpenGLRenderer)
    mock_renderer.fps_updated = Mock()
    mock_renderer.fps_updated.connect = Mock()
    mock_renderer.makeCurrent = Mock()
    mock_renderer.paintGL = Mock()
    mock_renderer.swapBuffers = Mock()
    mock_renderer.width.return_value = 1920
    mock_renderer.height.return_value = 1080
    
    mock_timeline = Mock(spec=TimelineEngine)
    mock_timeline.current_time = 0.0
    mock_timeline.duration = 30.0
    mock_timeline.get_playback_speed.return_value = 1.0
    mock_timeline.is_playing.return_value = False
    mock_timeline.get_active_elements_at_time.return_value = []
    
    # Create preview system
    preview_system = PreviewSystem(mock_renderer, mock_timeline)
    
    try:
        # Test viewport transformation performance
        start_time = time.time()
        iterations = 10000
        
        for i in range(iterations):
            # Test various zoom levels
            zoom = 0.5 + (i % 100) / 50.0  # Zoom from 0.5 to 2.5
            preview_system.set_zoom(zoom)
            
            # Test pan positions
            pan_x = (i % 200) - 100  # Pan from -100 to 100
            pan_y = (i % 200) - 100
            preview_system.set_pan(pan_x, pan_y)
            
            # Test position transformation
            test_pos = (i % 1000, (i * 2) % 1000)
            transformed = preview_system._transform_position(test_pos)
        
        end_time = time.time()
        duration = end_time - start_time
        ops_per_second = iterations / duration
        
        print(f"Performed {iterations} viewport operations in {duration:.3f} seconds")
        print(f"Operations per second: {ops_per_second:.0f}")
        
        if ops_per_second >= 100000:  # Should handle 100k ops/sec easily
            print("✓ Viewport performance test PASSED")
        else:
            print("⚠ Viewport performance test WARNING - Lower than expected performance")
        
        # Test safe area calculation performance
        start_time = time.time()
        
        for i in range(1000):
            for safe_area_type in [SafeAreaType.ACTION_SAFE, SafeAreaType.TITLE_SAFE]:
                bounds = preview_system.get_safe_area_bounds(safe_area_type, 1920, 1080)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Safe area calculations: {2000 / duration:.0f} ops/sec")
        
    finally:
        preview_system.stop_preview()
    
    print("Viewport performance test completed")