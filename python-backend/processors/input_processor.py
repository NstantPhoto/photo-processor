import numpy as np
from typing import Tuple
from pipeline.base_processor import BaseProcessor


class InputProcessor(BaseProcessor):
    """
    Input node for the pipeline. Simply passes through the image.
    """
    
    def __init__(self):
        super().__init__(name="Input", processor_type="input")
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Input node doesn't require additional memory"""
        return 0
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Pass through for preview"""
        return image
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Pass through for full processing"""
        return image


class OutputProcessor(BaseProcessor):
    """
    Output node for the pipeline. Simply passes through the image.
    """
    
    def __init__(self):
        super().__init__(name="Output", processor_type="output")
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Output node doesn't require additional memory"""
        return 0
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Pass through for preview"""
        return image
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Pass through for full processing"""
        return image