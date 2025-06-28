"""
GPU acceleration manager using CuPy with automatic fallback to CPU.
Provides a unified interface for GPU/CPU processing.
"""

import numpy as np
from typing import Optional, Callable, Any, Dict
import logging
import functools

logger = logging.getLogger(__name__)

# Try to import CuPy
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    cp = None
    CUPY_AVAILABLE = False
    logger.warning("CuPy not available. GPU acceleration disabled.")

# Try to import cv2 with CUDA support
try:
    import cv2
    # Check if OpenCV was built with CUDA
    CV2_CUDA_AVAILABLE = cv2.cuda.getCudaEnabledDeviceCount() > 0
except:
    CV2_CUDA_AVAILABLE = False


class GPUManager:
    """
    Manages GPU acceleration with automatic CPU fallback.
    Provides unified interface for array operations.
    """
    
    def __init__(self, force_cpu: bool = False):
        """
        Initialize GPU manager.
        
        Args:
            force_cpu: Force CPU usage even if GPU is available
        """
        self.force_cpu = force_cpu
        self._gpu_available = False
        self._gpu_memory_limit = None
        self._device_info = {}
        
        if not force_cpu and CUPY_AVAILABLE:
            self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU and get device information."""
        try:
            # Test GPU availability
            test_array = cp.array([1, 2, 3])
            _ = test_array * 2
            
            self._gpu_available = True
            
            # Get device info
            device = cp.cuda.Device()
            self._device_info = {
                'name': device.name.decode('utf-8') if hasattr(device.name, 'decode') else str(device.name),
                'compute_capability': device.compute_capability,
                'memory_total': device.mem_info[1],
                'memory_free': device.mem_info[0]
            }
            
            # Set memory limit to 80% of available
            self._gpu_memory_limit = int(self._device_info['memory_total'] * 0.8)
            cp.cuda.MemoryPool().set_limit(self._gpu_memory_limit)
            
            logger.info(f"GPU initialized: {self._device_info['name']}")
            logger.info(f"GPU memory: {self._device_info['memory_free'] / 1e9:.2f}GB free")
            
        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}")
            self._gpu_available = False
    
    @property
    def is_gpu_available(self) -> bool:
        """Check if GPU is available for processing."""
        return self._gpu_available and not self.force_cpu
    
    @property
    def xp(self):
        """Get the array module (cupy or numpy)."""
        return cp if self.is_gpu_available else np
    
    def asarray(self, array: np.ndarray, dtype: Optional[np.dtype] = None) -> Any:
        """
        Convert numpy array to GPU array if available.
        
        Args:
            array: Input numpy array
            dtype: Optional data type
            
        Returns:
            GPU array if available, otherwise numpy array
        """
        if self.is_gpu_available:
            try:
                return cp.asarray(array, dtype=dtype)
            except cp.cuda.memory.OutOfMemoryError:
                logger.warning("GPU out of memory, falling back to CPU")
                self._gpu_available = False
                return array if dtype is None else array.astype(dtype)
        return array if dtype is None else array.astype(dtype)
    
    def asnumpy(self, array: Any) -> np.ndarray:
        """
        Convert GPU array to numpy array.
        
        Args:
            array: GPU or numpy array
            
        Returns:
            Numpy array
        """
        if self.is_gpu_available and hasattr(array, 'get'):
            return array.get()
        return array
    
    def gpu_accelerated(self, func: Callable) -> Callable:
        """
        Decorator to automatically handle GPU/CPU arrays.
        
        Usage:
            @gpu_manager.gpu_accelerated
            def process_image(image):
                # Use self.xp instead of np
                return self.xp.multiply(image, 2)
        """
        @functools.wraps(func)
        def wrapper(self, image: np.ndarray, *args, **kwargs):
            # Convert to GPU if available
            gpu_image = self.asarray(image)
            
            # Process
            result = func(self, gpu_image, *args, **kwargs)
            
            # Convert back to numpy
            return self.asnumpy(result)
        
        return wrapper
    
    def check_memory_available(self, required_bytes: int) -> bool:
        """
        Check if enough GPU memory is available.
        
        Args:
            required_bytes: Required memory in bytes
            
        Returns:
            True if memory available
        """
        if not self.is_gpu_available:
            return True  # CPU always assumed to have memory
        
        try:
            mempool = cp.get_default_memory_pool()
            free_memory = self._device_info['memory_total'] - mempool.used_bytes()
            return free_memory >= required_bytes
        except:
            return False
    
    def clear_memory(self):
        """Clear GPU memory cache."""
        if self.is_gpu_available:
            try:
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
            except:
                pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get GPU information."""
        if not self.is_gpu_available:
            return {
                'available': False,
                'reason': 'GPU not available or disabled'
            }
        
        return {
            'available': True,
            'device': self._device_info,
            'cupy_version': cp.__version__ if cp else None,
            'cuda_available': CUPY_AVAILABLE,
            'opencv_cuda': CV2_CUDA_AVAILABLE
        }
    
    # Convenience methods for common operations
    def convolve2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """2D convolution with GPU acceleration."""
        if self.is_gpu_available:
            from cupyx.scipy import ndimage
            gpu_image = self.asarray(image)
            gpu_kernel = self.asarray(kernel)
            result = ndimage.convolve(gpu_image, gpu_kernel)
            return self.asnumpy(result)
        else:
            from scipy import ndimage
            return ndimage.convolve(image, kernel)
    
    def gaussian_blur(self, image: np.ndarray, sigma: float) -> np.ndarray:
        """Gaussian blur with GPU acceleration."""
        if self.is_gpu_available and CV2_CUDA_AVAILABLE:
            # Use OpenCV CUDA
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(image)
            
            # Create Gaussian filter
            ksize = int(6 * sigma + 1)
            if ksize % 2 == 0:
                ksize += 1
            
            gpu_result = cv2.cuda.bilateralFilter(gpu_image, -1, sigma, sigma)
            result = gpu_result.download()
            return result
        else:
            # CPU fallback
            return cv2.GaussianBlur(image, (0, 0), sigma)
    
    def resize(self, image: np.ndarray, size: tuple, 
              interpolation: int = cv2.INTER_LINEAR) -> np.ndarray:
        """Resize image with GPU acceleration."""
        if self.is_gpu_available and CV2_CUDA_AVAILABLE:
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(image)
            gpu_result = cv2.cuda.resize(gpu_image, size, interpolation=interpolation)
            return gpu_result.download()
        else:
            return cv2.resize(image, size, interpolation=interpolation)


# Global GPU manager instance
_gpu_manager = None

def get_gpu_manager(force_cpu: bool = False) -> GPUManager:
    """
    Get global GPU manager instance.
    
    Args:
        force_cpu: Force CPU usage
        
    Returns:
        GPU manager instance
    """
    global _gpu_manager
    if _gpu_manager is None or _gpu_manager.force_cpu != force_cpu:
        _gpu_manager = GPUManager(force_cpu)
    return _gpu_manager