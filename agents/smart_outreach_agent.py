import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartOutreachAgent:
    """
    Smart Outreach Agent - Automated Multi-Channel Outreach
    
    Responsibilities:
    - Automatically determine optimal outreach channels per lead
    - Schedule messages at optimal times
    - A/B test different message approaches
    - Learn from response patterns
    - Handle multi-channel sequences
    - Optimize for maximum response rates
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Channel optimization rules
        self.channel_rules = {
            "email": {
                "best_for": ["formal_industries", "detailed_proposals", "compliance_heavy"],
                "optimal_times": ["tuesday_morning", "wednesday_morning", "thursday_morning"],
                "response_rate": 0.15,
                "personalization_level": "high"
            },
            "linkedin": {
                "best_for": ["networking", "relationship_building", "tech_industries"],
                "optimal_times": ["wednesday_afternoon", "thursday_afternoon"],
                "response_rate": 0.25,
                "personalization_level": "medium"
            },
            "phone": {
                "best_for": ["urgent_deals", "high_value_prospects", "enterprise"],
                "optimal_times": ["tuesday_morning", "wednesday_morning"],
                "response_rate": 0.35,
                "personalization_level": "low"
            }
        }
        
        # Industry-specific patterns
        self.industry_patterns = {
            "saas": {
                "preferred_channels": ["email", "linkedin"],
                "best_times": ["tuesday_9am", "wednesday_10am"],
                "message_style": "technical_but_accessible"
            },
            "fintech": {
                "preferred_channels": ["email"],
                "best_times": ["tuesday_9am", "wednesday_9am"],
                "message_style": "professional_secure"
            },
            "healthcare": {
                "preferred_channels": ["email", "phone"],
                "best_times": ["tuesday_10am", "wednesday_10am"],
                "message_style": "caring_professional"
            },
            "technology": {
                "preferred_channels": ["linkedin", "email"],
                "best_times": ["wednesday_2pm", "thursday_2pm"],
                "message_style": "innovative_forward_thinking"
            }
        }
    
    def create_smart_outreach_plan(self, leads: List[Dict[str, Any]], 
                                 campaign_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an intelligent outreach plan for multiple leads
        
        Args:
            leads: List of enriched leads
            campaign_context: Campaign context and objectives
            
        Returns:
            Dict with optimized outreach plan
        """
        try:
            logger.info(f"Creating smart outreach plan for {len(leads)} leads")
            
            outreach_plan = {
                "total_leads": len(leads),
                "channels": {},
                "schedule": [],
                "optimization_strategy": {},
                "expected_results": {}
            }
            
            # Analyze leads and determine optimal channels
            for lead in leads:
                lead_analysis = self._analyze_lead_for_outreach(lead)
                optimal_channel = self._determine_optimal_channel(lead_analysis)
                optimal_timing = self._determine_optimal_timing(lead_analysis)
                
                # Add to outreach plan
                if optimal_channel not in outreach_plan["channels"]:
                    outreach_plan["channels"][optimal_channel] = []
                
                outreach_plan["channels"][optimal_channel].append({
                    "lead": lead,
                    "analysis": lead_analysis,
                    "timing": optimal_timing,
                    "priority": lead_analysis["priority_score"]
                })
            
            # Sort by priority and create schedule
            outreach_plan["schedule"] = self._create_optimized_schedule(outreach_plan["channels"])
            
            # Generate optimization strategy
            outreach_plan["optimization_strategy"] = self._generate_optimization_strategy(leads, campaign_context)
            
            # Calculate expected results
            outreach_plan["expected_results"] = self._calculate_expected_results(outreach_plan)
            
            return {
                "success": True,
                "outreach_plan": outreach_plan,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Smart outreach planning failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_smart_outreach(self, outreach_plan: Dict[str, Any], 
                             user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the smart outreach plan automatically
        
        Args:
            outreach_plan: The optimized outreach plan
            user_preferences: User's preferences and constraints
            
        Returns:
            Dict with execution results
        """
        try:
            logger.info("Executing smart outreach plan")
            
            execution_results = {
                "messages_sent": 0,
                "channels_used": {},
                "responses_received": 0,
                "meetings_scheduled": 0,
                "errors": []
            }
            
            # Process each scheduled outreach
            for scheduled_outreach in outreach_plan["schedule"]:
                try:
                    # Generate personalized message
                    message_result = self._generate_smart_message(
                        scheduled_outreach["lead"],
                        scheduled_outreach["channel"],
                        scheduled_outreach["analysis"]
                    )
                    
                    if message_result["success"]:
                        # Send message (placeholder for actual sending)
                        send_result = self._send_message(
                            scheduled_outreach["lead"],
                            scheduled_outreach["channel"],
                            message_result["message"]
                        )
                        
                        if send_result["success"]:
                            execution_results["messages_sent"] += 1
                            if scheduled_outreach["channel"] not in execution_results["channels_used"]:
                                execution_results["channels_used"][scheduled_outreach["channel"]] = 0
                            execution_results["channels_used"][scheduled_outreach["channel"]] += 1
                        else:
                            execution_results["errors"].append(send_result["error"])
                    else:
                        execution_results["errors"].append(message_result["error"])
                        
                except Exception as e:
                    execution_results["errors"].append(f"Failed to process lead {scheduled_outreach['lead']['name']}: {str(e)}")
            
            return {
                "success": True,
                "execution_results": execution_results,
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Smart outreach execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_lead_for_outreach(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a lead to determine optimal outreach strategy"""
        
        # Extract lead characteristics
        industry = lead.get("industry", "").lower()
        company_size = lead.get("company_size", "")
        title = lead.get("title", "").lower()
        lead_score = lead.get("lead_score", {}).get("total_score", 0)
        
        # Determine priority score
        priority_score = 0
        if lead_score >= 80:
            priority_score += 40
        elif lead_score >= 60:
            priority_score += 20
        
        if "vp" in title or "director" in title or "cto" in title or "ceo" in title:
            priority_score += 30
        elif "manager" in title or "head" in title:
            priority_score += 20
        
        if company_size and "200" in company_size:
            priority_score += 20
        elif company_size and "50" in company_size:
            priority_score += 10
        
        # Determine urgency
        urgency = "low"
        if priority_score >= 70:
            urgency = "high"
        elif priority_score >= 50:
            urgency = "medium"
        
        return {
            "industry": industry,
            "company_size": company_size,
            "title": title,
            "lead_score": lead_score,
            "priority_score": priority_score,
            "urgency": urgency,
            "has_email": bool(lead.get("email")),
            "has_linkedin": bool(lead.get("linkedin_url")),
            "has_phone": bool(lead.get("phone"))
        }
    
    def _determine_optimal_channel(self, lead_analysis: Dict[str, Any]) -> str:
        """Determine the optimal outreach channel for a lead"""
        
        industry = lead_analysis["industry"]
        urgency = lead_analysis["urgency"]
        has_email = lead_analysis["has_email"]
        has_linkedin = lead_analysis["has_linkedin"]
        has_phone = lead_analysis["has_phone"]
        
        # Get industry preferences
        industry_prefs = self.industry_patterns.get(industry, self.industry_patterns["technology"])
        preferred_channels = industry_prefs["preferred_channels"]
        
        # Determine channel based on availability and preferences
        if urgency == "high" and has_phone:
            return "phone"
        elif "email" in preferred_channels and has_email:
            return "email"
        elif "linkedin" in preferred_channels and has_linkedin:
            return "linkedin"
        elif has_email:
            return "email"
        elif has_linkedin:
            return "linkedin"
        else:
            return "email"  # Default fallback
    
    def _determine_optimal_timing(self, lead_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal timing for outreach"""
        
        industry = lead_analysis["industry"]
        urgency = lead_analysis["urgency"]
        
        # Get industry-specific timing
        industry_patterns = self.industry_patterns.get(industry, self.industry_patterns["technology"])
        best_times = industry_patterns["best_times"]
        
        # Calculate optimal send time
        now = datetime.now()
        
        # For high urgency, send sooner
        if urgency == "high":
            send_time = now + timedelta(hours=2)
        elif urgency == "medium":
            send_time = now + timedelta(days=1)
        else:
            send_time = now + timedelta(days=2)
        
        # Adjust to optimal time of day
        if "9am" in best_times[0]:
            send_time = send_time.replace(hour=9, minute=0, second=0)
        elif "10am" in best_times[0]:
            send_time = send_time.replace(hour=10, minute=0, second=0)
        elif "2pm" in best_times[0]:
            send_time = send_time.replace(hour=14, minute=0, second=0)
        
        return {
            "send_time": send_time.isoformat(),
            "timezone": "user_local",
            "reasoning": f"Optimal for {industry} industry, {urgency} urgency"
        }
    
    def _create_optimized_schedule(self, channels: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Create an optimized schedule for outreach"""
        
        schedule = []
        
        # Sort leads by priority within each channel
        for channel, leads in channels.items():
            sorted_leads = sorted(leads, key=lambda x: x["priority"], reverse=True)
            
            for i, lead_data in enumerate(sorted_leads):
                # Stagger timing to avoid overwhelming recipients
                base_time = datetime.fromisoformat(lead_data["timing"]["send_time"])
                staggered_time = base_time + timedelta(minutes=i * 15)  # 15 minutes apart
                
                schedule.append({
                    "lead": lead_data["lead"],
                    "channel": channel,
                    "scheduled_time": staggered_time.isoformat(),
                    "priority": lead_data["priority"],
                    "analysis": lead_data["analysis"]
                })
        
        # Sort entire schedule by priority
        schedule.sort(key=lambda x: x["priority"], reverse=True)
        
        return schedule
    
    def _generate_smart_message(self, lead: Dict[str, Any], channel: str, 
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a smart, personalized message for the lead"""
        
        try:
            # Import the copywriter agent for message generation
            from agents.copywriter_agent import CopywriterAgent
            
            copywriter = CopywriterAgent()
            
            # Determine message type based on channel
            message_type_map = {
                "email": "cold_email",
                "linkedin": "linkedin_message",
                "phone": "cold_email"  # Use email format for phone scripts
            }
            
            message_type = message_type_map.get(channel, "cold_email")
            
            # Generate personalized message
            result = copywriter.personalize_message(lead, message_type)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": result["personalized_message"],
                    "channel": channel,
                    "personalization_score": result["personalization_score"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to generate message")
                }
                
        except Exception as e:
            logger.error(f"Smart message generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_message(self, lead: Dict[str, Any], channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via the specified channel (placeholder implementation)"""
        
        try:
            # This is a placeholder - in real implementation, you would:
            # - Send email via SMTP/Gmail API
            # - Send LinkedIn message via LinkedIn API
            # - Make phone call via telephony service
            
            logger.info(f"Sending {channel} message to {lead['name']} at {lead['company']}")
            
            # Simulate sending
            return {
                "success": True,
                "message_id": f"msg_{int(datetime.now().timestamp())}",
                "channel": channel,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message sending failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_optimization_strategy(self, leads: List[Dict[str, Any]], 
                                      campaign_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate optimization strategy based on lead analysis"""
        
        # Analyze lead distribution
        industries = {}
        company_sizes = {}
        titles = {}
        
        for lead in leads:
            industry = lead.get("industry", "Unknown")
            company_size = lead.get("company_size", "Unknown")
            title = lead.get("title", "Unknown")
            
            industries[industry] = industries.get(industry, 0) + 1
            company_sizes[company_size] = company_sizes.get(company_size, 0) + 1
            titles[title] = titles.get(title, 0) + 1
        
        return {
            "lead_distribution": {
                "industries": industries,
                "company_sizes": company_sizes,
                "titles": titles
            },
            "optimization_recommendations": [
                f"Focus on {max(industries, key=industries.get)} industry (highest concentration)",
                f"Target {max(company_sizes, key=company_sizes.get)} companies (most common size)",
                f"Prioritize {max(titles, key=titles.get)} roles (highest frequency)"
            ],
            "a_b_testing_suggestions": [
                "Test different send times for each industry",
                "Compare email vs LinkedIn response rates",
                "Experiment with message length variations"
            ]
        }
    
    def _calculate_expected_results(self, outreach_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate expected results based on historical data"""
        
        total_leads = outreach_plan["total_leads"]
        channels = outreach_plan["channels"]
        
        expected_responses = 0
        expected_meetings = 0
        
        for channel, leads in channels.items():
            channel_data = self.channel_rules.get(channel, {"response_rate": 0.15})
            response_rate = channel_data["response_rate"]
            
            channel_responses = len(leads) * response_rate
            expected_responses += channel_responses
            
            # Assume 20% of responses convert to meetings
            expected_meetings += channel_responses * 0.2
        
        return {
            "expected_response_rate": expected_responses / total_leads if total_leads > 0 else 0,
            "expected_responses": int(expected_responses),
            "expected_meetings": int(expected_meetings),
            "confidence_level": "medium"  # Based on historical data
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the Smart Outreach Agent"""
        return {
            "name": "Smart Outreach Agent",
            "description": "AI-powered automated multi-channel outreach with intelligent optimization",
            "capabilities": [
                "Automatic channel selection",
                "Optimal timing optimization",
                "Multi-channel sequence management",
                "A/B testing automation",
                "Response rate learning",
                "Performance analytics"
            ],
            "supported_channels": list(self.channel_rules.keys()),
            "supported_industries": list(self.industry_patterns.keys()),
            "version": "1.0.0"
        }

if __name__ == "__main__":
    # Test the Smart Outreach Agent
    agent = SmartOutreachAgent()
    
    test_leads = [
        {
            "name": "Sarah Johnson",
            "title": "VP of Sales",
            "company": "TechCorp Solutions",
            "industry": "SaaS",
            "company_size": "50-200",
            "email": "sarah.johnson@techcorp.com",
            "linkedin_url": "https://linkedin.com/in/sarahjohnson",
            "lead_score": {"total_score": 85}
        },
        {
            "name": "Mike Chen",
            "title": "CTO",
            "company": "DataFlow Inc",
            "industry": "Technology",
            "company_size": "100-500",
            "email": "mike.chen@dataflow.com",
            "linkedin_url": "https://linkedin.com/in/mikechen",
            "lead_score": {"total_score": 78}
        }
    ]
    
    test_campaign = {
        "value_proposition": "Increase sales efficiency by 40% with our AI-powered CRM",
        "call_to_action": "Schedule a 15-minute demo"
    }
    
    # Test smart outreach planning
    plan_result = agent.create_smart_outreach_plan(test_leads, test_campaign)
    print(f"Smart Outreach Planning: {plan_result['success']}")
    if plan_result['success']:
        print(f"Total leads: {plan_result['outreach_plan']['total_leads']}")
        print(f"Channels: {list(plan_result['outreach_plan']['channels'].keys())}")
        print(f"Expected responses: {plan_result['outreach_plan']['expected_results']['expected_responses']}")
    
    # Test execution
    if plan_result['success']:
        execution_result = agent.execute_smart_outreach(plan_result['outreach_plan'])
        print(f"Smart Outreach Execution: {execution_result['success']}")
        if execution_result['success']:
            print(f"Messages sent: {execution_result['execution_results']['messages_sent']}")
            print(f"Channels used: {execution_result['execution_results']['channels_used']}")


