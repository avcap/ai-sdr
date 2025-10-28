-- ==============================================
-- PHASE 3: MULTI-TOUCH SEQUENCES
-- Database Schema for Automated Email Sequences
-- ==============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- SEQUENCES TABLES
-- ==============================================

-- Sequences: Define email sequences/drip campaigns
CREATE TABLE IF NOT EXISTS sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Sequence details
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'archived')),
    
    -- Configuration
    steps_count INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}', -- timezone, default_send_time, business_hours_only, etc.
    
    -- Performance tracking
    total_enrolled INTEGER DEFAULT 0,
    total_completed INTEGER DEFAULT 0,
    total_stopped INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sequence Steps: Individual steps in a sequence
CREATE TABLE IF NOT EXISTS sequence_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    sequence_id UUID NOT NULL REFERENCES sequences(id) ON DELETE CASCADE,
    
    -- Step ordering
    step_order INTEGER NOT NULL,
    name TEXT NOT NULL,
    step_type TEXT NOT NULL CHECK (step_type IN ('email', 'delay', 'condition', 'action')),
    
    -- Email content (for step_type = 'email')
    email_template_id UUID, -- Optional: link to template library
    subject_line TEXT,
    body_text TEXT,
    body_html TEXT,
    
    -- Timing (for step_type = 'delay' or email steps)
    delay_days INTEGER DEFAULT 0,
    delay_hours INTEGER DEFAULT 0,
    send_time TEXT, -- "09:00" (optional specific time HH:MM)
    business_hours_only BOOLEAN DEFAULT true,
    
    -- Conditional logic (for step_type = 'condition')
    condition_type TEXT CHECK (condition_type IN (
        'if_replied', 'if_opened', 'if_clicked', 'if_not_replied', 
        'if_not_opened', 'if_bounced', 'if_unsubscribed', 'always'
    )),
    condition_config JSONB DEFAULT '{}', -- days_to_check, link_url, etc.
    
    -- Branching (for conditions)
    next_step_if_true UUID, -- Step to go to if condition is true
    next_step_if_false UUID, -- Step to go to if condition is false
    
    -- Actions (for step_type = 'action')
    action_type TEXT CHECK (action_type IN (
        'update_status', 'tag_lead', 'notify_user', 'assign_to_user', 
        'add_to_campaign', 'remove_from_sequence', 'mark_qualified'
    )),
    action_config JSONB DEFAULT '{}',
    
    -- A/B Testing
    variant TEXT, -- 'A', 'B', 'C' for split testing
    variant_percentage INTEGER, -- What % of leads get this variant
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(sequence_id, step_order)
);

-- Lead Sequence State: Track where each lead is in each sequence
CREATE TABLE IF NOT EXISTS lead_sequence_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    sequence_id UUID NOT NULL REFERENCES sequences(id) ON DELETE CASCADE,
    
    -- Current state
    current_step_id UUID REFERENCES sequence_steps(id) ON DELETE SET NULL,
    current_step_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN (
        'pending', 'active', 'paused', 'completed', 'stopped', 'failed'
    )),
    
    -- Progress tracking
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_action_at TIMESTAMP WITH TIME ZONE, -- When to execute next step
    completed_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    stopped_reason TEXT,
    
    -- Engagement metrics
    steps_completed INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    
    -- Lead response tracking
    replied_at TIMESTAMP WITH TIME ZONE,
    reply_step_id UUID, -- Which step did they reply to
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    
    -- Variant tracking (for A/B tests)
    assigned_variant TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}', -- Custom data, tags, pause reasons, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(lead_id, sequence_id)
);

