#!/usr/bin/env python3
"""Test script to verify pipeline integration works correctly"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_pipeline_execution():
    """Test the pipeline execution endpoint"""
    
    # Test image path
    test_image = Path("/home/canon/projects/photo-processor/test-images/hot-folder-test/test_image_0001.jpg")
    output_path = test_image.parent / f"{test_image.stem}_pipeline_test.jpg"
    
    # Simple pipeline configuration with Input -> Brightness -> Output
    pipeline_config = {
        "nodes": [
            {
                "id": "input_1",
                "node_type": "input",
                "processor_type": "input",
                "parameters": {},
                "position": [100, 100]
            },
            {
                "id": "brightness_1",
                "node_type": "processor",
                "processor_type": "brightness",
                "parameters": {
                    "adjustment": 0.2,
                    "mode": "linear"
                },
                "position": [300, 100]
            },
            {
                "id": "output_1",
                "node_type": "output",
                "processor_type": "output",
                "parameters": {},
                "position": [500, 100]
            }
        ],
        "connections": [
            {"source": "input_1", "target": "brightness_1"},
            {"source": "brightness_1", "target": "output_1"}
        ]
    }
    
    # Request payload
    request_data = {
        "pipeline_config": pipeline_config,
        "input_path": str(test_image),
        "output_path": str(output_path),
        "session_id": None
    }
    
    print("Testing pipeline execution...")
    print(f"Input: {test_image}")
    print(f"Output: {output_path}")
    print("\nPipeline: Input -> Brightness (+20%) -> Output")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test backend health first
            health_response = await client.get("http://localhost:8888/health")
            print(f"\nBackend health: {health_response.json()}")
            
            # Execute pipeline
            print("\nExecuting pipeline...")
            response = await client.post(
                "http://localhost:8888/api/pipeline/execute",
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess! Processing completed in {result['processing_time']:.2f} seconds")
                print(f"Output saved to: {result['output_path']}")
                if result.get('quality_score'):
                    print(f"Quality score: {result['quality_score']}")
                    
                # Check if output file exists
                if Path(result['output_path']).exists():
                    print("\n✅ Output file created successfully!")
                else:
                    print("\n❌ Output file not found!")
            else:
                print(f"\n❌ Pipeline execution failed: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pipeline_execution())