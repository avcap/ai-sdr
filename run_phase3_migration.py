"""
Phase 3 Sequences Schema Migration
Runs the sequences database schema creation in Supabase
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

print('🚀 Phase 3: Multi-Touch Sequences Migration')
print('=' * 60)
print()

# Read SQL file
with open('phase3_sequences_schema.sql', 'r') as f:
    sql_content = f.read()

print('📝 SQL file loaded successfully')
print(f'📊 Size: {len(sql_content)} characters')
print()

print('⚠️  MIGRATION INSTRUCTIONS:')
print()
print('The SQL migration needs to be run directly in Supabase.')
print('Please follow these steps:')
print()
print('1. Go to your Supabase Dashboard: https://app.supabase.com')
print('2. Select your project')
print('3. Click on "SQL Editor" in the left sidebar')
print('4. Click "New Query"')
print('5. Copy the contents of: phase3_sequences_schema.sql')
print('6. Paste into the SQL Editor')
print('7. Click "Run" to execute')
print()
print('=' * 60)
print()
print('✅ Once complete, the following will be created:')
print()
print('📁 TABLES (4):')
print('   - sequences - Email sequence definitions')
print('   - sequence_steps - Individual steps (email, delay, condition, action)')
print('   - lead_sequence_state - Track each lead\'s progress')
print('   - sequence_execution_log - Audit trail of all actions')
print()
print('🔧 FEATURES:')
print('   - Multi-step email sequences with delays')
print('   - Conditional branching (if replied, if opened, etc.)')
print('   - A/B testing support')
print('   - Timezone-aware scheduling')
print('   - Lead-level progress tracking')
print('   - Performance analytics')
print()
print('⚡ PERFORMANCE:')
print('   - 15+ optimized indexes')
print('   - Partial indexes for scheduler queries')
print('   - Materialized view for performance summary')
print()
print('🔒 SECURITY:')
print('   - Row Level Security (RLS) policies')
print('   - Tenant isolation')
print('   - Automatic triggers for data integrity')
print()
print('🛠️  HELPER FUNCTIONS:')
print('   - enroll_lead_in_sequence() - Add lead to sequence')
print('   - advance_to_next_step() - Move to next step')
print('   - stop_lead_sequence() - Stop sequence with reason')
print()
print('File ready for migration: phase3_sequences_schema.sql')
print()
print('=' * 60)

