#!/bin/bash
# PharmaGuard 2.0 - Automated Setup Script (Mac/Linux)

echo "🚀 PharmaGuard 2.0 - Quick Setup Script"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "📦 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check Node
echo ""
echo "📦 Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Setup Backend
echo ""
echo "🔧 Setting up Backend..."
cd pharmaguard-backend

echo "   Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

if [ ! -f .env ]; then
    echo "   Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
fi

cd ..

# Setup Frontend
echo ""
echo "🔧 Setting up Frontend..."
cd pharmaguard-frontend

echo "   Installing dependencies..."
npm install --legacy-peer-deps > /dev/null 2>&1

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Edit the backend configuration:"
echo "   nano pharmaguard-backend/.env"
echo "   → Add your OPENAI_API_KEY"
echo ""
echo "2. Start the backend (Terminal 1):"
echo "   cd pharmaguard-backend"
echo "   python -m uvicorn app.main:app --reload --port 8000"
echo ""
echo "3. Start the frontend (Terminal 2):"
echo "   cd pharmaguard-frontend"
echo "   npm run dev"
echo ""
echo "4. Open browser:"
echo "   http://localhost:3003"
echo ""
echo "5. Register/Login to start analyzing!"
echo ""
