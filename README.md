_Under Development_

# Content Repurposing Tool##

**Current (MVP)**:
```
React Frontend (localhost:3000)
    ↓ HTTP
FastAPI Backend (localhost:8000)
    ├── In-memory storage (users, documents, transformations)
    ├── Local file system (uploads/)
    └── Claude API (AI processing)
```

**Target (Production)**:
```
React Frontend
    ↓ HTTP/WebSocket
FastAPI Main App + Celery Workers
    ├── PostgreSQL (with Row-Level Security)
    ├── Redis (caching, sessions, background jobs)
    └── Multi-provider AI (Claude, OpenAI)
``` React application for transforming documents into different content formats using AI.

**Current Status**: MVP (Minimum Viable Product) - Basic functionality working, production features in development.

[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://python.org)
[![React](https://img.shields.io/badge/react-18.2.0-blue)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104.1-green)](https://fastapi.tiangolo.com)

## 🚀 Current Features

### Working (MVP)
- **File Upload**: PDF, DOCX, TXT, MD support with basic validation
- **AI Transformations**: 6 content types via Anthropic Claude API
- **User Authentication**: JWT-based login/registration
- **Basic UI**: React frontend with Material-UI components

### In Development (Production Roadmap)
- **Database**: Migrating from in-memory to PostgreSQL with Row-Level Security
- **Real-time Features**: WebSocket support for collaboration
- **Enhanced Security**: Refresh tokens, rate limiting, audit logs
- **File Processing**: Real content extraction from PDF/DOCX
- **Multi-tenant**: Workspace-based organization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  External APIs  │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│  (Claude API)   │
│   Port: 3000    │    │   Port: 8000    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Web Browser    │    │  File System    │    │  AI Processing  │
│  (Client State) │    │  (/uploads)     │    │  (Background)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚦 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Anthropic Claude API key

### 1. Clone and Setup
```bash
git clone https://github.com/2bxtech/content-repurpose.git
cd content-repurpose
cp .env.example .env
# Edit .env with your Claude API key
```

### 2. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 3. Frontend
```bash
cd frontend
npm install
npm start
```

### 4. Test
1. Go to http://localhost:3000
2. Register account
3. Upload a document
4. Create transformation

### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Development

### Current Status
- **MVP**: Basic upload, transform, download workflow
- **Database**: In-memory dictionaries (not persistent)
- **File Processing**: Simple file reading (no content extraction)
- **Authentication**: Basic JWT (no refresh tokens)
- **Testing**: Manual testing only

### Tech Stack
- **Backend**: FastAPI 0.104.1, Python 3.12+
- **Frontend**: React 18.2.0, TypeScript, Material-UI
- **AI**: Anthropic Claude API
- **Storage**: Local filesystem + in-memory data

## ️ Development Roadmap

### Week 1-2: Foundation
- [ ] Migrate to PostgreSQL with Row-Level Security
- [ ] Real file content extraction (PDF/DOCX)
- [ ] Enhanced JWT with refresh tokens
- [ ] Redis integration for caching

### Week 3-4: Production Features
- [ ] WebSocket support for real-time updates
- [ ] Celery background processing
- [ ] Multi-provider AI support (Claude + OpenAI)
- [ ] Rate limiting and security hardening

### Week 5-6: Polish
- [ ] Comprehensive testing
- [ ] Docker deployment
- [ ] Performance optimization
- [ ] Production documentation

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed implementation steps.

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup for Contributors
```bash
# Install development dependencies
cd backend && pip install -r requirements-dev.txt
cd frontend && npm install --include=dev

# Run tests before submitting
pytest  # Backend tests
npm test  # Frontend tests
```

## 📊 Current Limitations

**Data Persistence**: All data lost on server restart (in-memory storage)  
**File Processing**: Basic file reading, no content extraction from PDFs  
**Security**: No rate limiting, basic JWT implementation  
**Testing**: Manual testing only, no automated test suite  
**Deployment**: Development setup only, no production deployment  

These limitations are addressed in the production roadmap.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
