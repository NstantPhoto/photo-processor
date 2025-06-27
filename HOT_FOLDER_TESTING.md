# Hot Folder Testing Guide

## Overview
The hot folder system monitors directories for new images and automatically queues them for processing.

## Testing Steps

### 1. Start the Application
```bash
# Terminal 1 - Start Python backend
cd python-backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8888

# Terminal 2 - Start Tauri app
npm run tauri:dev
```

### 2. Add a Hot Folder
1. Click "Add Folder" in the Hot Folder panel (right side)
2. Select a directory to monitor
3. The folder will appear in the list with "Active" status

### 3. Test File Detection
```bash
# Terminal 3 - Run test script
python test-hotfolder.py
```

This will:
- Create a `test-images/hot-folder-test` directory
- Generate test images every 3 seconds
- Each image has a unique color and number

### 4. Verify Functionality
- **File Detection**: New files should appear in queue within 2 seconds
- **Stability Check**: Files are only queued after 2 seconds of no changes
- **Queue Status**: Shows pending/processing/completed counts
- **Pause/Resume**: Click pause button to stop processing
- **Folder Toggle**: Click "Active/Inactive" to enable/disable folders

### 5. Manual Testing
You can also:
- Copy images into the monitored folder
- Take screenshots and save to the folder
- Export from photo editing software

## Expected Behavior
- ✅ Files detected within 2 seconds
- ✅ Only stable files are queued (no partial files)
- ✅ Queue updates in real-time
- ✅ Multiple folders can be monitored
- ✅ Only image files are queued (jpg, png, etc.)

## Troubleshooting
- **No files detected**: Check folder permissions
- **Python errors**: Ensure backend is running on port 8888
- **UI not updating**: Check browser console for SSE errors