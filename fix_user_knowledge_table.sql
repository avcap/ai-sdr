-- Fix the user_knowledge table to match backend expectations
-- Run this in Supabase SQL Editor

-- Drop the existing user_knowledge table if it exists
DROP TABLE IF EXISTS user_knowledge CASCADE;

-- Create user_knowledge table with the correct columns that the backend expects
CREATE TABLE user_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_info JSONB,
    sales_approach TEXT,
    products JSONB,
    key_messages JSONB,
    value_propositions TEXT,
    target_audience JSONB,
    competitive_advantages TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_knowledge ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for tenant isolation
CREATE POLICY "Users can only see their tenant's knowledge" ON user_knowledge
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_knowledge_tenant_id ON user_knowledge(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_user_id ON user_knowledge(user_id);

