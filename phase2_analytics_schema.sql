-- ==============================================
-- PHASE 2: ANALYTICS & PERFORMANCE TRACKING
-- Database Schema Extensions
-- ==============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- ANALYTICS TABLES
-- ==============================================

-- Campaign Analytics - Time-series performance data
CREATE TABLE IF NOT EXISTS campaign_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Email metrics
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    
    -- Lead metrics
    leads_contacted INTEGER DEFAULT 0,
    leads_responded INTEGER DEFAULT 0,
    leads_qualified INTEGER DEFAULT 0,
    leads_unqualified INTEGER DEFAULT 0,
    
    -- Engagement metrics
    avg_response_time_hours DECIMAL(10,2),
    avg_lead_score DECIMAL(5,2),
    
    -- Conversion metrics
    open_rate DECIMAL(5,2),
    click_rate DECIMAL(5,2),
    reply_rate DECIMAL(5,2),
    qualification_rate DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one record per campaign per day
    UNIQUE(campaign_id, date)
);

-- Lead Engagement Tracking - Individual lead interactions
CREATE TABLE IF NOT EXISTS lead_engagement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    
    -- Engagement type
    event_type TEXT NOT NULL CHECK (event_type IN (
        'email_sent', 'email_delivered', 'email_opened', 'email_clicked', 
        'email_replied', 'email_bounced', 'email_unsubscribed',
        'linkedin_viewed', 'linkedin_connected', 'linkedin_replied',
        'meeting_scheduled', 'meeting_completed', 'meeting_cancelled',
        'lead_qualified', 'lead_unqualified', 'status_changed'
    )),
    
    -- Event details
    event_data JSONB DEFAULT '{}', -- Store email subject, link clicked, etc.
    message_id TEXT, -- For tracking specific emails
    
    -- Metadata
    user_agent TEXT,
    ip_address INET,
    location_data JSONB, -- City, country, timezone
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activity Timeline - Comprehensive activity log for campaigns
CREATE TABLE IF NOT EXISTS campaign_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Activity details
    activity_type TEXT NOT NULL CHECK (activity_type IN (
        'campaign_created', 'campaign_started', 'campaign_paused', 'campaign_completed',
        'lead_added', 'lead_contacted', 'lead_replied', 'lead_qualified',
        'sequence_assigned', 'sequence_completed',
        'email_sent', 'meeting_scheduled',
        'note_added', 'status_changed', 'bulk_action'
    )),
    
    title TEXT NOT NULL, -- Human-readable activity title
    description TEXT, -- Detailed description
    metadata JSONB DEFAULT '{}', -- Additional context
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email Tracking - Detailed email performance
CREATE TABLE IF NOT EXISTS email_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Email details
    message_id TEXT UNIQUE NOT NULL, -- Gmail message ID
    subject TEXT,
    body_preview TEXT, -- First 200 chars
    template_id UUID, -- If from template
    
    -- Tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    first_click_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    
    -- Engagement metrics
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    links_clicked JSONB DEFAULT '[]', -- Array of clicked URLs
    
    -- Status
    status TEXT DEFAULT 'sent' CHECK (status IN (
        'queued', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed'
    )),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign Comparisons - A/B test results and performance comparison
