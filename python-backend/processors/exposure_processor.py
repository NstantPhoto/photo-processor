import numpy as np
import cv2
from typing import Tuple
from pipeline.base_processor import BaseProcessor


class ExposureProcessor(BaseProcessor):
    """
    Adjusts image exposure using gamma correction and brightness scaling.
    Supports both automatic and manual modes.
    """
    
    def __init__(self):
        super().__init__(name="Exposure", processor_type="exposure")
        self.parameters = {
            'exposure_value': 0.0,  # -2.0 to +2.0 EV
            'auto_mode': True,
            'preserve_highlights': True,
            'preserve_shadows': True
        }
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory usage for exposure processing."""
        height, width, channels = image_shape
        # Need memory for: input + output + histogram + LUT
        base_memory = height * width * channels * 4  # float32 processing
        histogram_memory = 256 * channels * 4  # histogram per channel
        lut_memory = 256 * channels  # lookup table
        
        return int(base_memory * 2 + histogram_memory + lut_memory)
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Fast preview processing."""
        return self._process_exposure(image, fast_mode=True)
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Full quality processing."""
        return self._process_exposure(image, fast_mode=False)
    
    def _process_exposure(self, image: np.ndarray, fast_mode: bool = False) -> np.ndarray:
        """Core exposure adjustment logic."""
        # Convert to float for processing
        img_float = image.astype(np.float32) / 255.0
        
        if self.parameters['auto_mode']:
            # Calculate optimal exposure adjustment
            exposure_value = self._calculate_auto_exposure(img_float)
        else:
            exposure_value = self.parameters['exposure_value']
        
        # Apply exposure adjustment
        if exposure_value != 0:
            # Convert EV to gamma value
            # EV = log2(new_exposure / old_exposure)
            # gamma = 2^(-EV)
            gamma = np.power(2, -exposure_value)
            
            # Apply gamma correction
            adjusted = np.power(img_float, gamma)
            
            # Preserve highlights and shadows if requested
            if self.parameters['preserve_highlights']:
                # Blend with original in highlight areas
                highlight_mask = img_float > 0.9
                adjusted = np.where(highlight_mask, 
                                  img_float * 0.3 + adjusted * 0.7, 
                                  adjusted)
            
            if self.parameters['preserve_shadows']:
                # Blend with original in shadow areas
                shadow_mask = img_float < 0.1
                adjusted = np.where(shadow_mask,
                                  img_float * 0.3 + adjusted * 0.7,
                                  adjusted)
            
            # Ensure values are in valid range
            adjusted = np.clip(adjusted, 0, 1)
        else:
            adjusted = img_float
        
        # Convert back to uint8
        return (adjusted * 255).astype(np.uint8)
    
    def _calculate_auto_exposure(self, img_float: np.ndarray) -> float:
        """Calculate automatic exposure adjustment."""
        # Calculate image histogram
        gray = cv2.cvtColor((img_float * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        
        # Normalize histogram
        hist = hist / hist.sum()
        
        # Calculate cumulative distribution
        cdf = hist.cumsum()
        
        # Find median brightness
        median_idx = np.where(cdf >= 0.5)[0][0]
        median_brightness = median_idx / 255.0
        
        # Target brightness (18% gray card standard)
        target_brightness = 0.5
        
        # Calculate exposure adjustment
        # Limit adjustment to reasonable range
        if median_brightness > 0.01:  # Avoid division by zero
            ratio = target_brightness / median_brightness
            exposure_value = -np.log2(ratio)
            exposure_value = np.clip(exposure_value, -2.0, 2.0)
        else:
            exposure_value = 2.0  # Maximum brightening for very dark images
        
        return exposure_value