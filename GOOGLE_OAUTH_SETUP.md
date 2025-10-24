# Google OAuth Setup Guide

This guide will help you set up Google OAuth integration for the AI SDR system, enabling users to connect their own Gmail and Google Sheets accounts.

## 🎯 How It Works

**Your Role**: You create ONE Google OAuth app that users authorize against
**User Role**: Each user connects their OWN Google account (Gmail, Sheets, Drive)
**Result**: Users can send emails from their Gmail and manage their own spreadsheets

## Prerequisites

- Google Cloud Console account
- Domain or localhost for testing

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Enable the following APIs:
   - **Gmail API**
   - **Google Sheets API**
   - **Google Drive API**

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Select "Web application" as the application type
4. Configure the OAuth consent screen if prompted

### OAuth Consent Screen Configuration
- **User Type**: External (for multiple users)
- **App Name**: "AI SDR Platform" (or your app name)
- **User Support Email**: Your email
- **Developer Contact**: Your email
- **Scopes**: Add the required scopes (Gmail, Sheets, Drive)

### Authorized JavaScript Origins
```
http://localhost:3000
http://127.0.0.1:3000
https://yourdomain.com  # For production
```

### Authorized Redirect URIs
```
http://localhost:3000/auth/google/callback
http://127.0.0.1:3000/auth/google/callback
https://yourdomain.com/auth/google/callback  # For production
```

## Step 4: Configure Environment Variables

### Backend (.env)
```bash
# Google OAuth Configuration
# These are YOUR app's credentials that users will authorize against
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# OpenAI API Key (required for CrewAI)
OPENAI_API_KEY=your_openai_api_key_here
```

### Frontend (.env.local)
```bash
# Backend API URL
BACKEND_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_here
```

## Step 5: OAuth Scopes

The system requests the following scopes from users:
- `https://www.googleapis.com/auth/gmail.send` - Send emails via Gmail
- `https://www.googleapis.com/auth/gmail.readonly` - Read Gmail messages
- `https://www.googleapis.com/auth/spreadsheets` - Access Google Sheets
- `https://www.googleapis.com/auth/drive.file` - Create and manage files

## Step 6: User Flow

1. **User visits your app** → Sees "Connect Google" button
2. **User clicks "Connect Google"** → Redirected to Google OAuth
3. **User authorizes your app** → Grants permission to access their Gmail/Sheets
4. **Google redirects back** → With authorization code
5. **Your app exchanges code** → For access tokens (stored securely)
6. **User can now** → Send emails from their Gmail, create their own spreadsheets

## Step 7: Testing the Integration

1. Start the backend server:
   ```bash
   cd /Users/zoecapital/ai-sdr
   source venv/bin/activate
   python backend/main.py
   ```

2. Start the frontend server:
   ```bash
   cd /Users/zoecapital/ai-sdr/frontend
   npm run dev
   ```

3. Access the dashboard at `http://localhost:3000/dashboard`

4. Click "Connect Google" to initiate the OAuth flow

5. Complete the Google authorization with YOUR Google account

6. Test Gmail and Google Sheets functionality

## Step 8: Production Deployment

For production deployment:

1. **Update OAuth credentials** with your production domain
2. **Add production redirect URIs** to Google Console
3. **Update environment variables** with production URLs
4. **Ensure HTTPS is enabled**
5. **Submit OAuth consent screen for verification** (if needed)

## 🔐 Security & Privacy

### What Users Authorize
- Users grant YOUR app permission to access their Gmail and Google Sheets
- Users can revoke access at any time in their Google Account settings
- Your app only accesses what's necessary for the AI SDR functionality

### Data Storage
- **Access tokens**: Stored encrypted in your database
- **Refresh tokens**: Stored encrypted for automatic renewal
- **User data**: Never stored, only accessed when needed

### Best Practices
1. **Minimal scopes**: Only request necessary permissions
2. **Token security**: Encrypt stored tokens
3. **Regular cleanup**: Remove unused tokens
4. **User control**: Allow users to disconnect anytime

## Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" error**
   - Ensure the redirect URI in Google Console matches exactly
   - Check for trailing slashes and protocol (http vs https)

2. **"invalid_client" error**
   - Verify client ID and secret are correct
   - Check that the OAuth consent screen is configured

3. **"access_denied" error**
   - User denied permission during OAuth flow
   - Check OAuth consent screen configuration

4. **"insufficient_scope" error**
   - Ensure all required APIs are enabled
   - Check that the requested scopes are approved

### Debug Mode

Enable debug logging by setting:
```bash
CREWAI_VERBOSE=True
```

## 📊 Multi-User Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App      │    │   Google OAuth   │    │   User's Gmail  │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ User A      │ │◄──►│ │ Your App     │ │◄──►│ │ User A's    │ │
│ │ Tokens      │ │    │ │ Credentials  │ │    │ │ Gmail       │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │                  │    │ ┌─────────────┐ │
│ │ User B      │ │◄──►│                  │◄──►│ │ User B's    │ │
│ │ Tokens      │ │    │                  │    │ │ Gmail       │ │
│ └─────────────┘ │    │                  │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 Key Benefits

1. **User Privacy**: Each user controls their own data
2. **Scalability**: No limits on number of users
3. **Security**: Users can revoke access anytime
4. **Compliance**: Meets data privacy requirements
5. **Flexibility**: Users use their own Google accounts

## Support

For issues with Google OAuth setup:
1. Check Google Cloud Console logs
2. Review OAuth consent screen configuration
3. Verify API enablement status
4. Check network connectivity and firewall settings
5. Test with different user accounts
