-- Add campaign_id to sequences table to link sequences to campaigns

ALTER TABLE sequences 
ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_sequences_campaign_id ON sequences(campaign_id);

-- Update RLS policy to include campaign access
DROP POLICY IF EXISTS "Users can view their own sequences" ON sequences;
CREATE POLICY "Users can view their own sequences" ON sequences
    FOR SELECT
    USING (tenant_id IN (SELECT tenant_id FROM users WHERE id = auth.uid()));

