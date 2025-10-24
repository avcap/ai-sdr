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
        
        # Create context for personalization
        context = {
            "lead_name": lead.name,
            "company": lead.company,
            "title": lead.title,
            "industry": lead.industry or "their industry",
            "company_size": lead.company_size or "their company size",
            "location": lead.location or "their location",
            "campaign_name": campaign.name,
            "value_proposition": campaign.value_proposition,
            "call_to_action": campaign.call_to_action
        }
        
        # Generate personalized message
        personalized_message = f"""
Subject: Quick question about {lead.company}'s {campaign.name}

Hi {lead.name},

I noticed you're {lead.title} at {lead.company} in the {context['industry']} space. 

{campaign.value_proposition}

I'd love to learn more about how {lead.company} handles this challenge. Would you be open to a brief 15-minute conversation this week?

{campaign.call_to_action}

Best regards,
[Your Name]

P.S. I've helped similar companies in {context['industry']} achieve [specific result]. Happy to share some insights if helpful.
        """.strip()
        
        # Generate LinkedIn message (shorter version)
        linkedin_message = f"""
Hi {lead.name}, I noticed you're {lead.title} at {lead.company}. {campaign.value_proposition} 

Would you be open to a brief conversation about how this might apply to {lead.company}?

{campaign.call_to_action}
        """.strip()
        
        return {
            "email_message": personalized_message,
            "linkedin_message": linkedin_message,
            "personalization_score": self._calculate_personalization_score(context)
        }
    
    def _calculate_personalization_score(self, context: Dict[str, str]) -> float:
        """Calculate how personalized the message is (0-1)"""
        score = 0.0
        
        # Check for personalization elements
        if context["lead_name"]:
            score += 0.2
        if context["company"]:
            score += 0.2
        if context["title"]:
            score += 0.2
        if context["industry"] != "their industry":
            score += 0.2
        if context["company_size"] != "their company size":
            score += 0.1
        if context["location"] != "their location":
            score += 0.1
            
        return min(score, 1.0)

class OutreachTool:
    name: str = "outreach_tool"
    description: str = "Tool for sending outreach messages and tracking responses"
    
    def run(self, lead: LeadData, message: Dict[str, str], channel: str = "email") -> Dict[str, Any]:
        """Send outreach message and return tracking info"""
        
        result = {
            "lead_id": f"{lead.name}_{lead.company}",
            "channel": channel,
            "message_sent": True,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}",
            "status": "sent",
            "response_received": False,
            "response_at": None,
            "meeting_scheduled": False,
            "meeting_date": None
        }
        
        # Simulate sending (in production, integrate with actual APIs)
        logger.info(f"Sending {channel} message to {lead.name} at {lead.company}")
        
        # Simulate response tracking
        if channel == "email":
            result["email_subject"] = message.get("email_message", "").split("\n")[0].replace("Subject: ", "")
        
        return result

