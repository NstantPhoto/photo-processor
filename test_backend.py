#!/usr/bin/env python3
"""Test script to verify backend is running and processing works"""

import requests
import json
import time
from pathlib import Path

def test_backend():
    base_url = "http://localhost:8888"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Backend is healthy:", response.json())
        else:
            print("✗ Backend health check failed:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend. Make sure it's running on port 8888")
        return False
    
    # Test pipeline execution with a simple pipeline
    print("\nTesting pipeline execution...")
    
    # Find a test image
    test_images_dir = Path("test-images/hot-folder-test/testsamples")
    test_images = list(test_images_dir.glob("*.jpg"))
    
    if not test_images:
        print("✗ No test images found")
        return False
    
    test_image = test_images[0].resolve()  # Get absolute path
    output_path = test_image.parent / f"{test_image.stem}_processed{test_image.suffix}"
    
    print(f"Using test image: {test_image}")
    
    # Create a simple pipeline config
    pipeline_config = {
        "pipeline_config": {
            "nodes": [
                {
                    "id": "input_1",
                    "node_type": "input",
                    "processor_type": "input",
                    "parameters": {},
                    "position": [50, 100]
                },
                {
                    "id": "brightness_1",
                    "node_type": "processor",
                    "processor_type": "brightness",
                    "parameters": {"adjustment": 0.2},
                    "position": [200, 100]
                },
                {
                    "id": "contrast_1",
                    "node_type": "processor", 
                    "processor_type": "contrast",
                    "parameters": {"factor": 1.2},
                    "position": [350, 100]
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
                {"source": "brightness_1", "target": "contrast_1"},
                {"source": "contrast_1", "target": "output_1"}
            ]
        },
        "input_path": str(test_image),
        "output_path": str(output_path),
        "session_id": None
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/api/pipeline/execute",
            json=pipeline_config,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            elapsed = time.time() - start_time
            
            if result["success"]:
                print(f"✓ Pipeline executed successfully in {elapsed:.2f}s")
                print(f"  Output: {result['output_path']}")
                print(f"  Processing time: {result['processing_time']:.2f}s")
                
                # Check if output file exists
                if Path(result['output_path']).exists():
                    print("✓ Output file created successfully")
                else:
                    print("✗ Output file not found")
            else:
                print(f"✗ Pipeline execution failed: {result['error']}")
        else:
            print(f"✗ Pipeline request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error during pipeline execution: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Nstant Nfinity Backend Test ===\n")
    
    if test_backend():
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Tests failed!")
        print("\nMake sure the backend is running:")
        print("  cd python-backend")
        print("  python -m uvicorn main:app --reload --port 8888")