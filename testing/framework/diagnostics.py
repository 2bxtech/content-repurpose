"""
Diagnostic Toolkit - Intelligent Error Handling and Root Cause Analysis
========================================================================

Provides automated diagnostics for common development and testing issues:
- Root cause analysis with actionable solutions
- Self-fixing capabilities for known issues
- Performance monitoring and regression detection
- Integration health checks
- Developer-friendly error explanations
"""

import os
import sys
import subprocess
import time
import psutil
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, asdict


class DiagnosticConfidence:
    """Confidence levels for diagnostic results."""

    HIGH = 0.9  # Auto-apply fixes (e.g., missing __init__.py files)
    MEDIUM = 0.7  # Prompt with recommendation (e.g., package updates)
    LOW = 0.4  # Show diagnostic only (e.g., performance suggestions)


@dataclass
class DiagnosticIssue:
    """Represents a diagnostic issue with metadata and confidence scoring."""

    category: str
    severity: str  # 'critical', 'warning', 'info'
    title: str
    description: str
    symptoms: List[str]
    root_cause: str
    solution: str
    auto_fixable: bool
    confidence: float  # 0.0 to 1.0 confidence score
    fix_command: Optional[str] = None

    def __post_init__(self):
        """Validate confidence score and determine fix behavior."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

        # Override auto_fixable based on confidence
        self.auto_fixable = self.confidence >= DiagnosticConfidence.HIGH
        self.prompt_fix = (
            DiagnosticConfidence.MEDIUM <= self.confidence < DiagnosticConfidence.HIGH
        )
        self.info_only = self.confidence < DiagnosticConfidence.MEDIUM


class DiagnosticToolkit:
    """Comprehensive diagnostic and troubleshooting toolkit."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.issues_found: List[DiagnosticIssue] = []
        self.system_info: Dict[str, Any] = {}

    def run_comprehensive_diagnostics(self, auto_fix: bool = False) -> bool:
        """
        Run comprehensive system diagnostics.

        Args:
            auto_fix: Whether to automatically fix detected issues

        Returns:
            bool: True if all checks pass or are successfully fixed
        """
        print("🔬 Running Comprehensive Diagnostics")
        print("=" * 50)

        # Collect system information
        self._collect_system_info()

        # Run diagnostic checks
        diagnostic_checks = [
            ("Port Conflicts", self._diagnose_port_conflicts),
            ("Docker Issues", self._diagnose_docker_issues),
            ("Database Connectivity", self._diagnose_database_issues),
            ("Redis Connectivity", self._diagnose_redis_issues),
            ("Python Environment", self._diagnose_python_environment),
            ("Import Resolution", self._diagnose_import_issues),
            ("Performance Issues", self._diagnose_performance_issues),
            ("Security Configuration", self._diagnose_security_config),
        ]

        all_healthy = True

        for check_name, check_func in diagnostic_checks:
            print(f"\n🔍 {check_name}...")
            try:
                issues = check_func()
                if issues:
                    print(f"  ⚠️  Found {len(issues)} issues")
                    self.issues_found.extend(issues)

                    if auto_fix:
                        fixed = self._auto_fix_issues(issues)
                        if fixed == len(issues):
                            print("  ✅ All issues auto-fixed")
                        else:
                            print(f"  ⚠️  {fixed}/{len(issues)} issues auto-fixed")
                            all_healthy = False
                    else:
                        all_healthy = False
                else:
                    print(f"  ✅ {check_name}: All clear")

            except Exception as e:
                print(f"  ❌ Diagnostic error: {e}")
                all_healthy = False

        # Print summary
        self._print_diagnostic_summary(auto_fix)

        return all_healthy

    def _collect_system_info(self):
        """Collect comprehensive system information."""
        self.system_info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "project_root": str(self.project_root),
            "memory_usage": psutil.virtual_memory()._asdict(),
            "cpu_count": psutil.cpu_count(),
            "disk_usage": psutil.disk_usage(str(self.project_root))._asdict(),
            "environment_variables": {
                k: "[REDACTED]"
                if any(
                    secret in k.lower()
                    for secret in ["key", "secret", "password", "token"]
                )
                else v
                for k, v in os.environ.items()
            },
        }

    def _diagnose_port_conflicts(self) -> List[DiagnosticIssue]:
        """Diagnose port conflicts that affect services."""
        issues = []

        # Standard ports used by the application
        required_ports = {
            8000: "FastAPI API Server",
            5433: "PostgreSQL Database",
            6379: "Redis Cache",
            5434: "PostgreSQL Test Database",
            6380: "Redis Test Instance",
        }

        for port, service in required_ports.items():
            if self._is_port_in_use(port):
                # Check if it's our service or a conflict
                process_info = self._get_port_process(port)

                if process_info and "docker" not in process_info.lower():
                    issues.append(
                        DiagnosticIssue(
                            category="Port Conflicts",
                            severity="warning",
                            title=f"Port {port} occupied by non-Docker process",
                            description=f"Port {port} required for {service} is being used by: {process_info}",
                            symptoms=[
                                f"Service startup failures on port {port}",
                                "Connection refused errors",
                                "Docker container startup failures",
                            ],
                            root_cause=f"Another process is using port {port}",
                            solution="Stop the conflicting process or change the service port configuration",
                            auto_fixable=False,
                            confidence=DiagnosticConfidence.MEDIUM,  # Medium confidence: requires user decision
                            fix_command=f"# Find and stop process: lsof -ti:{port} | xargs kill -9",
                        )
                    )

        return issues

    def _diagnose_docker_issues(self) -> List[DiagnosticIssue]:
        """Diagnose Docker-related issues."""
        issues = []

        # Check Docker availability
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                issues.append(
                    DiagnosticIssue(
                        category="Docker Issues",
                        severity="critical",
                        title="Docker not available",
                        description="Docker command failed or not found",
                        symptoms=["docker command not found", "Permission denied"],
                        root_cause="Docker not installed or not in PATH",
                        solution="Install Docker Desktop or add Docker to PATH",
                        auto_fixable=False,
                    )
                )
        except FileNotFoundError:
            issues.append(
                DiagnosticIssue(
                    category="Docker Issues",
                    severity="critical",
                    title="Docker not installed",
                    description="Docker command not found",
                    symptoms=["docker: command not found"],
                    root_cause="Docker is not installed",
                    solution="Install Docker Desktop from https://docker.com/get-started",
                    auto_fixable=False,
                )
            )
        except subprocess.TimeoutExpired:
            issues.append(
                DiagnosticIssue(
                    category="Docker Issues",
                    severity="warning",
                    title="Docker responds slowly",
                    description="Docker command timed out",
                    symptoms=["Slow Docker responses", "Timeouts"],
                    root_cause="Docker daemon may be overloaded or starting up",
                    solution="Restart Docker Desktop or wait for daemon to stabilize",
                    auto_fixable=False,
                )
            )

        # Check Docker Compose
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                issues.append(
                    DiagnosticIssue(
                        category="Docker Issues",
                        severity="critical",
                        title="Docker Compose not available",
                        description="docker-compose command failed",
                        symptoms=["docker-compose command not found"],
                        root_cause="Docker Compose not installed or not in PATH",
                        solution="Install Docker Compose or use 'docker compose' (newer syntax)",
                        auto_fixable=False,
                    )
                )
        except FileNotFoundError:
            # Try newer 'docker compose' syntax
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    # This is fine, just using newer syntax
                    pass
                else:
                    issues.append(
                        DiagnosticIssue(
                            category="Docker Issues",
                            severity="critical",
                            title="Docker Compose not available",
                            description="Neither docker-compose nor docker compose available",
                            symptoms=["Compose commands fail"],
                            root_cause="Docker Compose not installed",
                            solution="Install Docker Desktop (includes Compose) or install Compose separately",
                            auto_fixable=False,
                        )
                    )
            except Exception:
                issues.append(
                    DiagnosticIssue(
                        category="Docker Issues",
                        severity="critical",
                        title="Docker Compose not available",
                        description="Docker Compose commands not working",
                        symptoms=["Cannot run docker-compose commands"],
                        root_cause="Docker Compose not properly installed",
                        solution="Install Docker Desktop or Docker Compose separately",
                        auto_fixable=False,
                    )
                )

        return issues

    def _diagnose_database_issues(self) -> List[DiagnosticIssue]:
        """Diagnose database connectivity and configuration issues."""
        issues = []

        # Check for common database driver issues
        try:
            import asyncpg
            import psycopg2
        except ImportError as e:
            missing_driver = (
                str(e).split("'")[1] if "'" in str(e) else "database driver"
            )
            issues.append(
                DiagnosticIssue(
                    category="Database Issues",
                    severity="critical",
                    title=f"Missing database driver: {missing_driver}",
                    description=f"Required database driver not installed: {e}",
                    symptoms=[
                        "ImportError for database drivers",
                        "Module not found errors",
                    ],
                    root_cause="Database drivers not installed in virtual environment",
                    solution=f"Install missing driver: pip install {missing_driver}",
                    auto_fixable=True,
                    fix_command=f"pip install {missing_driver}",
                )
            )

        # Check database URL configuration
        database_urls = [os.getenv("DATABASE_URL"), os.getenv("DATABASE_URL_SYNC")]

        for url in database_urls:
            if url:
                if "psycopg2" in url and "async" in str(url):
                    issues.append(
                        DiagnosticIssue(
                            category="Database Issues",
                            severity="critical",
                            title="Async/sync database driver mismatch",
                            description="psycopg2 (sync) driver used in async context",
                            symptoms=[
                                "InvalidRequestError about async drivers",
                                "The loaded 'psycopg2' is not async",
                            ],
                            root_cause="Database URL uses sync driver (psycopg2) for async operations",
                            solution="Use postgresql+asyncpg:// for async connections",
                            auto_fixable=True,
                            fix_command="Update DATABASE_URL to use asyncpg driver",
                        )
                    )

        return issues

    def _diagnose_redis_issues(self) -> List[DiagnosticIssue]:
        """Diagnose Redis connectivity issues."""
        issues = []

        # Check Redis connectivity
        redis_hosts = [
            ("localhost", 6379, "Main Redis"),
            ("localhost", 6380, "Test Redis"),
        ]

        for host, port, name in redis_hosts:
            if not self._can_connect_to_port(host, port):
                issues.append(
                    DiagnosticIssue(
                        category="Redis Issues",
                        severity="warning",
                        title=f"{name} not accessible",
                        description=f"Cannot connect to {name} at {host}:{port}",
                        symptoms=[
                            f"Connection refused to {host}:{port}",
                            "Redis service unavailable",
                        ],
                        root_cause=f"Redis service not running on {host}:{port}",
                        solution="Start Redis service or check Docker containers",
                        auto_fixable=False,
                        confidence=DiagnosticConfidence.MEDIUM,  # Medium confidence: service issue
                        fix_command="docker-compose up -d redis",
                    )
                )

        return issues

    def _diagnose_python_environment(self) -> List[DiagnosticIssue]:
        """Diagnose Python environment issues."""
        issues = []

        # Check Python version
        if sys.version_info < (3, 9):
            issues.append(
                DiagnosticIssue(
                    category="Python Environment",
                    severity="critical",
                    title="Python version too old",
                    description=f"Python {sys.version_info.major}.{sys.version_info.minor} detected, need 3.9+",
                    symptoms=["Compatibility errors", "Syntax errors in modern code"],
                    root_cause="Python version below minimum requirement",
                    solution="Upgrade to Python 3.9 or later",
                    auto_fixable=False,
                )
            )

        # Check virtual environment
        if sys.prefix == sys.base_prefix:
            issues.append(
                DiagnosticIssue(
                    category="Python Environment",
                    severity="warning",
                    title="No virtual environment detected",
                    description="Running in global Python environment",
                    symptoms=["Package conflicts", "Permission errors"],
                    root_cause="Not using virtual environment",
                    solution="Create and activate virtual environment",
                    auto_fixable=True,
                    confidence=DiagnosticConfidence.HIGH,  # High confidence: safe venv creation
                    fix_command="python -m venv .venv && source .venv/bin/activate",
                )
            )

        # Check sys.path for backend
        backend_path = str(self.project_root / "backend")
        if backend_path not in sys.path:
            issues.append(
                DiagnosticIssue(
                    category="Python Environment",
                    severity="warning",
                    title="Backend not in Python path",
                    description="Backend directory not in sys.path for imports",
                    symptoms=["Import errors for app modules", "Module not found"],
                    root_cause="sys.path not configured for project structure",
                    solution="Add backend directory to sys.path",
                    auto_fixable=True,
                    fix_command="sys.path.insert(0, 'backend')",
                )
            )

        return issues

    def _diagnose_import_issues(self) -> List[DiagnosticIssue]:
        """Diagnose Python import resolution issues."""
        issues = []

        # Test critical imports
        critical_imports = [
            ("fastapi", "FastAPI framework"),
            ("sqlalchemy", "Database ORM"),
            ("redis", "Redis client"),
            ("celery", "Background task processing"),
            ("pytest", "Testing framework"),
            ("websockets", "WebSocket support"),
        ]

        for module_name, description in critical_imports:
            try:
                __import__(module_name)
            except ImportError:
                issues.append(
                    DiagnosticIssue(
                        category="Import Issues",
                        severity="critical",
                        title=f"Missing critical dependency: {module_name}",
                        description=f"Cannot import {module_name} ({description})",
                        symptoms=[f"ImportError: No module named '{module_name}'"],
                        root_cause=f"{module_name} not installed in current environment",
                        solution=f"Install {module_name}",
                        auto_fixable=True,
                        confidence=DiagnosticConfidence.HIGH,  # High confidence: standard package install
                        fix_command=f"pip install {module_name}",
                    )
                )

        # Check for missing __init__.py files
        package_dirs = [
            self.project_root / "backend" / "app",
            self.project_root / "backend" / "app" / "core",
            self.project_root / "backend" / "app" / "api",
            self.project_root / "tests",
        ]

        for pkg_dir in package_dirs:
            if pkg_dir.exists() and pkg_dir.is_dir():
                init_file = pkg_dir / "__init__.py"
                if not init_file.exists():
                    issues.append(
                        DiagnosticIssue(
                            category="Import Issues",
                            severity="warning",
                            title=f"Missing __init__.py in {pkg_dir.name}",
                            description=f"Package directory missing __init__.py: {pkg_dir}",
                            symptoms=["Import errors", "Package not recognized"],
                            root_cause="Python package structure incomplete",
                            solution=f"Create __init__.py in {pkg_dir}",
                            auto_fixable=True,
                            confidence=DiagnosticConfidence.HIGH,  # High confidence: safe file creation
                            fix_command=f"touch {init_file}",
                        )
                    )

        return issues

    def _diagnose_performance_issues(self) -> List[DiagnosticIssue]:
        """Diagnose performance-related issues."""
        issues = []

        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            issues.append(
                DiagnosticIssue(
                    category="Performance Issues",
                    severity="warning",
                    title="High memory usage",
                    description=f"System memory usage at {memory.percent:.1f}%",
                    symptoms=["Slow performance", "Out of memory errors"],
                    root_cause="System running low on memory",
                    solution="Close unnecessary applications or add more RAM",
                    auto_fixable=False,
                )
            )

        # Check disk space
        disk = psutil.disk_usage(str(self.project_root))
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 90:
            issues.append(
                DiagnosticIssue(
                    category="Performance Issues",
                    severity="warning",
                    title="Low disk space",
                    description=f"Disk usage at {disk_percent:.1f}%",
                    symptoms=["Slow I/O", "Write errors", "Build failures"],
                    root_cause="Insufficient disk space",
                    solution="Free up disk space or add storage",
                    auto_fixable=False,
                )
            )

        # Check for too many Python processes
        python_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if "python" in proc.info["name"].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if len(python_processes) > 10:
            issues.append(
                DiagnosticIssue(
                    category="Performance Issues",
                    severity="info",
                    title="Many Python processes running",
                    description=f"Found {len(python_processes)} Python processes",
                    symptoms=["Resource contention", "Slow performance"],
                    root_cause="Multiple Python processes competing for resources",
                    solution="Review and terminate unnecessary Python processes",
                    auto_fixable=False,
                )
            )

        return issues

    def _diagnose_security_config(self) -> List[DiagnosticIssue]:
        """Diagnose security configuration issues."""
        issues = []

        # Check for weak secret keys
        secret_key = os.getenv("SECRET_KEY", "")
        if secret_key and len(secret_key) < 32:
            issues.append(
                DiagnosticIssue(
                    category="Security Configuration",
                    severity="critical",
                    title="Weak SECRET_KEY",
                    description=f"SECRET_KEY is only {len(secret_key)} characters",
                    symptoms=["Security warnings", "Authentication issues"],
                    root_cause="SECRET_KEY below minimum security length",
                    solution="Generate a strong 32+ character SECRET_KEY",
                    auto_fixable=True,
                    fix_command="Generate new secret key with sufficient entropy",
                )
            )

        # Check for development keys in production-like environment
        if secret_key and "dev" in secret_key.lower():
            env = os.getenv("ENVIRONMENT", "development")
            if env != "development":
                issues.append(
                    DiagnosticIssue(
                        category="Security Configuration",
                        severity="critical",
                        title="Development keys in non-dev environment",
                        description="Using development SECRET_KEY in non-development environment",
                        symptoms=["Security vulnerabilities"],
                        root_cause="Development configuration in production",
                        solution="Generate production-grade secret keys",
                        auto_fixable=False,
                    )
                )

        return issues

    def _auto_fix_issues(self, issues: List[DiagnosticIssue]) -> int:
        """Automatically fix issues that can be auto-fixed."""
        fixed_count = 0

        for issue in issues:
            if issue.auto_fixable and issue.fix_command:
                try:
                    print(f"    🔧 Auto-fixing: {issue.title}")

                    if issue.fix_command.startswith("pip install"):
                        # Handle pip installs
                        package = issue.fix_command.split("pip install ")[1]
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", package],
                            check=True,
                            capture_output=True,
                        )

                    elif "sys.path.insert" in issue.fix_command:
                        # Handle sys.path additions
                        backend_path = str(self.project_root / "backend")
                        if backend_path not in sys.path:
                            sys.path.insert(0, backend_path)

                    elif "touch" in issue.fix_command:
                        # Handle file creation
                        file_path = issue.fix_command.split("touch ")[1]
                        Path(file_path).touch()

                    elif "Generate new secret key" in issue.fix_command:
                        # Generate secure secret key
                        import secrets

                        new_key = secrets.token_urlsafe(32)
                        os.environ["SECRET_KEY"] = new_key
                        if not os.getenv("REFRESH_SECRET_KEY"):
                            os.environ["REFRESH_SECRET_KEY"] = secrets.token_urlsafe(32)

                    print(f"      ✅ Fixed: {issue.title}")
                    fixed_count += 1

                except Exception as e:
                    print(f"      ❌ Failed to fix: {e}")

        return fixed_count

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                return result == 0
        except Exception:
            return False

    def _can_connect_to_port(self, host: str, port: int, timeout: int = 2) -> bool:
        """Check if we can connect to a specific host:port."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    def _get_port_process(self, port: int) -> Optional[str]:
        """Get information about the process using a port."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    try:
                        process = psutil.Process(conn.pid)
                        return f"{process.name()} (PID: {conn.pid})"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return f"PID: {conn.pid}"
            return None
        except Exception:
            return None

    def _print_diagnostic_summary(self, auto_fix: bool):
        """Print comprehensive diagnostic summary."""
        print("\n" + "=" * 50)
        print("🔬 DIAGNOSTIC SUMMARY")
        print("=" * 50)

        if not self.issues_found:
            print("🎉 No issues detected - system is healthy!")
            return

        # Group issues by category and severity
        by_category = {}
        by_severity = {"critical": 0, "warning": 0, "info": 0}

        for issue in self.issues_found:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
            by_severity[issue.severity] += 1

        print(f"📊 Found {len(self.issues_found)} issues:")
        print(f"   🚨 Critical: {by_severity['critical']}")
        print(f"   ⚠️  Warning: {by_severity['warning']}")
        print(f"   ℹ️  Info: {by_severity['info']}")

        print("\n📋 Issues by Category:")
        for category, issues in by_category.items():
            print(f"   {category}: {len(issues)} issues")

        print("\n🔧 Fixable Issues:")
        fixable = len([i for i in self.issues_found if i.auto_fixable])
        print(f"   {fixable}/{len(self.issues_found)} issues can be auto-fixed")

        if not auto_fix and fixable > 0:
            print(f"\n💡 Run with --fix to automatically resolve {fixable} issues")

        # Export detailed report
        self._export_diagnostic_report()

    def _export_diagnostic_report(self) -> Path:
        """Export detailed diagnostic report."""
        report_dir = self.project_root / "testing" / "diagnostics"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        report_file = report_dir / f"diagnostic_report_{timestamp}.json"

        # Sanitize system info for privacy
        sanitized_system_info = self._sanitize_system_info(self.system_info)

        report_data = {
            "timestamp": timestamp,
            "system_info": sanitized_system_info,
            "issues": [asdict(issue) for issue in self.issues_found],
            "summary": {
                "total_issues": len(self.issues_found),
                "critical": len(
                    [i for i in self.issues_found if i.severity == "critical"]
                ),
                "warning": len(
                    [i for i in self.issues_found if i.severity == "warning"]
                ),
                "info": len([i for i in self.issues_found if i.severity == "info"]),
                "auto_fixable": len([i for i in self.issues_found if i.auto_fixable]),
            },
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed diagnostic report: {report_file}")
        return report_file

    def _sanitize_system_info(self, system_info: Dict) -> Dict:
        """Remove sensitive personal information from system info."""
        sanitized = system_info.copy()

        # Sanitize environment variables
        if "environment_variables" in sanitized:
            env_vars = sanitized["environment_variables"].copy()

            # Remove/redact sensitive environment variables
            sensitive_patterns = [
                "USERNAME",
                "USER",
                "HOME",
                "USERPROFILE",
                "ONEDRIVE",
                "LOCALAPPDATA",
                "APPDATA",
                "TEMP",
                "TMP",
                "COMPUTERNAME",
                "LOGONSERVER",
                "USERDOMAIN",
                "SECRET",
                "KEY",
                "TOKEN",
                "PASSWORD",
            ]

            for key in list(env_vars.keys()):
                # Remove paths that contain usernames
                if any(pattern in key.upper() for pattern in sensitive_patterns):
                    if (
                        "SECRET" in key.upper()
                        or "KEY" in key.upper()
                        or "PASSWORD" in key.upper()
                    ):
                        env_vars[key] = "[REDACTED]"
                    else:
                        env_vars[key] = "[SANITIZED]"

                # Sanitize PATH variable to remove personal directories
                elif key == "PATH":
                    paths = env_vars[key].split(";")
                    sanitized_paths = []
                    for path in paths:
                        if "Users\\" in path or "\\Users\\" in path:
                            sanitized_paths.append("[USER_PATH_SANITIZED]")
                        else:
                            sanitized_paths.append(path)
                    env_vars[key] = ";".join(sanitized_paths)

            sanitized["environment_variables"] = env_vars

        # Sanitize file paths
        if "working_directory" in sanitized:
            sanitized["working_directory"] = sanitized["working_directory"].replace(
                "\\Users\\", "\\[USER]\\"
            )

        if "project_root" in sanitized:
            sanitized["project_root"] = sanitized["project_root"].replace(
                "\\Users\\", "\\[USER]\\"
            )

        if "python_executable" in sanitized:
            sanitized["python_executable"] = sanitized["python_executable"].replace(
                "\\Users\\", "\\[USER]\\"
            )

        return sanitized


def main():
    """Command-line interface for diagnostic toolkit."""
    import argparse

    parser = argparse.ArgumentParser(description="Diagnostic Toolkit")
    parser.add_argument(
        "--diagnose", action="store_true", help="Run comprehensive diagnostics"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix detected issues")
    parser.add_argument(
        "--category",
        choices=[
            "docker",
            "database",
            "redis",
            "python",
            "imports",
            "performance",
            "security",
        ],
        help="Run diagnostics for specific category",
    )

    args = parser.parse_args()

    toolkit = DiagnosticToolkit()

    if args.diagnose or args.fix:
        success = toolkit.run_comprehensive_diagnostics(auto_fix=args.fix)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
