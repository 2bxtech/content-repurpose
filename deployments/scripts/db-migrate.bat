@echo off
REM Database Migration and Management Script for Windows
REM Handles database operations for different environments

setlocal enabledelayedexpansion

REM Default configuration
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%\..
set BACKEND_DIR=%PROJECT_ROOT%\backend

REM Color codes for output (limited Windows support)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

REM Logging functions
goto :main

:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM Load environment configuration
:load_environment
set env_file=%PROJECT_ROOT%\deployments\.env.%ENVIRONMENT%

if exist "%env_file%" (
    call :log_info "Loading environment configuration for: %ENVIRONMENT%"
    for /f "usebackq tokens=1,2 delims==" %%a in ("%env_file%") do (
        if not "%%a"=="" if not "%%a"=="#" set %%a=%%b
    )
) else (
    call :log_warning "Environment file not found: %env_file%"
    call :log_info "Using default/system environment variables"
)
goto :eof

REM Check database connectivity
:check_database
call :log_info "Checking database connectivity for %ENVIRONMENT% environment..."

set max_attempts=30
set attempt=1

:check_db_loop
if %attempt% gtr %max_attempts% goto :check_db_failed

pg_isready -h %DATABASE_HOST% -p %DATABASE_PORT% -U %DATABASE_USER% -d %DATABASE_NAME% >nul 2>&1
if %errorlevel%==0 (
    call :log_success "Database is ready"
    goto :eof
)

call :log_info "Attempt %attempt%/%max_attempts% - Database not ready, waiting 2 seconds..."
timeout /t 2 /nobreak >nul
set /a attempt+=1
goto :check_db_loop

:check_db_failed
call :log_error "Database connection failed after %max_attempts% attempts"
exit /b 1

REM Wait for services
:wait_for_services
call :log_info "Waiting for services to be ready..."
call :check_database
goto :eof

REM Run database migrations
:run_migrations
call :log_info "Running database migrations for %ENVIRONMENT% environment..."

cd /d "%BACKEND_DIR%"

REM Check if alembic is available
alembic --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Alembic not found. Please install requirements first."
    exit /b 1
)

REM Run migrations
alembic upgrade head
if %errorlevel%==0 (
    call :log_success "Database migrations completed successfully"
) else (
    call :log_error "Database migration failed"
    exit /b 1
)
goto :eof

REM Create new migration
:create_migration
if "%~1"=="" (
    call :log_error "Migration message is required"
    echo Usage: %0 create-migration "Migration description"
    exit /b 1
)

call :log_info "Creating new migration: %~1"

cd /d "%BACKEND_DIR%"

alembic revision --autogenerate -m "%~1"
if %errorlevel%==0 (
    call :log_success "Migration created successfully"
    call :log_info "Please review the generated migration file before applying"
) else (
    call :log_error "Migration creation failed"
    exit /b 1
)
goto :eof

REM Check migration status
:check_migration_status
call :log_info "Checking migration status for %ENVIRONMENT% environment..."

cd /d "%BACKEND_DIR%"

call :log_info "Current migration status:"
alembic current

call :log_info "Available migrations:"
alembic history
goto :eof

REM Initialize database
:init_database
call :log_info "Initializing database for %ENVIRONMENT% environment..."

cd /d "%BACKEND_DIR%"

call :run_migrations
call :log_success "Database initialization completed"
goto :eof

REM Show help
:show_help
echo Database Migration and Management Script for Windows
echo.
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   migrate                     Run database migrations
echo   create-migration MESSAGE    Create a new migration
echo   status                      Check migration status
echo   init                        Initialize database (fresh setup)
echo   wait-services              Wait for services to be ready
echo   check-db                   Check database connectivity
echo   help                       Show this help message
echo.
echo Environment Variables:
echo   ENVIRONMENT=development    Set environment (development, staging, production)
echo.
echo Examples:
echo   %0 migrate
echo   %0 create-migration "Add user preferences table"
echo   set ENVIRONMENT=staging && %0 init
goto :eof

REM Main script logic
:main
set command=%1

REM Load environment configuration
call :load_environment

if "%command%"=="migrate" (
    call :wait_for_services
    call :run_migrations
) else if "%command%"=="create-migration" (
    call :create_migration "%~2"
) else if "%command%"=="status" (
    call :check_migration_status
) else if "%command%"=="init" (
    call :wait_for_services
    call :init_database
) else if "%command%"=="wait-services" (
    call :wait_for_services
) else if "%command%"=="check-db" (
    call :check_database
) else if "%command%"=="help" (
    call :show_help
) else if "%command%"=="--help" (
    call :show_help
) else if "%command%"=="-h" (
    call :show_help
) else if "%command%"=="" (
    call :show_help
) else (
    call :log_error "Unknown command: %command%"
    echo.
    call :show_help
    exit /b 1
)

endlocal