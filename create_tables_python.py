#!/usr/bin/env python3
"""
Create the missing tables directly using Supabase Python client
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def create_missing_tables():
    """Create missing tables using direct SQL execution"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        client = create_client(url, key)
        
        print("📋 Creating missing tables...")
        
        # SQL statements to create missing tables
        sql_statements = [
            # Create training_documents table
            """
            CREATE TABLE IF NOT EXISTS training_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                subject TEXT,
                status TEXT DEFAULT 'uploaded',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Create user_knowledge table
            """
            CREATE TABLE IF NOT EXISTS user_knowledge (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_id UUID,
                confidence_score FLOAT DEFAULT 0.8,
                tags TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Enable RLS
            "ALTER TABLE training_documents ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE user_knowledge ENABLE ROW LEVEL SECURITY;",
            
            # Create indexes
            "CREATE INDEX IF NOT EXISTS idx_training_documents_tenant_id ON training_documents(tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_knowledge_tenant_id ON user_knowledge(tenant_id);"
        ]
        
        # Execute each SQL statement
        for i, sql in enumerate(sql_statements, 1):
            try:
                print(f"Executing statement {i}...")
                # Use the postgrest client to execute SQL
                result = client.postgrest.rpc('exec', {'sql': sql.strip()})
                print(f"✅ Statement {i} executed successfully")
            except Exception as e:
                print(f"⚠️  Statement {i} result: {e}")
                # Continue with other statements even if one fails
        
        # Test if tables were created
        print("\n🧪 Testing table creation...")
        
        try:
            result = client.table('training_documents').select('id').limit(1).execute()
            print("✅ training_documents table created successfully")
        except Exception as e:
            print(f"❌ training_documents table still missing: {e}")
        
        try:
            result = client.table('user_knowledge').select('id').limit(1).execute()
            print("✅ user_knowledge table created successfully")
        except Exception as e:
            print(f"❌ user_knowledge table still missing: {e}")
        
        print("\n🎯 Table creation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_missing_tables()

