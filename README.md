# Nstant Nfinity - Photo Processor

Revolutionary automated photo processing application for professional photographers.

## Prerequisites

- Node.js 18+
- Python 3.13
- Rust (for Tauri)

## Setup

1. Install dependencies:
```bash
# Install Node dependencies
npm install

# Install Python dependencies
cd python-backend
pip install -r requirements.txt
cd ..
```

2. Start development environment:

**Linux/macOS:**
```bash
./start-dev.sh
```

**Windows:**
```batch
start-dev.bat
```

Or manually:
```bash
# Terminal 1 - Start Python backend
cd python-backend
python -m uvicorn main:app --reload --port 8888

# Terminal 2 - Start Tauri app
npm run tauri:dev
```

## Architecture

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Desktop**: Tauri 2.0 (Rust)
- **Backend**: Python 3.13 + FastAPI + OpenCV
- **IPC**: MessagePack + HTTP/SSE

## Development

The app follows a strict 5-phase development workflow:
1. REVIEW - Understand the task
2. DESIGN - Plan the implementation
3. IMPLEMENTATION - Build incrementally
4. INTEGRATION - Connect components
5. CHECKPOINT - Update documentation

See DEVELOPMENT_WORKFLOW.md for details.