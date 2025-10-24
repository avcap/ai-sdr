import os
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai_tools import RagTool
from pydantic import BaseModel, Field
import pandas as pd
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from openai import OpenAI

class LeadData(BaseModel):
    name: str
    company: str
    title: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None

class CampaignData(BaseModel):
    campaign_id: str
    name: str
    description: str
    target_audience: str
    value_proposition: str
    call_to_action: str
    created_at: datetime
    status: str = "draft"

class GoogleDriveTool:
    name: str = "google_drive_tool"
    description: str = "Tool for reading and writing CSV files in Google Drive"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def run(self, action: str, file_name: str = None, data: List[Dict] = None) -> Dict[str, Any]:
        """Read or write CSV files in Google Drive"""
        try:
            from integrations.google_oauth_service import GoogleOAuthService
            google_oauth = GoogleOAuthService()
            
            if action == "read_csv":
                return self._read_csv_from_drive(file_name)
            elif action == "write_csv":
                return self._write_csv_to_drive(file_name, data)
            else:
                return {"success": False, "error": "Invalid action"}
                
        except Exception as e:
            logger.error(f"Google Drive operation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _read_csv_from_drive(self, file_name: str) -> Dict[str, Any]:
        """Read CSV file from Google Drive"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            credentials = Credentials(token=self.access_token)
            service = build('drive', 'v3', credentials=credentials)
            
            # Search for the file
            results = service.files().list(
                q=f"name='{file_name}' and mimeType='text/csv'",
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return {"success": False, "error": f"File '{file_name}' not found"}
            
            file_id = files[0]['id']
            
            # Download file content
            content = service.files().get_media(fileId=file_id).execute()
            
            # Parse CSV content
            import csv
            import io
            
            csv_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            leads_data = list(csv_reader)
            
            return {
                "success": True,
                "leads": leads_data,
                "count": len(leads_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to read CSV from Drive: {e}")
            return {"success": False, "error": str(e)}
    
    def _write_csv_to_drive(self, file_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Write CSV file to Google Drive"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            import csv
            import io
            
            credentials = Credentials(token=self.access_token)
            service = build('drive', 'v3', credentials=credentials)
            
            # Convert data to CSV
            output = io.StringIO()
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            csv_content = output.getvalue()
            
            # Create file metadata
            file_metadata = {
                'name': file_name,
                'mimeType': 'text/csv'
            }
            
            # Upload file
            media = io.BytesIO(csv_content.encode('utf-8'))
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file_name,
                "rows_written": len(data)
            }
            
        except Exception as e:
            logger.error(f"Failed to write CSV to Drive: {e}")
            return {"success": False, "error": str(e)}

class GmailTool:
    name: str = "gmail_tool"
    description: str = "Tool for sending emails via Gmail API"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def run(self, to_email: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            from integrations.google_oauth_service import GoogleOAuthService
            google_oauth = GoogleOAuthService()
            
            result = google_oauth.send_email_via_gmail(
                self.access_token, to_email, subject, body, from_email
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Gmail operation failed: {e}")
            return {"success": False, "error": str(e)}

class GoogleSheetsTool:
    name: str = "google_sheets_tool"
    description: str = "Tool for managing Google Sheets"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def run(self, action: str, spreadsheet_id: str = None, title: str = None, data: List[Dict] = None) -> Dict[str, Any]:
        """Manage Google Sheets"""
        try:
            from integrations.google_oauth_service import GoogleOAuthService
            google_oauth = GoogleOAuthService()
            
            if action == "create":
                return google_oauth.create_spreadsheet(self.access_token, title)
            elif action == "add_leads":
                return google_oauth.add_leads_to_spreadsheet(self.access_token, spreadsheet_id, data)
            elif action == "update_status":
                return google_oauth.update_lead_status(
                    self.access_token, spreadsheet_id, 
                    data.get('email'), data.get('status'), data.get('notes', '')
                )
            else:
                return {"success": False, "error": "Invalid action"}
                
        except Exception as e:
            logger.error(f"Google Sheets operation failed: {e}")
            return {"success": False, "error": str(e)}

class ProspectingTool:
    name: str = "prospecting_tool"
    description: str = "Tool for ingesting and validating lead data"
    
    def run(self, leads_data: List[Dict[str, Any]]) -> List[LeadData]:
        """Process and validate lead data"""
        validated_leads = []
        
        for lead in leads_data:
            try:
                # Validate required fields
                if not all(key in lead for key in ['name', 'company', 'title']):
                    logger.warning(f"Skipping lead with missing required fields: {lead}")
                    continue
                
                validated_lead = LeadData(
                    name=lead['name'],
                    company=lead['company'],
                    title=lead['title'],
                    email=lead.get('email'),
                    linkedin_url=lead.get('linkedin_url'),
                    phone=lead.get('phone'),
                    industry=lead.get('industry'),
                    company_size=lead.get('company_size'),
                    location=lead.get('location')
                )
                validated_leads.append(validated_lead)
                
            except Exception as e:
                logger.error(f"Error validating lead {lead}: {e}")
                continue
        
        logger.info(f"Successfully validated {len(validated_leads)} leads")
        return validated_leads

class PersonalizationTool:
    name: str = "personalization_tool"
    description: str = "Tool for generating personalized outreach messages"
    
    def run(self, lead: LeadData, campaign: CampaignData) -> Dict[str, str]:
        """Generate personalized message for a lead"""
        try:
            # Use OpenAI to generate personalized message
            import openai
            
            prompt = f"""
            Generate a personalized outreach email for the following lead and campaign:
            
            Lead Information:
            - Name: {lead.name}
            - Company: {lead.company}
            - Title: {lead.title}
            - Industry: {lead.industry or 'Unknown'}
            - Company Size: {lead.company_size or 'Unknown'}
            - Location: {lead.location or 'Unknown'}
            
            Campaign Information:
            - Campaign Name: {campaign.name}
            - Target Audience: {campaign.target_audience}
            - Value Proposition: {campaign.value_proposition}
            - Call to Action: {campaign.call_to_action}
            
            Generate a professional, personalized email that:
            1. Addresses the lead by name
            2. References their company and role
            3. Connects to the value proposition
            4. Includes a clear call to action
            5. Is concise and professional
            
            Return the response in this format:
            Subject: [email subject]
            Body: [email body]
            """
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse subject and body
            lines = content.split('\n')
            subject = ""
            body_lines = []
            
            for line in lines:
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('Body:'):
                    body_lines.append(line.replace('Body:', '').strip())
                elif line.strip() and not line.startswith('Subject:'):
                    body_lines.append(line.strip())
            
            body = '\n'.join(body_lines)
            
            return {
                "subject": subject or f"Re: {campaign.value_proposition[:50]}...",
                "body": body,
                "personalized": True
            }
            
        except Exception as e:
            logger.error(f"Personalization failed: {e}")
            # Fallback to template
            return {
                "subject": f"Re: {campaign.value_proposition[:50]}...",
                "body": f"Hi {lead.name},\n\n{campaign.value_proposition}\n\n{campaign.call_to_action}\n\nBest regards,\nAI SDR Team",
                "personalized": False
            }

class OutreachTool:
    name: str = "outreach_tool"
    description: str = "Tool for sending outreach messages and tracking responses"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def run(self, lead: LeadData, message: Dict[str, str], channel: str = "email") -> Dict[str, Any]:
        """Send outreach message and return tracking info"""
        try:
            if channel == "email" and lead.email:
                gmail_tool = GmailTool(self.access_token)
                result = gmail_tool.run(
                    to_email=lead.email,
                    subject=message["subject"],
                    body=message["body"]
                )
                
                if result["success"]:
                    return {
                        "success": True,
                        "channel": "email",
                        "recipient": lead.email,
                        "message_id": result.get("message_id"),
                        "sent_at": result.get("sent_at"),
                        "status": "sent"
                    }
                else:
                    return {
                        "success": False,
                        "channel": "email",
                        "recipient": lead.email,
                        "error": result.get("error"),
                        "status": "failed"
                    }
            else:
                return {
                    "success": False,
                    "channel": channel,
                    "error": f"No email address for {lead.name}",
                    "status": "skipped"
                }
                
        except Exception as e:
            logger.error(f"Outreach failed for {lead.name}: {e}")
            return {
                "success": False,
                "channel": channel,
                "error": str(e),
                "status": "failed"
            }

class CoordinatorTool:
    name: str = "coordinator_tool"
    description: str = "Tool for orchestrating the workflow and managing campaign state"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def run(self, campaign_id: str, leads: List[LeadData], campaign: CampaignData) -> Dict[str, Any]:
        """Coordinate the entire workflow"""
        try:
            results = {
                "campaign_id": campaign_id,
                "leads_processed": 0,
                "messages_sent": 0,
                "responses_received": 0,
                "meetings_scheduled": 0,
                "execution_time": 0,
                "details": [],
                "spreadsheet_created": False,
                "spreadsheet_id": None
            }
            
            start_time = datetime.now()
            
            # Step 1: Create Google Sheets for tracking
            sheets_tool = GoogleSheetsTool(self.access_token)
            spreadsheet_result = sheets_tool.run(
                action="create",
                title=f"AI SDR Campaign - {campaign.name} - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            if spreadsheet_result["success"]:
                results["spreadsheet_created"] = True
                results["spreadsheet_id"] = spreadsheet_result["spreadsheet_id"]
                logger.info(f"Created spreadsheet: {spreadsheet_result['spreadsheet_url']}")
            
            # Step 2: Process each lead
            for lead in leads:
                try:
                    # Generate personalized message
                    personalization_tool = PersonalizationTool()
                    message = personalization_tool.run(lead, campaign)
                    
                    # Send outreach
                    outreach_tool = OutreachTool(self.access_token)
                    result = outreach_tool.run(lead, message, "email")
                    
                    # Update results
                    results["leads_processed"] += 1
                    if result["success"]:
                        results["messages_sent"] += 1
                    
                    # Add to details
                    results["details"].append({
                        "lead": lead.name,
                        "company": lead.company,
                        "email": lead.email,
                        "status": result["status"],
                        "message": message["subject"][:100] + "..." if len(message["subject"]) > 100 else message["subject"]
                    })
                    
                    # Update spreadsheet if created
                    if results["spreadsheet_created"]:
                        sheets_tool.run(
                            action="update_status",
                            spreadsheet_id=results["spreadsheet_id"],
                            data={
                                "email": lead.email,
                                "status": result["status"],
                                "notes": f"Message: {message['subject'][:50]}..."
                            }
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing lead {lead.name}: {e}")
                    results["details"].append({
                        "lead": lead.name,
                        "company": lead.company,
                        "email": lead.email,
                        "status": "error",
                        "message": f"Error: {str(e)}"
                    })
            
            # Step 3: Add all leads to spreadsheet
            if results["spreadsheet_created"]:
                leads_data = [lead.dict() for lead in leads]
                sheets_tool.run(
                    action="add_leads",
                    spreadsheet_id=results["spreadsheet_id"],
                    data=leads_data
                )
            
            end_time = datetime.now()
            results["execution_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Campaign {campaign_id} completed: {results['messages_sent']} messages sent")
            
            return results
            
        except Exception as e:
            logger.error(f"Campaign coordination failed: {e}")
            return {
                "campaign_id": campaign_id,
                "success": False,
                "error": str(e),
                "execution_time": 0
            }

class AISDRWorkflow:
    def __init__(self):
        self.crew = None
        self.campaign_data = None
        
    def create_crew(self, campaign_id: str, leads_data: List[Dict[str, Any]], campaign: CampaignData, user_access_token: str):
        """Create and configure the CrewAI crew with user's Google access"""
        
        # Convert leads data to LeadData objects
        prospecting_tool = ProspectingTool()
        validated_leads = prospecting_tool.run(leads_data)
        
        if not validated_leads:
            raise ValueError("No valid leads found")
        
        # Create tools with user's access token
        drive_tool = GoogleDriveTool(user_access_token)
        gmail_tool = GmailTool(user_access_token)
        sheets_tool = GoogleSheetsTool(user_access_token)
        coordinator_tool = CoordinatorTool(user_access_token)
        
        # Store campaign data
        self.campaign_data = campaign
        
        logger.info(f"Created AI SDR workflow for campaign {campaign_id} with {len(validated_leads)} leads")
        
        return {
            "campaign_id": campaign_id,
            "leads_count": len(validated_leads),
            "tools_created": ["drive_tool", "gmail_tool", "sheets_tool", "coordinator_tool"],
            "status": "ready"
        }
    
    def execute_campaign(self, campaign_id: str, leads_data: List[Dict[str, Any]], campaign: CampaignData, user_access_token: str) -> Dict[str, Any]:
        """Execute the AI SDR campaign"""
        try:
            # Create crew
            crew_info = self.create_crew(campaign_id, leads_data, campaign, user_access_token)
            
            # Convert leads data to LeadData objects
            prospecting_tool = ProspectingTool()
            validated_leads = prospecting_tool.run(leads_data)
            
            # Execute workflow
            coordinator_tool = CoordinatorTool(user_access_token)
            results = coordinator_tool.run(campaign_id, validated_leads, campaign)
            
            return results
            
        except Exception as e:
            logger.error(f"Campaign execution failed: {e}")
            return {
                "campaign_id": campaign_id,
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
