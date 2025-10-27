-- Google OAuth tokens table for multi-tenant AI SDR
-- Stores user's Google OAuth credentials for Gmail/Sheets integration

CREATE TABLE IF NOT EXISTS public.google_auth (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    scopes TEXT[],
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_google_auth_tenant_user ON google_auth(tenant_id, user_id);

-- Enable RLS
ALTER TABLE google_auth ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage their own Google auth" ON google_auth
    FOR ALL USING (
        tenant_id::text = auth.jwt() ->> 'tenant_id' AND 
        user_id::text = auth.jwt() ->> 'user_id'
    );

-- Trigger for updated_at
CREATE TRIGGER update_google_auth_updated_at 
    BEFORE UPDATE ON google_auth
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

