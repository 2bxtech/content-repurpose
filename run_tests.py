#!/usr/bin/env python3
"""
Production-Ready Automated Testing Framework
Simple, Direct, Flexible, and Maintainable

Usage Examples:
    python run_tests.py                    # Full automated test suite
    python run_tests.py --quick           # Quick validation tests
    python run_tests.py --setup-only      # Setup test environment
    python run_tests.py --unit            # Unit tests only
    python run_tests.py --integration     # Integration tests only
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
import requests

# ========================================
# CONFIGURATION - Single Source of Truth
# ========================================

class TestConfig:
    """Centralized test configuration"""
    
    # URLs and Ports
    API_URL = "http://localhost:8002"
    DB_URL = "postgresql://postgres:test_password@localhost:5434/content_repurpose_test"
    REDIS_URL = "redis://localhost:6380"
    
    # Docker Configuration
    COMPOSE_FILE = "docker-compose.test.yml"
    PROJECT_NAME = "content-repurpose-test"
    
    # Test Categories
    UNIT_TESTS = ["tests/test_basic.py::TestUtilities"]
    INTEGRATION_TESTS = [
        "tests/test_basic.py::TestAPIHealth",
        "tests/test_basic.py::TestAuthentication"
    ]
    E2E_TESTS = ["tests/test_basic.py::TestContentTransformation"]
    QUICK_TESTS = UNIT_TESTS + ["tests/test_basic.py::TestAPIHealth::test_api_health"]
    
    # Timeouts
    HEALTH_CHECK_TIMEOUT = 60
    SERVICE_START_TIMEOUT = 120


class TestAutomationSuite:
    """
    Enterprise-grade test automation suite with Docker orchestration
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_env_ready = False
        self.test_results = {}
        self.start_time = None
        
    def print_banner(self):
        """Print test suite banner"""
        print("=" * 80)
        print("🚀 CONTENT REPURPOSE - AUTOMATED TEST SUITE")
        print("   Enterprise-Grade Testing Framework")
        print("=" * 80)
        print(f"📁 Project Root: {self.project_root}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def setup_test_environment(self) -> bool:
        """Set up Docker test environment"""
        print("\n🐳 SETTING UP TEST ENVIRONMENT")
        print("-" * 50)
        
        try:
            # Check Docker availability
            print("🔍 Checking Docker availability...")
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Docker: {result.stdout.strip()}")
            
            # Check Docker Compose availability
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Docker Compose: {result.stdout.strip()}")
            
            # Clean up any existing test containers
            print("🧹 Cleaning up existing test containers...")
            subprocess.run([
                "docker-compose",
                "-f", "docker-compose.test.yml",
                "-p", "content-repurpose-test",
                "down", "-v", "--remove-orphans"
            ], capture_output=True, cwd=self.project_root)
            
            # Start test environment
            print("🚀 Starting test services...")
            result = subprocess.run([
                "docker-compose",
                "-f", "docker-compose.test.yml", 
                "-p", "content-repurpose-test",
                "up", "-d", "--build", "--force-recreate"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print(f"❌ Failed to start test services:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
            
            print("✅ Test services started successfully")
            
            # Wait for services to be healthy
            print("⏳ Waiting for services to be healthy...")
            if not self.wait_for_services_healthy():
                print("❌ Services failed to become healthy")
                return False
            
            print("✅ All test services are healthy and ready")
            self.test_env_ready = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker setup failed: {e}")
            return False
        except FileNotFoundError:
            print("❌ Docker or Docker Compose not found. Please install Docker.")
            return False
    
    def wait_for_services_healthy(self, timeout: int = 120) -> bool:
        """Wait for all services to be healthy"""
        import requests
        
        services = [
            ("API", "http://localhost:8002/api/health"),
            ("Detailed Health", "http://localhost:8002/api/health/detailed")
        ]
        
        print("🔍 Checking service health...")
        
        for attempt in range(timeout // 5):
            all_healthy = True
            
            for service_name, url in services:
                try:
                    response = requests.get(url, timeout=3)
                    if response.status_code == 200:
                        print(f"   ✅ {service_name}: Healthy")
                    else:
                        print(f"   ⚠️  {service_name}: Status {response.status_code}")
                        all_healthy = False
                except Exception as e:
                    print(f"   ❌ {service_name}: {str(e)[:50]}...")
                    all_healthy = False
            
            if all_healthy:
                return True
            
            if attempt < (timeout // 5) - 1:
                print(f"   ⏳ Waiting... (attempt {attempt + 1}/{timeout // 5})")
                time.sleep(5)
        
        return False
    
    def run_tests(self, test_args: List[str]) -> bool:
        """Run pytest with specified arguments"""
        print(f"\n🧪 RUNNING TESTS")
        print("-" * 50)
        
        if not self.test_env_ready:
            print("❌ Test environment not ready. Run setup first.")
            return False
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"] + test_args
        
        print(f"📋 Command: {' '.join(cmd)}")
        print("🏃 Executing tests...")
        
        self.start_time = time.time()
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                text=True
            )
            
            execution_time = time.time() - self.start_time
            
            # Store results
            self.test_results = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "execution_time": execution_time
            }
            
            print(f"\n⏱️  Test execution completed in {execution_time:.2f} seconds")
            
            if result.returncode == 0:
                print("✅ ALL TESTS PASSED!")
                return True
            else:
                print(f"❌ Tests failed with return code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print(f"\n📊 GENERATING TEST REPORT")
        print("-" * 50)
        
        # Check for generated reports
        reports = {
            "HTML Report": self.project_root / "tests" / "report.html",
            "Coverage Report": self.project_root / "tests" / "coverage_html" / "index.html",
            "JSON Report": self.project_root / "tests" / "report.json",
            "Coverage XML": self.project_root / "tests" / "coverage.xml"
        }
        
        available_reports = []
        for report_name, report_path in reports.items():
            if report_path.exists():
                available_reports.append((report_name, report_path))
                print(f"✅ {report_name}: {report_path}")
            else:
                print(f"⚠️  {report_name}: Not generated")
        
        if available_reports:
            print(f"\n📋 Available reports: {len(available_reports)}")
            for report_name, report_path in available_reports:
                if report_name == "HTML Report":
                    print(f"🌐 Open in browser: file://{report_path.absolute()}")
                elif report_name == "Coverage Report":
                    print(f"📈 Coverage report: file://{report_path.absolute()}")
        
        # Try to parse JSON report for summary
        json_report_path = reports["JSON Report"]
        if json_report_path.exists():
            try:
                with open(json_report_path) as f:
                    report_data = json.load(f)
                
                summary = report_data.get("summary", {})
                print(f"\n📈 TEST SUMMARY:")
                print(f"   Total: {summary.get('total', 0)}")
                print(f"   Passed: {summary.get('passed', 0)}")
                print(f"   Failed: {summary.get('failed', 0)}")
                print(f"   Skipped: {summary.get('skipped', 0)}")
                print(f"   Duration: {summary.get('duration', 0):.2f}s")
                
            except Exception as e:
                print(f"⚠️  Could not parse JSON report: {e}")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print(f"\n🧹 CLEANING UP TEST ENVIRONMENT")
        print("-" * 50)
        
        try:
            result = subprocess.run([
                "docker-compose",
                "-f", "docker-compose.test.yml",
                "-p", "content-repurpose-test", 
                "down", "-v", "--remove-orphans"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Test environment cleaned up successfully")
            else:
                print("⚠️  Cleanup completed with warnings")
                
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
    
    def print_summary(self):
        """Print final test summary"""
        print(f"\n🎯 FINAL SUMMARY")
        print("=" * 50)
        
        if self.test_results:
            success = self.test_results["success"]
            execution_time = self.test_results.get("execution_time", 0)
            
            status_icon = "✅" if success else "❌"
            status_text = "PASSED" if success else "FAILED"
            
            print(f"{status_icon} Test Status: {status_text}")
            print(f"⏱️  Execution Time: {execution_time:.2f} seconds")
            print(f"🐳 Test Environment: Docker Compose")
            print(f"📊 Reports Available: Yes")
            
            if success:
                print(f"\n🎉 All tests completed successfully!")
                print(f"   The application is ready for deployment.")
            else:
                print(f"\n⚠️  Some tests failed. Please review the results.")
                print(f"   Check the HTML report for detailed information.")
        else:
            print("⚠️  No test results available")


def build_pytest_args(args: argparse.Namespace) -> List[str]:
    """Build pytest command arguments based on user options"""
    pytest_args = []
    
    # Test selection
    if args.unit:
        pytest_args.extend(["-m", "unit"])
    elif args.integration:
        pytest_args.extend(["-m", "integration"])
    elif args.e2e:
        pytest_args.extend(["-m", "e2e"])
    elif args.quick:
        pytest_args.extend(["-m", "unit or integration"])
    # Default: run all tests (no marker filter)
    
    # Parallel execution
    if args.parallel:
        pytest_args.extend(["-n", "auto"])
    
    # Verbose output
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    # Coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=backend/app",
            "--cov-report=term-missing",
            "--cov-report=html:tests/coverage_html"
        ])
    
    # HTML report
    if args.html_report:
        pytest_args.extend([
            "--html=tests/report.html",
            "--self-contained-html"
        ])
    
    # JSON report (always generate for summary)
    pytest_args.extend([
        "--json-report",
        "--json-report-file=tests/report.json"
    ])
    
    # Test directory
    pytest_args.append("tests/")
    
    return pytest_args


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="Content Repurpose Automated Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--quick", action="store_true", 
                           help="Run only fast tests (unit + integration)")
    test_group.add_argument("--full", action="store_true", 
                           help="Run all tests including end-to-end (default)")
    test_group.add_argument("--unit", action="store_true", 
                           help="Run only unit tests")
    test_group.add_argument("--integration", action="store_true", 
                           help="Run only integration tests")
    test_group.add_argument("--e2e", action="store_true", 
                           help="Run only end-to-end tests")
    
    # Report options
    parser.add_argument("--coverage", action="store_true", 
                       help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", 
                       help="Generate HTML test report")
    
    # Execution options
    parser.add_argument("--parallel", action="store_true", 
                       help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", 
                       help="Verbose output")
    
    # Environment options
    parser.add_argument("--cleanup", action="store_true", 
                       help="Clean up test environment after run")
    parser.add_argument("--setup-only", action="store_true", 
                       help="Only set up test environment, don't run tests")
    
    args = parser.parse_args()
    
    # Default to full tests if no specific test type selected
    if not any([args.quick, args.unit, args.integration, args.e2e]):
        args.full = True
    
    # Project root
    project_root = Path(__file__).parent
    
    # Initialize test suite
    suite = TestAutomationSuite(project_root)
    suite.print_banner()
    
    try:
        # Set up test environment
        if not suite.setup_test_environment():
            print("❌ Failed to set up test environment")
            return 1
        
        if args.setup_only:
            print("✅ Test environment setup completed. Services are running.")
            print("   API: http://localhost:8002")
            print("   Docs: http://localhost:8002/docs")
            print("   Run tests manually with: python -m pytest tests/")
            return 0
        
        # Build pytest arguments
        pytest_args = build_pytest_args(args)
        
        # Run tests
        success = suite.run_tests(pytest_args)
        
        # Generate reports
        suite.generate_test_report()
        
        # Print summary
        suite.print_summary()
        
        return 0 if success else 1
        
    finally:
        # Cleanup if requested
        if args.cleanup or args.setup_only:
            suite.cleanup_test_environment()


if __name__ == "__main__":
    sys.exit(main())