# Google OAuth App Verification Process

## Option 2: Submit for Verification (Production)

### Step 1: Complete App Information
1. Go to **APIs & Services** → **OAuth consent screen**
2. Complete all required sections:
   - **App Information**: Name, logo, support email
   - **Scopes**: All required scopes added
   - **Test Users**: Add initial test users
   - **Contact Information**: Developer contact details

### Step 2: Submit for Verification
1. In OAuth consent screen, click **"Publish App"**
2. Google will review your application
3. Review process can take **days to weeks**
4. Google may request additional information

### Step 3: Verification Requirements
Google requires:
- **Privacy Policy**: Must be publicly accessible
- **Terms of Service**: Must be publicly accessible
- **App Domain Verification**: Verify your domain
- **Sensitive Scopes**: May require additional justification
- **App Review**: Google reviews app functionality

## Option 3: Use Internal User Type (Organization Only)

### If you're in a Google Workspace organization:
1. Go to **OAuth consent screen**
2. Change **User Type** from "External" to "Internal"
3. Only users in your organization can access
4. No verification required for internal apps

## Recommendation for Development

**Keep testing mode** for now because:
- ✅ Faster setup (no verification needed)
- ✅ Easy to add/remove test users
- ✅ No privacy policy required
- ✅ Perfect for development and testing

## For Production Later

When ready for production:
1. Create privacy policy and terms of service
2. Verify your domain
3. Submit for Google verification
4. Wait for approval

## Current Status

Your app is in **testing mode** which is perfect for development. Just add test users as needed!


