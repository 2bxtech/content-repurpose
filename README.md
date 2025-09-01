# Content Transformation Platform

FastAPI backend with PostgreSQL multi-tenant architecture, Celery background processing, and WebSocket real-time features for content workflow automation.

- **Multi-Tenant Architecture**: PostgreSQL Row-Level Security with workspace isolation, JWT authentication with refresh tokens
- **Async Background Processing**: Celery workers with Redis broker, task lifecycle management, AI provider integration  
- **Real-Time Features**: WebSocket connections, live transformation updates, Redis pub/sub messaging
- **Database Foundation**: SQLAlchemy async sessions, Alembic migrations, audit trails, soft deletes
- **Testing Infrastructure**: pytest framework with Docker automation, environment validation with auto-repair
- **Configuration Management**: Dependency injection, workspace context management, connection pooling

## Technology Stack

**API Layer**: FastAPI 0.104.1, Python 3.12+, OpenAPI documentation  
**Authentication**: JWT access (15min) + refresh (7day) tokens, BCrypt hashing, Redis session management  
**Database**: PostgreSQL 16 with Row-Level Security, SQLAlchemy async ORM, Alembic migrations  
**Background Processing**: Celery 5.3.4 workers, Redis 7-alpine broker, task status tracking  
**Real-Time**: WebSocket connections, Redis pub/sub messaging  
**AI Integration**: OpenAI/Anthropic providers with automatic failover, rate limiting  
**Testing**: pytest with Docker isolation, environment validation, coverage reporting  
**Infrastructure**: Docker Compose orchestration, environment-based config

## System Architecture

Multi-tenant backend with async task processing, real-time WebSocket features, and workspace isolation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI        │    │  Celery Worker  │    │  PostgreSQL     │
│  • JWT Auth     │◄──►│  • Redis Broker │    │  • Row Level    │
│  • Workspace    │    │  • AI Tasks     │    │    Security     │
│  • WebSockets   │    │  • Status Track │    │  • Multi-tenant │
│  • OpenAPI      │    │  • Notifications│    │  • Async Driver │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │   AI Providers  │    │   Testing       │
│  • Session Mgmt │    │  • OpenAI       │    │  • pytest       │
│  • Task Queue   │    │  • Anthropic    │    │  • Docker       │
│  • WebSocket    │    │  • Failover     │    │  • Validation   │
│  • Pub/Sub      │    │  • Rate Limits  │    │  • Auto-repair  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Implementation Status

### Phase 1-5 Complete
- **JWT Authentication**: Access/refresh token pattern, Redis session management, BCrypt hashing
- **Multi-Tenant Database**: PostgreSQL RLS policies, workspace isolation, audit trails, soft deletes  
- **Celery Background Processing**: Redis broker, task lifecycle tracking, AI provider integration
- **WebSocket Real-Time Features**: Live transformation updates, workspace presence, Redis pub/sub integration
- **Database Schema**: User/Document/Transformation models with workspace scoping, Alembic migrations
- **API Layer**: FastAPI with dependency injection, workspace context management, OpenAPI documentation

### Phase 5b: Testing Framework Enhancement
- **Environment Validation**: Auto-detects missing dependencies and package structure issues
- **Docker Service Management**: Automated service orchestration with health checks
- **Test Discovery**: Phase-agnostic test execution with unit/integration/e2e categorization
- **Diagnostic Toolkit**: Root cause analysis with actionable solutions
- **Developer Setup**: One-command environment configuration

### Technical Implementation Details
- **Connection Pooling**: 20 base + 30 overflow connections for concurrent request handling
- **Task Management**: Real-time status tracking, cancellation support, worker monitoring endpoints
- **Multi-Provider AI**: OpenAI/Anthropic integration with automatic failover and rate limiting
- **Security**: Refresh token rotation, input validation, audit logging, workspace access control
- **Cross-Platform**: Windows/Linux compatible scripts, Git Bash support, Docker orchestration
- **WebSocket Implementation**: Redis pub/sub for multi-instance message broadcasting

### Phase 6: Frontend Interface & File Processing (Next)
- **React Frontend**: Document upload and transformation workflow interface
- **File Processing**: PDF/DOCX parsing with security validation
- **Workspace Management**: Member invitations, role management
- **Production Deployment**: Kubernetes configuration, monitoring setup

## Quick Start

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- AI API key (OpenAI or Anthropic)

### Setup
```bash
git clone https://github.com/2bxtech/content-repurpose.git
cd content-repurpose
cp .env.example .env
# Edit .env with your AI API key and database settings

# One-command setup (recommended)
python setup_dev_environment.py

# Manual setup
docker-compose up -d postgres redis
cd backend && python -m alembic upgrade head
```

### Testing and Validation
```bash
# Environment validation with auto-repair
python testing/run_tests.py --validate --fix

# Quick validation (< 1 second)
python testing/run_tests.py --quick-validate

# Full test suite
python testing/run_tests.py
```

### Development
```bash
# Start API server
cd backend && python main.py

# Start Celery worker (separate terminal)
cd backend && celery -A app.core.celery_app worker --loglevel=info
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **WebSocket Endpoint**: ws://localhost:8000/api/ws

## Development

### Architecture Decisions
- **PostgreSQL RLS**: Chosen for automatic multi-tenant data isolation at database level
- **JWT + Redis Pattern**: Reduces database auth queries while maintaining stateless API design  
- **Celery Task Queue**: Prevents HTTP request blocking during AI processing operations
- **WebSocket + Redis Pub/Sub**: Enables real-time updates across multiple application instances
- **Docker-First Testing**: Ensures consistent test environments across development machines

### Environment Management
```bash
# Clone and setup
git clone https://github.com/2bxtech/content-repurpose.git
cd content-repurpose && cp .env.example .env

# Automated setup
python setup_dev_environment.py

# Validation and diagnostics
python testing/run_tests.py --validate --fix
python testing/run_tests.py --diagnose --fix
```

### Testing Framework
```bash
# Test execution
python testing/run_tests.py                     # Full test suite
python testing/run_tests.py --unit              # Unit tests only
python testing/run_tests.py --integration       # Integration tests only
python testing/run_tests.py --quick             # Fast validation tests

# WebSocket testing
python validate_phase5.py                       # Phase 5 validation
python test_phase5_automated.py                 # WebSocket integration tests
```

## License

MIT License - see [LICENSE](LICENSE) file for details.