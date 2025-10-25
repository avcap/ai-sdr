import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from services.knowledge_service import KnowledgeService
from services.knowledge_fusion_service import KnowledgeFusionService
from services.llm_selector_service import LLMSelectorService
from agents.adaptive_ai_agent import AdaptiveAIAgent, KnowledgeLevel, AdaptationStrategy
from integrations.grok_service import GrokService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CopywriterAgent:
    """
    Copywriter Agent - Personalization & Sequence Creation
    
    Responsibilities:
    - Generate personalized outreach messages
    - Create multi-touch email sequences
    - Adapt messaging to different channels (Email, LinkedIn)
    - Personalize based on lead data and company context
    - A/B test different message variations
    - Optimize for different industries and roles
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.knowledge_service = KnowledgeService()
        
        # Phase 3: Enhanced services
        self.knowledge_fusion = KnowledgeFusionService()
        self.llm_selector = LLMSelectorService()
        self.adaptive_agent = AdaptiveAIAgent()
        self.grok_service = GrokService()
        
        # Message templates and frameworks
        self.message_frameworks = {
            "cold_email": {
                "structure": ["hook", "problem", "solution", "social_proof", "cta"],
                "tone": "professional_yet_personal",
                "length": "concise"
            },
            "linkedin_message": {
                "structure": ["connection", "value_proposition", "soft_cta"],
                "tone": "conversational",
                "length": "very_short"
            },
            "follow_up": {
                "structure": ["reference", "additional_value", "urgency", "cta"],
                "tone": "helpful",
                "length": "brief"
            }
        }
        
        # Industry-specific messaging
        self.industry_contexts = {
            "saas": {
                "pain_points": ["inefficient processes", "manual workflows", "scaling challenges"],
                "benefits": ["automation", "efficiency", "growth"],
                "language": "technical_but_accessible"
            },
            "fintech": {
                "pain_points": ["compliance", "security", "integration"],
                "benefits": ["security", "compliance", "efficiency"],
                "language": "professional_secure"
            },
            "healthcare": {
                "pain_points": ["patient care", "compliance", "efficiency"],
                "benefits": ["patient_outcomes", "compliance", "efficiency"],
                "language": "caring_professional"
            },
            "technology": {
                "pain_points": ["innovation", "scaling", "competition"],
                "benefits": ["innovation", "competitive_advantage", "growth"],
                "language": "innovative_forward_thinking"
            }
        }
    
    def personalize_message(self, lead_data: Dict[str, Any], message_type: str = "cold_email", 
                          campaign_context: Dict[str, Any] = None, user_template: str = None,
                          tenant_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Generate a personalized message for a specific lead with company knowledge
        
        Args:
            lead_data: Lead information (name, company, title, industry, etc.)
            message_type: Type of message (cold_email, linkedin_message, follow_up)
            campaign_context: Campaign context (value_proposition, call_to_action, etc.)
            user_template: User-provided template for personalization
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Dict with personalized message and metadata
        """
        try:
            logger.info(f"Generating personalized {message_type} for {lead_data.get('name', 'Unknown')}")
            
            # Get company knowledge for enhanced personalization
            company_context = ""
            products = []
            value_propositions = []
            sales_approach = ""
            competitive_advantages = []
            
            if tenant_id and user_id:
                company_context = self.knowledge_service.get_company_context(tenant_id, user_id, task_type="copywriting")
                products = self.knowledge_service.get_products(tenant_id, user_id, task_type="copywriting")
                value_propositions = self.knowledge_service.get_value_propositions(tenant_id, user_id, task_type="copywriting")
                sales_approach = self.knowledge_service.get_sales_approach(tenant_id, user_id, task_type="copywriting")
                competitive_advantages = self.knowledge_service.get_competitive_advantages(tenant_id, user_id, task_type="copywriting")
            
            # Extract lead context
            lead_context = self._extract_lead_context(lead_data)
            industry_context = self._get_industry_context(lead_data.get('industry', '').lower())
            
            # If user provided a template, use it for personalization
            if user_template:
                personalization_prompt = self._build_template_personalization_prompt(
                    lead_context, industry_context, user_template, campaign_context,
                    company_context, products, value_propositions, sales_approach, competitive_advantages
                )
            else:
                # Build personalization prompt with company knowledge
                personalization_prompt = self._build_personalization_prompt(
                    lead_context, industry_context, message_type, campaign_context,
                    company_context, products, value_propositions, sales_approach, competitive_advantages
                )
            
            # Generate personalized message
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": personalization_prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            message_content = response.choices[0].message.content.strip()
            
            # Parse and structure the response
            personalized_message = self._parse_message_response(message_content, message_type)
            
            return {
                "success": True,
                "message_type": message_type,
                "personalized_message": personalized_message,
                "lead_context": lead_context,
                "industry_context": industry_context,
                "personalization_score": self._calculate_personalization_score(lead_context),
                "message_length": len(message_content),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message personalization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_type": message_type
            }
    
    def create_email_sequence(self, lead_data: Dict[str, Any], 
                            campaign_context: Dict[str, Any] = None,
                            sequence_length: int = 3) -> Dict[str, Any]:
        """
        Create a multi-touch email sequence for a lead
        
        Args:
            lead_data: Lead information
            campaign_context: Campaign context
            sequence_length: Number of emails in sequence (default 3)
            
        Returns:
            Dict with complete email sequence
        """
        try:
            logger.info(f"Creating {sequence_length}-email sequence for {lead_data.get('name', 'Unknown')}")
            
            sequence_prompt = self._build_sequence_prompt(lead_data, campaign_context, sequence_length)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": sequence_prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            sequence_content = response.choices[0].message.content.strip()
            
            # Parse sequence into structured emails
            email_sequence = self._parse_sequence_response(sequence_content, sequence_length)
            
            return {
                "success": True,
                "sequence_length": sequence_length,
                "email_sequence": email_sequence,
                "lead_context": self._extract_lead_context(lead_data),
                "campaign_context": campaign_context,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sequence creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sequence_length": sequence_length
            }
    
    def generate_message_variations(self, lead_data: Dict[str, Any], 
                                  message_type: str = "cold_email",
                                  num_variations: int = 3) -> Dict[str, Any]:
        """
        Generate multiple message variations for A/B testing
        
        Args:
            lead_data: Lead information
            message_type: Type of message
            num_variations: Number of variations to generate
            
        Returns:
            Dict with message variations
        """
        try:
            logger.info(f"Generating {num_variations} {message_type} variations for {lead_data.get('name', 'Unknown')}")
            
            variations = []
            for i in range(num_variations):
                # Vary the temperature for different styles
                temperature = 0.5 + (i * 0.3)  # 0.5, 0.8, 1.1
                
                variation_result = self.personalize_message(lead_data, message_type)
                if variation_result["success"]:
                    variation_result["variation_id"] = i + 1
                    variation_result["style"] = self._get_variation_style(i)
                    variations.append(variation_result)
            
            return {
                "success": True,
                "message_type": message_type,
                "variations": variations,
                "num_variations": len(variations),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message variation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_type": message_type
            }
    
    def _extract_lead_context(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from lead data for personalization"""
        return {
            "name": lead_data.get("name", ""),
            "title": lead_data.get("title", ""),
            "company": lead_data.get("company", ""),
            "industry": lead_data.get("industry", ""),
            "company_size": lead_data.get("company_size", ""),
            "location": lead_data.get("location", ""),
            "email": lead_data.get("email", ""),
            "linkedin_url": lead_data.get("linkedin_url", ""),
            "phone": lead_data.get("phone", ""),
            "lead_score": lead_data.get("lead_score", {}),
            "validation_status": {
                "email_valid": lead_data.get("email_validation", {}).get("valid", False),
                "phone_valid": lead_data.get("phone_validation", {}).get("valid", False),
                "linkedin_valid": lead_data.get("linkedin_validation", {}).get("valid", False)
            }
        }
    
    def _get_industry_context(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific context for messaging"""
        industry_key = industry.lower()
        for key, context in self.industry_contexts.items():
            if key in industry_key or industry_key in key:
                return context
        return self.industry_contexts["technology"]  # Default fallback
    
    def _build_personalization_prompt(self, lead_context: Dict[str, Any], 
                                    industry_context: Dict[str, Any],
                                    message_type: str, 
                                    campaign_context: Dict[str, Any] = None,
                                    company_context: str = "",
                                    products: List[Dict[str, Any]] = None,
                                    value_propositions: List[str] = None,
                                    sales_approach: str = "",
                                    competitive_advantages: List[str] = None) -> str:
        """Build the personalization prompt for OpenAI with company knowledge"""
        
        framework = self.message_frameworks.get(message_type, self.message_frameworks["cold_email"])
        
        # Format company knowledge
        company_section = ""
        if company_context:
            company_section = f"""
        
        COMPANY CONTEXT:
        {company_context}
        """
        
        products_section = ""
        if products:
            products_list = "\n".join([f"- {p.get('name', 'Product')}: {p.get('description', 'No description')}" for p in products])
            products_section = f"""
        
        PRODUCTS/SERVICES:
        {products_list}
        """
        
        value_props_section = ""
        if value_propositions:
            value_props_list = "\n".join([f"- {vp}" for vp in value_propositions])
            value_props_section = f"""
        
        VALUE PROPOSITIONS:
        {value_props_list}
        """
        
        sales_approach_section = ""
        if sales_approach:
            sales_approach_section = f"""
        
        SALES APPROACH:
        {sales_approach}
        """
        
        competitive_advantages_section = ""
        if competitive_advantages:
            comp_adv_list = "\n".join([f"- {ca}" for ca in competitive_advantages])
            competitive_advantages_section = f"""
        
        COMPETITIVE ADVANTAGES:
        {comp_adv_list}
        """
        
        prompt = f"""
        You are an expert B2B copywriter who writes like a professional human. Create a personalized {message_type} message.
        
        LEAD CONTEXT:
        - Name: {lead_context['name']}
        - Title: {lead_context['title']}
        - Company: {lead_context['company']}
        - Industry: {lead_context['industry']}
        - Company Size: {lead_context['company_size']}
        - Location: {lead_context['location']}
        
        INDUSTRY CONTEXT:
        - Pain Points: {', '.join(industry_context['pain_points'])}
        - Benefits: {', '.join(industry_context['benefits'])}
        - Language Style: {industry_context['language']}
        
        {company_section}
        {products_section}
        {value_props_section}
        {sales_approach_section}
        {competitive_advantages_section}
        
        MESSAGE FRAMEWORK:
        - Structure: {', '.join(framework['structure'])}
        - Tone: {framework['tone']}
        - Length: {framework['length']}
        
        WRITING STYLE REQUIREMENTS:
        - Write like a professional human, not a robot
        - Use proper sentence spacing and natural paragraph breaks
        - NO emojis or special characters (no --, no bullet points, no symbols)
        - Use proper punctuation and capitalization
        - Write in a conversational yet professional tone
        - Use natural transitions between ideas
        - Keep sentences varied in length for readability
        - Use active voice when possible
        - Avoid corporate jargon and buzzwords
        - Make it sound personal and authentic
        """
        
        if campaign_context:
            prompt += f"""
        
        CAMPAIGN CONTEXT:
        - Value Proposition: {campaign_context.get('value_proposition', 'Not specified')}
        - Call to Action: {campaign_context.get('call_to_action', 'Not specified')}
        - Target Audience: {campaign_context.get('target_audience', 'Not specified')}
        """
        
        prompt += f"""
        
        REQUIREMENTS:
        1. Use the lead's name and company naturally in the opening
        2. Reference their industry and role-specific challenges
        3. Include a clear value proposition without buzzwords
        4. End with a specific, low-pressure call to action
        5. Keep it {framework['length']} and {framework['tone']}
        6. Make it feel personal, not templated
        7. Write in proper business email format with natural spacing
        8. Use professional language that builds trust
        9. Avoid any symbols, emojis, or special formatting
        10. Make each sentence flow naturally into the next
        
        Generate the {message_type} message with proper formatting:
        """
        
        return prompt
    
    def _build_template_personalization_prompt(self, lead_context: Dict[str, Any], 
                                             industry_context: Dict[str, Any],
                                             user_template: str,
                                             campaign_context: Dict[str, Any] = None) -> str:
        """Build a personalization prompt based on user-provided template"""
        
        prompt = f"""
        You are an expert B2B copywriter who personalizes user-provided templates. 
        Take the user's template and personalize it with specific lead information.
        
        LEAD CONTEXT:
        - Name: {lead_context['name']}
        - Title: {lead_context['title']}
        - Company: {lead_context['company']}
        - Industry: {lead_context['industry']}
        - Company Size: {lead_context['company_size']}
        - Location: {lead_context['location']}
        
        INDUSTRY CONTEXT:
        - Pain Points: {', '.join(industry_context['pain_points'])}
        - Benefits: {', '.join(industry_context['benefits'])}
        - Language Style: {industry_context['language']}
        
        USER TEMPLATE:
        {user_template}
        
        PERSONALIZATION REQUIREMENTS:
        - Replace generic placeholders with specific lead information
        - Use the lead's name and company naturally
        - Reference their industry and role-specific challenges
        - Maintain the user's original tone and structure
        - Keep it professional and human-like
        - Use proper sentence spacing and natural paragraph breaks
        - NO emojis or special characters (no --, no bullet points, no symbols)
        - Use proper punctuation and capitalization
        - Make it sound personal and authentic
        
        Generate the personalized message:
        """
        
        if campaign_context:
            prompt += f"""
        
        CAMPAIGN CONTEXT:
        - Value Proposition: {campaign_context.get('value_proposition', 'Not specified')}
        - Call to Action: {campaign_context.get('call_to_action', 'Not specified')}
        - Target Audience: {campaign_context.get('target_audience', 'Not specified')}
        """
        
        return prompt
    
    def _build_sequence_prompt(self, lead_data: Dict[str, Any], 
                             campaign_context: Dict[str, Any] = None,
                             sequence_length: int = 3) -> str:
        """Build prompt for email sequence creation"""
        
        lead_context = self._extract_lead_context(lead_data)
        industry_context = self._get_industry_context(lead_data.get('industry', '').lower())
        
        prompt = f"""
        Create a {sequence_length}-email sequence for B2B outreach.
        
        LEAD: {lead_context['name']} - {lead_context['title']} at {lead_context['company']}
        INDUSTRY: {lead_context['industry']} ({', '.join(industry_context['pain_points'])})
        
        EMAIL SEQUENCE STRUCTURE:
        Email 1: Cold introduction with value proposition
        Email 2: Social proof and case study
        Email 3: Urgency and final call to action
        
        Each email should:
        - Be personalized to the lead
        - Build on the previous email
        - Provide increasing value
        - Have a clear, specific CTA
        - Be concise (under 150 words)
        
        Format as JSON with subject lines and body content.
        """
        
        if campaign_context:
            prompt += f"""
        
        CAMPAIGN CONTEXT:
        - Value Prop: {campaign_context.get('value_proposition', 'Not specified')}
        - CTA: {campaign_context.get('call_to_action', 'Not specified')}
        """
        
        return prompt
    
    def _parse_message_response(self, content: str, message_type: str) -> Dict[str, Any]:
        """Parse the AI response into structured message format"""
        return {
            "subject": self._extract_subject(content),
            "body": content,
            "call_to_action": self._extract_cta(content),
            "personalization_elements": self._identify_personalization(content),
            "message_type": message_type
        }
    
    def _parse_sequence_response(self, content: str, sequence_length: int) -> List[Dict[str, Any]]:
        """Parse sequence response into structured email list"""
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                parsed = json.loads(content)
                return parsed.get('emails', [])
        except:
            pass
        
        # Fallback: parse manually
        emails = []
        lines = content.split('\n')
        current_email = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Email') or line.startswith('Subject:'):
                if current_email:
                    emails.append(current_email)
                current_email = {"subject": "", "body": ""}
                if line.startswith('Subject:'):
                    current_email["subject"] = line.replace('Subject:', '').strip()
            elif line and current_email:
                if not current_email["subject"]:
                    current_email["subject"] = line
                else:
                    current_email["body"] += line + "\n"
        
        if current_email:
            emails.append(current_email)
        
        return emails[:sequence_length]
    
    def _extract_subject(self, content: str) -> str:
        """Extract subject line from message content"""
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('Subject:') or line.strip().startswith('Re:'):
                return line.strip()
        return "Quick question about your business"
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from message content"""
        # Look for common CTA patterns
        cta_patterns = [
            "schedule a call", "book a meeting", "set up a demo",
            "let's connect", "would you be interested", "are you available"
        ]
        
        content_lower = content.lower()
        for pattern in cta_patterns:
            if pattern in content_lower:
                return pattern.title()
        
        return "Schedule a brief call"
    
    def _identify_personalization(self, content: str) -> List[str]:
        """Identify personalization elements in the message"""
        personalization_elements = []
        
        if "{name}" in content or any(name in content for name in ["Mr.", "Ms.", "Dear"]):
            personalization_elements.append("name")
        
        if any(company_word in content.lower() for company_word in ["company", "organization", "team"]):
            personalization_elements.append("company")
        
        if any(role_word in content.lower() for role_word in ["role", "position", "title"]):
            personalization_elements.append("role")
        
        if any(industry_word in content.lower() for industry_word in ["industry", "sector", "market"]):
            personalization_elements.append("industry")
        
        return personalization_elements
    
    def _calculate_personalization_score(self, lead_context: Dict[str, Any]) -> int:
        """Calculate personalization score based on available data"""
        score = 0
        
        if lead_context["name"]:
            score += 20
        if lead_context["company"]:
            score += 20
        if lead_context["title"]:
            score += 15
        if lead_context["industry"]:
            score += 15
        if lead_context["company_size"]:
            score += 10
        if lead_context["location"]:
            score += 10
        if lead_context["linkedin_url"]:
            score += 10
        
        return min(score, 100)
    
    def execute_adaptive(self, prompt: str, lead_data: Dict[str, Any], 
                       message_type: str = "cold_email", tenant_id: str = None, 
                       user_id: str = None) -> Dict[str, Any]:
        """
        Phase 3: Adaptive copywriting execution based on knowledge level and market context.
        
        Args:
            prompt: User's campaign prompt
            lead_data: Lead information for personalization
            message_type: Type of message to generate
            tenant_id: Organization identifier
            user_id: User identifier
            
        Returns:
            Enhanced message generation result with adaptive intelligence
        """
        logger.info(f"Executing adaptive copywriting for {message_type}")
        
        try:
            # 1. Assess knowledge level
            assessment = self.adaptive_agent.assess_knowledge_level(tenant_id, user_id, prompt)
            logger.info(f"Knowledge level: {assessment.level.value}")
            
            # 2. Select adaptation strategy
            strategy_plan = self.adaptive_agent.select_adaptation_strategy(assessment.level, "copywriting")
            logger.info(f"Selected strategy: {strategy_plan.strategy.value}")
            
            # 3. Execute with strategy
            execution_result = self.adaptive_agent.execute_with_strategy(
                strategy_plan.strategy,
                prompt,
                {"task_type": "copywriting", "message_type": message_type, "lead_data": lead_data},
                tenant_id,
                user_id
            )
            
            # 4. Enhance with market intelligence
            market_context = self._get_market_context_for_copywriting(lead_data, prompt)
            
            # 5. Generate adaptive message
            adaptive_result = self._generate_adaptive_message(
                lead_data, message_type, execution_result, market_context, strategy_plan
            )
            
            return {
                "success": True,
                "message": adaptive_result["message"],
                "personalization_score": adaptive_result["personalization_score"],
                "market_awareness_score": adaptive_result["market_awareness_score"],
                "strategy_used": strategy_plan.strategy.value,
                "knowledge_level": assessment.level.value,
                "confidence_score": execution_result.get("strategy_metadata", {}).get("fused_overall_score", 0.0),
                "adaptive_metadata": {
                    "assessment": assessment,
                    "strategy_plan": strategy_plan,
                    "market_context": market_context,
                    "execution_result": execution_result
                }
            }
            
        except Exception as e:
            logger.error(f"Adaptive copywriting failed: {e}")
            # Fallback to standard personalization
            return self.personalize_message(lead_data, message_type)
    
    def _get_market_context_for_copywriting(self, lead_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Get market context for copywriting enhancement"""
        try:
            industry = lead_data.get("industry", "general")
            company = lead_data.get("company", "")
            
            # Get market sentiment and trends
            market_sentiment = self.grok_service.get_market_sentiment(industry, ["growth", "challenges"])
            industry_trends = self.grok_service.get_industry_trends(industry, "6months")
            
            # Get competitive intelligence if company is specified
            competitive_context = {}
            if company:
                competitive_context = self.grok_service.get_competitive_intelligence(company)
            
            return {
                "market_sentiment": market_sentiment,
                "industry_trends": industry_trends,
                "competitive_context": competitive_context,
                "industry": industry,
                "company": company
            }
            
        except Exception as e:
            logger.warning(f"Failed to get market context: {e}")
            return {"industry": lead_data.get("industry", "general")}
    
    def _generate_adaptive_message(self, lead_data: Dict[str, Any], message_type: str,
                                 execution_result: Dict[str, Any], market_context: Dict[str, Any],
                                 strategy_plan) -> Dict[str, Any]:
        """Generate message using adaptive intelligence"""
        
        # Get fused knowledge
        fused_knowledge = execution_result.get("fused_knowledge", {})
        
        # Select optimal model for copywriting
        model_selection = self.llm_selector.recommend_model_for_task(
            "personalization", 
            len(str(fused_knowledge)) + len(str(market_context))
        )
        
        selected_model = model_selection["recommended_model"]
        logger.info(f"Selected model for copywriting: {selected_model}")
        
        # Build enhanced prompt with market context
        enhanced_prompt = self._build_adaptive_prompt(
            lead_data, message_type, fused_knowledge, market_context, strategy_plan
        )
        
        # Generate message using selected model
        if selected_model.startswith("gpt"):
            message_content = self._generate_with_openai(enhanced_prompt, selected_model)
        elif selected_model.startswith("claude"):
            message_content = self._generate_with_claude(enhanced_prompt, selected_model)
        else:
            # Fallback to default
            message_content = self._generate_with_openai(enhanced_prompt, "gpt-4")
        
        # Calculate enhanced scores
        personalization_score = self._calculate_enhanced_personalization_score(
            lead_data, fused_knowledge, message_content
        )
        
        market_awareness_score = self._calculate_market_awareness_score(
            message_content, market_context
        )
        
        return {
            "message": message_content,
            "personalization_score": personalization_score,
            "market_awareness_score": market_awareness_score,
            "model_used": selected_model,
            "strategy_applied": strategy_plan.strategy.value
        }
    
    def _build_adaptive_prompt(self, lead_data: Dict[str, Any], message_type: str,
                             fused_knowledge: Dict[str, Any], market_context: Dict[str, Any],
                             strategy_plan) -> str:
        """Build enhanced prompt with adaptive intelligence"""
        
        prompt_parts = [
            f"Generate a {message_type} message for:",
            f"Lead: {lead_data.get('name', 'Unknown')} at {lead_data.get('company', 'Unknown Company')}",
            f"Role: {lead_data.get('title', 'Unknown Role')}",
            f"Industry: {lead_data.get('industry', 'Unknown Industry')}",
            "",
            "Company Knowledge:",
            f"- Products/Services: {fused_knowledge.get('products', 'Not specified')}",
            f"- Value Propositions: {fused_knowledge.get('value_propositions', 'Not specified')}",
            f"- Target Audience: {fused_knowledge.get('target_audience', 'Not specified')}",
            f"- Sales Approach: {fused_knowledge.get('sales_approach', 'Not specified')}",
            "",
            "Market Context:",
            f"- Industry Trends: {market_context.get('industry_trends', {}).get('trends', 'Not available')}",
            f"- Market Sentiment: {market_context.get('market_sentiment', {}).get('sentiment', 'Neutral')}",
            "",
            f"Strategy: {strategy_plan.strategy.value}",
            f"Confidence Threshold: {strategy_plan.confidence_threshold}",
            "",
            "Requirements:",
            "- Personalize based on lead's role and company",
            "- Incorporate market trends and sentiment",
            "- Use company's value propositions",
            "- Include a clear call-to-action",
            "- Maintain professional yet engaging tone",
            "- Keep message concise and impactful"
        ]
        
        return "\n".join(prompt_parts)
    
    def _generate_with_openai(self, prompt: str, model: str) -> str:
        """Generate message using OpenAI models"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return "Unable to generate message at this time."
    
    def _generate_with_claude(self, prompt: str, model: str) -> str:
        """Generate message using Claude models (placeholder - would need Anthropic client)"""
        # For now, fallback to OpenAI
        return self._generate_with_openai(prompt, "gpt-4")
    
    def _calculate_enhanced_personalization_score(self, lead_data: Dict[str, Any], 
                                               fused_knowledge: Dict[str, Any], 
                                               message_content: str) -> int:
        """Calculate enhanced personalization score"""
        base_score = self._calculate_personalization_score(lead_data)
        
        # Enhance based on fused knowledge usage
        knowledge_enhancement = 0
        if fused_knowledge.get('products'):
            knowledge_enhancement += 10
        if fused_knowledge.get('value_propositions'):
            knowledge_enhancement += 15
        if fused_knowledge.get('target_audience'):
            knowledge_enhancement += 10
        
        # Check for specific personalization elements in message
        personalization_elements = self._identify_personalization(message_content)
        element_score = len(personalization_elements) * 5
        
        return min(100, base_score + knowledge_enhancement + element_score)
    
    def _calculate_market_awareness_score(self, message_content: str, 
                                        market_context: Dict[str, Any]) -> int:
        """Calculate market awareness score based on market context usage"""
        score = 0
        
        # Check for industry trend mentions
        trends = market_context.get('industry_trends', {}).get('trends', [])
        for trend in trends:
            if trend.lower() in message_content.lower():
                score += 20
        
        # Check for market sentiment awareness
        sentiment = market_context.get('market_sentiment', {}).get('sentiment', 'neutral')
        if sentiment in message_content.lower():
            score += 15
        
        # Check for competitive awareness
        if market_context.get('competitive_context'):
            score += 10
        
        return min(100, score)

    def _get_variation_style(self, variation_index: int) -> str:
        """Get style description for message variation"""
        styles = ["professional", "conversational", "direct"]
        return styles[variation_index % len(styles)]
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the Copywriter Agent with Phase 3 enhancements"""
        return {
            "name": "Copywriter Agent",
            "description": "AI-powered copywriting with adaptive intelligence, market awareness, and multi-model optimization",
            "capabilities": [
                "Personalized message generation",
                "Multi-touch email sequences",
                "A/B test message variations",
                "Industry-specific messaging",
                "Channel optimization (Email, LinkedIn)",
                "Personalization scoring",
                "Adaptive intelligence based on knowledge level",
                "Market-aware messaging with Grok integration",
                "Intelligent model selection (GPT-4, Claude, etc.)",
                "Knowledge fusion for enhanced personalization",
                "Real-time market context integration"
            ],
            "supported_message_types": list(self.message_frameworks.keys()),
            "supported_industries": list(self.industry_contexts.keys()),
            "ai_models": ["GPT-4", "GPT-3.5-turbo", "Claude-Sonnet", "Claude-Haiku"],
            "phase_3_features": [
                "Adaptive execution based on knowledge level",
                "Market context integration",
                "Intelligent model selection",
                "Enhanced personalization scoring",
                "Market awareness scoring"
            ],
            "version": "3.0.0"
        }

if __name__ == "__main__":
    # Test the Copywriter Agent
    agent = CopywriterAgent()
    
    test_lead = {
        "name": "Sarah Johnson",
        "title": "VP of Sales",
        "company": "TechCorp Solutions",
        "industry": "SaaS",
        "company_size": "50-200",
        "location": "San Francisco, CA",
        "email": "sarah.johnson@techcorp.com",
        "linkedin_url": "https://linkedin.com/in/sarahjohnson"
    }
    
    test_campaign = {
        "value_proposition": "Increase sales efficiency by 40% with our AI-powered CRM",
        "call_to_action": "Schedule a 15-minute demo",
        "target_audience": "Sales leaders at growing SaaS companies"
    }
    
    # Test personalized message
    result = agent.personalize_message(test_lead, "cold_email", test_campaign)
    print(f"Message Generation: {result['success']}")
    if result['success']:
        print(f"Personalization Score: {result['personalization_score']}")
        print(f"Message Length: {result['message_length']} characters")
    
    # Test email sequence
    sequence_result = agent.create_email_sequence(test_lead, test_campaign, 3)
    print(f"Sequence Creation: {sequence_result['success']}")
    if sequence_result['success']:
        print(f"Sequence Length: {len(sequence_result['email_sequence'])} emails")
    
    # Test variations
    variations_result = agent.generate_message_variations(test_lead, "cold_email", 3)
    print(f"Variations Generation: {variations_result['success']}")
    if variations_result['success']:
        print(f"Generated {variations_result['num_variations']} variations")
