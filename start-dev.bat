@echo off
echo Starting Nstant Nfinity Development Environment...

echo Starting Python processing engine...
start /b cmd /c "cd python-backend && python -m uvicorn main:app --reload --port 8888"

timeout /t 2 /nobreak > nul

echo Starting Tauri application...
npm run tauri:dev