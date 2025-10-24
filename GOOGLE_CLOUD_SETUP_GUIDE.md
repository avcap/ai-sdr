# Complete Google Cloud Setup Guide for AI SDR Project

## Overview
You need to set up Google Cloud APIs and OAuth credentials for your "ai-sdr" project to enable Gmail and Google Sheets integration.

## Step 1: Enable Required APIs

### 1.1 Go to API Library
1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for and enable these APIs:
   - **Gmail API** (for sending emails)
   - **Google Sheets API** (for CRM tracking)
   - **Google Drive API** (for creating spreadsheets)

### 1.2 Enable APIs
For each API:
1. Click on the API name
2. Click **"ENABLE"**
3. Wait for confirmation

## Step 2: Configure OAuth Consent Screen

### 2.1 Go to OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Click **"CREATE"** if you haven't set it up yet

### 2.2 App Information (Branding)
Fill in:
- **App name**: `AI SDR Application`
- **User support email**: Your email (e.g., `avius@zoecapital.net`)
- **App logo**: Upload a logo (optional)
- **App domain**: Leave blank for now
- **Developer contact information**: Your email
- Click **"SAVE AND CONTINUE"**

### 2.3 Scopes
**CRITICAL**: Add these scopes:
1. Click **"ADD OR REMOVE SCOPES"**
2. Search for and add:
   - `.../auth/gmail.send` (Send emails)
   - `.../auth/gmail.readonly` (Read emails)
   - `.../auth/spreadsheets` (Access Google Sheets)
   - `.../auth/drive.file` (Create files in Google Drive)
3. Click **"UPDATE"** then **"SAVE AND CONTINUE"**

### 2.4 Test Users
Since you're in testing mode:
1. Add your Google account email (`avius@zoecapital.net`)
2. Add any other test accounts
3. Click **"SAVE AND CONTINUE"**

### 2.5 Summary
Review and click **"BACK TO DASHBOARD"**

## Step 3: Create OAuth 2.0 Client ID

### 3.1 Go to Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"OAuth client ID"**

### 3.2 Configure OAuth Client
Fill in:
- **Application type**: `Web application`
- **Name**: `AI SDR Web Client`

### 3.3 Authorized Origins
Add:
- `http://localhost:3000` (frontend)
- `http://localhost:8000` (backend)

### 3.4 Authorized Redirect URIs
**CRITICAL**: Add these exact URIs:
- `http://localhost:3000/auth/google/callback`
- `http://localhost:8000/auth/google/callback`

### 3.5 Create and Copy Credentials
1. Click **"CREATE"**
2. **IMMEDIATELY COPY** the Client ID and Client Secret
3. Save them securely

## Step 4: Update Your Application

### 4.1 Update .env File
Open `/Users/zoecapital/ai-sdr/.env` and update:

```bash
# Google OAuth Configuration (for the application itself, not per user)
GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_NEW_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

### 4.2 Update Frontend .env.local
Open `/Users/zoecapital/ai-sdr/frontend/.env.local` and update:

```bash
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=7Dx+uXhfhB8rWxhBt7Dq7G8aWvibpJdyMIzw9YvDU0Y=

# Google OAuth (if using NextAuth with Google provider)
GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_NEW_CLIENT_SECRET_HERE
```

## Step 5: Test the Setup

### 5.1 Restart Your Application
```bash
cd /Users/zoecapital/ai-sdr
source venv/bin/activate
python backend/main.py
```

In another terminal:
```bash
cd /Users/zoecapital/ai-sdr/frontend
npm run dev
```

### 5.2 Test Google OAuth
1. Go to `http://localhost:3000`
2. Click "Connect Google"
3. You should see Google's consent screen
4. Authorize the application
5. You should be redirected back successfully

## Troubleshooting

### Common Issues:

1. **"redirect_uri_mismatch"**
   - Ensure redirect URIs match exactly in Google Cloud Console
   - Use `http://` not `https://` for localhost
   - No trailing slashes

2. **"access_denied"**
   - Add your email to test users
   - Ensure scopes are correctly configured

3. **"invalid_client"**
   - Check Client ID and Secret are correct
   - Ensure they're from the right project

4. **APIs not enabled**
   - Verify all required APIs are enabled
   - Wait a few minutes for changes to propagate

## Expected Result

After setup:
- ✅ Google OAuth button works
- ✅ Users can connect their Google accounts
- ✅ App can send emails via Gmail API
- ✅ App can create and update Google Sheets
- ✅ Campaign execution uses Google services

## Next Steps

Once OAuth is working:
1. Test campaign execution with Google integration
2. Verify emails are sent via Gmail API
3. Check Google Sheets are created automatically
4. Test with different user accounts

The key is ensuring all URIs match exactly and all required APIs are enabled!


