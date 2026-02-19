@echo off
REM PharmaGuard - Development Startup Script for Windows

echo.
echo ============================================
echo 🛡️  PHARMAGUARD - Development Environment
echo ============================================
echo.

REM Start Backend
echo Starting FastAPI Backend...
cd pharmaguard-backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing Python dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Start backend in new window
start "PharmaGuard Backend" cmd /k "python run_backend.py"
echo.
echo ✓ Backend started on http://localhost:8000
echo ✓ API docs on http://localhost:8000/docs
echo.

timeout /t 2 /nobreak

REM Start Frontend
cd ..\pharmaguard-frontend
echo.
echo Starting React Frontend...

if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install --legacy-peer-deps
)

REM Start frontend in new window
start "PharmaGuard Frontend" cmd /k "npm run dev"
echo.
echo ✓ Frontend started on http://localhost:3000
echo.

echo.
echo ============================================
echo ✅ PharmaGuard is running!
echo ============================================
echo.
echo Windows: Use Ctrl+C in each terminal to stop servers
echo.
pause