class CoordinatorTool:
    name: str = "coordinator_tool"
    description: str = "Tool for orchestrating the workflow and managing campaign state"
    
    def run(self, campaign_id: str, leads: List[LeadData], campaign: CampaignData) -> Dict[str, Any]:
        """Coordinate the entire workflow"""
        
        workflow_status = {
            "campaign_id": campaign_id,
            "total_leads": len(leads),
            "processed_leads": 0,
            "successful_outreach": 0,
            "responses_received": 0,
            "meetings_scheduled": 0,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Process each lead
        for i, lead in enumerate(leads):
            try:
                # Step 1: Validate lead
                prospecting_tool = ProspectingTool()
                validated_lead = prospecting_tool.run([lead.dict()])[0]
                
                # Step 2: Generate personalized message
                personalization_tool = PersonalizationTool()
                message = personalization_tool.run(validated_lead, campaign)
                
                # Step 3: Send outreach
                outreach_tool = OutreachTool()
                result = outreach_tool.run(validated_lead, message, "email")
                
                workflow_status["processed_leads"] += 1
                if result["message_sent"]:
                    workflow_status["successful_outreach"] += 1
                
                logger.info(f"Processed lead {i+1}/{len(leads)}: {lead.name}")
                
            except Exception as e:
                error_msg = f"Error processing lead {lead.name}: {str(e)}"
                workflow_status["errors"].append(error_msg)
                logger.error(error_msg)
        
        workflow_status["status"] = "completed"
        workflow_status["completed_at"] = datetime.now().isoformat()
        
        return workflow_status

# Create CrewAI Agents
def create_prospecting_agent():
    return Agent(
        role='Lead Prospecting Specialist',
        goal='Ingest, validate, and prepare high-quality lead data for outreach campaigns',
        backstory="""You are an expert in B2B lead prospecting with years of experience 
        in data validation and lead qualification. You excel at identifying high-value 
        prospects and ensuring data quality for successful outreach campaigns.""",
        verbose=True,
        allow_delegation=False,
        tools=[ProspectingTool()]
    )

def create_personalization_agent():
    return Agent(
        role='Personalization Expert',
        goal='Create highly personalized, contextual outreach messages that resonate with each prospect',
        backstory="""You are a master of personalization and copywriting, specializing in 
        B2B outreach. You understand how to craft messages that feel authentic and relevant 
        to each prospect's specific situation, company, and role.""",
        verbose=True,
        allow_delegation=False,
        tools=[PersonalizationTool()]
    )

def create_outreach_agent():
    return Agent(
        role='Outreach Specialist',
        goal='Execute outreach campaigns across multiple channels and track engagement',
        backstory="""You are an experienced outreach specialist who knows how to deliver 
        messages effectively across email, LinkedIn, and other channels. You excel at 
        tracking responses and managing follow-up sequences.""",
        verbose=True,
        allow_delegation=False,
        tools=[OutreachTool()]
    )

def create_coordinator_agent():
    return Agent(
        role='Campaign Coordinator',
        goal='Orchestrate the entire SDR workflow, manage campaign state, and ensure optimal execution',
        backstory="""You are a strategic campaign coordinator with deep experience in 
        managing complex B2B outreach workflows. You excel at coordinating multiple agents, 
        managing campaign state, and ensuring smooth execution from start to finish.""",
        verbose=True,
        allow_delegation=True,
        tools=[CoordinatorTool()]
    )

# Create Tasks
def create_prospecting_task(leads_data: List[Dict[str, Any]]):
    return Task(
        description=f"""
        Process and validate the provided lead data. Ensure all leads have required fields 
        (name, company, title) and clean up any data quality issues. Return a list of 
        validated leads ready for personalization.
        
        Lead data to process: {len(leads_data)} leads
        """,
        agent=create_prospecting_agent(),
        expected_output="List of validated LeadData objects with all required fields populated"
    )

def create_personalization_task(leads: List[LeadData], campaign: CampaignData):
    return Task(
        description=f"""
        Generate highly personalized outreach messages for each lead based on the campaign 
        context. Create both email and LinkedIn message variants. Ensure each message 
        feels authentic and relevant to the specific prospect.
        
        Campaign: {campaign.name}
        Value Proposition: {campaign.value_proposition}
        Number of leads: {len(leads)}
        """,
        agent=create_personalization_agent(),
        expected_output="Dictionary mapping each lead to personalized message content"
    )

def create_outreach_task(leads: List[LeadData], messages: Dict[str, Dict[str, str]]):
    return Task(
        description=f"""
        Execute the outreach campaign by sending personalized messages to each lead. 
        Track delivery status, responses, and engagement metrics. Handle both email and 
        LinkedIn outreach channels.
        
        Number of leads: {len(leads)}
        """,
        agent=create_outreach_agent(),
        expected_output="Detailed tracking data for each outreach attempt including status and responses"
    )

def create_coordination_task(campaign_id: str, leads: List[LeadData], campaign: CampaignData):
    return Task(
        description=f"""
        Coordinate the entire SDR workflow from start to finish. Manage the sequence of 
        prospecting, personalization, and outreach tasks. Track overall campaign progress 
        and handle any errors or exceptions that occur during execution.
        
        Campaign ID: {campaign_id}
        Campaign: {campaign.name}
        Total leads: {len(leads)}
        """,
        agent=create_coordinator_agent(),
        expected_output="Complete campaign execution report with metrics and status"
    )

# Main CrewAI Workflow
class AISDRWorkflow:
    def __init__(self):
        self.crew = None
        self.campaign_data = None
        
    def create_crew(self, campaign_id: str, leads_data: List[Dict[str, Any]], campaign: CampaignData):
        """Create and configure the CrewAI crew"""
        
        # Convert leads data to LeadData objects
        prospecting_tool = ProspectingTool()
        validated_leads = prospecting_tool.run(leads_data)
        
        # Create tasks
        prospecting_task = create_prospecting_task(leads_data)
        personalization_task = create_personalization_task(validated_leads, campaign)
        outreach_task = create_outreach_task(validated_leads, {})
        coordination_task = create_coordination_task(campaign_id, validated_leads, campaign)
        
        # Create crew
        self.crew = Crew(
            agents=[
                create_prospecting_agent(),
                create_personalization_agent(),
                create_outreach_agent(),
                create_coordinator_agent()
            ],
            tasks=[
                prospecting_task,
                personalization_task,
                outreach_task,
                coordination_task
            ],
            process=Process.sequential,
            verbose=True
        )
        
        self.campaign_data = campaign
        return self.crew
    
    def execute_campaign(self) -> Dict[str, Any]:
        """Execute the complete SDR campaign"""
        if not self.crew:
            raise ValueError("Crew not initialized. Call create_crew() first.")
        
        logger.info("Starting AI SDR campaign execution...")
        
        try:
            result = self.crew.kickoff()
            logger.info("Campaign execution completed successfully")
            return {
                "status": "success",
                "result": result,
                "campaign_id": self.campaign_data.campaign_id if self.campaign_data else None,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Campaign execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "campaign_id": self.campaign_data.campaign_id if self.campaign_data else None,
                "executed_at": datetime.now().isoformat()
            }

# Utility functions
def load_leads_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load leads from CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error loading leads from CSV: {e}")
        return []

def save_campaign_results(results: Dict[str, Any], output_path: str):
    """Save campaign results to file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Campaign results saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving campaign results: {e}")

if __name__ == "__main__":
    # Example usage
    sample_leads = [
        {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "title": "VP of Engineering",
            "email": "john@techcorp.com",
            "linkedin_url": "https://linkedin.com/in/johnsmith",
            "industry": "Technology",
            "company_size": "100-500",
            "location": "San Francisco, CA"
        },
        {
            "name": "Sarah Johnson",
            "company": "DataFlow Systems",
            "title": "CTO",
            "email": "sarah@dataflow.com",
            "linkedin_url": "https://linkedin.com/in/sarahjohnson",
            "industry": "Data Analytics",
            "company_size": "50-100",
            "location": "Austin, TX"
        }
    ]
    
    sample_campaign = CampaignData(
        campaign_id="campaign_001",
        name="AI Automation Outreach",
        description="Outreach campaign for AI automation services",
        target_audience="Engineering leaders at mid-size tech companies",
        value_proposition="Our AI automation platform can reduce your engineering team's manual work by 40% while improving code quality.",
        call_to_action="Would you be open to a 15-minute call to discuss how this could work for your team?",
        created_at=datetime.now()
    )
    
    # Create and execute workflow
    workflow = AISDRWorkflow()
    crew = workflow.create_crew("campaign_001", sample_leads, sample_campaign)
    results = workflow.execute_campaign()
    
    print("Campaign Results:")
    print(json.dumps(results, indent=2, default=str))
