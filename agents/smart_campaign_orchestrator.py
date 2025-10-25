import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from openai import OpenAI
from services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartCampaignOrchestrator:
    """
    Smart Campaign Pipeline Orchestrator
    
    Orchestrates the complete AI SDR workflow:
    Prompt → Prospector Agent → Enrichment Agent → Quality Gates → Campaign Ready
    
    Features:
    - Unified pipeline execution
    - Real-time progress tracking
    - Quality gates and lead filtering
    - AI-powered insights and recommendations
    - Smart campaign defaults
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.knowledge_service = KnowledgeService()
        self.pipeline_stages = [
            "prompt_analysis",
            "prospecting", 
            "enrichment",
            "quality_gates",
            "campaign_creation"
        ]
        
    def analyze_prompt(self, user_prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Analyze user prompt to extract targeting criteria and generate smart defaults with company knowledge
        
        Args:
            user_prompt: User's natural language prompt
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Dict with analyzed criteria and smart defaults
        """
        try:
            # Get company knowledge for enhanced analysis
            company_context = ""
            target_audience = {}
            value_propositions = []
            if tenant_id and user_id:
                company_context = self.knowledge_service.get_company_context(tenant_id, user_id, task_type="campaign")
                target_audience = self.knowledge_service.get_target_audience(tenant_id, user_id, task_type="campaign")
                value_propositions = self.knowledge_service.get_value_propositions(tenant_id, user_id, task_type="campaign")
            
            analysis_prompt = f"""
            Analyze this B2B prospecting prompt and extract key information:
            
            User Prompt: "{user_prompt}"
            
            {f"Company Context: {company_context}" if company_context else ""}
            {f"Target Audience: {target_audience}" if target_audience else ""}
            {f"Value Propositions: {value_propositions}" if value_propositions else ""}
            
            Extract and return a JSON response with:
            - target_role: Primary job title/role
            - industry: Industry/sector
            - company_size: Company size range (e.g., "10-50", "50-200", "200-1000", "1000+")
            - location: Geographic location
            - count: Number of leads requested (default to 10 if not specified)
            - additional_filters: Any other criteria mentioned
            - campaign_name: Suggested campaign name
            - target_audience: Suggested target audience description
            - value_proposition: Suggested value proposition for this audience
            - call_to_action: Suggested call-to-action
            
            {f"Use the company's target audience and value propositions to enhance the analysis." if company_context else ""}
            Be realistic and conservative in your estimates.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # Fallback analysis with company knowledge
                fallback_target_audience = target_audience.get('industry', 'Technology') + ' decision makers' if target_audience else "Technology decision makers"
                fallback_value_prop = value_propositions[0] if value_propositions else "Streamline your operations with our innovative solution"
                
                analysis = {
                    "target_role": "Decision Maker",
                    "industry": target_audience.get('industry', 'Technology') if target_audience else "Technology",
                    "company_size": target_audience.get('company_size', '50-200') if target_audience else "50-200",
                    "location": "United States",
                    "count": 10,
                    "additional_filters": None,
                    "campaign_name": f"AI Generated Campaign - {datetime.now().strftime('%Y%m%d')}",
                    "target_audience": fallback_target_audience,
                    "value_proposition": fallback_value_prop,
                    "call_to_action": "Schedule a brief call to discuss how we can help"
                }
            
            return {
                "success": True,
                "analysis": analysis,
                "original_prompt": user_prompt
            }
            
        except Exception as e:
            logger.error(f"Prompt analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    def execute_prospector_stage(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Prospector Agent stage
        
        Args:
            criteria: Analyzed criteria from prompt analysis
            
        Returns:
            Dict with prospecting results
        """
        try:
            from agents.prospector_agent import ProspectorAgent
            
            # Create prospector prompt from criteria
            prospector_prompt = f"Find me {criteria['count']} {criteria['target_role']}s in {criteria['industry']} industry"
            if criteria.get('location'):
                prospector_prompt += f" located in {criteria['location']}"
            if criteria.get('company_size'):
                prospector_prompt += f" with {criteria['company_size']} employees"
            
            logger.info(f"Executing prospector stage with prompt: {prospector_prompt}")
            
            agent = ProspectorAgent()
            result = agent.prospect_leads(prospector_prompt)
            
            if result["success"]:
                return {
                    "success": True,
                    "stage": "prospecting",
                    "leads": result["leads"],
                    "criteria": result["criteria"],
                    "message": f"Found {len(result['leads'])} prospects"
                }
            else:
                return {
                    "success": False,
                    "stage": "prospecting",
                    "error": result.get("error", "Prospecting failed"),
                    "leads": []
                }
                
        except Exception as e:
            logger.error(f"Prospector stage failed: {e}")
            return {
                "success": False,
                "stage": "prospecting",
                "error": str(e),
                "leads": []
            }
    
    def execute_enrichment_stage(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the Enrichment Agent stage
        
        Args:
            leads: Leads from prospector stage
            
        Returns:
            Dict with enrichment results
        """
        try:
            from agents.enrichment_agent import EnrichmentAgent
            
            logger.info(f"Executing enrichment stage for {len(leads)} leads")
            
            agent = EnrichmentAgent()
            result = agent.enrich_leads(leads)
            
            if result["success"]:
                return {
                    "success": True,
                    "stage": "enrichment",
                    "enriched_leads": result["enriched_leads"],
                    "stats": result["stats"],
                    "message": f"Enriched {len(result['enriched_leads'])} leads"
                }
            else:
                return {
                    "success": False,
                    "stage": "enrichment",
                    "error": result.get("error", "Enrichment failed"),
                    "enriched_leads": []
                }
                
        except Exception as e:
            logger.error(f"Enrichment stage failed: {e}")
            return {
                "success": False,
                "stage": "enrichment",
                "error": str(e),
                "enriched_leads": []
            }
    
    def apply_quality_gates(self, enriched_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply quality gates to filter and categorize leads
        
        Args:
            enriched_leads: Enriched leads from enrichment stage
            
        Returns:
            Dict with quality-gated leads
        """
        try:
            premium_leads = []
            backup_leads = []
            excluded_leads = []
            
            for lead in enriched_leads:
                score = lead.get('lead_score', {})
                grade = score.get('grade', 'F')
                total_score = score.get('total_score', 0)
                
                if grade in ['A', 'B'] and total_score >= 80:
                    premium_leads.append(lead)
                elif grade in ['C', 'D'] and total_score >= 60:
                    backup_leads.append(lead)
                else:
                    excluded_leads.append(lead)
            
            # Generate insights
            insights = self._generate_insights(enriched_leads, premium_leads, backup_leads, excluded_leads)
            
            return {
                "success": True,
                "stage": "quality_gates",
                "premium_leads": premium_leads,
                "backup_leads": backup_leads,
                "excluded_leads": excluded_leads,
                "insights": insights,
                "message": f"Quality gates applied: {len(premium_leads)} premium, {len(backup_leads)} backup, {len(excluded_leads)} excluded"
            }
            
        except Exception as e:
            logger.error(f"Quality gates failed: {e}")
            return {
                "success": False,
                "stage": "quality_gates",
                "error": str(e),
                "premium_leads": [],
                "backup_leads": [],
                "excluded_leads": []
            }
    
    def _generate_insights(self, all_leads: List[Dict[str, Any]], premium: List[Dict[str, Any]], 
                         backup: List[Dict[str, Any]], excluded: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations"""
        try:
            total_leads = len(all_leads)
            premium_rate = (len(premium) / total_leads * 100) if total_leads > 0 else 0
            backup_rate = (len(backup) / total_leads * 100) if total_leads > 0 else 0
            
            # Analyze common issues
            common_issues = []
            if len(excluded) > 0:
                common_issues.append(f"{len(excluded)} leads excluded due to poor data quality")
            
            # Check for missing data patterns
            missing_linkedin = sum(1 for lead in all_leads if not lead.get('linkedin_validation', {}).get('valid', False))
            missing_phone = sum(1 for lead in all_leads if not lead.get('phone_validation', {}).get('valid', False))
            
            if missing_linkedin > total_leads * 0.5:
                common_issues.append(f"{missing_linkedin} leads missing valid LinkedIn profiles")
            if missing_phone > total_leads * 0.5:
                common_issues.append(f"{missing_phone} leads missing phone numbers")
            
            # Generate recommendations
            recommendations = []
            if premium_rate < 50:
                recommendations.append("Consider refining targeting criteria for higher quality leads")
            if missing_linkedin > 0:
                recommendations.append("Add LinkedIn profile requirements to improve lead quality")
            if missing_phone > 0:
                recommendations.append("Include phone number validation for better contact success")
            
            return {
                "total_leads": total_leads,
                "premium_rate": round(premium_rate, 1),
                "backup_rate": round(backup_rate, 1),
                "common_issues": common_issues,
                "recommendations": recommendations,
                "quality_summary": f"{len(premium)} premium leads ready for immediate outreach, {len(backup)} backup leads for follow-up"
            }
            
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            return {
                "total_leads": len(all_leads),
                "premium_rate": 0,
                "backup_rate": 0,
                "common_issues": [],
                "recommendations": [],
                "quality_summary": "Unable to generate insights"
            }
    
    def create_campaign_data(self, analysis: Dict[str, Any], premium_leads: List[Dict[str, Any]], 
                           backup_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create campaign data with smart defaults
        
        Args:
            analysis: Original prompt analysis
            premium_leads: High-quality leads
            backup_leads: Backup leads
            
        Returns:
            Dict with campaign data
        """
        try:
            campaign_data = {
                "name": analysis.get("campaign_name", f"Smart Campaign - {datetime.now().strftime('%Y%m%d_%H%M')}"),
                "description": f"AI-generated campaign targeting {analysis.get('target_role', 'decision makers')} in {analysis.get('industry', 'technology')}",
                "target_audience": analysis.get("target_audience", "Technology decision makers"),
                "value_proposition": analysis.get("value_proposition", "Streamline your operations with our innovative solution"),
                "call_to_action": analysis.get("call_to_action", "Schedule a brief call to discuss how we can help"),
                "status": "draft",
                "created_at": datetime.utcnow().isoformat(),
                "lead_count": len(premium_leads) + len(backup_leads),
                "premium_leads": len(premium_leads),
                "backup_leads": len(backup_leads)
            }
            
            return {
                "success": True,
                "stage": "campaign_creation",
                "campaign_data": campaign_data,
                "message": f"Campaign '{campaign_data['name']}' created with {campaign_data['lead_count']} leads"
            }
            
        except Exception as e:
            logger.error(f"Campaign creation failed: {e}")
            return {
                "success": False,
                "stage": "campaign_creation",
                "error": str(e),
                "campaign_data": None
            }
    
    def execute_smart_campaign(self, user_prompt: str, tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Execute the complete Smart Campaign pipeline with company knowledge
        
        Args:
            user_prompt: User's natural language prompt
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Dict with complete pipeline results
        """
        logger.info(f"Starting Smart Campaign pipeline with prompt: {user_prompt}")
        
        pipeline_results = {
            "success": False,
            "pipeline_id": f"smart_campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_prompt": user_prompt,
            "stages": {},
            "final_results": {},
            "execution_time": 0,
            "error": None
        }
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Prompt Analysis
            logger.info("Stage 1: Analyzing prompt...")
            analysis_result = self.analyze_prompt(user_prompt, tenant_id, user_id)
            pipeline_results["stages"]["prompt_analysis"] = analysis_result
            
            if not analysis_result["success"]:
                pipeline_results["error"] = f"Prompt analysis failed: {analysis_result['error']}"
                return pipeline_results
            
            criteria = analysis_result["analysis"]
            
            # Stage 2: Prospecting
            logger.info("Stage 2: Executing prospector agent...")
            prospector_result = self.execute_prospector_stage(criteria)
            pipeline_results["stages"]["prospecting"] = prospector_result
            
            if not prospector_result["success"]:
                pipeline_results["error"] = f"Prospecting failed: {prospector_result['error']}"
                return pipeline_results
            
            leads = prospector_result["leads"]
            
            # Stage 3: Enrichment
            logger.info("Stage 3: Executing enrichment agent...")
            enrichment_result = self.execute_enrichment_stage(leads)
            pipeline_results["stages"]["enrichment"] = enrichment_result
            
            if not enrichment_result["success"]:
                pipeline_results["error"] = f"Enrichment failed: {enrichment_result['error']}"
                return pipeline_results
            
            enriched_leads = enrichment_result["enriched_leads"]
            
            # Stage 4: Quality Gates
            logger.info("Stage 4: Applying quality gates...")
            quality_result = self.apply_quality_gates(enriched_leads)
            pipeline_results["stages"]["quality_gates"] = quality_result
            
            if not quality_result["success"]:
                pipeline_results["error"] = f"Quality gates failed: {quality_result['error']}"
                return pipeline_results
            
            # Stage 5: Campaign Creation
            logger.info("Stage 5: Creating campaign...")
            campaign_result = self.create_campaign_data(
                criteria, 
                quality_result["premium_leads"], 
                quality_result["backup_leads"]
            )
            pipeline_results["stages"]["campaign_creation"] = campaign_result
            
            if not campaign_result["success"]:
                pipeline_results["error"] = f"Campaign creation failed: {campaign_result['error']}"
                return pipeline_results
            
            # Compile final results
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            pipeline_results.update({
                "success": True,
                "execution_time": execution_time,
                "final_results": {
                    "campaign_data": campaign_result["campaign_data"],
                    "premium_leads": quality_result["premium_leads"],
                    "backup_leads": quality_result["backup_leads"],
                    "excluded_leads": quality_result["excluded_leads"],
                    "insights": quality_result["insights"],
                    "enrichment_stats": enrichment_result["stats"]
                }
            })
            
            logger.info(f"Smart Campaign pipeline completed successfully in {execution_time:.1f} seconds")
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Smart Campaign pipeline failed: {e}")
            pipeline_results["error"] = str(e)
            pipeline_results["execution_time"] = (datetime.now() - start_time).total_seconds()
            return pipeline_results

if __name__ == "__main__":
    # Test the Smart Campaign Orchestrator
    orchestrator = SmartCampaignOrchestrator()
    
    test_prompt = "Find me 5 SaaS CTOs in San Francisco with 50-200 employees"
    result = orchestrator.execute_smart_campaign(test_prompt)
    
    print(f"Pipeline Success: {result['success']}")
    print(f"Execution Time: {result['execution_time']:.1f} seconds")
    if result['success']:
        print(f"Campaign: {result['final_results']['campaign_data']['name']}")
        print(f"Premium Leads: {len(result['final_results']['premium_leads'])}")
        print(f"Backup Leads: {len(result['final_results']['backup_leads'])}")
        print(f"Insights: {result['final_results']['insights']['quality_summary']}")
    else:
        print(f"Error: {result['error']}")


