#!/bin/bash
# Quick Test Runner for Linux/Mac/WSL
# Usage: ./quick_test.sh

set -e

echo "🚀 CONTENT REPURPOSE - QUICK TESTS"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Run validation
echo "🔍 Validating test framework..."
python3 validate_tests.py

echo ""
echo "🎯 QUICK TEST EXECUTION"
echo "======================="

# Run quick tests
python3 run_tests.py --quick --verbose

echo ""
echo "✅ Quick tests completed!"
echo "💡 For full tests: python3 run_tests.py"