from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class BaseProcessor(ABC):
    """Base class for all image processors"""
    
    @abstractmethod
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory requirements in bytes for processing an image"""
        pass
    
    @abstractmethod
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Process a preview version of the image (must complete in <100ms)"""
        pass
    
    @abstractmethod
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Process the full resolution image"""
        pass