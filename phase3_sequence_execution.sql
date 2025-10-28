-- Phase 3.5: Sequence Execution Engine + Scheduling
-- Run this in Supabase SQL Editor

-- 1. Add scheduling column to sequences table
ALTER TABLE sequences 
ADD COLUMN IF NOT EXISTS scheduled_start_at TIMESTAMPTZ NULL;

-- 2. Add status tracking to sequence_enrollments
ALTER TABLE sequence_enrollments
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

ALTER TABLE sequence_enrollments
ADD COLUMN IF NOT EXISTS scheduled_start_at TIMESTAMPTZ NULL;

ALTER TABLE sequence_enrollments
ADD COLUMN IF NOT EXISTS exit_reason TEXT NULL;

-- Add comments
COMMENT ON COLUMN sequence_enrollments.status IS 'scheduled, active, paused, completed';
COMMENT ON COLUMN sequence_enrollments.exit_reason IS 'replied, unsubscribed, bounced, completed';

-- 3. Create sequence_step_executions table for tracking
CREATE TABLE IF NOT EXISTS sequence_step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES sequence_enrollments(id) ON DELETE CASCADE,
    step_id UUID NOT NULL REFERENCES sequence_steps(id) ON DELETE CASCADE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'sent',
    error_message TEXT,
    email_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_step_executions_enrollment ON sequence_step_executions(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_step_executions_tenant ON sequence_step_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status_next_action ON sequence_enrollments(status, next_action_at);
CREATE INDEX IF NOT EXISTS idx_sequences_scheduled_start ON sequences(scheduled_start_at);

-- Add RLS policies for sequence_step_executions
ALTER TABLE sequence_step_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own step executions"
    ON sequence_step_executions
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "Users can insert own step executions"
    ON sequence_step_executions
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Add comment
COMMENT ON TABLE sequence_step_executions IS 'Tracks each step execution in a sequence for auditing and analytics';

