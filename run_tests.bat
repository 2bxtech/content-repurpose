@echo off
REM Windows batch script for running automated tests
REM Provides convenient shortcuts for different test scenarios

setlocal enabledelayedexpansion

REM Colors (limited support in Windows)
set "RED=[31m"
set "GREEN=[32m" 
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:print_banner
echo ==================================================================
echo 🚀 CONTENT REPURPOSE - AUTOMATED TEST SUITE
echo    Windows Test Runner
echo ==================================================================
goto :eof

:print_help
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo COMMANDS:
echo     quick       Run quick tests (unit + integration)
echo     full        Run all tests including end-to-end
echo     unit        Run only unit tests
echo     integration Run only integration tests
echo     e2e         Run only end-to-end tests
echo     setup       Set up test environment only
echo     cleanup     Clean up test environment
echo     coverage    Run tests with coverage report
echo     ci          Run tests suitable for CI environment
echo.
echo OPTIONS:
echo     --parallel  Run tests in parallel
echo     --verbose   Verbose output
echo     --html      Generate HTML report
echo     --help      Show this help message
echo.
echo EXAMPLES:
echo     %0 quick                    # Quick tests
echo     %0 full --coverage          # Full tests with coverage
echo     %0 e2e --verbose            # E2E tests with verbose output
echo     %0 setup                    # Just set up environment
echo     %0 ci                       # CI-optimized test run
echo.
goto :eof

:check_dependencies
echo 🔍 Checking dependencies...

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed
    exit /b 1
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is required but not installed
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is required but not installed
    exit /b 1
)

echo ✅ All dependencies available
goto :eof

:install_test_dependencies
echo 📦 Installing test dependencies...

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
pip install -r backend\requirements.txt
pip install -r tests\requirements-test.txt

echo ✅ Test dependencies installed
goto :eof

:run_python_tests
set "test_args=%~1"

REM Ensure virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    call :install_test_dependencies
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run Python test runner
python run_tests.py %test_args%
goto :eof

:main
call :print_banner

set "command="
set "options="

REM Parse arguments
:parse_args
if "%~1"=="" goto :execute_command

if "%~1"=="quick" set "command=quick" & shift & goto :parse_args
if "%~1"=="full" set "command=full" & shift & goto :parse_args
if "%~1"=="unit" set "command=unit" & shift & goto :parse_args
if "%~1"=="integration" set "command=integration" & shift & goto :parse_args
if "%~1"=="e2e" set "command=e2e" & shift & goto :parse_args
if "%~1"=="setup" set "command=setup" & shift & goto :parse_args
if "%~1"=="cleanup" set "command=cleanup" & shift & goto :parse_args
if "%~1"=="coverage" set "command=coverage" & shift & goto :parse_args
if "%~1"=="ci" set "command=ci" & shift & goto :parse_args
if "%~1"=="--parallel" set "options=!options! --parallel" & shift & goto :parse_args
if "%~1"=="--verbose" set "options=!options! --verbose" & shift & goto :parse_args
if "%~1"=="--html" set "options=!options! --html" & shift & goto :parse_args
if "%~1"=="--help" call :print_help & exit /b 0
if "%~1"=="-h" call :print_help & exit /b 0

echo Unknown option: %~1
call :print_help
exit /b 1

:execute_command
REM Default command
if "%command%"=="" set "command=quick"

REM Check dependencies
call :check_dependencies
if %errorlevel% neq 0 exit /b %errorlevel%

REM Execute command
if "%command%"=="quick" (
    echo 🏃 Running quick tests...
    call :run_python_tests "--quick !options!"
) else if "%command%"=="full" (
    echo 🔬 Running full test suite...
    call :run_python_tests "--full --coverage --html-report !options!"
) else if "%command%"=="unit" (
    echo 🧪 Running unit tests...
    call :run_python_tests "--unit !options!"
) else if "%command%"=="integration" (
    echo 🔗 Running integration tests...
    call :run_python_tests "--integration !options!"
) else if "%command%"=="e2e" (
    echo 🎭 Running end-to-end tests...
    call :run_python_tests "--e2e !options!"
) else if "%command%"=="setup" (
    echo 🛠️  Setting up test environment...
    call :run_python_tests "--setup-only"
) else if "%command%"=="cleanup" (
    echo 🧹 Cleaning up test environment...
    call :run_python_tests "--cleanup"
) else if "%command%"=="coverage" (
    echo 📊 Running tests with coverage...
    call :run_python_tests "--full --coverage --html-report !options!"
) else if "%command%"=="ci" (
    echo 🤖 Running CI-optimized tests...
    call :run_python_tests "--quick --parallel --coverage !options!"
) else (
    echo Unknown command: %command%
    call :print_help
    exit /b 1
)

set "exit_code=%errorlevel%"

if %exit_code% equ 0 (
    echo 🎉 Tests completed successfully!
) else (
    echo ❌ Tests failed
)

exit /b %exit_code%

REM Call main function with all arguments
call :main %*