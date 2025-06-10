#!/bin/bash

echo "🚀 Starting Reddit Pain Finder Phase 3 Services..."

# Function to check if port is in use (Windows-compatible)
check_port() {
    netstat -an | grep ":$1" > /dev/null 2>&1
}

# Kill any existing services (Windows-compatible)
echo "🧹 Cleaning up existing services..."
if check_port 8000; then
    echo "Port 8000 appears to be in use, attempting to stop..."
    # On Windows, we'll just note it and continue
fi

if check_port 3000; then
    echo "Port 3000 appears to be in use, attempting to stop..."
    # On Windows, we'll just note it and continue
fi

# Make sure we're in the phase3 directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the phase3 directory"
    echo "Current directory: $(pwd)"
    echo "Expected to find 'backend' and 'frontend' directories"
    exit 1
fi

# Start backend
echo "🔧 Starting FastAPI backend..."
cd backend
echo "📂 Backend directory: $(pwd)"

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Start backend in background
python backend.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running with a simple HTTP request
echo "🔍 Checking backend health..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend started successfully on http://localhost:8000"
else
    echo "⚠️ Backend may still be starting, continuing with frontend..."
fi

# Start frontend
echo "🎨 Starting Next.js frontend..."
cd frontend
echo "📂 Frontend directory: $(pwd)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 8

# Final health check
echo "🔍 Final health check..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is healthy at http://localhost:8000"
else
    echo "⚠️ Backend may need more time to start"
fi

if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is healthy at http://localhost:3000"
else
    echo "⚠️ Frontend may need more time to start"
fi

echo ""
echo "🎉 Reddit Pain Finder Phase 3 services started!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Docs:  http://localhost:8000/docs"
echo "💡 API Health: http://localhost:8000/"
echo ""
echo "🛠️ Quick Start:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Search for a topic (e.g., 'indie game developers')"
echo "3. Sign up to save searches and set up alerts"
echo ""
echo "🛑 To stop services, press Ctrl+C"
echo ""

# Keep script running and handle Ctrl+C
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Services stopped"; exit 0' INT

# Wait for user to stop
echo "⏸️ Services running... Press Ctrl+C to stop"
wait 