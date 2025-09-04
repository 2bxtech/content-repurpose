"""
Environment Manager - Self-Healing Environment Setup
====================================================

Automatically detects and fixes common environment issues:
- Missing __init__.py files in Python packages
- Invalid Python package structure
- Missing dependencies with clear installation guidance
- Environment variable configuration
- Python path resolution issues
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Dict
import json


class EnvironmentManager:
    """Manages and validates the development environment with auto-repair capabilities."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.backend_path = self.project_root / "backend"
        self.issues_found: List[Dict] = []
        self.fixes_applied: List[Dict] = []

    def validate_environment(self, auto_fix: bool = False) -> bool:
        """
        Comprehensive environment validation with optional auto-fix.

        Returns:
            bool: True if environment is valid (or successfully fixed)
        """
        print("🔍 Environment Validation Starting...")
        print("=" * 50)

        all_valid = True

        # Run all validation checks
        checks = [
            ("Python Package Structure", self._check_package_structure),
            ("Python Dependencies", self._check_dependencies),
            ("Python Path Configuration", self._check_python_path),
            ("Environment Variables", self._check_env_variables),
            ("Docker Environment", self._check_docker_environment),
        ]

        for check_name, check_func in checks:
            print(f"\n📋 {check_name}...")
            try:
                is_valid = check_func(auto_fix)
                if is_valid:
                    print(f"  ✅ {check_name}: PASS")
                else:
                    print(f"  ❌ {check_name}: FAIL")
                    all_valid = False
            except Exception as e:
                print(f"  ⚠️  {check_name}: ERROR - {e}")
                all_valid = False
                self.issues_found.append(
                    {"category": check_name, "error": str(e), "severity": "ERROR"}
                )

        # Print summary
        print("\n" + "=" * 50)
        if all_valid:
            print("🎉 Environment validation PASSED!")
            if self.fixes_applied:
                print(f"✨ Applied {len(self.fixes_applied)} automatic fixes")
        else:
            print("⚠️  Environment validation FAILED!")
            print(f"Found {len(self.issues_found)} issues")
            if not auto_fix:
                print("\n💡 Run with --fix to automatically resolve issues")

        return all_valid

    def _check_package_structure(self, auto_fix: bool = False) -> bool:
        """Check and fix Python package structure."""
        missing_inits = []

        # Define package directories that need __init__.py
        package_dirs = [
            self.backend_path / "app",
            self.backend_path / "app" / "api",
            self.backend_path / "app" / "api" / "routes",
            self.backend_path / "app" / "core",
            self.backend_path / "app" / "models",
            self.backend_path / "app" / "services",
            self.backend_path / "app" / "tasks",
            self.backend_path / "app" / "utils",
            self.backend_path / "app" / "middleware",
            self.backend_path / "app" / "db",
            self.backend_path / "app" / "db" / "models",
            self.project_root / "testing",
            self.project_root / "testing" / "framework",
            self.project_root / "tests",
        ]

        for pkg_dir in package_dirs:
            if pkg_dir.exists() and pkg_dir.is_dir():
                init_file = pkg_dir / "__init__.py"
                if not init_file.exists():
                    missing_inits.append(init_file)

        if missing_inits:
            print(f"    Found {len(missing_inits)} missing __init__.py files")

            if auto_fix:
                for init_file in missing_inits:
                    try:
                        # Create appropriate __init__.py content
                        content = self._generate_init_content(init_file.parent)
                        init_file.write_text(content, encoding="utf-8")
                        print(
                            f"    ✅ Created: {init_file.relative_to(self.project_root)}"
                        )
                        self.fixes_applied.append(
                            {
                                "type": "created_init_file",
                                "path": str(init_file),
                                "content": content,
                            }
                        )
                    except Exception as e:
                        print(f"    ❌ Failed to create {init_file}: {e}")
                        return False
                return True
            else:
                for init_file in missing_inits:
                    print(f"    ❌ Missing: {init_file.relative_to(self.project_root)}")
                return False

        print("    ✅ All package directories have __init__.py files")
        return True

    def _generate_init_content(self, package_dir: Path) -> str:
        """Generate appropriate __init__.py content based on package directory."""
        relative_path = package_dir.relative_to(self.project_root)

        if "api" in str(relative_path):
            return '"""\nAPI package\n"""'
        elif "core" in str(relative_path):
            return '"""\nCore application modules\n"""'
        elif "models" in str(relative_path):
            return '"""\nData models\n"""'
        elif "services" in str(relative_path):
            return '"""\nBusiness logic services\n"""'
        elif "tasks" in str(relative_path):
            return '"""\nBackground tasks\n"""'
        elif "utils" in str(relative_path):
            return '"""\nUtility functions\n"""'
        elif "testing" in str(relative_path):
            return '"""\nTesting framework\n"""'
        elif "tests" in str(relative_path):
            return '"""\nTest suite\n"""'
        else:
            return f'"""\n{package_dir.name.title()} package\n"""'

    def _check_dependencies(self, auto_fix: bool = False) -> bool:
        """Check if all required dependencies are installed."""
        requirements_file = self.backend_path / "requirements.txt"

        if not requirements_file.exists():
            print("    ❌ requirements.txt not found")
            return False

        # Read requirements
        try:
            requirements = requirements_file.read_text().strip().split("\n")
            requirements = [
                req.strip()
                for req in requirements
                if req.strip() and not req.startswith("#")
            ]
        except Exception as e:
            print(f"    ❌ Error reading requirements.txt: {e}")
            return False

        missing_packages = []

        for requirement in requirements:
            # Parse package name (handle version specifiers)
            package_name = (
                requirement.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
                .split("~=")[0]
            )

            try:
                importlib.import_module(package_name.replace("-", "_"))
                print(f"    ✅ {package_name}")
            except ImportError:
                missing_packages.append(requirement)
                print(f"    ❌ {package_name} - missing")

        if missing_packages:
            if auto_fix:
                print(f"    🔧 Installing {len(missing_packages)} missing packages...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install"] + missing_packages,
                        check=True,
                        capture_output=True,
                    )
                    print("    ✅ Successfully installed missing packages")
                    self.fixes_applied.append(
                        {"type": "installed_packages", "packages": missing_packages}
                    )
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"    ❌ Failed to install packages: {e}")
                    return False
            else:
                print(f"    💡 Run: pip install {' '.join(missing_packages)}")
                return False

        return True

    def _check_python_path(self, auto_fix: bool = False) -> bool:
        """Check Python path configuration for imports."""
        backend_in_path = str(self.backend_path) in sys.path

        if not backend_in_path:
            print(f"    ❌ Backend path not in sys.path: {self.backend_path}")
            if auto_fix:
                sys.path.insert(0, str(self.backend_path))
                print("    ✅ Added backend to sys.path")
                self.fixes_applied.append(
                    {"type": "added_to_sys_path", "path": str(self.backend_path)}
                )
            return auto_fix
        else:
            print("    ✅ Backend path in sys.path")
            return True

    def _check_env_variables(self, auto_fix: bool = False) -> bool:
        """Check required environment variables."""
        required_vars = ["SECRET_KEY", "REFRESH_SECRET_KEY"]

        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"    ❌ Missing environment variables: {', '.join(missing_vars)}")
            if auto_fix:
                # Set development defaults
                env_defaults = {
                    "SECRET_KEY": "dev_secret_key_change_in_production_32_chars_minimum_for_security",
                    "REFRESH_SECRET_KEY": "dev_refresh_secret_key_change_in_production_32_chars_minimum_for_security",
                }

                for var in missing_vars:
                    if var in env_defaults:
                        os.environ[var] = env_defaults[var]
                        print(f"    ✅ Set {var} to development default")
                        self.fixes_applied.append(
                            {
                                "type": "set_env_var",
                                "variable": var,
                                "value": "[REDACTED]",
                            }
                        )
                return True
            return False

        print("    ✅ All required environment variables set")
        return True

    def _check_docker_environment(self, auto_fix: bool = False) -> bool:
        """Check Docker environment availability."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"    ✅ Docker available: {result.stdout.strip()}")

                # Check Docker Compose
                compose_result = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if compose_result.returncode == 0:
                    print(
                        f"    ✅ Docker Compose available: {compose_result.stdout.strip()}"
                    )
                    return True
                else:
                    print("    ❌ Docker Compose not available")
                    return False
            else:
                print("    ❌ Docker not available")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("    ❌ Docker command not found")
            return False

    def get_diagnostic_report(self) -> Dict:
        """Generate comprehensive diagnostic report."""
        return {
            "project_root": str(self.project_root),
            "backend_path": str(self.backend_path),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "sys_path": sys.path,
            "environment_variables": {
                k: "[REDACTED]" if "key" in k.lower() or "secret" in k.lower() else v
                for k, v in os.environ.items()
            },
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
        }

    def export_diagnostic_report(self, output_file: Path = None) -> Path:
        """Export diagnostic report to JSON file."""
        if output_file is None:
            output_file = self.project_root / "testing" / "diagnostic_report.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.get_diagnostic_report(), f, indent=2)

        return output_file


def main():
    """Command-line interface for environment management."""
    import argparse

    parser = argparse.ArgumentParser(description="Environment Manager")
    parser.add_argument("--validate", action="store_true", help="Validate environment")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument(
        "--report", action="store_true", help="Generate diagnostic report"
    )

    args = parser.parse_args()

    env_manager = EnvironmentManager()

    if args.validate or args.fix:
        env_manager.validate_environment(auto_fix=args.fix)

    if args.report:
        report_file = env_manager.export_diagnostic_report()
        print(f"\n📄 Diagnostic report exported to: {report_file}")


if __name__ == "__main__":
    main()
