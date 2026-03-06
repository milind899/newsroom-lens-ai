@echo off
echo Starting backend...
cd /d C:\Users\milin\Downloads\Lexo\Hack\backend
start "LEXO-BACKEND" py -3.12 -m uvicorn main:app --host 0.0.0.0 --port 8000
echo Starting frontend...
cd /d C:\Users\milin\Downloads\Lexo\Hack\frontend
start "LEXO-FRONTEND" npm run dev
echo.
echo Both servers starting. Wait ~10 seconds then open http://localhost:3000
