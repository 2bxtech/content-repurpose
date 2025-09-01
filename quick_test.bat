@echo off
REM Quick Test Runner for Windows
REM Usage: quick_test.bat

echo 🚀 CONTENT REPURPOSE - QUICK TESTS
echo ==================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    exit /b 1
)

REM Run validation
echo 🔍 Validating test framework...
python validate_tests.py
if errorlevel 1 (
    echo ❌ Validation failed
    exit /b 1
)

echo.
echo 🎯 QUICK TEST EXECUTION
echo =======================

REM Run quick tests
python run_tests.py --quick --verbose

echo.
echo ✅ Quick tests completed!
echo 💡 For full tests: python run_tests.py