"""
Bulletproof Testing Framework for Multi-Phase Development
=========================================================

A comprehensive testing framework designed for scalable, multi-phase development
with automatic environment setup, Docker orchestration, and intelligent error handling.

Key Features:
- Self-healing environment detection and repair
- Docker-first testing with automatic service management
- Phase-agnostic test discovery and execution
- Intelligent error handling with diagnostic tools
- Developer experience optimization

Usage:
    python testing/run_tests.py --phase 5 --mode integration
    python testing/run_tests.py --all --parallel
    python testing/setup_env.py --validate --fix
"""

__version__ = "1.0.0"
__author__ = "Content Repurpose Development Team"

from .environment import EnvironmentManager
from .docker_manager import DockerTestManager
from .test_runner import PhaseTestRunner
from .diagnostics import DiagnosticToolkit

__all__ = [
    "EnvironmentManager",
    "DockerTestManager",
    "PhaseTestRunner",
    "DiagnosticToolkit",
]
