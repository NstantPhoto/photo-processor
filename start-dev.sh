#!/bin/bash

echo "Starting Nstant Nfinity Development Environment..."

# Start Python backend in background
echo "Starting Python processing engine..."
cd python-backend
source ../venv/bin/activate
python -m uvicorn main:app --reload --port 8888 &
PYTHON_PID=$!
cd ..

# Wait for Python to start
sleep 2

# Start Tauri dev
echo "Starting Tauri application..."
npm run tauri:dev

# Kill Python when Tauri exits
kill $PYTHON_PID