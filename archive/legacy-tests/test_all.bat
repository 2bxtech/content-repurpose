@echo off
REM Simple test runner for Windows
echo 🧪 Running complete test suite...
echo =================================

REM Change to project root
cd /d "%~dp0"

REM Run frontend unit tests
echo 📱 Frontend Unit Tests...
cd frontend
call npm test -- --coverage --watchAll=false --passWithNoTests
set frontend_exit=%ERRORLEVEL%
cd ..

REM Run backend tests  
echo 📡 Backend Tests...
cd backend
python -m pytest tests/test_integration_comprehensive.py -v
set backend_exit=%ERRORLEVEL%
cd ..

REM Summary
echo.
echo 📊 Test Results:
if %frontend_exit%==0 (echo Frontend: ✅ PASSED) else (echo Frontend: ❌ FAILED)
if %backend_exit%==0 (echo Backend: ✅ PASSED) else (echo Backend: ❌ FAILED)

if %frontend_exit%==0 if %backend_exit%==0 (
    echo 🎉 All tests passed!
    exit /b 0
) else (
    echo 💥 Some tests failed!
    exit /b 1
)