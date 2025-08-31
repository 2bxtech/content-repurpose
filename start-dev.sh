#!/bin/bash

# Content Repurposing Tool - Development Startup Script
# This script sets up the complete development environment

set -e

echo "🚀 Starting Content Repurposing Tool Development Environment"
echo "============================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. You can customize it if needed."
else
    echo "✅ .env file already exists"
fi

# Start PostgreSQL and Redis containers
echo "🐘 Starting PostgreSQL and Redis containers..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec postgres pg_isready -U postgres -d content_repurpose > /dev/null 2>&1; do
    sleep 2
    echo "   Still waiting for PostgreSQL..."
done

echo "✅ PostgreSQL is ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
until docker-compose exec redis redis-cli ping > /dev/null 2>&1; do
    sleep 2
    echo "   Still waiting for Redis..."
done

echo "✅ Redis is ready"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo ""
echo "🎉 Development environment is ready!"
echo "============================================================"
echo ""
echo "Services running:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • pgAdmin: http://localhost:5050 (admin@contentrepurpose.local / admin123)"
echo "  • Redis Commander: http://localhost:8081"
echo ""
echo "To start the FastAPI server, run:"
echo "  cd backend && python main.py"
echo ""
echo "To stop the containers, run:"
echo "  docker-compose down"
echo ""