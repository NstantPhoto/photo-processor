#!/bin/bash

echo "Starting Nstant Nfinity Python Backend..."

# Activate virtual environment
source venv/bin/activate

# Change to python-backend directory
cd python-backend

# Start the backend server
echo "Starting FastAPI server on http://localhost:8888"
python -m uvicorn main:app --reload --port 8888