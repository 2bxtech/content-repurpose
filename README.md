# Content Transformation Platform

FastAPI backend with PostgreSQL multi-tenant architecture, Celery background processing, and comprehensive testing infrastructure for content workflow automation.

• **Multi-Tenant Architecture**: PostgreSQL Row-Level Security with workspace isolation, JWT authentication with refresh tokens
• **Async Background Processing**: Celery workers with Redis broker, task lifecycle management, AI provider integration
• **Database Foundation**: SQLAlchemy async sessions, Alembic migrations, audit trails, soft deletes
• **Testing Infrastructure**: pytest framework with Docker Compose automation, HTTP-based testing, coverage reporting
• **Enterprise Patterns**: Dependency injection, workspace context management, connection pooling, error handling

## 🛠️ Technology Stack

**API Layer**: FastAPI 0.104.1, Python 3.12+, OpenAPI documentation, dependency injection  
**Authentication**: JWT access (15min) + refresh (7day) tokens, BCrypt hashing, Redis session management  
**Database**: PostgreSQL 16 with Row-Level Security, SQLAlchemy async ORM, Alembic migrations  
**Background Processing**: Celery 5.3.4 workers, Redis 7-alpine broker, task status tracking  
**AI Integration**: Multi-provider support (OpenAI/Anthropic), automatic failover, rate limiting  
**Testing**: pytest with async fixtures, Docker test isolation, coverage reporting, HTTP client testing  
**Infrastructure**: Docker Compose orchestration, environment-based config, connection pooling (20+30)

## 🏗️ System Architecture

Multi-tenant backend with async task processing and workspace isolation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI        │    │  Celery Worker  │    │  PostgreSQL     │
│  • JWT Auth     │◄──►│  • Redis Broker │    │  • Row Level    │
│  • Workspace    │    │  • AI Tasks     │    │    Security     │
│  • OpenAPI      │    │  • Status Track │    │  • Multi-tenant │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │   AI Providers  │    │   Testing       │
│  • Session Mgmt │    │  • OpenAI       │    │  • pytest      │
│  • Task Queue   │    │  • Anthropic    │    │  • Docker       │
│  • Token Cache  │    │  • Failover     │    │  • HTTP Client  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Key Features**: Workspace context injection, RLS enforcement, async task lifecycle, refresh token rotation

## 🚀 Implementation Status

### ✅ **Phase 1-4 Complete**
- **JWT Authentication System**: Access/refresh token pattern, Redis session management, BCrypt security
- **Multi-Tenant Database**: PostgreSQL RLS policies, workspace isolation, audit trails, soft deletes  
- **Celery Background Processing**: Redis broker, task lifecycle tracking, AI provider integration
- **Testing Infrastructure**: pytest with async fixtures, Docker test environment, HTTP client automation
- **Database Schema**: User/Document/Transformation models with workspace scoping, Alembic migrations
- **API Layer**: FastAPI with dependency injection, workspace context management, OpenAPI documentation

### 🔧 **Technical Implementation Details**
- **Connection Pooling**: 20 base + 30 overflow connections for concurrent request handling
- **Task Management**: Real-time status tracking, cancellation support, worker monitoring endpoints
- **Multi-Provider AI**: OpenAI/Anthropic integration with automatic failover and rate limiting
- **Security**: Refresh token rotation, input validation, audit logging, workspace access control
- **Cross-Platform**: Windows/Linux compatible scripts, Git Bash support, Docker orchestration

### 🚧 **Phase 5: Real-Time Collaboration (Next)**
- **WebSocket Integration**: Live task status updates, collaborative document editing
- **Frontend Interface**: React UI for document upload and transformation workflows
- **Advanced Workspace Features**: Member invitations, role management, plan enforcement
- **Production Deployment**: Kubernetes manifests, monitoring, CI/CD pipeline

## 🚦 Quick Start

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- AI API key (OpenAI, Anthropic, etc.)

### 1. Clone and Setup
```bash
git clone https://github.com/2bxtech/content-repurpose.git
cd content-repurpose
cp .env.example .env
# Edit .env with your AI API key and database settings
```

### 2. Start Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
cd backend
python -m alembic upgrade head

# Start the API server
python main.py
```

### 3. Run Tests
```bash
# Run comprehensive test suite
python run_tests.py

# Or run specific test categories
pytest tests/test_basic.py::TestAuthentication
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Development

### **Architecture Highlights**
- **Multi-Tenant Security**: PostgreSQL RLS with workspace context injection ensures data isolation
- **Stateless Authentication**: JWT pattern with Redis caching reduces database auth latency  
- **Async Task Processing**: Celery workers handle AI operations without blocking HTTP requests
- **Enterprise Testing**: Comprehensive pytest suite with Docker isolation and coverage reporting
- **Cross-Platform Support**: Windows Git Bash and Linux-compatible development environment

### **Development Environment**
```bash
# Clone and setup
git clone https://github.com/2bxtech/content-repurpose.git
cd content-repurpose && cp .env.example .env

# Start services (PostgreSQL, Redis)
docker-compose up -d

# Database setup
cd backend && python -m alembic upgrade head

# Run comprehensive tests
python run_tests.py

# Start development server
python main.py
```

### **Testing Framework**
```bash
# Validate entire testing infrastructure
python validate_tests.py

# Run specific test categories  
pytest tests/test_basic.py::TestAuthentication    # Auth flows
pytest tests/test_basic.py::TestContentTransformation  # Background tasks
pytest tests/test_basic.py::TestUtilities         # Core functionality

# Cross-platform test runners
./quick_test.sh    # Linux/WSL
quick_test.bat     # Windows Git Bash
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
