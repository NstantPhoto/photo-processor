#!/usr/bin/env python3
"""
Test script for hot folder functionality.
Creates test images in a folder to trigger the file watcher.
"""

import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_image(path: Path, index: int):
    """Create a test image with an index number"""
    # Create a simple test image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color=(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    ))
    
    draw = ImageDraw.Draw(image)
    
    # Draw some shapes
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.rectangle([x1, y1, x2, y2], fill=color, outline=(255, 255, 255))
    
    # Add text
    text = f"Test Image #{index}"
    draw.text((width//2 - 50, height//2), text, fill=(255, 255, 255))
    
    # Save the image
    image.save(path, 'JPEG')
    print(f"Created: {path}")

def main():
    # Create test folder
    test_folder = Path("test-images/hot-folder-test")
    test_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"Test folder: {test_folder.absolute()}")
    print("Add this folder as a hot folder in the app")
    print("Press Ctrl+C to stop generating images\n")
    
    # Generate images periodically
    index = 1
    try:
        while True:
            filename = f"test_image_{index:04d}.jpg"
            filepath = test_folder / filename
            
            create_test_image(filepath, index)
            
            # Wait a bit before creating the next image
            time.sleep(3)
            index += 1
            
    except KeyboardInterrupt:
        print("\nStopped generating images")
        print(f"Generated {index - 1} test images")

if __name__ == "__main__":
    main()