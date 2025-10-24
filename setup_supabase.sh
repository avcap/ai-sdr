#!/bin/bash

# Multi-Tenant AI SDR Platform Setup Script
# This script helps you set up the Supabase integration

echo "🚀 Multi-Tenant AI SDR Platform Setup"
echo "====================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create .env file with your Supabase credentials"
    echo ""
    echo "Required environment variables:"
    echo "SUPABASE_URL=https://your-project-id.supabase.co"
    echo "SUPABASE_ANON_KEY=your-anon-key-here"
    echo "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here"
    echo "DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres"
    echo "JWT_SECRET=your-jwt-secret-here"
    echo ""
    echo "See supabase_config_example.txt for details"
    exit 1
fi

echo "✅ .env file found"

# Check if Supabase credentials are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ Supabase credentials not set in .env"
    echo "Please add your Supabase project credentials to .env"
    exit 1
fi

echo "✅ Supabase credentials configured"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install supabase

echo "✅ Dependencies installed"

# Test Supabase connection
echo "🔌 Testing Supabase connection..."
python -c "
from services.supabase_service import SupabaseService
try:
    service = SupabaseService()
    if service.test_connection():
        print('✅ Supabase connection successful')
    else:
        print('❌ Supabase connection failed')
        exit(1)
except Exception as e:
    print(f'❌ Supabase connection error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Supabase connection test failed"
    echo "Please check your credentials and try again"
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Go to your Supabase project dashboard"
echo "2. Run the SQL schema from supabase_schema.sql"
echo "3. Start the multi-tenant backend:"
echo "   python backend_multi_tenant.py"
echo ""
echo "Your multi-tenant AI SDR platform is ready! 🚀"


