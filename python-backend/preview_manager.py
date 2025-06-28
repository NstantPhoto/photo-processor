"""
Preview generation and caching system for fast image previews
"""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
from pydantic import BaseModel

class PreviewRequest(BaseModel):
    """Request model for preview generation"""
    image_path: str
    width: int = 800
    height: int = 600
    quality: int = 85
    format: str = "jpeg"

class PreviewResponse(BaseModel):
    """Response model for preview generation"""
    preview_path: str
    width: int
    height: int
    generation_time: float
    cached: bool

class PreviewManager:
    """Manages preview generation and caching"""
    
    def __init__(self, cache_dir: Path = Path("./preview_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cache_index: Dict[str, Dict[str, Any]] = {}
        self._load_cache_index()
    
    def _load_cache_index(self):
        """Load cache index from disk"""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            import json
            try:
                with open(index_file, 'r') as f:
                    self._cache_index = json.load(f)
            except:
                self._cache_index = {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        import json
        index_file = self.cache_dir / "cache_index.json"
        with open(index_file, 'w') as f:
            json.dump(self._cache_index, f)
    
    def _get_cache_key(self, image_path: str, width: int, height: int) -> str:
        """Generate cache key for preview"""
        path = Path(image_path)
        stat = path.stat()
        
        # Include file mtime and size in hash for cache invalidation
        cache_data = f"{image_path}_{width}_{height}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str, format: str) -> Path:
        """Get cache file path for key"""
        return self.cache_dir / f"{cache_key}.{format}"
    
    def _resize_image(self, image: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
        """Resize image maintaining aspect ratio"""
        h, w = image.shape[:2]
        
        # Calculate scaling factor
        scale = min(target_width / w, target_height / h)
        
        # Only downscale, never upscale
        if scale < 1.0:
            new_width = int(w * scale)
            new_height = int(h * scale)
            
            # Use INTER_AREA for downscaling (best quality)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image
    
    def _generate_preview_sync(self, image_path: str, width: int, height: int, 
                             quality: int, format: str) -> Tuple[str, int, int, bool]:
        """Synchronous preview generation"""
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(image_path, width, height)
        cache_path = self._get_cache_path(cache_key, format)
        
        # Return cached preview if exists
        if cache_path.exists():
            cached_image = cv2.imread(str(cache_path))
            if cached_image is not None:
                h, w = cached_image.shape[:2]
                return str(cache_path), w, h, True
        
        # Load and resize image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Generate preview
        preview = self._resize_image(image, width, height)
        h, w = preview.shape[:2]
        
        # Save to cache
        if format.lower() in ['jpg', 'jpeg']:
            cv2.imwrite(str(cache_path), preview, [cv2.IMWRITE_JPEG_QUALITY, quality])
        elif format.lower() == 'png':
            cv2.imwrite(str(cache_path), preview, [cv2.IMWRITE_PNG_COMPRESSION, 9 - (quality // 10)])
        else:
            cv2.imwrite(str(cache_path), preview)
        
        # Update cache index
        self._cache_index[cache_key] = {
            'path': str(cache_path),
            'source': image_path,
            'width': w,
            'height': h,
            'created': time.time()
        }
        self._save_cache_index()
        
        return str(cache_path), w, h, False
    
    async def generate_preview(self, request: PreviewRequest) -> PreviewResponse:
        """Generate preview asynchronously"""
        loop = asyncio.get_event_loop()
        
        try:
            # Run preview generation in thread pool
            preview_path, width, height, cached = await loop.run_in_executor(
                self.executor,
                self._generate_preview_sync,
                request.image_path,
                request.width,
                request.height,
                request.quality,
                request.format
            )
            
            generation_time = 0.0 if cached else time.time()
            
            return PreviewResponse(
                preview_path=preview_path,
                width=width,
                height=height,
                generation_time=generation_time,
                cached=cached
            )
            
        except Exception as e:
            raise ValueError(f"Preview generation failed: {str(e)}")
    
    async def generate_thumbnail(self, image_path: str, size: int = 150) -> str:
        """Generate small thumbnail (square crop)"""
        request = PreviewRequest(
            image_path=image_path,
            width=size,
            height=size,
            quality=75,
            format="jpeg"
        )
        response = await self.generate_preview(request)
        return response.preview_path
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """Clear preview cache"""
        import shutil
        
        if older_than_days is None:
            # Clear entire cache
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_index.clear()
            self._save_cache_index()
        else:
            # Clear old entries
            current_time = time.time()
            cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
            
            keys_to_remove = []
            for key, info in self._cache_index.items():
                if info.get('created', 0) < cutoff_time:
                    cache_file = Path(info['path'])
                    if cache_file.exists():
                        cache_file.unlink()
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache_index[key]
            
            self._save_cache_index()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = 0
        file_count = 0
        
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file() and cache_file.suffix in ['.jpg', '.jpeg', '.png']:
                total_size += cache_file.stat().st_size
                file_count += 1
        
        return {
            'total_files': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_entries': len(self._cache_index)
        }