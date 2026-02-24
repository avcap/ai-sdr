#!/bin/bash
# Start the multi-tenant backend with proper environment variables

cd /Users/zoecapital/ai-sdr
source venv/bin/activate

# Set environment variables (use .env or export real values locally - never commit secrets)
export SUPABASE_URL="${SUPABASE_URL:-https://your-project.supabase.co}"
export SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-your-service-role-key}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-your-anthropic-api-key}"

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the backend
echo "🚀 Starting multi-tenant backend..."
python backend_multi_tenant.py



