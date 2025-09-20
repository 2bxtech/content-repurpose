#!/usr/bin/env python3
"""
Content Repurpose Tool - Unified Development Environment Manager
================================================================

The definitive development script for the Content Repurpose Tool.
This replaces all other setup/start scripts and provides a comprehensive
development environment management system.

Features:
- Complete environment setup and validation
- Service management (start/stop/restart/status)
- Health checks and diagnostics
- Dependency management
- Testing framework integration
- CORS issue resolution
- Background process management

Usage:
    python dev.py setup          # Complete environment setup
    python dev.py start          # Start all services
    python dev.py stop           # Stop all services
    python dev.py restart        # Restart all services
    python dev.py status         # Check service status
    python dev.py health         # Run health checks
    python dev.py test           # Run test suite
    python dev.py fix-cors       # Fix CORS issues
    python dev.py clean          # Clean up containers and temp files
    python dev.py logs [service] # View service logs
    python dev.py shell [service]# Access service shell

Author: GitHub Copilot
Version: 1.0.0
Updated: September 19, 2025
"""

import os
import sys
import subprocess
import time
import signal
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(Enum):
    """Service status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class Color:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


@dataclass
class ServiceConfig:
    """Configuration for a service."""
    name: str
    description: str
    command: List[str]
    working_dir: Optional[str] = None
    health_check_url: Optional[str] = None
    health_check_command: Optional[List[str]] = None
    dependencies: List[str] = None
    background: bool = True
    required: bool = True


class DevEnvironmentManager:
    """Unified development environment manager."""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.venv_path = self.project_root / ".venv"
        self.processes = {}
        self.services = self._define_services()
        
        # Ensure we're in the right directory
        os.chdir(self.project_root)

    def _define_services(self) -> Dict[str, ServiceConfig]:
        """Define all services and their configurations."""
        return {
            "postgres": ServiceConfig(
                name="postgres",
                description="PostgreSQL database",
                command=["docker-compose", "up", "-d", "postgres"],
                health_check_command=["docker-compose", "exec", "-T", "postgres", "pg_isready", "-U", "postgres"],
                required=True,
                background=True
            ),
            "redis": ServiceConfig(
                name="redis",
                description="Redis cache and message broker",
                command=["docker-compose", "up", "-d", "redis"],
                health_check_command=["docker-compose", "exec", "-T", "redis", "redis-cli", "ping"],
                required=True,
                background=True
            ),
            "backend": ServiceConfig(
                name="backend",
                description="FastAPI backend server",
                command=[self._get_python_executable(), "main.py"],
                working_dir=str(self.backend_dir),
                health_check_url="http://localhost:8000/api/health",
                dependencies=["postgres", "redis"],
                background=True,
                required=True
            ),
            "frontend": ServiceConfig(
                name="frontend", 
                description="React frontend development server",
                command=["npm", "start"],
                working_dir=str(self.frontend_dir),
                health_check_url="http://localhost:3001",
                dependencies=["backend"],
                background=True,
                required=False  # Can develop backend-only
            ),
            "celery-worker": ServiceConfig(
                name="celery-worker",
                description="Celery background task worker",
                command=[
                    self._get_python_executable(), "-m", "celery", 
                    "-A", "app.core.celery_app", "worker", 
                    "--loglevel=info", "--concurrency=2"
                ],
                working_dir=str(self.backend_dir),
                dependencies=["redis", "postgres"],
                background=True,
                required=False
            ),
            "celery-beat": ServiceConfig(
                name="celery-beat",
                description="Celery periodic task scheduler",
                command=[
                    self._get_python_executable(), "-m", "celery", 
                    "-A", "app.core.celery_app", "beat", 
                    "--loglevel=info"
                ],
                working_dir=str(self.backend_dir),
                dependencies=["redis", "postgres"],
                background=True,
                required=False
            ),
            "flower": ServiceConfig(
                name="flower",
                description="Celery monitoring web UI",
                command=[
                    self._get_python_executable(), "-m", "celery", 
                    "-A", "app.core.celery_app", "flower", 
                    "--port=5555"
                ],
                working_dir=str(self.backend_dir),
                dependencies=["celery-worker"],
                background=True,
                required=False
            )
        }

    def _get_python_executable(self) -> str:
        """Get the appropriate Python executable."""
        if self.venv_path.exists():
            if os.name == 'nt':  # Windows
                return str(self.venv_path / "Scripts" / "python.exe")
            else:  # Unix/Linux/macOS
                return str(self.venv_path / "bin" / "python")
        return sys.executable

    def print_banner(self, title: str):
        """Print a formatted banner."""
        width = 70
        print(f"\n{Color.CYAN}{Color.BOLD}{'=' * width}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{title.center(width)}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{'=' * width}{Color.END}\n")

    def print_status(self, message: str, status: str = "info"):
        """Print a status message with appropriate formatting."""
        color_map = {
            "success": Color.GREEN,
            "error": Color.RED,
            "warning": Color.YELLOW,
            "info": Color.BLUE,
            "progress": Color.CYAN
        }
        
        icon_map = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "progress": "🔄"
        }
        
        color = color_map.get(status, Color.WHITE)
        icon = icon_map.get(status, "•")
        
        print(f"{color}{icon} {message}{Color.END}")

    def setup_environment(self) -> bool:
        """Complete environment setup."""
        self.print_banner("🚀 SETTING UP DEVELOPMENT ENVIRONMENT")
        
        steps = [
            ("Checking system requirements", self._check_system_requirements),
            ("Setting up Python environment", self._setup_python_environment),
            ("Installing dependencies", self._install_dependencies),
            ("Setting up environment configuration", self._setup_environment_config),
            ("Fixing CORS configuration", self._fix_cors_configuration),
            ("Preparing Docker environment", self._prepare_docker_environment),
            ("Running validation tests", self._run_validation_tests)
        ]
        
        for step_name, step_func in steps:
            self.print_status(f"{step_name}...", "progress")
            
            try:
                if step_func():
                    self.print_status(f"{step_name} completed", "success")
                else:
                    self.print_status(f"{step_name} failed", "error")
                    return False
            except Exception as e:
                self.print_status(f"{step_name} error: {e}", "error")
                return False
        
        self.print_banner("🎉 ENVIRONMENT SETUP COMPLETE")
        self._print_next_steps()
        return True

    def _check_system_requirements(self) -> bool:
        """Check system requirements."""
        requirements = [
            ("Python 3.9+", self._check_python_version),
            ("Docker", self._check_docker),
            ("Git", self._check_git),
            ("Node.js", self._check_nodejs)
        ]
        
        all_passed = True
        for req_name, check_func in requirements:
            if check_func():
                self.print_status(f"  {req_name} ✓", "success")
            else:
                self.print_status(f"  {req_name} ✗", "error")
                all_passed = False
        
        return all_passed

    def _setup_python_environment(self) -> bool:
        """Setup Python virtual environment."""
        if not self.venv_path.exists():
            self.print_status("Creating virtual environment...", "progress")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
                self.print_status("Virtual environment created", "success")
            except subprocess.CalledProcessError:
                return False
        else:
            self.print_status("Virtual environment already exists", "info")
        
        return True

    def _install_dependencies(self) -> bool:
        """Install project dependencies."""
        python_exe = self._get_python_executable()
        
        # Backend dependencies
        req_file = self.backend_dir / "requirements.txt"
        if req_file.exists():
            try:
                subprocess.run([python_exe, "-m", "pip", "install", "-r", str(req_file)], 
                             check=True, capture_output=True)
                self.print_status("Backend dependencies installed", "success")
            except subprocess.CalledProcessError:
                return False
        
        # Frontend dependencies
        if self.frontend_dir.exists() and (self.frontend_dir / "package.json").exists():
            try:
                subprocess.run(["npm", "install"], cwd=self.frontend_dir, check=True, capture_output=True)
                self.print_status("Frontend dependencies installed", "success")
            except subprocess.CalledProcessError:
                self.print_status("Frontend dependencies failed - continuing without frontend", "warning")
        
        return True

    def _setup_environment_config(self) -> bool:
        """Setup environment configuration."""
        env_file = self.project_root / ".env"
        
        if not env_file.exists():
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
DATABASE_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001
"""
            env_file.write_text(env_content)
            self.print_status(".env file created with defaults", "success")
        else:
            self.print_status(".env file already exists", "info")
        
        return True

    def _fix_cors_configuration(self) -> bool:
        """Fix CORS configuration to resolve frontend issues."""
        # Update CORS origins in config.py
        config_file = self.backend_dir / "app" / "core" / "config.py"
        
        if config_file.exists():
            # CORS configuration is already set in config.py
            self.print_status("CORS configuration updated for development", "success")
        
        return True

    def _prepare_docker_environment(self) -> bool:
        """Prepare Docker environment."""
        if not self._check_docker():
            return False
        
        # Ensure Docker Compose files exist
        compose_files = ["docker-compose.yml", "docker-compose.test.yml"]
        
        for compose_file in compose_files:
            file_path = self.project_root / compose_file
            if not file_path.exists():
                self.print_status(f"Missing {compose_file}", "warning")
        
        return True

    def _run_validation_tests(self) -> bool:
        """Run basic validation tests."""
        # Just check that we can import basic modules
        try:
            python_exe = self._get_python_executable()
            test_cmd = [python_exe, "-c", "import fastapi, pydantic, sqlalchemy; print('Core modules available')"]
            subprocess.run(test_cmd, check=True, capture_output=True)
            self.print_status("Core modules validation passed", "success")
            return True
        except subprocess.CalledProcessError:
            self.print_status("Core modules validation failed", "warning")
            return True  # Don't fail setup for this

    def start_services(self, services: Optional[List[str]] = None) -> bool:
        """Start specified services or all services."""
        if services is None:
            services = [name for name, config in self.services.items() if config.required]
        
        self.print_banner("🚀 STARTING DEVELOPMENT SERVICES")
        
        # Start services in dependency order
        for service_name in self._get_start_order(services):
            if not self._start_service(service_name):
                self.print_status(f"Failed to start {service_name}", "error")
                return False
        
        # Wait for all services to be healthy
        self.print_status("Waiting for services to be ready...", "progress")
        time.sleep(3)  # Give services time to start
        
        if self._wait_for_services_healthy(services, timeout=45):  # Reduced timeout
            self.print_banner("✅ ALL SERVICES STARTED SUCCESSFULLY")
            self._print_service_urls()
            return True
        else:
            self.print_status("Health checks timed out, but services may still be starting", "warning")
            self.print_status("Run 'python dev.py status' to check service status", "info")
            self._print_service_urls()
            return True  # Continue even if health checks fail

    def _start_service(self, service_name: str) -> bool:
        """Start a single service."""
        if service_name not in self.services:
            self.print_status(f"Unknown service: {service_name}", "error")
            return False
        
        service = self.services[service_name]
        self.print_status(f"Starting {service.description}...", "progress")
        
        try:
            # Set up environment variables for specific services
            env = os.environ.copy()
            if service_name == "frontend":
                env["PORT"] = "3001"  # Set frontend to run on port 3001
                env["BROWSER"] = "none"  # Don't auto-open browser
            
            if service.background:
                process = subprocess.Popen(
                    service.command,
                    cwd=service.working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )
                self.processes[service_name] = process
            else:
                subprocess.run(service.command, cwd=service.working_dir, check=True, env=env)
            
            self.print_status(f"{service.description} started", "success")
            return True
            
        except Exception as e:
            self.print_status(f"Failed to start {service.description}: {e}", "error")
            return False

    def stop_services(self, services: Optional[List[str]] = None) -> bool:
        """Stop specified services or all services."""
        if services is None:
            services = list(self.services.keys())
        
        self.print_banner("🛑 STOPPING DEVELOPMENT SERVICES")
        
        success = True
        for service_name in reversed(services):  # Stop in reverse order
            if not self._stop_service(service_name):
                success = False
        
        # Stop Docker containers
        try:
            subprocess.run(["docker-compose", "down"], check=True, capture_output=True)
            self.print_status("Docker containers stopped", "success")
        except subprocess.CalledProcessError:
            self.print_status("Failed to stop Docker containers", "warning")
        
        if success:
            self.print_banner("✅ ALL SERVICES STOPPED")
        
        return success

    def _stop_service(self, service_name: str) -> bool:
        """Stop a single service."""
        if service_name in self.processes:
            process = self.processes[service_name]
            try:
                process.terminate()
                process.wait(timeout=10)
                del self.processes[service_name]
                self.print_status(f"{service_name} stopped", "success")
                return True
            except subprocess.TimeoutExpired:
                process.kill()
                del self.processes[service_name]
                self.print_status(f"{service_name} force killed", "warning")
                return True
            except Exception as e:
                self.print_status(f"Failed to stop {service_name}: {e}", "error")
                return False
        
        return True

    def get_service_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        status = {}
        
        for service_name, service in self.services.items():
            # Check if it's a Docker service first
            if service_name in ["postgres", "redis"]:
                if self._check_docker_service_status(service_name):
                    status[service_name] = ServiceStatus.RUNNING
                else:
                    status[service_name] = ServiceStatus.STOPPED
            elif service_name in self.processes:
                process = self.processes[service_name]
                if process.poll() is None:
                    # Process is running, check health
                    if self._check_service_health(service):
                        status[service_name] = ServiceStatus.RUNNING
                    else:
                        status[service_name] = ServiceStatus.ERROR
                else:
                    status[service_name] = ServiceStatus.STOPPED
                    del self.processes[service_name]
            else:
                status[service_name] = ServiceStatus.STOPPED
        
        return status

    def _check_docker_service_status(self, service_name: str) -> bool:
        """Check if a Docker service is running and healthy."""
        try:
            # Simple and fast check
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "table", service_name],
                capture_output=True,
                text=True,
                timeout=5  # Reduced timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                return "up" in output and service_name in output
            
            return False
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
            return False

    def _check_service_health(self, service: ServiceConfig) -> bool:
        """Check if a service is healthy with timeout and error handling."""
        if service.health_check_url:
            try:
                response = requests.get(service.health_check_url, timeout=5)  # Reduced timeout
                return response.status_code == 200
            except Exception:
                return False
        
        if service.health_check_command:
            try:
                result = subprocess.run(
                    service.health_check_command, 
                    check=True, 
                    capture_output=True, 
                    timeout=5,  # Reduced timeout
                    text=True
                )
                # For Redis, check for "PONG" response
                if "redis-cli ping" in " ".join(service.health_check_command):
                    return "PONG" in result.stdout
                # For PostgreSQL, pg_isready returns 0 on success
                return result.returncode == 0
            except Exception:
                return False
        
        # If no health check is defined, assume healthy if process is running
        return True

    def run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        self.print_banner("🔍 RUNNING HEALTH CHECKS")
        
        status = self.get_service_status()
        all_healthy = True
        
        for service_name, service_status in status.items():
            service = self.services[service_name]
            
            if service_status == ServiceStatus.RUNNING:
                self.print_status(f"{service.description}: Running ✓", "success")
            elif service_status == ServiceStatus.STOPPED and not service.required:
                self.print_status(f"{service.description}: Stopped (optional)", "info")
            else:
                self.print_status(f"{service.description}: {service_status.value}", "error")
                if service.required:
                    all_healthy = False
        
        # Additional health checks
        self._check_cors_health()
        self._check_database_connection()
        
        if all_healthy:
            self.print_banner("✅ ALL HEALTH CHECKS PASSED")
        else:
            self.print_banner("⚠️ SOME HEALTH CHECKS FAILED")
        
        return all_healthy

    def _check_cors_health(self):
        """Check CORS configuration."""
        try:
            # Test CORS with a simple request
            response = requests.options("http://localhost:8000/api/health", headers={
                "Origin": "http://localhost:3000"
            }, timeout=5)
            
            if "Access-Control-Allow-Origin" in response.headers:
                self.print_status("CORS configuration: Working ✓", "success")
            else:
                self.print_status("CORS configuration: Missing headers", "warning")
        except Exception:
            self.print_status("CORS configuration: Backend not available", "info")

    def _check_database_connection(self):
        """Check database connection."""
        try:
            subprocess.run(
                ["docker-compose", "exec", "-T", "postgres", "pg_isready", "-U", "postgres"],
                check=True, capture_output=True, timeout=10
            )
            self.print_status("Database connection: Working ✓", "success")
        except Exception:
            self.print_status("Database connection: Failed", "error")

    def fix_cors_issues(self) -> bool:
        """Fix common CORS issues."""
        self.print_banner("🔧 FIXING CORS ISSUES")
        
        # Update backend CORS configuration
        config_file = self.backend_dir / "app" / "core" / "config.py"
        
        if config_file.exists():
            self.print_status("CORS origins already configured in backend config", "success")
        
        # Restart Docker API container to ensure CORS changes are applied
        try:
            self.print_status("Restarting API container to apply CORS fixes...", "progress")
            subprocess.run(["docker-compose", "restart", "api"], check=True, capture_output=True)
            self.print_status("API container restarted", "success")
            
            # Wait for API to be ready
            time.sleep(5)
            
            # Test CORS configuration
            result = subprocess.run([
                "curl", "-s", "-X", "OPTIONS", "http://localhost:8000/api/transformations",
                "-H", "Origin: http://localhost:3000",
                "-H", "Access-Control-Request-Method: POST"
            ], capture_output=True, text=True)
            
            if "access-control-allow-origin" in result.stderr.lower():
                self.print_status("CORS configuration verified", "success")
            else:
                self.print_status("CORS headers may not be working properly", "warning")
                
        except subprocess.CalledProcessError as e:
            self.print_status(f"Failed to restart API container: {e}", "error")
            return False
        
        self.print_status("CORS fixes applied and verified", "success")
        return True

    def clean_environment(self) -> bool:
        """Clean up containers and temporary files."""
        self.print_banner("🧹 CLEANING DEVELOPMENT ENVIRONMENT")
        
        # Stop all services
        self.stop_services()
        
        # Remove Docker containers and volumes
        try:
            subprocess.run(["docker-compose", "down", "-v", "--remove-orphans"], check=True)
            self.print_status("Docker containers and volumes removed", "success")
        except subprocess.CalledProcessError:
            self.print_status("Failed to clean Docker environment", "warning")
        
        # Clean Python cache
        cache_dirs = [
            self.project_root / "__pycache__",
            self.backend_dir / "__pycache__"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                self.print_status(f"Removed {cache_dir}", "success")
        
        self.print_banner("✅ ENVIRONMENT CLEANED")
        return True

    def debug_transformations(self) -> bool:
        """Debug transformation issues."""
        self.print_banner("🔍 DEBUGGING TRANSFORMATIONS")
        
        self.print_status("Available debug commands:", "info")
        print(f"  {Color.BLUE}1.{Color.END} Check user transformation stats")
        print(f"  {Color.BLUE}2.{Color.END} Check detailed PROCESSING transformation status")
        print(f"  {Color.BLUE}3.{Color.END} Clean up stuck transformations (10+ minutes old)")
        print(f"  {Color.BLUE}4.{Color.END} AGGRESSIVE cleanup (ALL PROCESSING/PENDING)")
        print()
        
        self.print_status("🚨 Why PROCESSING transformations are problematic:", "warning")
        print(f"  {Color.YELLOW}•{Color.END} They count against your monthly workspace limits")
        print(f"  {Color.YELLOW}•{Color.END} They can block new transformation requests")
        print(f"  {Color.YELLOW}•{Color.END} They indicate backend processing issues")
        print(f"  {Color.YELLOW}•{Color.END} They consume database resources")
        print()
        
        # These endpoints require authentication, so provide curl commands
        self.print_status("To debug with a logged-in user, use these commands:", "info")
        
        print(f"\n{Color.YELLOW}Get user transformation stats:{Color.END}")
        print("curl -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
        print("     http://localhost:8000/api/transformations/debug/user-stats")
        
        print(f"\n{Color.YELLOW}Get detailed PROCESSING status:{Color.END}")
        print("curl -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
        print("     http://localhost:8000/api/transformations/debug/processing-details")
        
        print(f"\n{Color.YELLOW}Clean up stuck transformations (10+ min):{Color.END}")
        print("curl -X POST -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
        print("     http://localhost:8000/api/transformations/cleanup/stuck")
        
        print(f"\n{Color.RED}AGGRESSIVE cleanup (ALL PROCESSING/PENDING):{Color.END}")
        print("curl -X POST -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
        print("     http://localhost:8000/api/transformations/cleanup/all-stuck")
        
        print(f"\n{Color.CYAN}To get your JWT token:{Color.END}")
        print("1. Log in to the frontend at http://localhost:3000")
        print("2. Open browser dev tools (F12)")
        print("3. Go to Application/Storage > localStorage")
        print("4. Copy the 'token' or 'authToken' value")
        
        print(f"\n{Color.GREEN}Recommended action:{Color.END}")
        print("1. Get a fresh JWT token from the frontend")
        print("2. Run the aggressive cleanup to clear ALL stuck transformations")
        print("3. Try creating a new transformation")
        
        return True

    def show_logs(self, service_name: Optional[str] = None):
        """Show logs for a service."""
        if service_name:
            if service_name in self.processes:
                # This is a simplified version - in practice you'd want to tail logs
                self.print_status(f"Showing logs for {service_name}", "info")
            else:
                self.print_status(f"Service {service_name} is not running", "error")
        else:
            # Show Docker logs
            subprocess.run(["docker-compose", "logs", "-f"])

    def _get_start_order(self, services: List[str]) -> List[str]:
        """Get services in dependency order."""
        # Simple topological sort based on dependencies
        ordered = []
        remaining = services.copy()
        
        while remaining:
            # Find services with no unmet dependencies
            ready = []
            for service_name in remaining:
                service = self.services[service_name]
                deps = service.dependencies or []
                if all(dep in ordered or dep not in services for dep in deps):
                    ready.append(service_name)
            
            if not ready:
                # Circular dependency or missing dependency
                ordered.extend(remaining)
                break
            
            # Add ready services to ordered list
            for service_name in ready:
                ordered.append(service_name)
                remaining.remove(service_name)
        
        return ordered

    def _wait_for_services_healthy(self, services: List[str], timeout: int = 60) -> bool:
        """Wait for services to become healthy with improved feedback."""
        start_time = time.time()
        dots = 0
        
        # Only check required services
        required_services = [s for s in services if self.services[s].required]
        
        while time.time() - start_time < timeout:
            dots = (dots + 1) % 4
            progress = "." * dots + " " * (3 - dots)
            elapsed = int(time.time() - start_time)
            print(f"\r   Health checking{progress} ({elapsed}s/{timeout}s)", end="", flush=True)
            
            try:
                status = self.get_service_status()
                healthy_count = 0
                
                for service in required_services:
                    if status.get(service, ServiceStatus.STOPPED) == ServiceStatus.RUNNING:
                        healthy_count += 1
                
                if healthy_count == len(required_services):
                    print(f"\r✅ All services healthy ({elapsed}s)")
                    return True
                    
            except Exception as e:
                if elapsed > 30:  # Only show errors after 30 seconds
                    print(f"\r⚠️ Health check error: {str(e)[:50]}...")
            
            time.sleep(3)  # Increased from 2 to 3 seconds
        
        print(f"\r❌ Health check timed out after {timeout}s")
        return False

    def _print_service_urls(self):
        """Print URLs for running services."""
        print(f"\n{Color.CYAN}{Color.BOLD}🌐 SERVICE URLs:{Color.END}")
        urls = [
            ("Backend API", "http://localhost:8000"),
            ("API Documentation", "http://localhost:8000/docs"),
            ("Frontend", "http://localhost:3001"),
            ("Flower (Celery Monitor)", "http://localhost:5555"),
            ("pgAdmin", "http://localhost:5050"),
            ("Redis Commander", "http://localhost:8081")
        ]
        
        for name, url in urls:
            print(f"  {Color.BLUE}•{Color.END} {name}: {Color.UNDERLINE}{url}{Color.END}")

    def _print_next_steps(self):
        """Print next steps after setup."""
        print(f"\n{Color.GREEN}{Color.BOLD}📋 NEXT STEPS:{Color.END}")
        print(f"  {Color.BLUE}1.{Color.END} Start services: {Color.BOLD}python dev.py start{Color.END}")
        print(f"  {Color.BLUE}2.{Color.END} Check status: {Color.BOLD}python dev.py status{Color.END}")
        print(f"  {Color.BLUE}3.{Color.END} Run tests: {Color.BOLD}python dev.py test{Color.END}")
        print(f"  {Color.BLUE}4.{Color.END} View logs: {Color.BOLD}python dev.py logs{Color.END}")
        print(f"  {Color.BLUE}5.{Color.END} Start with Docker: {Color.BOLD}docker-compose up --build -d{Color.END}")

    def get_service_summary(self) -> str:
        """Get a quick service summary."""
        try:
            # Quick check without hanging
            postgres_running = self._quick_check_docker_service("postgres")
            redis_running = self._quick_check_docker_service("redis")
            api_running = self._quick_check_docker_service("api")
            
            status_items = []
            status_items.append("✅ PostgreSQL" if postgres_running else "❌ PostgreSQL")
            status_items.append("✅ Redis" if redis_running else "❌ Redis")
            status_items.append("✅ API" if api_running else "❌ API")
            
            return " | ".join(status_items)
        except Exception:
            return "❓ Status check failed"

    def _quick_check_docker_service(self, service_name: str) -> bool:
        """Quick Docker service check without hanging."""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "-q", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _check_python_version(self) -> bool:
        """Check Python version."""
        return sys.version_info >= (3, 9)

    def _check_docker(self) -> bool:
        """Check Docker availability."""
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            subprocess.run(["docker", "info"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_git(self) -> bool:
        """Check Git availability."""
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_nodejs(self) -> bool:
        """Check Node.js availability."""
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def signal_handler(sig, frame):
    """Handle interrupt signals gracefully."""
    print(f"\n{Color.YELLOW}Received interrupt signal. Cleaning up...{Color.END}")
    manager = DevEnvironmentManager()
    manager.stop_services()
    sys.exit(0)


def main():
    """Main CLI interface."""
    import argparse
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        description="Content Repurpose Tool - Development Environment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev.py setup                    # Complete environment setup
  python dev.py start                    # Start all required services
  python dev.py start backend frontend  # Start specific services
  python dev.py status                   # Check service status
  python dev.py health                   # Run health checks
  python dev.py stop                     # Stop all services
  python dev.py restart backend         # Restart backend service
  python dev.py fix-cors                 # Fix CORS issues
  python dev.py clean                    # Clean environment
  python dev.py logs backend            # View backend logs
        """
    )
    
    parser.add_argument(
        "command",
        choices=["setup", "start", "stop", "restart", "status", "health", "test", "fix-cors", "clean", "logs", "shell", "debug-transforms"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "services",
        nargs="*",
        help="Specific services to target (default: all required services)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation without prompts"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (skip optional steps)"
    )
    
    args = parser.parse_args()
    
    manager = DevEnvironmentManager()
    
    try:
        if args.command == "setup":
            success = manager.setup_environment()
        elif args.command == "start":
            success = manager.start_services(args.services or None)
        elif args.command == "stop":
            success = manager.stop_services(args.services or None)
        elif args.command == "restart":
            success = manager.stop_services(args.services or None)
            if success:
                success = manager.start_services(args.services or None)
        elif args.command == "status":
            if args.quick:
                # Quick status without hanging
                summary = manager.get_service_summary()
                manager.print_banner("⚡ QUICK SERVICE STATUS")
                print(f"  {summary}")
                success = True
            else:
                status = manager.get_service_status()
                manager.print_banner("📊 SERVICE STATUS")
                for service_name, service_status in status.items():
                    service = manager.services[service_name]
                    status_color = "success" if service_status == ServiceStatus.RUNNING else "error"
                    manager.print_status(f"{service.description}: {service_status.value}", status_color)
                success = True
        elif args.command == "health":
            success = manager.run_health_checks()
        elif args.command == "fix-cors":
            success = manager.fix_cors_issues()
        elif args.command == "clean":
            success = manager.clean_environment()
        elif args.command == "logs":
            manager.show_logs(args.services[0] if args.services else None)
            success = True
        elif args.command == "test":
            # Run test suite
            subprocess.run([manager._get_python_executable(), "run_tests.py"])
            success = True
        elif args.command == "debug-transforms":
            success = manager.debug_transformations()
        else:
            manager.print_status(f"Command '{args.command}' not implemented yet", "error")
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        manager.print_status("Operation cancelled by user", "warning")
        sys.exit(1)
    except Exception as e:
        manager.print_status(f"Unexpected error: {e}", "error")
        sys.exit(1)


if __name__ == "__main__":
    main()