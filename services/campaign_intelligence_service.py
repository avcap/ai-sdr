import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
import anthropic
from services.knowledge_service import KnowledgeService
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class CampaignIntelligenceService:
    """
    Service for analyzing uploaded documents and generating intelligent campaign suggestions.
    Uses LLM (Claude/OpenAI) to extract campaign-relevant insights and generate contextual prompts.
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.knowledge_service = KnowledgeService()
        self.supabase = SupabaseService()
        
        # Add Claude client for LLM analysis
        import anthropic
        self.claude_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
    def analyze_documents_for_campaigns(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """
        Analyze uploaded documents to extract campaign-relevant insights.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Dict containing campaign insights and suggestions
        """
        try:
            logger.info(f"Analyzing documents for campaigns for user {user_id}")
            
            # Get user's knowledge from uploaded documents
            knowledge = self.knowledge_service.get_user_knowledge(tenant_id, user_id, task_type='campaign')
            
            # Check if user has uploaded any documents
            if not knowledge or knowledge.get('source_count', 0) == 0:
                logger.warning(f"No documents found for user {user_id} - cannot generate suggestions")
                return self._get_default_campaign_insights()
            
            logger.info(f"Retrieved knowledge from {knowledge.get('source_count', 0)} sources")
            
            # Extract campaign context from knowledge
            campaign_context = self._extract_campaign_context(knowledge)
            campaign_context['tenant_id'] = tenant_id
            campaign_context['user_id'] = user_id
            
            # Try to generate LLM-powered suggestions
            try:
                suggestions = self._generate_llm_suggestions(campaign_context, count=3)
            except Exception as llm_error:
                # LLM failed but user HAS documents - use knowledge-based fallback
                logger.error(f"LLM generation failed: {llm_error}")
                suggestions = self._handle_llm_error_fallback(llm_error, campaign_context)
            
            # Calculate insights
            insights = {
                'target_audience': campaign_context.get('target_audience', {}),
                'industry_focus': campaign_context.get('industry', 'Technology'),
                'product_categories': campaign_context.get('products', []),
                'sales_approach': campaign_context.get('sales_approach', ''),
                'competitive_positioning': campaign_context.get('competitive_advantages', []),
                'suggested_campaigns': suggestions,
                'document_count': knowledge.get('source_count', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'has_knowledge': True
            }
            
            logger.info(f"Generated {len(suggestions)} campaign suggestions")
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing documents for campaigns: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Major error - return no suggestions
            return self._get_default_campaign_insights()
    
    def generate_prompt_suggestions(self, knowledge: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate prompt suggestions based on knowledge.
        
        Args:
            knowledge: User's aggregated knowledge
            count: Number of suggestions to generate
            
        Returns:
            List of suggestion dictionaries
        """
        try:
            campaign_context = self._extract_campaign_context(knowledge)
            suggestions = self._generate_llm_suggestions(campaign_context, count)
            
            # Save suggestions to database for future reference
            for suggestion in suggestions:
                self._save_suggestion_to_db(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating prompt suggestions: {e}")
            return self._get_fallback_suggestions()
    
    def _extract_campaign_context(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract campaign-relevant context from aggregated knowledge.
        
        Args:
            knowledge: User's aggregated knowledge from knowledge_service
            
        Returns:
            Dict containing campaign context for LLM
        """
        # Extract real data from aggregated knowledge
        company_info = knowledge.get('company_info', {})
        
        context = {
            'company_name': company_info.get('company_name', 'Your Company'),
            'industry': company_info.get('industry', knowledge.get('industry_context', {}).get('industry', 'Technology')),
            'products': knowledge.get('products', []),
            'target_audience': knowledge.get('target_audience', {}),
            'sales_approach': knowledge.get('sales_approach', ''),
            'competitive_advantages': knowledge.get('competitive_advantages', []),
            'value_propositions': knowledge.get('value_propositions', []),
            'key_messages': knowledge.get('key_messages', []),
            'sales_methodologies': knowledge.get('sales_methodologies', []),
            'source_count': knowledge.get('source_count', 0)
        }
        
        logger.info(f"📊 Extracted campaign context: {context['company_name']} in {context['industry']}")
        
        return context
    
    def _generate_llm_suggestions(self, campaign_context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Use Claude with adaptive sales strategies to generate contextual campaign suggestions.
        
        Args:
            campaign_context: Extracted campaign context from documents
            count: Number of suggestions to generate
            
        Returns:
            List of LLM-generated campaign suggestions with adaptive strategies
        """
        try:
            import hashlib
            from services.sales_playbook_service import SalesPlaybookService
            
            # Get adaptive sales strategies
            playbook_service = SalesPlaybookService()
            tenant_id = campaign_context.get('tenant_id')
            user_id = campaign_context.get('user_id')
            
            adaptive_strategies = playbook_service.get_adaptive_strategies(
                tenant_id, user_id, campaign_context
            )
            
            # Build comprehensive context from knowledge
            company_name = campaign_context.get('company_name', 'Your Company')
            industry = campaign_context.get('industry', 'Technology')
            products = campaign_context.get('products', [])
            target_audience = campaign_context.get('target_audience', {})
            value_props = campaign_context.get('value_propositions', [])
            sales_approach = campaign_context.get('sales_approach', '')
            competitive_advantages = campaign_context.get('competitive_advantages', [])
            
            # Format strategies for prompt
            strategy_source = adaptive_strategies.get('source', 'universal')
            strategies = adaptive_strategies.get('strategies', {})
            strategy_confidence = adaptive_strategies.get('confidence', 0.5)
            strategy_reasoning = adaptive_strategies.get('reasoning', '')
            
            # Create enhanced prompt with adaptive strategies
            analysis_prompt = f"""
You are an expert SDR campaign strategist. Generate {count} highly specific, actionable campaign suggestions.

COMPANY PROFILE:
- Company: {company_name}
- Industry: {industry}
- Products/Services: {', '.join(products[:5]) if products else 'Not specified'}
- Target Audience: {json.dumps(target_audience, indent=2)}
- Value Propositions: {', '.join(value_props[:3]) if value_props else 'Not specified'}
- Sales Approach: {sales_approach or 'Not specified'}
- Competitive Advantages: {', '.join(competitive_advantages[:3]) if competitive_advantages else 'Not specified'}

SALES STRATEGY FRAMEWORK (Confidence: {strategy_confidence:.0%}):
Source: {strategy_source}
{strategy_reasoning}

Framework Details:
{json.dumps(strategies, indent=2)}

INSTRUCTIONS:
Generate {count} unique campaign suggestions that:
1. Apply the sales strategy framework above
2. Are specific to this company's offerings and target market
3. Include concrete prospecting criteria (roles, company sizes, industries, qualifying criteria)
4. Reference specific pain points, value propositions, or trigger events
5. Include the recommended messaging approach from the framework
6. Specify multi-touch sequence if applicable
7. Include actionable prompts ready to execute

For each suggestion, provide:
- title: Compelling campaign title (max 60 chars)
- prompt: Complete, specific prospecting prompt with target roles, company size, industry, and qualifying criteria
- reasoning: Why this campaign fits the company's profile AND the selected sales framework (2-3 sentences)
- confidence: Score from 0.0-1.0 based on how well company data + framework supports this campaign
- category: Campaign category (executive_prospecting, mid_market, enterprise_focus, industry_specific, problem_focused, trigger_based)
- framework_application: How you applied the sales framework (1 sentence)
- expected_outcome: What results to expect based on framework best practices

Return ONLY valid JSON array:
[
    {{
        "title": "...",
        "prompt": "...",
        "reasoning": "...",
        "confidence": 0.85,
        "category": "...",
        "framework_application": "...",
        "expected_outcome": "..."
    }}
]
"""
            
            # Call Claude for analysis
            logger.info(f"🤖 Calling Claude with adaptive strategies (source: {strategy_source})")
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # Use Haiku (available in user's API)
                max_tokens=2500,
                temperature=0.7,  # Allow some creativity
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }]
            )
            
            # Parse Claude's response
            suggestions_text = response.content[0].text.strip()
            
            # Extract JSON from response (handle code blocks)
            if "```json" in suggestions_text:
                suggestions_text = suggestions_text.split("```json")[1].split("```")[0].strip()
            elif "```" in suggestions_text:
                suggestions_text = suggestions_text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(suggestions_text)
            
            # Add metadata to each suggestion
            for i, suggestion in enumerate(suggestions):
                suggestion['id'] = f"llm_{hashlib.md5(suggestion['title'].encode()).hexdigest()[:8]}"
                suggestion['generated_at'] = datetime.now().isoformat()
                suggestion['model_used'] = 'claude-3-haiku'
                suggestion['strategy_source'] = strategy_source
                suggestion['strategy_confidence'] = strategy_confidence
            
            logger.info(f"✅ Generated {len(suggestions)} adaptive suggestions")
            
            # Save suggestions to database for tracking
            if tenant_id and user_id:
                for suggestion in suggestions:
                    self._save_suggestion_to_db(suggestion, tenant_id, user_id)
            
            return suggestions[:count]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude's response as JSON: {e}")
            logger.error(f"Response text: {suggestions_text if 'suggestions_text' in locals() else 'N/A'}")
            raise
            
        except Exception as e:
            logger.error(f"Error generating LLM suggestions: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _prepare_context_for_llm(self, context: Dict[str, Any]) -> str:
        """
        Prepare context summary for LLM processing.
        
        Args:
            context: Campaign context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Company information
        context_parts.append(f"Company: {context['company_name']}")
        context_parts.append(f"Industry: {context['industry']}")
        
        # Products
        if context['products']:
            products_str = ', '.join(context['products'][:3])  # Limit to 3 products
            context_parts.append(f"Products/Services: {products_str}")
        
        # Target audience
        target_audience = context['target_audience']
        if target_audience:
            personas = ', '.join(target_audience.get('buyer_personas', [])[:3])
            sizes = ', '.join(target_audience.get('company_sizes', [])[:2])
            context_parts.append(f"Target Roles: {personas}")
            context_parts.append(f"Company Sizes: {sizes}")
            
            pain_points = target_audience.get('pain_points', [])
            if pain_points:
                pain_points_str = ', '.join(pain_points[:3])
                context_parts.append(f"Pain Points: {pain_points_str}")
        
        # Sales approach
        if context['sales_approach']:
            context_parts.append(f"Sales Approach: {context['sales_approach'][:200]}...")
        
        # Competitive advantages
        if context['competitive_advantages']:
            advantages_str = ', '.join(context['competitive_advantages'][:3])
            context_parts.append(f"Competitive Advantages: {advantages_str}")
        
        return '\n'.join(context_parts)
    
    def _generate_with_claude(self, context_summary: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate suggestions using Claude.
        
        Args:
            context_summary: Formatted context for LLM
            count: Number of suggestions to generate
            
        Returns:
            List of suggestion dictionaries
        """
        try:
            system_prompt = """You are an expert sales development representative who creates highly effective prospecting campaigns. 

Your task is to generate specific, actionable campaign prompts based on company information. Each prompt should be:
1. Specific about target roles, industries, and company sizes
2. Actionable and clear about what prospects to find
3. Relevant to the company's products/services and target audience
4. Professional and focused on business value

Format your response as a JSON array with exactly 3 objects, each containing:
- "title": A descriptive title for the campaign
- "prompt": The specific prospecting prompt
- "reasoning": Why this campaign would be effective
- "confidence": A confidence score from 0.0 to 1.0

Example format:
[
  {
    "title": "AI-Savvy CTO Prospecting",
    "prompt": "Find me 20 CTOs at 50-200 employee companies in the AI/ML space who are looking to implement intelligent automation solutions",
    "reasoning": "Based on your AI agent specialization and target audience insights",
    "confidence": 0.9
  }
]"""

            user_prompt = f"""Based on this company information, generate 3 specific prospecting campaign prompts:

{context_summary}

Focus on creating campaigns that would be most effective for this company's products and target audience."""

            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text
            suggestions = json.loads(response_text)
            
            # Validate and format suggestions
            formatted_suggestions = []
            for i, suggestion in enumerate(suggestions[:count]):
                formatted_suggestions.append({
                    'id': f'suggestion_{i+1}',
                    'title': suggestion.get('title', f'Campaign Suggestion {i+1}'),
                    'prompt': suggestion.get('prompt', ''),
                    'reasoning': suggestion.get('reasoning', ''),
                    'confidence': float(suggestion.get('confidence', 0.7)),
                    'category': self._categorize_suggestion(suggestion.get('prompt', '')),
                    'generated_at': datetime.now().isoformat()
                })
            
            return formatted_suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions with Claude: {e}")
            return self._get_fallback_suggestions()
    
    def _categorize_suggestion(self, prompt: str) -> str:
        """
        Categorize suggestion based on prompt content.
        
        Args:
            prompt: The suggestion prompt
            
        Returns:
            Category string
        """
        prompt_lower = prompt.lower()
        
        if any(role in prompt_lower for role in ['cto', 'vp', 'director', 'head of']):
            return 'executive_prospecting'
        elif any(size in prompt_lower for size in ['enterprise', '500+', '1000+']):
            return 'enterprise_focus'
        elif any(industry in prompt_lower for industry in ['saas', 'tech', 'software', 'ai']):
            return 'tech_industry'
        elif any(size in prompt_lower for size in ['startup', 'small', '50-']):
            return 'smb_focus'
        else:
            return 'general'
    
    def _save_suggestion_to_db(self, suggestion: Dict[str, Any], tenant_id: str = None, user_id: str = None) -> bool:
        """
        Save campaign suggestion to database for analytics and tracking.
        
        Args:
            suggestion: Suggestion dictionary
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            True if saved successfully
        """
        if not tenant_id or not user_id:
            logger.warning("Cannot save suggestion: missing tenant_id or user_id")
            return False
        
        try:
            suggestion_data = {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'suggestion_type': suggestion.get('category', 'general'),
                'prompt_text': suggestion.get('prompt', ''),
                'reasoning': suggestion.get('reasoning', ''),
                'confidence_score': suggestion.get('confidence', 0.7),
                'metadata': {
                    'title': suggestion.get('title', ''),
                    'model_used': suggestion.get('model_used', 'claude'),
                    'generated_at': suggestion.get('generated_at', datetime.now().isoformat())
                }
            }
            
            response = self.supabase.client.from_('campaign_suggestions').insert(suggestion_data).execute()
            
            if response.data:
                logger.info(f"💾 Saved suggestion to database: {suggestion.get('title', 'Untitled')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving suggestion to database: {e}")
            return False
    
    def _get_default_campaign_insights(self) -> Dict[str, Any]:
        """
        Return default insights when no knowledge is available.
        User MUST upload documents to get suggestions.
        """
        return {
            'target_audience': {
                'buyer_personas': [],
                'company_sizes': [],
                'industries': [],
                'pain_points': []
            },
            'industry_focus': '',
            'product_categories': [],
            'sales_approach': '',
            'competitive_positioning': [],
            'suggested_campaigns': [],  # EMPTY - no suggestions without documents
            'document_count': 0,
            'analysis_timestamp': datetime.now().isoformat(),
            'has_knowledge': False,
            'message': 'No training data available. Please upload documents in the Knowledge Bank to get AI-powered campaign suggestions.',
            'call_to_action': 'Upload company information, product details, sales training materials, or website links in the Knowledge Bank to enable smart campaign suggestions.'
        }
    
    def _handle_llm_error_fallback(self, error: Exception, campaign_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fallback when LLM API fails BUT user has uploaded documents.
        Uses extracted knowledge to create basic suggestions without LLM analysis.
        
        Only called when:
        - User HAS documents uploaded
        - Claude API fails (rate limit, timeout, error)
        
        Args:
            error: The exception that occurred
            campaign_context: Extracted context from user's documents
            
        Returns:
            List of basic suggestions derived from extracted knowledge (not generic)
        """
        logger.error(f"LLM API error, using knowledge-based fallback: {error}")
        
        company_name = campaign_context.get('company_name', 'Your Company')
        industry = campaign_context.get('industry', 'your industry')
        products = campaign_context.get('products', [])
        target_audience = campaign_context.get('target_audience', {})
        
        # Extract target roles from knowledge
        buyer_personas = target_audience.get('buyer_personas', [])
        if not buyer_personas:
            buyer_personas = ['decision makers', 'executives']
        
        # Create 1-2 basic suggestions using extracted knowledge
        suggestions = []
        
        # Suggestion 1: Based on company info
        suggestions.append({
            'id': 'knowledge_fallback_1',
            'title': f'{company_name} Target Audience Outreach',
            'prompt': f'Find me {", ".join(buyer_personas[:2])} at companies in {industry}',
            'reasoning': f'Based on your uploaded company information. (Note: Claude API unavailable - using basic suggestion from extracted knowledge)',
            'confidence': 0.5,
            'category': 'knowledge_based',
            'generated_at': datetime.now().isoformat(),
            'is_fallback': True,
            'fallback_reason': 'llm_api_error'
        })
        
        # Suggestion 2: If we have product info
        if products:
            suggestions.append({
                'id': 'knowledge_fallback_2',
                'title': f'{products[0]} Product-Focused Campaign',
                'prompt': f'Target decision makers interested in {products[0]} solutions',
                'reasoning': f'Based on your product information. (Note: Claude API unavailable - using basic suggestion from extracted knowledge)',
                'confidence': 0.5,
                'category': 'knowledge_based',
                'generated_at': datetime.now().isoformat(),
                'is_fallback': True,
                'fallback_reason': 'llm_api_error'
            })
        
        return suggestions[:2]  # Return 1-2 suggestions based on available knowledge
    
    def _extract_knowledge_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract knowledge from uploaded documents when no knowledge exists.
        
        Args:
            documents: List of document records
            
        Returns:
            Extracted knowledge dictionary
        """
        try:
            logger.info(f"Extracting knowledge from {len(documents)} documents")
            
            # Import the knowledge extraction agent
            from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
            
            # Initialize the agent
            agent = KnowledgeExtractionAgent()
            
            # Prepare file paths
            file_paths = []
            document_types = []
            
            for doc in documents:
                file_path = doc.get('file_path')
                if file_path and os.path.exists(file_path):
                    file_paths.append(file_path)
                    document_types.append(doc.get('document_type', 'company_info'))
            
            if not file_paths:
                logger.warning("No valid file paths found in documents")
                return {}
            
            # Extract knowledge (handle async method)
            import asyncio
            if hasattr(agent, 'extract_knowledge_parallel'):
                # Use async method
                result = asyncio.run(agent.extract_knowledge_parallel(file_paths, document_type=document_types[0] if len(set(document_types)) == 1 else None))
            else:
                # Use sync method
                result = agent.extract_knowledge_from_files(file_paths, document_type=document_types[0] if len(set(document_types)) == 1 else None)
            
            if result.get('success'):
                logger.info("Successfully extracted knowledge from documents")
                knowledge = result.get('knowledge', {})
                
                # Save the extracted knowledge to the database
                self._save_extracted_knowledge(knowledge, documents[0])
                
                return knowledge
            else:
                logger.error(f"Failed to extract knowledge: {result.get('error', 'Unknown error')}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting knowledge from documents: {e}")
            return {}
    
    def _save_extracted_knowledge(self, knowledge: Dict[str, Any], document: Dict[str, Any]) -> None:
        """
        Save extracted knowledge to the database.
        
        Args:
            knowledge: Extracted knowledge dictionary
            document: Document record
        """
        try:
            logger.info(f"Saving extracted knowledge for document: {document.get('filename', 'Unknown')}")
            
            # Prepare knowledge data for database
            knowledge_data = {
                'tenant_id': document.get('tenant_id'),
                'user_id': document.get('user_id'),
                'document_id': document.get('id'),
                'document_type': knowledge.get('document_type', document.get('document_type', 'company_info')),
                'extracted_content': json.dumps(knowledge),
                'quality_score': knowledge.get('quality_metrics', {}).get('overall_score', 0.7),
                'extraction_method': 'claude_ai',
                'status': 'completed'
            }
            
            # Save to database
            self.supabase.client.table("user_knowledge").insert(knowledge_data).execute()
            logger.info("Knowledge saved to database successfully")
            
        except Exception as e:
            logger.error(f"Error saving extracted knowledge: {e}")
    
    # _get_document_based_suggestions() method removed - replaced with real LLM analysis
    
    def get_cached_suggestions(self, tenant_id: str, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached suggestions if available and not expired.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Cached suggestions or None
        """
        try:
            # This would check for recent suggestions in the database
            # For now, return None to always generate fresh suggestions
            return None
        except Exception as e:
            logger.error(f"Error getting cached suggestions: {e}")
            return None
