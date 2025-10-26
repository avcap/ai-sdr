import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from services.supabase_service import SupabaseService
from services.knowledge_service import KnowledgeService
import anthropic

logger = logging.getLogger(__name__)

class SalesPlaybookService:
    """
    Adaptive sales playbook service that intelligently selects appropriate
    sales strategies based on company context and user's sales training.
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.knowledge_service = KnowledgeService()
        self.claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def get_adaptive_strategies(self, tenant_id: str, user_id: str, campaign_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adaptive sales strategies based on context.
        
        Priority:
        1. User's uploaded sales training (if available)
        2. LLM-selected framework from library
        3. Universal SDR fundamentals
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            campaign_context: Context from campaign intelligence (company, industry, etc.)
            
        Returns:
            Dict containing selected strategies, reasoning, and confidence
        """
        try:
            logger.info(f"Getting adaptive strategies for user {user_id}")
            
            # Check if user has uploaded sales training documents
            user_sales_training = self._get_user_sales_training(tenant_id, user_id)
            
            if user_sales_training:
                logger.info("Using user's uploaded sales training")
                return {
                    'source': 'user_training',
                    'strategies': user_sales_training,
                    'confidence': 0.95,
                    'reasoning': 'Using your uploaded sales training and proven methodologies'
                }
            
            # Use LLM to select appropriate framework from library
            logger.info("No user training found, using LLM framework selection")
            selected_framework = self._llm_select_framework(campaign_context)
            
            return {
                'source': 'adaptive_library',
                'strategies': selected_framework,
                'confidence': selected_framework.get('confidence', 0.75),
                'reasoning': selected_framework.get('reasoning', 'Selected based on company profile and industry')
            }
            
        except Exception as e:
            logger.error(f"Error getting adaptive strategies: {e}")
            # Fallback to universal fundamentals
            return self._get_universal_fundamentals()
    
    def _get_user_sales_training(self, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract sales training information from user's uploaded documents.
        Uses existing knowledge base with 'sales_training' document_type.
        """
        try:
            # Get knowledge articles tagged as 'sales_training'
            knowledge = self.knowledge_service.get_user_knowledge(
                tenant_id, user_id, task_type='sales_training'
            )
            
            if not knowledge or knowledge.get('source_count', 0) == 0:
                return None
            
            # Extract sales-specific information
            sales_approach = knowledge.get('sales_approach', '')
            value_props = knowledge.get('value_propositions', [])
            target_audience = knowledge.get('target_audience', {})
            competitive_advantages = knowledge.get('competitive_advantages', [])
            
            if not sales_approach and not value_props:
                return None
            
            return {
                'has_training': True,
                'sales_approach': sales_approach,
                'value_propositions': value_props,
                'target_audience': target_audience,
                'competitive_advantages': competitive_advantages,
                'messaging_guidelines': knowledge.get('messaging', ''),
                'qualification_criteria': knowledge.get('qualification_criteria', {}),
                'sources': knowledge.get('sources', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting user sales training: {e}")
            return None
    
    def _llm_select_framework(self, campaign_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Claude to intelligently select the most appropriate sales framework
        from the library based on company context.
        """
        try:
            # Get all frameworks from database
            frameworks_result = self.supabase.client.table('sales_frameworks').select('*').execute()
            frameworks = frameworks_result.data if frameworks_result.data else []
            
            if not frameworks:
                logger.warning("No frameworks found in database")
                return self._get_universal_fundamentals()
            
            # Build context for Claude
            company_name = campaign_context.get('company_name', 'Unknown')
            industry = campaign_context.get('industry', 'Technology')
            products = campaign_context.get('products', [])
            target_audience = campaign_context.get('target_audience', {})
            
            # Create selection prompt
            selection_prompt = f"""
You are a sales strategy expert. Analyze this company profile and select the most appropriate sales framework.

COMPANY PROFILE:
- Company: {company_name}
- Industry: {industry}
- Products: {', '.join(products[:5]) if products else 'Not specified'}
- Target Audience: {json.dumps(target_audience)}

AVAILABLE FRAMEWORKS:
{json.dumps(frameworks, indent=2)}

TASK:
1. Analyze the company profile
2. Select the BEST framework from the library
3. Explain WHY it's the best fit
4. Provide confidence score (0.0-1.0)
5. Suggest any adaptations needed

Return ONLY valid JSON:
{{
    "selected_framework": "framework_name",
    "reasoning": "2-3 sentences explaining why this framework fits",
    "confidence": 0.85,
    "adaptations": ["specific adaptation 1", "specific adaptation 2"],
    "key_tactics": ["tactic 1", "tactic 2", "tactic 3"]
}}
"""
            
            # Call Claude
            logger.info("Calling Claude for framework selection")
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.3,  # Lower temp for more consistent selection
                messages=[{"role": "user", "content": selection_prompt}]
            )
            
            # Parse response
            selection_text = response.content[0].text.strip()
            if "```json" in selection_text:
                selection_text = selection_text.split("```json")[1].split("```")[0].strip()
            
            selection = json.loads(selection_text)
            
            # Get full framework details
            selected_framework_name = selection['selected_framework']
            framework_details = next((f for f in frameworks if f['framework_name'] == selected_framework_name), None)
            
            if framework_details:
                return {
                    **framework_details,
                    'selection_reasoning': selection['reasoning'],
                    'confidence': selection['confidence'],
                    'adaptations': selection.get('adaptations', []),
                    'key_tactics': selection.get('key_tactics', [])
                }
            else:
                logger.warning(f"Selected framework '{selected_framework_name}' not found in database")
                return self._get_universal_fundamentals()
                
        except Exception as e:
            logger.error(f"Error in LLM framework selection: {e}")
            return self._get_universal_fundamentals()
    
    def _get_universal_fundamentals(self) -> Dict[str, Any]:
        """
        Universal SDR fundamentals that apply to all sales approaches.
        Used as fallback when no specific framework is available.
        """
        return {
            'framework_name': 'Universal SDR Fundamentals',
            'description': 'Core principles that apply to all modern sales approaches',
            'confidence': 0.50,
            'tactics': {
                'personalization': {
                    'importance': 'critical',
                    'best_practices': [
                        'Reference specific company news or achievements',
                        'Mention role-specific pain points',
                        'Use prospect\'s own language from LinkedIn/website'
                    ]
                },
                'multi_touch': {
                    'importance': 'high',
                    'sequence': '5-7 touches over 14 days increases response rate by 80%',
                    'channels': ['email', 'linkedin', 'phone']
                },
                'timing': {
                    'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                    'best_times': '9-11am and 2-4pm in prospect timezone',
                    'avoid': 'Mondays before 10am, Fridays after 2pm'
                },
                'messaging': {
                    'value_first': 'Lead with insights, not product features',
                    'keep_brief': 'Initial emails under 100 words get 50% more responses',
                    'clear_cta': 'Single, specific call-to-action'
                }
            }
        }

