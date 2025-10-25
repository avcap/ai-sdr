import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from openai import OpenAI
import re

logger = logging.getLogger(__name__)

class AdaptivePromptProcessor:
    """
    Processes user prompts to extract business context and generate knowledge structures.
    Enables the system to work with minimal or no documents by leveraging detailed prompts.
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Business context extraction patterns
        self.business_patterns = {
            "company_type": [
                r"(?:we are|we're|our company is|we're a|we are a)\s+([^,\.]+)",
                r"(?:company|business|organization|startup|firm)\s+(?:that|which|specializing|focused)",
                r"(?:SaaS|software|tech|technology|AI|fintech|healthtech|edtech)"
            ],
            "target_audience": [
                r"(?:target|sell to|focus on|serve|customers are)\s+([^,\.]+)",
                r"(?:CTO|CEO|VP|Director|Manager|Sales|Marketing|HR)",
                r"(?:enterprise|SMB|startup|mid-market|small business)"
            ],
            "products_services": [
                r"(?:we sell|our product|our service|we offer|we provide)\s+([^,\.]+)",
                r"(?:platform|software|tool|solution|service|product)",
                r"(?:helps|enables|allows|provides|delivers)"
            ],
            "value_proposition": [
                r"(?:value proposition|key benefit|main advantage|why choose us)\s*:?\s*([^,\.]+)",
                r"(?:saves|reduces|increases|improves|streamlines|automates)",
                r"(?:ROI|efficiency|productivity|cost|time|revenue)"
            ],
            "industry": [
                r"(?:industry|sector|market|vertical)\s*:?\s*([^,\.]+)",
                r"(?:healthcare|finance|education|retail|manufacturing|technology)"
            ]
        }
    
    def analyze_detailed_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze user prompt to extract comprehensive business context.
        
        Args:
            user_prompt: User's natural language prompt describing their business/campaign
            
        Returns:
            Dict with extracted business context and confidence scores
        """
        logger.info(f"Analyzing detailed prompt: {user_prompt[:100]}...")
        
        try:
            # Use LLM for comprehensive analysis
            analysis_prompt = self._build_analysis_prompt(user_prompt)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            business_context = self._parse_business_analysis(analysis_text)
            
            # Add pattern-based extraction as fallback/validation
            pattern_context = self._extract_with_patterns(user_prompt)
            
            # Merge and validate results
            merged_context = self._merge_analysis_results(business_context, pattern_context)
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(merged_context, user_prompt)
            
            return {
                "business_context": merged_context,
                "confidence_scores": confidence_scores,
                "extraction_method": "llm_enhanced",
                "prompt_length": len(user_prompt),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing prompt: {e}")
            # Fallback to pattern-based extraction
            pattern_context = self._extract_with_patterns(user_prompt)
            return {
                "business_context": pattern_context,
                "confidence_scores": {"overall": 0.5},
                "extraction_method": "pattern_fallback",
                "prompt_length": len(user_prompt),
                "analysis_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _build_analysis_prompt(self, user_prompt: str) -> str:
        """Build comprehensive analysis prompt for LLM"""
        return f"""
Analyze this user prompt to extract comprehensive business context for an AI sales system:

USER PROMPT: "{user_prompt}"

Extract the following information with high accuracy:

1. COMPANY/BUSINESS TYPE:
   - What type of company/business is this?
   - Industry sector
   - Company size/stage (startup, SMB, enterprise)
   - Business model (B2B, B2C, marketplace, etc.)

2. TARGET AUDIENCE:
   - Who are their ideal customers?
   - Job titles/roles they target
   - Company sizes they serve
   - Industries they focus on
   - Geographic regions

3. PRODUCTS/SERVICES:
   - What do they sell/offer?
   - Key features and capabilities
   - Product categories
   - Service offerings

4. VALUE PROPOSITIONS:
   - Main benefits they provide
   - Key differentiators
   - ROI/value they deliver
   - Problems they solve

5. SALES APPROACH:
   - Sales methodology mentioned
   - Sales philosophy
   - Approach to customers
   - Sales process

6. COMPETITIVE ADVANTAGES:
   - What makes them unique?
   - Competitive differentiators
   - Market positioning
   - Strengths vs competitors

7. CAMPAIGN GOALS:
   - What are they trying to achieve?
   - Campaign objectives
   - Target outcomes
   - Success metrics

8. MARKET CONTEXT:
   - Industry trends mentioned
   - Market conditions
   - Timing considerations
   - Market opportunities

Return your analysis as structured JSON with confidence scores (0-1) for each extracted field.
If information is not available or unclear, use "Not specified" and set confidence to 0.0.

Format:
{{
  "company_info": {{
    "company_type": "...",
    "industry": "...",
    "company_size": "...",
    "business_model": "...",
    "confidence": 0.8
  }},
  "target_audience": {{
    "primary_roles": ["..."],
    "company_sizes": ["..."],
    "industries": ["..."],
    "regions": ["..."],
    "confidence": 0.7
  }},
  "products_services": {{
    "main_products": ["..."],
    "key_features": ["..."],
    "service_offerings": ["..."],
    "confidence": 0.9
  }},
  "value_propositions": {{
    "primary_benefits": ["..."],
    "key_differentiators": ["..."],
    "roi_value": "...",
    "problems_solved": ["..."],
    "confidence": 0.8
  }},
  "sales_approach": {{
    "methodology": "...",
    "philosophy": "...",
    "process": "...",
    "confidence": 0.6
  }},
  "competitive_advantages": {{
    "unique_selling_points": ["..."],
    "differentiators": ["..."],
    "market_position": "...",
    "confidence": 0.7
  }},
  "campaign_goals": {{
    "objectives": ["..."],
    "target_outcomes": ["..."],
    "success_metrics": ["..."],
    "confidence": 0.8
  }},
  "market_context": {{
    "industry_trends": ["..."],
    "market_conditions": "...",
    "timing_factors": ["..."],
    "opportunities": ["..."],
    "confidence": 0.6
  }}
}}
"""
    
    def _parse_business_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse LLM analysis response into structured data"""
        try:
            # Extract JSON from response
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = analysis_text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in analysis response")
                return self._get_default_business_context()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._get_default_business_context()
    
    def _extract_with_patterns(self, user_prompt: str) -> Dict[str, Any]:
        """Extract business context using regex patterns as fallback"""
        context = {}
        
        for category, patterns in self.business_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, user_prompt, re.IGNORECASE)
                matches.extend(found)
            
            if matches:
                context[category] = list(set(matches))  # Remove duplicates
        
        return context
    
    def _merge_analysis_results(self, llm_context: Dict[str, Any], pattern_context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM analysis with pattern-based extraction"""
        merged = llm_context.copy()
        
        # Use pattern results to validate/fill gaps in LLM analysis
        for category, pattern_data in pattern_context.items():
            if category not in merged or not merged[category]:
                merged[category] = pattern_data
        
        return merged
    
    def _calculate_confidence_scores(self, context: Dict[str, Any], user_prompt: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted information"""
        scores = {}
        
        # Base confidence on prompt length and detail
        prompt_score = min(len(user_prompt) / 500, 1.0)  # Longer prompts = higher confidence
        
        for category, data in context.items():
            if isinstance(data, dict):
                # Use confidence from LLM analysis if available
                scores[category] = data.get("confidence", prompt_score)
            elif isinstance(data, list) and data:
                # Pattern-based extraction
                scores[category] = min(len(data) * 0.2, 0.8)
            else:
                scores[category] = 0.0
        
        # Overall confidence
        scores["overall"] = sum(scores.values()) / len(scores) if scores else 0.0
        
        return scores
    
    def generate_adaptive_knowledge(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive knowledge structure from business context.
        
        Args:
            business_context: Extracted business context from prompt analysis
            
        Returns:
            Dict with structured knowledge for AI agents
        """
        logger.info("Generating adaptive knowledge structure")
        
        try:
            # Generate knowledge using LLM
            knowledge_prompt = self._build_knowledge_generation_prompt(business_context)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": knowledge_prompt}],
                max_tokens=2000,
                temperature=0.4
            )
            
            knowledge_text = response.choices[0].message.content
            knowledge_structure = self._parse_knowledge_structure(knowledge_text)
            
            # Enhance with confidence scores
            enhanced_knowledge = self._enhance_knowledge_with_confidence(knowledge_structure, business_context)
            
            return enhanced_knowledge
            
        except Exception as e:
            logger.error(f"Error generating knowledge: {e}")
            return self._create_fallback_knowledge(business_context)
    
    def _build_knowledge_generation_prompt(self, business_context: Dict[str, Any]) -> str:
        """Build prompt for knowledge structure generation"""
        return f"""
Based on this business context analysis, generate a comprehensive knowledge structure for AI sales agents:

BUSINESS CONTEXT: {json.dumps(business_context, indent=2)}

Create a detailed knowledge structure that includes:

1. COMPANY INFORMATION:
   - Company name and type
   - Industry and market position
   - Company size and stage
   - Business model and revenue streams

2. PRODUCTS/SERVICES:
   - Detailed product descriptions
   - Key features and capabilities
   - Service offerings
   - Pricing models (if mentioned)

3. TARGET AUDIENCE:
   - Detailed buyer personas
   - Decision maker profiles
   - Company characteristics
   - Pain points and challenges

4. VALUE PROPOSITIONS:
   - Primary benefits and outcomes
   - ROI and value metrics
   - Competitive differentiators
   - Problem-solution fit

5. SALES METHODOLOGY:
   - Sales approach and philosophy
   - Sales process and stages
   - Qualification criteria
   - Objection handling strategies

6. COMPETITIVE INTELLIGENCE:
   - Competitive landscape
   - Market positioning
   - Unique advantages
   - Differentiation strategies

7. INDUSTRY CONTEXT:
   - Market trends and opportunities
   - Industry challenges
   - Regulatory considerations
   - Market timing factors

8. MESSAGING FRAMEWORK:
   - Key messages and themes
   - Tone and voice guidelines
   - Value proposition statements
   - Call-to-action strategies

Generate this as structured JSON that AI agents can use for:
- Lead prospecting and qualification
- Message personalization
- Campaign creation
- Sales conversation guidance

Make reasonable inferences and industry best practices where specific information is missing.
Focus on actionable intelligence for sales activities.
"""
    
    def _parse_knowledge_structure(self, knowledge_text: str) -> Dict[str, Any]:
        """Parse generated knowledge structure"""
        try:
            json_start = knowledge_text.find('{')
            json_end = knowledge_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = knowledge_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return self._get_default_knowledge_structure()
                
        except json.JSONDecodeError as e:
            logger.error(f"Knowledge structure parsing error: {e}")
            return self._get_default_knowledge_structure()
    
    def _enhance_knowledge_with_confidence(self, knowledge: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add confidence scores and metadata to knowledge structure"""
        enhanced = knowledge.copy()
        
        # Add metadata
        enhanced["metadata"] = {
            "source": "prompt_analysis",
            "generation_method": "llm_generated",
            "confidence_level": "medium",
            "created_at": datetime.now().isoformat(),
            "context_quality": self._assess_context_quality(context)
        }
        
        # Add confidence scores to each section
        for section in enhanced:
            if isinstance(enhanced[section], dict) and "metadata" not in section:
                enhanced[section]["confidence"] = 0.7  # Default for LLM-generated
        
        return enhanced
    
    def _assess_context_quality(self, context: Dict[str, Any]) -> str:
        """Assess the quality of extracted context"""
        filled_fields = sum(1 for field in context.values() if field and field != "Not specified")
        total_fields = len(context)
        
        quality_ratio = filled_fields / total_fields if total_fields > 0 else 0
        
        if quality_ratio >= 0.8:
            return "high"
        elif quality_ratio >= 0.5:
            return "medium"
        else:
            return "low"
    
    def assess_prompt_quality(self, user_prompt: str) -> Dict[str, Any]:
        """
        Assess the quality and detail level of user prompt.
        
        Args:
            user_prompt: User's prompt to assess
            
        Returns:
            Dict with quality assessment and recommendations
        """
        logger.info("Assessing prompt quality")
        
        # Basic metrics
        word_count = len(user_prompt.split())
        char_count = len(user_prompt)
        
        # Check for key business elements
        business_elements = {
            "company_type": bool(re.search(r"(?:company|business|we are|startup|firm)", user_prompt, re.IGNORECASE)),
            "target_audience": bool(re.search(r"(?:target|customers|sell to|serve)", user_prompt, re.IGNORECASE)),
            "products_services": bool(re.search(r"(?:product|service|offer|sell|provide)", user_prompt, re.IGNORECASE)),
            "value_proposition": bool(re.search(r"(?:benefit|value|advantage|help|solve)", user_prompt, re.IGNORECASE)),
            "industry": bool(re.search(r"(?:industry|sector|market|vertical)", user_prompt, re.IGNORECASE))
        }
        
        # Calculate quality score
        element_score = sum(business_elements.values()) / len(business_elements)
        length_score = min(word_count / 100, 1.0)  # Optimal around 100+ words
        overall_score = (element_score + length_score) / 2
        
        # Generate recommendations
        recommendations = []
        if word_count < 50:
            recommendations.append("Add more detail about your business and goals")
        if not business_elements["company_type"]:
            recommendations.append("Describe your company type and industry")
        if not business_elements["target_audience"]:
            recommendations.append("Specify your target customers and audience")
        if not business_elements["products_services"]:
            recommendations.append("Explain what products or services you offer")
        if not business_elements["value_proposition"]:
            recommendations.append("Describe the value and benefits you provide")
        
        return {
            "overall_score": overall_score,
            "word_count": word_count,
            "char_count": char_count,
            "business_elements": business_elements,
            "element_score": element_score,
            "length_score": length_score,
            "quality_level": "high" if overall_score >= 0.7 else "medium" if overall_score >= 0.4 else "low",
            "recommendations": recommendations,
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _get_default_business_context(self) -> Dict[str, Any]:
        """Return default business context structure"""
        return {
            "company_info": {"company_type": "Not specified", "industry": "Not specified"},
            "target_audience": {"primary_roles": [], "industries": []},
            "products_services": {"main_products": [], "key_features": []},
            "value_propositions": {"primary_benefits": [], "problems_solved": []},
            "sales_approach": {"methodology": "Not specified"},
            "competitive_advantages": {"unique_selling_points": []},
            "campaign_goals": {"objectives": []},
            "market_context": {"industry_trends": []}
        }
    
    def _get_default_knowledge_structure(self) -> Dict[str, Any]:
        """Return default knowledge structure"""
        return {
            "company_info": {
                "company_name": "Not specified",
                "company_type": "Not specified",
                "industry": "Not specified",
                "company_size": "Not specified"
            },
            "products": [],
            "value_propositions": [],
            "target_audience": {},
            "sales_approach": "Not specified",
            "competitive_advantages": [],
            "key_messages": []
        }
    
    def _create_fallback_knowledge(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic knowledge structure from context as fallback"""
        return {
            "company_info": {
                "company_type": business_context.get("company_type", "Not specified"),
                "industry": business_context.get("industry", "Not specified")
            },
            "products": business_context.get("products_services", []),
            "value_propositions": business_context.get("value_proposition", []),
            "target_audience": business_context.get("target_audience", {}),
            "sales_approach": "Consultative selling approach",
            "competitive_advantages": [],
            "key_messages": [],
            "metadata": {
                "source": "prompt_analysis",
                "generation_method": "fallback",
                "confidence_level": "low",
                "created_at": datetime.now().isoformat()
            }
        }
