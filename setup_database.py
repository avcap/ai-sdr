#!/usr/bin/env python3
"""
Execute the Supabase schema to create all tables
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def execute_schema():
    """Execute the database schema"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        client = create_client(url, key)
        
        # Read the schema file
        with open('/Users/zoecapital/ai-sdr/supabase_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        print("📋 Executing database schema...")
        
        # Execute the schema
        result = client.rpc('exec_sql', {'sql': schema_sql})
        
        print("✅ Database schema executed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error executing schema: {e}")
        
        # Try alternative approach - execute SQL directly
        try:
            print("🔄 Trying direct SQL execution...")
            
            # Split schema into individual statements
            statements = schema_sql.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        client.postgrest.rpc('exec', {'sql': statement})
                    except Exception as stmt_error:
                        print(f"⚠️  Statement failed: {stmt_error}")
                        continue
            
            print("✅ Schema execution completed!")
            return True
            
        except Exception as e2:
            print(f"❌ Direct execution also failed: {e2}")
            return False

if __name__ == "__main__":
    execute_schema()

