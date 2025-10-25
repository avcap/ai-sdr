import os
import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
from openai import OpenAI

# Import our existing Google workflow components
from .google_workflow import LeadData, CampaignData
from services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

class ProspectorCriteria(BaseModel):
    """Criteria for lead prospecting"""
    target_role: str
    industry: str
    company_size: str
    location: str
    count: int = 50
    additional_filters: Optional[Dict[str, Any]] = None

class ProspectorTool:
    """Tool for AI-powered lead prospecting based on natural language prompts"""
    
    name: str = "prospector_tool"
    description: str = "AI-powered lead prospecting tool that generates realistic lead data based on user prompts"
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.knowledge_service = KnowledgeService()
    
    def parse_prompt(self, prompt: str, tenant_id: str = None, user_id: str = None) -> ProspectorCriteria:
        """Parse natural language prompt into structured criteria with company knowledge"""
        try:
            # Get company knowledge if available
            company_context = ""
            if tenant_id and user_id:
                company_context = self.knowledge_service.get_company_context(tenant_id, user_id)
            
            parse_prompt = f"""
            Parse this lead prospecting request into structured criteria:
            
            User Request: "{prompt}"
            
            {f"Company Context: {company_context}" if company_context else ""}
            
            Extract the following information:
            - target_role: The job title/role (e.g., "CTO", "VP Engineering", "Founder")
            - industry: The industry/sector (e.g., "SaaS", "Fintech", "Healthcare")
            - company_size: Company size range (e.g., "10-50", "50-200", "500+")
            - location: Geographic location (e.g., "San Francisco", "New York", "Remote")
            - count: Number of leads requested (default 50)
            
            {f"Consider the company's target audience and industry when parsing the request." if company_context else ""}
            
            Return as JSON format:
            {{
                "target_role": "extracted_role",
                "industry": "extracted_industry", 
                "company_size": "extracted_size",
                "location": "extracted_location",
                "count": extracted_number
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": parse_prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            criteria_json = response.choices[0].message.content.strip()
            # Clean up the response to ensure valid JSON
            if criteria_json.startswith("```json"):
                criteria_json = criteria_json.replace("```json", "").replace("```", "").strip()
            
            criteria_data = json.loads(criteria_json)
            return ProspectorCriteria(**criteria_data)
            
        except Exception as e:
            logger.error(f"Error parsing prompt: {e}")
            # Fallback to default criteria
            return ProspectorCriteria(
                target_role="CTO",
                industry="Technology",
                company_size="50-200",
                location="San Francisco",
                count=50
            )
    
    def generate_leads(self, criteria: ProspectorCriteria, tenant_id: str = None, user_id: str = None) -> List[LeadData]:
        """Generate realistic lead data based on criteria and company knowledge"""
        try:
            # Get company knowledge for enhanced lead generation
            company_context = ""
            target_audience = {}
            if tenant_id and user_id:
                company_context = self.knowledge_service.get_company_context(tenant_id, user_id, task_type="prospecting")
                target_audience = self.knowledge_service.get_target_audience(tenant_id, user_id, task_type="prospecting")
            
            generation_prompt = f"""
            Generate {criteria.count} realistic B2B leads with the following criteria:
            
            Target Role: {criteria.target_role}
            Industry: {criteria.industry}
            Company Size: {criteria.company_size}
            Location: {criteria.location}
            
            {f"Company Context: {company_context}" if company_context else ""}
            {f"Target Audience Info: {target_audience}" if target_audience else ""}
            
            IMPORTANT: This is for DEMO/TESTING purposes only. Generate fictional but realistic data.
            
            For each lead, provide:
            - name: Realistic first and last name (fictional)
            - company: Realistic company name in the {criteria.industry} industry (fictional)
            - title: The target role or similar
            - email: Professional email format (firstname.lastname@company.com) - fictional
            - linkedin_url: Use placeholder format "https://www.linkedin.com/in/firstname-lastname-[random]" - these are NOT real profiles
            - phone: US phone number format (fictional)
            - industry: The specified industry
            - company_size: The specified company size
            - location: The specified location
            
            Make the data realistic and diverse. Use actual company naming patterns and professional email formats.
            Add random suffixes to LinkedIn URLs to make them clearly fictional (e.g., -demo, -test, -sample).
            {f"Consider the company's target audience when generating relevant leads." if company_context else ""}
            Return as JSON array of lead objects.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": generation_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            leads_json = response.choices[0].message.content.strip()
            # Clean up the response
            if leads_json.startswith("```json"):
                leads_json = leads_json.replace("```json", "").replace("```", "").strip()
            
            leads_data = json.loads(leads_json)
            
            # Convert to LeadData objects
            leads = []
            for lead_dict in leads_data:
                try:
                    lead = LeadData(**lead_dict)
                    leads.append(lead)
                except Exception as e:
                    logger.warning(f"Skipping invalid lead data: {e}")
                    continue
            
            logger.info(f"Generated {len(leads)} leads for criteria: {criteria.target_role} in {criteria.industry}")
            return leads
            
        except Exception as e:
            logger.error(f"Error generating leads: {e}")
            return []
    
    def create_csv(self, leads: List[LeadData], filename: str = None) -> Dict[str, Any]:
        """Create CSV file from leads data"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"prospected_leads_{timestamp}.csv"
            
            # Create CSV content
            output = io.StringIO()
            fieldnames = ['name', 'company', 'title', 'email', 'linkedin_url', 'phone', 'industry', 'company_size', 'location']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead.dict())
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "filename": filename,
                "csv_content": csv_content,
                "lead_count": len(leads)
            }
            
        except Exception as e:
            logger.error(f"Error creating CSV: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run(self, prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Main execution method for prospector tool with company knowledge"""
        try:
            # Parse the user prompt with company context
            criteria = self.parse_prompt(prompt, tenant_id, user_id)
            logger.info(f"Parsed criteria: {criteria}")
            
            # Generate leads with company knowledge
            leads = self.generate_leads(criteria, tenant_id, user_id)
            
            if not leads:
                return {
                    "success": False,
                    "error": "Failed to generate any leads"
                }
            
            # Create CSV
            csv_result = self.create_csv(leads)
            
            if not csv_result["success"]:
                return csv_result
            
            return {
                "success": True,
                "criteria": criteria.dict(),
                "leads": [lead.dict() for lead in leads],
                "csv_filename": csv_result["filename"],
                "csv_content": csv_result["csv_content"],
                "lead_count": len(leads),
                "message": f"Successfully generated {len(leads)} leads for {criteria.target_role} in {criteria.industry}"
            }
            
        except Exception as e:
            logger.error(f"Prospector tool error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class ProspectorAgent:
    """AI Prospector Agent for lead mining and targeting with company knowledge"""
    
    def __init__(self):
        self.tool = ProspectorTool()
        self.knowledge_service = KnowledgeService()
        self.name = "Scout"
        self.role = "Lead Mining & Targeting Specialist"
        self.goal = "Generate high-quality, targeted lead lists based on natural language prompts and company knowledge"
        self.backstory = """You are Scout, an expert lead prospecting specialist with years of experience 
        in B2B sales development. You excel at understanding complex targeting requirements and generating 
        realistic, high-quality lead data that sales teams can immediately use for outreach campaigns.
        You leverage company knowledge to find the most relevant prospects."""
    
    def prospect_leads(self, prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Main method to prospect leads based on user prompt and company knowledge"""
        logger.info(f"Starting lead prospecting with prompt: {prompt}")
        
        result = self.tool.run(prompt, tenant_id, user_id)
        
        if result["success"]:
            logger.info(f"Prospecting completed: {result['lead_count']} leads generated")
        else:
            logger.error(f"Prospecting failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent information"""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the prospector agent
    agent = ProspectorAgent()
    
    test_prompt = "Find me 25 SaaS CTOs in San Francisco with 50-200 employees"
    
    print(f"Testing Prospector Agent: {agent.name}")
    print(f"Prompt: {test_prompt}")
    print("-" * 50)
    
    result = agent.prospect_leads(test_prompt)
    
    if result["success"]:
        print(f"✅ Success! Generated {result['lead_count']} leads")
        print(f"📄 CSV File: {result['csv_filename']}")
        print(f"🎯 Criteria: {result['criteria']}")
        print(f"📊 First 3 leads:")
        for i, lead in enumerate(result['leads'][:3]):
            print(f"  {i+1}. {lead['name']} - {lead['title']} at {lead['company']}")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
