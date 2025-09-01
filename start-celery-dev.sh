#!/bin/bash

# Celery Worker and Beat Startup Script for Development

echo "🚀 Starting Celery Services for Content Repurposing Tool"
echo "========================================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source .venv/Scripts/activate
fi

# Navigate to backend directory
cd backend

# Start Redis in background if not running
echo "📡 Checking Redis server..."
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "🔴 Redis not running. Please start Redis server first:"
    echo "   redis-server"
    exit 1
else
    echo "✅ Redis server is running"
fi

# Function to start Celery worker
start_worker() {
    echo "👷 Starting Celery Worker..."
    celery -A app.core.celery_app worker --loglevel=info --concurrency=2 &
    WORKER_PID=$!
    echo "✅ Celery Worker started (PID: $WORKER_PID)"
}

# Function to start Celery beat
start_beat() {
    echo "⏰ Starting Celery Beat Scheduler..."
    celery -A app.core.celery_app beat --loglevel=info &
    BEAT_PID=$!
    echo "✅ Celery Beat started (PID: $BEAT_PID)"
}

# Function to start Flower (Celery monitoring)
start_flower() {
    echo "🌸 Starting Flower (Celery monitoring)..."
    celery -A app.core.celery_app flower --port=5555 &
    FLOWER_PID=$!
    echo "✅ Flower started (PID: $FLOWER_PID) - Available at http://localhost:5555"
}

# Cleanup function
cleanup() {
    echo "🛑 Shutting down Celery services..."
    if [ ! -z "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null
        echo "   Stopped Celery Worker"
    fi
    if [ ! -z "$BEAT_PID" ]; then
        kill $BEAT_PID 2>/dev/null
        echo "   Stopped Celery Beat"
    fi
    if [ ! -z "$FLOWER_PID" ]; then
        kill $FLOWER_PID 2>/dev/null
        echo "   Stopped Flower"
    fi
    exit 0
}

# Set up signal handler
trap cleanup SIGINT SIGTERM

# Start services
start_worker
sleep 2
start_beat
sleep 2
start_flower

echo ""
echo "🎉 All Celery services started successfully!"
echo "========================================================"
echo "📊 Monitoring:"
echo "   • Flower (Web UI): http://localhost:5555"
echo "   • Redis CLI: redis-cli monitor"
echo ""
echo "🔧 Management Commands:"
echo "   • View active tasks: celery -A app.core.celery_app inspect active"
echo "   • View registered tasks: celery -A app.core.celery_app inspect registered"
echo "   • Purge queue: celery -A app.core.celery_app purge"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for interrupt
while true; do
    sleep 1
done