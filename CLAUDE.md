# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nstant Nfinity** is a revolutionary automated photo processing application designed for high-volume professional photographers (wedding, event, sports, portrait). It processes images automatically through an AI-powered, node-based visual pipeline, delivering professional results in minutes instead of hours.

**Target Performance:**
- Process 100 RAW files (25MP) in under 5 minutes
- Preview generation: <100ms for thumbnails, <500ms for full preview
- Memory efficient: Handle 3MP to 100MP images
- Must outperform Perfectly Clear, Imagen AI, and Radiant Photo

## Technology Stack

**Frontend:**
- React 18+ with TypeScript (strict mode)
- React Flow for node-based editor
- Tailwind CSS + Framer Motion
- Zustand for state management
- Glass morphism UI with neon accents (blue #00d4ff, red #ff3366)

**Desktop Framework:**
- Tauri 2.0 (Rust)
- Native window management
- File system access
- IPC bridge to Python

**Backend:**
- Python 3.13 with type hints
- FastAPI on localhost:8888
- OpenCV + CuPy for GPU acceleration
- MessagePack for IPC serialization
- Memory-mapped files for large images

**AI Models (all open-source):**
- NIMA for quality assessment
- Deep White Balance for color correction
- U²-Net for background removal
- Real-ESRGAN for upscaling
- MobileViT for scene classification

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend (UI)                    │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ Node Editor │ │ Image Viewer │ │ Control Panels  │  │
│  └──────┬──────┘ └──────┬───────┘ └────────┬────────┘  │
│         └────────────────┼──────────────────┘           │
└─────────────────────────┼───────────────────────────────┘
                          │ Tauri IPC (invoke)
┌─────────────────────────┼───────────────────────────────┐
│                   Tauri Core (Rust)                      │
│  ┌─────────────┐ ┌──────┴───────┐ ┌─────────────────┐  │
│  │ File System │ │ Process Mgmt │ │ Resource Alloc  │  │
│  └─────────────┘ └──────────────┘ └─────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP/SSE
┌─────────────────────────┴───────────────────────────────┐
│              Python Processing Engine                    │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ AI Pipeline │ │ GPU Process  │ │ Queue Manager   │  │
│  └─────────────┘ └──────────────┘ └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Development Commands

```bash
# Development
npm run dev                    # Start React dev server
npm run tauri dev             # Start full Tauri app
python -m uvicorn python-backend.main:app --reload --port 8888

# Testing
npm test                      # Jest tests for React
pytest python-backend/tests   # Python backend tests
npm run test:e2e             # Playwright E2E tests

# Building
npm run build                # Build React app
npm run tauri build         # Build distributable

# Performance
npm run benchmark           # Run performance tests
python benchmark_suite.py   # Backend benchmarks
```

## Key Implementation Patterns

### 1. Image Data Flow
- Frontend requests processing via `invoke('process_image', {path: '/path/to/image'})`
- Tauri validates path and forwards to Python backend
- Python processes and saves result, returns new path
- Tauri sends path back to frontend for display
- **Never send raw image data through IPC - only paths**

### 2. Memory Management
```python
# Dynamic chunk sizing for large images
base_chunk = 2048  # 2K tiles
overlap = 128      # For seamless processing
chunk_size = min(2048, sqrt(available_memory_mb * 1024 * 1024 / 16))
```

### 3. Processing Pipeline
```python
# Every processor must implement:
class BaseProcessor:
    def estimate_memory(self, image_shape: Tuple[int, int, int]) -> int
    def process_preview(self, image: np.ndarray) -> np.ndarray  # <100ms
    def process_full(self, image: np.ndarray) -> np.ndarray     # Handle up to 100MP
```

### 4. Node System
- Hot Folder → AI Analysis → Corrections → Export
- Nodes can run parallel or sequential based on dependencies
- Each node has auto mode (AI-driven) and manual controls
- Real-time preview updates via Server-Sent Events

## Performance Requirements

**Mandatory Benchmarks:**
- Hot folder scanning: <2 seconds detection
- Small images (<5MP): <0.5s processing
- Medium images (5-20MP): <2s processing
- Large images (20-100MP): <10s processing
- Batch: 100+ images/hour on standard hardware
- UI: 60fps during all operations

**Resource Limits:**
- Memory: 8GB max for processing queue
- GPU: Fallback to CPU when unavailable
- Workers: Dynamic based on system resources

## Critical Development Rules

1. **Non-Destructive**: Original files are sacred - never modify
2. **Memory First**: Every operation must consider memory constraints
3. **Preview Priority**: Show something in <100ms, process full quality in background
4. **Error Recovery**: Never fail entire batch for one bad image
5. **Cross-Platform**: Test on Windows and macOS regularly

## Node Types Reference

**Input/Output:**
- Hot Folder Monitor
- Manual Import
- Batch Export

**Analysis:**
- AI Scene Analysis
- Face Detection
- Quality Assessment

**Corrections:**
- Exposure/Brightness
- Color Balance
- Noise Reduction
- Sharpening
- Lens Correction

**Creative:**
- Color Grading
- Background Removal
- Portrait Retouching

**Utility:**
- Auto Culling
- Image Resize
- Watermark
- Metadata Editor

## Session Management

Photography jobs are organized by session (wedding, portrait shoot, etc.):
```typescript
interface PhotoSession {
  id: string
  name: string
  date: Date
  type: 'wedding' | 'portrait' | 'sports' | 'event'
  imageCount: number
  processedCount: number
}
```

## Testing Strategy

1. **Unit Tests**: Each processor, node, and utility function
2. **Integration Tests**: Full pipeline processing
3. **Performance Tests**: Meet benchmark requirements
4. **Visual Tests**: UI consistency and responsiveness
5. **Memory Tests**: No leaks during long sessions

## Deployment

- **Windows**: NSIS installer with model downloads
- **macOS**: DMG with code signing
- **Models**: Downloaded during first run (~500MB)
- **Updates**: Tauri updater with delta updates