"""
Docker Test Manager - Docker-First Testing Strategy
===================================================

Manages Docker containers and services for testing with:
- Automatic service dependency resolution
- Health checks with retry logic
- Test-specific Docker Compose profiles
- Proper cleanup and isolation
- Cross-platform compatibility
"""

import os
import time
import subprocess
import yaml
import docker
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import json
from contextlib import contextmanager


class DockerTestManager:
    """Manages Docker services for testing with automatic health checks and cleanup."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.docker_client = None
        self.compose_file = self.project_root / "docker-compose.yml" 
        self.test_compose_file = self.project_root / "docker-compose.test.yml"
        self.running_services: Dict[str, str] = {}
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
        except Exception as e:
            print(f"⚠️  Docker not available: {e}")
    
    def validate_docker_environment(self) -> bool:
        """Validate Docker is available and working."""
        if not self.docker_client:
            return False
        
        try:
            # Test basic Docker functionality
            self.docker_client.images.list()
            return True
        except Exception:
            return False
    
    def create_test_compose_profile(self, 
                                   services: List[str] = None,
                                   test_name: str = "default") -> Path:
        """
        Create a test-specific Docker Compose file with optimized settings.
        
        Args:
            services: List of services to include (default: all essential services)
            test_name: Name for the test profile
            
        Returns:
            Path to generated compose file
        """
        if services is None:
            services = ["postgres-test", "redis-test", "api-test", "celery-worker-test"]
        
        # Load base test compose
        with open(self.test_compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Filter services
        if 'services' in compose_config:
            filtered_services = {
                name: config for name, config in compose_config['services'].items()
                if name in services
            }
            compose_config['services'] = filtered_services
        
        # Optimize for testing
        for service_name, service_config in compose_config.get('services', {}).items():
            # Reduce startup time
            if 'healthcheck' in service_config:
                service_config['healthcheck']['interval'] = '2s'
                service_config['healthcheck']['timeout'] = '2s'
                service_config['healthcheck']['retries'] = 15
            
            # Use test-specific container names
            if 'container_name' in service_config:
                service_config['container_name'] = f"{service_config['container_name']}-{test_name}"
        
        # Create temporary compose file
        temp_compose = self.project_root / f"docker-compose.test.{test_name}.yml"
        with open(temp_compose, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        return temp_compose
    
    def start_services(self, 
                      services: List[str] = None,
                      wait_for_health: bool = True,
                      timeout: int = 300) -> bool:
        """
        Start Docker services with health check waiting.
        
        Args:
            services: List of services to start
            wait_for_health: Whether to wait for health checks
            timeout: Maximum time to wait for services
            
        Returns:
            bool: True if all services started successfully
        """
        if not self.validate_docker_environment():
            print("❌ Docker environment not available")
            return False
        
        if services is None:
            services = ["postgres-test", "redis-test"]
        
        print(f"🐳 Starting Docker services: {', '.join(services)}")
        
        try:
            # Use test compose file
            cmd = [
                "docker-compose", 
                "-f", str(self.test_compose_file),
                "up", "-d"
            ] + services
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to start services: {result.stderr}")
                return False
            
            print(f"✅ Services started successfully")
            
            # Track running services
            for service in services:
                self.running_services[service] = f"{service}-container"
            
            if wait_for_health:
                return self.wait_for_services_health(services, timeout)
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout starting services")
            return False
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            return False
    
    def wait_for_services_health(self, 
                                services: List[str], 
                                timeout: int = 300) -> bool:
        """
        Wait for services to become healthy with progress indication.
        
        Args:
            services: List of services to check
            timeout: Maximum time to wait
            
        Returns:
            bool: True if all services become healthy
        """
        print(f"⏳ Waiting for services to become healthy (timeout: {timeout}s)...")
        
        start_time = time.time()
        check_interval = 2
        
        healthy_services = set()
        
        while time.time() - start_time < timeout:
            for service in services:
                if service in healthy_services:
                    continue
                
                if self.check_service_health(service):
                    print(f"  ✅ {service} is healthy")
                    healthy_services.add(service)
                else:
                    print(f"  ⏳ {service} starting...")
            
            if len(healthy_services) == len(services):
                elapsed = time.time() - start_time
                print(f"🎉 All services healthy in {elapsed:.1f}s")
                return True
            
            time.sleep(check_interval)
        
        # Timeout reached
        unhealthy = set(services) - healthy_services
        print(f"❌ Timeout waiting for services: {', '.join(unhealthy)}")
        
        # Provide diagnostic information
        for service in unhealthy:
            self.diagnose_service_issues(service)
        
        return False
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a specific service is healthy."""
        try:
            # Get container name from test compose
            container_name = f"content-repurpose-{service_name}"
            
            container = self.docker_client.containers.get(container_name)
            
            # Check if container is running
            if container.status != 'running':
                return False
            
            # Check health status if available
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                return health.get('Status') == 'healthy'
            
            # If no health check, assume healthy if running
            return True
            
        except docker.errors.NotFound:
            return False
        except Exception:
            return False
    
    def diagnose_service_issues(self, service_name: str) -> Dict:
        """Diagnose issues with a service and provide actionable feedback."""
        diagnosis = {
            "service": service_name,
            "status": "unknown",
            "issues": [],
            "suggestions": []
        }
        
        try:
            container_name = f"content-repurpose-{service_name}"
            container = self.docker_client.containers.get(container_name)
            
            diagnosis["status"] = container.status
            
            # Get logs for analysis
            logs = container.logs(tail=50).decode('utf-8', errors='ignore')
            diagnosis["recent_logs"] = logs
            
            # Analyze common issues
            if "connection refused" in logs.lower():
                diagnosis["issues"].append("Connection refused - service may not be fully started")
                diagnosis["suggestions"].append("Wait longer for service initialization")
            
            if "out of memory" in logs.lower():
                diagnosis["issues"].append("Out of memory error")
                diagnosis["suggestions"].append("Increase Docker memory limits")
            
            if "permission denied" in logs.lower():
                diagnosis["issues"].append("Permission denied error")
                diagnosis["suggestions"].append("Check volume mount permissions")
            
            # Port conflicts
            if "port already in use" in logs.lower():
                diagnosis["issues"].append("Port conflict detected")
                diagnosis["suggestions"].append("Stop conflicting services or change ports")
            
        except docker.errors.NotFound:
            diagnosis["issues"].append("Container not found")
            diagnosis["suggestions"].append("Check if service is defined in docker-compose.test.yml")
        except Exception as e:
            diagnosis["issues"].append(f"Diagnostic error: {e}")
        
        # Print diagnosis
        print(f"\n🔍 Diagnosis for {service_name}:")
        print(f"   Status: {diagnosis['status']}")
        if diagnosis["issues"]:
            print(f"   Issues: {'; '.join(diagnosis['issues'])}")
        if diagnosis["suggestions"]:
            print(f"   Suggestions: {'; '.join(diagnosis['suggestions'])}")
        
        return diagnosis
    
    def stop_services(self, services: List[str] = None, remove_volumes: bool = True):
        """Stop and cleanup Docker services."""
        if services is None:
            services = list(self.running_services.keys())
        
        if not services:
            print("ℹ️  No services to stop")
            return
        
        print(f"🛑 Stopping services: {', '.join(services)}")
        
        try:
            cmd = [
                "docker-compose",
                "-f", str(self.test_compose_file),
                "down"
            ]
            
            if remove_volumes:
                cmd.append("--volumes")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Services stopped successfully")
                self.running_services.clear()
            else:
                print(f"⚠️  Warning stopping services: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error stopping services: {e}")
    
    def cleanup_test_artifacts(self):
        """Clean up temporary Docker Compose files and test artifacts."""
        patterns = [
            "docker-compose.test.*.yml",
            "testing/diagnostic_report.json"
        ]
        
        cleaned = 0
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    file_path.unlink()
                    cleaned += 1
                except Exception:
                    pass
        
        if cleaned > 0:
            print(f"🧹 Cleaned up {cleaned} test artifacts")
    
    @contextmanager
    def test_services(self, 
                     services: List[str] = None,
                     auto_cleanup: bool = True):
        """
        Context manager for test services with automatic cleanup.
        
        Usage:
            with docker_manager.test_services(['postgres-test', 'redis-test']):
                # Run tests
                pass
        """
        services_started = False
        
        try:
            services_started = self.start_services(services)
            if not services_started:
                raise RuntimeError("Failed to start test services")
            
            yield self
            
        finally:
            if auto_cleanup and services_started:
                self.stop_services(services)
                self.cleanup_test_artifacts()
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> str:
        """Get recent logs from a service."""
        try:
            container_name = f"content-repurpose-{service_name}"
            container = self.docker_client.containers.get(container_name)
            return container.logs(tail=lines).decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error getting logs: {e}"
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all running services."""
        status = {}
        
        for service_name in self.running_services:
            try:
                container_name = f"content-repurpose-{service_name}"
                container = self.docker_client.containers.get(container_name)
                
                status[service_name] = {
                    "status": container.status,
                    "health": container.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown'),
                    "ports": container.ports,
                    "uptime": container.attrs.get('State', {}).get('StartedAt')
                }
            except docker.errors.NotFound:
                status[service_name] = {"status": "not_found"}
            except Exception as e:
                status[service_name] = {"status": "error", "error": str(e)}
        
        return status


def main():
    """Command-line interface for Docker test management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Docker Test Manager")
    parser.add_argument("--start", nargs="*", help="Start services")
    parser.add_argument("--stop", nargs="*", help="Stop services") 
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--logs", help="Show logs for service")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup test artifacts")
    
    args = parser.parse_args()
    
    manager = DockerTestManager()
    
    if args.start is not None:
        services = args.start if args.start else None
        manager.start_services(services)
    
    if args.stop is not None:
        services = args.stop if args.stop else None
        manager.stop_services(services)
    
    if args.status:
        status = manager.get_service_status()
        print(json.dumps(status, indent=2))
    
    if args.logs:
        logs = manager.get_service_logs(args.logs)
        print(logs)
    
    if args.cleanup:
        manager.cleanup_test_artifacts()


if __name__ == "__main__":
    main()