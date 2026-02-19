@echo off
REM PharmaGuard 2.0 - Automated Setup Script (Windows)

echo.
echo PharmaGuard 2.0 - Quick Setup Script (Windows)
echo ============================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION%

REM Check Node
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] %NODE_VERSION%

REM Setup Backend
echo.
echo Setting up Backend...
cd pharmaguard-backend

echo    Installing dependencies...
pip install -r requirements.txt >nul 2>&1

if not exist .env (
    echo    Creating .env file...
    copy .env.example .env >nul
    echo [WARNING] Please edit .env and add your OPENAI_API_KEY
)

cd ..

REM Setup Frontend
echo.
echo Setting up Frontend...
cd pharmaguard-frontend

echo    Installing dependencies...
npm install --legacy-peer-deps >nul 2>&1

cd ..

echo.
echo [SUCCESS] Setup complete!
echo.
echo Next steps:
echo.
echo 1. Edit the backend configuration:
echo    Opening .env file...
echo    notepad pharmaguard-backend\.env
echo    - Add your OPENAI_API_KEY
echo.
echo 2. Start the backend (Press Ctrl+C to stop)
echo    Open a NEW Command Prompt and run:
echo    cd pharmaguard-backend
echo    python -m uvicorn app.main:app --reload --port 8000
echo.
echo 3. Start the frontend (Press Ctrl+C to stop)
echo    Open another NEW Command Prompt and run:
echo    cd pharmaguard-frontend
echo    npm run dev
echo.
echo 4. Open your browser:
echo    http://localhost:3003
echo.
echo 5. Register/Login to start analyzing!
echo.
pause
