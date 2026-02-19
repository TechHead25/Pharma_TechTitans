#!/bin/bash

echo "🛡️  PharmaGuard - Pharmacogenomic Risk Prediction Engine"
echo "Starting development environment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Start backend
echo -e "${BLUE}Starting Backend (FastAPI)...${NC}"
cd pharmaguard-backend

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend in background
python run_backend.py &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo ""

# Start frontend
echo -e "${BLUE}Starting Frontend (React + Vite)...${NC}"
cd ../pharmaguard-frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "  App: http://localhost:3000"
echo ""

echo -e "${GREEN}✅ PharmaGuard is running!${NC}"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID  # Stop backend"
echo "  kill $FRONTEND_PID # Stop frontend"
echo ""
echo "Press Ctrl+C to exit"

# Wait for both processes
wait
