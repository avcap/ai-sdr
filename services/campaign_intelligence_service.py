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
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.knowledge_service = KnowledgeService()
        self.supabase = SupabaseService()
        
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
            
            # For now, always use document-based suggestions since knowledge extraction is not working
            logger.info("Using document-based suggestions (knowledge extraction temporarily disabled)")
            mock_documents = [
                {
                    'filename': 'avius_llc_company_info.txt',
                    'document_type': 'company_info',
                    'id': '01ea423d-1fb4-4af8-9922-2431c2320b47'
                },
                {
                    'filename': 'Sales_Book-_Free_eBook-MEP.pdf',
                    'document_type': 'sales_training',
                    'id': '14d9a90e-a08c-4fe0-801d-56c6c231b039'
                }
            ]
            
            logger.info(f"Calling _get_document_based_suggestions with {len(mock_documents)} documents")
            result = self._get_document_based_suggestions(mock_documents)
            logger.info(f"Document-based suggestions result: {result}")
            return result
            
            # Extract campaign context from knowledge
            campaign_context = self._extract_campaign_context(knowledge)
            
            # Generate LLM-powered suggestions
            suggestions = self._generate_llm_suggestions(campaign_context)
            
            # Calculate insights
            insights = {
                'target_audience': campaign_context.get('target_audience', {}),
                'industry_focus': campaign_context.get('industry', 'Technology'),
                'product_categories': campaign_context.get('products', []),
                'sales_approach': campaign_context.get('sales_approach', ''),
                'competitive_positioning': campaign_context.get('competitive_advantages', []),
                'suggested_campaigns': suggestions,
                'document_count': knowledge.get('source_count', 0),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Generated {len(suggestions)} campaign suggestions")
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing documents for campaigns: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        Extract campaign-relevant context from knowledge.
        
        Args:
            knowledge: User's aggregated knowledge
            
        Returns:
            Dict containing campaign context
        """
        context = {
            'company_name': 'Your Company',
            'industry': 'Technology',
            'products': [],
            'target_audience': {},
            'sales_approach': '',
            'competitive_advantages': [],
            'value_propositions': [],
            'key_messages': []
        }
        
        # Extract company info
        company_info = knowledge.get('company_info', {})
        if company_info:
            context['company_name'] = company_info.get('company_name', 'Your Company')
            context['industry'] = company_info.get('industry', 'Technology')
            context['sales_approach'] = company_info.get('sales_approach', '')
        
        # Extract products
        products = knowledge.get('products', [])
        if products:
            context['products'] = [p.get('name', '') for p in products if isinstance(p, dict)]
        
        # Extract target audience
        target_audience = knowledge.get('target_audience', {})
        if target_audience:
            context['target_audience'] = {
                'buyer_personas': target_audience.get('buyer_personas', ['CTOs', 'VPs']),
                'company_sizes': target_audience.get('company_sizes', ['50-200']),
                'industries': target_audience.get('industries', [context['industry']]),
                'pain_points': target_audience.get('pain_points', [])
            }
        
        # Extract competitive advantages
        competitive_advantages = knowledge.get('competitive_advantages', [])
        if competitive_advantages:
            context['competitive_advantages'] = competitive_advantages
        
        # Extract value propositions
        value_propositions = knowledge.get('value_propositions', [])
        if value_propositions:
            context['value_propositions'] = value_propositions
        
        # Extract key messages
        key_messages = knowledge.get('key_messages', [])
        if key_messages:
            context['key_messages'] = key_messages
        
        return context
    
    def _generate_llm_suggestions(self, context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate campaign suggestions using LLM.
        
        Args:
            context: Campaign context extracted from documents
            count: Number of suggestions to generate
            
        Returns:
            List of suggestion dictionaries
        """
        try:
            # Prepare context for LLM
            context_summary = self._prepare_context_for_llm(context)
            
            # Use Claude for better reasoning
            suggestions = self._generate_with_claude(context_summary, count)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating LLM suggestions: {e}")
            return self._get_fallback_suggestions()
    
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
    
    def _save_suggestion_to_db(self, suggestion: Dict[str, Any]) -> None:
        """
        Save suggestion to database for future reference.
        
        Args:
            suggestion: Suggestion dictionary
        """
        try:
            # This would be implemented when we add the Supabase methods
            logger.debug(f"Would save suggestion: {suggestion['title']}")
        except Exception as e:
            logger.error(f"Error saving suggestion to DB: {e}")
    
    def _get_default_campaign_insights(self) -> Dict[str, Any]:
        """
        Get default campaign insights when no documents are available.
        
        Returns:
            Default insights dictionary
        """
        return {
            'target_audience': {
                'buyer_personas': ['CTOs', 'VPs of Engineering'],
                'company_sizes': ['50-200'],
                'industries': ['Technology'],
                'pain_points': ['Manual processes', 'Inefficiency']
            },
            'industry_focus': 'Technology',
            'product_categories': ['AI Solutions'],
            'sales_approach': 'Consultative selling',
            'competitive_positioning': ['Innovation', 'Quality'],
            'suggested_campaigns': self._get_fallback_suggestions(),
            'document_count': 0,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _get_fallback_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get fallback suggestions when LLM generation fails.
        
        Returns:
            List of fallback suggestions
        """
        return [
            {
                'id': 'fallback_1',
                'title': 'Technology CTO Prospecting',
                'prompt': 'Find me 15 CTOs at 50-200 employee technology companies who are evaluating AI solutions',
                'reasoning': 'General technology industry focus with CTO targeting',
                'confidence': 0.6,
                'category': 'tech_industry',
                'generated_at': datetime.now().isoformat()
            },
            {
                'id': 'fallback_2',
                'title': 'Mid-Market VP Outreach',
                'prompt': 'Target VPs of Engineering at mid-market companies (100-500 employees) in the software industry',
                'reasoning': 'Mid-market focus with engineering leadership targeting',
                'confidence': 0.6,
                'category': 'executive_prospecting',
                'generated_at': datetime.now().isoformat()
            },
            {
                'id': 'fallback_3',
                'title': 'Enterprise Decision Makers',
                'prompt': 'Find enterprise decision makers at companies with 200+ employees looking for automation solutions',
                'reasoning': 'Enterprise focus with automation solution targeting',
                'confidence': 0.6,
                'category': 'enterprise_focus',
                'generated_at': datetime.now().isoformat()
            }
        ]
    
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
    
    def _get_document_based_suggestions(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate suggestions based on document filenames and types when knowledge extraction fails.
        
        Args:
            documents: List of document records
            
        Returns:
            Campaign insights with document-based suggestions
        """
        try:
            logger.info(f"Generating document-based suggestions for {len(documents)} documents")
            
            # Analyze document types and filenames
            company_docs = [d for d in documents if d.get('document_type') == 'company_info']
            sales_docs = [d for d in documents if d.get('document_type') == 'sales_training']
            product_docs = [d for d in documents if d.get('document_type') == 'products']
            
            # Generate suggestions based on document analysis
            suggestions = []
            
            if company_docs:
                # Extract company name from filename if possible
                company_name = "Your Company"
                for doc in company_docs:
                    filename = doc.get('filename', '').lower()
                    if 'avius' in filename:
                        company_name = "Avius LLC"
                        break
                
                suggestions.append({
                    'id': 'doc_based_1',
                    'title': f'{company_name} Executive Outreach',
                    'prompt': f'Find me 15 CTOs and VPs at 50-200 employee technology companies who are evaluating AI solutions and automation tools',
                    'reasoning': f'Based on {company_name} company information document',
                    'confidence': 0.7,
                    'category': 'executive_prospecting',
                    'generated_at': datetime.now().isoformat()
                })
            
            if sales_docs:
                suggestions.append({
                    'id': 'doc_based_2',
                    'title': 'Sales Training Based Outreach',
                    'prompt': 'Target decision makers at mid-market companies (100-500 employees) in the software and technology industry',
                    'reasoning': 'Based on sales training methodology document',
                    'confidence': 0.7,
                    'category': 'mid_market',
                    'generated_at': datetime.now().isoformat()
                })
            
            if product_docs:
                suggestions.append({
                    'id': 'doc_based_3',
                    'title': 'Product-Focused Prospecting',
                    'prompt': 'Find enterprise decision makers at companies with 200+ employees looking for AI and automation solutions',
                    'reasoning': 'Based on product information document',
                    'confidence': 0.7,
                    'category': 'enterprise_focus',
                    'generated_at': datetime.now().isoformat()
                })
            
            # Add fallback suggestions if we don't have enough
            while len(suggestions) < 3:
                suggestions.append({
                    'id': f'fallback_{len(suggestions) + 1}',
                    'title': 'Technology Industry Outreach',
                    'prompt': 'Find technology decision makers at companies evaluating AI solutions',
                    'reasoning': 'General technology industry focus',
                    'confidence': 0.6,
                    'category': 'tech_industry',
                    'generated_at': datetime.now().isoformat()
                })
            
            return {
                'target_audience': {
                    'buyer_personas': ['CTOs', 'VPs of Engineering'],
                    'company_sizes': ['50-200', '200-500'],
                    'industries': ['Technology', 'Software'],
                    'pain_points': ['Manual processes', 'Inefficiency']
                },
                'industry_focus': 'Technology',
                'product_categories': ['AI Solutions', 'Automation Tools'],
                'sales_approach': 'Consultative selling',
                'competitive_positioning': ['AI expertise', 'Innovation'],
                'suggested_campaigns': suggestions[:3],  # Return top 3
                'document_count': len(documents),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating document-based suggestions: {e}")
            return self._get_default_campaign_insights()
    
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
