#!/usr/bin/env python3
"""
Bulletproof Test Runner - Single Entry Point for All Testing
=============================================================

A comprehensive, bulletproof testing framework that handles:
- Automatic environment validation and repair
- Docker service orchestration with health checks
- Phase-agnostic test discovery and execution
- Intelligent error handling and diagnostics
- Developer experience optimization

Usage Examples:
    # Run all tests for Phase 5
    python testing/run_tests.py --phase 5

    # Run all phases with parallel execution
    python testing/run_tests.py --all --parallel

    # Validate environment and auto-fix issues
    python testing/run_tests.py --validate --fix

    # Run comprehensive diagnostics
    python testing/run_tests.py --diagnose --fix

    # Quick validation (fastest)
    python testing/run_tests.py --quick-validate

    # Setup new developer environment
    python testing/run_tests.py --setup-dev
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List

# Add the testing framework to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root / "backend"))

try:
    from framework.environment import EnvironmentManager
    from framework.docker_manager import DockerTestManager
    from framework.test_runner import PhaseTestRunner
    from framework.diagnostics import DiagnosticToolkit
except ImportError as e:
    print(f"❌ Failed to import testing framework: {e}")
    print("💡 Run: pip install -r requirements.txt")
    sys.exit(1)


class BulletproofTestRunner:
    """Main orchestrator for bulletproof testing framework."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent

        # Initialize managers
        print("🔧 Initializing Bulletproof Testing Framework...")
        self.env_manager = EnvironmentManager(self.project_root)
        self.docker_manager = DockerTestManager(self.project_root)
        self.test_runner = PhaseTestRunner(self.project_root)
        self.diagnostics = DiagnosticToolkit(self.project_root)

        self.start_time = time.time()

    def setup_new_developer(self) -> bool:
        """Complete setup for new developer environment."""
        print("🚀 Setting up new developer environment...")
        print("=" * 60)

        # Step 1: Environment validation and auto-fix
        print("Step 1: Environment Validation & Auto-Fix")
        env_valid = self.env_manager.validate_environment(auto_fix=True)
        if not env_valid:
            print("❌ Environment setup failed")
            return False

        # Step 2: Install missing dependencies
        print("\nStep 2: Dependency Installation")
        try:
            self._install_framework_dependencies()
            print("✅ Framework dependencies installed")
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

        # Step 3: Docker validation
        print("\nStep 3: Docker Environment Validation")
        if not self.docker_manager.validate_docker_environment():
            print("❌ Docker not available - please install Docker Desktop")
            return False

        # Step 4: Test Docker services
        print("\nStep 4: Testing Docker Services")
        test_services = ["postgres-test", "redis-test"]
        with self.docker_manager.test_services(test_services, auto_cleanup=True):
            print("✅ Docker services working")

        # Step 5: Run quick validation
        print("\nStep 5: Quick Validation Test")
        quick_success = self._run_quick_validation()

        elapsed = time.time() - self.start_time

        if quick_success:
            print(f"\n🎉 Developer environment setup COMPLETE in {elapsed:.1f}s!")
            print("\n📋 Next steps:")
            print("  • Run tests: python testing/run_tests.py --phase 5")
            print("  • Run diagnostics: python testing/run_tests.py --diagnose")
            print("  • Run all phases: python testing/run_tests.py --all")
            return True
        else:
            print(f"\n⚠️  Setup completed with issues in {elapsed:.1f}s")
            print("💡 Run diagnostics: python testing/run_tests.py --diagnose --fix")
            return False

    def run_quick_validation(self) -> bool:
        """Fast validation of critical components."""
        print("⚡ Quick Validation (optimized for speed)")
        print("=" * 50)

        checks = [
            ("Python Environment", self._quick_check_python),
            ("Critical Imports", self._quick_check_imports),
            ("Docker Availability", self._quick_check_docker),
        ]

        all_passed = True

        for check_name, check_func in checks:
            print(f"🔍 {check_name}...", end=" ")
            try:
                if check_func():
                    print("✅")
                else:
                    print("❌")
                    all_passed = False
            except Exception as e:
                print(f"❌ ({e})")
                all_passed = False

        elapsed = time.time() - self.start_time

        if all_passed:
            print(f"\n🎉 Quick validation PASSED in {elapsed:.1f}s")
        else:
            print(f"\n⚠️  Quick validation FAILED in {elapsed:.1f}s")
            print(
                "💡 Run full validation: python testing/run_tests.py --validate --fix"
            )

        return all_passed

    def run_comprehensive_validation(self, auto_fix: bool = False) -> bool:
        """Comprehensive environment validation with optional auto-fix."""
        print("🔍 Comprehensive Environment Validation")
        print("=" * 60)

        # Run environment validation
        env_valid = self.env_manager.validate_environment(auto_fix=auto_fix)

        # Run diagnostics
        print("\n🔬 Running System Diagnostics...")
        diag_healthy = self.diagnostics.run_comprehensive_diagnostics(auto_fix=auto_fix)

        overall_success = env_valid and diag_healthy
        elapsed = time.time() - self.start_time

        if overall_success:
            print(f"\n🎉 Comprehensive validation PASSED in {elapsed:.1f}s")
        else:
            print(f"\n⚠️  Validation completed with issues in {elapsed:.1f}s")
            if not auto_fix:
                print("💡 Run with --fix to automatically resolve issues")

        return overall_success

    def run_phase_tests(
        self,
        phase: int,
        test_types: List[str] = None,
        parallel: bool = False,
        stop_on_failure: bool = False,
    ) -> bool:
        """Run tests for a specific phase with full orchestration."""
        print(f"🚀 Running Phase {phase} Tests with Bulletproof Framework")
        print("=" * 60)

        # Pre-flight validation
        print("🔍 Pre-flight validation...")
        if not self._run_quick_validation():
            print("❌ Pre-flight validation failed")
            return False

        # Run the phase tests
        success = self.test_runner.run_phase_tests(
            phase=phase,
            test_types=test_types,
            parallel=parallel,
            stop_on_failure=stop_on_failure,
        )

        elapsed = time.time() - self.start_time

        if success:
            print(f"\n🎉 Phase {phase} tests PASSED in {elapsed:.1f}s")
        else:
            print(f"\n❌ Phase {phase} tests FAILED in {elapsed:.1f}s")
            print("💡 Run diagnostics: python testing/run_tests.py --diagnose")

        return success

    def run_all_phases(self, parallel_phases: bool = False) -> bool:
        """Run tests for all discovered phases."""
        print("🚀 Running ALL Phase Tests with Bulletproof Framework")
        print("=" * 60)

        # Pre-flight validation
        print("🔍 Pre-flight validation...")
        if not self._run_quick_validation():
            print("❌ Pre-flight validation failed")
            return False

        # Discover phases
        phases = self.test_runner.discover_phases()
        phase_numbers = sorted(phases.keys())

        print(f"📋 Discovered {len(phase_numbers)} phases: {phase_numbers}")

        # Run all phases
        success = self.test_runner.run_all_phases(
            phases=phase_numbers, parallel_phases=parallel_phases
        )

        elapsed = time.time() - self.start_time

        if success:
            print(f"\n🎉 ALL phases PASSED in {elapsed:.1f}s")
        else:
            print(f"\n❌ Some phases FAILED in {elapsed:.1f}s")

        return success

    def _install_framework_dependencies(self):
        """Install framework dependencies that might be missing."""
        framework_deps = [
            "docker",  # Docker Python SDK
            "psutil",  # System monitoring
            "pyyaml",  # YAML parsing
        ]

        missing_deps = []

        for dep in framework_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)

        if missing_deps:
            print(f"Installing missing framework dependencies: {missing_deps}")
            import subprocess

            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + missing_deps, check=True
            )

    def _run_quick_validation(self) -> bool:
        """Internal quick validation helper."""
        return (
            self._quick_check_python()
            and self._quick_check_imports()
            and self._quick_check_docker()
        )

    def _quick_check_python(self) -> bool:
        """Quick Python environment check."""
        return (
            sys.version_info >= (3, 9)
            and str(self.project_root / "backend") in sys.path
        )

    def _quick_check_imports(self) -> bool:
        """Quick check of critical imports."""
        critical_modules = ["fastapi", "pytest"]

        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                return False
        return True

    def _quick_check_docker(self) -> bool:
        """Quick Docker availability check."""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "--version"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


