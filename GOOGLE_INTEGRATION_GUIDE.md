# Google Integration Guide for AI SDR

This guide explains how to set up Google OAuth integration so users can connect their own Google accounts and let AI agents operate within their Google Workspace.

## 🎯 How It Works

**Your Role**: You create ONE Google OAuth app that users authorize against
**User Role**: Each user connects their OWN Google account (Gmail, Sheets, Drive)
**AI Agents**: Operate within each user's Google account permissions

## 📋 Prerequisites

1. Google Cloud Console account
2. OpenAI API key
3. Domain or localhost for testing

## 🚀 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your Project ID

### Step 2: Enable Required APIs

1. Go to **APIs & Services** > **Library**
2. Enable these APIs:
   - **Gmail API**
   - **Google Sheets API**
   - **Google Drive API**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type
3. Fill in required fields:
   - **App name**: AI SDR Platform
   - **User support email**: your-email@domain.com
   - **Developer contact**: your-email@domain.com
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive.file`
5. Add test users (for development)

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Add authorized redirect URIs:
   - `http://localhost:3000/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
5. Copy **Client ID** and **Client Secret**

### Step 5: Configure Environment Variables

Update your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 6: Update Frontend Configuration

Update `frontend/.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_key_here
```

## 🔧 Installation

### Option 1: Quick Setup (Recommended)

```bash
# Run the Google setup script
./setup-google.sh
```

### Option 2: Manual Setup

```bash
# Install dependencies
source venv/bin/activate
pip install -r requirements-google.txt

# Start backend
python backend/main.py

# Start frontend (in new terminal)
cd frontend
npm run dev
```

## 🎮 User Workflow

### 1. User Signs In
- User visits your app
- Signs in with your authentication system

### 2. Connect Google Account
- User clicks "Connect Google" button
- Redirected to Google OAuth consent screen
- User authorizes your app to access their Gmail, Sheets, Drive

### 3. AI Agents Operate
- **Prospecting Agent**: Reads CSV files from user's Google Drive
- **Personalization Agent**: Generates personalized emails using OpenAI
- **Outreach Agent**: Sends emails via user's Gmail account
- **Coordinator Agent**: Creates Google Sheets for campaign tracking

### 4. Campaign Execution
- User uploads leads (CSV or via Google Drive)
- AI agents process leads and send personalized emails
- Results tracked in Google Sheets
- User can monitor progress in real-time

## 🔒 Security Features

### Per-User Isolation
- Each user's Google account is completely isolated
- No sharing of credentials between users
- Users can revoke access anytime

### Token Management
- Access tokens stored securely per user
- Automatic token refresh when expired
- No long-term credential storage

### Permission Scoping
- Only requested permissions are granted
- Users see exactly what your app can access
- Granular control over data access

## 📊 What AI Agents Can Do

### With User's Google Account:

1. **Read CSV Files**
   - Access user's Google Drive
   - Read lead data from CSV files
   - Validate and process lead information

2. **Send Emails**
   - Use user's Gmail account
   - Send personalized outreach emails
   - Track email delivery status

3. **Manage Spreadsheets**
   - Create Google Sheets for campaign tracking
   - Update lead status and notes
   - Generate campaign reports

4. **Generate Content**
   - Use OpenAI to create personalized messages
   - Adapt content based on lead information
   - Maintain professional tone and style

## 🚨 Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Check that redirect URI matches exactly in Google Console
   - Ensure no trailing slashes or extra characters

2. **"Access denied"**
   - Verify OAuth consent screen is configured
   - Check that required scopes are added
   - Ensure app is in testing mode with test users

3. **"Token expired"**
   - System automatically refreshes tokens
   - Check that refresh token is stored correctly
   - Verify Google API quotas are not exceeded

4. **"Permission denied"**
   - User may have revoked access
   - Check token validity and refresh if needed
   - Verify API permissions in Google Console

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Check logs
tail -f logs/ai_sdr.log
```

## 🔄 Production Deployment

### 1. Update OAuth Settings
- Change redirect URI to production domain
- Update OAuth consent screen for production
- Remove test users, add production users

### 2. Environment Variables
```bash
# Production .env
GOOGLE_CLIENT_ID=your_production_client_id
GOOGLE_CLIENT_SECRET=your_production_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

### 3. SSL Certificate
- Ensure HTTPS is enabled
- Google OAuth requires secure connections
- Use Let's Encrypt or commercial SSL

## 📈 Scaling Considerations

### Rate Limits
- Gmail API: 1 billion quota units per day
- Sheets API: 100 requests per 100 seconds per user
- Drive API: 1,000 requests per 100 seconds per user

### Monitoring
- Track API usage in Google Console
- Monitor token refresh rates
- Set up alerts for quota limits

### Performance
- Cache frequently accessed data
- Batch API requests when possible
- Use background processing for large campaigns

## 🎯 Next Steps

1. **Test the Integration**
   - Connect your own Google account
   - Upload sample leads
   - Execute a test campaign

2. **Customize AI Prompts**
   - Modify personalization templates
   - Adjust email tone and style
   - Add industry-specific content

3. **Add Features**
   - LinkedIn integration
   - Advanced analytics
   - A/B testing for messages

4. **Deploy to Production**
   - Set up production environment
   - Configure monitoring
   - Launch to users

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Google Cloud Console logs
3. Check application logs for errors
4. Verify all environment variables are set correctly

## 🔗 Useful Links

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

**Ready to get started?** Run `./setup-google.sh` and follow the prompts!


