# Google Re-authentication Guide

## How to Re-authenticate Your Google Account in AI SDR

### Method 1: Using the Dashboard (Recommended)

1. **Sign in to the app** at `http://localhost:3002`
   - Email: `demo@example.com`
   - Password: `password`

2. **Go to the Dashboard** - You'll see the Google Integration section

3. **If Google is already connected:**
   - Click **"Reconnect Google"** button
   - This will start a fresh OAuth flow
   - You'll be redirected to Google's consent screen
   - Grant permissions again

4. **If Google is not connected:**
   - Click **"Connect Google Account"** button
   - Follow the OAuth flow

### Method 2: Disconnect and Reconnect

1. **Disconnect your Google account:**
   - In the dashboard, click **"Disconnect"** button
   - Confirm the disconnection

2. **Reconnect your Google account:**
   - Click **"Connect Google Account"** button
   - Follow the OAuth flow

### Method 3: Using API Endpoints (Advanced)

#### Disconnect Google Account
```bash
curl -X DELETE http://localhost:8000/auth/google/disconnect \
  -H "Authorization: Bearer demo_token"
```

#### Get Google Auth URL
```bash
curl http://localhost:8000/auth/google/url \
  -H "Authorization: Bearer demo_token"
```

#### Check Google Status
```bash
curl http://localhost:8000/auth/google/status \
  -H "Authorization: Bearer demo_token"
```

### What Happens During Re-authentication

1. **Fresh OAuth Flow**: You'll be redirected to Google's consent screen
2. **Permission Grant**: You'll need to grant permissions again for:
   - Gmail (send emails)
   - Google Sheets (read/write spreadsheets)
   - Google Drive (read files)
3. **Token Refresh**: New access and refresh tokens are generated
4. **Database Update**: Your account tokens are updated in the database

### Troubleshooting

#### "Google account disconnected successfully" but still shows as connected
- Refresh the page (F5 or Cmd+R)
- The dashboard will update the status

#### OAuth consent screen shows "This app isn't verified"
- Click "Advanced" → "Go to [app name] (unsafe)"
- This is normal for development apps

#### "Access blocked" error
- Check if you're using the correct Google account
- Make sure the app has the required permissions
- Try disconnecting and reconnecting

#### Token expired errors
- The app automatically refreshes tokens
- If you see errors, try reconnecting your Google account

### Benefits of Re-authentication

- **Fresh Permissions**: Ensures you have the latest permissions
- **Token Refresh**: Gets new, valid access tokens
- **Error Resolution**: Fixes token-related issues
- **Permission Updates**: Updates if Google changed permission requirements

### Security Notes

- **Revoke Access**: You can revoke access in your Google Account settings
- **Token Security**: Tokens are stored securely in the database
- **Scope Updates**: Re-authentication ensures you have the latest scopes

---

## Quick Steps Summary

1. **Sign in** → `http://localhost:3002` (demo@example.com / password)
2. **Dashboard** → Look for "Google Integration" section
3. **Reconnect** → Click "Reconnect Google" or "Connect Google Account"
4. **Grant Permissions** → Allow access on Google's consent screen
5. **Done** → You're re-authenticated!

The app will now have fresh access to your Gmail and Google Sheets for sending emails and managing campaigns.


