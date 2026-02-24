import sys
import os
if '__file__' in globals():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import os
from datetime import datetime
import uuid
import asyncio
import time
from pathlib import Path
import logging

from agents.google_workflow import AISDRWorkflow, CampaignData, LeadData
from integrations.email_service import EmailService
from integrations.linkedin_service import LinkedInService
from integrations.google_sheets_service import GoogleSheetsService
from integrations.google_oauth_service import GoogleOAuthService
from services.supabase_service import SupabaseService
from services.sequence_execution_service import sequence_execution_service
from services.ai_sequence_generator import AISequenceGenerator
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase service
try:
    supabase_service = SupabaseService()
    logger.info("✅ Supabase service initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase: {e}")
    raise

# FastAPI app
app = FastAPI(title="AI SDR API", version="1.0.0")

# Initialize background scheduler for sequence execution
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    try:
        # Schedule sequence processor to run every 1 minute
        scheduler.add_job(
            sequence_execution_service.process_all_sequences,
            'interval',
            minutes=1,
            id='sequence_processor',
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ Sequence execution scheduler started (runs every 1 minute)")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on app shutdown"""
    try:
        scheduler.shutdown()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency to get current user (simplified for demo)
def get_current_user():
    # In production, implement proper JWT validation
    return {
        "user_id": "89985897-54af-436b-8ff5-61c5fa30f434", 
        "email": "demo@example.com", 
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
    }

# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    description: str
    target_audience: str
    value_proposition: str
    call_to_action: str

class CampaignResponse(BaseModel):
    id: str
    name: str
    description: str
    target_audience: Optional[str] = ""
    value_proposition: Optional[str] = ""
    call_to_action: Optional[str] = ""
    status: str
    created_at: str
    updated_at: str

class LeadCreate(BaseModel):
    name: str
    company: str
    title: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None

class LeadResponse(BaseModel):
    id: str
    campaign_id: str
    name: str
    company: str
    title: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    status: str
    score: Optional[int] = 0
    data: Optional[Dict[str, Any]] = {}
    created_at: str
    updated_at: Optional[str] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_audience: Optional[str] = None
    value_proposition: Optional[str] = None
    call_to_action: Optional[str] = None
    status: Optional[str] = None

class CampaignStats(BaseModel):
    campaign_id: str
    total_leads: int
    contacted_leads: int
    replied_leads: int
    qualified_leads: int
    new_leads: int
    reply_rate: float
    contact_rate: float
    qualification_rate: float
    status_breakdown: Dict[str, int]

class CampaignWithStats(CampaignResponse):
    total_leads: int = 0
    contacted_leads: int = 0
    replied_leads: int = 0
    reply_rate: float = 0.0
    last_activity: Optional[str] = None
    progress_percentage: float = 0.0

# API Endpoints

@app.get("/")
async def root():
    return {"message": "AI SDR API is running with Supabase"}

@app.get("/health")
async def health_check():
    # Test Supabase connection
    try:
        supabase_service.test_connection()
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "database": "supabase",
            "redis": "disabled"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Google Auth endpoints
@app.get("/auth/google/status")
async def get_google_auth_status(current_user: dict = Depends(get_current_user)):
    """Get Google authentication status"""
    try:
        # Check if user has Google tokens in database
        google_tokens = supabase_service.get_google_tokens(
            current_user["tenant_id"],
            current_user["user_id"]
        )
        
        if google_tokens and google_tokens.get("access_token"):
            return {
                "connected": True,
                "email": google_tokens.get("email"),
                "status": "connected"
            }
        else:
            return {
                "connected": False,
                "email": None,
                "status": "not_connected"
            }
    except Exception as e:
        logger.error(f"Google auth status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/google/url")
async def get_google_auth_url(
    current_user: dict = Depends(get_current_user)
):
    """Get Google OAuth authorization URL"""
    try:
        google_oauth = GoogleOAuthService()
        state = f"user_{current_user['user_id']}"
        auth_url = google_oauth.get_authorization_url(state)
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to get Google auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class GoogleCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

@app.post("/auth/google/callback")
async def handle_google_callback(
    request: GoogleCallbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Handle Google OAuth callback"""
    try:
        code = request.code
        
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        google_oauth = GoogleOAuthService()
        tokens = google_oauth.exchange_code_for_tokens(code)
        
        # Get user's Google email
        gmail_service = google_oauth.get_gmail_service(tokens["access_token"])
        profile = gmail_service.users().getProfile(userId='me').execute()
        google_email = profile['emailAddress']
        
        # Save tokens to google_auth table
        supabase_service.save_google_tokens(
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            tokens={
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "expires_at": tokens.get("expires_at"),
                "scopes": tokens.get("scopes", []),
                "email": google_email
            }
        )
        
        logger.info(f"✅ Google account connected for user {current_user['user_id']}: {google_email}")
        
        return {
            "success": True,
            "message": "Google account connected successfully",
            "google_email": google_email
        }
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/auth/google/disconnect")
async def disconnect_google(
    current_user: dict = Depends(get_current_user)
):
    """Disconnect Google account"""
    try:
        supabase_service.delete_google_tokens(
            current_user["tenant_id"],
            current_user["user_id"]
        )
        
        logger.info(f"✅ Google account disconnected for user {current_user['user_id']}")
        
        return {
            "success": True,
            "message": "Google account disconnected"
        }
    except Exception as e:
        logger.error(f"Failed to disconnect Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Campaign endpoints
@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new campaign"""
    try:
        logger.info(f"📝 Creating campaign: {campaign.name}")
        
        # Create campaign in Supabase
        campaign_data = {
            "name": campaign.name,
            "description": campaign.description,
            "target_audience": campaign.target_audience,
            "value_proposition": campaign.value_proposition,
            "call_to_action": campaign.call_to_action,
            "status": "draft"
        }
        
        result = supabase_service.client.table("campaigns").insert({
            "tenant_id": current_user["tenant_id"],
            "user_id": current_user["user_id"],
            **campaign_data
        }).execute()
        
        if result.data:
            campaign_record = result.data[0]
            logger.info(f"✅ Campaign created: {campaign_record['id']}")
            return CampaignResponse(**campaign_record)
        else:
            raise HTTPException(status_code=500, detail="Failed to create campaign")
            
    except Exception as e:
        logger.error(f"❌ Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns", response_model=List[CampaignWithStats])
async def get_campaigns(
    current_user: dict = Depends(get_current_user)
):
    """Get all campaigns for the current user with aggregated stats"""
    try:
        logger.info(f"📋 Getting campaigns for user: {current_user['user_id']}")
        
        result = supabase_service.client.table("campaigns").select("*").eq("tenant_id", current_user["tenant_id"]).order("created_at", desc=True).execute()
        
        campaigns = result.data or []
        logger.info(f"✅ Found {len(campaigns)} campaigns")
        
        # Enrich each campaign with stats
        campaigns_with_stats = []
        for campaign in campaigns:
            # Get lead counts for this campaign
            leads_result = supabase_service.client.table("leads").select("status, data").eq("campaign_id", campaign["id"]).execute()
            leads = leads_result.data or []
            
            total_leads = len(leads)
            contacted_leads = len([l for l in leads if l.get("status") in ["contacted", "responded", "qualified", "unqualified"]])
            replied_leads = len([l for l in leads if l.get("status") in ["responded", "qualified"]])
            
            reply_rate = (replied_leads / contacted_leads * 100) if contacted_leads > 0 else 0.0
            progress_percentage = (contacted_leads / total_leads * 100) if total_leads > 0 else 0.0
            
            # Get last activity from lead data
            last_activity = None
            for lead in leads:
                if lead.get("data") and isinstance(lead["data"], dict):
                    outreach_log = lead["data"].get("outreach_log", [])
                    if outreach_log and len(outreach_log) > 0:
                        last_activity = outreach_log[-1].get("timestamp")
                        break
            
            campaign_with_stats = CampaignWithStats(
                **campaign,
                total_leads=total_leads,
                contacted_leads=contacted_leads,
                replied_leads=replied_leads,
                reply_rate=round(reply_rate, 1),
                last_activity=last_activity,
                progress_percentage=round(progress_percentage, 1)
            )
            campaigns_with_stats.append(campaign_with_stats)
        
        return campaigns_with_stats
        
    except Exception as e:
        logger.error(f"❌ Error getting campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific campaign"""
    try:
        logger.info(f"🔍 Getting campaign: {campaign_id}")
        
        result = supabase_service.client.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if result.data:
            campaign = result.data[0]
            logger.info(f"✅ Campaign found: {campaign['name']}")
            return CampaignResponse(**campaign)
        else:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
    except Exception as e:
        logger.error(f"❌ Error getting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a campaign"""
    try:
        logger.info(f"✏️ Updating campaign: {campaign_id}")
        
        # Verify campaign exists and belongs to user
        campaign_result = supabase_service.client.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Build update dict (only include fields that were provided)
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            # No updates provided, return existing campaign
            return CampaignResponse(**campaign_result.data[0])
        
        # Update campaign
        result = supabase_service.client.table("campaigns").update(update_data).eq("id", campaign_id).execute()
        
        if result.data:
            updated_campaign = result.data[0]
            logger.info(f"✅ Campaign updated: {updated_campaign['name']}")
            return CampaignResponse(**updated_campaign)
        else:
            raise HTTPException(status_code=500, detail="Failed to update campaign")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a campaign and all associated leads"""
    try:
        logger.info(f"🗑️ Deleting campaign: {campaign_id}")
        
        # Verify campaign exists and belongs to user
        campaign_result = supabase_service.client.table("campaigns").select("name").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_name = campaign_result.data[0]["name"]
        
        # Delete campaign (leads will be cascade deleted due to foreign key)
        supabase_service.client.table("campaigns").delete().eq("id", campaign_id).execute()
        
        logger.info(f"✅ Campaign deleted: {campaign_name}")
        return {"success": True, "message": f"Campaign '{campaign_name}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed statistics for a campaign"""
    try:
        logger.info(f"📊 Getting stats for campaign: {campaign_id}")
        
        # Verify campaign exists
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get all leads for this campaign
        leads_result = supabase_service.client.table("leads").select("status").eq("campaign_id", campaign_id).execute()
        leads = leads_result.data or []
        
        total_leads = len(leads)
        new_leads = len([l for l in leads if l.get("status") == "new"])
        contacted_leads = len([l for l in leads if l.get("status") in ["contacted", "responded", "qualified", "unqualified"]])
        replied_leads = len([l for l in leads if l.get("status") in ["responded", "qualified"]])
        qualified_leads = len([l for l in leads if l.get("status") == "qualified"])
        
        # Calculate rates
        reply_rate = (replied_leads / contacted_leads * 100) if contacted_leads > 0 else 0.0
        contact_rate = (contacted_leads / total_leads * 100) if total_leads > 0 else 0.0
        qualification_rate = (qualified_leads / replied_leads * 100) if replied_leads > 0 else 0.0
        
        # Status breakdown
        status_breakdown = {}
        for lead in leads:
            status = lead.get("status", "new")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        stats = CampaignStats(
            campaign_id=campaign_id,
            total_leads=total_leads,
            contacted_leads=contacted_leads,
            replied_leads=replied_leads,
            qualified_leads=qualified_leads,
            new_leads=new_leads,
            reply_rate=round(reply_rate, 1),
            contact_rate=round(contact_rate, 1),
            qualification_rate=round(qualification_rate, 1),
            status_breakdown=status_breakdown
        )
        
        logger.info(f"✅ Stats calculated: {total_leads} total leads")
        return stats
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting campaign stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/execute")
async def execute_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Execute a campaign using the CrewAI multi-agent workflow (Prospector, Personalization, Outreach, Coordinator)."""
    try:
        logger.info(f"🚀 Executing campaign {campaign_id} with CrewAI workflow")
        campaign_result = supabase_service.client.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        campaign_row = campaign_result.data[0]
        leads_result = supabase_service.client.table("leads").select("*").eq("campaign_id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        leads = leads_result.data or []
        if not leads:
            raise HTTPException(status_code=400, detail="Campaign has no leads")
        created_at = campaign_row.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if "Z" in created_at else datetime.fromisoformat(created_at)
        else:
            created_at = created_at or datetime.utcnow()
        from agents.workflow import AISDRWorkflow as CrewAIWorkflow, CampaignData as CrewCampaignData
        campaign_data = CrewCampaignData(
            campaign_id=campaign_id,
            name=campaign_row.get("name", ""),
            description=campaign_row.get("description", "") or "",
            target_audience=campaign_row.get("target_audience", "") or "",
            value_proposition=campaign_row.get("value_proposition", "") or "",
            call_to_action=campaign_row.get("call_to_action", "") or "",
            created_at=created_at,
            status=campaign_row.get("status", "draft"),
        )
        leads_data = []
        for lead in leads:
            leads_data.append({
                "name": lead.get("name", ""),
                "company": lead.get("company", ""),
                "title": lead.get("title", ""),
                "email": lead.get("email"),
                "linkedin_url": lead.get("linkedin_url"),
                "phone": lead.get("phone"),
                "industry": (lead.get("data") or {}).get("industry") if isinstance(lead.get("data"), dict) else None,
                "company_size": (lead.get("data") or {}).get("company_size") if isinstance(lead.get("data"), dict) else None,
                "location": (lead.get("data") or {}).get("location") if isinstance(lead.get("data"), dict) else None,
            })
        workflow = CrewAIWorkflow()
        workflow.create_crew(campaign_id, leads_data, campaign_data)
        results = workflow.execute_campaign()
        supabase_service.client.table("campaigns").update({"status": "active", "updated_at": datetime.utcnow().isoformat()}).eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        return {
            "success": True,
            "message": "Campaign executed with CrewAI workflow",
            "campaign_id": campaign_id,
            "result": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error executing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lead endpoints
@app.post("/campaigns/{campaign_id}/leads", response_model=LeadResponse)
async def create_lead(
    campaign_id: str,
    lead: LeadCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new lead for a campaign"""
    try:
        logger.info(f"👤 Creating lead: {lead.name} for campaign: {campaign_id}")
        
        # Verify campaign exists
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Create lead in Supabase
        lead_data = {
            "tenant_id": current_user["tenant_id"],
            "campaign_id": campaign_id,
            "name": lead.name,
            "company": lead.company,
            "title": lead.title,
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "phone": lead.phone,
            "status": "new"
        }
        
        result = supabase_service.client.table("leads").insert(lead_data).execute()
        
        if result.data:
            lead_record = result.data[0]
            logger.info(f"✅ Lead created: {lead_record['id']}")
            return LeadResponse(**lead_record)
        else:
            raise HTTPException(status_code=500, detail="Failed to create lead")
            
    except Exception as e:
        logger.error(f"❌ Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/leads/upload")
async def upload_leads(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload leads from CSV/Excel file with smart, flexible column mapping"""
    try:
        logger.info(f"📤 Uploading leads file: {file.filename} for campaign: {campaign_id}")
        
        # Verify campaign exists
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Read file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Normalize column names: lowercase, strip whitespace
        df.columns = df.columns.str.lower().str.strip()
        
        # Define column mappings (handle common variations)
        column_mapping = {
            'name': ['name', 'full name', 'contact name', 'lead name'],
            'company': ['company', 'company name', 'organization', 'org'],
            'title': ['title', 'job title', 'position', 'role'],
            'email': ['email', 'email address', 'e-mail', 'contact email'],
            'phone': ['phone', 'phone number', 'telephone', 'mobile', 'cell'],
            'linkedin_url': ['linkedin_url', 'linkedin', 'linkedin url', 'linkedin profile', 'li url'],
            'industry': ['industry', 'sector', 'vertical'],
            'company_size': ['company_size', 'company size', 'size', 'employees', '# of employees', 'employee count'],
            'location': ['location', 'city', 'region', 'country', 'geography'],
            'website': ['website', 'company website', 'url', 'web']
        }
        
        # Map columns to standardized names
        standardized_columns = {}
        for standard_name, variations in column_mapping.items():
            for col in df.columns:
                if col in variations:
                    standardized_columns[col] = standard_name
                    break
        
        # Rename columns to standardized names
        df.rename(columns=standardized_columns, inplace=True)
        
        # Validate required columns
        required_columns = ['name', 'company', 'title']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}. Please ensure your CSV has columns for contact name, company, and job title."
            )
        
        # Prepare leads data
        leads_data = []
        unknown_columns = []
        
        for _, row in df.iterrows():
            lead_data = {
                "tenant_id": current_user["tenant_id"],
                "campaign_id": campaign_id,
                "name": str(row['name']) if pd.notna(row['name']) else '',
                "company": str(row['company']) if pd.notna(row['company']) else '',
                "title": str(row['title']) if pd.notna(row['title']) else '',
                "status": "new"
            }
            
            # Add optional columns if present
            if 'email' in df.columns and pd.notna(row.get('email')):
                lead_data['email'] = str(row['email'])
            if 'linkedin_url' in df.columns and pd.notna(row.get('linkedin_url')):
                lead_data['linkedin_url'] = str(row['linkedin_url'])
            if 'phone' in df.columns and pd.notna(row.get('phone')):
                lead_data['phone'] = str(row['phone'])
            
            # Store unknown columns in metadata (for future enhancement)
            metadata = {}
            for col in df.columns:
                if col not in ['name', 'company', 'title', 'email', 'linkedin_url', 'phone'] and pd.notna(row.get(col)):
                    metadata[col] = str(row[col])
                    if col not in unknown_columns:
                        unknown_columns.append(col)
            
            if metadata:
                # Store metadata as JSON string if you have a metadata field
                # For now, we'll just log it
                pass
            
            leads_data.append(lead_data)
        
        # Insert leads in batch
        result = supabase_service.client.table("leads").insert(leads_data).execute()
        
        leads_created = len(result.data) if result.data else 0
        logger.info(f"✅ Uploaded {leads_created} leads")
        
        # Log unknown columns for analytics
        if unknown_columns:
            logger.info(f"📊 Detected additional columns (stored for future use): {unknown_columns}")
        
        return {
            "message": f"Successfully uploaded {leads_created} leads",
            "leads_created": leads_created,
            "additional_columns_detected": unknown_columns if unknown_columns else []
        }
        
    except Exception as e:
        logger.error(f"❌ Error uploading leads: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/campaigns/{campaign_id}/leads", response_model=List[LeadResponse])
async def get_leads(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    """Get leads for a campaign with optional filtering and pagination"""
    try:
        logger.info(f"📋 Getting leads for campaign: {campaign_id} (page {page}, limit {limit})")
        
        # Verify campaign belongs to user
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Build query
        query = supabase_service.client.table("leads").select("*").eq("campaign_id", campaign_id).eq("tenant_id", current_user["tenant_id"])
        
        # Apply status filter if provided
        if status and status != 'all':
            query = query.eq("status", status)
        
        # Apply search filter if provided (search in name, company, title)
        if search:
            # Note: Supabase doesn't support OR queries easily, so we'll filter in memory
            # In production, you'd want to use full-text search or add a search endpoint
            pass
        
        # Order by created_at descending
        query = query.order("created_at", desc=True)
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit - 1
        query = query.range(start, end)
        
        result = query.execute()
        leads = result.data or []
        
        # Apply search filter in memory if provided
        if search:
            search_lower = search.lower()
            leads = [
                lead for lead in leads
                if (search_lower in lead.get('name', '').lower() or
                    search_lower in lead.get('company', '').lower() or
                    search_lower in lead.get('title', '').lower() or
                    search_lower in lead.get('email', '').lower())
            ]
        
        logger.info(f"✅ Found {len(leads)} leads")
        
        return [LeadResponse(**lead) for lead in leads]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific lead by ID"""
    try:
        logger.info(f"🔍 Getting lead: {lead_id}")
        
        result = supabase_service.client.table("leads").select("*").eq("id", lead_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if result.data:
            lead = result.data[0]
            logger.info(f"✅ Lead found: {lead['name']}")
            return LeadResponse(**lead)
        else:
            raise HTTPException(status_code=404, detail="Lead not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    updates: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a lead"""
    try:
        logger.info(f"✏️ Updating lead: {lead_id}")
        
        # Verify lead exists and belongs to user
        lead_result = supabase_service.client.table("leads").select("*").eq("id", lead_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Build update dict (only include fields that were provided)
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            # No updates provided, return existing lead
            return LeadResponse(**lead_result.data[0])
        
        # Update lead
        result = supabase_service.client.table("leads").update(update_data).eq("id", lead_id).execute()
        
        if result.data:
            updated_lead = result.data[0]
            logger.info(f"✅ Lead updated: {updated_lead['name']}")
            return LeadResponse(**updated_lead)
        else:
            raise HTTPException(status_code=500, detail="Failed to update lead")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a lead"""
    try:
        logger.info(f"🗑️ Deleting lead: {lead_id}")
        
        # Verify lead exists and belongs to user
        lead_result = supabase_service.client.table("leads").select("name").eq("id", lead_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead_name = lead_result.data[0]["name"]
        
        # Delete lead
        supabase_service.client.table("leads").delete().eq("id", lead_id).execute()
        
        logger.info(f"✅ Lead deleted: {lead_name}")
        return {"success": True, "message": f"Lead '{lead_name}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/leads/bulk-update")
async def bulk_update_leads(
    campaign_id: str,
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Bulk update multiple leads"""
    try:
        lead_ids = request.get("lead_ids", [])
        updates = request.get("updates", {})
        
        if not lead_ids:
            raise HTTPException(status_code=400, detail="No lead IDs provided")
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        logger.info(f"📝 Bulk updating {len(lead_ids)} leads")
        
        # Verify campaign belongs to user
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Update each lead (Supabase doesn't support bulk update with IN clause easily)
        updated_count = 0
        for lead_id in lead_ids:
            try:
                result = supabase_service.client.table("leads").update(updates).eq("id", lead_id).eq("tenant_id", current_user["tenant_id"]).eq("campaign_id", campaign_id).execute()
                if result.data:
                    updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to update lead {lead_id}: {e}")
                continue
        
        logger.info(f"✅ Updated {updated_count} leads")
        return {
            "success": True,
            "message": f"Successfully updated {updated_count} leads",
            "updated_count": updated_count
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error bulk updating leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Train Your Team endpoints
@app.post("/train-your-team/upload")
async def upload_training_files(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Upload documents for AI agent training or process URL content"""
    try:
        logger.info(f"📤 Upload request received from user: {current_user['user_id']}")
        
        # Check content type to determine if it's JSON (URL) or multipart (files)
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Handle URL request
            body = await request.json()
            url = body.get("url")
            document_type = body.get("document_type")
            
            if not url or not document_type:
                raise HTTPException(status_code=400, detail="URL and document_type are required")
            
            logger.info(f"🌐 Processing URL: {url}")
            logger.info(f"📋 Document type: {document_type}")
            
            # Scrape URL content
            try:
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text_content = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Save content to file
                upload_dir = Path("uploads/training")
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"url_content_{hash(url)}.txt"
                file_path = upload_dir / f"{current_user['user_id']}_{filename}"
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(clean_text)
                
                logger.info(f"✅ URL content saved to: {file_path}")
                
                # Save document record in Supabase
                document_data = {
                    "tenant_id": current_user["tenant_id"],
                    "user_id": current_user["user_id"],
                    "filename": filename,
                    "file_path": str(file_path),
                    "file_size": len(clean_text),
                    "file_type": ".txt",
                    "document_type": document_type,
                    "status": "uploaded"
                }
                
                result = supabase_service.client.table("training_documents").insert(document_data).execute()
                
                return {
                    "success": True,
                    "message": "URL content processed successfully",
                    "uploaded_files": [{
                        "filename": filename,
                        "path": str(file_path),
                        "size": len(clean_text),
                        "document_id": result.data[0]["id"] if result.data else None,
                        "url": url
                    }],
                    "content_path": str(file_path)
                }
                
            except Exception as e:
                logger.error(f"❌ URL processing error: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process URL: {str(e)}")
        
        else:
            # Handle file upload (multipart/form-data)
            form = await request.form()
            files = form.getlist("files")
            document_type = form.get("document_type")
            
            if not files:
                logger.error("❌ No files provided for upload")
                raise HTTPException(status_code=400, detail="No files provided")
            
            if not document_type:
                logger.error("❌ No document type provided")
                raise HTTPException(status_code=400, detail="Document type is required")
            
            logger.info(f"📁 Number of files: {len(files)}")
            logger.info(f"📋 Document type: {document_type}")
            
            # Log each file details
            for i, file in enumerate(files):
                logger.info(f"📄 Uploading file {i+1}: {file.filename}")
            
            # Create upload directory if it doesn't exist
            upload_dir = Path("uploads/training")
            upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📂 Upload directory: {upload_dir.absolute()}")
            
            uploaded_files = []
            for file in files:
                # Validate file type
                allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt']
                file_extension = Path(file.filename).suffix.lower()
                logger.info(f"🔍 File extension: {file_extension}")
                
                if file_extension not in allowed_extensions:
                    logger.error(f"❌ Unsupported file type: {file_extension}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported file type: {file_extension}. Allowed: {allowed_extensions}"
                    )
                
                # Save file
                file_path = upload_dir / f"{current_user['user_id']}_{file.filename}"
                logger.info(f"💾 Saving file to: {file_path}")
                
                content = await file.read()
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                logger.info(f"✅ File saved successfully: {file_path} ({len(content)} bytes)")
                
                # Save document record in Supabase
                document_data = {
                    "tenant_id": current_user["tenant_id"],
                    "user_id": current_user["user_id"],
                    "filename": file.filename,
                    "file_path": str(file_path),
                    "file_size": len(content),
                    "file_type": file_extension,
                    "document_type": document_type,
                    "status": "uploaded"
                }
                
                result = supabase_service.client.table("training_documents").insert(document_data).execute()
                
                uploaded_files.append({
                    "filename": file.filename,
                    "path": str(file_path),
                    "size": len(content),
                    "document_id": result.data[0]["id"] if result.data else None
                })
            
            logger.info(f"🎉 Successfully uploaded {len(uploaded_files)} files")
            return {
                "success": True,
                "message": f"Successfully uploaded {len(uploaded_files)} files",
                "uploaded_files": uploaded_files
            }
        
    except Exception as e:
        logger.error(f"💥 Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-your-team/extract-knowledge")
async def extract_knowledge_from_files(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Extract knowledge from uploaded documents using Claude AI"""
    try:
        logger.info(f"🔍 Knowledge extraction request received from user: {current_user['user_id']}")
        logger.info(f"📋 Request body: {request}")
        
        files = request.get("files", [])
        document_type = request.get("document_type", "")
        logger.info(f"📁 Files in request: {len(files)} files")
        logger.info(f"📋 Document type: {document_type}")
        
        if not files:
            logger.error("❌ No files provided in request")
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Log each file details
        for i, file in enumerate(files):
            logger.info(f"📄 File {i+1}: {file}")
        
        # Import the knowledge extraction agent
        from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
        
        # Initialize and run the knowledge extraction agent
        logger.info("🤖 Initializing Knowledge Extraction Agent...")
        agent = KnowledgeExtractionAgent()
        
        # Extract file paths
        file_paths = [file["path"] for file in files]
        logger.info(f"🗂️ File paths to process: {file_paths}")
        
        # Check if files exist
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                raise HTTPException(status_code=400, detail=f"File not found: {file_path}")
            else:
                logger.info(f"✅ File exists: {file_path}")
        
        logger.info("🚀 Starting knowledge extraction...")
        
        # Pass document_type to the agent if provided
        if document_type:
            result = agent.extract_knowledge_from_files(file_paths, document_type=document_type)
        else:
            result = agent.extract_knowledge_from_files(file_paths)
        
        if result["success"]:
            logger.info("✅ Knowledge extraction completed successfully")
            logger.info(f"📊 Extracted knowledge keys: {list(result['knowledge'].keys())}")
            
            # Save knowledge to Supabase
            try:
                saved_knowledge = supabase_service.save_user_knowledge(
                    current_user["tenant_id"],
                    current_user["user_id"],
                    result["knowledge"]
                )
                logger.info(f"💾 Knowledge saved to Supabase: {saved_knowledge['id']}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save knowledge to Supabase: {e}")
            
            return {
                "success": True,
                "message": "Knowledge extracted successfully",
                "knowledge": result["knowledge"]
            }
        else:
            logger.error(f"❌ Knowledge extraction failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to extract knowledge"))
            
    except Exception as e:
        logger.error(f"💥 Knowledge extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-your-team/save-knowledge")
async def save_extracted_knowledge(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save extracted knowledge to user's profile"""
    try:
        knowledge = request.get("knowledge")
        if not knowledge:
            raise HTTPException(status_code=400, detail="No knowledge data provided")
        
        logger.info(f"💾 Saving knowledge for user: {current_user['user_id']}")
        
        # Save knowledge to Supabase
        saved_knowledge = supabase_service.save_user_knowledge(
            current_user["tenant_id"],
            current_user["user_id"],
            knowledge
        )
        
        logger.info(f"✅ Knowledge saved successfully: {saved_knowledge['id']}")
        
        return {
            "success": True,
            "message": "Knowledge saved successfully. Your AI agents are now trained!",
            "knowledge_id": saved_knowledge["id"]
        }
        
    except Exception as e:
        logger.error(f"💥 Save knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/train-your-team/get-knowledge")
async def get_user_knowledge(
    current_user: dict = Depends(get_current_user)
):
    """Get user's stored knowledge"""
    try:
        logger.info(f"📖 Getting knowledge for user: {current_user['user_id']}")
        
        # Use KnowledgeService to get normalized knowledge
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        
        normalized_knowledge = knowledge_service.get_user_knowledge(
            current_user["tenant_id"],
            current_user["user_id"]
        )
        
        return {
            "success": True,
            "message": "Knowledge retrieved successfully",
            "knowledge": normalized_knowledge
        }
        
    except Exception as e:
        logger.error(f"💥 Get knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Agent endpoints
@app.post("/prospector/generate-leads")
async def generate_leads_with_prospector(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Generate leads using the Prospector Agent with Phase 3 adaptive intelligence"""
    try:
        prompt = request.get("prompt", "")
        use_adaptive = request.get("use_adaptive", True)  # Default to adaptive mode
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🔍 Prospector request: {prompt} (adaptive: {use_adaptive})")
        
        # Import the prospector agent
        from agents.prospector_agent import ProspectorAgent
        
        # Initialize and run the prospector agent
        agent = ProspectorAgent()
        result = agent.prospect_leads(
            prompt, 
            tenant_id=current_user["tenant_id"], 
            user_id=current_user["user_id"],
            use_adaptive=use_adaptive
        )
        
        if result["success"]:
            response_data = {
                "success": True,
                "message": f"Generated {result['lead_count']} leads",
                "leads": result["leads"],
                "criteria": result["criteria"],
                "csv_content": result.get("csv_content", ""),
                "csv_filename": result.get("csv_filename", "")
            }
            
            # Add Phase 3 specific data if available
            if use_adaptive and "strategy_used" in result:
                response_data.update({
                    "strategy_used": result["strategy_used"],
                    "knowledge_level": result["knowledge_level"],
                    "confidence_score": result["confidence_score"],
                    "market_intelligence": result.get("market_intelligence", {}),
                    "adaptive_metadata": result.get("adaptive_metadata", {})
                })
            
            return response_data
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate leads"))
            
    except Exception as e:
        logger.error(f"Prospector agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-campaign/execute")
async def execute_smart_campaign(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Execute Smart Campaign with Phase 3 adaptive intelligence"""
    try:
        prompt = request.get("prompt", "")
        use_adaptive = request.get("use_adaptive", True)  # Default to adaptive mode
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🚀 Smart Campaign request: {prompt} (adaptive: {use_adaptive})")
        
        # Import the smart campaign orchestrator
        from agents.smart_campaign_orchestrator import SmartCampaignOrchestrator
        
        # Initialize and run the smart campaign orchestrator
        orchestrator = SmartCampaignOrchestrator()
        
        if use_adaptive:
            # Use Phase 3 adaptive campaign execution
            result = orchestrator.execute_adaptive_campaign(
                prompt,
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"]
            )
        else:
            # Use standard campaign execution
            result = orchestrator.execute_smart_campaign(
                prompt,
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"]
            )
        
        if result["success"]:
            response_data = {
                "success": True,
                "message": "Smart campaign executed successfully",
                "pipeline_id": result.get("pipeline_id", "adaptive_pipeline"),
                "stages": result.get("stages", []),
                "final_results": result.get("final_results", result.get("campaign_results", {})),
                "execution_time": result.get("execution_time", 0)
            }
            
            # Add Phase 3 specific data if available
            if use_adaptive and "strategy_used" in result:
                response_data.update({
                    "strategy_used": result["strategy_used"],
                    "knowledge_level": result["knowledge_level"],
                    "confidence_score": result["confidence_score"],
                    "market_intelligence": result.get("market_intelligence", {}),
                    "adaptive_metadata": result.get("adaptive_metadata", {})
                })
            
            return response_data
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to execute smart campaign"))
            
    except Exception as e:
        logger.error(f"Smart Campaign error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-campaign/save-campaign")
async def save_smart_campaign(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save Smart Campaign results as a campaign with leads"""
    try:
        campaign_data = request.get("campaign_data", {})
        premium_leads = request.get("premium_leads", [])
        backup_leads = request.get("backup_leads", [])
        
        logger.info(f"💾 Saving Smart Campaign: {campaign_data.get('name', 'Untitled')}")
        
        # Create campaign (store extra data in settings JSONB)
        campaign = supabase_service.client.table('campaigns').insert({
            'tenant_id': current_user['tenant_id'],
            'user_id': current_user['user_id'],
            'name': campaign_data.get('name', 'Smart Campaign'),
            'description': campaign_data.get('description', ''),
            'status': 'active',
            'settings': {
                'target_audience': campaign_data.get('target_audience', ''),
                'value_proposition': campaign_data.get('value_proposition', ''),
                'call_to_action': campaign_data.get('call_to_action', ''),
                'campaign_type': 'smart_campaign'
            }
        }).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=500, detail="Failed to create campaign")
        
        campaign_id = campaign.data[0]['id']
        logger.info(f"✅ Created campaign {campaign_id}")
        
        # Save all leads
        all_leads = premium_leads + backup_leads
        leads_to_insert = []
        
        for lead in all_leads:
            leads_to_insert.append({
                'tenant_id': current_user['tenant_id'],
                'campaign_id': campaign_id,
                'name': lead.get('name', ''),
                'company': lead.get('company', ''),
                'title': lead.get('title', ''),
                'email': lead.get('email'),
                'phone': lead.get('phone'),
                'linkedin_url': lead.get('linkedin_url'),
                'industry': lead.get('industry'),
                'company_size': lead.get('company_size'),
                'location': lead.get('location'),
                'status': 'new',
                'grade': lead.get('grade', 'B'),
                'score': lead.get('score', 0),
                'enrichment_status': lead.get('enrichment_status', 'enriched')
            })
        
        if leads_to_insert:
            leads_result = supabase_service.client.table('leads').insert(leads_to_insert).execute()
            logger.info(f"✅ Saved {len(leads_to_insert)} leads")
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "id": campaign_id,
            "name": campaign_data.get('name'),
            "leads_count": len(all_leads),
            "leads": all_leads,
            "message": f"Campaign saved with {len(all_leads)} leads"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error saving Smart Campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copywriter/personalize-message")
async def personalize_message(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Generate a personalized message using Copywriter Agent with Phase 3 adaptive intelligence"""
    try:
        lead_data = request.get("lead_data", {})
        message_type = request.get("message_type", "cold_email")
        campaign_context = request.get("campaign_context", {})
        user_template = request.get("user_template", None)
        use_adaptive = request.get("use_adaptive", True)  # Default to adaptive mode
        
        if not lead_data:
            raise HTTPException(status_code=400, detail="Lead data is required")
        
        logger.info(f"✍️ Personalizing {message_type} for {lead_data.get('name', 'Unknown')} (adaptive: {use_adaptive})")
        
        # Import the copywriter agent
        from agents.copywriter_agent import CopywriterAgent
        
        # Initialize and run the copywriter agent
        agent = CopywriterAgent()
        
        if use_adaptive:
            # Use Phase 3 adaptive copywriting
            result = agent.execute_adaptive(
                prompt=f"Personalize {message_type} for {lead_data.get('name', 'lead')}",
                lead_data=lead_data,
                message_type=message_type,
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"]
            )
        else:
            # Use standard personalization
            result = agent.personalize_message(
                lead_data, 
                message_type, 
                campaign_context, 
                user_template,
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"]
            )
        
        if result["success"]:
            response_data = {
                "success": True,
                "message": "Message personalized successfully",
                "personalized_message": result.get("personalized_message", result.get("message", "")),
                "lead_context": result.get("lead_context", {}),
                "industry_context": result.get("industry_context", {}),
                "personalization_score": result.get("personalization_score", 0.0),
                "message_length": result.get("message_length", 0),
                "generated_at": result.get("generated_at", datetime.now().isoformat())
            }
            
            # Add Phase 3 specific data if available
            if use_adaptive and "strategy_used" in result:
                response_data.update({
                    "strategy_used": result["strategy_used"],
                    "knowledge_level": result["knowledge_level"],
                    "confidence_score": result["confidence_score"],
                    "market_awareness_score": result.get("market_awareness_score", 0.0),
                    "adaptive_metadata": result.get("adaptive_metadata", {})
                })
            
            return response_data
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to personalize message"))
            
    except Exception as e:
        logger.error(f"Copywriter agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-outreach/create-plan")
async def create_smart_outreach_plan(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a smart outreach plan using SmartOutreachAgent with company knowledge"""
    try:
        leads = request.get("leads", [])
        campaign_context = request.get("campaign_context", {})
        
        if not leads:
            raise HTTPException(status_code=400, detail="Leads data is required")
        
        logger.info(f"📧 Creating smart outreach plan for {len(leads)} leads")
        
        # Import the smart outreach agent
        from agents.smart_outreach_agent import SmartOutreachAgent
        
        # Initialize and run the smart outreach agent with company knowledge
        agent = SmartOutreachAgent()
        result = agent.create_smart_outreach_plan(
            leads,
            campaign_context,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"]
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Smart outreach plan created successfully",
                "outreach_plan": result["outreach_plan"],
                "created_at": result["created_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create outreach plan"))
            
    except Exception as e:
        logger.error(f"Smart Outreach agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-outreach/execute")
async def execute_smart_outreach(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Execute smart outreach campaign - send actual emails via Gmail API"""
    try:
        outreach_plan = request.get("outreach_plan", {})
        campaign_id = request.get("campaign_id")
        
        if not outreach_plan:
            raise HTTPException(status_code=400, detail="Outreach plan is required")
        
        logger.info(f"🚀 Executing smart outreach for campaign {campaign_id}")
        
        # Get user's Google OAuth tokens from Supabase
        google_tokens = supabase_service.get_google_tokens(
            current_user["tenant_id"],
            current_user["user_id"]
        )
        
        if not google_tokens or not google_tokens.get("access_token"):
            raise HTTPException(
                status_code=401,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize Google OAuth service
        google_service = GoogleOAuthService()
        
        # Check if token needs refresh
        access_token = google_tokens["access_token"]
        expires_at = google_tokens.get("expires_at")
        if expires_at:
            from dateutil import parser
            from datetime import timezone
            expiry = parser.parse(expires_at)
            now = datetime.now(timezone.utc)
            # Make expiry timezone-aware if it's not
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry <= now:
                # Token expired, refresh it
                logger.info("Access token expired, refreshing...")
                refresh_result = google_service.refresh_access_token(google_tokens["refresh_token"])
                access_token = refresh_result["access_token"]
                
                # Update tokens in database
                supabase_service.save_google_tokens(
                    current_user["tenant_id"],
                    current_user["user_id"],
                    refresh_result
                )
        
        # Import the smart outreach agent
        from agents.smart_outreach_agent import SmartOutreachAgent
        
        # Execute outreach with real email sending
        agent = SmartOutreachAgent()
        execution_results = {
            "messages_sent": 0,
            "channels_used": {},
            "errors": [],
            "lead_updates": []
        }
        
        schedule = outreach_plan.get("schedule", [])
        
        for scheduled_outreach in schedule:
            try:
                lead = scheduled_outreach["lead"]
                channel = scheduled_outreach["channel"]
                
                # Generate personalized message
                message_result = agent._generate_smart_message(
                    lead,
                    channel,
                    scheduled_outreach["analysis"]
                )
                
                if not message_result["success"]:
                    execution_results["errors"].append({
                        "lead": lead.get("name"),
                        "error": message_result.get("error")
                    })
                    continue
                
                message = message_result["message"]
                
                # Send via appropriate channel
                send_result = None
                if channel == "email" and lead.get("email"):
                    # Send via Gmail API
                    send_result = google_service.send_email_via_gmail(
                        access_token=access_token,
                        to_email=lead["email"],
                        subject=message.get("subject", ""),
                        body=message.get("body", "")
                    )
                elif channel == "linkedin":
                    # LinkedIn sending not implemented yet
                    send_result = {
                        "success": False,
                        "error": "LinkedIn integration coming soon"
                    }
                elif channel == "phone":
                    # Phone calling not implemented yet
                    send_result = {
                        "success": False,
                        "error": "Phone integration coming soon"
                    }
                
                if send_result and send_result["success"]:
                    execution_results["messages_sent"] += 1
                    if channel not in execution_results["channels_used"]:
                        execution_results["channels_used"][channel] = 0
                    execution_results["channels_used"][channel] += 1
                    
                    # Update lead status in database
                    if campaign_id:
                        lead_update_result = supabase_service.client.table("leads").update({
                            "status": "contacted",
                            "data": {
                                **lead.get("data", {}),
                                "last_contact": datetime.now().isoformat(),
                                "last_contact_channel": channel,
                                "message_id": send_result.get("message_id")
                            },
                            "updated_at": datetime.now().isoformat()
                        }).eq("campaign_id", campaign_id).eq("email", lead.get("email")).execute()
                        
                        execution_results["lead_updates"].append({
                            "lead": lead.get("name"),
                            "status": "contacted",
                            "channel": channel
                        })
                else:
                    error_msg = send_result.get("error") if send_result else "Unknown error"
                    execution_results["errors"].append({
                        "lead": lead.get("name"),
                        "channel": channel,
                        "error": error_msg
                    })
                    
            except Exception as e:
                logger.error(f"Error processing lead {scheduled_outreach.get('lead', {}).get('name')}: {e}")
                execution_results["errors"].append({
                    "lead": scheduled_outreach.get("lead", {}).get("name"),
                    "error": str(e)
                })
        
        # Update campaign results
        if campaign_id:
            try:
                supabase_service.client.table("campaigns").update({
                    "results": {
                        "outreach_executed": True,
                        "messages_sent": execution_results["messages_sent"],
                        "channels_used": execution_results["channels_used"],
                        "execution_date": datetime.now().isoformat(),
                        "errors_count": len(execution_results["errors"])
                    },
                    "updated_at": datetime.now().isoformat()
                }).eq("id", campaign_id).execute()
            except Exception as e:
                logger.error(f"Failed to update campaign results: {e}")
        
        return {
            "success": True,
            "message": f"Successfully sent {execution_results['messages_sent']} messages",
            "execution_results": execution_results,
            "completed_at": datetime.now().isoformat()
        }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Smart Outreach execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================
# KNOWLEDGE BANK MANAGEMENT
# ==============================================

@app.get("/knowledge-bank/documents")
async def get_knowledge_bank_documents(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get all training documents for the knowledge bank"""
    try:
        logger.info(f"📚 Fetching documents for user {current_user['user_id']}")
        
        # Get documents from Supabase
        result = supabase_service.client.table("training_documents").select("*").eq(
            "tenant_id", current_user["tenant_id"]
        ).eq("user_id", current_user["user_id"]).order("created_at", desc=True).execute()
        
        documents = result.data if result.data else []
        logger.info(f"✅ Found {len(documents)} documents")
        
        return {"success": True, "documents": documents}
        
    except Exception as e:
        logger.error(f"❌ Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-bank/knowledge")
async def get_knowledge_bank_knowledge(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get all extracted knowledge for the knowledge bank"""
    try:
        logger.info(f"🧠 Fetching knowledge for user {current_user['user_id']}")
        
        # Get knowledge from Supabase
        result = supabase_service.client.table("user_knowledge").select("*").eq(
            "tenant_id", current_user["tenant_id"]
        ).eq("user_id", current_user["user_id"]).order("created_at", desc=True).execute()
        
        knowledge = result.data if result.data else []
        logger.info(f"✅ Found {len(knowledge)} knowledge items")
        
        return {"success": True, "knowledge": knowledge}
        
    except Exception as e:
        logger.error(f"❌ Error fetching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/knowledge-bank/documents/{document_id}")
async def delete_knowledge_bank_document(
    document_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document from the knowledge bank"""
    try:
        logger.info(f"🗑️ Deleting document {document_id} for user {current_user['user_id']}")
        
        # First, get the document to check ownership and get file path
        doc_result = supabase_service.client.table("training_documents").select("*").eq(
            "id", document_id
        ).eq("tenant_id", current_user["tenant_id"]).eq("user_id", current_user["user_id"]).execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_result.data[0]
        
        # Delete the physical file if it exists
        try:
            file_path = Path(document["file_path"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Deleted physical file: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete physical file: {e}")
        
        # Delete associated knowledge entries
        try:
            supabase_service.client.table("user_knowledge").delete().eq(
                "source_id", document_id
            ).execute()
            logger.info(f"🗑️ Deleted associated knowledge entries")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete associated knowledge: {e}")
        
        # Delete the document record
        result = supabase_service.client.table("training_documents").delete().eq(
            "id", document_id
        ).eq("tenant_id", current_user["tenant_id"]).eq("user_id", current_user["user_id"]).execute()
        
        logger.info(f"✅ Document {document_id} deleted successfully")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/knowledge-bank/knowledge/{knowledge_id}")
async def delete_knowledge_bank_knowledge(
    knowledge_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete a knowledge item from the knowledge bank"""
    try:
        logger.info(f"🗑️ Deleting knowledge {knowledge_id} for user {current_user['user_id']}")
        
        # Delete the knowledge record
        result = supabase_service.client.table("user_knowledge").delete().eq(
            "id", knowledge_id
        ).eq("tenant_id", current_user["tenant_id"]).eq("user_id", current_user["user_id"]).execute()
        
        # Check if deletion was successful (Supabase returns empty array for successful deletes)
        if result.data is None or (isinstance(result.data, list) and len(result.data) == 0):
            logger.info(f"✅ Knowledge {knowledge_id} deleted successfully")
            return {"success": True, "message": "Knowledge item deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================
# PHASE 3: ADAPTIVE AI & MARKET INTELLIGENCE
# ==============================================

@app.get("/phase3/knowledge-assessment")
async def get_knowledge_assessment(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive knowledge assessment for the user"""
    try:
        logger.info(f"🧠 Getting knowledge assessment for user {current_user['user_id']}")
        
        from agents.adaptive_ai_agent import AdaptiveAIAgent
        
        adaptive_agent = AdaptiveAIAgent()
        
        # Get a sample prompt for assessment (could be from user's recent campaigns)
        sample_prompt = "Generate leads for our SaaS product targeting CTOs in mid-market companies"
        
        assessment = adaptive_agent.assess_knowledge_level(
            current_user["tenant_id"], 
            current_user["user_id"], 
            sample_prompt
        )
        
        return {
            "success": True,
            "assessment": {
                "level": assessment.level.value,
                "document_count": assessment.document_count,
                "prompt_quality_score": assessment.prompt_quality_score,
                "overall_confidence": assessment.overall_confidence,
                "available_sources": assessment.available_sources,
                "gaps": assessment.gaps
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting knowledge assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/phase3/market-intelligence/{industry}")
async def get_market_intelligence(
    industry: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get market intelligence for a specific industry"""
    try:
        logger.info(f"📊 Getting market intelligence for industry: {industry}")
        
        from integrations.grok_service import GrokService
        
        grok_service = GrokService()
        
        # Get comprehensive market intelligence
        market_sentiment = grok_service.get_market_sentiment(industry)
        industry_trends = grok_service.get_industry_trends(industry)
        competitive_intelligence = grok_service.get_competitive_intelligence(industry)
        
        return {
            "success": True,
            "industry": industry,
            "market_sentiment": market_sentiment,
            "industry_trends": industry_trends,
            "competitive_intelligence": competitive_intelligence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting market intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/phase3/adaptive-strategy")
async def get_adaptive_strategy(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Get recommended adaptive strategy for a specific task"""
    try:
        task_type = request.get("task_type", "campaign_orchestration")
        prompt = request.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🎯 Getting adaptive strategy for task: {task_type}")
        
        from agents.adaptive_ai_agent import AdaptiveAIAgent
        
        adaptive_agent = AdaptiveAIAgent()
        
        # Assess knowledge level
        assessment = adaptive_agent.assess_knowledge_level(
            current_user["tenant_id"], 
            current_user["user_id"], 
            prompt
        )
        
        # Select adaptation strategy
        strategy_plan = adaptive_agent.select_adaptation_strategy(assessment.level, task_type)
        
        return {
            "success": True,
            "assessment": {
                "level": assessment.level.value,
                "document_count": assessment.document_count,
                "prompt_quality_score": assessment.prompt_quality_score,
                "overall_confidence": assessment.overall_confidence,
                "available_sources": assessment.available_sources,
                "gaps": assessment.gaps
            },
            "strategy_plan": {
                "strategy": strategy_plan.strategy.value,
                "confidence_threshold": strategy_plan.confidence_threshold,
                "fallback_strategies": [s.value for s in strategy_plan.fallback_strategies],
                "required_services": strategy_plan.required_services,
                "execution_priority": strategy_plan.execution_priority
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting adaptive strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/phase3/llm-recommendation")
async def get_llm_recommendation(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Get LLM model recommendation for a specific task"""
    try:
        task_type = request.get("task_type", "general")
        prompt_length = request.get("prompt_length", 0)
        preferences = request.get("preferences", {})
        
        logger.info(f"🤖 Getting LLM recommendation for task: {task_type}")
        
        from services.llm_selector_service import LLMSelectorService
        
        llm_selector = LLMSelectorService()
        
        recommendation = llm_selector.recommend_model_for_task(
            task_type, 
            prompt_length, 
            preferences
        )
        
        return {
            "success": True,
            "recommendation": recommendation,
            "task_type": task_type,
            "prompt_length": prompt_length,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting LLM recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/phase3/knowledge-fusion")
async def fuse_knowledge_sources(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Fuse knowledge from multiple sources"""
    try:
        document_knowledge = request.get("document_knowledge", {})
        prompt_knowledge = request.get("prompt_knowledge", {})
        market_knowledge = request.get("market_knowledge", {})
        
        logger.info(f"🔗 Fusing knowledge sources for user {current_user['user_id']}")
        
        from services.knowledge_fusion_service import KnowledgeFusionService
        
        fusion_service = KnowledgeFusionService()
        
        fused_knowledge = fusion_service.fuse_knowledge(
            document_knowledge,
            prompt_knowledge,
            market_knowledge
        )
        
        return {
            "success": True,
            "fused_knowledge": fused_knowledge,
            "sources_used": {
                "document": bool(document_knowledge),
                "prompt": bool(prompt_knowledge),
                "market": bool(market_knowledge)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error fusing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/phase3/market-monitoring/{industry}")
async def get_market_monitoring(
    industry: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time market monitoring data"""
    try:
        logger.info(f"📈 Getting market monitoring for industry: {industry}")
        
        from services.market_monitoring_service import MarketMonitoringService
        
        monitoring_service = MarketMonitoringService()
        
        # Get comprehensive market monitoring data
        trends = monitoring_service.get_real_time_market_trends(industry)
        opportunities = monitoring_service.detect_market_opportunities(industry)
        alerts = monitoring_service.get_market_alerts(industry)
        
        return {
            "success": True,
            "industry": industry,
            "trends": trends,
            "opportunities": opportunities,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting market monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/phase3/predictive-analytics")
async def get_predictive_analytics(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Get predictive analytics for campaign optimization"""
    try:
        campaign_data = request.get("campaign_data", {})
        lead_data = request.get("lead_data", [])
        
        logger.info(f"🔮 Getting predictive analytics for user {current_user['user_id']}")
        
        from services.predictive_analytics_service import PredictiveAnalyticsService
        
        analytics_service = PredictiveAnalyticsService()
        
        # Get comprehensive predictive analytics
        campaign_prediction = analytics_service.predict_campaign_performance(campaign_data, lead_data)
        targeting_optimization = analytics_service.optimize_targeting(lead_data)
        timing_recommendation = analytics_service.recommend_optimal_timing(lead_data)
        
        return {
            "success": True,
            "campaign_prediction": campaign_prediction,
            "targeting_optimization": targeting_optimization,
            "timing_recommendation": timing_recommendation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting predictive analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================
# CAMPAIGN INTELLIGENCE ENDPOINTS
# ==============================================

@app.get("/campaign-intelligence/suggestions")
async def get_campaign_suggestions(
    current_user: dict = Depends(get_current_user)
):
    """Get smart campaign suggestions based on uploaded documents"""
    try:
        logger.info(f"🧠 Getting campaign suggestions for user {current_user['user_id']}")
        
        from services.campaign_intelligence_service import CampaignIntelligenceService
        
        intelligence_service = CampaignIntelligenceService()
        
        # Check for cached suggestions first
        cached_suggestions = intelligence_service.get_cached_suggestions(
            current_user["tenant_id"], 
            current_user["user_id"]
        )
        
        if cached_suggestions:
            logger.info("Returning cached suggestions")
            return {
                "success": True,
                "suggestions": cached_suggestions,
                "cached": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate new suggestions
        insights = intelligence_service.analyze_documents_for_campaigns(
            current_user["tenant_id"], 
            current_user["user_id"]
        )
        
        suggestions = insights.get("suggested_campaigns", [])
        
        return {
            "success": True,
            "suggestions": suggestions,
            "insights": {
                "target_audience": insights.get("target_audience", {}),
                "industry_focus": insights.get("industry_focus", "Technology"),
                "product_categories": insights.get("product_categories", []),
                "document_count": insights.get("document_count", 0)
            },
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting campaign suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaign-intelligence/generate")
async def generate_campaign_suggestions(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Force regenerate campaign suggestions (after new document upload)"""
    try:
        logger.info(f"🔄 Regenerating campaign suggestions for user {current_user['user_id']}")
        
        from services.campaign_intelligence_service import CampaignIntelligenceService
        
        intelligence_service = CampaignIntelligenceService()
        
        # Force generate new suggestions
        insights = intelligence_service.analyze_documents_for_campaigns(
            current_user["tenant_id"], 
            current_user["user_id"]
        )
        
        suggestions = insights.get("suggested_campaigns", [])
        
        return {
            "success": True,
            "suggestions": suggestions,
            "insights": {
                "target_audience": insights.get("target_audience", {}),
                "industry_focus": insights.get("industry_focus", "Technology"),
                "product_categories": insights.get("product_categories", []),
                "document_count": insights.get("document_count", 0)
            },
            "regenerated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error regenerating campaign suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaign-intelligence/record-execution")
async def record_campaign_execution(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Record campaign execution for learning"""
    try:
        prompt_data = request.get("prompt_data", {})
        results = request.get("results", {})
        
        logger.info(f"📊 Recording campaign execution for user {current_user['user_id']}")
        
        from services.campaign_learning_service import CampaignLearningService
        
        learning_service = CampaignLearningService()
        
        execution_record = learning_service.record_campaign_execution(
            current_user["tenant_id"],
            current_user["user_id"],
            prompt_data,
            results
        )
        
        return {
            "success": True,
            "execution_record": execution_record,
            "message": "Campaign execution recorded for learning",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error recording campaign execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaign-intelligence/insights")
async def get_campaign_insights(
    current_user: dict = Depends(get_current_user)
):
    """Get analysis insights about uploaded documents"""
    try:
        logger.info(f"🔍 Getting campaign insights for user {current_user['user_id']}")
        
        from services.campaign_intelligence_service import CampaignIntelligenceService
        
        intelligence_service = CampaignIntelligenceService()
        
        insights = intelligence_service.analyze_documents_for_campaigns(
            current_user["tenant_id"], 
            current_user["user_id"]
        )
        
        return {
            "success": True,
            "insights": {
                "target_audience": insights.get("target_audience", {}),
                "industry_focus": insights.get("industry_focus", "Technology"),
                "product_categories": insights.get("product_categories", []),
                "sales_approach": insights.get("sales_approach", ""),
                "competitive_positioning": insights.get("competitive_positioning", []),
                "document_count": insights.get("document_count", 0),
                "analysis_timestamp": insights.get("analysis_timestamp")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting campaign insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================
# PHASE 2: ANALYTICS & PERFORMANCE TRACKING
# ==============================================

class AnalyticsTimeSeriesResponse(BaseModel):
    date: str
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    leads_contacted: int
    leads_responded: int
    open_rate: float
    reply_rate: float

class ActivityItem(BaseModel):
    id: str
    activity_type: str
    title: str
    description: Optional[str] = None
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    timestamp: str

class FunnelStats(BaseModel):
    stage: str
    count: int
    percentage: float
    conversion_rate: Optional[float] = None

class CampaignAnalyticsResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    time_series: List[AnalyticsTimeSeriesResponse]
    total_emails_sent: int
    total_emails_opened: int
    total_emails_replied: int
    avg_open_rate: float
    avg_reply_rate: float
    best_day: Optional[str] = None
    engagement_trend: str  # "improving", "declining", "stable"

@app.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get time-series analytics for a campaign"""
    try:
        logger.info(f"📊 Getting analytics for campaign {campaign_id}")
        
        # Get campaign
        campaign_result = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_result.data[0]
        
        # Build query for analytics data
        query = supabase_service.client.table('campaign_analytics').select('*').eq('campaign_id', campaign_id)
        
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)
        
        analytics_result = query.order('date', desc=False).execute()
        
        # If no analytics data exists yet, create sample data structure
        if not analytics_result.data:
            logger.info(f"No analytics data found for campaign {campaign_id}, returning empty structure")
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign['name'],
                "time_series": [],
                "total_emails_sent": 0,
                "total_emails_opened": 0,
                "total_emails_replied": 0,
                "avg_open_rate": 0.0,
                "avg_reply_rate": 0.0,
                "best_day": None,
                "engagement_trend": "stable"
            }
        
        # Process time series data
        time_series = []
        total_sent = 0
        total_opened = 0
        total_replied = 0
        
        for row in analytics_result.data:
            time_series.append({
                "date": row['date'],
                "emails_sent": row.get('emails_sent', 0),
                "emails_opened": row.get('emails_opened', 0),
                "emails_clicked": row.get('emails_clicked', 0),
                "emails_replied": row.get('emails_replied', 0),
                "leads_contacted": row.get('leads_contacted', 0),
                "leads_responded": row.get('leads_responded', 0),
                "open_rate": float(row.get('open_rate', 0)),
                "reply_rate": float(row.get('reply_rate', 0))
            })
            total_sent += row.get('emails_sent', 0)
            total_opened += row.get('emails_opened', 0)
            total_replied += row.get('emails_replied', 0)
        
        # Calculate averages
        avg_open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        avg_reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        # Find best performing day
        best_day = None
        if time_series:
            best_day_data = max(time_series, key=lambda x: x['reply_rate'])
            best_day = best_day_data['date']
        
        # Determine engagement trend (simple: compare first half vs second half)
        engagement_trend = "stable"
        if len(time_series) >= 4:
            mid_point = len(time_series) // 2
            first_half_avg = sum(x['reply_rate'] for x in time_series[:mid_point]) / mid_point
            second_half_avg = sum(x['reply_rate'] for x in time_series[mid_point:]) / (len(time_series) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                engagement_trend = "improving"
            elif second_half_avg < first_half_avg * 0.9:
                engagement_trend = "declining"
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign['name'],
            "time_series": time_series,
            "total_emails_sent": total_sent,
            "total_emails_opened": total_opened,
            "total_emails_replied": total_replied,
            "avg_open_rate": round(avg_open_rate, 2),
            "avg_reply_rate": round(avg_reply_rate, 2),
            "best_day": best_day,
            "engagement_trend": engagement_trend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/activity", response_model=List[ActivityItem])
async def get_campaign_activity(
    campaign_id: str,
    limit: int = 50,
    activity_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get activity timeline for a campaign"""
    try:
        logger.info(f"📋 Getting activity for campaign {campaign_id}")
        
        # Verify campaign exists and belongs to tenant
        campaign_result = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Build query
        query = supabase_service.client.table('campaign_activity').select(
            'id, activity_type, title, description, lead_id, created_at'
        ).eq('campaign_id', campaign_id)
        
        if activity_type:
            query = query.eq('activity_type', activity_type)
        
        activity_result = query.order('created_at', desc=True).limit(limit).execute()
        
        # Enrich with lead names
        activities = []
        for activity in activity_result.data:
            lead_name = None
            if activity.get('lead_id'):
                lead_result = supabase_service.client.table('leads').select('name').eq('id', activity['lead_id']).execute()
                if lead_result.data:
                    lead_name = lead_result.data[0]['name']
            
            activities.append({
                "id": activity['id'],
                "activity_type": activity['activity_type'],
                "title": activity['title'],
                "description": activity.get('description'),
                "lead_id": activity.get('lead_id'),
                "lead_name": lead_name,
                "timestamp": activity['created_at']
            })
        
        return activities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting campaign activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/funnel", response_model=List[FunnelStats])
async def get_campaign_funnel(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversion funnel statistics for a campaign"""
    try:
        logger.info(f"🔽 Getting funnel stats for campaign {campaign_id}")
        
        # Verify campaign exists
        campaign_result = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get lead counts by status
        leads_result = supabase_service.client.table('leads').select('status').eq('campaign_id', campaign_id).execute()
        
        if not leads_result.data:
            return []
        
        # Count leads by status
        total_leads = len(leads_result.data)
        status_counts = {}
        for lead in leads_result.data:
            status = lead.get('status', 'new')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Build funnel (ordered stages)
        funnel_stages = [
            ('new', 'New Leads'),
            ('contacted', 'Contacted'),
            ('responded', 'Responded'),
            ('qualified', 'Qualified')
        ]
        
        funnel_data = []
        previous_count = total_leads
        
        for status_key, stage_name in funnel_stages:
            count = status_counts.get(status_key, 0)
            percentage = (count / total_leads * 100) if total_leads > 0 else 0
            conversion_rate = (count / previous_count * 100) if previous_count > 0 else 0
            
            funnel_data.append({
                "stage": stage_name,
                "count": count,
                "percentage": round(percentage, 1),
                "conversion_rate": round(conversion_rate, 1) if status_key != 'new' else None
            })
            
            previous_count = count
        
        return funnel_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting campaign funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/engagement/track")
async def track_engagement_event(
    campaign_id: str,
    lead_id: str,
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Track an engagement event (email open, click, reply, etc.)"""
    try:
        logger.info(f"📈 Tracking {event_type} event for lead {lead_id}")
        
        # Verify lead exists and belongs to campaign
        lead_result = supabase_service.client.table('leads').select('*').eq('id', lead_id).eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Insert engagement event
        engagement_data = {
            "tenant_id": current_user['tenant_id'],
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "event_type": event_type,
            "event_data": event_data or {}
        }
        
        result = supabase_service.client.table('lead_engagement').insert(engagement_data).execute()
        
        # Update lead status based on event type
        if event_type == 'email_replied':
            supabase_service.client.table('leads').update({
                "status": "responded",
                "updated_at": datetime.now().isoformat()
            }).eq('id', lead_id).execute()
        
        # Log activity
        activity_titles = {
            'email_opened': f"Lead opened email",
            'email_clicked': f"Lead clicked link in email",
            'email_replied': f"Lead replied to email",
            'linkedin_viewed': f"Lead viewed LinkedIn profile",
            'linkedin_connected': f"Lead connected on LinkedIn",
            'meeting_scheduled': f"Meeting scheduled with lead"
        }
        
        if event_type in activity_titles:
            supabase_service.client.table('campaign_activity').insert({
                "tenant_id": current_user['tenant_id'],
                "campaign_id": campaign_id,
                "lead_id": lead_id,
                "activity_type": event_type,
                "title": activity_titles[event_type],
                "description": json.dumps(event_data) if event_data else None
            }).execute()
        
        return {
            "success": True,
            "event_id": result.data[0]['id'],
            "message": f"Engagement event tracked: {event_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error tracking engagement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/export")
async def export_campaign_data(
    campaign_id: str,
    format: str = "csv",  # csv or json
    include_analytics: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Export campaign data (leads, analytics, activity)"""
    try:
        logger.info(f"📥 Exporting campaign {campaign_id} data as {format}")
        
        # Verify campaign exists
        campaign_result = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_result.data[0]
        
        # Get leads
        leads_result = supabase_service.client.table('leads').select('*').eq('campaign_id', campaign_id).execute()
        
        export_data = {
            "campaign": {
                "id": campaign['id'],
                "name": campaign['name'],
                "description": campaign.get('description'),
                "status": campaign['status'],
                "created_at": campaign['created_at']
            },
            "leads": leads_result.data,
            "export_date": datetime.now().isoformat()
        }
        
        # Include analytics if requested
        if include_analytics:
            analytics_result = supabase_service.client.table('campaign_analytics').select('*').eq('campaign_id', campaign_id).execute()
            export_data['analytics'] = analytics_result.data
        
        if format == "csv":
            # Convert leads to CSV format
            import io
            import csv
            
            output = io.StringIO()
            if leads_result.data:
                fieldnames = ['name', 'email', 'company', 'title', 'status', 'score', 'created_at']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(leads_result.data)
            
            from fastapi.responses import StreamingResponse
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=campaign_{campaign['name'].replace(' ', '_')}_leads.csv"
                }
            )
        else:
            # Return JSON
            return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error exporting campaign data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/dashboard")
async def get_analytics_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get overall analytics dashboard for all campaigns"""
    try:
        logger.info(f"📊 Getting analytics dashboard for tenant {current_user['tenant_id']}")
        
        # Get all campaigns for tenant
        campaigns_result = supabase_service.client.table('campaigns').select('id, name, status, created_at').eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaigns_result.data:
            return {
                "total_campaigns": 0,
                "active_campaigns": 0,
                "total_leads": 0,
                "total_emails_sent": 0,
                "avg_reply_rate": 0,
                "top_campaigns": []
            }
        
        campaign_ids = [c['id'] for c in campaigns_result.data]
        
        # Get aggregated stats
        leads_result = supabase_service.client.table('leads').select('campaign_id, status').in_('campaign_id', campaign_ids).execute()
        
        total_leads = len(leads_result.data)
        responded_leads = len([l for l in leads_result.data if l['status'] == 'responded'])
        
        # Get email stats from analytics
        analytics_result = supabase_service.client.table('campaign_analytics').select('campaign_id, emails_sent, emails_replied').in_('campaign_id', campaign_ids).execute()
        
        total_emails = sum(a.get('emails_sent', 0) for a in analytics_result.data)
        total_replies = sum(a.get('emails_replied', 0) for a in analytics_result.data)
        avg_reply_rate = (total_replies / total_emails * 100) if total_emails > 0 else 0
        
        # Calculate top performing campaigns
        campaign_performance = {}
        for campaign in campaigns_result.data:
            campaign_leads = [l for l in leads_result.data if l['campaign_id'] == campaign['id']]
            campaign_responded = len([l for l in campaign_leads if l['status'] == 'responded'])
            reply_rate = (campaign_responded / len(campaign_leads) * 100) if campaign_leads else 0
            
            campaign_performance[campaign['id']] = {
                "id": campaign['id'],
                "name": campaign['name'],
                "reply_rate": reply_rate,
                "leads": len(campaign_leads),
                "responded": campaign_responded
            }
        
        # Sort by reply rate
        top_campaigns = sorted(campaign_performance.values(), key=lambda x: x['reply_rate'], reverse=True)[:5]
        
        return {
            "total_campaigns": len(campaigns_result.data),
            "active_campaigns": len([c for c in campaigns_result.data if c['status'] == 'active']),
            "total_leads": total_leads,
            "responded_leads": responded_leads,
            "total_emails_sent": total_emails,
            "total_replies": total_replies,
            "avg_reply_rate": round(avg_reply_rate, 2),
            "top_campaigns": top_campaigns
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================
# PHASE 3: MULTI-TOUCH SEQUENCES
# ==============================================

class SequenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}

class SequenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class SequenceResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: str
    steps_count: int
    total_enrolled: int
    total_completed: int
    total_stopped: int
    settings: Dict[str, Any]
    created_at: str
    updated_at: str

class SequenceStepCreate(BaseModel):
    step_order: int
    name: str
    step_type: str  # email, delay, condition, action
    subject_line: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    delay_days: Optional[int] = 0
    delay_hours: Optional[int] = 0
    send_time: Optional[str] = None
    business_hours_only: Optional[bool] = True
    condition_type: Optional[str] = None
    condition_config: Optional[Dict[str, Any]] = {}
    action_type: Optional[str] = None
    action_config: Optional[Dict[str, Any]] = {}

class SequenceStepResponse(BaseModel):
    id: str
    sequence_id: str
    step_order: int
    name: str
    step_type: str
    subject_line: Optional[str] = None
    body_text: Optional[str] = None
    delay_days: Optional[int] = 0
    delay_hours: Optional[int] = 0
    condition_type: Optional[str] = None
    action_type: Optional[str] = None
    created_at: str

@app.post("/sequences", response_model=SequenceResponse)
async def create_sequence(
    sequence: SequenceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new email sequence"""
    try:
        logger.info(f"📧 Creating sequence: {sequence.name}")
        
        sequence_data = {
            "tenant_id": current_user['tenant_id'],
            "user_id": current_user['user_id'],
            "name": sequence.name,
            "description": sequence.description,
            "status": "draft",
            "settings": sequence.settings or {}
        }
        
        result = supabase_service.client.table('sequences').insert(sequence_data).execute()
        
        logger.info(f"✅ Sequence created: {result.data[0]['id']}")
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Error creating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sequences", response_model=List[SequenceResponse])
async def get_sequences(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all sequences for the tenant"""
    try:
        logger.info(f"📋 Getting sequences for tenant {current_user['tenant_id']}")
        
        query = supabase_service.client.table('sequences').select('*').eq('tenant_id', current_user['tenant_id'])
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).execute()
        
        logger.info(f"✅ Found {len(result.data)} sequences")
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Error getting sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sequences/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific sequence"""
    try:
        logger.info(f"🔍 Getting sequence: {sequence_id}")
        
        result = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        logger.info(f"✅ Sequence found: {result.data[0]['name']}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/sequences/{sequence_id}", response_model=SequenceResponse)
async def update_sequence(
    sequence_id: str,
    sequence: SequenceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a sequence"""
    try:
        logger.info(f"✏️ Updating sequence: {sequence_id}")
        
        # Verify sequence exists and belongs to tenant
        existing = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Build update data
        update_data = {}
        if sequence.name is not None:
            update_data['name'] = sequence.name
        if sequence.description is not None:
            update_data['description'] = sequence.description
        if sequence.status is not None:
            update_data['status'] = sequence.status
        if sequence.settings is not None:
            update_data['settings'] = sequence.settings
        
        if not update_data:
            return existing.data[0]
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = supabase_service.client.table('sequences').update(update_data).eq('id', sequence_id).execute()
        
        logger.info(f"✅ Sequence updated")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sequences/{sequence_id}")
async def delete_sequence(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a sequence"""
    try:
        logger.info(f"🗑️ Deleting sequence: {sequence_id}")
        
        # Verify sequence exists and belongs to tenant
        existing = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Check if sequence is active
        if existing.data[0]['status'] == 'active':
            raise HTTPException(status_code=400, detail="Cannot delete active sequence. Pause it first.")
        
        # Delete sequence (cascade will delete steps and states)
        supabase_service.client.table('sequences').delete().eq('id', sequence_id).execute()
        
        logger.info(f"✅ Sequence deleted")
        return {"success": True, "message": "Sequence deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sequences/{sequence_id}/duplicate", response_model=SequenceResponse)
async def duplicate_sequence(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Duplicate a sequence with all its steps"""
    try:
        logger.info(f"📋 Duplicating sequence: {sequence_id}")
        
        # Get original sequence
        original = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not original.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        orig_data = original.data[0]
        
        # Create new sequence
        new_sequence_data = {
            "tenant_id": current_user['tenant_id'],
            "user_id": current_user['user_id'],
            "name": f"{orig_data['name']} (Copy)",
            "description": orig_data.get('description'),
            "status": "draft",
            "settings": orig_data.get('settings', {})
        }
        
        new_sequence = supabase_service.client.table('sequences').insert(new_sequence_data).execute()
        new_sequence_id = new_sequence.data[0]['id']
        
        # Get and duplicate steps
        steps = supabase_service.client.table('sequence_steps').select('*').eq('sequence_id', sequence_id).order('step_order').execute()
        
        if steps.data:
            new_steps = []
            for step in steps.data:
                new_step = {
                    "tenant_id": current_user['tenant_id'],
                    "sequence_id": new_sequence_id,
                    "step_order": step['step_order'],
                    "name": step['name'],
                    "step_type": step['step_type'],
                    "subject_line": step.get('subject_line'),
                    "body_text": step.get('body_text'),
                    "body_html": step.get('body_html'),
                    "delay_days": step.get('delay_days', 0),
                    "delay_hours": step.get('delay_hours', 0),
                    "send_time": step.get('send_time'),
                    "business_hours_only": step.get('business_hours_only', True),
                    "condition_type": step.get('condition_type'),
                    "condition_config": step.get('condition_config', {}),
                    "action_type": step.get('action_type'),
                    "action_config": step.get('action_config', {})
                }
                new_steps.append(new_step)
            
            supabase_service.client.table('sequence_steps').insert(new_steps).execute()
        
        # Get the complete new sequence
        result = supabase_service.client.table('sequences').select('*').eq('id', new_sequence_id).execute()
        
        logger.info(f"✅ Sequence duplicated: {new_sequence_id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error duplicating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sequences/{sequence_id}/enrollments")
async def get_sequence_enrollments(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all enrollments for a sequence"""
    try:
        result = supabase_service.client.table('sequence_enrollments').select('*').eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Error getting enrollments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sequences/{sequence_id}/execution-stats")
async def get_sequence_execution_stats(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time execution statistics for a sequence"""
    try:
        # Get sequence info
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).single().execute()
        
        # Get enrollment stats
        enrollments = supabase_service.client.table('sequence_enrollments').select('id, status, current_step, exit_reason').eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        # Get step execution stats (last 20)
        executions = supabase_service.client.table('sequence_step_executions').select('*, sequence_steps(name, step_type)').eq('tenant_id', current_user['tenant_id']).order('executed_at', desc=True).limit(20).execute()
        
        logger.info(f"📊 Raw executions count: {len(executions.data)}")
        logger.info(f"📊 First execution sample: {executions.data[0] if executions.data else 'None'}")
        
        # Filter executions for this sequence by joining with enrollments
        enrollment_ids = [e['id'] for e in enrollments.data]
        sequence_executions = [e for e in executions.data if e.get('enrollment_id') in enrollment_ids]
        
        logger.info(f"📊 Filtered sequence_executions count: {len(sequence_executions)}")
        
        # Calculate stats
        total_enrolled = len(enrollments.data)
        active = len([e for e in enrollments.data if e['status'] == 'active'])
        scheduled = len([e for e in enrollments.data if e['status'] == 'scheduled'])
        completed = len([e for e in enrollments.data if e['status'] == 'completed'])
        failed = len([e for e in enrollments.data if e['status'] == 'failed'])
        
        # Calculate by step
        step_distribution = {}
        for e in enrollments.data:
            step = e.get('current_step', 0)
            step_distribution[step] = step_distribution.get(step, 0) + 1
        
        # Recent sends (last 20)
        recent_sends = []
        for exec in sequence_executions[:20]:
            recent_sends.append({
                'executed_at': exec.get('executed_at'),
                'status': exec.get('status'),
                'step_name': exec.get('sequence_steps', {}).get('name', 'Unknown'),
                'step_type': exec.get('sequence_steps', {}).get('step_type', 'unknown'),
                'email_sent': exec.get('email_sent', False),
                'error_message': exec.get('error_message')
            })
        
        return {
            'sequence': {
                'id': sequence.data['id'],
                'name': sequence.data['name'],
                'status': sequence.data['status'],
                'steps_count': sequence.data.get('steps_count', 0)
            },
            'stats': {
                'total_enrolled': total_enrolled,
                'active': active,
                'scheduled': scheduled,
                'completed': completed,
                'failed': failed,
                'step_distribution': step_distribution
            },
            'recent_activity': recent_sends,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting execution stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sequences/{sequence_id}/activate")
async def activate_sequence(
    sequence_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Activate a sequence with optional scheduling"""
    try:
        scheduled_start_at = request.get('scheduled_start_at')
        
        logger.info(f"🚀 Activating sequence: {sequence_id} (scheduled: {scheduled_start_at})")
        
        # Verify sequence exists and belongs to tenant
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Update sequence status to active
        update_data = {
            'status': 'active',
            'updated_at': datetime.now().isoformat()
        }
        
        if scheduled_start_at:
            update_data['scheduled_start_at'] = scheduled_start_at
        
        supabase_service.client.table('sequences').update(update_data).eq('id', sequence_id).execute()
        
        # Get all enrolled leads
        enrollments = supabase_service.client.table('sequence_enrollments').select('*').eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        # Update enrollments based on scheduling
        enrollment_count = 0
        for enrollment in enrollments.data:
            enrollment_update = {
                'current_step': 1
            }
            
            if scheduled_start_at:
                # Schedule for future
                enrollment_update['status'] = 'scheduled'
                enrollment_update['next_action_at'] = scheduled_start_at
                enrollment_update['scheduled_start_at'] = scheduled_start_at
            else:
                # Start immediately
                enrollment_update['status'] = 'active'
                enrollment_update['next_action_at'] = datetime.now().isoformat()
                enrollment_update['started_at'] = datetime.now().isoformat()
            
            supabase_service.client.table('sequence_enrollments').update(enrollment_update).eq('id', enrollment['id']).execute()
            enrollment_count += 1
        
        status_message = "scheduled" if scheduled_start_at else "activated"
        logger.info(f"✅ Sequence {status_message} with {enrollment_count} leads")
        
        return {
            "success": True,
            "message": f"Sequence {status_message} successfully",
            "sequence_id": sequence_id,
            "enrolled_leads": enrollment_count,
            "scheduled_start_at": scheduled_start_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error activating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sequence Steps Endpoints

@app.get("/sequences/{sequence_id}/steps", response_model=List[SequenceStepResponse])
async def get_sequence_steps(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all steps for a sequence"""
    try:
        logger.info(f"📋 Getting steps for sequence: {sequence_id}")
        
        # Verify sequence exists
        sequence = supabase_service.client.table('sequences').select('id').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Get steps
        result = supabase_service.client.table('sequence_steps').select('*').eq('sequence_id', sequence_id).order('step_order').execute()
        
        logger.info(f"✅ Found {len(result.data)} steps")
        
        # Convert to JSON-serializable format
        steps = []
        for step in result.data:
            steps.append({
                'id': str(step['id']),
                'sequence_id': str(step['sequence_id']),
                'step_order': step['step_order'],
                'name': step['name'],
                'step_type': step['step_type'],
                'subject_line': step.get('subject_line'),
                'body_text': step.get('body_text'),
                'delay_days': step.get('delay_days', 0),
                'delay_hours': step.get('delay_hours', 0),
                'condition_type': step.get('condition_type'),
                'action_type': step.get('action_type'),
                'created_at': str(step['created_at']) if step.get('created_at') else None
            })
        
        return steps
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting sequence steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sequences/{sequence_id}/steps", response_model=SequenceStepResponse)
async def create_sequence_step(
    sequence_id: str,
    step: SequenceStepCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a step to a sequence"""
    try:
        logger.info(f"➕ Adding step to sequence: {sequence_id}")
        
        # Verify sequence exists
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Cannot modify active sequences
        if sequence.data[0]['status'] == 'active':
            raise HTTPException(status_code=400, detail="Cannot modify active sequence. Pause it first.")
        
        step_data = {
            "tenant_id": current_user['tenant_id'],
            "sequence_id": sequence_id,
            "step_order": step.step_order,
            "name": step.name,
            "step_type": step.step_type,
            "subject_line": step.subject_line,
            "body_text": step.body_text,
            "body_html": step.body_html,
            "delay_days": step.delay_days,
            "delay_hours": step.delay_hours,
            "send_time": step.send_time,
            "business_hours_only": step.business_hours_only,
            "condition_type": step.condition_type,
            "condition_config": step.condition_config,
            "action_type": step.action_type,
            "action_config": step.action_config
        }
        
        result = supabase_service.client.table('sequence_steps').insert(step_data).execute()
        
        logger.info(f"✅ Step added: {result.data[0]['id']}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating sequence step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/sequences/{sequence_id}/steps/{step_id}", response_model=SequenceStepResponse)
async def update_sequence_step(
    sequence_id: str,
    step_id: str,
    step: SequenceStepCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update a sequence step"""
    try:
        logger.info(f"✏️ Updating step: {step_id}")
        
        # Verify sequence exists
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        if sequence.data[0]['status'] == 'active':
            raise HTTPException(status_code=400, detail="Cannot modify active sequence")
        
        # Update step
        update_data = {
            "name": step.name,
            "step_type": step.step_type,
            "subject_line": step.subject_line,
            "body_text": step.body_text,
            "body_html": step.body_html,
            "delay_days": step.delay_days,
            "delay_hours": step.delay_hours,
            "send_time": step.send_time,
            "business_hours_only": step.business_hours_only,
            "condition_type": step.condition_type,
            "condition_config": step.condition_config,
            "action_type": step.action_type,
            "action_config": step.action_config,
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase_service.client.table('sequence_steps').update(update_data).eq('id', step_id).eq('sequence_id', sequence_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Step not found")
        
        logger.info(f"✅ Step updated")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating sequence step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sequences/{sequence_id}/steps/{step_id}")
async def delete_sequence_step(
    sequence_id: str,
    step_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a sequence step"""
    try:
        logger.info(f"🗑️ Deleting step: {step_id}")
        
        # Verify sequence exists
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        if sequence.data[0]['status'] == 'active':
            raise HTTPException(status_code=400, detail="Cannot modify active sequence")
        
        # Delete step
        supabase_service.client.table('sequence_steps').delete().eq('id', step_id).eq('sequence_id', sequence_id).execute()
        
        logger.info(f"✅ Step deleted")
        return {"success": True, "message": "Step deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting sequence step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sequence Assignment & Enrollment

class EnrollLeadsRequest(BaseModel):
    lead_ids: List[str]
    sequence_id: str
    campaign_id: Optional[str] = None

@app.post("/campaigns/{campaign_id}/assign-sequence")
async def assign_sequence_to_campaign(
    campaign_id: str,
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign a sequence to a campaign and enroll all leads"""
    try:
        logger.info(f"🔗 Assigning sequence {sequence_id} to campaign {campaign_id}")
        
        # Verify campaign and sequence exist
        campaign = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        sequence = supabase_service.client.table('sequences').select('*').eq('id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Get all leads in campaign
        leads = supabase_service.client.table('leads').select('id').eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not leads.data:
            return {"success": True, "enrolled": 0, "message": "No leads to enroll"}
        
        # Enroll each lead
        enrolled_count = 0
        for lead in leads.data:
            try:
                # Call the database function to enroll lead
                result = supabase_service.client.rpc('enroll_lead_in_sequence', {
                    'p_tenant_id': current_user['tenant_id'],
                    'p_lead_id': lead['id'],
                    'p_campaign_id': campaign_id,
                    'p_sequence_id': sequence_id
                }).execute()
                
                enrolled_count += 1
            except Exception as e:
                logger.warning(f"Failed to enroll lead {lead['id']}: {e}")
        
        logger.info(f"✅ Enrolled {enrolled_count} leads in sequence")
        return {
            "success": True,
            "enrolled": enrolled_count,
            "total_leads": len(leads.data),
            "message": f"Enrolled {enrolled_count} leads in sequence"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error assigning sequence to campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/create-sequence")
async def create_sequence_from_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a pre-filled sequence from a campaign with template steps and auto-enrolled leads"""
    try:
        logger.info(f"🎯 Creating sequence from campaign {campaign_id}")
        
        # Get campaign details
        campaign = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = campaign.data[0]
        
        # Extract campaign settings
        settings = campaign_data.get('settings', {})
        target_audience = settings.get('target_audience', campaign_data.get('description', 'your industry'))
        value_proposition = settings.get('value_proposition', 'We help companies like yours achieve better results.')
        call_to_action = settings.get('call_to_action', 'Would you be open to a quick 15-minute call to discuss?')
        
        # Get campaign leads for context
        leads = supabase_service.client.table('leads').select('*').eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).limit(5).execute()
        
        # Create sequence
        sequence_name = f"{campaign_data['name']} - Follow-up Sequence"
        sequence_description = f"Automated multi-touch sequence for {campaign_data['name']} campaign"
        
        sequence = supabase_service.client.table('sequences').insert({
            'tenant_id': current_user['tenant_id'],
            'user_id': current_user['user_id'],
            'name': sequence_name,
            'description': sequence_description,
            'status': 'draft',
            'campaign_id': campaign_id
        }).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=500, detail="Failed to create sequence")
        
        sequence_id = sequence.data[0]['id']
        logger.info(f"✅ Created sequence {sequence_id}")
        
        # Generate AI-powered sequence steps using knowledge bank
        ai_generator = AISequenceGenerator()
        ai_steps = ai_generator.generate_sequence_steps(
            campaign_data=campaign_data,
            lead_sample=leads.data if leads.data else [],
            tenant_id=current_user['tenant_id'],
            user_id=current_user['user_id'],
            num_steps=7
        )
        
        logger.info(f"🤖 Generated {len(ai_steps)} AI-powered steps")
        
        # Add tenant_id and sequence_id to each AI-generated step
        template_steps = []
        for step in ai_steps:
            step_data = {
                'tenant_id': current_user['tenant_id'],
                'sequence_id': sequence_id,
                **step  # Merge in the AI-generated step data
            }
            # Ensure delay fields exist for all step types
            if 'delay_days' not in step_data:
                step_data['delay_days'] = 0
            if 'delay_hours' not in step_data:
                step_data['delay_hours'] = 0
            template_steps.append(step_data)
        
        # Insert all steps
        steps_result = supabase_service.client.table('sequence_steps').insert(template_steps).execute()
        
        if not steps_result.data:
            logger.warning("⚠️ Failed to create template steps, but sequence was created")
        else:
            logger.info(f"✅ Created {len(steps_result.data)} template steps")
        
        # Enroll all campaign leads
        all_leads = supabase_service.client.table('leads').select('id').eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        enrolled_count = 0
        if all_leads.data:
            for lead in all_leads.data:
                try:
                    result = supabase_service.client.rpc('enroll_lead_in_sequence', {
                        'p_tenant_id': current_user['tenant_id'],
                        'p_lead_id': lead['id'],
                        'p_campaign_id': campaign_id,
                        'p_sequence_id': sequence_id
                    }).execute()
                    enrolled_count += 1
                except Exception as e:
                    logger.warning(f"Failed to enroll lead {lead['id']}: {e}")
        
        logger.info(f"✅ Enrolled {enrolled_count} leads in new sequence")
        
        return {
            "sequence_id": sequence_id,
            "name": sequence_name,
            "steps_created": len(template_steps),
            "leads_enrolled": enrolled_count,
            "message": f"Sequence created with {len(template_steps)} steps and {enrolled_count} leads enrolled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating sequence from campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/generate-blast-email")
async def generate_blast_email(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered email template for one-time blast"""
    try:
        logger.info(f"🤖 Generating email template for campaign {campaign_id}")
        
        # Get campaign details
        campaign = supabase_service.client.table('campaigns').select('*').eq('id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = campaign.data[0]
        
        # Get lead sample for context
        leads = supabase_service.client.table('leads').select('*').eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).limit(5).execute()
        
        # Generate AI template using AISequenceGenerator
        ai_generator = AISequenceGenerator()
        ai_steps = ai_generator.generate_sequence_steps(
            campaign_data=campaign_data,
            lead_sample=leads.data if leads.data else [],
            tenant_id=current_user['tenant_id'],
            user_id=current_user['user_id'],
            num_steps=1  # Just generate the initial email
        )
        
        # Extract the first email step
        if ai_steps and len(ai_steps) > 0 and ai_steps[0]['step_type'] == 'email':
            email_step = ai_steps[0]
            return {
                "subject": email_step.get('subject_line', 'Quick question'),
                "body": email_step.get('body_text', 'Email content')
            }
        else:
            # Fallback to default template
            settings = campaign_data.get('settings', {})
            target_audience = settings.get('target_audience', campaign_data.get('description', 'your industry'))
            value_proposition = settings.get('value_proposition', 'We help companies improve their operations.')
            call_to_action = settings.get('call_to_action', 'Would you be open to a quick call?')
            
            return {
                "subject": f"Quick question about {{{{company}}}}'s {target_audience}",
                "body": f"""Hi {{{{name}}}},

I noticed {{{{company}}}} is working in {target_audience}.

{value_proposition}

{call_to_action}

Best regards,
{{{{sender_name}}}}"""
            }
            
    except Exception as e:
        logger.error(f"❌ Error generating blast email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/send-blast")
async def send_email_blast(
    campaign_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Send one-time email blast to all campaign leads"""
    try:
        subject = request.get('subject')
        body = request.get('body')
        
        if not subject or not body:
            raise HTTPException(status_code=400, detail="Subject and body are required")
        
        logger.info(f"📧 Sending email blast for campaign {campaign_id}")
        
        # Get all leads for this campaign
        leads = supabase_service.client.table('leads').select('*').eq('campaign_id', campaign_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not leads.data:
            raise HTTPException(status_code=404, detail="No leads found for this campaign")
        
        # Get user's Gmail credentials
        google_auth = supabase_service.client.table('google_auth').select('*').eq('tenant_id', current_user['tenant_id']).execute()
        
        if not google_auth.data:
            raise HTTPException(status_code=400, detail="Google account not connected. Please connect your Gmail account first.")
        
        auth_data = google_auth.data[0]
        access_token = auth_data.get('access_token')
        refresh_token = auth_data.get('refresh_token')
        
        # Create email blast record
        blast_record = supabase_service.client.table('email_blasts').insert({
            'tenant_id': current_user['tenant_id'],
            'user_id': current_user['user_id'],
            'campaign_id': campaign_id,
            'subject': subject,
            'body': body,
            'total_leads': len(leads.data),
            'emails_sent': 0,
            'emails_failed': 0,
            'status': 'sending'
        }).execute()
        
        if not blast_record.data:
            raise HTTPException(status_code=500, detail="Failed to create blast record")
        
        blast_id = blast_record.data[0]['id']
        logger.info(f"📋 Created blast record: {blast_id}")
        
        # Send emails
        google_service = GoogleOAuthService()
        emails_sent = 0
        emails_failed = 0
        blast_recipients = []
        
        for lead in leads.data:
            try:
                # Personalize email for this lead
                personalized_subject = subject.replace('{{name}}', lead.get('name', ''))
                personalized_subject = personalized_subject.replace('{{company}}', lead.get('company', ''))
                personalized_subject = personalized_subject.replace('{{title}}', lead.get('title', ''))
                personalized_subject = personalized_subject.replace('{{industry}}', lead.get('industry', ''))
                
                personalized_body = body.replace('{{name}}', lead.get('name', ''))
                personalized_body = personalized_body.replace('{{company}}', lead.get('company', ''))
                personalized_body = personalized_body.replace('{{title}}', lead.get('title', ''))
                personalized_body = personalized_body.replace('{{industry}}', lead.get('industry', ''))
                personalized_body = personalized_body.replace('{{sender_name}}', 'Your Sales Team')  # TODO: Get from user profile
                
                # Send via Gmail API
                result = google_service.send_email_via_gmail(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    to_email=lead.get('email'),
                    subject=personalized_subject,
                    body=personalized_body
                )
                
                # Track recipient
                recipient_status = 'sent' if result.get('success') else 'failed'
                blast_recipients.append({
                    'tenant_id': current_user['tenant_id'],
                    'blast_id': blast_id,
                    'lead_id': lead.get('id'),
                    'email': lead.get('email'),
                    'name': lead.get('name'),
                    'company': lead.get('company'),
                    'personalized_subject': personalized_subject,
                    'personalized_body': personalized_body,
                    'status': recipient_status,
                    'error_message': result.get('error') if not result.get('success') else None
                })
                
                if result.get('success'):
                    emails_sent += 1
                    # Update lead status
                    supabase_service.client.table('leads').update({
                        'status': 'contacted',
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }).eq('id', lead.get('id')).eq('tenant_id', current_user['tenant_id']).execute()
                else:
                    emails_failed += 1
                    logger.warning(f"Failed to send to {lead.get('email')}: {result.get('error')}")
                    
            except Exception as e:
                emails_failed += 1
                error_msg = str(e)
                logger.error(f"Error sending to {lead.get('email')}: {e}")
                
                # Track failed recipient
                blast_recipients.append({
                    'tenant_id': current_user['tenant_id'],
                    'blast_id': blast_id,
                    'lead_id': lead.get('id'),
                    'email': lead.get('email'),
                    'name': lead.get('name'),
                    'company': lead.get('company'),
                    'personalized_subject': personalized_subject,
                    'personalized_body': personalized_body,
                    'status': 'failed',
                    'error_message': error_msg
                })
        
        # Save all recipients to database
        if blast_recipients:
            supabase_service.client.table('email_blast_recipients').insert(blast_recipients).execute()
            logger.info(f"📝 Recorded {len(blast_recipients)} blast recipients")
        
        # Update blast record with final stats
        supabase_service.client.table('email_blasts').update({
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'status': 'completed',
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', blast_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        logger.info(f"✅ Email blast completed: {emails_sent} sent, {emails_failed} failed")
        
        return {
            "success": True,
            "blast_id": blast_id,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "total_leads": len(leads.data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending email blast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/email-blasts")
async def get_campaign_email_blasts(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all email blasts for a campaign"""
    try:
        logger.info(f"📧 Fetching email blasts for campaign {campaign_id}")
        
        blasts = supabase_service.client.table('email_blasts')\
            .select('*')\
            .eq('campaign_id', campaign_id)\
            .eq('tenant_id', current_user['tenant_id'])\
            .order('sent_at', desc=True)\
            .execute()
        
        return {
            "blasts": blasts.data or [],
            "total": len(blasts.data) if blasts.data else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching email blasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email-blasts/{blast_id}")
async def get_email_blast_details(
    blast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get email blast details with recipients"""
    try:
        logger.info(f"📧 Fetching blast details for {blast_id}")
        
        # Get blast record
        blast = supabase_service.client.table('email_blasts')\
            .select('*')\
            .eq('id', blast_id)\
            .eq('tenant_id', current_user['tenant_id'])\
            .single()\
            .execute()
        
        if not blast.data:
            raise HTTPException(status_code=404, detail="Blast not found")
        
        # Get recipients
        recipients = supabase_service.client.table('email_blast_recipients')\
            .select('*')\
            .eq('blast_id', blast_id)\
            .eq('tenant_id', current_user['tenant_id'])\
            .order('sent_at', desc=True)\
            .execute()
        
        # Get stats
        stats = supabase_service.client.rpc('get_email_blast_stats', {
            'p_blast_id': blast_id,
            'p_tenant_id': current_user['tenant_id']
        }).execute()
        
        return {
            "blast": blast.data,
            "recipients": recipients.data or [],
            "stats": stats.data[0] if stats.data else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching blast details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/enroll-in-sequence")
async def enroll_leads_in_sequence(
    request: EnrollLeadsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Enroll specific leads in a sequence"""
    try:
        logger.info(f"📝 Enrolling {len(request.lead_ids)} leads in sequence {request.sequence_id}")
        
        # Verify sequence exists
        sequence = supabase_service.client.table('sequences').select('*').eq('id', request.sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not sequence.data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        enrolled_count = 0
        failed_leads = []
        
        for lead_id in request.lead_ids:
            try:
                # Verify lead exists and belongs to tenant
                lead = supabase_service.client.table('leads').select('*').eq('id', lead_id).eq('tenant_id', current_user['tenant_id']).execute()
                
                if not lead.data:
                    failed_leads.append({"lead_id": lead_id, "reason": "Lead not found"})
                    continue
                
                # Enroll lead
                result = supabase_service.client.rpc('enroll_lead_in_sequence', {
                    'p_tenant_id': current_user['tenant_id'],
                    'p_lead_id': lead_id,
                    'p_campaign_id': request.campaign_id or lead.data[0].get('campaign_id'),
                    'p_sequence_id': request.sequence_id
                }).execute()
                
                enrolled_count += 1
            except Exception as e:
                failed_leads.append({"lead_id": lead_id, "reason": str(e)})
        
        logger.info(f"✅ Enrolled {enrolled_count}/{len(request.lead_ids)} leads")
        return {
            "success": True,
            "enrolled": enrolled_count,
            "failed": len(failed_leads),
            "failed_leads": failed_leads
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error enrolling leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads/{lead_id}/sequence-state")
async def get_lead_sequence_state(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a lead's current sequence state"""
    try:
        logger.info(f"🔍 Getting sequence state for lead {lead_id}")
        
        result = supabase_service.client.table('lead_sequence_state').select('*').eq('lead_id', lead_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not result.data:
            return {"sequences": []}
        
        return {"sequences": result.data}
        
    except Exception as e:
        logger.error(f"❌ Error getting lead sequence state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/pause-sequence")
async def pause_lead_sequence(
    lead_id: str,
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a lead's sequence"""
    try:
        logger.info(f"⏸️ Pausing sequence for lead {lead_id}")
        
        result = supabase_service.client.table('lead_sequence_state').update({
            "status": "paused",
            "updated_at": datetime.now().isoformat()
        }).eq('lead_id', lead_id).eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Lead sequence state not found")
        
        logger.info(f"✅ Sequence paused")
        return {"success": True, "message": "Sequence paused"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error pausing sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/resume-sequence")
async def resume_lead_sequence(
    lead_id: str,
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resume a paused sequence"""
    try:
        logger.info(f"▶️ Resuming sequence for lead {lead_id}")
        
        result = supabase_service.client.table('lead_sequence_state').update({
            "status": "active",
            "updated_at": datetime.now().isoformat()
        }).eq('lead_id', lead_id).eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Lead sequence state not found")
        
        logger.info(f"✅ Sequence resumed")
        return {"success": True, "message": "Sequence resumed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resuming sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/stop-sequence")
async def stop_lead_sequence(
    lead_id: str,
    sequence_id: str,
    reason: str = "Manual stop",
    current_user: dict = Depends(get_current_user)
):
    """Stop a lead's sequence"""
    try:
        logger.info(f"🛑 Stopping sequence for lead {lead_id}")
        
        # Get the state ID
        state = supabase_service.client.table('lead_sequence_state').select('id').eq('lead_id', lead_id).eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not state.data:
            raise HTTPException(status_code=404, detail="Lead sequence state not found")
        
        # Call stop function
        result = supabase_service.client.rpc('stop_lead_sequence', {
            'p_state_id': state.data[0]['id'],
            'p_reason': reason
        }).execute()
        
        logger.info(f"✅ Sequence stopped")
        return {"success": True, "message": "Sequence stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error stopping sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sequence Execution & Scheduler

@app.get("/sequences/{sequence_id}/analytics")
async def get_sequence_analytics(
    sequence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get analytics for a sequence"""
    try:
        logger.info(f"📊 Getting analytics for sequence {sequence_id}")
        
        # Get from materialized view
        result = supabase_service.client.table('sequence_performance_summary').select('*').eq('sequence_id', sequence_id).eq('tenant_id', current_user['tenant_id']).execute()
        
        if not result.data:
            # Return empty analytics if not found
            return {
                "sequence_id": sequence_id,
                "current_leads": 0,
                "active_leads": 0,
                "completed_leads": 0,
                "total_emails_sent": 0,
                "open_rate": 0,
                "reply_rate": 0,
                "completion_rate": 0
            }
        
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Error getting sequence analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sequences/process-queue")
async def process_sequence_queue(background_tasks: BackgroundTasks):
    """Process pending sequence actions (cron job endpoint)"""
    try:
        logger.info(f"⚙️ Processing sequence queue...")
        
        # Get all active lead sequences that are due
        now = datetime.now().isoformat()
        
        pending = supabase_service.client.table('lead_sequence_state').select(
            '*, leads(name, email), sequences(name), sequence_steps(id, step_type, step_order, subject_line, body_text, delay_days, delay_hours)'
        ).eq('status', 'active').lte('next_action_at', now).limit(100).execute()
        
        if not pending.data:
            logger.info(f"✅ No pending actions")
            return {"success": True, "processed": 0, "message": "No pending actions"}
        
        processed = 0
        errors = []
        
        for state in pending.data:
            try:
                # Process this lead's next step
                await execute_sequence_step(state)
                processed += 1
            except Exception as e:
                errors.append({"lead_id": state['lead_id'], "error": str(e)})
                logger.error(f"Error processing lead {state['lead_id']}: {e}")
        
        logger.info(f"✅ Processed {processed} sequence actions")
        return {
            "success": True,
            "processed": processed,
            "errors": len(errors),
            "error_details": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing sequence queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_sequence_step(state: dict):
    """Execute a single sequence step for a lead"""
    try:
        step = state.get('sequence_steps')
        if not step:
            logger.warning(f"No step found for state {state['id']}")
            return
        
        lead = state.get('leads')
        sequence = state.get('sequences')
        
        logger.info(f"🎬 Executing step {step['step_order']} for lead {lead.get('name', 'Unknown')}")
        
        # Handle different step types
        if step['step_type'] == 'email':
            await send_sequence_email(state, step, lead)
        elif step['step_type'] == 'delay':
            await process_delay_step(state, step)
        elif step['step_type'] == 'condition':
            await evaluate_condition_step(state, step, lead)
        elif step['step_type'] == 'action':
            await execute_action_step(state, step, lead)
        
        # Log execution
        supabase_service.client.table('sequence_execution_log').insert({
            "tenant_id": state['tenant_id'],
            "lead_id": state['lead_id'],
            "sequence_id": state['sequence_id'],
            "step_id": step['id'],
            "action_type": 'step_completed',
            "action_result": 'success',
            "step_order": step['step_order'],
            "step_name": step.get('name', f"Step {step['step_order']}")
        }).execute()
        
        # Advance to next step
        supabase_service.client.rpc('advance_to_next_step', {
            'p_state_id': state['id'],
            'p_skip_current': False
        }).execute()
        
    except Exception as e:
        logger.error(f"❌ Error executing step: {e}")
        # Log error
        supabase_service.client.table('sequence_execution_log').insert({
            "tenant_id": state['tenant_id'],
            "lead_id": state['lead_id'],
            "sequence_id": state['sequence_id'],
            "step_id": step.get('id'),
            "action_type": 'error_occurred',
            "action_result": 'failed',
            "error_message": str(e)
        }).execute()
        raise

async def send_sequence_email(state: dict, step: dict, lead: dict):
    """Send an email as part of a sequence"""
    try:
        logger.info(f"📧 Sending email: {step.get('subject_line')}")
        
        # TODO: Integrate with actual email service
        # For now, just log and update metrics
        
        # Update lead sequence state
        supabase_service.client.table('lead_sequence_state').update({
            "emails_sent": state.get('emails_sent', 0) + 1,
            "updated_at": datetime.now().isoformat()
        }).eq('id', state['id']).execute()
        
        # Track engagement
        supabase_service.client.table('lead_engagement').insert({
            "tenant_id": state['tenant_id'],
            "lead_id": state['lead_id'],
            "campaign_id": state.get('campaign_id'),
            "event_type": "email_sent",
            "event_data": {
                "sequence_id": state['sequence_id'],
                "step_id": step['id'],
                "subject": step.get('subject_line')
            }
        }).execute()
        
        logger.info(f"✅ Email sent")
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        raise

async def process_delay_step(state: dict, step: dict):
    """Process a delay step"""
    # Delay steps are handled by the advance_to_next_step function
    # which calculates the next_action_at based on delay_days/delay_hours
    pass

async def evaluate_condition_step(state: dict, step: dict, lead: dict):
    """Evaluate a conditional step"""
    try:
        condition_type = step.get('condition_type')
        logger.info(f"🔀 Evaluating condition: {condition_type}")
        
        condition_met = False
        
        if condition_type == 'if_replied':
            # Check if lead has replied
            replied = state.get('replied_at') is not None
            condition_met = replied
        
        elif condition_type == 'if_opened':
            # Check if lead opened recent email
            opens = state.get('emails_opened', 0)
            condition_met = opens > 0
        
        elif condition_type == 'if_clicked':
            # Check if lead clicked links
            clicks = state.get('emails_clicked', 0)
            condition_met = clicks > 0
        
        elif condition_type == 'if_not_replied':
            replied = state.get('replied_at') is not None
            condition_met = not replied
        
        # If condition met and lead replied, stop sequence
        if condition_type == 'if_replied' and condition_met:
            supabase_service.client.rpc('stop_lead_sequence', {
                'p_state_id': state['id'],
                'p_reason': 'Lead replied'
            }).execute()
        
        logger.info(f"✅ Condition result: {condition_met}")
        
    except Exception as e:
        logger.error(f"❌ Error evaluating condition: {e}")
        raise

async def execute_action_step(state: dict, step: dict, lead: dict):
    """Execute an action step"""
    try:
        action_type = step.get('action_type')
        logger.info(f"⚡ Executing action: {action_type}")
        
        if action_type == 'update_status':
            # Update lead status
            new_status = step.get('action_config', {}).get('status', 'contacted')
            supabase_service.client.table('leads').update({
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            }).eq('id', state['lead_id']).execute()
        
        elif action_type == 'mark_qualified':
            supabase_service.client.table('leads').update({
                "status": "qualified",
                "updated_at": datetime.now().isoformat()
            }).eq('id', state['lead_id']).execute()
        
        logger.info(f"✅ Action executed")
        
    except Exception as e:
        logger.error(f"❌ Error executing action: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
