# Development Files Tracking

This document tracks development-only files that should be cleaned up or gitignored for production readiness.

## Phase 4: Background Processing Development Files

### 🧪 Test & Debug Scripts (Should be .gitignored)
- `diagnostic_server.py` - Server shutdown debugging script
- `test_minimal_server.py` - Minimal FastAPI server for isolation testing
- `test_health.py` - Quick health check script
- `test_server_request.py` - HTTP client testing script
- `test_phase4_complete.py` - Comprehensive Phase 4 test suite
- `test_phase4_comprehensive.py` - Docker-based test automation
- `test_phase4_docker.bat` - Windows Docker test script
- `test_phase4_docker.sh` - Linux Docker test script
- `verify_phase4_success.py` - Implementation verification script

### 🔧 Windows Development Compatibility Scripts (Should be .gitignored)
- `server_gitbash_fix.py` - Git Bash signal handling workaround
- `server_hypercorn.py` - Alternative ASGI server testing
- `server_powershell.py` - PowerShell-optimized launcher
- `server_threaded.py` - Threaded server approach for Windows
- `smart_windows_server.py` - Terminal detection and adaptation
- `start_server_windows.py` - Windows-compatible server startup

### 📋 Celery Development Tools (Keep for development)
- `backend/test_celery_integration.py` - Celery functionality testing
- `start-celery-dev.sh` - Development Celery startup (Linux/Mac)
- `start-celery-dev.bat` - Development Celery startup (Windows)

## Action Items

### Immediate (Post Phase 4 Commit)
- [ ] Add above test/debug files to `.gitignore`
- [ ] Move test scripts to `tests/` directory
- [ ] Create proper test configuration for CI/CD

### Future Cleanup
- [ ] Consolidate Windows compatibility scripts into single launcher
- [ ] Create proper development documentation
- [ ] Set up automated testing pipeline
- [ ] Remove debugging artifacts from main codebase

## .gitignore Additions Needed

```gitignore
# Development and debugging scripts
diagnostic_server.py
test_minimal_server.py
test_health.py
test_server_request.py
server_*.py
smart_windows_server.py
start_server_windows.py
verify_phase4_success.py

# Phase-specific test files
test_phase*.py
test_phase*.bat
test_phase*.sh

# Development artifacts
*.diff
```

## Notes

- Keep Celery development scripts as they're useful for ongoing development
- Test files should eventually move to proper `tests/` directory structure
- Windows compatibility scripts were necessary for development but not for production
- Document any permanent solutions for cross-platform development

## Senior Engineering Best Practices

This tracking ensures:
- ✅ Clean production codebase
- ✅ Organized development workflow  
- ✅ Easy cleanup and maintenance
- ✅ Professional repository management
- ✅ Future team onboarding clarity