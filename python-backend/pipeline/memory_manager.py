import psutil
import numpy as np
from typing import Tuple, List, Generator, Optional, Callable, Any
from dataclasses import dataclass
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class MemoryStatus:
    """Current memory status"""
    total_mb: float
    available_mb: float
    used_mb: float
    percent_used: float
    can_process_image: bool
    recommended_chunk_size: int


@dataclass
class ImageChunk:
    """Represents a chunk of an image for tiled processing"""
    data: np.ndarray
    y_start: int
    y_end: int
    x_start: int
    x_end: int
    overlap_top: int
    overlap_bottom: int
    overlap_left: int
    overlap_right: int


class MemoryManager:
    """
    Manages memory usage for image processing operations.
    Implements dynamic chunk sizing as per CLAUDE.md requirements.
    """
    
    def __init__(self, max_memory_percent: float = 80.0):
        """
        Initialize memory manager.
        
        Args:
            max_memory_percent: Maximum percentage of system memory to use
        """
        self.max_memory_percent = max_memory_percent
        self.base_chunk_size = 2048  # 2K tiles as per CLAUDE.md
        self.chunk_overlap = 128  # For seamless processing
        self.min_chunk_size = 512
        self.max_chunk_size = 4096
        
    def get_memory_status(self) -> MemoryStatus:
        """Get current system memory status."""
        memory = psutil.virtual_memory()
        
        total_mb = memory.total / (1024 * 1024)
        available_mb = memory.available / (1024 * 1024)
        used_mb = memory.used / (1024 * 1024)
        percent_used = memory.percent
        
        # Check if we can process at least a small image
        min_required_mb = 100  # Minimum 100MB for processing
        can_process = available_mb > min_required_mb
        
        # Calculate recommended chunk size based on available memory
        # As per CLAUDE.md: chunk_size = min(2048, sqrt(available_memory_mb * 1024 * 1024 / 16))
        recommended_chunk = min(
            self.base_chunk_size,
            int(math.sqrt(available_mb * 1024 * 1024 / 16))
        )
        recommended_chunk = max(self.min_chunk_size, recommended_chunk)
        
        return MemoryStatus(
            total_mb=total_mb,
            available_mb=available_mb,
            used_mb=used_mb,
            percent_used=percent_used,
            can_process_image=can_process,
            recommended_chunk_size=recommended_chunk
        )
    
    def estimate_image_memory(self, shape: Tuple[int, int, int], 
                             dtype: np.dtype = np.uint8) -> int:
        """
        Estimate memory required for an image.
        
        Args:
            shape: (height, width, channels)
            dtype: Data type of the image
            
        Returns:
            Estimated memory in bytes
        """
        height, width, channels = shape
        bytes_per_pixel = np.dtype(dtype).itemsize
        
        # Base image size
        image_size = height * width * channels * bytes_per_pixel
        
        # Add overhead for processing (typically need 2-3x for intermediate results)
        overhead_factor = 2.5
        
        return int(image_size * overhead_factor)
    
    def can_process_in_memory(self, shape: Tuple[int, int, int], 
                             dtype: np.dtype = np.uint8) -> bool:
        """
        Check if an image can be processed in memory without chunking.
        
        Args:
            shape: (height, width, channels)
            dtype: Data type of the image
            
        Returns:
            True if image can be processed in memory
        """
        required_memory = self.estimate_image_memory(shape, dtype)
        status = self.get_memory_status()
        
        # Convert to MB for comparison
        required_mb = required_memory / (1024 * 1024)
        
        # Check if we have enough memory with safety margin
        available_for_processing = status.available_mb * (self.max_memory_percent / 100)
        
        return required_mb < available_for_processing
    
    def calculate_chunks(self, image_shape: Tuple[int, int, int], 
                        chunk_size: Optional[int] = None) -> List[Tuple[int, int, int, int]]:
        """
        Calculate chunk boundaries for tiled processing.
        
        Args:
            image_shape: (height, width, channels)
            chunk_size: Optional custom chunk size
            
        Returns:
            List of (y_start, y_end, x_start, x_end) tuples
        """
        height, width, _ = image_shape
        
        if chunk_size is None:
            status = self.get_memory_status()
            chunk_size = status.recommended_chunk_size
        
        chunks = []
        
        # Calculate number of chunks needed
        y_chunks = max(1, math.ceil(height / (chunk_size - self.chunk_overlap)))
        x_chunks = max(1, math.ceil(width / (chunk_size - self.chunk_overlap)))
        
        for y_idx in range(y_chunks):
            for x_idx in range(x_chunks):
                # Calculate chunk boundaries
                y_start = y_idx * (chunk_size - self.chunk_overlap)
                y_end = min(y_start + chunk_size, height)
                
                x_start = x_idx * (chunk_size - self.chunk_overlap)
                x_end = min(x_start + chunk_size, width)
                
                # Adjust last chunks to ensure full coverage
                if y_idx == y_chunks - 1:
                    y_end = height
                if x_idx == x_chunks - 1:
                    x_end = width
                
                chunks.append((y_start, y_end, x_start, x_end))
        
        return chunks
    
    def process_in_chunks(self, image: np.ndarray, 
                         chunk_size: Optional[int] = None) -> Generator[ImageChunk, None, None]:
        """
        Generator that yields image chunks for processing.
        
        Args:
            image: Input image
            chunk_size: Optional custom chunk size
            
        Yields:
            ImageChunk objects
        """
        chunks = self.calculate_chunks(image.shape, chunk_size)
        
        for y_start, y_end, x_start, x_end in chunks:
            # Extract chunk with overlap information
            chunk_data = image[y_start:y_end, x_start:x_end]
            
            # Calculate overlap amounts
            overlap_top = self.chunk_overlap if y_start > 0 else 0
            overlap_bottom = self.chunk_overlap if y_end < image.shape[0] else 0
            overlap_left = self.chunk_overlap if x_start > 0 else 0
            overlap_right = self.chunk_overlap if x_end < image.shape[1] else 0
            
            yield ImageChunk(
                data=chunk_data,
                y_start=y_start,
                y_end=y_end,
                x_start=x_start,
                x_end=x_end,
                overlap_top=overlap_top,
                overlap_bottom=overlap_bottom,
                overlap_left=overlap_left,
                overlap_right=overlap_right
            )
    
    def merge_chunks(self, chunks: List[Tuple[ImageChunk, np.ndarray]], 
                    output_shape: Tuple[int, int, int]) -> np.ndarray:
        """
        Merge processed chunks back into a single image.
        
        Args:
            chunks: List of (chunk_info, processed_data) tuples
            output_shape: Shape of the output image
            
        Returns:
            Merged image
        """
        output = np.zeros(output_shape, dtype=chunks[0][1].dtype)
        
        for chunk_info, processed_data in chunks:
            # Calculate the region to copy (excluding overlaps for interior chunks)
            y_start = chunk_info.y_start + chunk_info.overlap_top
            y_end = chunk_info.y_end - chunk_info.overlap_bottom
            x_start = chunk_info.x_start + chunk_info.overlap_left
            x_end = chunk_info.x_end - chunk_info.overlap_right
            
            # Copy the processed data
            data_y_start = chunk_info.overlap_top
            data_y_end = processed_data.shape[0] - chunk_info.overlap_bottom
            data_x_start = chunk_info.overlap_left
            data_x_end = processed_data.shape[1] - chunk_info.overlap_right
            
            output[y_start:y_end, x_start:x_end] = processed_data[
                data_y_start:data_y_end,
                data_x_start:data_x_end
            ]
        
        return output
    
    def cleanup(self):
        """Force garbage collection to free memory."""
        import gc
        gc.collect()
    
    def get_optimal_batch_size(self, image_shape: Tuple[int, int, int], 
                              total_images: int) -> int:
        """
        Calculate optimal batch size for processing multiple images.
        
        Args:
            image_shape: Shape of a single image
            total_images: Total number of images to process
            
        Returns:
            Optimal batch size
        """
        status = self.get_memory_status()
        single_image_memory = self.estimate_image_memory(image_shape)
        
        # Calculate how many images can fit in available memory
        available_for_processing = status.available_mb * (self.max_memory_percent / 100) * 1024 * 1024
        max_batch_size = int(available_for_processing / single_image_memory)
        
        # Limit batch size to reasonable values
        max_batch_size = max(1, min(max_batch_size, 16))
        
        return min(max_batch_size, total_images)
    
    def process_large_image(self, image: np.ndarray, 
                           processor_func: Callable[[np.ndarray], np.ndarray],
                           parallel: bool = True,
                           max_workers: Optional[int] = None) -> np.ndarray:
        """
        Process a large image using tiled processing with optional parallelization.
        
        Args:
            image: Input image
            processor_func: Function to process each chunk
            parallel: Whether to process chunks in parallel
            max_workers: Maximum number of parallel workers
            
        Returns:
            Processed image
        """
        # Check if we can process in memory
        if self.can_process_in_memory(image.shape):
            return processor_func(image)
        
        # Process in chunks
        chunks_to_process = list(self.process_in_chunks(image))
        processed_chunks = []
        
        if parallel and len(chunks_to_process) > 1:
            # Parallel processing
            if max_workers is None:
                max_workers = min(4, len(chunks_to_process))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all chunks for processing
                future_to_chunk = {
                    executor.submit(processor_func, chunk.data): chunk
                    for chunk in chunks_to_process
                }
                
                # Collect results in order
                for future in as_completed(future_to_chunk):
                    chunk_info = future_to_chunk[future]
                    try:
                        processed_data = future.result()
                        processed_chunks.append((chunk_info, processed_data))
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        # Use original data on error
                        processed_chunks.append((chunk_info, chunk_info.data))
        else:
            # Sequential processing
            for chunk in chunks_to_process:
                try:
                    processed_data = processor_func(chunk.data)
                    processed_chunks.append((chunk, processed_data))
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    processed_chunks.append((chunk, chunk.data))
        
        # Sort chunks by position to ensure correct order
        processed_chunks.sort(key=lambda x: (x[0].y_start, x[0].x_start))
        
        # Merge processed chunks
        return self.merge_chunks(processed_chunks, image.shape)
    
    def apply_blend_mask(self, chunk: ImageChunk, processed_data: np.ndarray) -> np.ndarray:
        """
        Apply blending mask to chunk overlaps for seamless merging.
        
        Args:
            chunk: Original chunk information
            processed_data: Processed chunk data
            
        Returns:
            Chunk with blended edges
        """
        h, w = processed_data.shape[:2]
        result = processed_data.copy()
        
        # Create blend masks for each edge
        if chunk.overlap_top > 0:
            # Top edge blend
            blend_zone = min(chunk.overlap_top, h // 4)
            alpha = np.linspace(0, 1, blend_zone).reshape(-1, 1)
            if len(result.shape) == 3:
                alpha = np.repeat(alpha[:, :, np.newaxis], result.shape[2], axis=2)
            result[:blend_zone] = result[:blend_zone] * alpha
        
        if chunk.overlap_bottom > 0:
            # Bottom edge blend
            blend_zone = min(chunk.overlap_bottom, h // 4)
            alpha = np.linspace(1, 0, blend_zone).reshape(-1, 1)
            if len(result.shape) == 3:
                alpha = np.repeat(alpha[:, :, np.newaxis], result.shape[2], axis=2)
            result[-blend_zone:] = result[-blend_zone:] * alpha
        
        if chunk.overlap_left > 0:
            # Left edge blend
            blend_zone = min(chunk.overlap_left, w // 4)
            alpha = np.linspace(0, 1, blend_zone).reshape(1, -1)
            if len(result.shape) == 3:
                alpha = np.repeat(alpha[:, :, np.newaxis], result.shape[2], axis=2)
            result[:, :blend_zone] = result[:, :blend_zone] * alpha
        
        if chunk.overlap_right > 0:
            # Right edge blend
            blend_zone = min(chunk.overlap_right, w // 4)
            alpha = np.linspace(1, 0, blend_zone).reshape(1, -1)
            if len(result.shape) == 3:
                alpha = np.repeat(alpha[:, :, np.newaxis], result.shape[2], axis=2)
            result[:, -blend_zone:] = result[:, -blend_zone:] * alpha
        
        return result
    
    def adaptive_chunk_size(self, image_shape: Tuple[int, int, int],
                           processor_memory_factor: float = 1.0) -> int:
        """
        Calculate adaptive chunk size based on image and processor requirements.
        
        Args:
            image_shape: Shape of the image
            processor_memory_factor: Memory multiplier for specific processor
            
        Returns:
            Optimal chunk size
        """
        status = self.get_memory_status()
        base_chunk = status.recommended_chunk_size
        
        # Adjust based on image dimensions
        height, width, _ = image_shape
        
        # For very wide or tall images, adjust chunk aspect ratio
        aspect_ratio = width / height
        if aspect_ratio > 2:  # Wide image
            # Use wider chunks
            chunk_size = int(base_chunk * math.sqrt(aspect_ratio))
        elif aspect_ratio < 0.5:  # Tall image
            # Use taller chunks
            chunk_size = int(base_chunk / math.sqrt(1 / aspect_ratio))
        else:
            chunk_size = base_chunk
        
        # Apply processor memory factor
        chunk_size = int(chunk_size / math.sqrt(processor_memory_factor))
        
        # Ensure within bounds
        chunk_size = max(self.min_chunk_size, min(chunk_size, self.max_chunk_size))
        
        return chunk_size