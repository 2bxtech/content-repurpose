#!/bin/bash

# Simple test runner for all tests
echo "🧪 Running complete test suite..."
echo "================================="

# Change to project root
cd "$(dirname "$0")"

# Run frontend unit tests
echo "📱 Frontend Unit Tests..."
cd frontend
npm test -- --coverage --watchAll=false --passWithNoTests
frontend_exit=$?
cd ..

# Run backend tests  
echo "📡 Backend Tests..."
cd backend
python -m pytest tests/test_integration_comprehensive.py -v
backend_exit=$?
cd ..

# Summary
echo ""
echo "📊 Test Results:"
echo "Frontend: $([ $frontend_exit -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Backend: $([ $backend_exit -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"

if [ $frontend_exit -eq 0 ] && [ $backend_exit -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "💥 Some tests failed!"
    exit 1
fi