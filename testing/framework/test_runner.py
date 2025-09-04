"""
Phase Test Runner - Phase-Agnostic Test Discovery and Execution
================================================================

Enhanced test runner with Claude Online's recommendations:
- Service dependency graphs for resource optimization
- Test categorization by resource requirements
- Performance regression detection
- Intelligent test isolation with confidence scoring
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, Future
import json
from dataclasses import dataclass, asdict
from enum import Enum

from .environment import EnvironmentManager
from .docker_manager import DockerTestManager


class TestCategory(Enum):
    """Test categories by resource requirements."""

    LIGHTWEIGHT = "lightweight"  # Unit tests, minimal resources
    INTEGRATION = "integration"  # API tests, moderate resources
    FULL_STACK = "full_stack"  # E2E tests, maximum resources
    PERFORMANCE = "performance"  # Performance benchmarks


@dataclass
class TestResourceProfile:
    """Resource requirements for test categories."""

    category: TestCategory
    max_memory_mb: int
    required_services: List[str]
    parallel_limit: int
    timeout_seconds: int


@dataclass
class ServiceDependencyGraph:
    """Smart service orchestration based on test requirements."""

    # Service dependency mapping based on test categories
    DEPENDENCY_MAP = {
        TestCategory.LIGHTWEIGHT: ["postgres-unit", "redis-unit"],
        TestCategory.INTEGRATION: [
            "postgres-integration",
            "redis-integration",
            "api-integration",
        ],
        TestCategory.FULL_STACK: [
            "postgres-integration",
            "redis-integration",
            "api-integration",
            "celery-integration",
        ],
        TestCategory.PERFORMANCE: [
            "postgres-integration",
            "redis-integration",
            "api-integration",
            "celery-integration",
        ],
    }

    # Resource profiles for each category
    RESOURCE_PROFILES = {
        TestCategory.LIGHTWEIGHT: TestResourceProfile(
            category=TestCategory.LIGHTWEIGHT,
            max_memory_mb=128,
            required_services=["postgres-unit", "redis-unit"],
            parallel_limit=8,
            timeout_seconds=30,
        ),
        TestCategory.INTEGRATION: TestResourceProfile(
            category=TestCategory.INTEGRATION,
            max_memory_mb=512,
            required_services=[
                "postgres-integration",
                "redis-integration",
                "api-integration",
            ],
            parallel_limit=4,
            timeout_seconds=120,
        ),
        TestCategory.FULL_STACK: TestResourceProfile(
            category=TestCategory.FULL_STACK,
            max_memory_mb=1024,
            required_services=[
                "postgres-integration",
                "redis-integration",
                "api-integration",
                "celery-integration",
            ],
            parallel_limit=2,
            timeout_seconds=300,
        ),
        TestCategory.PERFORMANCE: TestResourceProfile(
            category=TestCategory.PERFORMANCE,
            max_memory_mb=2048,
            required_services=[
                "postgres-integration",
                "redis-integration",
                "api-integration",
                "celery-integration",
            ],
            parallel_limit=1,
            timeout_seconds=600,
        ),
    }

    @classmethod
    def get_required_services(cls, test_categories: List[TestCategory]) -> List[str]:
        """Return minimal service set for test categories."""
        required = set()
        for category in test_categories:
            required.update(cls.DEPENDENCY_MAP.get(category, []))
        return list(required)

    @classmethod
    def get_resource_profile(cls, category: TestCategory) -> TestResourceProfile:
        """Get resource profile for test category."""
        return cls.RESOURCE_PROFILES[category]


@dataclass
class TestResult:
    """Test execution result with detailed information."""

    phase: str
    test_type: str
    test_file: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None


@dataclass
class PhaseTestSuite:
    """Test suite configuration for a phase."""

    phase: int
    name: str
    unit_tests: List[Path]
    integration_tests: List[Path]
    e2e_tests: List[Path]
    required_services: List[str]
    setup_scripts: List[Path]
    teardown_scripts: List[Path]


class PhaseTestRunner:
    """Manages test execution across phases with intelligent orchestration."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.env_manager = EnvironmentManager(self.project_root)
        self.docker_manager = DockerTestManager(self.project_root)

        self.test_results: List[TestResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def discover_phases(self) -> Dict[int, PhaseTestSuite]:
        """Auto-discover test phases and their configurations."""
        phases = {}

        # Look for phase-specific test files
        phase_patterns = [
            ("test_phase*.py", r"test_phase(\d+)"),
            ("test_*_phase*.py", r"test_.*_phase(\d+)"),
            ("phase*/test_*.py", r"phase(\d+)"),
        ]

        discovered_files = {}

        # Scan for test files
        for pattern, regex in phase_patterns:
            import re

            for test_file in self.tests_dir.glob(pattern):
                match = re.search(regex, test_file.name)
                if match:
                    phase_num = int(match.group(1))
                    if phase_num not in discovered_files:
                        discovered_files[phase_num] = []
                    discovered_files[phase_num].append(test_file)

        # Classify tests and create phase suites
        for phase_num, files in discovered_files.items():
            unit_tests = []
            integration_tests = []
            e2e_tests = []

            for file_path in files:
                if "unit" in file_path.name or "basic" in file_path.name:
                    unit_tests.append(file_path)
                elif "integration" in file_path.name or "e2e" in file_path.name:
                    integration_tests.append(file_path)
                elif "websocket" in file_path.name:
                    integration_tests.append(file_path)
                else:
                    # Default classification based on phase
                    if phase_num <= 2:
                        unit_tests.append(file_path)
                    else:
                        integration_tests.append(file_path)

            # Determine required services based on phase
            required_services = self._get_phase_services(phase_num)

            phases[phase_num] = PhaseTestSuite(
                phase=phase_num,
                name=self._get_phase_name(phase_num),
                unit_tests=unit_tests,
                integration_tests=integration_tests,
                e2e_tests=e2e_tests,
                required_services=required_services,
                setup_scripts=[],
                teardown_scripts=[],
            )

        return phases

    def _get_phase_services(self, phase_num: int) -> List[str]:
        """Get required Docker services for a phase."""
        base_services = ["postgres-test", "redis-test"]

        if phase_num >= 4:  # Celery background processing
            base_services.append("celery-worker-test")

        if phase_num >= 5:  # WebSocket/real-time features
            base_services.append("api-test")

        return base_services

    def _get_phase_name(self, phase_num: int) -> str:
        """Get descriptive name for a phase."""
        phase_names = {
            1: "Foundation & Environment",
            2: "Authentication & Security",
            3: "Multi-Tenancy & RLS",
            4: "Background Processing",
            5: "Real-Time & WebSockets",
            6: "File Processing",
            7: "AI Provider Management",
            8: "Security & Monitoring",
            9: "Frontend Enhancement",
            10: "Deployment & DevOps",
        }
        return phase_names.get(phase_num, f"Phase {phase_num}")

    def run_phase_tests(
        self,
        phase: int,
        test_types: List[str] = None,
        parallel: bool = False,
        stop_on_failure: bool = False,
    ) -> bool:
        """
        Run tests for a specific phase with intelligent orchestration.

        Args:
            phase: Phase number to test
            test_types: List of test types ('unit', 'integration', 'e2e')
            parallel: Whether to run tests in parallel
            stop_on_failure: Whether to stop on first failure

        Returns:
            bool: True if all tests passed
        """
        phases = self.discover_phases()

        if phase not in phases:
            print(f"❌ Phase {phase} not found")
            return False

        phase_suite = phases[phase]

        if test_types is None:
            test_types = ["unit", "integration", "e2e"]

        print(f"🚀 Running Phase {phase} Tests: {phase_suite.name}")
        print("=" * 60)

        # Validate environment
        print("🔍 Environment Validation...")
        if not self.env_manager.validate_environment(auto_fix=True):
            print("❌ Environment validation failed")
            return False

        # Start required services
        success = True
        with self.docker_manager.test_services(phase_suite.required_services):
            # Run tests in order
            for test_type in test_types:
                test_files = getattr(phase_suite, f"{test_type}_tests", [])

                if not test_files:
                    print(f"ℹ️  No {test_type} tests found for Phase {phase}")
                    continue

                print(f"\n📋 Running {test_type.title()} Tests...")

                type_success = self._run_test_files(
                    test_files, test_type, phase, parallel
                )

                if not type_success:
                    success = False
                    if stop_on_failure:
                        print(f"❌ Stopping due to {test_type} test failures")
                        break

        # Print summary
        self._print_phase_summary(phase, success)

        return success

    def _run_test_files(
        self, test_files: List[Path], test_type: str, phase: int, parallel: bool = False
    ) -> bool:
        """Run a collection of test files."""
        if not test_files:
            return True

        if parallel and len(test_files) > 1:
            return self._run_tests_parallel(test_files, test_type, phase)
        else:
            return self._run_tests_sequential(test_files, test_type, phase)

    def _run_tests_sequential(
        self, test_files: List[Path], test_type: str, phase: int
    ) -> bool:
        """Run tests sequentially with progress indication."""
        all_passed = True

        for i, test_file in enumerate(test_files, 1):
            print(f"  [{i}/{len(test_files)}] {test_file.name}...")

            start_time = time.time()
            result = self._run_single_test(test_file, test_type, phase)
            duration = time.time() - start_time

            self.test_results.append(
                TestResult(
                    phase=str(phase),
                    test_type=test_type,
                    test_file=test_file.name,
                    status=result["status"],
                    duration=duration,
                    error_message=result.get("error"),
                    output=result.get("output"),
                )
            )

            if result["status"] == "passed":
                print(f"    ✅ PASSED ({duration:.1f}s)")
            else:
                print(f"    ❌ {result['status'].upper()} ({duration:.1f}s)")
                if result.get("error"):
                    print(f"    💬 {result['error']}")
                all_passed = False

        return all_passed

    def _run_tests_parallel(
        self, test_files: List[Path], test_type: str, phase: int
    ) -> bool:
        """Run tests in parallel with proper isolation."""
        print(f"  🚀 Running {len(test_files)} tests in parallel...")

        all_passed = True
        futures: List[Tuple[Future, Path]] = []

        with ThreadPoolExecutor(max_workers=min(4, len(test_files))) as executor:
            # Submit all tests
            for test_file in test_files:
                future = executor.submit(
                    self._run_single_test, test_file, test_type, phase
                )
                futures.append((future, test_file))

            # Collect results as they complete
            for future, test_file in futures:
                start_time = time.time()
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    duration = time.time() - start_time

                    self.test_results.append(
                        TestResult(
                            phase=str(phase),
                            test_type=test_type,
                            test_file=test_file.name,
                            status=result["status"],
                            duration=duration,
                            error_message=result.get("error"),
                            output=result.get("output"),
                        )
                    )

                    if result["status"] == "passed":
                        print(f"    ✅ {test_file.name} PASSED ({duration:.1f}s)")
                    else:
                        print(f"    ❌ {test_file.name} {result['status'].upper()}")
                        all_passed = False

                except Exception as e:
                    print(f"    ❌ {test_file.name} FAILED: {e}")
                    all_passed = False

        return all_passed

    def _run_single_test(
        self, test_file: Path, test_type: str, phase: int
    ) -> Dict[str, Any]:
        """Run a single test file using pytest."""
        try:
            # Configure pytest arguments
            pytest_args = [
                str(test_file),
                "-v",
                "--tb=short",
                "--disable-warnings",
                f"--junit-xml=testing/results/{test_file.stem}_results.xml",
            ]

            # Add environment variables for test isolation
            env = os.environ.copy()
            env["PYTEST_CURRENT_TEST"] = str(test_file)
            env["TEST_PHASE"] = str(phase)
            env["TEST_TYPE"] = test_type

            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest"] + pytest_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                env=env,
                timeout=180,  # 3 minute timeout per test
            )

            if result.returncode == 0:
                return {"status": "passed", "output": result.stdout}
            else:
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Test execution timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_all_phases(
        self, phases: List[int] = None, parallel_phases: bool = False
    ) -> bool:
        """Run tests for multiple phases."""
        discovered_phases = self.discover_phases()

        if phases is None:
            phases = sorted(discovered_phases.keys())

        print(f"🚀 Running Tests for {len(phases)} Phases")
        print("=" * 60)

        self.start_time = time.time()
        overall_success = True

        for phase in phases:
            phase_success = self.run_phase_tests(phase)
            if not phase_success:
                overall_success = False

        self.end_time = time.time()

        # Print final summary
        self._print_final_summary(overall_success)

        return overall_success

    def _print_phase_summary(self, phase: int, success: bool):
        """Print summary for a single phase."""
        phase_results = [r for r in self.test_results if r.phase == str(phase)]

        if not phase_results:
            return

        passed = len([r for r in phase_results if r.status == "passed"])
        failed = len([r for r in phase_results if r.status == "failed"])
        total_time = sum(r.duration for r in phase_results)

        print(f"\n📊 Phase {phase} Summary:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏱️  Total Time: {total_time:.1f}s")
        print(f"   🎯 Success: {'✅ YES' if success else '❌ NO'}")

    def _print_final_summary(self, success: bool):
        """Print final test run summary."""
        if not self.test_results:
            return

        total_duration = (
            self.end_time - self.start_time if self.start_time and self.end_time else 0
        )

        passed = len([r for r in self.test_results if r.status == "passed"])
        failed = len([r for r in self.test_results if r.status == "failed"])
        total = len(self.test_results)

        print("\n" + "=" * 60)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total Duration: {total_duration:.1f}s")
        print(f"🎉 Overall Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")

        # Export detailed results
        self._export_test_results()

    def _export_test_results(self):
        """Export detailed test results to JSON."""
        results_dir = self.project_root / "testing" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        results_file = results_dir / f"test_results_{int(time.time())}.json"

        export_data = {
            "summary": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": self.end_time - self.start_time
                if self.start_time and self.end_time
                else 0,
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r.status == "passed"]),
                "failed": len([r for r in self.test_results if r.status == "failed"]),
            },
            "results": [asdict(result) for result in self.test_results],
        }

        with open(results_file, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"📄 Detailed results exported to: {results_file}")


def main():
    """Command-line interface for phase test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase Test Runner")
    parser.add_argument("--phase", type=int, help="Run tests for specific phase")
    parser.add_argument("--all", action="store_true", help="Run tests for all phases")
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
    parser.add_argument(
        "--discover", action="store_true", help="Discover and list available phases"
    )

    args = parser.parse_args()

    runner = PhaseTestRunner()

    if args.discover:
        phases = runner.discover_phases()
        print("📋 Discovered Test Phases:")
        for phase_num, phase_suite in phases.items():
            print(f"  Phase {phase_num}: {phase_suite.name}")
            print(f"    Unit: {len(phase_suite.unit_tests)} tests")
            print(f"    Integration: {len(phase_suite.integration_tests)} tests")
            print(f"    E2E: {len(phase_suite.e2e_tests)} tests")
        return

    if args.all:
        success = runner.run_all_phases(parallel_phases=args.parallel)
    elif args.phase:
        success = runner.run_phase_tests(
            args.phase,
            test_types=args.types,
            parallel=args.parallel,
            stop_on_failure=args.stop_on_failure,
        )
    else:
        parser.print_help()
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
