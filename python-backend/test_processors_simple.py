#!/usr/bin/env python3
"""
Simple test of processors without full dependencies.
Tests the processor logic without actual image processing.
"""

import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from processors import (
    ExposureProcessor,
    BrightnessProcessor,
    ColorBalanceProcessor,
    ContrastProcessor
)


def test_processor_initialization():
    """Test that all processors initialize correctly."""
    print("Testing processor initialization...")
    
    processors = [
        ExposureProcessor(),
        BrightnessProcessor(),
        ColorBalanceProcessor(),
        ContrastProcessor()
    ]
    
    for processor in processors:
        print(f"\n{processor.name}:")
        print(f"  Type: {processor.processor_type}")
        print(f"  Parameters: {processor.get_parameters()}")
        print(f"  Enabled: {processor.enabled}")
        
        # Test memory estimation for a 24MP image
        test_shape = (4000, 6000, 3)  # 24 megapixels
        memory_mb = processor.estimate_memory(test_shape) / (1024 * 1024)
        print(f"  Memory needed for 24MP image: {memory_mb:.1f} MB")


def test_parameter_setting():
    """Test parameter configuration."""
    print("\n\nTesting parameter configuration...")
    
    # Test exposure processor
    exposure = ExposureProcessor()
    exposure.set_parameters(
        exposure_value=1.5,
        auto_mode=False,
        preserve_highlights=False
    )
    
    params = exposure.get_parameters()
    print(f"\nExposure parameters after update:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Test color balance
    color = ColorBalanceProcessor()
    color.set_parameters(
        temperature=25,
        tint=-10,
        auto_mode=True
    )
    
    params = color.get_parameters()
    print(f"\nColor Balance parameters after update:")
    for key, value in params.items():
        print(f"  {key}: {value}")


def test_input_validation():
    """Test input validation."""
    print("\n\nTesting input validation...")
    
    processor = BrightnessProcessor()
    
    # Test valid inputs
    valid_inputs = [
        np.zeros((100, 100, 3), dtype=np.uint8),  # Color image
        np.zeros((100, 100), dtype=np.uint8),     # Grayscale image
    ]
    
    for i, img in enumerate(valid_inputs):
        result = processor.validate_input(img)
        print(f"Valid input {i+1}: {result} (shape: {img.shape})")
    
    # Test invalid inputs
    invalid_inputs = [
        None,                                      # None
        "not an array",                           # String
        np.zeros((0, 0, 3)),                      # Empty array
        np.zeros((10, 10, 10, 10)),              # 4D array
    ]
    
    for i, img in enumerate(invalid_inputs):
        try:
            result = processor.validate_input(img)
            print(f"Invalid input {i+1}: {result}")
        except:
            print(f"Invalid input {i+1}: False (exception)")


def test_pipeline_info():
    """Display pipeline capabilities."""
    print("\n\nPipeline Capabilities:")
    print("=" * 50)
    
    info = {
        "Input Formats": ["JPEG", "PNG", "RAW", "TIFF", "BMP"],
        "Max Image Size": "100 megapixels",
        "Processing Modes": ["Preview (<100ms)", "Full Quality"],
        "Memory Management": ["Automatic tiling", "GPU acceleration (optional)"],
        "Batch Processing": "100+ images/hour target",
    }
    
    for category, value in info.items():
        if isinstance(value, list):
            print(f"\n{category}:")
            for item in value:
                print(f"  • {item}")
        else:
            print(f"\n{category}: {value}")
    
    print("\n\nTest Image Location:")
    print(f"  /test-images/hot-folder-test/testsamples/")
    print(f"  Contains 109 test images (DSC04593-DSC04705)")


if __name__ == "__main__":
    print("=" * 60)
    print("Nstant Nfinity Processor Test (No Dependencies)")
    print("=" * 60)
    
    test_processor_initialization()
    test_parameter_setting()
    test_input_validation()
    test_pipeline_info()
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("\nNote: This test verifies processor logic without actual image processing.")
    print("To test with real images, ensure all dependencies are installed:")
    print("  - opencv-python-headless")
    print("  - numpy")
    print("  - torch & torchvision (for NIMA)")
    print("  - psutil (for memory management)")
    print("=" * 60)