# Fix Google OAuth Redirect URI Mismatch

## The Problem
**Error 400: redirect_uri_mismatch**

This happens when the redirect URI in your Google Cloud Console doesn't match the one your app is using.

## Current Configuration
Your app is configured to use:
```
http://localhost:3000/auth/google/callback
```

## Solution: Update Google Cloud Console

### Step 1: Go to Google Cloud Console
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" → "Credentials"

### Step 2: Edit Your OAuth 2.0 Client
1. Find your OAuth 2.0 Client ID: `313493319470-mnpjc1rvjm8jbok4kvl0cfaqdqo62kg3.apps.googleusercontent.com`
2. Click the edit (pencil) icon

### Step 3: Add Authorized Redirect URIs
Add these exact URIs to the "Authorized redirect URIs" section:

```
http://localhost:3000/auth/google/callback
http://localhost:8000/auth/google/callback
```

**Important:** 
- Include both `localhost:3000` (frontend) and `localhost:8000` (backend)
- Use `http://` not `https://` for localhost
- Include the exact path `/auth/google/callback`

### Step 4: Save Changes
1. Click "Save"
2. Wait a few minutes for changes to propagate

## Alternative: Quick Test with Different Port

If you want to test immediately, you can temporarily change your redirect URI:

1. **Update your .env file:**
```bash
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback
```

2. **Add this to Google Cloud Console:**
```
http://localhost:3001/auth/google/callback
```

3. **Restart your frontend on port 3001:**
```bash
cd frontend && npm run dev -- -p 3001
```

## Verification

After updating Google Cloud Console:

1. **Wait 2-3 minutes** for changes to propagate
2. **Test the Google button** again
3. **You should see** Google's consent screen instead of the error

## Common Mistakes to Avoid

❌ **Wrong protocol:** Using `https://` instead of `http://` for localhost
❌ **Wrong port:** Using a different port than your app
❌ **Missing path:** Not including `/auth/google/callback`
❌ **Extra characters:** Trailing slashes or spaces
❌ **Case sensitivity:** Different capitalization

## Expected Result

After fixing the redirect URI:
- Click "Connect Google" → Google consent screen appears
- User authorizes → Redirected back to your app
- Google account connected → Can send emails via Gmail API

The redirect URI must match **exactly** between your app and Google Cloud Console!


