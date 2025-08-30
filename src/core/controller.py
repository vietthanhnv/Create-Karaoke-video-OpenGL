"""
Application controller and coordination logic.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .interfaces import (
    IProjectManager, ITimelineEngine, IEffectSystem, 
    IRenderEngine, IValidationSystem, Project
)
from .project_manager import ProjectManager
from .validation import ValidationSystem


class IApplicationController(ABC):
    """Interface for the main application controller."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the application and all subsystems."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the application and cleanup resources."""
        pass
    
    @abstractmethod
    def get_project_manager(self) -> IProjectManager:
        """Get the project manager instance."""
        pass
    
    @abstractmethod
    def get_timeline_engine(self) -> ITimelineEngine:
        """Get the timeline engine instance."""
        pass
    
    @abstractmethod
    def get_effect_system(self) -> IEffectSystem:
        """Get the effect system instance."""
        pass
    
    @abstractmethod
    def get_render_engine(self) -> IRenderEngine:
        """Get the render engine instance."""
        pass
    
    @abstractmethod
    def get_validation_system(self) -> IValidationSystem:
        """Get the validation system instance."""
        pass
    
    @abstractmethod
    def get_current_project(self) -> Optional[Project]:
        """Get the currently loaded project."""
        pass
    
    @abstractmethod
    def set_current_project(self, project: Project) -> None:
        """Set the current project."""
        pass


class ApplicationController(IApplicationController):
    """Concrete implementation of the application controller."""
    
    def __init__(self):
        self._project_manager: Optional[IProjectManager] = None
        self._timeline_engine: Optional[ITimelineEngine] = None
        self._effect_system: Optional[IEffectSystem] = None
        self._render_engine: Optional[IRenderEngine] = None
        self._validation_system: Optional[IValidationSystem] = None
        self._current_project: Optional[Project] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the application and all subsystems."""
        if self._initialized:
            return True
        
        try:
            # Initialize validation system first
            self._validation_system = ValidationSystem()
            
            # Initialize project manager with validation system
            self._project_manager = ProjectManager(self._validation_system)
            
            # Other subsystems will be initialized in later tasks
            # self._timeline_engine = TimelineEngine()
            # self._effect_system = EffectSystem()
            # self._render_engine = RenderEngine()
            
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize application: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the application and cleanup resources."""
        if self._render_engine:
            # Cleanup OpenGL resources
            pass
        
        self._initialized = False
    
    def get_project_manager(self) -> IProjectManager:
        """Get the project manager instance."""
        if not self._project_manager:
            raise RuntimeError("Project manager not initialized")
        return self._project_manager
    
    def get_timeline_engine(self) -> ITimelineEngine:
        """Get the timeline engine instance."""
        if not self._timeline_engine:
            raise RuntimeError("Timeline engine not initialized")
        return self._timeline_engine
    
    def get_effect_system(self) -> IEffectSystem:
        """Get the effect system instance."""
        if not self._effect_system:
            raise RuntimeError("Effect system not initialized")
        return self._effect_system
    
    def get_render_engine(self) -> IRenderEngine:
        """Get the render engine instance."""
        if not self._render_engine:
            raise RuntimeError("Render engine not initialized")
        return self._render_engine
    
    def get_validation_system(self) -> IValidationSystem:
        """Get the validation system instance."""
        if not self._validation_system:
            raise RuntimeError("Validation system not initialized")
        return self._validation_system
    
    def get_current_project(self) -> Optional[Project]:
        """Get the currently loaded project."""
        return self._current_project
    
    def set_current_project(self, project: Project) -> None:
        """Set the current project."""
        self._current_project = project