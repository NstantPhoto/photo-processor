#!/usr/bin/env python3
"""Test script to verify preview generation works correctly"""

import asyncio
import httpx
import time
from pathlib import Path

async def test_preview_generation():
    """Test the preview generation endpoint"""
    
    # Test images
    test_images = [
        "/home/canon/projects/photo-processor/test-images/hot-folder-test/test_image_0001.jpg",
        "/home/canon/projects/photo-processor/test-images/hot-folder-test/testsamples/DSC04593.jpg"
    ]
    
    async with httpx.AsyncClient() as client:
        print("Testing preview generation system...\n")
        
        # Test health
        health = await client.get("http://localhost:8888/health")
        print(f"Backend health: {health.json()}\n")
        
        # Test preview generation for each image
        for image_path in test_images:
            print(f"Generating preview for: {Path(image_path).name}")
            
            # Generate standard preview
            preview_request = {
                "image_path": image_path,
                "width": 800,
                "height": 600,
                "quality": 85,
                "format": "jpeg"
            }
            
            start_time = time.time()
            response = await client.post(
                "http://localhost:8888/api/preview/generate",
                json=preview_request
            )
            
            if response.status_code == 200:
                result = response.json()
                gen_time = time.time() - start_time
                print(f"  ✅ Preview generated in {gen_time:.3f}s")
                print(f"     Size: {result['width']}x{result['height']}")
                print(f"     Cached: {result['cached']}")
                print(f"     Path: {result['preview_path']}")
            else:
                print(f"  ❌ Failed: {response.text}")
            
            # Generate thumbnail
            print(f"\n  Generating thumbnail...")
            thumb_response = await client.post(
                "http://localhost:8888/api/preview/thumbnail",
                params={"image_path": image_path, "size": 150}
            )
            
            if thumb_response.status_code == 200:
                thumb_result = thumb_response.json()
                print(f"  ✅ Thumbnail generated: {thumb_result['thumbnail_path']}")
            else:
                print(f"  ❌ Thumbnail failed: {thumb_response.text}")
            
            print()
        
        # Test cache stats
        print("\nChecking cache statistics...")
        stats_response = await client.get("http://localhost:8888/api/preview/cache/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total size: {stats['total_size_mb']} MB")
            print(f"  Cache entries: {stats['cache_entries']}")
        
        # Test cached preview (should be instant)
        print("\nTesting cached preview retrieval...")
        start_time = time.time()
        cached_response = await client.post(
            "http://localhost:8888/api/preview/generate",
            json={
                "image_path": test_images[0],
                "width": 800,
                "height": 600,
                "quality": 85,
                "format": "jpeg"
            }
        )
        
        if cached_response.status_code == 200:
            result = cached_response.json()
            retrieval_time = time.time() - start_time
            print(f"  ✅ Cached preview retrieved in {retrieval_time*1000:.1f}ms")
            print(f"     Was cached: {result['cached']}")

if __name__ == "__main__":
    asyncio.run(test_preview_generation())