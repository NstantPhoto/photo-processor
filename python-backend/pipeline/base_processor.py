from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
import numpy as np
import time
from dataclasses import dataclass
from .memory_manager import MemoryManager


@dataclass
class ProcessingResult:
    """Result of image processing operation"""
    image: np.ndarray
    processing_time: float
    metadata: Dict[str, Any]
    preview: Optional[np.ndarray] = None


class BaseProcessor(ABC):
    """
    Base class for all image processors.
    Implements memory estimation and processing methods as per CLAUDE.md requirements.
    """
    
    def __init__(self, name: str, processor_type: str):
        self.name = name
        self.processor_type = processor_type
        self.enabled = True
        self.parameters = {}
        self._preview_max_dimension = 800
        self.memory_manager = MemoryManager()
        self.supports_tiled_processing = True
    
    @abstractmethod
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """
        Estimate memory usage in bytes for processing the given image shape.
        
        Args:
            image_shape: (height, width, channels) of the image
            
        Returns:
            Estimated memory usage in bytes
        """
        pass
    
    @abstractmethod
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """
        Process a preview version of the image. Must complete in <100ms.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Processed preview image
        """
        pass
    
    @abstractmethod
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """
        Process the full resolution image. Must handle up to 100MP images.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Processed full resolution image
        """
        pass
    
    def process_chunk(self, chunk: np.ndarray) -> np.ndarray:
        """
        Process a single chunk of an image. Override for tiled processing.
        Default implementation calls process_full.
        
        Args:
            chunk: Image chunk as numpy array
            
        Returns:
            Processed chunk
        """
        return self.process_full(chunk)
    
    def process(self, image: np.ndarray, preview_only: bool = False) -> ProcessingResult:
        """
        Main processing method that handles both preview and full processing.
        
        Args:
            image: Input image as numpy array
            preview_only: If True, only process preview
            
        Returns:
            ProcessingResult with processed image and metadata
        """
        start_time = time.time()
        
        if preview_only:
            processed_image = self.process_preview(image)
            preview = processed_image
        else:
            # Generate preview first
            preview = self._generate_preview(image)
            preview = self.process_preview(preview)
            
            # Process full image with tiled processing if needed
            if self.supports_tiled_processing and not self.memory_manager.can_process_in_memory(image.shape):
                processed_image = self.memory_manager.process_large_image(
                    image,
                    self.process_chunk,
                    parallel=True
                )
            else:
                processed_image = self.process_full(image)
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            image=processed_image,
            processing_time=processing_time,
            metadata={
                'processor': self.name,
                'type': self.processor_type,
                'parameters': self.parameters.copy(),
                'input_shape': image.shape,
                'output_shape': processed_image.shape
            },
            preview=preview
        )
    
    def _generate_preview(self, image: np.ndarray) -> np.ndarray:
        """Generate a preview image by resizing if necessary."""
        height, width = image.shape[:2]
        
        if max(height, width) <= self._preview_max_dimension:
            return image.copy()
        
        # Calculate scaling factor
        scale = self._preview_max_dimension / max(height, width)
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        # Use OpenCV for fast resizing
        import cv2
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    def set_parameters(self, **kwargs):
        """Set processor parameters."""
        self.parameters.update(kwargs)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current processor parameters."""
        return self.parameters.copy()
    
    def validate_input(self, image: np.ndarray) -> bool:
        """
        Validate input image.
        
        Args:
            image: Input image
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(image, np.ndarray):
            return False
        
        if len(image.shape) not in [2, 3]:
            return False
        
        if image.size == 0:
            return False
        
        return True
    
    def get_memory_factor(self) -> float:
        """
        Get memory multiplication factor for this processor.
        Override in subclasses for processors that need more memory.
        
        Returns:
            Memory factor (1.0 = normal, >1.0 = needs more memory)
        """
        return 1.0
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.processor_type}')"