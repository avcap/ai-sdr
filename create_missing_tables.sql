-- Create only the missing tables for Train Your Team feature
-- Run this in Supabase SQL Editor

-- Create training_documents table (if it doesn't exist)
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

-- Create user_knowledge table (if it doesn't exist)
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

-- Create campaigns table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create leads table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    email TEXT,
    name TEXT,
    company TEXT,
    title TEXT,
    phone TEXT,
    linkedin_url TEXT,
    status TEXT DEFAULT 'new',
    score INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create agent_results table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS agent_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status TEXT DEFAULT 'completed',
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit_logs table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security on all tables
ALTER TABLE training_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tenant isolation
CREATE POLICY "Users can only see their tenant's training documents" ON training_documents
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can only see their tenant's knowledge" ON user_knowledge
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can only see their tenant's campaigns" ON campaigns
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can only see their tenant's leads" ON leads
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can only see their tenant's agent results" ON agent_results
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can only see their tenant's audit logs" ON audit_logs
    FOR ALL USING (tenant_id IN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    ));

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_training_documents_tenant_id ON training_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_training_documents_user_id ON training_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_tenant_id ON user_knowledge(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_user_id ON user_knowledge(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_tenant_id ON campaigns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_tenant_id ON leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_campaign_id ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_agent_results_tenant_id ON agent_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);

