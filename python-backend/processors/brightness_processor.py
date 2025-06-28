import numpy as np
import cv2
from typing import Tuple
from pipeline.base_processor import BaseProcessor


class BrightnessProcessor(BaseProcessor):
    """
    Adjusts image brightness using linear scaling.
    Faster than exposure adjustment but less sophisticated.
    """
    
    def __init__(self):
        super().__init__(name="Brightness", processor_type="brightness")
        self.parameters = {
            'brightness': 0,  # -100 to +100
            'auto_mode': False,
            'preserve_contrast': True
        }
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory usage for brightness processing."""
        height, width, channels = image_shape
        # Need memory for: input + output + temporary float conversion
        return height * width * channels * 3
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Fast preview processing."""
        return self._adjust_brightness(image)
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Full quality processing."""
        return self._adjust_brightness(image)
    
    def _adjust_brightness(self, image: np.ndarray) -> np.ndarray:
        """Core brightness adjustment logic."""
        brightness = self.parameters['brightness']
        
        if self.parameters['auto_mode']:
            # Calculate optimal brightness adjustment
            brightness = self._calculate_auto_brightness(image)
        
        if brightness == 0:
            return image
        
        # Convert brightness value to scaling factor
        # -100 to +100 maps to 0.0 to 2.0
        if brightness > 0:
            factor = 1.0 + (brightness / 100.0)
        else:
            factor = 1.0 + (brightness / 100.0)
        
        if self.parameters['preserve_contrast']:
            # Use more sophisticated adjustment that preserves contrast
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Adjust only the L channel
            l_float = l.astype(np.float32)
            
            if brightness > 0:
                # Brighten: scale up with soft clipping
                l_adjusted = l_float * factor
                # Soft clip using tanh-like function
                l_adjusted = 255 * np.tanh(l_adjusted / 255)
            else:
                # Darken: scale down
                l_adjusted = l_float * factor
            
            l_adjusted = np.clip(l_adjusted, 0, 255).astype(np.uint8)
            
            # Merge channels and convert back
            lab_adjusted = cv2.merge([l_adjusted, a, b])
            result = cv2.cvtColor(lab_adjusted, cv2.COLOR_LAB2BGR)
        else:
            # Simple linear adjustment
            if brightness > 0:
                result = cv2.add(image, int(brightness * 2.55))
            else:
                result = cv2.subtract(image, int(-brightness * 2.55))
        
        return result
    
    def _calculate_auto_brightness(self, image: np.ndarray) -> float:
        """Calculate automatic brightness adjustment."""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate mean brightness
        mean_brightness = np.mean(gray)
        
        # Target brightness (middle gray)
        target_brightness = 128
        
        # Calculate adjustment needed
        difference = target_brightness - mean_brightness
        
        # Convert to -100 to +100 scale
        brightness_adjustment = (difference / 128) * 100
        
        # Limit adjustment range
        brightness_adjustment = np.clip(brightness_adjustment, -100, 100)
        
        return brightness_adjustment