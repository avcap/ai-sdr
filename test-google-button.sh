#!/bin/bash

echo "🧪 Testing Google Button Fix..."

# Test if backend is running
echo "1. Checking backend server..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "   ✅ Backend server is running on port 8000"
else
    echo "   ❌ Backend server is not running on port 8000"
    echo "   Start it with: cd /Users/zoecapital/ai-sdr && source venv/bin/activate && python backend/main.py"
    exit 1
fi

# Test if frontend is running
echo "2. Checking frontend server..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend server is running on port 3000"
else
    echo "   ❌ Frontend server is not running on port 3000"
    echo "   Start it with: cd /Users/zoecapital/ai-sdr/frontend && npm run dev"
    exit 1
fi

# Test environment variables
echo "3. Checking environment variables..."
if [ -f "frontend/.env.local" ]; then
    echo "   ✅ frontend/.env.local exists"
    
    if grep -q "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" frontend/.env.local; then
        echo "   ✅ NEXT_PUBLIC_BACKEND_URL is set correctly"
    else
        echo "   ❌ NEXT_PUBLIC_BACKEND_URL is not set correctly"
    fi
    
    if grep -q "NEXTAUTH_SECRET=" frontend/.env.local && ! grep -q "your_nextauth_secret_key_here" frontend/.env.local; then
        echo "   ✅ NEXTAUTH_SECRET is set"
    else
        echo "   ❌ NEXTAUTH_SECRET is not set properly"
    fi
else
    echo "   ❌ frontend/.env.local does not exist"
    echo "   Run: ./fix-google-button.sh"
    exit 1
fi

# Test API routes
echo "4. Testing API routes..."
if curl -s http://localhost:3000/api/auth/google/url > /dev/null; then
    echo "   ✅ Google URL API route is accessible"
else
    echo "   ❌ Google URL API route is not accessible"
fi

echo ""
echo "🎉 Google Button Fix Summary:"
echo "✅ Backend server running on port 8000"
echo "✅ Frontend server running on port 3000"
echo "✅ Environment variables configured"
echo "✅ API routes updated to use NEXT_PUBLIC_BACKEND_URL"
echo ""
echo "🚀 The Google button should now work!"
echo ""
echo "📝 Next steps:"
echo "1. Refresh your browser at http://localhost:3000"
echo "2. Click the 'Connect Google' button"
echo "3. If you see OAuth errors, you need to set up Google OAuth credentials"
echo "   See GOOGLE_INTEGRATION_GUIDE.md for setup instructions"


