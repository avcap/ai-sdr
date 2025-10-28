-- Create sequence_enrollments table
-- This replaces/supplements lead_sequence_state for the execution engine

CREATE TABLE IF NOT EXISTS sequence_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    sequence_id UUID NOT NULL REFERENCES sequences(id) ON DELETE CASCADE,
    
    -- Current state
    current_step INTEGER DEFAULT 1,
    next_action_at TIMESTAMPTZ,
    
    -- Status tracking
    status TEXT DEFAULT 'active' CHECK (status IN ('scheduled', 'active', 'paused', 'completed', 'failed')),
    scheduled_start_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    exit_reason TEXT, -- 'replied', 'unsubscribed', 'bounced', 'completed', etc.
    
    -- Timestamps
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure a lead can only be enrolled once per sequence
    UNIQUE(lead_id, sequence_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_enrollments_sequence ON sequence_enrollments(sequence_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_lead ON sequence_enrollments(lead_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON sequence_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_next_action ON sequence_enrollments(next_action_at);
CREATE INDEX IF NOT EXISTS idx_enrollments_status_next_action ON sequence_enrollments(status, next_action_at);
CREATE INDEX IF NOT EXISTS idx_enrollments_tenant ON sequence_enrollments(tenant_id);

-- Enable RLS
ALTER TABLE sequence_enrollments ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own enrollments"
    ON sequence_enrollments
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Users can insert own enrollments"
    ON sequence_enrollments
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Users can update own enrollments"
    ON sequence_enrollments
    FOR UPDATE
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Users can delete own enrollments"
    ON sequence_enrollments
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Create function to enroll lead in sequence (used by backend)
CREATE OR REPLACE FUNCTION enroll_lead_in_sequence(
    p_tenant_id UUID,
    p_lead_id UUID,
    p_campaign_id UUID,
    p_sequence_id UUID
) RETURNS UUID AS $$
DECLARE
    v_enrollment_id UUID;
BEGIN
    -- Insert or get existing enrollment
    INSERT INTO sequence_enrollments (
        tenant_id,
        lead_id,
        campaign_id,
        sequence_id,
        current_step,
        status,
        enrolled_at
    ) VALUES (
        p_tenant_id,
        p_lead_id,
        p_campaign_id,
        p_sequence_id,
        1,
        'active',
        NOW()
    )
    ON CONFLICT (lead_id, sequence_id) 
    DO UPDATE SET
        updated_at = NOW()
    RETURNING id INTO v_enrollment_id;
    
    RETURN v_enrollment_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment
COMMENT ON TABLE sequence_enrollments IS 'Tracks lead enrollment and progression through sequences';