CREATE TABLE IF NOT EXISTS campaign_comparison (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Comparison details
    name TEXT NOT NULL,
    description TEXT,
    campaign_ids UUID[] NOT NULL, -- Array of campaign IDs being compared
    
    -- Test configuration
    comparison_type TEXT DEFAULT 'performance' CHECK (comparison_type IN (
        'performance', 'ab_test', 'time_period', 'audience'
    )),
    
    -- Results
    winner_campaign_id UUID, -- ID of best performing campaign
    results JSONB DEFAULT '{}', -- Detailed comparison results
    insights TEXT, -- AI-generated insights
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- INDEXES FOR ANALYTICS
-- ==============================================

-- Campaign Analytics indexes
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_tenant_id ON campaign_analytics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_campaign_id ON campaign_analytics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_date ON campaign_analytics(date);
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_campaign_date ON campaign_analytics(campaign_id, date);

-- Lead Engagement indexes
CREATE INDEX IF NOT EXISTS idx_lead_engagement_tenant_id ON lead_engagement(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lead_engagement_lead_id ON lead_engagement(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_engagement_campaign_id ON lead_engagement(campaign_id);
CREATE INDEX IF NOT EXISTS idx_lead_engagement_event_type ON lead_engagement(event_type);
CREATE INDEX IF NOT EXISTS idx_lead_engagement_created_at ON lead_engagement(created_at);

-- Campaign Activity indexes
CREATE INDEX IF NOT EXISTS idx_campaign_activity_tenant_id ON campaign_activity(tenant_id);
CREATE INDEX IF NOT EXISTS idx_campaign_activity_campaign_id ON campaign_activity(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_activity_lead_id ON campaign_activity(lead_id);
CREATE INDEX IF NOT EXISTS idx_campaign_activity_type ON campaign_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_campaign_activity_created_at ON campaign_activity(created_at DESC);

-- Email Tracking indexes
CREATE INDEX IF NOT EXISTS idx_email_tracking_tenant_id ON email_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_campaign_id ON email_tracking(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_lead_id ON email_tracking(lead_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_message_id ON email_tracking(message_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_status ON email_tracking(status);
CREATE INDEX IF NOT EXISTS idx_email_tracking_sent_at ON email_tracking(sent_at);

-- Campaign Comparison indexes
CREATE INDEX IF NOT EXISTS idx_campaign_comparison_tenant_id ON campaign_comparison(tenant_id);
CREATE INDEX IF NOT EXISTS idx_campaign_comparison_campaign_ids ON campaign_comparison USING GIN(campaign_ids);

-- ==============================================
-- ROW LEVEL SECURITY
-- ==============================================

-- Enable RLS on all analytics tables
ALTER TABLE campaign_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_engagement ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_comparison ENABLE ROW LEVEL SECURITY;

-- Campaign Analytics policies
CREATE POLICY "Users can view tenant analytics" ON campaign_analytics
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can insert analytics" ON campaign_analytics
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY "System can update analytics" ON campaign_analytics
    FOR UPDATE USING (tenant_id = get_current_tenant_id());

-- Lead Engagement policies
CREATE POLICY "Users can view tenant engagement" ON lead_engagement
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can insert engagement" ON lead_engagement
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

-- Campaign Activity policies
CREATE POLICY "Users can view tenant activity" ON campaign_activity
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can insert activity" ON campaign_activity
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

-- Email Tracking policies
CREATE POLICY "Users can view tenant emails" ON email_tracking
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY "System can manage emails" ON email_tracking
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Campaign Comparison policies
CREATE POLICY "Users can manage tenant comparisons" ON campaign_comparison
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- ==============================================
-- TRIGGERS
-- ==============================================

-- Update updated_at timestamp on change
CREATE TRIGGER update_campaign_analytics_updated_at BEFORE UPDATE ON campaign_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_tracking_updated_at BEFORE UPDATE ON email_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_comparison_updated_at BEFORE UPDATE ON campaign_comparison
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ==============================================

-- Campaign Performance Summary (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS campaign_performance_summary AS
SELECT 
    c.id as campaign_id,
    c.tenant_id,
    c.name,
    c.status,
    
    -- Lead stats
    COUNT(l.id) as total_leads,
    COUNT(CASE WHEN l.status = 'contacted' THEN 1 END) as contacted_leads,
    COUNT(CASE WHEN l.status = 'responded' THEN 1 END) as responded_leads,
    COUNT(CASE WHEN l.status = 'qualified' THEN 1 END) as qualified_leads,
    
    -- Email stats (from tracking)
    COALESCE(SUM(ca.emails_sent), 0) as total_emails_sent,
    COALESCE(SUM(ca.emails_opened), 0) as total_emails_opened,
    COALESCE(SUM(ca.emails_clicked), 0) as total_emails_clicked,
    COALESCE(SUM(ca.emails_replied), 0) as total_emails_replied,
    
    -- Rates
    CASE 
        WHEN COUNT(l.id) > 0 
        THEN ROUND((COUNT(CASE WHEN l.status = 'responded' THEN 1 END)::DECIMAL / COUNT(l.id) * 100), 2)
        ELSE 0 
    END as response_rate,
    
    CASE 
        WHEN COALESCE(SUM(ca.emails_sent), 0) > 0 
        THEN ROUND((COALESCE(SUM(ca.emails_opened), 0)::DECIMAL / COALESCE(SUM(ca.emails_sent), 1) * 100), 2)
        ELSE 0 
    END as open_rate,
    
    -- Timing
    c.created_at,
    MAX(ca.date) as last_activity_date,
    MAX(l.updated_at) as last_lead_update
    
FROM campaigns c
LEFT JOIN leads l ON c.id = l.campaign_id
LEFT JOIN campaign_analytics ca ON c.id = ca.campaign_id
GROUP BY c.id, c.tenant_id, c.name, c.status, c.created_at;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_campaign_performance_summary_campaign_id 
ON campaign_performance_summary(campaign_id);

CREATE INDEX IF NOT EXISTS idx_campaign_performance_summary_tenant_id 
ON campaign_performance_summary(tenant_id);

-- ==============================================
-- HELPER FUNCTIONS
-- ==============================================

-- Function to refresh campaign analytics for a specific date
CREATE OR REPLACE FUNCTION refresh_campaign_analytics(p_campaign_id UUID, p_date DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO campaign_analytics (
        tenant_id, campaign_id, date,
        emails_sent, emails_delivered, emails_opened, emails_clicked, emails_replied, emails_bounced,
        leads_contacted, leads_responded, leads_qualified, leads_unqualified,
        open_rate, click_rate, reply_rate
    )
    SELECT 
        c.tenant_id,
        c.id,
        p_date,
        
        -- Email metrics from engagement tracking
        COUNT(CASE WHEN le.event_type = 'email_sent' THEN 1 END),
        COUNT(CASE WHEN le.event_type = 'email_delivered' THEN 1 END),
        COUNT(CASE WHEN le.event_type = 'email_opened' THEN 1 END),
        COUNT(CASE WHEN le.event_type = 'email_clicked' THEN 1 END),
        COUNT(CASE WHEN le.event_type = 'email_replied' THEN 1 END),
        COUNT(CASE WHEN le.event_type = 'email_bounced' THEN 1 END),
        
        -- Lead metrics
        COUNT(DISTINCT CASE WHEN l.status IN ('contacted', 'responded', 'qualified') THEN l.id END),
        COUNT(DISTINCT CASE WHEN l.status = 'responded' THEN l.id END),
        COUNT(DISTINCT CASE WHEN l.status = 'qualified' THEN l.id END),
        COUNT(DISTINCT CASE WHEN l.status = 'unqualified' THEN l.id END),
        
        -- Calculate rates
        CASE 
            WHEN COUNT(CASE WHEN le.event_type = 'email_sent' THEN 1 END) > 0
            THEN ROUND((COUNT(CASE WHEN le.event_type = 'email_opened' THEN 1 END)::DECIMAL / 
                       COUNT(CASE WHEN le.event_type = 'email_sent' THEN 1 END) * 100), 2)
            ELSE 0
        END,
        CASE 
            WHEN COUNT(CASE WHEN le.event_type = 'email_opened' THEN 1 END) > 0
            THEN ROUND((COUNT(CASE WHEN le.event_type = 'email_clicked' THEN 1 END)::DECIMAL / 
                       COUNT(CASE WHEN le.event_type = 'email_opened' THEN 1 END) * 100), 2)
            ELSE 0
        END,
        CASE 
            WHEN COUNT(CASE WHEN le.event_type = 'email_sent' THEN 1 END) > 0
            THEN ROUND((COUNT(CASE WHEN le.event_type = 'email_replied' THEN 1 END)::DECIMAL / 
                       COUNT(CASE WHEN le.event_type = 'email_sent' THEN 1 END) * 100), 2)
            ELSE 0
        END
        
    FROM campaigns c
    LEFT JOIN leads l ON c.id = l.campaign_id
    LEFT JOIN lead_engagement le ON c.id = le.campaign_id 
        AND DATE(le.created_at) = p_date
    WHERE c.id = p_campaign_id
    GROUP BY c.id, c.tenant_id
    
    ON CONFLICT (campaign_id, date) 
    DO UPDATE SET
        emails_sent = EXCLUDED.emails_sent,
        emails_delivered = EXCLUDED.emails_delivered,
        emails_opened = EXCLUDED.emails_opened,
        emails_clicked = EXCLUDED.emails_clicked,
        emails_replied = EXCLUDED.emails_replied,
        emails_bounced = EXCLUDED.emails_bounced,
        leads_contacted = EXCLUDED.leads_contacted,
        leads_responded = EXCLUDED.leads_responded,
        leads_qualified = EXCLUDED.leads_qualified,
        leads_unqualified = EXCLUDED.leads_unqualified,
        open_rate = EXCLUDED.open_rate,
        click_rate = EXCLUDED.click_rate,
        reply_rate = EXCLUDED.reply_rate,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to log campaign activity
CREATE OR REPLACE FUNCTION log_campaign_activity(
    p_tenant_id UUID,
    p_campaign_id UUID,
    p_user_id UUID,
    p_lead_id UUID,
    p_activity_type TEXT,
    p_title TEXT,
    p_description TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    activity_id UUID;
BEGIN
    INSERT INTO campaign_activity (
        tenant_id, campaign_id, user_id, lead_id,
        activity_type, title, description, metadata
    ) VALUES (
        p_tenant_id, p_campaign_id, p_user_id, p_lead_id,
        p_activity_type, p_title, p_description, p_metadata
    )
    RETURNING id INTO activity_id;
    
    RETURN activity_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- COMMENTS
-- ==============================================

COMMENT ON TABLE campaign_analytics IS 'Time-series performance metrics for campaigns';
COMMENT ON TABLE lead_engagement IS 'Individual lead interaction tracking for engagement analysis';
COMMENT ON TABLE campaign_activity IS 'Comprehensive activity timeline for campaigns';
COMMENT ON TABLE email_tracking IS 'Detailed email tracking with opens, clicks, and replies';
COMMENT ON TABLE campaign_comparison IS 'A/B test results and campaign performance comparisons';

