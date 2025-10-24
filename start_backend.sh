#!/bin/bash
# Start the multi-tenant backend with proper environment variables

cd /Users/zoecapital/ai-sdr
source venv/bin/activate

# Set environment variables
export SUPABASE_URL="https://nxzxdllhjdazcfjvlkyy.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im54enhkbGxoamRhemNmanZsa3l5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI1MjI1MSwiZXhwIjoyMDc2ODI4MjUxfQ.sYKbZK1JtFgoIpm1QbWF1XmVxpndmycJsvzh6ufugmw"
export ANTHROPIC_API_KEY="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"

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the backend
echo "🚀 Starting multi-tenant backend..."
python backend_multi_tenant.py