-- Sequence Execution Log: Audit trail of all sequence actions
CREATE TABLE IF NOT EXISTS sequence_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    sequence_id UUID NOT NULL REFERENCES sequences(id) ON DELETE CASCADE,
    step_id UUID REFERENCES sequence_steps(id) ON DELETE SET NULL,
    
    -- Action details
    action_type TEXT NOT NULL CHECK (action_type IN (
        'sequence_started', 'email_sent', 'email_delivered', 'email_failed',
        'delay_started', 'condition_evaluated', 'step_completed', 'step_skipped',
        'sequence_paused', 'sequence_resumed', 'sequence_completed', 'sequence_stopped',
        'action_executed', 'variant_assigned', 'error_occurred'
    )),
    action_result TEXT CHECK (action_result IN ('success', 'failed', 'skipped', 'pending')),
    
    -- Context
    step_order INTEGER,
    step_name TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}', -- Email ID, condition result, action data, etc.
    
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Sequences indexes
CREATE INDEX IF NOT EXISTS idx_sequences_tenant_id ON sequences(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sequences_user_id ON sequences(user_id);
CREATE INDEX IF NOT EXISTS idx_sequences_status ON sequences(status);

-- Sequence Steps indexes
CREATE INDEX IF NOT EXISTS idx_sequence_steps_tenant_id ON sequence_steps(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sequence_steps_sequence_id ON sequence_steps(sequence_id);
CREATE INDEX IF NOT EXISTS idx_sequence_steps_order ON sequence_steps(sequence_id, step_order);
CREATE INDEX IF NOT EXISTS idx_sequence_steps_type ON sequence_steps(step_type);

-- Lead Sequence State indexes (critical for performance)
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_tenant_id ON lead_sequence_state(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_lead_id ON lead_sequence_state(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_sequence_id ON lead_sequence_state(sequence_id);
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_campaign_id ON lead_sequence_state(campaign_id);
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_status ON lead_sequence_state(status);
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_next_action ON lead_sequence_state(next_action_at) 
    WHERE status = 'active' AND next_action_at IS NOT NULL; -- Partial index for scheduler
CREATE INDEX IF NOT EXISTS idx_lead_sequence_state_active ON lead_sequence_state(status, next_action_at)
    WHERE status = 'active'; -- Composite index for active sequences

-- Execution Log indexes
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_tenant_id ON sequence_execution_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_lead_id ON sequence_execution_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_sequence_id ON sequence_execution_log(sequence_id);
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_step_id ON sequence_execution_log(step_id);
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_executed_at ON sequence_execution_log(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_sequence_execution_log_action_type ON sequence_execution_log(action_type);

-- ==============================================
-- ROW LEVEL SECURITY
-- ==============================================

-- Enable RLS on all tables
ALTER TABLE sequences ENABLE ROW LEVEL SECURITY;
ALTER TABLE sequence_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_sequence_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE sequence_execution_log ENABLE ROW LEVEL SECURITY;

-- Sequences policies
CREATE POLICY "Users can manage tenant sequences" ON sequences
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Sequence Steps policies
CREATE POLICY "Users can manage tenant sequence steps" ON sequence_steps
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Lead Sequence State policies
CREATE POLICY "Users can view tenant lead states" ON lead_sequence_state
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can manage lead states" ON lead_sequence_state
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Execution Log policies
CREATE POLICY "Users can view tenant execution logs" ON sequence_execution_log
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can insert execution logs" ON sequence_execution_log
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

-- ==============================================
-- TRIGGERS
-- ==============================================

-- Update updated_at timestamp on change
CREATE TRIGGER update_sequences_updated_at BEFORE UPDATE ON sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sequence_steps_updated_at BEFORE UPDATE ON sequence_steps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lead_sequence_state_updated_at BEFORE UPDATE ON lead_sequence_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update sequence steps_count when steps are added/removed
CREATE OR REPLACE FUNCTION update_sequence_steps_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE sequences 
        SET steps_count = steps_count + 1,
            updated_at = NOW()
        WHERE id = NEW.sequence_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE sequences 
        SET steps_count = GREATEST(steps_count - 1, 0),
            updated_at = NOW()
        WHERE id = OLD.sequence_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sequence_steps_count_trigger
    AFTER INSERT OR DELETE ON sequence_steps
    FOR EACH ROW EXECUTE FUNCTION update_sequence_steps_count();

-- ==============================================
-- HELPER FUNCTIONS
-- ==============================================

-- Function to enroll a lead in a sequence
CREATE OR REPLACE FUNCTION enroll_lead_in_sequence(
    p_tenant_id UUID,
    p_lead_id UUID,
    p_campaign_id UUID,
    p_sequence_id UUID
)
RETURNS UUID AS $$
DECLARE
    state_id UUID;
    first_step_id UUID;
    first_step_order INTEGER;
    first_step_delay_days INTEGER;
    first_step_delay_hours INTEGER;
    next_action TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get first step of sequence
    SELECT id, step_order, delay_days, delay_hours
    INTO first_step_id, first_step_order, first_step_delay_days, first_step_delay_hours
    FROM sequence_steps
    WHERE sequence_id = p_sequence_id
      AND is_active = true
    ORDER BY step_order ASC
    LIMIT 1;
    
    -- Calculate next action time
    next_action := NOW() + 
        INTERVAL '1 day' * COALESCE(first_step_delay_days, 0) + 
        INTERVAL '1 hour' * COALESCE(first_step_delay_hours, 0);
    
    -- Create lead sequence state
    INSERT INTO lead_sequence_state (
        tenant_id, lead_id, campaign_id, sequence_id,
        current_step_id, current_step_order,
        status, next_action_at
    ) VALUES (
        p_tenant_id, p_lead_id, p_campaign_id, p_sequence_id,
        first_step_id, first_step_order,
        'active', next_action
    )
    RETURNING id INTO state_id;
    
    -- Log enrollment
    INSERT INTO sequence_execution_log (
        tenant_id, lead_id, sequence_id, step_id,
        action_type, action_result, step_order
    ) VALUES (
        p_tenant_id, p_lead_id, p_sequence_id, first_step_id,
        'sequence_started', 'success', first_step_order
    );
    
    -- Update sequence enrollment count
    UPDATE sequences
    SET total_enrolled = total_enrolled + 1,
        updated_at = NOW()
    WHERE id = p_sequence_id;
    
    RETURN state_id;
END;
$$ LANGUAGE plpgsql;

-- Function to advance lead to next step
CREATE OR REPLACE FUNCTION advance_to_next_step(
    p_state_id UUID,
    p_skip_current BOOLEAN DEFAULT false
)
RETURNS BOOLEAN AS $$
DECLARE
    state_record RECORD;
    next_step RECORD;
    next_action TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get current state
    SELECT * INTO state_record
    FROM lead_sequence_state
    WHERE id = p_state_id;
    
    -- Get next step
    SELECT * INTO next_step
    FROM sequence_steps
    WHERE sequence_id = state_record.sequence_id
      AND step_order > state_record.current_step_order
      AND is_active = true
    ORDER BY step_order ASC
    LIMIT 1;
    
    -- If no next step, complete sequence
    IF next_step.id IS NULL THEN
        UPDATE lead_sequence_state
        SET status = 'completed',
            completed_at = NOW(),
            updated_at = NOW()
        WHERE id = p_state_id;
        
        -- Update sequence completion count
        UPDATE sequences
        SET total_completed = total_completed + 1,
            updated_at = NOW()
        WHERE id = state_record.sequence_id;
        
        RETURN true;
    END IF;
    
    -- Calculate next action time
    next_action := NOW() + 
        INTERVAL '1 day' * COALESCE(next_step.delay_days, 0) + 
        INTERVAL '1 hour' * COALESCE(next_step.delay_hours, 0);
    
    -- Update state to next step
    UPDATE lead_sequence_state
    SET current_step_id = next_step.id,
        current_step_order = next_step.step_order,
        steps_completed = steps_completed + 1,
        next_action_at = next_action,
        updated_at = NOW()
    WHERE id = p_state_id;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Function to stop a lead's sequence
CREATE OR REPLACE FUNCTION stop_lead_sequence(
    p_state_id UUID,
    p_reason TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    sequence_id_var UUID;
BEGIN
    -- Get sequence_id before update
    SELECT sequence_id INTO sequence_id_var
    FROM lead_sequence_state
    WHERE id = p_state_id;
    
    -- Update state
    UPDATE lead_sequence_state
    SET status = 'stopped',
        stopped_at = NOW(),
        stopped_reason = p_reason,
        updated_at = NOW()
    WHERE id = p_state_id;
    
    -- Update sequence stopped count
    UPDATE sequences
    SET total_stopped = total_stopped + 1,
        updated_at = NOW()
    WHERE id = sequence_id_var;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- MATERIALIZED VIEWS
-- ==============================================

-- Sequence Performance Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS sequence_performance_summary AS
SELECT 
    s.id as sequence_id,
    s.tenant_id,
    s.name,
    s.status,
    s.steps_count,
    s.total_enrolled,
    s.total_completed,
    s.total_stopped,
    
    -- Lead states
    COUNT(DISTINCT lss.id) as current_leads,
    COUNT(DISTINCT CASE WHEN lss.status = 'active' THEN lss.id END) as active_leads,
    COUNT(DISTINCT CASE WHEN lss.status = 'completed' THEN lss.id END) as completed_leads,
    
    -- Email metrics
    COALESCE(SUM(lss.emails_sent), 0) as total_emails_sent,
    COALESCE(SUM(lss.emails_opened), 0) as total_emails_opened,
    COALESCE(SUM(lss.emails_clicked), 0) as total_emails_clicked,
    COALESCE(SUM(lss.emails_replied), 0) as total_emails_replied,
    
    -- Rates
    CASE 
        WHEN SUM(lss.emails_sent) > 0 
        THEN ROUND((SUM(lss.emails_opened)::DECIMAL / SUM(lss.emails_sent) * 100), 2)
        ELSE 0 
    END as open_rate,
    
    CASE 
        WHEN SUM(lss.emails_sent) > 0 
        THEN ROUND((SUM(lss.emails_replied)::DECIMAL / SUM(lss.emails_sent) * 100), 2)
        ELSE 0 
    END as reply_rate,
    
    CASE 
        WHEN s.total_enrolled > 0 
        THEN ROUND((s.total_completed::DECIMAL / s.total_enrolled * 100), 2)
        ELSE 0 
    END as completion_rate,
    
    s.created_at,
    s.updated_at
    
FROM sequences s
LEFT JOIN lead_sequence_state lss ON s.id = lss.sequence_id
GROUP BY s.id, s.tenant_id, s.name, s.status, s.steps_count, 
         s.total_enrolled, s.total_completed, s.total_stopped,
         s.created_at, s.updated_at;

-- Create indexes on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_sequence_performance_summary_sequence_id 
ON sequence_performance_summary(sequence_id);

CREATE INDEX IF NOT EXISTS idx_sequence_performance_summary_tenant_id 
ON sequence_performance_summary(tenant_id);

-- ==============================================
-- COMMENTS
-- ==============================================

COMMENT ON TABLE sequences IS 'Email sequences/drip campaigns definition';
COMMENT ON TABLE sequence_steps IS 'Individual steps in sequences (emails, delays, conditions, actions)';
COMMENT ON TABLE lead_sequence_state IS 'Track each lead''s progress through sequences';
COMMENT ON TABLE sequence_execution_log IS 'Audit trail of all sequence actions and events';

COMMENT ON COLUMN sequence_steps.next_step_if_true IS 'Step to jump to if condition evaluates to true';
COMMENT ON COLUMN sequence_steps.next_step_if_false IS 'Step to jump to if condition evaluates to false';
COMMENT ON COLUMN lead_sequence_state.next_action_at IS 'When to execute next step (used by scheduler)';
COMMENT ON COLUMN lead_sequence_state.assigned_variant IS 'A/B test variant assigned to this lead';

