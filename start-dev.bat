@echo off
REM Content Repurposing Tool - Development Startup Script (Windows)
REM This script sets up the complete development environment

echo 🚀 Starting Content Repurposing Tool Development Environment
echo ============================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

echo ✅ Docker is running

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env >nul
    echo ✅ .env file created. You can customize it if needed.
) else (
    echo ✅ .env file already exists
)

REM Start PostgreSQL and Redis containers
echo 🐘 Starting PostgreSQL and Redis containers...
docker-compose up -d postgres redis

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
:wait_postgres
docker-compose exec postgres pg_isready -U postgres -d content_repurpose >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    echo    Still waiting for PostgreSQL...
    goto wait_postgres
)

echo ✅ PostgreSQL is ready

REM Wait for Redis to be ready
echo ⏳ Waiting for Redis to be ready...
:wait_redis
docker-compose exec redis redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    echo    Still waiting for Redis...
    goto wait_redis
)

echo ✅ Redis is ready

REM Install Python dependencies
echo 📦 Installing Python dependencies...
cd backend
pip install -r requirements.txt

REM Run database migrations
echo 🗄️  Running database migrations...
alembic upgrade head

echo.
echo 🎉 Development environment is ready!
echo ============================================================
echo.
echo Services running:
echo   • PostgreSQL: localhost:5432
echo   • Redis: localhost:6379
echo   • pgAdmin: http://localhost:5050 (admin@contentrepurpose.local / admin123)
echo   • Redis Commander: http://localhost:8081
echo.
echo To start the FastAPI server, run:
echo   cd backend ^&^& python main.py
echo.
echo To stop the containers, run:
echo   docker-compose down
echo.