@echo off
echo ========================================
echo Starting EduVerse AI Frontend
echo ========================================
echo.

cd /d "%~dp0\frontend"

echo Checking Node.js installation...
node --version
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Starting Vite development server...
echo Frontend will be available at: http://localhost:5173
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

npm run dev

pause
