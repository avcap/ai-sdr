-- Smart Campaign Suggestions Database Schema
-- Migration: create_smart_campaign_tables.sql

-- Table: campaign_suggestions
-- Stores generated suggestions for quick retrieval
CREATE TABLE IF NOT EXISTS campaign_suggestions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    prompt_text TEXT NOT NULL,
    reasoning TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    category VARCHAR(100),
    source_documents JSONB DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT 0.0 CHECK (success_rate >= 0 AND success_rate <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: campaign_executions
-- Tracks campaign execution history for learning
CREATE TABLE IF NOT EXISTS campaign_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    original_prompt TEXT NOT NULL,
    suggested_prompt_id UUID REFERENCES campaign_suggestions(id) ON DELETE SET NULL,
    execution_results JSONB DEFAULT '{}',
    lead_count INTEGER DEFAULT 0,
    quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    user_feedback JSONB DEFAULT '{}',
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: prompt_patterns
-- Stores successful prompt patterns learned over time
CREATE TABLE IF NOT EXISTS prompt_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_template TEXT NOT NULL,
    success_count INTEGER DEFAULT 0,
    avg_quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    industry VARCHAR(100),
    target_role VARCHAR(100),
    company_size VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaign_suggestions_tenant_user ON campaign_suggestions(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_campaign_suggestions_category ON campaign_suggestions(category);
CREATE INDEX IF NOT EXISTS idx_campaign_suggestions_confidence ON campaign_suggestions(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_campaign_executions_tenant_user ON campaign_executions(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_campaign_executions_executed_at ON campaign_executions(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaign_executions_suggested_prompt ON campaign_executions(suggested_prompt_id);

CREATE INDEX IF NOT EXISTS idx_prompt_patterns_tenant ON prompt_patterns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_prompt_patterns_type ON prompt_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_prompt_patterns_industry ON prompt_patterns(industry);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_campaign_suggestions_updated_at 
    BEFORE UPDATE ON campaign_suggestions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_patterns_updated_at 
    BEFORE UPDATE ON prompt_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE campaign_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_patterns ENABLE ROW LEVEL SECURITY;

-- Policies for campaign_suggestions
CREATE POLICY "Users can view their own campaign suggestions" ON campaign_suggestions
    FOR SELECT USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can insert their own campaign suggestions" ON campaign_suggestions
    FOR INSERT WITH CHECK (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can update their own campaign suggestions" ON campaign_suggestions
    FOR UPDATE USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can delete their own campaign suggestions" ON campaign_suggestions
    FOR DELETE USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

-- Policies for campaign_executions
CREATE POLICY "Users can view their own campaign executions" ON campaign_executions
    FOR SELECT USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can insert their own campaign executions" ON campaign_executions
    FOR INSERT WITH CHECK (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can update their own campaign executions" ON campaign_executions
    FOR UPDATE USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

-- Policies for prompt_patterns
CREATE POLICY "Users can view their own prompt patterns" ON prompt_patterns
    FOR SELECT USING (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can insert their own prompt patterns" ON prompt_patterns
    FOR INSERT WITH CHECK (tenant_id::text = auth.jwt() ->> 'tenant_id');

CREATE POLICY "Users can update their own prompt patterns" ON prompt_patterns
    FOR UPDATE USING (tenant_id::text = auth.jwt() ->> 'tenant_id');
