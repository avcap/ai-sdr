#!/bin/bash

# Simple AI SDR Setup Script
# This script sets up the AI SDR application with minimal dependencies

echo "🚀 Setting up AI SDR Application (Simple Mode)..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "📦 Creating Python virtual environment..."
python3 -m venv venv

echo "📦 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-simple.txt

echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo "📝 Setting up environment files..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Created .env file. Please edit it with your API keys."
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local file."
fi

echo "🗄️  Setting up database..."
# Create SQLite database if it doesn't exist
if [ ! -f ai_sdr.db ]; then
    source venv/bin/activate
    python -c "
from backend.main import Base, engine
Base.metadata.create_all(bind=engine)
print('Database created successfully')
"
fi

echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "1. Edit .env with your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start the backend: python backend/main.py"
echo "4. Start the frontend: cd frontend && npm run dev"
echo ""
echo "Access the application at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo ""
echo "Demo credentials:"
echo "- Email: demo@example.com"
echo "- Password: password"


