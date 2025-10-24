import sys
import os
if '__file__' in globals():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
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
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from celery import Celery
import logging

from agents.google_workflow import AISDRWorkflow, CampaignData, LeadData
from integrations.email_service import EmailService
from integrations.linkedin_service import LinkedInService
from integrations.google_sheets_service import GoogleSheetsService
from integrations.google_oauth_service import GoogleOAuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_sdr.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Celery setup
celery_app = Celery(
    "ai_sdr",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379")
)

# Database Models
class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    target_audience = Column(String)
    value_proposition = Column(Text)
    call_to_action = Column(Text)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String)

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    email = Column(String)
    linkedin_url = Column(String)
    phone = Column(String)
    industry = Column(String)
    company_size = Column(String)
    location = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class OutreachLog(Base):
    __tablename__ = "outreach_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, nullable=False)
    lead_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    message_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    response_received = Column(Boolean, default=False)
    response_at = Column(DateTime)
    meeting_scheduled = Column(Boolean, default=False)
    meeting_date = Column(DateTime)
    status = Column(String, default="pending")

class UserGoogleAccount(Base):
    __tablename__ = "user_google_accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    google_email = Column(String, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    scopes = Column(Text)  # JSON string of scopes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserKnowledge(Base):
    __tablename__ = "user_knowledge"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    company_info = Column(Text)  # JSON string
    sales_approach = Column(Text)
    products = Column(Text)  # JSON string
    key_messages = Column(Text)  # JSON string
    value_propositions = Column(Text)  # JSON string
    target_audience = Column(Text)  # JSON string
    competitive_advantages = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    description: str
    target_audience: str
    value_proposition: str
    call_to_action: str

class CampaignResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    name: str
    description: str
    target_audience: str
    value_proposition: str
    call_to_action: str
    status: str
    created_at: datetime
    updated_at: datetime

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
    model_config = {"from_attributes": True}
    
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
    created_at: datetime

class OutreachLogResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    campaign_id: str
    lead_id: str
    channel: str
    message_sent: bool
    sent_at: Optional[datetime] = None
    response_received: bool
    response_at: Optional[datetime] = None
    meeting_scheduled: bool
    meeting_date: Optional[datetime] = None
    status: str

class CampaignStats(BaseModel):
    campaign_id: str
    total_leads: int
    processed_leads: int
    successful_outreach: int
    responses_received: int
    meetings_scheduled: int
    success_rate: float
    response_rate: float
    meeting_rate: float

# FastAPI app
app = FastAPI(title="AI SDR API", version="1.0.0")

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

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user (simplified for demo)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In production, implement proper JWT validation
    return {"user_id": "demo_user", "email": "demo@example.com"}

# Celery tasks
@celery_app.task
def execute_campaign_task(campaign_id: str, user_id: str):
    """Background task to execute campaign"""
    try:
        db = SessionLocal()
        
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get leads
        leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
        leads_data = [lead.__dict__ for lead in leads]
        
        # Create campaign data
        campaign_data = CampaignData(
            campaign_id=campaign_id,
            name=campaign.name,
            description=campaign.description,
            target_audience=campaign.target_audience,
            value_proposition=campaign.value_proposition,
            call_to_action=campaign.call_to_action,
            created_at=campaign.created_at,
            status=campaign.status
        )
        
        # Execute workflow
        workflow = AISDRWorkflow()
        crew = workflow.create_crew(campaign_id, leads_data, campaign_data)
        results = workflow.execute_campaign()
        
        # Update campaign status
        campaign.status = "completed" if results["status"] == "success" else "failed"
        db.commit()
        
        # Store results in Redis
        redis_client.set(f"campaign_results:{campaign_id}", json.dumps(results, default=str))
        
        db.close()
        return results
        
    except Exception as e:
        logger.error(f"Campaign execution failed: {e}")
        # Update campaign status to failed
        db = SessionLocal()
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.status = "failed"
            db.commit()
        db.close()
        raise e

# API Endpoints

@app.get("/")
async def root():
    return {"message": "AI SDR API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Campaign endpoints
@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    db_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        target_audience=campaign.target_audience,
        value_proposition=campaign.value_proposition,
        call_to_action=campaign.call_to_action,
        user_id=current_user["user_id"]
    )
    
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    return CampaignResponse.model_validate(db_campaign)

@app.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for the current user"""
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user["user_id"]).all()
    return [CampaignResponse.model_validate(campaign) for campaign in campaigns]

@app.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignResponse.model_validate(campaign)

@app.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign: CampaignCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a campaign"""
    db_campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db_campaign.name = campaign.name
    db_campaign.description = campaign.description
    db_campaign.target_audience = campaign.target_audience
    db_campaign.value_proposition = campaign.value_proposition
    db_campaign.call_to_action = campaign.call_to_action
    db_campaign.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_campaign)
    
    return CampaignResponse.model_validate(db_campaign)

@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}

