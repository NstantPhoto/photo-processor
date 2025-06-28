#!/bin/bash

echo "🔧 Fixing common issues..."

# Kill any existing processes
echo "🛑 Stopping existing processes..."
pkill -f uvicorn || true
pkill -f vite || true
pkill -f tauri || true

# Clean build artifacts
echo "🧹 Cleaning build artifacts..."
rm -rf dist/
rm -rf src-tauri/target/
rm -rf node_modules/.vite/

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
pip install psutil networkx

# Build frontend
echo "🏗️ Building frontend..."
npm run build

echo "✅ Issues fixed! You can now run:"
echo "   ./start-app.sh"
echo ""
echo "Or manually:"
echo "   # Terminal 1:"
echo "   cd python-backend && source ../venv/bin/activate && python -m uvicorn main:app --port 8888"
echo ""
echo "   # Terminal 2:"
echo "   npm run tauri dev"