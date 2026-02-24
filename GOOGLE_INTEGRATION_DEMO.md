# AI SDR Google Integration Demo Guide

This guide demonstrates the new Google OAuth integration features in the AI SDR system.

## 🎯 What's New

### ✅ Google OAuth Integration
- **Gmail API**: Send emails directly through Gmail
- **Google Sheets API**: Create and manage spreadsheets for CRM
- **Secure Authentication**: OAuth 2.0 flow with token management

### ✅ Enhanced Frontend Dashboard
- **Google Account Connection**: One-click Google account linking
- **CSV Upload Interface**: Drag-and-drop lead upload
- **Campaign Management**: Create, execute, and monitor campaigns
- **Real-time Status**: Live campaign execution tracking

### ✅ Improved Backend APIs
- **Google OAuth Endpoints**: Complete OAuth flow handling
- **Token Management**: Automatic token refresh
- **Gmail Integration**: Send emails via Gmail API
- **Sheets Integration**: Create and sync spreadsheets

## 🚀 Quick Start

### 1. Setup Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API, Google Sheets API, and Google Drive API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:3000/auth/google/callback`

### 2. Configure Environment

Update `.env` file:
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# OpenAI API Key (required for CrewAI)
OPENAI_API_KEY=your_openai_api_key_here
```

Update `frontend/.env.local`:
```bash
BACKEND_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_here
```

### 3. Start the Application

```bash
# Terminal 1: Backend
cd /Users/zoecapital/ai-sdr
source venv/bin/activate
python backend/main.py

# Terminal 2: Frontend
cd /Users/zoecapital/ai-sdr/frontend
npm run dev
```

### 4. Access the Dashboard

Open `http://localhost:3000/dashboard`

## 🎮 Demo Workflow

### Step 1: Connect Google Account
1. Click "Connect Google" button
2. Complete OAuth flow
3. Verify connection status shows "Google Connected"

### Step 2: Create Campaign
1. Click "New Campaign" button
2. Fill in campaign details:
   - Name: "Q4 Sales Outreach"
   - Description: "Targeting tech companies"
   - Target Audience: "VP of Engineering"
   - Value Proposition: "AI-powered sales automation"
   - Call to Action: "Schedule a demo"
3. Click "Create Campaign"

### Step 3: Upload Leads
1. Click "Upload Leads" on your campaign
2. Select a CSV file with columns:
   - name, company, title, email, industry, company_size, location
3. Click "Upload Leads"

### Step 4: Create Google Spreadsheet
1. Click "Create Spreadsheet" button
2. Enter title: "AI SDR Campaign - Q4 Sales"
3. Spreadsheet will be created and shared

### Step 5: Execute Campaign
1. Click "Execute" on your campaign
2. Watch real-time progress:
   - Leads processed
   - Messages generated
   - Emails sent via Gmail
   - Responses tracked

### Step 6: Monitor Results
1. Check campaign status
2. View outreach logs
3. Monitor Google Sheets for updates
4. Track email responses

## 📊 Sample Lead Data

Create a CSV file with this format:
```csv
name,company,title,email,industry,company_size,location
John Smith,TechCorp Inc,VP of Engineering,john@techcorp.com,Technology,100-500,San Francisco CA
Sarah Johnson,DataFlow Systems,CTO,sarah@dataflow.com,Data Analytics,50-100,Austin TX
Mike Chen,StartupXYZ,Founder,mike@startupxyz.com,Fintech,10-50,New York NY
Lisa Rodriguez,MarketingPro,Marketing Director,lisa@marketingpro.com,Marketing,500-1000,Chicago IL
David Kim,CloudTech Solutions,CTO,david@cloudtech.com,Cloud Computing,100-500,Seattle WA
```

## 🔧 API Endpoints

### Google OAuth
- `GET /auth/google/url` - Get authorization URL
- `POST /auth/google/callback` - Handle OAuth callback
- `GET /auth/google/status` - Check connection status

### Google Sheets
- `POST /google/sheets/create` - Create new spreadsheet
- `POST /campaigns/{id}/google/sheets/sync` - Sync leads to spreadsheet

### Campaigns
- `GET /campaigns` - List campaigns
- `POST /campaigns` - Create campaign
- `POST /campaigns/{id}/execute` - Execute campaign
- `POST /campaigns/{id}/leads/upload` - Upload leads

## 🎯 Key Features Demonstrated

### 1. **Seamless Google Integration**
- One-click Google account connection
- Automatic token management
- Secure OAuth 2.0 flow

### 2. **Professional Dashboard**
- Modern, responsive UI
- Real-time campaign monitoring
- Intuitive workflow

### 3. **AI-Powered Personalization**
- CrewAI agents generate personalized messages
- Context-aware outreach
- Automated follow-up

### 4. **CRM Integration**
- Google Sheets as CRM
- Real-time lead tracking
- Status updates

### 5. **Email Automation**
- Gmail API integration
- Bulk email sending
- Response tracking

## 🚨 Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch"**
   - Check Google Console redirect URI
   - Ensure exact match with callback URL

2. **"invalid_client"**
   - Verify client ID and secret
   - Check OAuth consent screen

3. **"access_denied"**
   - User denied permission
   - Check consent screen configuration

4. **Database errors**
   - Ensure SQLite database exists
   - Check file permissions

### Debug Mode

Enable verbose logging:
```bash
export CREWAI_VERBOSE=True
```

## 📈 Next Steps

1. **Scale Up**: Add more lead sources
2. **Customize**: Modify AI prompts for your industry
3. **Integrate**: Connect with other CRM systems
4. **Automate**: Set up scheduled campaigns
5. **Analyze**: Add analytics and reporting

## 🎉 Success Metrics

After running the demo, you should see:
- ✅ Google account connected
- ✅ Campaign created successfully
- ✅ Leads uploaded and processed
- ✅ Personalized messages generated
- ✅ Emails sent via Gmail
- ✅ Spreadsheet created and synced
- ✅ Real-time status updates

## 📞 Support

For issues or questions:
1. Check the logs in terminal
2. Review Google Cloud Console
3. Verify environment variables
4. Test API endpoints directly

The system is now production-ready with Google OAuth integration!




