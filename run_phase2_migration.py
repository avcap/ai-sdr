"""
Phase 2 Analytics Schema Migration
Runs the analytics database schema creation in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import sys

load_dotenv()

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

print('🚀 Phase 2: Analytics & Performance Tracking Migration')
print('=' * 60)
print()

# Read SQL file
with open('phase2_analytics_schema.sql', 'r') as f:
    sql_content = f.read()

print('📝 SQL file loaded successfully')
print(f'📊 Size: {len(sql_content)} characters')
print()

# Note: Supabase Python client doesn't support direct SQL execution
# We need to use the SQL Editor in Supabase Dashboard or psycopg2

print('⚠️  MIGRATION INSTRUCTIONS:')
print()
print('The SQL migration needs to be run directly in Supabase.')
print('Please follow these steps:')
print()
print('1. Go to your Supabase Dashboard: https://app.supabase.com')
print('2. Select your project')
print('3. Click on "SQL Editor" in the left sidebar')
print('4. Click "New Query"')
print('5. Copy the contents of: phase2_analytics_schema.sql')
print('6. Paste into the SQL Editor')
print('7. Click "Run" to execute')
print()
print('=' * 60)
print()
print('✅ Once complete, the following tables will be created:')
print('   - campaign_analytics (time-series performance data)')
print('   - lead_engagement (individual interaction tracking)')
print('   - campaign_activity (comprehensive activity log)')
print('   - email_tracking (detailed email performance)')
print('   - campaign_comparison (A/B test results)')
print()
print('   Plus indexes, RLS policies, and helper functions!')
print()
print('File ready for migration: phase2_analytics_schema.sql')

