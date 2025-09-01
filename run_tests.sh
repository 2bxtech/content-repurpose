#!/bin/bash
# Cross-platform test runner script for Unix-like systems
# Provides convenient shortcuts for running different test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_color() {
    printf "${2}${1}${NC}\n"
}

print_banner() {
    echo "=================================================================="
    print_color "🚀 CONTENT REPURPOSE - AUTOMATED TEST SUITE" "$GREEN"
    print_color "   Cross-Platform Test Runner" "$BLUE"
    echo "=================================================================="
}

print_help() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    quick       Run quick tests (unit + integration)
    full        Run all tests including end-to-end
    unit        Run only unit tests
    integration Run only integration tests
    e2e         Run only end-to-end tests
    setup       Set up test environment only
    cleanup     Clean up test environment
    coverage    Run tests with coverage report
    ci          Run tests suitable for CI environment

OPTIONS:
    --parallel  Run tests in parallel
    --verbose   Verbose output
    --html      Generate HTML report
    --help      Show this help message

EXAMPLES:
    $0 quick                    # Quick tests
    $0 full --coverage          # Full tests with coverage
    $0 e2e --verbose            # E2E tests with verbose output
    $0 setup                    # Just set up environment
    $0 ci                       # CI-optimized test run

EOF
}

check_dependencies() {
    print_color "🔍 Checking dependencies..." "$BLUE"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_color "❌ Python 3 is required but not installed" "$RED"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_color "❌ Docker is required but not installed" "$RED"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_color "❌ Docker Compose is required but not installed" "$RED"
        exit 1
    fi
    
    print_color "✅ All dependencies available" "$GREEN"
}

install_test_dependencies() {
    print_color "📦 Installing test dependencies..." "$BLUE"
    
    if [ ! -d ".venv" ]; then
        print_color "Creating virtual environment..." "$YELLOW"
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    pip install -r backend/requirements.txt
    pip install -r tests/requirements-test.txt
    
    print_color "✅ Test dependencies installed" "$GREEN"
}

run_python_tests() {
    local test_args="$1"
    
    # Ensure virtual environment is activated
    if [ ! -f ".venv/bin/activate" ]; then
        install_test_dependencies
    fi
    
    source .venv/bin/activate
    
    # Run Python test runner
    python3 run_tests.py $test_args
}

main() {
    print_banner
    
    local command=""
    local options=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            quick|full|unit|integration|e2e|setup|cleanup|coverage|ci)
                command="$1"
                shift
                ;;
            --parallel|--verbose|--html|--cleanup)
                options="$options $1"
                shift
                ;;
            --help|-h)
                print_help
                exit 0
                ;;
            *)
                print_color "Unknown option: $1" "$RED"
                print_help
                exit 1
                ;;
        esac
    done
    
    # Default command
    if [ -z "$command" ]; then
        command="quick"
    fi
    
    # Check dependencies
    check_dependencies
    
    # Execute command
    case $command in
        quick)
            print_color "🏃 Running quick tests..." "$BLUE"
            run_python_tests "--quick $options"
            ;;
        full)
            print_color "🔬 Running full test suite..." "$BLUE" 
            run_python_tests "--full --coverage --html-report $options"
            ;;
        unit)
            print_color "🧪 Running unit tests..." "$BLUE"
            run_python_tests "--unit $options"
            ;;
        integration)
            print_color "🔗 Running integration tests..." "$BLUE"
            run_python_tests "--integration $options"
            ;;
        e2e)
            print_color "🎭 Running end-to-end tests..." "$BLUE"
            run_python_tests "--e2e $options"
            ;;
        setup)
            print_color "🛠️  Setting up test environment..." "$BLUE"
            run_python_tests "--setup-only"
            ;;
        cleanup)
            print_color "🧹 Cleaning up test environment..." "$BLUE"
            run_python_tests "--cleanup"
            ;;
        coverage)
            print_color "📊 Running tests with coverage..." "$BLUE"
            run_python_tests "--full --coverage --html-report $options"
            ;;
        ci)
            print_color "🤖 Running CI-optimized tests..." "$BLUE"
            run_python_tests "--quick --parallel --coverage $options"
            ;;
        *)
            print_color "Unknown command: $command" "$RED"
            print_help
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_color "🎉 Tests completed successfully!" "$GREEN"
    else
        print_color "❌ Tests failed" "$RED"
    fi
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"