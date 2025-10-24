# Google OAuth Setup Guide

## Current Status
✅ **Google Button Fixed**: The authentication issue has been resolved
✅ **Backend Routes Working**: Google OAuth endpoints are accessible
❌ **Google OAuth Not Configured**: Need to set up Google Cloud Project

## The Issue
The Google button was failing because:
1. Frontend API routes were using wrong environment variable (`BACKEND_URL` instead of `NEXT_PUBLIC_BACKEND_URL`)
2. Authentication token mismatch between frontend and backend
3. Missing Google OAuth credentials

## What's Fixed
✅ Updated all frontend API routes to use `NEXT_PUBLIC_BACKEND_URL`
✅ Fixed authentication by adding `demo_token` to NextAuth session
✅ Created proper environment files
✅ Backend Google OAuth endpoints are now accessible

## Next Steps: Configure Google OAuth

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Gmail API
   - Google Sheets API
   - Google Drive API

### 2. Create OAuth 2.0 Credentials
1. Go to "Credentials" in Google Cloud Console
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:3000/auth/google/callback`
   - `http://localhost:8000/auth/google/callback` (for backend)

### 3. Update Environment Variables
Add your Google OAuth credentials to `.env`:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

### 4. Test the Integration
1. Restart the backend: `python backend/main.py`
2. Refresh the frontend: `http://localhost:3000`
3. Click "Connect Google" button
4. You should be redirected to Google OAuth consent screen

## Current Working State
- ✅ Frontend: `http://localhost:3000`
- ✅ Backend: `http://localhost:8000`
- ✅ Authentication: Working with demo token
- ✅ Google OAuth endpoints: Accessible and responding
- ❌ Google OAuth credentials: Need to be configured

## Testing Commands
```bash
# Test backend Google OAuth endpoint
curl -H "Authorization: Bearer demo_token" http://localhost:8000/auth/google/url

# Test frontend API route
curl http://localhost:3000/api/auth/google/url
```

## Troubleshooting
If you still see errors:
1. Check browser console for JavaScript errors
2. Check backend logs for Python errors
3. Verify environment variables are set correctly
4. Ensure both servers are running

The Google button should now work once you configure the Google OAuth credentials!


