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
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    created_at: str

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
        # For demo purposes, return not connected
        return {
            "connected": False,
            "email": None,
            "status": "not_connected"
        }
    except Exception as e:
        logger.error(f"Google auth status error: {e}")
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

@app.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    current_user: dict = Depends(get_current_user)
):
    """Get all campaigns for the current user"""
    try:
        logger.info(f"📋 Getting campaigns for user: {current_user['user_id']}")
        
        result = supabase_service.client.table("campaigns").select("*").eq("tenant_id", current_user["tenant_id"]).execute()
        
        campaigns = result.data or []
        logger.info(f"✅ Found {len(campaigns)} campaigns")
        
        return [CampaignResponse(**campaign) for campaign in campaigns]
        
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
    """Upload leads from CSV/Excel file"""
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
        
        # Validate required columns
        required_columns = ['name', 'company', 'title']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Prepare leads data
        leads_data = []
        for _, row in df.iterrows():
            lead_data = {
                "tenant_id": current_user["tenant_id"],
                "campaign_id": campaign_id,
                "name": str(row['name']),
                "company": str(row['company']),
                "title": str(row['title']),
                "email": row.get('email'),
                "linkedin_url": row.get('linkedin_url'),
                "phone": row.get('phone'),
                "status": "new"
            }
            leads_data.append(lead_data)
        
        # Insert leads in batch
        result = supabase_service.client.table("leads").insert(leads_data).execute()
        
        leads_created = len(result.data) if result.data else 0
        logger.info(f"✅ Uploaded {leads_created} leads")
        
        return {
            "message": f"Successfully uploaded {leads_created} leads",
            "leads_created": leads_created
        }
        
    except Exception as e:
        logger.error(f"❌ Error uploading leads: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/campaigns/{campaign_id}/leads", response_model=List[LeadResponse])
async def get_leads(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all leads for a campaign"""
    try:
        logger.info(f"📋 Getting leads for campaign: {campaign_id}")
        
        # Verify campaign belongs to user
        campaign_result = supabase_service.client.table("campaigns").select("id").eq("id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        result = supabase_service.client.table("leads").select("*").eq("campaign_id", campaign_id).eq("tenant_id", current_user["tenant_id"]).execute()
        
        leads = result.data or []
        logger.info(f"✅ Found {len(leads)} leads")
        
        return [LeadResponse(**lead) for lead in leads]
        
    except Exception as e:
        logger.error(f"❌ Error getting leads: {e}")
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
    """Generate leads using the Prospector Agent with company knowledge"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🔍 Prospector request: {prompt}")
        
        # Import the prospector agent
        from agents.prospector_agent import ProspectorAgent
        
        # Initialize and run the prospector agent with company knowledge
        agent = ProspectorAgent()
        result = agent.prospect_leads(
            prompt, 
            tenant_id=current_user["tenant_id"], 
            user_id=current_user["user_id"]
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Generated {result['lead_count']} leads",
                "leads": result["leads"],
                "criteria": result["criteria"],
                "csv_content": result.get("csv_content", ""),
                "csv_filename": result.get("csv_filename", "")
            }
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
    """Execute Smart Campaign with company knowledge"""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🚀 Smart Campaign request: {prompt}")
        
        # Import the smart campaign orchestrator
        from agents.smart_campaign_orchestrator import SmartCampaignOrchestrator
        
        # Initialize and run the smart campaign orchestrator with company knowledge
        orchestrator = SmartCampaignOrchestrator()
        result = orchestrator.execute_smart_campaign(
            prompt,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"]
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Smart campaign executed successfully",
                "pipeline_id": result["pipeline_id"],
                "stages": result["stages"],
                "final_results": result["final_results"],
                "execution_time": result["execution_time"]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to execute smart campaign"))
            
    except Exception as e:
        logger.error(f"Smart Campaign error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copywriter/personalize-message")
async def personalize_message(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Generate a personalized message using Copywriter Agent with company knowledge"""
    try:
        lead_data = request.get("lead_data", {})
        message_type = request.get("message_type", "cold_email")
        campaign_context = request.get("campaign_context", {})
        user_template = request.get("user_template", None)
        
        if not lead_data:
            raise HTTPException(status_code=400, detail="Lead data is required")
        
        logger.info(f"✍️ Personalizing {message_type} for {lead_data.get('name', 'Unknown')}")
        
        # Import the copywriter agent
        from agents.copywriter_agent import CopywriterAgent
        
        # Initialize and run the copywriter agent with company knowledge
        agent = CopywriterAgent()
        result = agent.personalize_message(
            lead_data, 
            message_type, 
            campaign_context, 
            user_template,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"]
        )
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
