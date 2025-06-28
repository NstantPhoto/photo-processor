#!/bin/bash

echo "🚀 Starting Nstant Nfinity Photo Processor..."

# Check if Python backend is running
if ! curl -s http://localhost:8888/health > /dev/null 2>&1; then
    echo "📦 Starting Python backend..."
    cd python-backend
    source ../venv/bin/activate
    python -m uvicorn main:app --port 8888 > ../backend.log 2>&1 &
    cd ..
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    sleep 3
    
    if curl -s http://localhost:8888/health > /dev/null 2>&1; then
        echo "✅ Backend started successfully"
    else
        echo "❌ Failed to start backend. Check backend.log for errors"
        exit 1
    fi
else
    echo "✅ Backend already running"
fi

# Start Tauri app
echo "🎨 Starting Tauri app..."
npm run tauri dev