#!/usr/bin/env python3
"""
Test script to verify the image processing pipeline works with real images.
"""

import asyncio
from pathlib import Path
import cv2
import numpy as np
import time

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent))

from pipeline import PipelineManager, ProcessingNode
from processors import (
    ExposureProcessor,
    BrightnessProcessor,
    ColorBalanceProcessor,
    ContrastProcessor,
    QualityAssessmentProcessor
)


async def test_single_image_processing():
    """Test processing a single image through the pipeline."""
    # Setup
    test_image_path = Path("../test-images/hot-folder-test/testsamples/DSC04593.jpg")
    output_path = Path("../test-output/DSC04593_processed.jpg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Testing with image: {test_image_path}")
    
    # Create pipeline manager
    pipeline = PipelineManager()
    
    # Register processors
    pipeline.register_processor('quality', QualityAssessmentProcessor)
    pipeline.register_processor('exposure', ExposureProcessor)
    pipeline.register_processor('brightness', BrightnessProcessor)
    pipeline.register_processor('color_balance', ColorBalanceProcessor)
    pipeline.register_processor('contrast', ContrastProcessor)
    
    # Create processing nodes
    quality_node = ProcessingNode(
        id="quality_1",
        processor=QualityAssessmentProcessor(),
        position=(100, 100)
    )
    
    exposure_node = ProcessingNode(
        id="exposure_1",
        processor=ExposureProcessor(),
        position=(300, 100)
    )
    
    color_node = ProcessingNode(
        id="color_1",
        processor=ColorBalanceProcessor(),
        position=(500, 100)
    )
    
    contrast_node = ProcessingNode(
        id="contrast_1",
        processor=ContrastProcessor(),
        position=(700, 100)
    )
    
    # Add nodes to pipeline
    pipeline.add_node(quality_node)
    pipeline.add_node(exposure_node)
    pipeline.add_node(color_node)
    pipeline.add_node(contrast_node)
    
    # Connect nodes: quality -> exposure -> color -> contrast
    pipeline.connect_nodes("quality_1", "exposure_1")
    pipeline.connect_nodes("exposure_1", "color_1")
    pipeline.connect_nodes("color_1", "contrast_1")
    
    # Set parameters
    exposure_node.processor.set_parameters(
        exposure_value=0.3,  # Slight brightening
        auto_mode=False
    )
    
    color_node.processor.set_parameters(
        temperature=10,  # Slight warming
        tint=0,
        auto_mode=False
    )
    
    contrast_node.processor.set_parameters(
        contrast=15,  # Moderate contrast boost
        algorithm='sigmoid'
    )
    
    # Validate pipeline
    is_valid, errors = pipeline.validate_pipeline()
    if not is_valid:
        print(f"Pipeline validation failed: {errors}")
        return
    
    print("Pipeline validated successfully")
    print(f"Execution order: {pipeline.get_execution_order()}")
    
    # Process image
    try:
        print("\nProcessing image...")
        start_time = time.time()
        
        result = await pipeline.process_image(
            test_image_path,
            output_path,
            preview_only=False
        )
        
        processing_time = time.time() - start_time
        
        print(f"\nProcessing completed in {processing_time:.2f} seconds")
        print(f"Output saved to: {output_path}")
        
        # Get quality score from the quality processor
        quality_metrics = quality_node.processor.get_quality_metrics()
        print(f"\nQuality Assessment:")
        print(f"  Score: {quality_metrics['score']:.2f}/10")
        
        # Display metadata
        print(f"\nProcessing metadata:")
        for key, value in result.metadata.items():
            if key != 'parameters':
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()


async def test_preview_generation():
    """Test preview generation speed."""
    test_image_path = Path("../test-images/hot-folder-test/testsamples/DSC04594.jpg")
    
    print(f"\nTesting preview generation with: {test_image_path}")
    
    # Load image
    image = cv2.imread(str(test_image_path))
    print(f"Image shape: {image.shape}")
    
    # Test each processor's preview generation
    processors = [
        ('Exposure', ExposureProcessor()),
        ('Brightness', BrightnessProcessor()),
        ('Color Balance', ColorBalanceProcessor()),
        ('Contrast', ContrastProcessor())
    ]
    
    for name, processor in processors:
        start_time = time.time()
        preview = processor.process_preview(image)
        preview_time = (time.time() - start_time) * 1000
        
        print(f"{name}: {preview_time:.1f}ms")
        
        # Check if we meet the <100ms requirement
        if preview_time < 100:
            print(f"  ✅ Meets <100ms requirement")
        else:
            print(f"  ❌ Exceeds 100ms requirement")


async def test_memory_efficiency():
    """Test memory-efficient processing of a large image."""
    from pipeline.memory_manager import MemoryManager
    
    print("\nTesting memory-efficient processing...")
    
    # Get memory status
    mem_manager = MemoryManager()
    status = mem_manager.get_memory_status()
    
    print(f"System Memory Status:")
    print(f"  Total: {status.total_mb:.1f} MB")
    print(f"  Available: {status.available_mb:.1f} MB")
    print(f"  Used: {status.percent_used:.1f}%")
    print(f"  Recommended chunk size: {status.recommended_chunk_size}px")
    
    # Test with a real image
    test_image_path = Path("../test-images/hot-folder-test/testsamples/DSC04595.jpg")
    image = cv2.imread(str(test_image_path))
    
    # Check if tiled processing would be needed
    can_process_full = mem_manager.can_process_in_memory(image.shape)
    print(f"\nImage shape: {image.shape}")
    print(f"Can process in memory: {can_process_full}")
    
    if not can_process_full:
        chunks = mem_manager.calculate_chunks(image.shape)
        print(f"Would process in {len(chunks)} chunks")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Nstant Nfinity Pipeline Test")
    print("=" * 60)
    
    # Test 1: Single image processing
    await test_single_image_processing()
    
    # Test 2: Preview generation speed
    await test_preview_generation()
    
    # Test 3: Memory efficiency
    await test_memory_efficiency()
    
    print("\n" + "=" * 60)
    print("Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())