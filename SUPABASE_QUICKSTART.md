# 🚀 Multi-Tenant AI SDR Platform - Quick Start Guide

## **Overview**
This is a cloud-native, multi-tenant AI SDR platform built with Supabase (PostgreSQL) and FastAPI. Each business gets their own isolated data space with complete security.

## **🏗️ Architecture**

**Frontend:** Next.js + React (localhost:3000)
**Backend:** FastAPI + Supabase (localhost:8000)
**Database:** PostgreSQL (Supabase Cloud)
**Storage:** Supabase Storage (documents)
**Auth:** Supabase Auth (JWT tokens)

## **📋 Prerequisites**

1. **Supabase Account** - [supabase.com](https://supabase.com)
2. **Python 3.8+** - Backend development
3. **Node.js 16+** - Frontend development
4. **Git** - Version control

## **🚀 Quick Setup (5 minutes)**

### **Step 1: Create Supabase Project**

1. Go to [supabase.com](https://supabase.com)
2. Sign up/Sign in
3. Click "New Project"
4. Choose organization
5. Project details:
   - **Name:** `ai-sdr-platform`
   - **Database Password:** Generate strong password (save it!)
   - **Region:** Choose closest to you
6. Click "Create new project"

### **Step 2: Get Supabase Credentials**

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY`
   - **service_role secret** → `SUPABASE_SERVICE_ROLE_KEY`

3. Go to **Settings** → **Database**
   - Copy **Connection string** → `DATABASE_URL`
   - Copy **JWT secret** → `JWT_SECRET`

### **Step 3: Configure Environment**

1. Copy `supabase_config_example.txt` to `.env`
2. Fill in your Supabase credentials:

```bash
# Supabase Project Settings
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres
JWT_SECRET=your-jwt-secret-here
```

### **Step 4: Run Database Schema**

1. Go to your Supabase project dashboard
2. Click **SQL Editor**
3. Copy and paste the contents of `supabase_schema.sql`
4. Click **Run** to create all tables and policies

### **Step 5: Start the Platform**

```bash
# Backend (Terminal 1)
cd /Users/zoecapital/ai-sdr
source venv/bin/activate
python backend_multi_tenant.py

# Frontend (Terminal 2)
cd /Users/zoecapital/ai-sdr/frontend
npm run dev
```

## **🎯 What You Get**

### **Multi-Tenant Features:**
- ✅ **Complete data isolation** - Each business sees only their data
- ✅ **Row-Level Security** - Database-level tenant protection
- ✅ **Scalable architecture** - Handle unlimited tenants
- ✅ **Audit logging** - Track all user actions
- ✅ **Role-based access** - Admin, Manager, User, Viewer roles

### **AI SDR Features:**
- ✅ **Train Your Team** - Upload documents, extract knowledge
- ✅ **Smart Campaigns** - AI-powered lead generation
- ✅ **Prospector Agent** - Find leads from prompts
- ✅ **Enrichment Agent** - Score and validate leads
- ✅ **Copywriter Agent** - Generate personalized outreach
- ✅ **Campaign Management** - Track and manage campaigns

## **🔧 Development**

### **Backend API Endpoints:**

```bash
# Health Check
GET /health

# Tenant Management
POST /tenants
GET /tenants/{tenant_id}
GET /tenants/slug/{slug}

# User Management
POST /users
GET /users/{user_id}
GET /tenants/{tenant_id}/users

# Knowledge Management
POST /train-your-team/upload
POST /train-your-team/save-knowledge
GET /train-your-team/get-knowledge
GET /train-your-team/documents

# Campaign Management
POST /campaigns
GET /tenants/{tenant_id}/campaigns
POST /campaigns/{campaign_id}/leads
GET /campaigns/{campaign_id}/leads

# Agent Results
POST /agent-results
GET /tenants/{tenant_id}/agent-results

# Dashboard Stats
GET /tenants/{tenant_id}/stats
```

### **Database Schema:**

**Core Tables:**
- `tenants` - Business organizations
- `users` - Multi-tenant users
- `user_knowledge` - Extracted company knowledge
- `training_documents` - Uploaded files
- `campaigns` - Marketing campaigns
- `leads` - Campaign leads
- `agent_results` - AI agent outputs
- `audit_logs` - Action tracking

## **🚀 Deployment**

### **Frontend (Vercel):**
```bash
# Deploy to Vercel
vercel --prod
```

### **Backend (Railway/Render):**
```bash
# Deploy to Railway
railway login
railway init
railway up
```

### **Database (Supabase):**
- Already hosted on Supabase
- Automatic backups
- Real-time updates
- Built-in auth

## **💰 Pricing**

### **Development (FREE):**
- ✅ **Supabase Free Tier** - 500MB database, 50MB storage
- ✅ **Vercel Free Tier** - Frontend hosting
- ✅ **Railway Free Tier** - Backend hosting
- ✅ **Total Cost: $0/month**

### **Production (Starting $25/month):**
- ✅ **Supabase Pro** - $25/month (8GB database, 100GB storage)
- ✅ **Vercel Pro** - $20/month (unlimited deployments)
- ✅ **Railway Pro** - $5/month (unlimited usage)
- ✅ **Total Cost: $50/month**

## **🔒 Security Features**

- ✅ **Row-Level Security** - Database-level tenant isolation
- ✅ **JWT Authentication** - Secure user sessions
- ✅ **Audit Logging** - Track all actions
- ✅ **Role-Based Access** - Granular permissions
- ✅ **Data Encryption** - Sensitive data protection
- ✅ **CORS Protection** - Cross-origin security

## **📊 Monitoring**

### **Supabase Dashboard:**
- Database performance
- API usage
- Storage usage
- User authentication

### **Application Logs:**
- Backend logs in terminal
- Frontend logs in browser console
- Error tracking and debugging

## **🆘 Troubleshooting**

### **Common Issues:**

1. **"Database service unavailable"**
   - Check Supabase credentials in `.env`
   - Verify project is active in Supabase

2. **"Tenant not found"**
   - Run the database schema
   - Check tenant exists in database

3. **"Permission denied"**
   - Check Row-Level Security policies
   - Verify user has correct role

4. **"Connection timeout"**
   - Check internet connection
   - Verify Supabase project is not paused

### **Debug Commands:**

```bash
# Test Supabase connection
python -c "from services.supabase_service import SupabaseService; print(SupabaseService().test_connection())"

# Check database info
curl http://localhost:8000/database/info

# Health check
curl http://localhost:8000/health
```

## **🎉 Success!**

Your multi-tenant AI SDR platform is now running! 

**Access Points:**
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Supabase Dashboard:** Your project dashboard

**Next Steps:**
1. Create your first tenant
2. Upload training documents
3. Run a smart campaign
4. Deploy to production

Happy building! 🚀


