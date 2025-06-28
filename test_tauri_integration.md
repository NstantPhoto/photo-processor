# Tauri Integration Test Plan

## Prerequisites
1. Python backend running on port 8888 ✅
2. Virtual environment activated ✅
3. All dependencies installed ✅

## Test Steps

### 1. Start the Tauri App
```bash
npm run tauri dev
```

### 2. Test Hot Folder
- The app should detect the 109 test images in `test-images/hot-folder-test/testsamples/`
- Images should appear in the image grid

### 3. Test Node Editor
- Go to the Node Editor tab
- Drag nodes from the palette:
  - Input node
  - Brightness processor
  - Contrast processor
  - Output node
- Connect them in sequence: Input → Brightness → Contrast → Output

### 4. Select Images
- Go back to the image grid
- Select a few test images (click to select)

### 5. Process Images
- Return to Node Editor
- A blue "Process X Images" button should appear at the bottom right
- Click the process button
- Watch the progress indicator

### 6. Verify Results
- Check the `test-images/hot-folder-test/testsamples/` directory
- Processed images should have `_processed` suffix
- Images should show brightness and contrast adjustments

## Expected Results
- ✅ Pipeline validates successfully
- ✅ Images process without errors
- ✅ Progress shows during processing
- ✅ Processed images are saved
- ✅ UI remains responsive

## Current Implementation Status
- ✅ Backend pipeline execution works
- ✅ Input/Output nodes implemented
- ✅ All processors working
- ✅ Node Editor syncs with pipeline store
- ✅ Process button wired to backend
- ✅ IPC commands connected

## Known Issues to Fix
- Image paths need to be absolute for backend processing
- No real-time progress updates (using simple progress bar)
- Processed images not shown in UI yet
- No error handling UI