#!/bin/bash

echo "🔧 Fixing Google Button Environment Variables..."

# Create frontend .env.local file
cat > frontend/.env.local << 'EOF'
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_key_here

# Google OAuth (if using NextAuth with Google provider)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
EOF

echo "✅ Created frontend/.env.local with correct environment variables"
echo ""
echo "📝 Next steps:"
echo "1. Update frontend/.env.local with your actual values:"
echo "   - NEXTAUTH_SECRET: Generate a random secret key"
echo "   - GOOGLE_CLIENT_ID: Your Google OAuth client ID"
echo "   - GOOGLE_CLIENT_SECRET: Your Google OAuth client secret"
echo ""
echo "2. Restart the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. The Google button should now work!"
echo ""
echo "🔗 To generate NEXTAUTH_SECRET, run:"
echo "openssl rand -base64 32"


