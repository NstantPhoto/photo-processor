import numpy as np
import cv2
from typing import Tuple
from pipeline.base_processor import BaseProcessor


class ColorBalanceProcessor(BaseProcessor):
    """
    Adjusts color balance for temperature and tint corrections.
    Supports automatic white balance detection.
    """
    
    def __init__(self):
        super().__init__(name="Color Balance", processor_type="color_balance")
        self.parameters = {
            'temperature': 0,  # -100 (cool/blue) to +100 (warm/yellow)
            'tint': 0,  # -100 (green) to +100 (magenta)
            'auto_mode': True,
            'strength': 1.0,  # 0.0 to 1.0
            'preserve_skin_tones': True
        }
    
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int:
        """Estimate memory usage for color balance processing."""
        height, width, channels = image_shape
        # Need memory for: input + output + float conversion + masks
        return height * width * channels * 4 * 2
    
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        """Fast preview processing."""
        return self._adjust_color_balance(image, fast_mode=True)
    
    def process_full(self, image: np.ndarray) -> np.ndarray:
        """Full quality processing."""
        return self._adjust_color_balance(image, fast_mode=False)
    
    def _adjust_color_balance(self, image: np.ndarray, fast_mode: bool = False) -> np.ndarray:
        """Core color balance adjustment logic."""
        if self.parameters['auto_mode']:
            # Calculate automatic white balance
            temp_adjustment, tint_adjustment = self._calculate_auto_white_balance(image, fast_mode)
        else:
            temp_adjustment = self.parameters['temperature']
            tint_adjustment = self.parameters['tint']
        
        if temp_adjustment == 0 and tint_adjustment == 0:
            return image
        
        # Convert to float for processing
        img_float = image.astype(np.float32) / 255.0
        
        # Apply temperature adjustment
        if temp_adjustment != 0:
            img_float = self._apply_temperature(img_float, temp_adjustment)
        
        # Apply tint adjustment
        if tint_adjustment != 0:
            img_float = self._apply_tint(img_float, tint_adjustment)
        
        # Preserve skin tones if requested
        if self.parameters['preserve_skin_tones'] and not fast_mode:
            skin_mask = self._detect_skin_tones(image)
            if skin_mask is not None:
                # Blend original and adjusted in skin areas
                original_float = image.astype(np.float32) / 255.0
                skin_mask_3ch = np.stack([skin_mask] * 3, axis=-1)
                img_float = np.where(skin_mask_3ch, 
                                   original_float * 0.5 + img_float * 0.5,
                                   img_float)
        
        # Apply strength parameter
        if self.parameters['strength'] < 1.0:
            original_float = image.astype(np.float32) / 255.0
            img_float = original_float * (1 - self.parameters['strength']) + \
                       img_float * self.parameters['strength']
        
        # Convert back to uint8
        result = np.clip(img_float * 255, 0, 255).astype(np.uint8)
        return result
    
    def _apply_temperature(self, img_float: np.ndarray, temperature: float) -> np.ndarray:
        """Apply color temperature adjustment."""
        # Temperature affects blue-yellow axis
        # Positive = warmer (more yellow), Negative = cooler (more blue)
        
        # Convert temperature to color shift
        temp_factor = temperature / 100.0
        
        if temp_factor > 0:
            # Warming: decrease blue, increase red slightly
            img_float[:, :, 0] *= (1 - temp_factor * 0.1)  # Blue channel
            img_float[:, :, 2] *= (1 + temp_factor * 0.05)  # Red channel
        else:
            # Cooling: increase blue, decrease red slightly
            img_float[:, :, 0] *= (1 - temp_factor * 0.15)  # Blue channel
            img_float[:, :, 2] *= (1 + temp_factor * 0.05)  # Red channel
        
        return img_float
    
    def _apply_tint(self, img_float: np.ndarray, tint: float) -> np.ndarray:
        """Apply tint adjustment."""
        # Tint affects green-magenta axis
        # Positive = more magenta, Negative = more green
        
        # Convert tint to color shift
        tint_factor = tint / 100.0
        
        if tint_factor > 0:
            # More magenta: decrease green
            img_float[:, :, 1] *= (1 - tint_factor * 0.1)  # Green channel
        else:
            # More green: increase green
            img_float[:, :, 1] *= (1 - tint_factor * 0.1)  # Green channel
        
        return img_float
    
    def _calculate_auto_white_balance(self, image: np.ndarray, fast_mode: bool) -> Tuple[float, float]:
        """Calculate automatic white balance corrections."""
        # Use gray world assumption for auto white balance
        b, g, r = cv2.split(image)
        
        # Calculate average values
        avg_b = np.mean(b)
        avg_g = np.mean(g)
        avg_r = np.mean(r)
        
        # Target gray value
        avg_gray = (avg_b + avg_g + avg_r) / 3
        
        # Calculate scaling factors
        scale_b = avg_gray / (avg_b + 1e-6)
        scale_g = avg_gray / (avg_g + 1e-6)
        scale_r = avg_gray / (avg_r + 1e-6)
        
        # Convert to temperature and tint adjustments
        # Temperature: blue-yellow axis
        temp_adjustment = (scale_b - scale_r) * 50
        temp_adjustment = np.clip(temp_adjustment, -100, 100)
        
        # Tint: green-magenta axis
        tint_adjustment = (scale_g - 1.0) * 50
        tint_adjustment = np.clip(tint_adjustment, -100, 100)
        
        return temp_adjustment, tint_adjustment
    
    def _detect_skin_tones(self, image: np.ndarray) -> np.ndarray:
        """Detect skin tone regions in the image."""
        # Convert to YCrCb color space
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        
        # Define skin color range in YCrCb
        lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        
        # Create skin mask
        skin_mask = cv2.inRange(ycrcb, lower_skin, upper_skin)
        
        # Clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
        
        # Blur for smooth blending
        skin_mask = cv2.GaussianBlur(skin_mask, (21, 21), 0)
        
        # Normalize to 0-1 range
        skin_mask = skin_mask.astype(np.float32) / 255.0
        
        return skin_mask