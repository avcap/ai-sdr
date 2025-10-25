import os
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from services.supabase_service import SupabaseService
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class KnowledgeService:
    """
    Service to retrieve and format user knowledge for AI agents.
    Provides structured access to uploaded document knowledge with aggregation and caching.
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        # Simple in-memory cache with TTL
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour
    
    def get_user_knowledge(self, tenant_id: str, user_id: str, task_type: str = None) -> Dict[str, Any]:
        """
        Retrieve user's aggregated knowledge from database with smart filtering and caching.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            task_type: Optional task type for smart filtering ('prospecting', 'copywriting', 'campaign', 'outreach')
            
        Returns:
            Dict containing aggregated and structured knowledge
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(tenant_id, user_id, task_type)
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Retrieved cached knowledge for user {user_id}")
                return cached_result
            
            # Get relevant knowledge articles
            knowledge_articles = self._get_relevant_knowledge(tenant_id, user_id, task_type)
            
            if knowledge_articles:
                logger.info(f"Retrieved {len(knowledge_articles)} knowledge articles for user {user_id}")
                
                # Aggregate knowledge from all articles
                aggregated_knowledge = self._aggregate_knowledge(knowledge_articles)
                
                # Cache the result
                self._set_cache(cache_key, aggregated_knowledge)
                
                return aggregated_knowledge
            else:
                logger.info(f"No knowledge found for user {user_id}, using defaults")
                default_knowledge = self._get_default_knowledge()
                self._set_cache(cache_key, default_knowledge)
                return default_knowledge
                
        except Exception as e:
            logger.error(f"Error retrieving user knowledge: {e}")
            return self._get_default_knowledge()
    
    def _get_relevant_knowledge(self, tenant_id: str, user_id: str, task_type: str = None) -> List[Dict[str, Any]]:
        """
        Get relevant knowledge articles based on task type.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            task_type: Task type for filtering
            
        Returns:
            List of relevant knowledge articles
        """
        # Define task-specific document type preferences
        task_document_types = {
            'prospecting': ['company_info', 'sales_training'],
            'copywriting': ['company_info', 'products', 'sales_training'],
            'campaign': ['company_info', 'products', 'sales_training'],
            'outreach': ['company_info', 'sales_training'],
            None: None  # Get all types
        }
        
        document_types = task_document_types.get(task_type)
        
        if document_types:
            # Get filtered knowledge by document types
            return self.supabase.get_user_knowledge_by_types(tenant_id, user_id, document_types)
        else:
            # Get all knowledge articles
            return self.supabase.get_all_user_knowledge(tenant_id, user_id)
    
    def _aggregate_knowledge(self, knowledge_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Intelligently aggregate multiple knowledge articles into a unified structure.
        
        Args:
            knowledge_articles: List of knowledge articles from database
            
        Returns:
            Aggregated knowledge structure
        """
        if not knowledge_articles:
            return self._get_default_knowledge()
        
        logger.info(f"🔄 Aggregating {len(knowledge_articles)} knowledge articles")
        
        # Initialize aggregated structure
        aggregated = {
            "document_type": "aggregated",
            "company_info": {},
            "products": [],
            "value_propositions": [],
            "sales_approach": "",
            "competitive_advantages": [],
            "target_audience": {},
            "key_messages": [],
            "sales_methodologies": [],
            "target_audience_insights": {},
            "sales_philosophy": "",
            "industry_context": {},
            "practical_advice": [],
            "source_count": len(knowledge_articles)
        }
        
        # Process each article
        for article in knowledge_articles:
            try:
                content = json.loads(article.get('content', '{}'))
                doc_type = content.get('document_type', 'company_info')
                
                logger.info(f"📄 Processing {doc_type} article from {article.get('created_at', 'unknown date')}")
                
                # Aggregate based on document type
                if doc_type == 'company_info':
                    self._aggregate_company_info(content, aggregated)
                elif doc_type == 'products':
                    self._aggregate_products(content, aggregated)
                elif doc_type == 'sales_training':
                    self._aggregate_sales_training(content, aggregated)
                else:
                    # Default to company_info aggregation
                    self._aggregate_company_info(content, aggregated)
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Failed to process knowledge article: {e}")
                continue
        
        # Post-process aggregated data
        self._post_process_aggregated_knowledge(aggregated)
        
        logger.info(f"✅ Aggregation complete. Sources: {aggregated['source_count']}")
        return aggregated
    
    def _aggregate_company_info(self, content: Dict[str, Any], aggregated: Dict[str, Any]):
        """Aggregate company info from content into aggregated structure."""
        # Company info (latest wins for conflicts)
        if 'company_info' in content:
            company_info = content['company_info']
            if isinstance(company_info, dict):
                aggregated['company_info'].update(company_info)
        
        # Products (append unique products)
        if 'products' in content:
            products = content['products']
            if isinstance(products, list):
                for product in products:
                    if product not in aggregated['products']:
                        aggregated['products'].append(product)
        
        # Value propositions (append unique)
        if 'value_propositions' in content:
            vps = content['value_propositions']
            if isinstance(vps, list):
                for vp in vps:
                    if vp not in aggregated['value_propositions']:
                        aggregated['value_propositions'].append(vp)
        
        # Sales approach (use latest non-empty)
        if 'sales_approach' in content and content['sales_approach']:
            aggregated['sales_approach'] = content['sales_approach']
        
        # Competitive advantages (append unique)
        if 'competitive_advantages' in content:
            advantages = content['competitive_advantages']
            if isinstance(advantages, list):
                for advantage in advantages:
                    if advantage not in aggregated['competitive_advantages']:
                        aggregated['competitive_advantages'].append(advantage)
        
        # Target audience (merge dictionaries)
        if 'target_audience' in content:
            target_audience = content['target_audience']
            if isinstance(target_audience, dict):
                aggregated['target_audience'].update(target_audience)
        
        # Key messages (append unique)
        if 'key_messages' in content:
            messages = content['key_messages']
            if isinstance(messages, list):
                for message in messages:
                    if message not in aggregated['key_messages']:
                        aggregated['key_messages'].append(message)
    
    def _aggregate_products(self, content: Dict[str, Any], aggregated: Dict[str, Any]):
        """Aggregate product information."""
        # Products (append unique products)
        if 'products' in content:
            products = content['products']
            if isinstance(products, list):
                for product in products:
                    if product not in aggregated['products']:
                        aggregated['products'].append(product)
        
        # Value propositions from products
        if 'value_propositions' in content:
            vps = content['value_propositions']
            if isinstance(vps, list):
                for vp in vps:
                    if vp not in aggregated['value_propositions']:
                        aggregated['value_propositions'].append(vp)
    
    def _aggregate_sales_training(self, content: Dict[str, Any], aggregated: Dict[str, Any]):
        """Aggregate sales training information."""
        # Sales methodologies (append unique)
        if 'sales_methodologies' in content:
            methodologies = content['sales_methodologies']
            if isinstance(methodologies, list):
                for methodology in methodologies:
                    if methodology not in aggregated['sales_methodologies']:
                        aggregated['sales_methodologies'].append(methodology)
        
        # Target audience insights (merge)
        if 'target_audience_insights' in content:
            insights = content['target_audience_insights']
            if isinstance(insights, dict):
                aggregated['target_audience_insights'].update(insights)
        
        # Sales philosophy (use latest non-empty)
        if 'sales_philosophy' in content and content['sales_philosophy']:
            aggregated['sales_philosophy'] = content['sales_philosophy']
        
        # Industry context (merge)
        if 'industry_context' in content:
            context = content['industry_context']
            if isinstance(context, dict):
                aggregated['industry_context'].update(context)
        
        # Practical advice (append unique)
        if 'practical_advice' in content:
            advice = content['practical_advice']
            if isinstance(advice, list):
                for item in advice:
                    if item not in aggregated['practical_advice']:
                        aggregated['practical_advice'].append(item)
    
    def _post_process_aggregated_knowledge(self, aggregated: Dict[str, Any]):
        """Post-process aggregated knowledge to ensure consistency."""
        # Ensure all lists are not None
        for key in ['products', 'value_propositions', 'competitive_advantages', 'key_messages', 
                   'sales_methodologies', 'practical_advice']:
            if aggregated[key] is None:
                aggregated[key] = []
        
        # Ensure all dicts are not None
        for key in ['company_info', 'target_audience', 'target_audience_insights', 'industry_context']:
            if aggregated[key] is None:
                aggregated[key] = {}
        
        # Ensure strings are not None
        for key in ['sales_approach', 'sales_philosophy']:
            if aggregated[key] is None:
                aggregated[key] = ""
    
    def _generate_cache_key(self, tenant_id: str, user_id: str, task_type: str = None) -> str:
        """Generate cache key for knowledge retrieval."""
        key_string = f"{tenant_id}:{user_id}:{task_type or 'all'}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get knowledge from cache if valid."""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return cached_data
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, knowledge: Dict[str, Any]):
        """Store knowledge in cache."""
        self._cache[cache_key] = (knowledge, datetime.now())
        
        # Simple cache cleanup (remove oldest entries if cache gets too large)
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
    
    def _normalize_knowledge_by_type(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize knowledge data based on document type to ensure consistent structure.
        
        Args:
            knowledge_data: Raw knowledge data from extraction
            
        Returns:
            Normalized knowledge structure
        """
        document_type = knowledge_data.get('document_type', 'company_info')
        
        # Debug logging
        logger.info(f"🔍 Normalizing knowledge with document_type: {document_type}")
        logger.info(f"📋 Knowledge keys: {list(knowledge_data.keys())}")
        
        # If no document_type is specified, try to infer from content
        if document_type == 'company_info' and not knowledge_data.get('company_info'):
            # Check if this looks like sales training content
            if (knowledge_data.get('sales_methodologies') or 
                knowledge_data.get('target_audience_insights') or
                knowledge_data.get('practical_advice') or
                knowledge_data.get('sales_philosophy')):
                document_type = 'sales_training'
                logger.info(f"🔄 Inferred document_type as sales_training")
            # Check if this looks like industry knowledge
            elif (knowledge_data.get('industry_insights') or
                  knowledge_data.get('buyer_behavior') or
                  knowledge_data.get('sales_opportunities')):
                document_type = 'industry_knowledge'
                logger.info(f"🔄 Inferred document_type as industry_knowledge")
        
        logger.info(f"✅ Final document_type: {document_type}")
        
        if document_type == 'sales_training':
            return self._normalize_sales_training_knowledge(knowledge_data)
        elif document_type == 'industry_knowledge':
            return self._normalize_industry_knowledge(knowledge_data)
        else:
            # Default to company_info structure
            return self._normalize_company_info_knowledge(knowledge_data)
    
    def _normalize_company_info_knowledge(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize company info knowledge to standard structure"""
        return {
            "document_type": "company_info",
            "company_info": knowledge_data.get('company_info', {}),
            "sales_approach": knowledge_data.get('sales_approach', ''),
            "products": knowledge_data.get('products', []),
            "key_messages": knowledge_data.get('key_messages', []),
            "value_propositions": knowledge_data.get('value_propositions', []),
            "target_audience": knowledge_data.get('target_audience', {}),
            "competitive_advantages": knowledge_data.get('competitive_advantages', [])
        }
    
    def _normalize_sales_training_knowledge(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize sales training knowledge to standard structure"""
        # Extract sales methodologies and convert to sales approach
        sales_methodologies = knowledge_data.get('sales_methodologies', [])
        sales_approach = knowledge_data.get('sales_philosophy', '')
        if sales_methodologies:
            sales_approach = f"{sales_approach}. Key methodologies: {', '.join(sales_methodologies)}"
        
        # Extract target audience insights
        audience_insights = knowledge_data.get('target_audience_insights', {})
        target_audience = {
            "primary_customers": ', '.join(audience_insights.get('buyer_personas', [])),
            "industries": knowledge_data.get('industry_context', {}).get('industries_mentioned', []),
            "company_sizes": [],
            "pain_points": audience_insights.get('pain_points', [])
        }
        
        # Extract key messages and practical advice
        key_messages = knowledge_data.get('key_messages', [])
        practical_advice = knowledge_data.get('practical_advice', [])
        all_messages = key_messages + practical_advice
        
        return {
            "document_type": "sales_training",
            "company_info": {
                "company_name": "Sales Training Knowledge",
                "industry": "Sales Training",
                "company_size": "Not specified",
                "mission": "Improve sales effectiveness",
                "values": [],
                "founding_year": "Not specified",
                "headquarters": "Not specified"
            },
            "sales_approach": sales_approach,
            "products": [],
            "key_messages": all_messages,
            "value_propositions": knowledge_data.get('key_messages', []),
            "target_audience": target_audience,
            "competitive_advantages": knowledge_data.get('practical_advice', [])
        }
    
    def _normalize_industry_knowledge(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize industry knowledge to standard structure"""
        industry_insights = knowledge_data.get('industry_insights', {})
        buyer_behavior = knowledge_data.get('buyer_behavior', {})
        
        # Extract target audience from buyer behavior
        target_audience = {
            "primary_customers": ', '.join(buyer_behavior.get('decision_makers', [])),
            "industries": industry_insights.get('industries_covered', []),
            "company_sizes": [],
            "pain_points": buyer_behavior.get('pain_points', [])
        }
        
        # Extract sales opportunities as value propositions
        sales_opportunities = knowledge_data.get('sales_opportunities', [])
        
        return {
            "document_type": "industry_knowledge",
            "company_info": {
                "company_name": "Industry Knowledge Base",
                "industry": ', '.join(industry_insights.get('industries_covered', [])),
                "company_size": "Not specified",
                "mission": "Industry insights and market intelligence",
                "values": [],
                "founding_year": "Not specified",
                "headquarters": "Not specified"
            },
            "sales_approach": f"Industry-focused approach based on market trends: {', '.join(industry_insights.get('growth_trends', []))}",
            "products": [],
            "key_messages": sales_opportunities,
            "value_propositions": sales_opportunities,
            "target_audience": target_audience,
            "competitive_advantages": knowledge_data.get('competitive_intelligence', [])
        }
    
    def get_company_context(self, tenant_id: str, user_id: str, task_type: str = None) -> str:
        """
        Get formatted company context for AI prompts.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            task_type: Optional task type for smart filtering
            
        Returns:
            Formatted string with company context
        """
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return self._format_knowledge_for_prompts(knowledge)
    
    def get_target_audience(self, tenant_id: str, user_id: str, task_type: str = None) -> Dict[str, Any]:
        """Get target audience information"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('target_audience', {})
    
    def get_value_propositions(self, tenant_id: str, user_id: str, task_type: str = None) -> List[str]:
        """Get value propositions"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('value_propositions', [])
    
    def get_products(self, tenant_id: str, user_id: str, task_type: str = None) -> List[Dict[str, Any]]:
        """Get products information"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('products', [])
    
    def get_sales_approach(self, tenant_id: str, user_id: str, task_type: str = None) -> str:
        """Get sales approach"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('sales_approach', '')
    
    def get_competitive_advantages(self, tenant_id: str, user_id: str, task_type: str = None) -> List[str]:
        """Get competitive advantages"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('competitive_advantages', [])
    
    def get_company_info(self, tenant_id: str, user_id: str, task_type: str = None) -> Dict[str, Any]:
        """Get company information"""
        knowledge = self.get_user_knowledge(tenant_id, user_id, task_type)
        return knowledge.get('company_info', {})
    
    def _format_knowledge_for_prompts(self, knowledge: Dict[str, Any]) -> str:
        """
        Format knowledge data into a readable string for AI prompts.
        
        Args:
            knowledge: Knowledge dictionary
            
        Returns:
            Formatted string with company context
        """
        try:
            document_type = knowledge.get('document_type', 'company_info')
            company_info = knowledge.get('company_info', {})
            products = knowledge.get('products', [])
            target_audience = knowledge.get('target_audience', {})
            value_propositions = knowledge.get('value_propositions', [])
            sales_approach = knowledge.get('sales_approach', '')
            competitive_advantages = knowledge.get('competitive_advantages', [])
            
            context_parts = []
            
            # Add document type context
            if document_type == 'sales_training':
                context_parts.append("📚 SALES TRAINING KNOWLEDGE:")
                context_parts.append("This knowledge comes from sales training materials and best practices.")
            elif document_type == 'industry_knowledge':
                context_parts.append("🏭 INDUSTRY KNOWLEDGE:")
                context_parts.append("This knowledge comes from industry research and market intelligence.")
            else:
                context_parts.append("🏢 COMPANY KNOWLEDGE:")
                context_parts.append("This knowledge comes from company-specific documents.")
            
            # Company information
            if company_info:
                context_parts.append("\nCompany Information:")
                for key, value in company_info.items():
                    if value and value != "Not specified":
                        context_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
            
            # Products
            if products:
                context_parts.append("\nProducts/Services:")
                for product in products:
                    if isinstance(product, dict):
                        name = product.get('name', 'Unknown Product')
                        description = product.get('description', 'No description')
                        context_parts.append(f"- {name}: {description}")
                    else:
                        context_parts.append(f"- {product}")
            
            # Target audience
            if target_audience:
                context_parts.append("\nTarget Audience:")
                for key, value in target_audience.items():
                    if value:
                        context_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
            
            # Value propositions
            if value_propositions:
                context_parts.append("\nValue Propositions:")
                for i, prop in enumerate(value_propositions, 1):
                    context_parts.append(f"{i}. {prop}")
            
            # Sales approach
            if sales_approach:
                context_parts.append(f"\nSales Approach: {sales_approach}")
            
            # Competitive advantages
            if competitive_advantages:
                context_parts.append("\nCompetitive Advantages:")
                for i, advantage in enumerate(competitive_advantages, 1):
                    context_parts.append(f"{i}. {advantage}")
            
            return "\n".join(context_parts) if context_parts else "No company information available."
            
        except Exception as e:
            logger.error(f"Error formatting knowledge: {e}")
            return "Error formatting company information."
    
    def _get_default_knowledge(self) -> Dict[str, Any]:
        """
        Get default knowledge structure when no user knowledge is available.
        
        Returns:
            Default knowledge dictionary
        """
        return {
            "document_type": "company_info",
            "company_info": {
                "name": "Unknown Company",
                "industry": "Technology",
                "description": "Technology company"
            },
            "products": [],
            "target_audience": {
                "industry": "Technology",
                "company_size": "Mid-size",
                "job_titles": ["Decision Makers"],
                "pain_points": ["Efficiency", "Cost"]
            },
            "value_propositions": [],
            "sales_approach": "Consultative selling approach",
            "competitive_advantages": [],
            "key_messages": []
        }
    
    def build_knowledge_enhanced_prompt(self, base_prompt: str, tenant_id: str, user_id: str) -> str:
        """
        Enhance prompts with user's company knowledge.
        
        Args:
            base_prompt: Original prompt
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            Enhanced prompt with company context
        """
        company_context = self.get_company_context(tenant_id, user_id)
        
        enhanced_prompt = f"""
COMPANY CONTEXT:
{company_context}

TASK:
{base_prompt}

INSTRUCTIONS:
- Use the company context above to personalize your response
- Reference specific products, value propositions, and target audience when relevant
- Maintain the company's sales approach and voice
- Incorporate competitive advantages where appropriate
"""
        
        return enhanced_prompt.strip()
