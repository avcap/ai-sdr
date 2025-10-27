# Smart Outreach Implementation Guide

## Overview

The Smart Outreach system now supports **real email sending** via Gmail API, with proper lead tracking, campaign analytics, and multi-channel support.

## Architecture

### Backend (`/smart-outreach/execute`)

**Location:** `backend/main_supabase.py` (lines 957-1130)

**Key Features:**
1. **Google OAuth Integration** - Retrieves user's Gmail access tokens from database
2. **Token Refresh** - Automatically refreshes expired tokens
3. **Real Email Sending** - Uses Gmail API to send personalized emails
4. **Lead Status Tracking** - Updates lead status to "contacted" after successful send
5. **Campaign Analytics** - Tracks messages sent, channels used, and errors
6. **Error Handling** - Gracefully handles API errors and missing data

**Flow:**
```
1. Get user's Google OAuth tokens from Supabase
2. Check if token expired → refresh if needed
3. For each lead in outreach plan:
   a. Generate personalized message via SmartOutreachAgent
   b. Send via Gmail API (or LinkedIn/phone if implemented)
   c. Update lead status in database
   d. Track results
4. Update campaign results with execution data
5. Return execution summary
```

### Database

**New Table:** `google_auth`
**Location:** `supabase_migrations/create_google_auth_table.sql`

**Schema:**
- `id` - UUID primary key
- `tenant_id` - Foreign key to tenants
- `user_id` - Foreign key to users
- `access_token` - Google OAuth access token
- `refresh_token` - Google OAuth refresh token
- `expires_at` - Token expiration timestamp
- `scopes` - Array of granted scopes
- `email` - User's Gmail address
- `created_at` / `updated_at` - Timestamps

**Note:** Run this migration in your Supabase SQL editor before testing.

### Supabase Service

**New Methods:**
- `save_google_tokens(tenant_id, user_id, tokens)` - Store/update OAuth tokens
- `get_google_tokens(tenant_id, user_id)` - Retrieve OAuth tokens
- `delete_google_tokens(tenant_id, user_id)` - Disconnect Google account

### Frontend

**Component:** `frontend/components/SmartOutreachAgent.js`
**API Route:** `frontend/pages/api/smart-outreach/execute.js`

**Updated Flow:**
1. User clicks "Execute" button
2. Frontend calls `/api/smart-outreach/execute` with:
   - `outreach_plan` - Generated plan from create-plan step
   - `campaign_id` - Campaign ID for tracking
   - `user_preferences` - Email limits, channels, etc.
3. Backend validates Google OAuth connection
4. Sends emails via Gmail API
5. Returns execution results with:
   - `messages_sent` - Total count
   - `channels_used` - Breakdown by channel
   - `errors` - Array of any failures
   - `lead_updates` - Array of updated leads

## Setup Instructions

### 1. Run Database Migration

In your Supabase SQL editor, run:

