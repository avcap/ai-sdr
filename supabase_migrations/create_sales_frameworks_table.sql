-- Sales frameworks library
CREATE TABLE IF NOT EXISTS public.sales_frameworks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    framework_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    best_for TEXT[], -- e.g., ['enterprise', 'long_sales_cycle']
    avg_deal_size_min INTEGER,
    avg_deal_size_max INTEGER,
    cycle_length_days_min INTEGER,
    cycle_length_days_max INTEGER,
    qualification_criteria JSONB,
    messaging_approach TEXT,
    channel_preferences TEXT[],
    sequence_structure JSONB,
    tactics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert standard frameworks
INSERT INTO sales_frameworks (framework_name, description, best_for, avg_deal_size_min, avg_deal_size_max, cycle_length_days_min, cycle_length_days_max, qualification_criteria, messaging_approach, channel_preferences, tactics) VALUES
('MEDDIC', 'Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion', ARRAY['enterprise', 'complex_sales', 'multi_stakeholder'], 100000, NULL, 90, 180, '{"focus": ["metrics", "economic_buyer", "decision_criteria", "decision_process", "pain", "champion"]}', 'consultative', ARRAY['email', 'phone', 'linkedin'], '{"personalization": "high", "multi_threading": true, "executive_focus": true}'),

('BANT', 'Budget, Authority, Need, Timeline', ARRAY['smb', 'transactional', 'fast_cycle'], 0, 50000, 14, 30, '{"focus": ["budget", "authority", "need", "timeline"]}', 'direct', ARRAY['email', 'phone'], '{"personalization": "medium", "velocity": "high", "qualification_first": true}'),

('SPICED', 'Situation, Pain, Impact, Critical Event, Decision', ARRAY['mid_market', 'consultative'], 25000, 250000, 30, 90, '{"focus": ["situation", "pain", "impact", "critical_event", "decision"]}', 'problem_aware', ARRAY['email', 'linkedin', 'phone'], '{"personalization": "high", "discovery_heavy": true}');

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_frameworks_deal_size ON sales_frameworks(avg_deal_size_min, avg_deal_size_max);
CREATE INDEX IF NOT EXISTS idx_frameworks_best_for ON sales_frameworks USING GIN(best_for);

