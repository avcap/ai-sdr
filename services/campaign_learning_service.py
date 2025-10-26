import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class CampaignLearningService:
    """
    Service for tracking campaign execution results and learning from successful patterns.
    Analyzes historical campaign data to improve future suggestions.
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        
    def record_campaign_execution(self, tenant_id: str, user_id: str, 
                                prompt_data: Dict[str, Any], 
                                results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record campaign execution for learning.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            prompt_data: Original prompt and suggestion data
            results: Campaign execution results
            
        Returns:
            Execution record data
        """
        try:
            logger.info(f"Recording campaign execution for user {user_id}")
            
            # Calculate success metrics
            success_metrics = self.calculate_success_metrics(results)
            
            # Prepare execution data
            execution_data = {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'campaign_id': results.get('campaign_id'),
                'original_prompt': prompt_data.get('original_prompt', ''),
                'suggested_prompt_id': prompt_data.get('suggested_prompt_id'),
                'execution_results': json.dumps(results),
                'lead_count': results.get('lead_count', 0),
                'quality_score': success_metrics.get('overall_score', 0.0),
                'user_feedback': json.dumps(prompt_data.get('user_feedback', {})),
                'executed_at': datetime.now().isoformat()
            }
            
            # Save to database
            execution_record = self.supabase.save_campaign_execution(execution_data)
            
            # Update suggestion performance if suggestion was used
            if prompt_data.get('suggested_prompt_id'):
                self.update_suggestion_performance(
                    prompt_data['suggested_prompt_id'], 
                    success_metrics
                )
            
            # Extract and save successful patterns
            self._extract_and_save_patterns(tenant_id, prompt_data, success_metrics)
            
            logger.info(f"Campaign execution recorded with quality score: {success_metrics.get('overall_score', 0.0)}")
            return execution_record
            
        except Exception as e:
            logger.error(f"Error recording campaign execution: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_successful_patterns(self, tenant_id: str, user_id: str, 
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """
        Analyze successful campaign patterns from historical data.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            limit: Maximum number of executions to analyze
            
        Returns:
            List of successful patterns
        """
        try:
            logger.info(f"Analyzing successful patterns for user {user_id}")
            
            # Get execution history
            executions = self.supabase.get_campaign_execution_history(tenant_id, user_id, limit)
            
            if not executions:
                logger.warning("No execution history found")
                return []
            
            # Filter successful executions (quality score > 0.7)
            successful_executions = [
                exec for exec in executions 
                if exec.get('quality_score', 0) > 0.7
            ]
            
            if not successful_executions:
                logger.warning("No successful executions found")
                return []
            
            # Analyze patterns
            patterns = self._analyze_patterns(successful_executions)
            
            logger.info(f"Found {len(patterns)} successful patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing successful patterns: {e}")
            return []
    
    def improve_suggestions(self, tenant_id: str, user_id: str, 
                          current_suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Improve suggestions based on historical performance.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            current_suggestions: Current suggestions to improve
            
        Returns:
            Improved suggestions
        """
        try:
            logger.info(f"Improving suggestions for user {user_id}")
            
            # Get successful patterns
            patterns = self.analyze_successful_patterns(tenant_id, user_id)
            
            if not patterns:
                logger.info("No patterns found, returning original suggestions")
                return current_suggestions
            
            # Apply pattern-based improvements
            improved_suggestions = self._apply_pattern_improvements(
                current_suggestions, patterns
            )
            
            logger.info(f"Improved {len(improved_suggestions)} suggestions")
            return improved_suggestions
            
        except Exception as e:
            logger.error(f"Error improving suggestions: {e}")
            return current_suggestions
    
    def calculate_success_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate success metrics from campaign results.
        
        Args:
            results: Campaign execution results
            
        Returns:
            Success metrics dictionary
        """
        try:
            metrics = {
                'lead_count': results.get('lead_count', 0),
                'quality_score': 0.0,
                'response_rate': 0.0,
                'engagement_score': 0.0,
                'overall_score': 0.0
            }
            
            # Calculate quality score based on lead count and quality
            lead_count = metrics['lead_count']
            if lead_count > 0:
                # Base quality score from lead count
                if lead_count >= 20:
                    metrics['quality_score'] = 0.9
                elif lead_count >= 10:
                    metrics['quality_score'] = 0.8
                elif lead_count >= 5:
                    metrics['quality_score'] = 0.7
                else:
                    metrics['quality_score'] = 0.6
                
                # Adjust based on lead quality indicators
                if results.get('high_quality_leads', 0) > 0:
                    metrics['quality_score'] = min(1.0, metrics['quality_score'] + 0.1)
                
                # Adjust based on campaign success indicators
                if results.get('campaign_success', False):
                    metrics['quality_score'] = min(1.0, metrics['quality_score'] + 0.1)
            
            # Calculate response rate (if available)
            if results.get('responses', 0) > 0 and lead_count > 0:
                metrics['response_rate'] = results['responses'] / lead_count
            
            # Calculate engagement score
            engagement_indicators = [
                results.get('opens', 0),
                results.get('clicks', 0),
                results.get('replies', 0)
            ]
            if any(engagement_indicators):
                metrics['engagement_score'] = sum(engagement_indicators) / (lead_count * 3)
            
            # Calculate overall score
            metrics['overall_score'] = (
                metrics['quality_score'] * 0.5 +
                metrics['response_rate'] * 0.3 +
                metrics['engagement_score'] * 0.2
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating success metrics: {e}")
            return {'overall_score': 0.5, 'quality_score': 0.5}
    
    def update_suggestion_performance(self, suggestion_id: str, 
                                   success_metrics: Dict[str, Any]) -> bool:
        """
        Update suggestion performance metrics.
        
        Args:
            suggestion_id: ID of the suggestion
            success_metrics: Success metrics from execution
            
        Returns:
            True if update successful
        """
        try:
            logger.info(f"Updating suggestion performance for {suggestion_id}")
            
            # Calculate new metrics
            new_usage_count = 1  # Increment usage
            new_success_rate = success_metrics.get('overall_score', 0.5)
            
            # Update suggestion in database
            update_data = {
                'usage_count': new_usage_count,
                'success_rate': new_success_rate,
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.supabase.update_suggestion_metrics(suggestion_id, update_data)
            
            logger.info(f"Suggestion performance updated: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating suggestion performance: {e}")
            return False
    
    def _analyze_patterns(self, successful_executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze patterns from successful executions.
        
        Args:
            successful_executions: List of successful execution records
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        try:
            # Analyze prompt patterns
            prompt_patterns = self._analyze_prompt_patterns(successful_executions)
            patterns.extend(prompt_patterns)
            
            # Analyze targeting patterns
            targeting_patterns = self._analyze_targeting_patterns(successful_executions)
            patterns.extend(targeting_patterns)
            
            # Analyze timing patterns
            timing_patterns = self._analyze_timing_patterns(successful_executions)
            patterns.extend(timing_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return []
    
    def _analyze_prompt_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze prompt patterns from successful executions.
        
        Args:
            executions: Successful execution records
            
        Returns:
            List of prompt patterns
        """
        patterns = []
        
        try:
            # Extract common prompt elements
            prompt_elements = []
            for execution in executions:
                prompt = execution.get('original_prompt', '')
                if prompt:
                    # Extract key elements (roles, industries, company sizes)
                    elements = self._extract_prompt_elements(prompt)
                    prompt_elements.extend(elements)
            
            # Find most common elements
            element_counts = Counter(prompt_elements)
            common_elements = element_counts.most_common(5)
            
            # Create patterns from common elements
            for element, count in common_elements:
                if count >= 2:  # At least 2 occurrences
                    patterns.append({
                        'pattern_type': 'prompt_element',
                        'pattern_template': element,
                        'success_count': count,
                        'avg_quality_score': 0.8,  # Default for successful patterns
                        'metadata': {'element_type': self._categorize_element(element)}
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing prompt patterns: {e}")
            return []
    
    def _analyze_targeting_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze targeting patterns from successful executions.
        
        Args:
            executions: Successful execution records
            
        Returns:
            List of targeting patterns
        """
        patterns = []
        
        try:
            # Extract targeting information from prompts
            targeting_info = []
            for execution in executions:
                prompt = execution.get('original_prompt', '')
                if prompt:
                    targeting = self._extract_targeting_info(prompt)
                    if targeting:
                        targeting_info.append(targeting)
            
            # Analyze common targeting combinations
            if targeting_info:
                # Find most successful role + industry combinations
                role_industry_combos = [
                    f"{t.get('role', '')} + {t.get('industry', '')}" 
                    for t in targeting_info
                ]
                combo_counts = Counter(role_industry_combos)
                
                for combo, count in combo_counts.most_common(3):
                    if count >= 2:
                        patterns.append({
                            'pattern_type': 'targeting_combo',
                            'pattern_template': combo,
                            'success_count': count,
                            'avg_quality_score': 0.8,
                            'metadata': {'combo_type': 'role_industry'}
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing targeting patterns: {e}")
            return []
    
    def _analyze_timing_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze timing patterns from successful executions.
        
        Args:
            executions: Successful execution records
            
        Returns:
            List of timing patterns
        """
        patterns = []
        
        try:
            # Analyze execution timing
            execution_times = []
            for execution in executions:
                executed_at = execution.get('executed_at')
                if executed_at:
                    dt = datetime.fromisoformat(executed_at.replace('Z', '+00:00'))
                    execution_times.append(dt)
            
            if execution_times:
                # Find most successful execution days/times
                day_counts = Counter([dt.weekday() for dt in execution_times])
                hour_counts = Counter([dt.hour for dt in execution_times])
                
                # Most successful day
                most_successful_day = day_counts.most_common(1)[0]
                if most_successful_day[1] >= 2:
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    patterns.append({
                        'pattern_type': 'timing_day',
                        'pattern_template': day_names[most_successful_day[0]],
                        'success_count': most_successful_day[1],
                        'avg_quality_score': 0.8,
                        'metadata': {'timing_type': 'day_of_week'}
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {e}")
            return []
    
    def _extract_prompt_elements(self, prompt: str) -> List[str]:
        """
        Extract key elements from a prompt.
        
        Args:
            prompt: The prompt text
            
        Returns:
            List of extracted elements
        """
        elements = []
        prompt_lower = prompt.lower()
        
        # Extract roles
        roles = ['cto', 'vp', 'director', 'head of', 'manager', 'ceo', 'founder']
        for role in roles:
            if role in prompt_lower:
                elements.append(f"role:{role}")
        
        # Extract industries
        industries = ['saas', 'tech', 'software', 'ai', 'fintech', 'healthcare', 'ecommerce']
        for industry in industries:
            if industry in prompt_lower:
                elements.append(f"industry:{industry}")
        
        # Extract company sizes
        if 'enterprise' in prompt_lower or '500+' in prompt_lower:
            elements.append("size:enterprise")
        elif 'startup' in prompt_lower or '50-' in prompt_lower:
            elements.append("size:startup")
        elif 'mid-market' in prompt_lower or '200' in prompt_lower:
            elements.append("size:mid-market")
        
        return elements
    
    def _extract_targeting_info(self, prompt: str) -> Dict[str, str]:
        """
        Extract targeting information from a prompt.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Targeting information dictionary
        """
        targeting = {}
        prompt_lower = prompt.lower()
        
        # Extract role
        roles = ['cto', 'vp', 'director', 'head of', 'manager', 'ceo', 'founder']
        for role in roles:
            if role in prompt_lower:
                targeting['role'] = role
                break
        
        # Extract industry
        industries = ['saas', 'tech', 'software', 'ai', 'fintech', 'healthcare', 'ecommerce']
        for industry in industries:
            if industry in prompt_lower:
                targeting['industry'] = industry
                break
        
        return targeting
    
    def _categorize_element(self, element: str) -> str:
        """
        Categorize a prompt element.
        
        Args:
            element: The element string
            
        Returns:
            Element category
        """
        if element.startswith('role:'):
            return 'role'
        elif element.startswith('industry:'):
            return 'industry'
        elif element.startswith('size:'):
            return 'company_size'
        else:
            return 'other'
    
    def _extract_and_save_patterns(self, tenant_id: str, prompt_data: Dict[str, Any], 
                                 success_metrics: Dict[str, Any]) -> None:
        """
        Extract and save patterns from successful execution.
        
        Args:
            tenant_id: User's tenant ID
            prompt_data: Prompt data
            success_metrics: Success metrics
            
        Returns:
            None
        """
        try:
            # Only save patterns for high-quality executions
            if success_metrics.get('overall_score', 0) < 0.7:
                return
            
            # Extract pattern from prompt
            prompt = prompt_data.get('original_prompt', '')
            if not prompt:
                return
            
            # Create pattern data
            pattern_data = {
                'tenant_id': tenant_id,
                'pattern_type': 'successful_prompt',
                'pattern_template': prompt,
                'success_count': 1,
                'avg_quality_score': success_metrics.get('overall_score', 0.7),
                'industry': self._extract_industry_from_prompt(prompt),
                'target_role': self._extract_role_from_prompt(prompt),
                'company_size': self._extract_size_from_prompt(prompt),
                'metadata': json.dumps({
                    'extracted_at': datetime.now().isoformat(),
                    'quality_score': success_metrics.get('overall_score', 0.7)
                })
            }
            
            # Save pattern to database
            self.supabase.save_prompt_pattern(pattern_data)
            
        except Exception as e:
            logger.error(f"Error extracting and saving patterns: {e}")
    
    def _extract_industry_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract industry from prompt."""
        prompt_lower = prompt.lower()
        industries = ['saas', 'tech', 'software', 'ai', 'fintech', 'healthcare', 'ecommerce']
        for industry in industries:
            if industry in prompt_lower:
                return industry
        return None
    
    def _extract_role_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract role from prompt."""
        prompt_lower = prompt.lower()
        roles = ['cto', 'vp', 'director', 'head of', 'manager', 'ceo', 'founder']
        for role in roles:
            if role in prompt_lower:
                return role
        return None
    
    def _extract_size_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract company size from prompt."""
        prompt_lower = prompt.lower()
        if 'enterprise' in prompt_lower or '500+' in prompt_lower:
            return 'enterprise'
        elif 'startup' in prompt_lower or '50-' in prompt_lower:
            return 'startup'
        elif 'mid-market' in prompt_lower or '200' in prompt_lower:
            return 'mid-market'
        return None
    
    def _apply_pattern_improvements(self, suggestions: List[Dict[str, Any]], 
                                  patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply pattern-based improvements to suggestions.
        
        Args:
            suggestions: Current suggestions
            patterns: Successful patterns
            
        Returns:
            Improved suggestions
        """
        improved_suggestions = []
        
        try:
            for suggestion in suggestions:
                improved_suggestion = suggestion.copy()
                
                # Apply pattern-based confidence adjustments
                prompt = suggestion.get('prompt', '')
                for pattern in patterns:
                    if self._pattern_matches_prompt(pattern, prompt):
                        # Increase confidence for pattern matches
                        current_confidence = improved_suggestion.get('confidence', 0.7)
                        improved_suggestion['confidence'] = min(1.0, current_confidence + 0.1)
                        
                        # Add pattern-based reasoning
                        reasoning = improved_suggestion.get('reasoning', '')
                        pattern_reason = f" Based on successful pattern: {pattern.get('pattern_template', '')}"
                        improved_suggestion['reasoning'] = reasoning + pattern_reason
                
                improved_suggestions.append(improved_suggestion)
            
            return improved_suggestions
            
        except Exception as e:
            logger.error(f"Error applying pattern improvements: {e}")
            return suggestions
    
    def _pattern_matches_prompt(self, pattern: Dict[str, Any], prompt: str) -> bool:
        """
        Check if a pattern matches a prompt.
        
        Args:
            pattern: Pattern dictionary
            prompt: Prompt text
            
        Returns:
            True if pattern matches
        """
        try:
            pattern_template = pattern.get('pattern_template', '').lower()
            prompt_lower = prompt.lower()
            
            # Simple substring matching for now
            # Could be enhanced with more sophisticated matching
            return pattern_template in prompt_lower
            
        except Exception as e:
            logger.error(f"Error checking pattern match: {e}")
            return False
