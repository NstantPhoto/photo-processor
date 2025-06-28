#!/usr/bin/env python3
"""Verify that image processing actually modifies the image"""

import cv2
import numpy as np
from pathlib import Path

def compare_images(original_path, processed_path):
    """Compare original and processed images"""
    
    # Load images
    original = cv2.imread(str(original_path))
    processed = cv2.imread(str(processed_path))
    
    if original is None or processed is None:
        print("❌ Failed to load images")
        return
    
    print(f"\n📊 Image Comparison:")
    print(f"Original size: {original.shape}")
    print(f"Processed size: {processed.shape}")
    
    # Calculate mean brightness
    original_brightness = np.mean(original)
    processed_brightness = np.mean(processed)
    brightness_change = ((processed_brightness - original_brightness) / original_brightness) * 100
    
    print(f"\n💡 Brightness Analysis:")
    print(f"Original brightness: {original_brightness:.2f}")
    print(f"Processed brightness: {processed_brightness:.2f}")
    print(f"Change: {brightness_change:+.1f}%")
    
    # Calculate contrast (standard deviation)
    original_contrast = np.std(original)
    processed_contrast = np.std(processed)
    contrast_change = ((processed_contrast - original_contrast) / original_contrast) * 100
    
    print(f"\n🎨 Contrast Analysis:")
    print(f"Original contrast: {original_contrast:.2f}")
    print(f"Processed contrast: {processed_contrast:.2f}")
    print(f"Change: {contrast_change:+.1f}%")
    
    # Check if images are different
    if np.array_equal(original, processed):
        print("\n⚠️  WARNING: Images are identical!")
    else:
        print("\n✅ Images are different - processing applied successfully!")
        
        # Calculate pixel difference
        diff = cv2.absdiff(original, processed)
        diff_percent = (np.count_nonzero(diff) / diff.size) * 100
        print(f"Pixels changed: {diff_percent:.1f}%")

if __name__ == "__main__":
    original = Path("test-images/hot-folder-test/testsamples/DSC04601.jpg")
    processed = Path("test-images/hot-folder-test/testsamples/DSC04601_processed.jpg")
    
    compare_images(original, processed)