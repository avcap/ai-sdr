-- ============================================================
-- COMPLETE SEQUENCE EXECUTION ENGINE MIGRATION
-- Run this entire file in Supabase SQL Editor
-- ============================================================

-- 1. Add scheduling column to sequences table
ALTER TABLE sequences 
ADD COLUMN IF NOT EXISTS scheduled_start_at TIMESTAMPTZ NULL;

-- 2. Create sequence_enrollments table
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

-- 3. Create indexes for sequence_enrollments
CREATE INDEX IF NOT EXISTS idx_enrollments_sequence ON sequence_enrollments(sequence_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_lead ON sequence_enrollments(lead_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON sequence_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_next_action ON sequence_enrollments(next_action_at);
CREATE INDEX IF NOT EXISTS idx_enrollments_status_next_action ON sequence_enrollments(status, next_action_at);
CREATE INDEX IF NOT EXISTS idx_enrollments_tenant ON sequence_enrollments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sequences_scheduled_start ON sequences(scheduled_start_at);

-- 4. Enable RLS for sequence_enrollments
ALTER TABLE sequence_enrollments ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies for sequence_enrollments
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

-- 6. Create sequence_step_executions table for tracking
CREATE TABLE IF NOT EXISTS sequence_step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES sequence_enrollments(id) ON DELETE CASCADE,
    step_id UUID NOT NULL REFERENCES sequence_steps(id) ON DELETE CASCADE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'skipped', 'pending')),
    error_message TEXT,
    email_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Create indexes for sequence_step_executions
CREATE INDEX IF NOT EXISTS idx_step_executions_enrollment ON sequence_step_executions(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_step_executions_tenant ON sequence_step_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_step_executions_step ON sequence_step_executions(step_id);
CREATE INDEX IF NOT EXISTS idx_step_executions_executed_at ON sequence_step_executions(executed_at);

-- 8. Enable RLS for sequence_step_executions
ALTER TABLE sequence_step_executions ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS policies for sequence_step_executions
CREATE POLICY "Users can view own step executions"
    ON sequence_step_executions
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Users can insert own step executions"
    ON sequence_step_executions
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 10. Create helper function to enroll lead in sequence
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

-- 11. Add comments
COMMENT ON TABLE sequence_enrollments IS 'Tracks lead enrollment and progression through sequences';
COMMENT ON TABLE sequence_step_executions IS 'Tracks each step execution in a sequence for auditing and analytics';
COMMENT ON COLUMN sequence_enrollments.status IS 'scheduled, active, paused, completed, failed';
COMMENT ON COLUMN sequence_enrollments.exit_reason IS 'replied, unsubscribed, bounced, completed';
COMMENT ON FUNCTION enroll_lead_in_sequence IS 'Helper function to enroll a lead in a sequence, used by backend';

-- ============================================================
-- MIGRATION COMPLETE!
-- ============================================================
-- Next: Activate a sequence in the frontend to test