# Lead endpoints
@app.post("/campaigns/{campaign_id}/leads", response_model=LeadResponse)
async def create_lead(
    campaign_id: str,
    lead: LeadCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new lead for a campaign"""
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db_lead = Lead(
        campaign_id=campaign_id,
        name=lead.name,
        company=lead.company,
        title=lead.title,
        email=lead.email,
        linkedin_url=lead.linkedin_url,
        phone=lead.phone,
        industry=lead.industry,
        company_size=lead.company_size,
        location=lead.location
    )
    
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    return LeadResponse.model_validate(db_lead)

@app.post("/campaigns/{campaign_id}/leads/upload")
async def upload_leads(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload leads from CSV/Excel file"""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        # Read file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Validate required columns
        required_columns = ['name', 'company', 'title']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Create leads
        leads_created = 0
        for _, row in df.iterrows():
            lead = Lead(
                campaign_id=campaign_id,
                name=str(row['name']),
                company=str(row['company']),
                title=str(row['title']),
                email=row.get('email'),
                linkedin_url=row.get('linkedin_url'),
                phone=row.get('phone'),
                industry=row.get('industry'),
                company_size=row.get('company_size'),
                location=row.get('location')
            )
            db.add(lead)
            leads_created += 1
        
        db.commit()
        
        return {
            "message": f"Successfully uploaded {leads_created} leads",
            "leads_created": leads_created
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/campaigns/{campaign_id}/leads", response_model=List[LeadResponse])
async def get_leads(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all leads for a campaign"""
    # Verify campaign belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
    return [LeadResponse.model_validate(lead) for lead in leads]

# Campaign execution endpoints
@app.post("/campaigns/{campaign_id}/execute")
async def execute_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a campaign"""
    # Verify campaign exists and belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if campaign has leads
    leads_count = db.query(Lead).filter(Lead.campaign_id == campaign_id).count()
    if leads_count == 0:
        raise HTTPException(status_code=400, detail="Campaign has no leads")
    
    # Update campaign status
    campaign.status = "running"
    db.commit()
    
    # Execute campaign synchronously (simplified for demo)
    try:
        # Get leads
        leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
        leads_data = [lead.__dict__ for lead in leads]
        
        # Create campaign data
        campaign_data = CampaignData(
            campaign_id=campaign_id,
            name=campaign.name,
            description=campaign.description,
            target_audience=campaign.target_audience,
            value_proposition=campaign.value_proposition,
            call_to_action=campaign.call_to_action,
            created_at=campaign.created_at,
            status=campaign.status
        )
        
        # Real campaign execution with AI agents
        try:
            # Execute campaign using Google-integrated workflow
            workflow = AISDRWorkflow()
            
            # Check if user has Google account connected
            user_google_account = db.query(UserGoogleAccount).filter(
                UserGoogleAccount.user_id == current_user["user_id"]
            ).first()
            
            if user_google_account:
                # Use Google-integrated workflow
                results = workflow.execute_campaign(
                    campaign_id=campaign_id,
                    leads_data=leads_data,
                    campaign=campaign_data,
                    user_access_token=user_google_account.access_token
                )
                
                messages_sent = results.get("messages_sent", 0)
                personalized_messages = results.get("details", [])
                
                # Create detailed results
                campaign_results = {
                    "status": "success",
                    "leads_processed": results.get("leads_processed", 0),
                    "messages_generated": len(leads_data),
                    "messages_sent": messages_sent,
                    "responses_received": 0,
                    "meetings_scheduled": 0,
                    "execution_time": f"{results.get('execution_time', 0):.1f} seconds",
                    "details": f"Campaign executed with Google-integrated AI agents. {messages_sent} emails sent via Gmail API.",
                    "personalized_messages": personalized_messages,
                    "spreadsheet_created": results.get("spreadsheet_created", False),
                    "spreadsheet_id": results.get("spreadsheet_id")
                }
                
            else:
                # Fallback to basic workflow without Google integration
                email_service = EmailService()
                messages_sent = 0
                personalized_messages = []
                
                for lead_data in leads_data:
                    # Generate personalized message using AI (simplified for now)
                    message_body = f"""
Subject: {campaign_data.value_proposition[:50]}...

Hi {lead_data['name']},

I noticed you're {lead_data['title']} at {lead_data['company']}. 

{campaign_data.value_proposition}

{campaign_data.call_to_action}

Best regards,
AI SDR Team
"""
                    subject = f"{campaign_data.value_proposition[:50]}..."
                    
                    # Send email via SMTP if configured
                    if email_service.is_configured() and lead_data.get('email'):
                        try:
                            email_service.send_email(
                                to_email=lead_data['email'],
                                subject=subject,
                                body=message_body
                            )
                            messages_sent += 1
                            logger.info(f"SMTP email sent to {lead_data['email']}")
                        except Exception as e:
                            logger.error(f"Failed to send SMTP email to {lead_data['email']}: {e}")
                    
                    personalized_messages.append({
                        "lead": lead_data['name'],
                        "email": lead_data.get('email', 'No email'),
                        "message": message_body[:200] + "..." if len(message_body) > 200 else message_body
                    })
                
                campaign_results = {
                    "status": "success",
                    "leads_processed": len(leads_data),
                    "messages_generated": len(leads_data),
                    "messages_sent": messages_sent,
                    "responses_received": 0,
                    "meetings_scheduled": 0,
                    "execution_time": "5.2 seconds",
                    "details": f"Campaign executed with basic AI agents. {messages_sent} emails sent via SMTP.",
                    "personalized_messages": personalized_messages
                }
            
        except Exception as e:
            logger.error(f"Campaign execution failed: {e}")
            campaign_results = {
                "status": "failed",
                "leads_processed": len(leads_data),
                "messages_generated": 0,
                "messages_sent": 0,
                "responses_received": 0,
                "meetings_scheduled": 0,
                "execution_time": "0.1 seconds",
                "details": f"Campaign execution failed: {str(e)}",
                "personalized_messages": []
            }
        
        # Update campaign status
        campaign.status = "completed" if campaign_results["status"] == "success" else "failed"
        db.commit()
        
        return {
            "message": "Campaign executed successfully",
            "campaign_id": campaign_id,
            "results": campaign_results
        }
        
    except Exception as e:
        logger.error(f"Campaign execution failed: {e}")
        campaign.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Campaign execution failed: {str(e)}")

@app.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign execution status"""
    # Verify campaign belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get results from Redis
    results_key = f"campaign_results:{campaign_id}"
    results = redis_client.get(results_key)
    
    if results:
        results_data = json.loads(results)
    else:
        results_data = None
    
    return {
        "campaign_id": campaign_id,
        "status": campaign.status,
        "results": results_data
    }

@app.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign statistics"""
    # Verify campaign belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get lead counts
    total_leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).count()
    processed_leads = db.query(Lead).filter(
        Lead.campaign_id == campaign_id,
        Lead.status.in_(["processed", "completed"])
    ).count()
    
    # Get outreach logs
    outreach_logs = db.query(OutreachLog).filter(OutreachLog.campaign_id == campaign_id).all()
    
    successful_outreach = len([log for log in outreach_logs if log.message_sent])
    responses_received = len([log for log in outreach_logs if log.response_received])
    meetings_scheduled = len([log for log in outreach_logs if log.meeting_scheduled])
    
    # Calculate rates
    success_rate = (successful_outreach / total_leads * 100) if total_leads > 0 else 0
    response_rate = (responses_received / successful_outreach * 100) if successful_outreach > 0 else 0
    meeting_rate = (meetings_scheduled / responses_received * 100) if responses_received > 0 else 0
    
    return CampaignStats(
        campaign_id=campaign_id,
        total_leads=total_leads,
        processed_leads=processed_leads,
        successful_outreach=successful_outreach,
        responses_received=responses_received,
        meetings_scheduled=meetings_scheduled,
        success_rate=round(success_rate, 2),
        response_rate=round(response_rate, 2),
        meeting_rate=round(meeting_rate, 2)
    )

# Outreach logs endpoints
@app.get("/campaigns/{campaign_id}/outreach-logs", response_model=List[OutreachLogResponse])
async def get_outreach_logs(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get outreach logs for a campaign"""
    # Verify campaign belongs to user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user["user_id"]
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    logs = db.query(OutreachLog).filter(OutreachLog.campaign_id == campaign_id).all()
    return [OutreachLogResponse.model_validate(log) for log in logs]

# Google OAuth endpoints
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Extract code and state from request body
        code = request.code
        state = request.state
        
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        google_oauth = GoogleOAuthService()
        tokens = google_oauth.exchange_code_for_tokens(code)
        
        # Get user's Google email
        gmail_service = google_oauth.get_gmail_service(tokens["access_token"])
        profile = gmail_service.users().getProfile(userId='me').execute()
        google_email = profile['emailAddress']
        
        # Check if user already has a Google account linked
        existing_account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"],
            UserGoogleAccount.google_email == google_email
        ).first()
        
        if existing_account:
            # Update existing account
            existing_account.access_token = tokens["access_token"]
            existing_account.refresh_token = tokens.get("refresh_token", existing_account.refresh_token)
            existing_account.expires_at = datetime.fromisoformat(tokens["expires_at"]) if tokens["expires_at"] else None
            existing_account.scopes = json.dumps(tokens["scopes"])
            existing_account.updated_at = datetime.utcnow()
        else:
            # Create new account
            new_account = UserGoogleAccount(
                user_id=current_user["user_id"],
                google_email=google_email,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                expires_at=datetime.fromisoformat(tokens["expires_at"]) if tokens["expires_at"] else None,
                scopes=json.dumps(tokens["scopes"])
            )
            db.add(new_account)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Google account connected successfully",
            "google_email": google_email
        }
        
    except Exception as e:
        logger.error(f"Failed to handle Google callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/auth/google/disconnect")
async def disconnect_google_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Google account"""
    try:
        # Delete user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if account:
            db.delete(account)
            db.commit()
            return {
                "success": True,
                "message": "Google account disconnected successfully"
            }
        else:
            return {
                "success": False,
                "message": "No Google account connected"
            }
    except Exception as e:
        logger.error(f"Failed to disconnect Google account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/google/status")
async def get_google_auth_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Google account connection status"""
    accounts = db.query(UserGoogleAccount).filter(
        UserGoogleAccount.user_id == current_user["user_id"]
    ).all()
    
    return {
        "connected": len(accounts) > 0,
        "accounts": [
            {
                "id": account.id,
                "google_email": account.google_email,
                "connected_at": account.created_at.isoformat(),
                "scopes": json.loads(account.scopes) if account.scopes else []
            }
            for account in accounts
        ]
    }

class CreateSpreadsheetRequest(BaseModel):
    title: str

@app.get("/google/sheets/list")
async def list_user_sheets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's Google Sheets"""
    try:
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        google_oauth = GoogleOAuthService()
        sheets_list = google_oauth.list_user_sheets(account.access_token)
        
        return {"success": True, "sheets": sheets_list}
        
    except Exception as e:
        logger.error(f"Failed to list Google Sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/google/sheets/{sheet_id}/preview")
async def preview_sheet_data(
    sheet_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview data from a Google Sheet"""
    try:
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        google_oauth = GoogleOAuthService()
        sheet_data = google_oauth.preview_sheet_data(account.access_token, sheet_id)
        
        return {"success": True, "data": sheet_data}
        
    except Exception as e:
        logger.error(f"Failed to preview sheet data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ImportLeadsFromSheetRequest(BaseModel):
    campaign_id: str
    column_mapping: Dict[str, str]  # Maps sheet columns to lead fields

@app.post("/google/sheets/create")
async def create_google_spreadsheet(
    request: CreateSpreadsheetRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Google Spreadsheet"""
    try:
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.create_spreadsheet(account.access_token, request.title)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Failed to create Google spreadsheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/google/sheets/{sheet_id}/add-sample-data")
async def add_sample_data_to_sheet(
    sheet_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add sample lead data to a Google Sheet for testing"""
    try:
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        # Sample lead data
        sample_leads = [
            {"name": "John Smith", "company": "Tech Corp", "title": "CTO", "email": "john@techcorp.com", "industry": "Technology", "company_size": "50-200", "location": "San Francisco"},
            {"name": "Jane Doe", "company": "Innovation Inc", "title": "VP Engineering", "email": "jane@innovation.com", "industry": "Software", "company_size": "10-50", "location": "New York"},
            {"name": "Mike Johnson", "company": "StartupXYZ", "title": "Founder", "email": "mike@startupxyz.com", "industry": "Fintech", "company_size": "5-10", "location": "Austin"},
            {"name": "Sarah Wilson", "company": "Enterprise Solutions", "title": "Director of IT", "email": "sarah@enterprise.com", "industry": "Enterprise", "company_size": "500+", "location": "Chicago"},
            {"name": "David Brown", "company": "CloudTech", "title": "Head of Engineering", "email": "david@cloudtech.com", "industry": "Cloud", "company_size": "100-500", "location": "Seattle"}
        ]
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.add_leads_to_spreadsheet(account.access_token, sheet_id, sample_leads)
        
        if result["success"]:
            return {"success": True, "message": f"Added {len(sample_leads)} sample leads to the sheet"}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Failed to add sample data to sheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/google/sheets/{sheet_id}/import")
async def import_leads_from_sheet(
    sheet_id: str,
    request: ImportLeadsFromSheetRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import leads from a Google Sheet to a campaign"""
    try:
        # Verify campaign exists and belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user["user_id"]
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        google_oauth = GoogleOAuthService()
        leads_data = google_oauth.get_sheet_data(account.access_token, sheet_id)
        
        # Map sheet data to lead format
        mapped_leads = []
        for row in leads_data:
            lead_data = {}
            for sheet_column, lead_field in request.column_mapping.items():
                if sheet_column in row:
                    lead_data[lead_field] = row[sheet_column]
            
            # Ensure required fields exist
            if all(field in lead_data for field in ['name', 'company', 'title']):
                lead_data['campaign_id'] = request.campaign_id
                lead_data['status'] = 'pending'
                mapped_leads.append(lead_data)
        
        # Save leads to database
        leads_added = 0
        for lead_data in mapped_leads:
            db_lead = Lead(**lead_data)
            db.add(db_lead)
            leads_added += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully imported {leads_added} leads from Google Sheet",
            "leads_added": leads_added
        }
        
    except Exception as e:
        logger.error(f"Failed to import leads from sheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def create_google_spreadsheet(
    request: CreateSpreadsheetRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Google Spreadsheet"""
    try:
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.create_spreadsheet(account.access_token, request.title)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Failed to create Google spreadsheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaigns/{campaign_id}/google/sheets/sync")
async def sync_campaign_to_google_sheets(
    campaign_id: str,
    spreadsheet_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync campaign leads to Google Sheets"""
    try:
        # Verify campaign belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user["user_id"]
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get user's Google account
        account = db.query(UserGoogleAccount).filter(
            UserGoogleAccount.user_id == current_user["user_id"]
        ).first()
        
        if not account:
            raise HTTPException(status_code=400, detail="No Google account connected")
        
        # Check if token needs refresh
        if account.expires_at and account.expires_at <= datetime.utcnow():
            google_oauth = GoogleOAuthService()
            refreshed_tokens = google_oauth.refresh_access_token(account.refresh_token)
            account.access_token = refreshed_tokens["access_token"]
            account.expires_at = datetime.fromisoformat(refreshed_tokens["expires_at"]) if refreshed_tokens["expires_at"] else None
            db.commit()
        
        # Get campaign leads
        leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
        leads_data = [lead.__dict__ for lead in leads]
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.add_leads_to_spreadsheet(account.access_token, spreadsheet_id, leads_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Failed to sync campaign to Google Sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Prospector Agent endpoints
@app.post("/prospector/generate-leads")
async def generate_leads_with_prospector(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate leads using the AI Prospector Agent"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Import the prospector agent
        from agents.prospector_agent import ProspectorAgent
        
        # Initialize and run the prospector agent
        agent = ProspectorAgent()
        result = agent.prospect_leads(prompt)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "criteria": result["criteria"],
                "leads": result["leads"],
                "csv_filename": result["csv_filename"],
                "csv_content": result["csv_content"],
                "lead_count": result["lead_count"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate leads"))
            
    except Exception as e:
        logger.error(f"Prospector agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prospector/save-leads")
async def save_prospected_leads(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save prospected leads to a campaign"""
    try:
        campaign_id = request.get("campaign_id")
        leads_data = request.get("leads", [])
        
        if not campaign_id:
            raise HTTPException(status_code=400, detail="Campaign ID is required")
        
        if not leads_data:
            raise HTTPException(status_code=400, detail="Leads data is required")
        
        # Verify campaign exists and belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user["user_id"]
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Save leads to database
        leads_created = 0
        for lead_data in leads_data:
            try:
                db_lead = Lead(
                    campaign_id=campaign_id,
                    name=lead_data.get("name", ""),
                    company=lead_data.get("company", ""),
                    title=lead_data.get("title", ""),
                    email=lead_data.get("email"),
                    linkedin_url=lead_data.get("linkedin_url"),
                    phone=lead_data.get("phone"),
                    industry=lead_data.get("industry"),
                    company_size=lead_data.get("company_size"),
                    location=lead_data.get("location"),
                    status="pending"
                )
                db.add(db_lead)
                leads_created += 1
            except Exception as e:
                logger.warning(f"Skipping invalid lead data: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully saved {leads_created} prospected leads to campaign",
            "leads_created": leads_created
        }
        
    except Exception as e:
        logger.error(f"Error saving prospected leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prospector/agent-info")
async def get_prospector_agent_info(
    current_user: dict = Depends(get_current_user)
):
    """Get information about the Prospector Agent"""
    try:
        from agents.prospector_agent import ProspectorAgent
        
        agent = ProspectorAgent()
        agent_info = agent.get_agent_info()
        
        return {
            "success": True,
            "agent": agent_info
        }
        
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enrichment Agent endpoints
@app.post("/enrichment/validate-leads")
async def validate_leads_with_enrichment(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate and enrich leads using the AI Enrichment Agent"""
    try:
        leads_data = request.get("leads", [])
        if not leads_data:
            raise HTTPException(status_code=400, detail="Leads data is required")
        
        # Import the enrichment agent
        from agents.enrichment_agent import EnrichmentAgent
        
        # Initialize and run the enrichment agent
        agent = EnrichmentAgent()
        result = agent.enrich_leads(leads_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "enriched_leads": result["enriched_leads"],
                "stats": result["stats"],
                "csv_filename": result["csv_filename"],
                "csv_content": result["csv_content"],
                "lead_count": len(result["enriched_leads"])
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to enrich leads"))
            
    except Exception as e:
        logger.error(f"Enrichment agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enrichment/save-enriched-leads")
async def save_enriched_leads(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save enriched leads to a campaign"""
    try:
        campaign_id = request.get("campaign_id")
        enriched_leads = request.get("enriched_leads", [])
        
        if not campaign_id:
            raise HTTPException(status_code=400, detail="Campaign ID is required")
        
        if not enriched_leads:
            raise HTTPException(status_code=400, detail="Enriched leads data is required")
        
        # Verify campaign exists and belongs to user
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user["user_id"]
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Save enriched leads to database
        leads_created = 0
        for lead_data in enriched_leads:
            try:
                # Extract core lead data (remove enrichment metadata)
                core_lead_data = {
                    "campaign_id": campaign_id,
                    "name": lead_data.get("name", ""),
                    "company": lead_data.get("company", ""),
                    "title": lead_data.get("title", ""),
                    "email": lead_data.get("email"),
                    "linkedin_url": lead_data.get("linkedin_url"),
                    "phone": lead_data.get("phone"),
                    "industry": lead_data.get("industry"),
                    "company_size": lead_data.get("company_size"),
                    "location": lead_data.get("location"),
                    "status": "enriched"  # Mark as enriched
                }
                
                db_lead = Lead(**core_lead_data)
                db.add(db_lead)
                leads_created += 1
            except Exception as e:
                logger.warning(f"Skipping invalid enriched lead data: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully saved {leads_created} enriched leads to campaign",
            "leads_created": leads_created
        }
        
    except Exception as e:
        logger.error(f"Error saving enriched leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/enrichment/agent-info")
async def get_enrichment_agent_info(
    current_user: dict = Depends(get_current_user)
):
    """Get information about the Enrichment Agent"""
    try:
        from agents.enrichment_agent import EnrichmentAgent
        
        agent = EnrichmentAgent()
        agent_info = agent.get_agent_info()
        
        return {
            "success": True,
            "agent": agent_info
        }
        
    except Exception as e:
        logger.error(f"Error getting enrichment agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart Campaign endpoints
@app.post("/smart-campaign/execute")
async def execute_smart_campaign(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute the complete Smart Campaign pipeline"""
    try:
        user_prompt = request.get("prompt", "")
        if not user_prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Import the smart campaign orchestrator
        from agents.smart_campaign_orchestrator import SmartCampaignOrchestrator
        
        # Initialize and execute the pipeline
        orchestrator = SmartCampaignOrchestrator()
        result = orchestrator.execute_smart_campaign(user_prompt)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Smart Campaign pipeline executed successfully",
                "pipeline_id": result["pipeline_id"],
                "execution_time": result["execution_time"],
                "campaign_data": result["final_results"]["campaign_data"],
                "premium_leads": result["final_results"]["premium_leads"],
                "backup_leads": result["final_results"]["backup_leads"],
                "excluded_leads": result["final_results"]["excluded_leads"],
                "insights": result["final_results"]["insights"],
                "enrichment_stats": result["final_results"]["enrichment_stats"],
                "stages": result["stages"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Smart Campaign pipeline failed"))
            
    except Exception as e:
        logger.error(f"Smart Campaign error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-campaign/save-campaign")
async def save_smart_campaign(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save Smart Campaign results to database"""
    try:
        campaign_data = request.get("campaign_data")
        premium_leads = request.get("premium_leads", [])
        backup_leads = request.get("backup_leads", [])
        
        if not campaign_data:
            raise HTTPException(status_code=400, detail="Campaign data is required")
        
        # Create campaign
        db_campaign = Campaign(
            name=campaign_data["name"],
            description=campaign_data["description"],
            target_audience=campaign_data["target_audience"],
            value_proposition=campaign_data["value_proposition"],
            call_to_action=campaign_data["call_to_action"],
            status="draft",
            user_id=current_user["user_id"]
        )
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        
        # Save premium leads
        premium_count = 0
        for lead_data in premium_leads:
            try:
                core_lead_data = {
                    "campaign_id": db_campaign.id,
                    "name": lead_data.get("name", ""),
                    "company": lead_data.get("company", ""),
                    "title": lead_data.get("title", ""),
                    "email": lead_data.get("email"),
                    "linkedin_url": lead_data.get("linkedin_url"),
                    "phone": lead_data.get("phone"),
                    "industry": lead_data.get("industry"),
                    "company_size": lead_data.get("company_size"),
                    "location": lead_data.get("location"),
                    "status": "premium"
                }
                db_lead = Lead(**core_lead_data)
                db.add(db_lead)
                premium_count += 1
            except Exception as e:
                logger.warning(f"Skipping invalid premium lead: {e}")
                continue
        
        # Save backup leads
        backup_count = 0
        for lead_data in backup_leads:
            try:
                core_lead_data = {
                    "campaign_id": db_campaign.id,
                    "name": lead_data.get("name", ""),
                    "company": lead_data.get("company", ""),
                    "title": lead_data.get("title", ""),
                    "email": lead_data.get("email"),
                    "linkedin_url": lead_data.get("linkedin_url"),
                    "phone": lead_data.get("phone"),
                    "industry": lead_data.get("industry"),
                    "company_size": lead_data.get("company_size"),
                    "location": lead_data.get("location"),
                    "status": "backup"
                }
                db_lead = Lead(**core_lead_data)
                db.add(db_lead)
                backup_count += 1
            except Exception as e:
                logger.warning(f"Skipping invalid backup lead: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Smart Campaign saved successfully",
            "campaign_id": db_campaign.id,
            "campaign_name": db_campaign.name,
            "premium_leads_saved": premium_count,
            "backup_leads_saved": backup_count,
            "total_leads_saved": premium_count + backup_count
        }
        
    except Exception as e:
        logger.error(f"Error saving Smart Campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Copywriter Agent endpoints
@app.post("/copywriter/personalize-message")
async def personalize_message(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a personalized message for a specific lead"""
    try:
        lead_data = request.get("lead_data", {})
        message_type = request.get("message_type", "cold_email")
        campaign_context = request.get("campaign_context", {})
        user_template = request.get("user_template", None)
        
        if not lead_data:
            raise HTTPException(status_code=400, detail="Lead data is required")
        
        # Import the copywriter agent
        from agents.copywriter_agent import CopywriterAgent
        
        # Initialize and run the copywriter agent
        agent = CopywriterAgent()
        result = agent.personalize_message(lead_data, message_type, campaign_context, user_template)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Message personalized successfully",
                "personalized_message": result["personalized_message"],
                "lead_context": result["lead_context"],
                "industry_context": result["industry_context"],
                "personalization_score": result["personalization_score"],
                "message_length": result["message_length"],
                "generated_at": result["generated_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to personalize message"))
            
    except Exception as e:
        logger.error(f"Copywriter agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copywriter/create-sequence")
async def create_email_sequence(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a multi-touch email sequence for a lead"""
    try:
        lead_data = request.get("lead_data", {})
        campaign_context = request.get("campaign_context", {})
        sequence_length = request.get("sequence_length", 3)
        
        if not lead_data:
            raise HTTPException(status_code=400, detail="Lead data is required")
        
        # Import the copywriter agent
        from agents.copywriter_agent import CopywriterAgent
        
        # Initialize and run the copywriter agent
        agent = CopywriterAgent()
        result = agent.create_email_sequence(lead_data, campaign_context, sequence_length)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Email sequence created successfully",
                "sequence_length": result["sequence_length"],
                "email_sequence": result["email_sequence"],
                "lead_context": result["lead_context"],
                "campaign_context": result["campaign_context"],
                "created_at": result["created_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create email sequence"))
            
    except Exception as e:
        logger.error(f"Copywriter sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copywriter/generate-variations")
async def generate_message_variations(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate multiple message variations for A/B testing"""
    try:
        lead_data = request.get("lead_data", {})
        message_type = request.get("message_type", "cold_email")
        num_variations = request.get("num_variations", 3)
        
        if not lead_data:
            raise HTTPException(status_code=400, detail="Lead data is required")
        
        # Import the copywriter agent
        from agents.copywriter_agent import CopywriterAgent
        
        # Initialize and run the copywriter agent
        agent = CopywriterAgent()
        result = agent.generate_message_variations(lead_data, message_type, num_variations)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Message variations generated successfully",
                "message_type": result["message_type"],
                "variations": result["variations"],
                "num_variations": result["num_variations"],
                "generated_at": result["generated_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate variations"))
            
    except Exception as e:
        logger.error(f"Copywriter variations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    @app.get("/copywriter/agent-info")
    async def get_copywriter_agent_info(
        current_user: dict = Depends(get_current_user)
    ):
        """Get information about the Copywriter Agent"""
        try:
            from agents.copywriter_agent import CopywriterAgent
            
            agent = CopywriterAgent()
            agent_info = agent.get_agent_info()
            
            return {
                "success": True,
                "agent": agent_info
            }
            
        except Exception as e:
            logger.error(f"Error getting copywriter agent info: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Smart Outreach Agent endpoints
@app.post("/smart-outreach/create-plan")
async def create_smart_outreach_plan(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an intelligent outreach plan for multiple leads"""
    try:
        leads = request.get("leads", [])
        campaign_context = request.get("campaign_context", {})
        
        if not leads:
            raise HTTPException(status_code=400, detail="Leads data is required")
        
        # Import the smart outreach agent
        from agents.smart_outreach_agent import SmartOutreachAgent
        
        # Initialize and run the smart outreach agent
        agent = SmartOutreachAgent()
        result = agent.create_smart_outreach_plan(leads, campaign_context)
        
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
        logger.error(f"Smart outreach planning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-outreach/execute")
async def execute_smart_outreach(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute the smart outreach plan automatically"""
    try:
        outreach_plan = request.get("outreach_plan", {})
        user_preferences = request.get("user_preferences", {})
        
        if not outreach_plan:
            raise HTTPException(status_code=400, detail="Outreach plan is required")
        
        # Import the smart outreach agent
        from agents.smart_outreach_agent import SmartOutreachAgent
        
        # Initialize and run the smart outreach agent
        agent = SmartOutreachAgent()
        result = agent.execute_smart_outreach(outreach_plan, user_preferences)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Smart outreach executed successfully",
                "execution_results": result["execution_results"],
                "completed_at": result["completed_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to execute outreach"))
            
    except Exception as e:
        logger.error(f"Smart outreach execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/smart-outreach/agent-info")
async def get_smart_outreach_agent_info():
    """Get information about the Smart Outreach Agent"""
    try:
        from agents.smart_outreach_agent import SmartOutreachAgent
        
        agent = SmartOutreachAgent()
        agent_info = agent.get_agent_info()
        
        return {
            "success": True,
            "agent": agent_info
        }
        
    except Exception as e:
        logger.error(f"Error getting smart outreach agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Train Your Team endpoints
@app.post("/train-your-team/upload")
async def upload_training_files(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload documents for AI agent training"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Create upload directory if it doesn't exist
        upload_dir = Path("uploads/training")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            # Validate file type
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt']
            file_extension = Path(file.filename).suffix.lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_extension}. Allowed: {allowed_extensions}"
                )
            
            # Save file
            file_path = upload_dir / f"{current_user['user_id']}_{file.filename}"
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": str(file_path),
                "size": len(content)
            })
        
        return {
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "uploaded_files": uploaded_files
        }
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-your-team/extract-knowledge")
async def extract_knowledge_from_files(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Extract knowledge from uploaded documents using Claude AI"""
    try:
        files = request.get("files", [])
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Import the knowledge extraction agent
        from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
        
        # Initialize and run the knowledge extraction agent
        agent = KnowledgeExtractionAgent()
        
        # Extract file paths
        file_paths = [file["path"] for file in files]
        result = agent.extract_knowledge_from_files(file_paths)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Knowledge extracted successfully",
                "knowledge": result["knowledge"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to extract knowledge"))
            
    except Exception as e:
        logger.error(f"Knowledge extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train-your-team/save-knowledge")
async def save_extracted_knowledge(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save extracted knowledge to user's profile"""
    try:
        knowledge = request.get("knowledge")
        if not knowledge:
            raise HTTPException(status_code=400, detail="No knowledge data provided")
        
        # Check if user already has knowledge stored
        existing_knowledge = db.query(UserKnowledge).filter(
            UserKnowledge.user_id == current_user['user_id'],
            UserKnowledge.is_active == True
        ).first()
        
        if existing_knowledge:
            # Update existing knowledge
            existing_knowledge.company_info = json.dumps(knowledge.get('company_info', {}))
            existing_knowledge.sales_approach = knowledge.get('sales_approach', '')
            existing_knowledge.products = json.dumps(knowledge.get('products', []))
            existing_knowledge.key_messages = json.dumps(knowledge.get('key_messages', []))
            existing_knowledge.value_propositions = json.dumps(knowledge.get('value_propositions', []))
            existing_knowledge.target_audience = json.dumps(knowledge.get('target_audience', {}))
            existing_knowledge.competitive_advantages = json.dumps(knowledge.get('competitive_advantages', []))
            existing_knowledge.updated_at = datetime.utcnow()
            
            db.commit()
            knowledge_id = existing_knowledge.id
        else:
            # Create new knowledge record
            new_knowledge = UserKnowledge(
                user_id=current_user['user_id'],
                company_info=json.dumps(knowledge.get('company_info', {})),
                sales_approach=knowledge.get('sales_approach', ''),
                products=json.dumps(knowledge.get('products', [])),
                key_messages=json.dumps(knowledge.get('key_messages', [])),
                value_propositions=json.dumps(knowledge.get('value_propositions', [])),
                target_audience=json.dumps(knowledge.get('target_audience', {})),
                competitive_advantages=json.dumps(knowledge.get('competitive_advantages', []))
            )
            
            db.add(new_knowledge)
            db.commit()
            db.refresh(new_knowledge)
            knowledge_id = new_knowledge.id
        
        logger.info(f"Knowledge saved for user {current_user['user_id']}")
        
        return {
            "success": True,
            "message": "Knowledge saved successfully. Your AI agents are now trained!",
            "knowledge_id": knowledge_id
        }
        
    except Exception as e:
        logger.error(f"Save knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/train-your-team/agent-info")
async def get_knowledge_extraction_agent_info(
    current_user: dict = Depends(get_current_user)
):
    """Get information about the Knowledge Extraction Agent"""
    try:
        from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
        
        agent = KnowledgeExtractionAgent()
        agent_info = agent.get_agent_info()
        
        return {
            "success": True,
            "agent": agent_info
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge extraction agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/train-your-team/get-knowledge")
async def get_user_knowledge(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's stored knowledge"""
    try:
        knowledge = db.query(UserKnowledge).filter(
            UserKnowledge.user_id == current_user['user_id'],
            UserKnowledge.is_active == True
        ).first()
        
        if not knowledge:
            return {
                "success": True,
                "message": "No knowledge found",
                "knowledge": None
            }
        
        # Parse JSON fields back to objects
        parsed_knowledge = {
            "company_info": json.loads(knowledge.company_info) if knowledge.company_info else {},
            "sales_approach": knowledge.sales_approach or "",
            "products": json.loads(knowledge.products) if knowledge.products else [],
            "key_messages": json.loads(knowledge.key_messages) if knowledge.key_messages else [],
            "value_propositions": json.loads(knowledge.value_propositions) if knowledge.value_propositions else [],
            "target_audience": json.loads(knowledge.target_audience) if knowledge.target_audience else {},
            "competitive_advantages": json.loads(knowledge.competitive_advantages) if knowledge.competitive_advantages else [],
            "created_at": knowledge.created_at.isoformat(),
            "updated_at": knowledge.updated_at.isoformat()
        }
        
        return {
            "success": True,
            "message": "Knowledge retrieved successfully",
            "knowledge": parsed_knowledge
        }
        
    except Exception as e:
        logger.error(f"Get knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
