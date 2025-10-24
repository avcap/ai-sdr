-- Multi-Tenant AI SDR Platform Database Schema
-- This schema provides complete tenant isolation and security

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security
ALTER DATABASE postgres SET row_security = on;

-- ==============================================
-- TENANT MANAGEMENT
-- ==============================================

-- Tenants table - Root level organization
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL, -- URL-friendly identifier
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- USER MANAGEMENT
-- ==============================================

-- Users table - Multi-tenant users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user', 'viewer')),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- ==============================================
-- KNOWLEDGE MANAGEMENT
-- ==============================================

-- User Knowledge table - Extracted from documents
CREATE TABLE user_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_info JSONB,
    sales_approach TEXT,
    products JSONB,
    key_messages JSONB,
    value_propositions TEXT,
    target_audience JSONB,
    competitive_advantages TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training Documents table - Uploaded files
CREATE TABLE training_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    status TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'processed', 'failed')),
    extracted_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- CAMPAIGN MANAGEMENT
-- ==============================================

-- Campaigns table - Multi-tenant campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),
    settings JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leads table - Campaign leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    name TEXT,
    email TEXT,
    company TEXT,
    title TEXT,
    linkedin_url TEXT,
    phone TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'responded', 'qualified', 'unqualified')),
    score INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- AGENT RESULTS
-- ==============================================

-- Agent Results table - AI agent outputs
CREATE TABLE agent_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL, -- 'prospector', 'enrichment', 'copywriter', etc.
    input_data JSONB,
    output_data JSONB,
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- AUDIT LOGGING
-- ==============================================

-- Audit Log table - Track all actions
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- 'create', 'update', 'delete', 'login', etc.
    resource_type TEXT NOT NULL, -- 'campaign', 'lead', 'user', etc.
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Tenant-based indexes
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_user_knowledge_tenant_id ON user_knowledge(tenant_id);
CREATE INDEX idx_training_documents_tenant_id ON training_documents(tenant_id);
CREATE INDEX idx_campaigns_tenant_id ON campaigns(tenant_id);
CREATE INDEX idx_leads_tenant_id ON leads(tenant_id);
CREATE INDEX idx_agent_results_tenant_id ON agent_results(tenant_id);
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);

-- User-based indexes
CREATE INDEX idx_user_knowledge_user_id ON user_knowledge(user_id);
CREATE INDEX idx_training_documents_user_id ON training_documents(user_id);
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_agent_results_user_id ON agent_results(user_id);

-- Campaign-based indexes
CREATE INDEX idx_leads_campaign_id ON leads(campaign_id);
CREATE INDEX idx_agent_results_campaign_id ON agent_results(campaign_id);

-- Status indexes
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_agent_results_status ON agent_results(status);

-- ==============================================
-- ROW LEVEL SECURITY (RLS)
-- ==============================================

-- Enable RLS on all tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ==============================================
-- RLS POLICIES
-- ==============================================

-- Function to get current tenant ID from JWT
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'tenant_id',
        current_setting('app.current_tenant_id', true)
    )::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user ID from JWT
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'user_id',
        current_setting('app.current_user_id', true)
    )::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Tenants policies
CREATE POLICY "Users can view their tenant" ON tenants
    FOR SELECT USING (id = get_current_tenant_id());

CREATE POLICY "Users can update their tenant" ON tenants
    FOR UPDATE USING (id = get_current_tenant_id());

-- Users policies
CREATE POLICY "Users can view tenant users" ON users
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (id = get_current_user_id() AND tenant_id = get_current_tenant_id());

-- User Knowledge policies
CREATE POLICY "Users can manage their knowledge" ON user_knowledge
    FOR ALL USING (tenant_id = get_current_tenant_id() AND user_id = get_current_user_id());

-- Training Documents policies
CREATE POLICY "Users can manage their documents" ON training_documents
    FOR ALL USING (tenant_id = get_current_tenant_id() AND user_id = get_current_user_id());

-- Campaigns policies
CREATE POLICY "Users can manage tenant campaigns" ON campaigns
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Leads policies
CREATE POLICY "Users can manage tenant leads" ON leads
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Agent Results policies
CREATE POLICY "Users can view tenant agent results" ON agent_results
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can create agent results" ON agent_results
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id() AND user_id = get_current_user_id());

-- Audit Logs policies
CREATE POLICY "Users can view tenant audit logs" ON audit_logs
    FOR SELECT USING (tenant_id = get_current_tenant_id());

-- ==============================================
-- TRIGGERS FOR UPDATED_AT
-- ==============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_knowledge_updated_at BEFORE UPDATE ON user_knowledge
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- SAMPLE DATA FOR TESTING
-- ==============================================

-- Insert sample tenant
INSERT INTO tenants (id, name, slug, plan) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'Demo Company', 'demo-company', 'free');

-- Insert sample user
INSERT INTO users (id, tenant_id, email, name, role) VALUES 
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', 'demo@demo.com', 'Demo User', 'admin');

-- ==============================================
-- VIEWS FOR COMMON QUERIES
-- ==============================================

-- View for tenant dashboard stats
CREATE VIEW tenant_dashboard_stats AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(DISTINCT c.id) as campaign_count,
    COUNT(DISTINCT l.id) as lead_count,
    COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_campaigns
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id
LEFT JOIN campaigns c ON t.id = c.tenant_id
LEFT JOIN leads l ON t.id = l.tenant_id
GROUP BY t.id, t.name;

-- View for user activity
CREATE VIEW user_activity AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email,
    t.name as tenant_name,
    COUNT(DISTINCT c.id) as campaigns_created,
    COUNT(DISTINCT l.id) as leads_managed,
    MAX(al.created_at) as last_activity
FROM users u
JOIN tenants t ON u.tenant_id = t.id
LEFT JOIN campaigns c ON u.id = c.user_id
LEFT JOIN leads l ON u.id = l.tenant_id
LEFT JOIN audit_logs al ON u.id = al.user_id
GROUP BY u.id, u.name, u.email, t.name;


