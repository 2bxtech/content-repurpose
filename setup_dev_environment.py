#!/usr/bin/env python3
"""
One-Command Developer Environment Setup
=======================================

Sets up a complete development environment for new team members:
- Validates system requirements
- Installs dependencies  
- Configures Docker environment
- Runs validation tests
- Provides next steps

Usage:
    python setup_dev_environment.py
    python setup_dev_environment.py --quick
    python setup_dev_environment.py --validate-only
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple


class DeveloperEnvironmentSetup:
    """One-command setup for new developers."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.start_time = time.time()
        self.steps_completed = 0
        self.total_steps = 8
        
    def setup_complete_environment(self, quick_mode: bool = False) -> bool:
        """Run complete environment setup."""
        print("🚀 Content Repurpose Tool - Developer Environment Setup")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Python: {sys.executable}")
        print(f"Mode: {'Quick' if quick_mode else 'Complete'}")
        print()
        
        success = True
        
        # Setup steps
        steps = [
            ("System Requirements", self._check_system_requirements),
            ("Python Environment", self._setup_python_environment),
            ("Project Dependencies", self._install_dependencies),
            ("Testing Framework", self._setup_testing_framework),
            ("Docker Environment", self._setup_docker if not quick_mode else self._validate_docker),
            ("Database Setup", self._setup_databases if not quick_mode else self._validate_databases),
            ("Environment Config", self._setup_environment_config),
            ("Validation Tests", self._run_validation_tests)
        ]
        
        for step_name, step_func in steps:
            if not self._execute_step(step_name, step_func):
                success = False
                if not quick_mode:
                    break
        
        elapsed = time.time() - self.start_time
        
        if success:
            self._print_success_summary(elapsed)
        else:
            self._print_failure_summary(elapsed)
        
        return success
    
    def _execute_step(self, step_name: str, step_func) -> bool:
        """Execute a setup step with progress indication."""
        self.steps_completed += 1
        print(f"[{self.steps_completed}/{self.total_steps}] {step_name}...")
        
        try:
            success = step_func()
            if success:
                print(f"  ✅ {step_name} completed")
            else:
                print(f"  ❌ {step_name} failed")
            return success
        except Exception as e:
            print(f"  ❌ {step_name} error: {e}")
            return False
    
    def _check_system_requirements(self) -> bool:
        """Check system requirements."""
        checks = [
            ("Python 3.9+", self._check_python_version),
            ("Git", self._check_git),
            ("Docker", self._check_docker),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            if check_func():
                print(f"    ✅ {check_name}")
            else:
                print(f"    ❌ {check_name}")
                all_passed = False
        
        return all_passed
    
    def _setup_python_environment(self) -> bool:
        """Setup Python virtual environment."""
        venv_path = self.project_root / ".venv"
        
        # Check if virtual environment exists
        if venv_path.exists():
            print(f"    ✅ Virtual environment exists: {venv_path}")
            return True
        
        # Create virtual environment
        try:
            print(f"    🔧 Creating virtual environment...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True, capture_output=True)
            
            print(f"    ✅ Virtual environment created: {venv_path}")
            
            # Provide activation instructions
            if os.name == 'nt':  # Windows
                activate_cmd = f"{venv_path}\\Scripts\\activate.bat"
            else:  # Unix/Linux/macOS
                activate_cmd = f"source {venv_path}/bin/activate"
            
            print(f"    💡 Activate with: {activate_cmd}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"    ❌ Failed to create virtual environment: {e}")
            return False
    
    def _install_dependencies(self) -> bool:
        """Install project dependencies."""
        requirements_files = [
            self.project_root / "backend" / "requirements.txt",
            self.project_root / "testing" / "requirements-testing.txt"
        ]
        
        for req_file in requirements_files:
            if not req_file.exists():
                print(f"    ⚠️  Requirements file not found: {req_file}")
                continue
            
            try:
                print(f"    🔧 Installing from {req_file.name}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(req_file)
                ], check=True, capture_output=True)
                print(f"    ✅ Installed dependencies from {req_file.name}")
            except subprocess.CalledProcessError as e:
                print(f"    ❌ Failed to install from {req_file.name}: {e}")
                return False
        
        return True
    
    def _setup_testing_framework(self) -> bool:
        """Setup bulletproof testing framework."""
        # Create testing directories
        test_dirs = [
            self.project_root / "testing" / "results",
            self.project_root / "testing" / "diagnostics",
            self.project_root / "testing" / "reports"
        ]
        
        for test_dir in test_dirs:
            test_dir.mkdir(parents=True, exist_ok=True)
            print(f"    ✅ Created directory: {test_dir.name}")
        
        # Test framework imports
        try:
            sys.path.insert(0, str(self.project_root / "testing"))
            from testing.framework.environment import EnvironmentManager
            print(f"    ✅ Testing framework imports working")
            return True
        except ImportError as e:
            print(f"    ❌ Testing framework import failed: {e}")
            return False
    
    def _setup_docker(self) -> bool:
        """Setup Docker environment."""
        # Check Docker Compose files
        compose_files = [
            "docker-compose.yml",
            "docker-compose.test.yml", 
            "docker-compose.testing.yml"
        ]
        
        for compose_file in compose_files:
            file_path = self.project_root / compose_file
            if file_path.exists():
                print(f"    ✅ Found {compose_file}")
            else:
                print(f"    ⚠️  Missing {compose_file}")
        
        # Test Docker services startup
        try:
            print(f"    🔧 Testing Docker services...")
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml", "config"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"    ✅ Docker Compose configuration valid")
                return True
            else:
                print(f"    ❌ Docker Compose configuration error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"    ❌ Docker setup error: {e}")
            return False
    
    def _validate_docker(self) -> bool:
        """Quick Docker validation."""
        try:
            result = subprocess.run([
                "docker", "--version"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"    ✅ Docker available: {result.stdout.strip()}")
                return True
            else:
                print(f"    ❌ Docker not available")
                return False
        except Exception as e:
            print(f"    ❌ Docker validation error: {e}")
            return False
    
    def _setup_databases(self) -> bool:
        """Setup test databases."""
        try:
            print(f"    🔧 Starting test databases...")
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml", 
                "up", "-d", "postgres-test", "redis-test"
            ], cwd=self.project_root, check=True, capture_output=True, timeout=60)
            
            # Wait for health
            import time
            print(f"    ⏳ Waiting for database health...")
            time.sleep(10)
            
            # Stop services
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml", "down"
            ], cwd=self.project_root, capture_output=True)
            
            print(f"    ✅ Database setup test completed")
            return True
            
        except Exception as e:
            print(f"    ❌ Database setup error: {e}")
            return False
    
    def _validate_databases(self) -> bool:
        """Quick database validation."""
        print(f"    ✅ Database validation skipped (quick mode)")
        return True
    
    def _setup_environment_config(self) -> bool:
        """Setup environment configuration."""
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print(f"    ✅ .env file exists")
        else:
            # Create basic .env file
            env_content = """# Development Environment Configuration
SECRET_KEY=dev_secret_key_change_in_production_32_chars_minimum_for_security
REFRESH_SECRET_KEY=dev_refresh_secret_key_change_in_production_32_chars_minimum_for_security
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=content_repurpose
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres_dev_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# AI Provider (add your API keys)
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
"""
            env_file.write_text(env_content)
            print(f"    ✅ Created .env file with defaults")
        
        return True
    
    def _run_validation_tests(self) -> bool:
        """Run validation tests."""
        try:
            # Test bulletproof framework
            print(f"    🔧 Testing bulletproof framework...")
            result = subprocess.run([
                sys.executable, "testing/run_tests.py", "--quick-validate"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"    ✅ Validation tests passed")
                return True
            else:
                print(f"    ⚠️  Validation tests had issues")
                print(f"    Output: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"    ❌ Validation test error: {e}")
            return False
    
    def _check_python_version(self) -> bool:
        """Check Python version."""
        return sys.version_info >= (3, 9)
    
    def _check_git(self) -> bool:
        """Check Git availability."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False
    
    def _check_docker(self) -> bool:
        """Check Docker availability."""
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False
    
    def _print_success_summary(self, elapsed: float):
        """Print success summary with next steps."""
        print(f"\n" + "=" * 60)
        print(f"🎉 DEVELOPER ENVIRONMENT SETUP COMPLETE!")
        print(f"=" * 60)
        print(f"⏱️  Setup completed in {elapsed:.1f} seconds")
        print(f"✅ All {self.total_steps} steps completed successfully")
        
        print(f"\n📋 Next Steps:")
        print(f"  1. Activate virtual environment:")
        if os.name == 'nt':
            print(f"     .venv\\Scripts\\activate.bat")
        else:
            print(f"     source .venv/bin/activate")
        
        print(f"  2. Run tests:")
        print(f"     python testing/run_tests.py --phase 5")
        print(f"     python testing/run_tests.py --all")
        
        print(f"  3. Start development:")
        print(f"     docker-compose up -d")
        print(f"     cd backend && python main.py")
        
        print(f"\n🔧 Available Commands:")
        print(f"  python testing/run_tests.py --validate --fix    # Environment validation")
        print(f"  python testing/run_tests.py --diagnose --fix    # System diagnostics")
        print(f"  python testing/run_tests.py --setup-dev         # Re-run setup")
        
        print(f"\n📚 Documentation:")
        print(f"  README.md - Project overview")
        print(f"  docs/DEVELOPMENT_PHASES.md - Development phases")
        print(f"  docs/TESTING.md - Testing guide")
    
    def _print_failure_summary(self, elapsed: float):
        """Print failure summary with troubleshooting."""
        print(f"\n" + "=" * 60)
        print(f"⚠️  DEVELOPER ENVIRONMENT SETUP INCOMPLETE")
        print(f"=" * 60)
        print(f"⏱️  Setup ran for {elapsed:.1f} seconds")
        print(f"✅ Completed {self.steps_completed}/{self.total_steps} steps")
        
        print(f"\n🔧 Troubleshooting:")
        print(f"  1. Run diagnostics:")
        print(f"     python testing/run_tests.py --diagnose --fix")
        
        print(f"  2. Check system requirements:")
        print(f"     - Python 3.9+")
        print(f"     - Docker Desktop")
        print(f"     - Git")
        
        print(f"  3. Manual setup:")
        print(f"     python -m venv .venv")
        print(f"     pip install -r backend/requirements.txt")
        print(f"     pip install -r testing/requirements-testing.txt")
        
        print(f"\n💡 Get help:")
        print(f"  - Check docs/TROUBLESHOOTING.md")
        print(f"  - Run: python testing/run_tests.py --validate --fix")


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Developer Environment Setup")
    parser.add_argument("--quick", action="store_true", help="Quick setup (skip Docker tests)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't install")
    
    args = parser.parse_args()
    
    setup = DeveloperEnvironmentSetup()
    
    if args.validate_only:
        success = setup._check_system_requirements()
    else:
        success = setup.setup_complete_environment(quick_mode=args.quick)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()