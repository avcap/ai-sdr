#!/bin/bash

echo "🚀 Setting up AI SDR with Google OAuth Integration..."

# Create Python virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "📦 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-google.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Setup environment files
echo "📝 Setting up environment files..."
if [ ! -f .env ]; then
    cp env.google.example .env
    echo "✅ Created .env file. Please edit it with your API keys."
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local file."
fi

# Set up database
echo "🗄️  Setting up database..."
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
echo "📋 Next Steps:"
echo "1. Set up Google OAuth credentials:"
echo "   - Go to https://console.cloud.google.com/"
echo "   - Create OAuth 2.0 credentials"
echo "   - Add http://localhost:3000/auth/google/callback as redirect URI"
echo "   - Update .env with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
echo ""
echo "2. Start the application:"
echo "   - Backend: source venv/bin/activate && python backend/main.py"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📖 For detailed Google OAuth setup, see GOOGLE_OAUTH_SETUP.md"


