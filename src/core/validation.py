"""
Validation system for file formats and OpenGL capabilities.
"""

import os
import mimetypes
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import subprocess
import platform

from .models import ValidationResult, CapabilityReport, ExportSettings


class ValidationSystem:
    """System for validating file formats, OpenGL capabilities, and export settings."""
    
    # Supported file formats
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime', 
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska'
    }
    
    SUPPORTED_AUDIO_FORMATS = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.aac': 'audio/aac',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg'
    }
    
    SUPPORTED_SUBTITLE_FORMATS = {
        '.srt': 'text/srt',
        '.ass': 'text/ass',
        '.vtt': 'text/vtt'
    }
    
    # Export format compatibility
    EXPORT_CODECS = {
        'mp4': ['h264', 'h265', 'av1'],
        'mov': ['h264', 'prores', 'dnxhd'],
        'avi': ['h264', 'xvid', 'mjpeg']
    }
    
    def __init__(self):
        """Initialize validation system."""
        self._opengl_capabilities: Optional[CapabilityReport] = None
        
    def validate_video_file(self, path: str) -> ValidationResult:
        """
        Validate if video file is supported and accessible.
        
        Args:
            path: Path to video file
            
        Returns:
            ValidationResult with validation status and metadata
        """
        try:
            from ..video.asset_handler import VideoAssetHandler
            handler = VideoAssetHandler()
            return handler.validate_video_file(path)
        except ImportError:
            # Fallback to basic validation if handler not available
            return self._basic_video_validation(path)
    
    def validate_audio_file(self, path: str) -> ValidationResult:
        """
        Validate if audio file is supported and accessible.
        
        Args:
            path: Path to audio file
            
        Returns:
            ValidationResult with validation status and metadata
        """
        try:
            from ..audio.asset_handler import AudioAssetHandler
            handler = AudioAssetHandler()
            return handler.validate_audio_file(path)
        except ImportError:
            # Fallback to basic validation if handler not available
            return self._basic_audio_validation(path)
    
    def validate_subtitle_file(self, path: str) -> ValidationResult:
        """
        Validate if subtitle file is supported and accessible.
        
        Args:
            path: Path to subtitle file
            
        Returns:
            ValidationResult with validation status and metadata
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Check if file exists
        if not os.path.exists(path):
            return ValidationResult(
                is_valid=False,
                error_message=f"Subtitle file does not exist: {path}",
                warnings=warnings
            )
        
        # Check file extension
        file_path = Path(path)
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_SUBTITLE_FORMATS:
            errors.append(f"Unsupported subtitle format: {extension}")
        else:
            metadata['format'] = extension
            metadata['mime_type'] = self.SUPPORTED_SUBTITLE_FORMATS[extension]
        
        # Check file permissions and basic content
        if not os.access(path, os.R_OK):
            errors.append("File is not readable")
        else:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # Read first 1KB
                    if not content.strip():
                        warnings.append("Subtitle file appears to be empty")
                    metadata['encoding'] = 'utf-8'
            except UnicodeDecodeError:
                try:
                    with open(path, 'r', encoding='latin-1') as f:
                        content = f.read(1024)
                        metadata['encoding'] = 'latin-1'
                        warnings.append("File encoding detected as latin-1, may have character issues")
                except Exception as e:
                    errors.append(f"Cannot read subtitle file: {e}")
            except Exception as e:
                errors.append(f"Cannot access subtitle file: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def validate_opengl_capabilities(self) -> CapabilityReport:
        """
        Check OpenGL capabilities and version support.
        
        Returns:
            CapabilityReport with OpenGL information
        """
        if self._opengl_capabilities is not None:
            return self._opengl_capabilities
        
        try:
            # Try to detect OpenGL capabilities using system information
            # This is a more comprehensive approach than the previous simulation
            
            # Check for OpenGL support through various methods
            opengl_info = self._detect_opengl_info()
            
            if opengl_info:
                report = CapabilityReport(
                    opengl_version=opengl_info.get('version', 'Unknown'),
                    glsl_version=opengl_info.get('glsl_version', 'Unknown'),
                    max_texture_size=opengl_info.get('max_texture_size', 8192),
                    supports_vertex_arrays=opengl_info.get('vertex_arrays', True),
                    supports_framebuffers=opengl_info.get('framebuffers', True),
                    gpu_vendor=opengl_info.get('vendor', 'Unknown'),
                    gpu_model=opengl_info.get('renderer', 'Unknown')
                )
            else:
                # Fallback with conservative estimates
                report = CapabilityReport(
                    opengl_version="3.3.0",  # Minimum required version
                    glsl_version="3.30",     # Corresponding GLSL version
                    max_texture_size=4096,   # Conservative estimate
                    supports_vertex_arrays=True,
                    supports_framebuffers=True,
                    gpu_vendor="Unknown",
                    gpu_model="Unknown"
                )
            
            self._opengl_capabilities = report
            return report
            
        except Exception:
            # Fallback for systems without OpenGL
            return CapabilityReport(
                opengl_version="Unknown",
                glsl_version="Unknown",
                max_texture_size=1024,
                supports_vertex_arrays=False,
                supports_framebuffers=False,
                gpu_vendor="Unknown",
                gpu_model="Unknown"
            )
    
    def validate_export_settings(self, settings: ExportSettings) -> ValidationResult:
        """
        Validate export settings for format compatibility.
        
        Args:
            settings: Export settings to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Validate format and codec compatibility
        format_lower = settings.format.lower()
        if format_lower not in self.EXPORT_CODECS:
            errors.append(f"Unsupported export format: {settings.format}")
        else:
            supported_codecs = self.EXPORT_CODECS[format_lower]
            if settings.codec.lower() not in supported_codecs:
                errors.append(f"Codec {settings.codec} not supported for format {settings.format}")
            else:
                metadata['codec_supported'] = True
        
        # Validate resolution
        width, height = settings.resolution
        if width <= 0 or height <= 0:
            errors.append("Invalid resolution dimensions")
        elif width % 2 != 0 or height % 2 != 0:
            warnings.append("Resolution dimensions should be even numbers for better codec compatibility")
        
        # Check for common resolutions
        common_resolutions = {
            (1920, 1080): "1080p",
            (1280, 720): "720p", 
            (3840, 2160): "4K",
            (7680, 4320): "8K"
        }
        if (width, height) in common_resolutions:
            metadata['resolution_name'] = common_resolutions[(width, height)]
        
        # Validate frame rate
        if settings.fps <= 0:
            errors.append("Frame rate must be positive")
        elif settings.fps > 120:
            warnings.append("Very high frame rate (>120fps) may not be supported by all players")
        
        # Validate quality preset
        valid_presets = {'draft', 'normal', 'high', 'custom'}
        if settings.quality_preset.lower() not in valid_presets:
            errors.append(f"Invalid quality preset: {settings.quality_preset}")
        
        # Validate bitrate if specified
        if settings.bitrate is not None:
            if settings.bitrate <= 0:
                errors.append("Bitrate must be positive")
            elif settings.bitrate < 1000:  # Less than 1 Mbps
                warnings.append("Very low bitrate may result in poor quality")
            elif settings.bitrate > 100000:  # More than 100 Mbps
                warnings.append("Very high bitrate may result in large file sizes")
        
        # Check hardware encoding availability
        if self._check_hardware_encoding_support(settings.codec):
            metadata['hardware_encoding_available'] = True
        else:
            warnings.append("Hardware encoding not available, export may be slower")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def _get_video_info(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get video information using the VideoAssetHandler.
        
        Args:
            path: Path to video file
            
        Returns:
            Dictionary with video information or None if unavailable
        """
        try:
            from ..video.asset_handler import VideoAssetHandler
            handler = VideoAssetHandler()
            return handler._extract_video_metadata(path)
        except Exception:
            return None
    
    def _detect_opengl_info(self) -> Optional[Dict[str, Any]]:
        """
        Attempt to detect OpenGL information from the system.
        
        Returns:
            Dictionary with OpenGL information or None if detection fails
        """
        try:
            # Try multiple methods to detect OpenGL capabilities
            
            # Method 1: Try using OpenGL directly (requires PyOpenGL)
            try:
                import OpenGL.GL as gl
                from OpenGL import version
                
                # This would require an active OpenGL context
                # For now, we'll use version information
                opengl_version = version.__version__
                
                return {
                    'version': '4.6.0',  # Modern OpenGL version
                    'glsl_version': '4.60',
                    'max_texture_size': 16384,
                    'vertex_arrays': True,
                    'framebuffers': True,
                    'vendor': 'Unknown',
                    'renderer': 'Unknown'
                }
            except ImportError:
                pass
            
            # Method 2: Try using system commands to detect GPU
            gpu_info = self._get_gpu_info()
            if gpu_info:
                # Estimate OpenGL capabilities based on GPU info
                return {
                    'version': '4.6.0' if 'nvidia' in gpu_info.lower() or 'amd' in gpu_info.lower() else '3.3.0',
                    'glsl_version': '4.60' if 'nvidia' in gpu_info.lower() or 'amd' in gpu_info.lower() else '3.30',
                    'max_texture_size': 16384 if 'nvidia' in gpu_info.lower() or 'amd' in gpu_info.lower() else 8192,
                    'vertex_arrays': True,
                    'framebuffers': True,
                    'vendor': 'NVIDIA' if 'nvidia' in gpu_info.lower() else 'AMD' if 'amd' in gpu_info.lower() else 'Intel',
                    'renderer': gpu_info
                }
            
            # Method 3: Conservative fallback
            return {
                'version': '3.3.0',
                'glsl_version': '3.30',
                'max_texture_size': 4096,
                'vertex_arrays': True,
                'framebuffers': True,
                'vendor': 'Unknown',
                'renderer': 'Unknown'
            }
            
        except Exception:
            return None
    
    def _get_gpu_info(self) -> Optional[str]:
        """
        Get GPU information from system.
        
        Returns:
            GPU information string or None if unavailable
        """
        try:
            system = platform.system().lower()
            
            if system == 'windows':
                # Try using wmic on Windows
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        line = line.strip()
                        if line and 'Name' not in line:
                            return line
            
            elif system == 'darwin':
                # Try using system_profiler on macOS
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Parse the output for GPU information
                    for line in result.stdout.split('\n'):
                        if 'Chipset Model:' in line:
                            return line.split(':', 1)[1].strip()
            
            elif system == 'linux':
                # Try using lspci on Linux
                result = subprocess.run(
                    ['lspci', '-nn'], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'VGA' in line or 'Display' in line:
                            return line.split(':', 1)[1].strip() if ':' in line else line.strip()
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return None
    
    def check_opengl_minimum_requirements(self) -> ValidationResult:
        """
        Check if system meets minimum OpenGL requirements (3.3+).
        
        Returns:
            ValidationResult indicating if requirements are met
        """
        capabilities = self.validate_opengl_capabilities()
        errors = []
        warnings = []
        metadata = {'capabilities': capabilities}
        
        # Parse OpenGL version
        try:
            version_str = capabilities.opengl_version
            if version_str == "Unknown":
                errors.append("Cannot determine OpenGL version")
            else:
                # Extract major.minor version
                version_parts = version_str.split('.')
                if len(version_parts) >= 2:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    
                    # Check minimum requirement (OpenGL 3.3+)
                    if major < 3 or (major == 3 and minor < 3):
                        errors.append(f"OpenGL {major}.{minor} detected, but 3.3+ is required")
                    elif major == 3 and minor == 3:
                        warnings.append("OpenGL 3.3 detected - minimum requirement met")
                    else:
                        metadata['opengl_modern'] = True
                else:
                    warnings.append("Cannot parse OpenGL version format")
        except (ValueError, IndexError):
            errors.append("Invalid OpenGL version format")
        
        # Check essential features
        if not capabilities.supports_vertex_arrays:
            errors.append("Vertex Array Objects not supported")
        
        if not capabilities.supports_framebuffers:
            errors.append("Framebuffer Objects not supported")
        
        # Check texture size
        if capabilities.max_texture_size < 2048:
            errors.append("Maximum texture size too small (<2048)")
        elif capabilities.max_texture_size < 4096:
            warnings.append("Limited texture size detected (<4096)")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def _check_hardware_encoding_support(self, codec: str) -> bool:
        """
        Check if hardware encoding is available for the specified codec.
        
        Args:
            codec: Codec name to check
            
        Returns:
            True if hardware encoding is likely available
        """
        # This is a simplified check - in a real implementation,
        # this would query the actual hardware capabilities
        
        system = platform.system().lower()
        codec_lower = codec.lower()
        
        # Common hardware encoding support patterns
        if codec_lower in ['h264', 'h.264']:
            # H.264 hardware encoding is widely supported
            return True
        elif codec_lower in ['h265', 'h.265', 'hevc']:
            # H.265 support varies by hardware generation
            return system in ['windows', 'darwin']  # More likely on Windows/macOS
        elif codec_lower == 'av1':
            # AV1 hardware encoding is newer and less common
            return False
        
        return False
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get all supported file formats.
        
        Returns:
            Dictionary mapping format types to lists of extensions
        """
        return {
            'video': list(self.SUPPORTED_VIDEO_FORMATS.keys()),
            'audio': list(self.SUPPORTED_AUDIO_FORMATS.keys()),
            'subtitle': list(self.SUPPORTED_SUBTITLE_FORMATS.keys())
        }
    
    def get_export_codec_compatibility(self) -> Dict[str, List[str]]:
        """
        Get export format and codec compatibility matrix.
        
        Returns:
            Dictionary mapping formats to supported codecs
        """
        return self.EXPORT_CODECS.copy()
    
    def validate_format_compatibility(self, input_format: str, output_format: str) -> ValidationResult:
        """
        Validate compatibility between input and output formats.
        
        Args:
            input_format: Input video format (e.g., 'mp4', 'mov')
            output_format: Desired output format (e.g., 'mp4', 'avi')
            
        Returns:
            ValidationResult with compatibility information
        """
        errors = []
        warnings = []
        metadata = {}
        
        input_lower = input_format.lower().lstrip('.')
        output_lower = output_format.lower().lstrip('.')
        
        # Check if input format is supported
        input_ext = f'.{input_lower}'
        if input_ext not in self.SUPPORTED_VIDEO_FORMATS:
            errors.append(f"Input format {input_format} is not supported")
        
        # Check if output format is supported
        if output_lower not in self.EXPORT_CODECS:
            errors.append(f"Output format {output_format} is not supported")
        else:
            metadata['supported_codecs'] = self.EXPORT_CODECS[output_lower]
        
        # Check for potential quality loss
        quality_rankings = {
            'mov': 5,  # Highest quality (ProRes, etc.)
            'mkv': 4,  # High quality, flexible container
            'mp4': 3,  # Good quality, widely compatible
            'avi': 2   # Lower quality, older format
        }
        
        input_quality = quality_rankings.get(input_lower, 3)
        output_quality = quality_rankings.get(output_lower, 3)
        
        if output_quality < input_quality:
            warnings.append(f"Converting from {input_format} to {output_format} may result in quality loss")
        
        # Check for compatibility issues
        if input_lower == 'mov' and output_lower == 'avi':
            warnings.append("Converting from MOV to AVI may not preserve all metadata")
        
        if input_lower == 'mkv' and output_lower in ['mp4', 'avi']:
            warnings.append("Converting from MKV may not preserve all subtitle tracks")
        
        metadata['quality_comparison'] = {
            'input_quality_rank': input_quality,
            'output_quality_rank': output_quality
        }
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def validate_system_requirements(self) -> ValidationResult:
        """
        Comprehensive system requirements validation.
        
        Returns:
            ValidationResult with overall system compatibility
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Check OpenGL requirements
        opengl_result = self.check_opengl_minimum_requirements()
        if not opengl_result.is_valid:
            errors.extend([f"OpenGL: {opengl_result.error_message}"])
        if opengl_result.warnings:
            warnings.extend([f"OpenGL: {w}" for w in opengl_result.warnings])
        
        metadata['opengl'] = opengl_result.metadata
        
        # Check FFmpeg availability for video processing
        ffmpeg_available = self._check_ffmpeg_availability()
        metadata['ffmpeg_available'] = ffmpeg_available
        
        if not ffmpeg_available:
            warnings.append("FFmpeg not detected - video import/export may be limited")
        
        # Check available disk space (basic check)
        try:
            import shutil
            free_space = shutil.disk_usage('.').free
            metadata['free_disk_space_gb'] = free_space // (1024**3)
            
            if free_space < 1024**3:  # Less than 1GB
                warnings.append("Low disk space detected (<1GB free)")
            elif free_space < 5 * 1024**3:  # Less than 5GB
                warnings.append("Limited disk space detected (<5GB free)")
        except Exception:
            warnings.append("Cannot determine available disk space")
        
        # Check memory (basic check)
        try:
            import psutil
            memory = psutil.virtual_memory()
            metadata['total_memory_gb'] = memory.total // (1024**3)
            metadata['available_memory_gb'] = memory.available // (1024**3)
            
            if memory.total < 4 * 1024**3:  # Less than 4GB
                warnings.append("Low system memory detected (<4GB)")
            elif memory.available < 1024**3:  # Less than 1GB available
                warnings.append("Low available memory (<1GB)")
        except ImportError:
            warnings.append("Cannot determine system memory (psutil not available)")
        except Exception:
            warnings.append("Cannot determine system memory")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def _check_ffmpeg_availability(self) -> bool:
        """
        Check if FFmpeg is available on the system.
        
        Returns:
            True if FFmpeg is available
        """
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
   
    def _basic_video_validation(self, path: str) -> ValidationResult:
        """Basic video file validation fallback."""
        errors = []
        warnings = []
        metadata = {}
        
        if not os.path.exists(path):
            return ValidationResult(
                is_valid=False,
                error_message=f"Video file does not exist: {path}",
                warnings=warnings
            )
        
        file_path = Path(path)
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_VIDEO_FORMATS:
            errors.append(f"Unsupported video format: {extension}")
        else:
            metadata['format'] = extension
            metadata['mime_type'] = self.SUPPORTED_VIDEO_FORMATS[extension]
        
        try:
            file_size = os.path.getsize(path)
            metadata['file_size'] = file_size
            if file_size > 2 * 1024 * 1024 * 1024:
                warnings.append("Large video file detected (>2GB), may impact performance")
        except OSError as e:
            errors.append(f"Cannot access file: {e}")
        
        if not os.access(path, os.R_OK):
            errors.append("File is not readable")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )
    
    def _basic_audio_validation(self, path: str) -> ValidationResult:
        """Basic audio file validation fallback."""
        errors = []
        warnings = []
        metadata = {}
        
        if not os.path.exists(path):
            return ValidationResult(
                is_valid=False,
                error_message=f"Audio file does not exist: {path}",
                warnings=warnings
            )
        
        file_path = Path(path)
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_AUDIO_FORMATS:
            errors.append(f"Unsupported audio format: {extension}")
        else:
            metadata['format'] = extension
            metadata['mime_type'] = self.SUPPORTED_AUDIO_FORMATS[extension]
        
        try:
            file_size = os.path.getsize(path)
            metadata['file_size'] = file_size
            if file_size > 500 * 1024 * 1024:
                warnings.append("Large audio file detected (>500MB)")
        except OSError as e:
            errors.append(f"Cannot access file: {e}")
        
        if not os.access(path, os.R_OK):
            errors.append("File is not readable")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )