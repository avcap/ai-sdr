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

# Import new adaptive services
from agents.adaptive_ai_agent import AdaptiveAIAgent, KnowledgeLevel, AdaptationStrategy
from integrations.grok_service import GrokService
from services.knowledge_fusion_service import KnowledgeFusionService
from services.llm_selector_service import LLMSelectorService

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
        
        # Initialize new adaptive services
        self.adaptive_agent = AdaptiveAIAgent()
        self.grok_service = GrokService()
        self.knowledge_fusion = KnowledgeFusionService()
        self.llm_selector = LLMSelectorService()
        
        # Enhanced capabilities
        self.name = "enhanced_prospector_tool"
        self.description = "AI-powered lead prospecting with adaptive intelligence, market data integration, and knowledge fusion"
    
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
    
    def execute_adaptive(self, prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Execute prospecting with adaptive intelligence based on available knowledge.
        
        Args:
            prompt: User's prospecting request
            tenant_id: Organization identifier
            user_id: User identifier
            
        Returns:
            Enhanced prospecting results with market intelligence
        """
        logger.info(f"Executing adaptive prospecting for user {user_id}")
        
        try:
            # Assess knowledge level and select strategy
            knowledge_assessment = self.adaptive_agent.assess_knowledge_level(
                tenant_id, user_id, prompt
            )
            
            adaptation_plan = self.adaptive_agent.select_adaptation_strategy(
                knowledge_assessment.level, "lead_generation"
            )
            
            # Execute with selected strategy
            strategy_result = self.adaptive_agent.execute_with_strategy(
                adaptation_plan.strategy, prompt, {
                    "task_type": "lead_generation",
                    "industry": self._extract_industry_from_prompt(prompt),
                    "target_role": self._extract_role_from_prompt(prompt)
                }, tenant_id, user_id
            )
            
            # Parse criteria using enhanced knowledge
            criteria = self.parse_prompt_enhanced(prompt, strategy_result, tenant_id, user_id)
            
            # Generate leads with market intelligence
            leads = self.generate_leads_enhanced(criteria, strategy_result, tenant_id, user_id)
            
            # Enrich leads with market data
            enriched_leads = self.enrich_leads_with_market_data(leads, criteria)
            
            # Create CSV with enhanced data
            csv_result = self.create_csv(enriched_leads)
            
            return {
                "success": True,
                "leads": enriched_leads,
                "csv_result": csv_result,
                "knowledge_level": knowledge_assessment.level.value,
                "strategy_used": adaptation_plan.strategy.value,
                "market_intelligence": self._get_market_intelligence_summary(criteria),
                "adaptation_metadata": strategy_result.get("strategy_metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error in adaptive prospecting: {e}")
            # Fallback to standard prospecting
            return self._fallback_prospecting(prompt, tenant_id, user_id)
    
    def parse_prompt_enhanced(self, prompt: str, strategy_result: Dict[str, Any], 
                            tenant_id: str = None, user_id: str = None) -> ProspectorCriteria:
        """Enhanced prompt parsing with fused knowledge"""
        try:
            # Get fused knowledge from strategy result
            fused_knowledge = strategy_result.get("knowledge", {})
            
            # Extract company context from fused knowledge
            company_context = ""
            if fused_knowledge.get("company_info"):
                company_context = json.dumps(fused_knowledge["company_info"])
            
            # Get target audience from fused knowledge
            target_audience = fused_knowledge.get("target_audience", {})
            
            # Enhanced parsing prompt with market context
            market_context = self._get_market_context_for_parsing(prompt)
            
            parse_prompt = f"""
            Parse this lead prospecting request into structured criteria with enhanced context:
            
            User Request: "{prompt}"
            
            Company Context: {company_context if company_context else "No company context available"}
            Target Audience: {json.dumps(target_audience) if target_audience else "No target audience data"}
            Market Context: {market_context}
            
            Extract the following information with high accuracy:
            - target_role: The job title/role (e.g., "CTO", "VP Engineering", "Founder")
            - industry: The industry/sector (e.g., "SaaS", "Fintech", "Healthcare")
            - company_size: Company size range (e.g., "10-50", "50-200", "500+")
            - location: Geographic location (e.g., "San Francisco", "New York", "Remote")
            - count: Number of leads requested (default 50)
            
            Consider the company's target audience, market conditions, and industry trends when parsing.
            
            Return as JSON format:
            {{
                "target_role": "extracted_role",
                "industry": "extracted_industry", 
                "company_size": "extracted_size",
                "location": "extracted_location",
                "count": extracted_number
            }}
            """
            
            # Use LLM selector for optimal model
            model_recommendation = self.llm_selector.recommend_model_for_task(
                "prompt_parsing", len(prompt), {"quality_priority": True}
            )
            
            selected_model = model_recommendation["recommended_model"]
            
            response = self.openai_client.chat.completions.create(
                model=selected_model,
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
            logger.error(f"Error in enhanced prompt parsing: {e}")
            # Fallback to standard parsing
            return self.parse_prompt(prompt, tenant_id, user_id)
    
    def generate_leads_enhanced(self, criteria: ProspectorCriteria, strategy_result: Dict[str, Any],
                              tenant_id: str = None, user_id: str = None) -> List[LeadData]:
        """Generate leads with enhanced market intelligence and knowledge fusion"""
        try:
            # Get fused knowledge
            fused_knowledge = strategy_result.get("knowledge", {})
            
            # Get market intelligence
            market_intelligence = self._get_market_intelligence_for_generation(criteria)
            
            # Enhanced generation prompt
            generation_prompt = f"""
            Generate {criteria.count} realistic B2B leads with enhanced market intelligence:
            
            Target Role: {criteria.target_role}
            Industry: {criteria.industry}
            Company Size: {criteria.company_size}
            Location: {criteria.location}
            
            Company Context: {json.dumps(fused_knowledge.get("company_info", {}))}
            Target Audience: {json.dumps(fused_knowledge.get("target_audience", {}))}
            Market Intelligence: {json.dumps(market_intelligence)}
            
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
            
            Consider market trends and industry insights when generating relevant leads.
            Return as JSON array of lead objects.
            """
            
            # Use optimal model for generation
            model_recommendation = self.llm_selector.recommend_model_for_task(
                "lead_generation", len(generation_prompt), {"quality_priority": True}
            )
            
            selected_model = model_recommendation["recommended_model"]
            
            response = self.openai_client.chat.completions.create(
                model=selected_model,
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
            
            logger.info(f"Generated {len(leads)} enhanced leads for criteria: {criteria.target_role} in {criteria.industry}")
            return leads
            
        except Exception as e:
            logger.error(f"Error generating enhanced leads: {e}")
            # Fallback to standard generation
            return self.generate_leads(criteria, tenant_id, user_id)
    
    def enrich_leads_with_market_data(self, leads: List[LeadData], criteria: ProspectorCriteria) -> List[LeadData]:
        """Enrich leads with market intelligence data"""
        try:
            enriched_leads = []
            
            # Get market sentiment for the industry
            market_sentiment = self.grok_service.get_market_sentiment(
                criteria.industry, ["growth", "innovation", "competition"]
            )
            
            # Get industry trends
            industry_trends = self.grok_service.get_industry_trends(criteria.industry)
            
            for lead in leads:
                # Add market intelligence metadata
                lead_dict = lead.dict()
                lead_dict["market_sentiment"] = market_sentiment.get("sentiment", "neutral")
                lead_dict["market_confidence"] = market_sentiment.get("confidence", 0.5)
                lead_dict["industry_trends"] = len(industry_trends.get("trends", []))
                lead_dict["enrichment_timestamp"] = datetime.now().isoformat()
                
                # Create enriched lead
                enriched_lead = LeadData(**lead_dict)
                enriched_leads.append(enriched_lead)
            
            logger.info(f"Enriched {len(enriched_leads)} leads with market data")
            return enriched_leads
            
        except Exception as e:
            logger.error(f"Error enriching leads with market data: {e}")
            return leads
    
    def _extract_industry_from_prompt(self, prompt: str) -> str:
        """Extract industry from prompt for context"""
        industries = ["technology", "saas", "fintech", "healthcare", "retail", "manufacturing"]
        prompt_lower = prompt.lower()
        
        for industry in industries:
            if industry in prompt_lower:
                return industry.title()
        
        return "Technology"  # Default
    
    def _extract_role_from_prompt(self, prompt: str) -> str:
        """Extract target role from prompt for context"""
        roles = ["cto", "ceo", "vp", "director", "manager", "founder"]
        prompt_lower = prompt.lower()
        
        for role in roles:
            if role in prompt_lower:
                return role.upper()
        
        return "CTO"  # Default
    
    def _get_market_context_for_parsing(self, prompt: str) -> str:
        """Get market context for enhanced parsing"""
        try:
            industry = self._extract_industry_from_prompt(prompt)
            market_sentiment = self.grok_service.get_market_sentiment(industry, ["growth"])
            
            return f"Market sentiment for {industry}: {market_sentiment.get('sentiment', 'neutral')} (confidence: {market_sentiment.get('confidence', 0.5):.2f})"
        except Exception as e:
            logger.warning(f"Could not get market context: {e}")
            return "Market context unavailable"
    
    def _get_market_intelligence_for_generation(self, criteria: ProspectorCriteria) -> Dict[str, Any]:
        """Get market intelligence for lead generation"""
        try:
            # Get market sentiment
            market_sentiment = self.grok_service.get_market_sentiment(
                criteria.industry, ["growth", "innovation", "competition"]
            )
            
            # Get industry trends
            industry_trends = self.grok_service.get_industry_trends(criteria.industry)
            
            # Get competitive intelligence
            competitive_intel = self.grok_service.get_competitive_intelligence(
                f"Company in {criteria.industry}", []
            )
            
            return {
                "market_sentiment": market_sentiment,
                "industry_trends": industry_trends,
                "competitive_intelligence": competitive_intel,
                "generation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Could not get market intelligence: {e}")
            return {
                "market_sentiment": {"sentiment": "neutral", "confidence": 0.5},
                "industry_trends": {"trends": []},
                "competitive_intelligence": {"competitors": []}
            }
    
    def _get_market_intelligence_summary(self, criteria: ProspectorCriteria) -> Dict[str, Any]:
        """Get market intelligence summary for results"""
        try:
            market_sentiment = self.grok_service.get_market_sentiment(
                criteria.industry, ["growth", "innovation"]
            )
            
            industry_trends = self.grok_service.get_industry_trends(criteria.industry)
            
            return {
                "industry": criteria.industry,
                "market_sentiment": market_sentiment.get("sentiment", "neutral"),
                "sentiment_confidence": market_sentiment.get("confidence", 0.5),
                "active_trends": len(industry_trends.get("trends", [])),
                "market_outlook": industry_trends.get("market_outlook", "stable"),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Could not get market intelligence summary: {e}")
            return {
                "industry": criteria.industry,
                "market_sentiment": "neutral",
                "sentiment_confidence": 0.5,
                "active_trends": 0,
                "market_outlook": "stable"
            }
    
    def _fallback_prospecting(self, prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Fallback to standard prospecting when adaptive fails"""
        logger.info("Using fallback prospecting method")
        
        try:
            criteria = self.parse_prompt(prompt, tenant_id, user_id)
            leads = self.generate_leads(criteria, tenant_id, user_id)
            csv_result = self.create_csv(leads)
            
            return {
                "success": True,
                "leads": leads,
                "csv_result": csv_result,
                "knowledge_level": "fallback",
                "strategy_used": "standard",
                "market_intelligence": {"status": "unavailable"},
                "adaptation_metadata": {"fallback": True}
            }
            
        except Exception as e:
            logger.error(f"Fallback prospecting failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "knowledge_level": "failed",
                "strategy_used": "none"
            }

class ProspectorAgent:
    """AI Prospector Agent for lead mining and targeting with company knowledge"""
    
    def __init__(self):
        self.tool = ProspectorTool()
        self.knowledge_service = KnowledgeService()
        self.name = "Scout"
        self.role = "Lead Mining & Targeting Specialist"
        self.goal = "Generate high-quality, targeted lead lists based on natural language prompts and company knowledge"
        self.backstory = """You are Scout, an advanced AI lead prospecting specialist with adaptive intelligence 
        and market research capabilities. You excel at understanding complex targeting requirements, leveraging 
        company knowledge, market intelligence, and industry trends to generate high-quality, market-aware lead data. 
        You adapt your strategy based on available knowledge sources and provide comprehensive market insights 
        alongside lead generation."""
    
    def prospect_leads(self, prompt: str, tenant_id: str = None, user_id: str = None, 
                     use_adaptive: bool = True) -> Dict[str, Any]:
        """Main method to prospect leads with adaptive intelligence"""
        logger.info(f"Starting lead prospecting with prompt: {prompt}")
        
        if use_adaptive:
            # Use enhanced adaptive prospecting
            result = self.tool.execute_adaptive(prompt, tenant_id, user_id)
        else:
            # Use standard prospecting
            result = self.tool.run(prompt, tenant_id, user_id)
        
        if result["success"]:
            lead_count = len(result.get("leads", []))
            logger.info(f"Prospecting completed: {lead_count} leads generated")
            
            # Log adaptive metadata if available
            if "strategy_used" in result:
                logger.info(f"Strategy used: {result['strategy_used']}")
                logger.info(f"Knowledge level: {result.get('knowledge_level', 'unknown')}")
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
