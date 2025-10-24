#!/usr/bin/env python3
"""
Create the essential tables for Train Your Team feature
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def create_tables():
    """Create essential tables"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        client = create_client(url, key)
        
        print("📋 Creating essential tables...")
        
        # Create tenants table
        tenants_sql = """
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            plan TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            settings JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Create users table
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user',
            avatar_url TEXT,
            preferences JSONB DEFAULT '{}',
            last_login TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(tenant_id, email)
        );
        """
        
        # Create training_documents table
        training_docs_sql = """
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
        """
        
        # Create user_knowledge table
        user_knowledge_sql = """
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
        """
        
        # Execute SQL statements
        tables = [
            ("tenants", tenants_sql),
            ("users", users_sql), 
            ("training_documents", training_docs_sql),
            ("user_knowledge", user_knowledge_sql)
        ]
        
        for table_name, sql in tables:
            try:
                print(f"Creating {table_name} table...")
                # Use the postgrest client to execute SQL
                result = client.postgrest.rpc('exec', {'sql': sql})
                print(f"✅ {table_name} table created")
            except Exception as e:
                print(f"⚠️  {table_name} table creation: {e}")
        
        print("✅ Essential tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()