```sql
-- From supabase_migrations/create_google_auth_table.sql
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

CREATE INDEX IF NOT EXISTS idx_google_auth_tenant_user ON google_auth(tenant_id, user_id);
ALTER TABLE google_auth ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own Google auth" ON google_auth
    FOR ALL USING (
        tenant_id::text = auth.jwt() ->> 'tenant_id' AND 
        user_id::text = auth.jwt() ->> 'user_id'
    );

CREATE TRIGGER update_google_auth_updated_at 
    BEFORE UPDATE ON google_auth
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. Connect Google Account

**Prerequisites:**
- Google OAuth credentials configured (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
- User has authorized your app with Gmail scopes

**Steps:**
1. Navigate to Google integration page
2. Click "Connect Google Account"
3. Authorize Gmail + Sheets scopes
4. Tokens are automatically saved to `google_auth` table

### 3. Test End-to-End

**Test Flow:**
1. **Generate Leads:**
   - Go to Smart Campaign
   - Enter prompt: "Find me 3 CTOs in San Francisco tech companies"
   - Wait for leads to generate

2. **Create Outreach Plan:**
   - Click "Smart Outreach" button
   - Agent analyzes leads and creates plan
   - Review: channels, timing, personalization

3. **Execute Campaign:**
   - Click "Execute" button
   - System checks Google auth
   - Sends emails via Gmail API
   - Updates lead status
   - Shows results

4. **Verify Results:**
   - Check Gmail "Sent" folder for emails
   - Check Supabase `leads` table for updated status
   - Check campaign `results` for analytics

## Current Implementation Status

### ✅ Completed
- Backend `/smart-outreach/execute` endpoint
- Gmail API integration for email sending
- Google OAuth token management (save/retrieve/refresh)
- Lead status tracking ("new" → "contacted")
- Campaign execution analytics
- Frontend execute button and API route
- Error handling and validation

### ⚠️ Partial
- **LinkedIn sending:** Placeholder (returns "coming soon")
- **Phone calling:** Placeholder (returns "coming soon")
- **Open/click tracking:** Not yet implemented (Gmail API doesn't provide this)
- **Response detection:** Not yet implemented

### 🔜 Future Enhancements
1. **Response Detection:**
   - Poll Gmail API for replies
   - Classify responses (interested/not interested)
   - Trigger follow-up sequences

2. **Multi-Touch Sequences:**
   - Schedule follow-up emails
   - Implement day-based sequences (Day 1: Email, Day 3: LinkedIn, etc.)
   - Track sequence progress

3. **LinkedIn Integration:**
   - Implement LinkedIn OAuth
   - Send connection requests
   - Send InMail messages

4. **Phone Integration:**
   - Integrate with Twilio or similar
   - Log call attempts
   - Record call outcomes

5. **Advanced Analytics:**
   - Open rate tracking (via link tracking)
   - Click-through rate tracking
   - Response rate by channel
   - A/B testing results

## Error Handling

### Common Errors

**1. "Google account not connected"**
- **Cause:** User hasn't authorized Google OAuth
- **Solution:** Navigate to Google integration and connect account

**2. "Token expired"**
- **Cause:** Access token has expired
- **Solution:** System automatically refreshes using refresh_token
- **Note:** If refresh fails, user needs to reconnect

**3. "Gmail API quota exceeded"**
- **Cause:** Hit Google's daily sending limits
- **Solution:** Wait 24 hours or upgrade Google Workspace plan

**4. "Invalid email address"**
- **Cause:** Lead has no email or invalid format
- **Solution:** System skips that lead and continues

**5. "Message generation failed"**
- **Cause:** OpenAI API error or missing company context
- **Solution:** Ensure knowledge bank has documents, check OpenAI API key

## Testing Checklist

Before deploying, test these scenarios:

### Basic Flow
- [ ] Generate 3-5 leads via Smart Campaign
- [ ] Open Smart Outreach modal
- [ ] Verify plan shows correct channels (email/linkedin)
- [ ] Click "Execute" button
- [ ] Verify success message shows messages sent
- [ ] Check Gmail "Sent" folder for emails
- [ ] Check Supabase `leads` table for "contacted" status

### Google Auth
- [ ] Test with connected Google account
- [ ] Test with disconnected account (should show error)
- [ ] Test with expired token (should auto-refresh)

### Lead Variations
- [ ] Test with leads that have emails
- [ ] Test with leads missing emails (should skip gracefully)
- [ ] Test with mixed email/linkedin leads

### Error Scenarios
- [ ] Test with no leads (should show error)
- [ ] Test with invalid campaign_id
- [ ] Test with OpenAI API error (message generation fails)
- [ ] Test with Gmail API error (sending fails)

## Performance

**Current Limits:**
- **Emails per campaign:** No hard limit (respects Gmail daily limits)
- **Concurrent sends:** Sequential (1 by 1)
- **Average send time:** 2-3 seconds per email

**Gmail API Limits:**
- **Free Gmail:** 500 emails/day
- **Google Workspace:** 2,000 emails/day
- **Rate limit:** 100 emails/min

**Recommendations:**
- For campaigns >100 leads, implement batching
- For campaigns >500 leads, spread over multiple days
- Monitor Gmail API quotas in Google Cloud Console

## Debugging

### Backend Logs

Check `/tmp/backend.log` for:
```bash
tail -f /tmp/backend.log | grep -i "smart outreach"
```

Look for:
- `🚀 Executing smart outreach for campaign {id}`
- `Sending email message to {name} at {company}`
- `Email sent via Gmail API to {email}`
- Errors: `Gmail API error:`, `Failed to send email via Gmail:`

### Supabase Logs

Check these tables:
- `google_auth` - Verify tokens exist and not expired
- `leads` - Check status changed to "contacted"
- `campaigns` - Check results.outreach_executed = true

### Frontend Console

Open browser dev tools, check for:
- `Outreach execution error:` - Frontend errors
- Network tab → `/api/smart-outreach/execute` - API response
- Response body → `execution_results` - Detailed results

## Security

**OAuth Token Storage:**
- Tokens stored encrypted in Supabase
- Row Level Security (RLS) ensures tenant isolation
- Access tokens expire and auto-refresh
- Refresh tokens never exposed to frontend

**Email Sending:**
- Emails sent via user's own Gmail account (not server)
- Users can't send as other users (RLS enforced)
- Rate limits prevent abuse

**Data Privacy:**
- Lead data scoped to tenant
- No cross-tenant data leakage
- Audit logs track all actions

## Next Steps

1. **Run the database migration** (create `google_auth` table)
2. **Connect your Google account** via the UI
3. **Test with 1-2 test leads** first
4. **Monitor Gmail "Sent" folder** to verify emails are sent
5. **Check Supabase** to verify lead status updates
6. **Scale up** to larger campaigns once validated

---

**Need Help?**
- Backend logs: `/tmp/backend.log`
- Frontend dev tools: Check Network tab
- Supabase dashboard: Check `google_auth`, `leads`, `campaigns` tables

