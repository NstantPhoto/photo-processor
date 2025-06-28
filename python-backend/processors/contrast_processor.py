import numpy as np
import cv2
from typing import Tuple
from pipeline.base_processor import BaseProcessor


class ContrastProcessor(BaseProcessor):
    """
    Adjusts image contrast using various algorithms.
    Supports CLAHE (Contrast Limited Adaptive Histogram Equalization) for advanced processing.
    """
    
    def __init__(self):
        super().__init__(name="Contrast", processor_type="contrast")
        self.parameters = {
            'contrast': 0,  # -100 to +100
            'auto_mode': False,
            'algorithm': 'linear',  # 'linear', 'sigmoid', 'clahe'
            'preserve_blacks': True,
            'preserve_whites': True
        }
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory usage for contrast processing."""
        height, width, channels = image_shape
        # Need memory for: input + output + histogram + temporary arrays
        if self.parameters['algorithm'] == 'clahe':
            # CLAHE needs more memory for tile processing
            return height * width * channels * 4 * 3
        else:
            return height * width * channels * 4 * 2
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Fast preview processing."""
        # Use simpler algorithm for preview
        if self.parameters['algorithm'] == 'clahe':
            # Use linear for preview as CLAHE is slow
            original_algo = self.parameters['algorithm']
            self.parameters['algorithm'] = 'linear'
            result = self._adjust_contrast(image)
            self.parameters['algorithm'] = original_algo
            return result
        return self._adjust_contrast(image)
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Full quality processing."""
        return self._adjust_contrast(image)
    
    def _adjust_contrast(self, image: np.ndarray) -> np.ndarray:
        """Core contrast adjustment logic."""
        if self.parameters['auto_mode']:
            contrast = self._calculate_auto_contrast(image)
        else:
            contrast = self.parameters['contrast']
        
        if contrast == 0 and self.parameters['algorithm'] != 'clahe':
            return image
        
        algorithm = self.parameters['algorithm']
        
        if algorithm == 'linear':
            return self._linear_contrast(image, contrast)
        elif algorithm == 'sigmoid':
            return self._sigmoid_contrast(image, contrast)
        elif algorithm == 'clahe':
            return self._clahe_contrast(image, contrast)
        else:
            return image
    
    def _linear_contrast(self, image: np.ndarray, contrast: float) -> np.ndarray:
        """Apply linear contrast adjustment."""
        # Convert contrast value to factor
        # -100 to +100 maps to 0.0 to 2.0
        if contrast >= 0:
            factor = 1.0 + (contrast / 100.0)
        else:
            factor = 1.0 + (contrast / 100.0)
        
        # Convert to float
        img_float = image.astype(np.float32)
        
        # Apply contrast around middle gray
        result = (img_float - 128) * factor + 128
        
        # Preserve blacks and whites if requested
        if self.parameters['preserve_blacks']:
            # Keep dark areas dark
            dark_mask = image < 20
            result = np.where(dark_mask, img_float, result)
        
        if self.parameters['preserve_whites']:
            # Keep bright areas bright
            bright_mask = image > 235
            result = np.where(bright_mask, img_float, result)
        
        # Clip and convert back
        result = np.clip(result, 0, 255).astype(np.uint8)
        return result
    
    def _sigmoid_contrast(self, image: np.ndarray, contrast: float) -> np.ndarray:
        """Apply sigmoid (S-curve) contrast adjustment."""
        # Convert to float and normalize
        img_float = image.astype(np.float32) / 255.0
        
        # Calculate sigmoid parameters
        # Contrast controls the steepness of the curve
        gain = 1.0 + abs(contrast) / 20.0
        
        if contrast > 0:
            # Increase contrast
            # Apply sigmoid function
            result = 1.0 / (1.0 + np.exp(-gain * (img_float - 0.5) * 12))
        else:
            # Decrease contrast
            # Inverse sigmoid for reducing contrast
            result = img_float * (1 - abs(contrast) / 100.0) + 0.5 * (abs(contrast) / 100.0)
        
        # Convert back to uint8
        result = (result * 255).astype(np.uint8)
        return result
    
    def _clahe_contrast(self, image: np.ndarray, contrast: float) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        # Map contrast parameter to clipLimit (1.0 to 10.0)
        clip_limit = 1.0 + (abs(contrast) / 100.0) * 9.0
        
        if contrast != 0:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            
            # Blend based on contrast value
            if contrast > 0:
                # Positive contrast: use CLAHE result
                blend_factor = contrast / 100.0
            else:
                # Negative contrast: reduce effect
                blend_factor = -contrast / 100.0
                l_clahe = l  # Use original for negative contrast
            
            # Blend original and processed
            l_result = cv2.addWeighted(l, 1 - blend_factor, l_clahe, blend_factor, 0)
        else:
            l_result = l
        
        # Merge channels and convert back
        lab_result = cv2.merge([l_result, a, b])
        result = cv2.cvtColor(lab_result, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _calculate_auto_contrast(self, image: np.ndarray) -> float:
        """Calculate automatic contrast adjustment."""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        
        # Calculate standard deviation as measure of contrast
        std_dev = np.std(gray)
        
        # Target standard deviation for good contrast
        target_std = 50.0
        
        # Calculate adjustment needed
        if std_dev < target_std:
            # Increase contrast
            contrast = min(100, (target_std - std_dev) * 2)
        else:
            # Decrease contrast if too high
            contrast = max(-100, (target_std - std_dev))
        
        return contrast