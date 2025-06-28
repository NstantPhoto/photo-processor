# Running Nstant Nfinity

## Quick Start

```bash
./start-app.sh
```

This will:
1. Start the Python backend on port 8888
2. Launch the Tauri desktop app

## Manual Start

### Terminal 1 - Python Backend
```bash
cd python-backend
source ../venv/bin/activate
python -m uvicorn main:app --port 8888
```

### Terminal 2 - Tauri App
```bash
npm run tauri dev
```

## If You Have Issues

Run the fix script:
```bash
./fix-issues.sh
```

## Common Issues & Solutions

### 1. "Cannot find module" errors
```bash
npm install
npm run build
```

### 2. Python import errors
```bash
source venv/bin/activate
pip install -r requirements.txt
pip install psutil networkx
```

### 3. Port 8888 already in use
```bash
pkill -f uvicorn
# or
lsof -i :8888  # find process
kill -9 <PID>  # kill it
```

### 4. TypeScript errors
Fixed! The app should now build without errors.

### 5. Missing ImageStore properties
Fixed! Added `images` and `selectedImages` to the store.

## What's Working

✅ Python backend with image processing pipeline
✅ Node-based visual editor (React Flow)
✅ Image selection and batch processing
✅ Hot folder monitoring
✅ Glass morphism UI with neon accents

## Testing the App

1. **Start the app** using one of the methods above

2. **Test Hot Folder**
   - The app will detect 109 test images in `test-images/hot-folder-test/testsamples/`

3. **Create a Pipeline**
   - Go to Node Editor tab
   - Drag nodes: Input → Brightness → Contrast → Output
   - Connect them in sequence

4. **Process Images**
   - Select images from the grid
   - Click "Process X Images" button in Node Editor
   - Check for processed images with `_processed` suffix

## Verify Backend is Running

```bash
curl http://localhost:8888/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "gpu_available": false
}
```

## Development Tips

- Backend auto-reloads on file changes
- Frontend hot-reloads with Vite
- Processed images saved to same directory with `_processed` suffix
- Check `backend.log` for Python errors
- Check browser console for frontend errors