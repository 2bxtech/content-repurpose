@echo off
REM Celery Worker and Beat Startup Script for Windows Development

echo 🚀 Starting Celery Services for Content Repurposing Tool
echo ========================================================

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  Virtual environment not activated. Activating...
    call .venv\Scripts\activate.bat
)

REM Navigate to backend directory
cd /d backend

REM Check Redis connection
echo 📡 Checking Redis server...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo 🔴 Redis not running. Please start Redis server first:
    echo    redis-server
    exit /b 1
) else (
    echo ✅ Redis server is running
)

echo.
echo 👷 Starting Celery Worker...
start "Celery Worker" cmd /k "celery -A app.core.celery_app worker --loglevel=info --concurrency=2"

timeout /t 3 >nul

echo ⏰ Starting Celery Beat Scheduler...
start "Celery Beat" cmd /k "celery -A app.core.celery_app beat --loglevel=info"

timeout /t 3 >nul

echo 🌸 Starting Flower (Celery monitoring)...
start "Flower Monitor" cmd /k "celery -A app.core.celery_app flower --port=5555"

echo.
echo 🎉 All Celery services started successfully!
echo ========================================================
echo 📊 Monitoring:
echo    • Flower (Web UI): http://localhost:5555
echo    • Redis CLI: redis-cli monitor
echo.
echo 🔧 Management Commands:
echo    • View active tasks: celery -A app.core.celery_app inspect active
echo    • View registered tasks: celery -A app.core.celery_app inspect registered
echo    • Purge queue: celery -A app.core.celery_app purge
echo.
echo Press any key to close this window...
pause >nul