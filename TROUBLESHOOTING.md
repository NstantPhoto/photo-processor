# Troubleshooting Nstant Nfinity

## Common Issues and Solutions

### 1. Tauri Won't Build - Permission Errors

**Error**: `Permission dialog:open not found` or similar

**Solution**: The capabilities file was using incorrect permissions. Fixed by using:
```json
{
  "permissions": [
    "core:default",
    "dialog:default",
    "fs:default",
    "fs:read-all",
    "fs:write-all",
    "shell:default"
  ]
}
```

### 2. TypeScript Build Errors

**Error**: `Property 'selectedImages' does not exist on type 'ImageStore'`

**Solution**: Added missing properties to ImageStore:
- `images: ImageInfo[]`
- `selectedImages: string[]`
- Related methods for image management

### 3. Python Backend Import Errors

**Error**: `No module named 'psutil'` or similar

**Solution**: Install all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
pip install psutil networkx
```

### 4. BaseProcessor Initialization Error

**Error**: `BaseProcessor.__init__() missing 2 required positional arguments`

**Solution**: Fixed Input/Output processors to call super().__init__ with required parameters

### 5. Image Path Issues

**Error**: `Failed to load image: test-images/...`

**Solution**: Use absolute paths when calling backend from different directory:
```python
test_image = test_images[0].resolve()  # Get absolute path
```

## Quick Fixes

### Clean Rebuild
```bash
rm -rf dist/
rm -rf src-tauri/target/
rm -rf node_modules/.vite/
npm install
npm run build
```

### Kill All Processes
```bash
pkill -f uvicorn
pkill -f vite
pkill -f tauri
```

### Check What's Running
```bash
ps aux | grep -E "uvicorn|tauri|vite"
lsof -i :8888  # Check Python backend
lsof -i :1420  # Check Vite dev server
```

### Verify Backend Health
```bash
curl http://localhost:8888/health
```

## Current Status

✅ TypeScript errors fixed
✅ Python backend working
✅ Tauri permissions fixed
✅ Pipeline processing tested
✅ Image store updated

The app should now compile and run properly!