def main():
    """Command-line interface for bulletproof test runner."""
    parser = argparse.ArgumentParser(
        description="Bulletproof Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python testing/run_tests.py --phase 5                    # Run Phase 5 tests
    python testing/run_tests.py --all --parallel             # Run all phases in parallel
    python testing/run_tests.py --validate --fix             # Validate and auto-fix
    python testing/run_tests.py --quick-validate             # Quick validation
    python testing/run_tests.py --setup-dev                  # New developer setup
    python testing/run_tests.py --diagnose --fix             # Comprehensive diagnostics
        """,
    )

    # Action groups
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--phase", type=int, help="Run tests for specific phase")
    action_group.add_argument(
        "--all", action="store_true", help="Run tests for all phases"
    )
    action_group.add_argument(
        "--validate", action="store_true", help="Comprehensive environment validation"
    )
    action_group.add_argument(
        "--quick-validate", action="store_true", help="Quick validation (fastest)"
    )
    action_group.add_argument(
        "--diagnose", action="store_true", help="Run comprehensive diagnostics"
    )
    action_group.add_argument(
        "--setup-dev", action="store_true", help="Setup new developer environment"
    )

    # Test configuration
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["unit", "integration", "e2e"],
        help="Test types to run",
    )
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument(
        "--stop-on-failure", action="store_true", help="Stop on first failure"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix detected issues")

    # Framework options
    parser.add_argument(
        "--no-docker", action="store_true", help="Skip Docker-based tests"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize the bulletproof runner
    try:
        runner = BulletproofTestRunner()
    except Exception as e:
        print(f"❌ Failed to initialize test runner: {e}")
        sys.exit(1)

    # Execute the requested action
    success = False

    try:
        if args.setup_dev:
            success = runner.setup_new_developer()

        elif args.quick_validate:
            success = runner.run_quick_validation()

        elif args.validate:
            success = runner.run_comprehensive_validation(auto_fix=args.fix)

        elif args.diagnose:
            success = runner.diagnostics.run_comprehensive_diagnostics(
                auto_fix=args.fix
            )

        elif args.phase:
            success = runner.run_phase_tests(
                phase=args.phase,
                test_types=args.types,
                parallel=args.parallel,
                stop_on_failure=args.stop_on_failure,
            )

        elif args.all:
            success = runner.run_all_phases(parallel_phases=args.parallel)

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        success = False

    # Exit with appropriate code
    elapsed = time.time() - runner.start_time
    print(f"\n⏱️  Total execution time: {elapsed:.1f}s")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
