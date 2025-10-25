import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from services.knowledge_fusion_service import KnowledgeFusionService
from services.knowledge_quality_service import KnowledgeQualityService
from agents.adaptive_prompt_processor import AdaptivePromptProcessor
from integrations.grok_service import GrokService

logger = logging.getLogger(__name__)

class KnowledgeLevel(Enum):
    """Knowledge availability levels"""
    HIGH = "high"          # Rich document knowledge + prompt
    MEDIUM = "medium"      # Some documents + detailed prompt
    LOW = "low"           # Minimal documents + basic prompt
    PROMPT_ONLY = "prompt_only"  # No documents, detailed prompt only

class AdaptationStrategy(Enum):
    """Adaptation strategies based on knowledge level"""
    DOCUMENT_FIRST = "document_first"      # Use document knowledge primarily
    HYBRID = "hybrid"                      # Balance document + prompt + market
    PROMPT_ENHANCED = "prompt_enhanced"    # Enhanced prompt processing
    MARKET_DRIVEN = "market_driven"        # Market data + prompt generation

@dataclass
class KnowledgeAssessment:
    """Assessment of available knowledge"""
    level: KnowledgeLevel
    document_count: int
    prompt_quality_score: float
    overall_confidence: float
    available_sources: List[str]
    gaps: List[str]

@dataclass
class AdaptationPlan:
    """Plan for adapting agent behavior"""
    strategy: AdaptationStrategy
    confidence_threshold: float
    fallback_strategies: List[AdaptationStrategy]
    required_services: List[str]
    execution_priority: List[str]

class AdaptiveAIAgent:
    """
    Adaptive AI Agent framework that adjusts behavior based on available knowledge.
    Provides intelligent fallbacks and optimization strategies for different scenarios.
    """
    
    def __init__(self):
        self.knowledge_fusion = KnowledgeFusionService()
        self.quality_service = KnowledgeQualityService()
        self.prompt_processor = AdaptivePromptProcessor()
        self.grok_service = GrokService()
        
        # Knowledge level thresholds
        self.knowledge_thresholds = {
            KnowledgeLevel.HIGH: {
                "min_documents": 3,
                "min_prompt_score": 0.7,
                "min_confidence": 0.8
            },
            KnowledgeLevel.MEDIUM: {
                "min_documents": 1,
                "min_prompt_score": 0.5,
                "min_confidence": 0.6
            },
            KnowledgeLevel.LOW: {
                "min_documents": 0,
                "min_prompt_score": 0.3,
                "min_confidence": 0.4
            },
            KnowledgeLevel.PROMPT_ONLY: {
                "min_documents": 0,
                "min_prompt_score": 0.6,
                "min_confidence": 0.5
            }
        }
        
        # Strategy configurations
        self.strategy_configs = {
            AdaptationStrategy.DOCUMENT_FIRST: {
                "primary_source": "document",
                "fallback_sources": ["prompt", "market"],
                "confidence_weight": 0.8,
                "use_cases": ["high_knowledge", "complex_analysis"]
            },
            AdaptationStrategy.HYBRID: {
                "primary_source": "balanced",
                "fallback_sources": ["market"],
                "confidence_weight": 0.7,
                "use_cases": ["medium_knowledge", "general_tasks"]
            },
            AdaptationStrategy.PROMPT_ENHANCED: {
                "primary_source": "prompt",
                "fallback_sources": ["market"],
                "confidence_weight": 0.6,
                "use_cases": ["low_knowledge", "quick_tasks"]
            },
            AdaptationStrategy.MARKET_DRIVEN: {
                "primary_source": "market",
                "fallback_sources": ["prompt"],
                "confidence_weight": 0.5,
                "use_cases": ["prompt_only", "market_analysis"]
            }
        }
    
    def assess_knowledge_level(self, tenant_id: str, user_id: str, 
                             user_prompt: str = None) -> KnowledgeAssessment:
        """
        Assess the knowledge level available for a user/organization.
        
        Args:
            tenant_id: Organization identifier
            user_id: User identifier
            user_prompt: Optional user prompt for assessment
            
        Returns:
            Knowledge assessment with level and details
        """
        logger.info(f"Assessing knowledge level for user {user_id}")
        
        # Get document count (simplified - in real implementation, query database)
        document_count = self._get_document_count(tenant_id, user_id)
        
        # Assess prompt quality if provided
        prompt_quality_score = 0.0
        if user_prompt:
            prompt_assessment = self.prompt_processor.assess_prompt_quality(user_prompt)
            prompt_quality_score = prompt_assessment["overall_score"]
        
        # Determine knowledge level
        knowledge_level = self._determine_knowledge_level(
            document_count, prompt_quality_score
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            document_count, prompt_quality_score, knowledge_level
        )
        
        # Identify available sources
        available_sources = self._identify_available_sources(
            document_count, prompt_quality_score
        )
        
        # Identify knowledge gaps
        gaps = self._identify_knowledge_gaps(knowledge_level, available_sources)
        
        return KnowledgeAssessment(
            level=knowledge_level,
            document_count=document_count,
            prompt_quality_score=prompt_quality_score,
            overall_confidence=overall_confidence,
            available_sources=available_sources,
            gaps=gaps
        )
    
    def select_adaptation_strategy(self, knowledge_level: KnowledgeLevel, 
                                 task_type: str = "general") -> AdaptationPlan:
        """
        Select the optimal adaptation strategy based on knowledge level and task.
        
        Args:
            knowledge_level: Assessed knowledge level
            task_type: Type of task to be performed
            
        Returns:
            Adaptation plan with strategy and execution details
        """
        logger.info(f"Selecting adaptation strategy for {knowledge_level.value} knowledge")
        
        # Select primary strategy
        primary_strategy = self._select_primary_strategy(knowledge_level, task_type)
        
        # Determine fallback strategies
        fallback_strategies = self._get_fallback_strategies(primary_strategy)
        
        # Set confidence threshold
        confidence_threshold = self._get_confidence_threshold(primary_strategy)
        
        # Determine required services
        required_services = self._get_required_services(primary_strategy)
        
        # Set execution priority
        execution_priority = self._get_execution_priority(primary_strategy)
        
        return AdaptationPlan(
            strategy=primary_strategy,
            confidence_threshold=confidence_threshold,
            fallback_strategies=fallback_strategies,
            required_services=required_services,
            execution_priority=execution_priority
        )
    
    def execute_with_strategy(self, strategy: AdaptationStrategy, prompt: str, 
                            context: Dict[str, Any], tenant_id: str = None, 
                            user_id: str = None) -> Dict[str, Any]:
        """
        Execute agent task using the selected adaptation strategy.
        
        Args:
            strategy: Selected adaptation strategy
            prompt: User prompt/request
            context: Additional context
            tenant_id: Organization identifier
            user_id: User identifier
            
        Returns:
            Execution results with strategy metadata
        """
        logger.info(f"Executing with strategy: {strategy.value}")
        
        try:
            # Get strategy configuration
            config = self.strategy_configs[strategy]
            
            # Execute based on strategy
            if strategy == AdaptationStrategy.DOCUMENT_FIRST:
                result = self._execute_document_first(prompt, context, tenant_id, user_id)
            elif strategy == AdaptationStrategy.HYBRID:
                result = self._execute_hybrid(prompt, context, tenant_id, user_id)
            elif strategy == AdaptationStrategy.PROMPT_ENHANCED:
                result = self._execute_prompt_enhanced(prompt, context, tenant_id, user_id)
            elif strategy == AdaptationStrategy.MARKET_DRIVEN:
                result = self._execute_market_driven(prompt, context, tenant_id, user_id)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            # Add strategy metadata
            result["strategy_metadata"] = {
                "strategy_used": strategy.value,
                "confidence_weight": config["confidence_weight"],
                "execution_timestamp": datetime.now().isoformat(),
                "fallback_available": len(config["fallback_sources"]) > 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            # Try fallback strategy
            return self._execute_fallback(strategy, prompt, context, tenant_id, user_id)
    
    def _determine_knowledge_level(self, document_count: int, 
                                 prompt_quality_score: float) -> KnowledgeLevel:
        """Determine knowledge level based on available resources"""
        if document_count >= 3 and prompt_quality_score >= 0.7:
            return KnowledgeLevel.HIGH
        elif document_count >= 1 and prompt_quality_score >= 0.5:
            return KnowledgeLevel.MEDIUM
        elif document_count >= 0 and prompt_quality_score >= 0.6:
            return KnowledgeLevel.PROMPT_ONLY
        else:
            return KnowledgeLevel.LOW
    
    def _calculate_overall_confidence(self, document_count: int, 
                                    prompt_quality_score: float, 
                                    knowledge_level: KnowledgeLevel) -> float:
        """Calculate overall confidence in available knowledge"""
        # Weight document count and prompt quality
        document_weight = min(document_count / 5, 1.0)  # Max 5 documents
        prompt_weight = prompt_quality_score
        
        # Combine with knowledge level multiplier
        level_multipliers = {
            KnowledgeLevel.HIGH: 1.0,
            KnowledgeLevel.MEDIUM: 0.8,
            KnowledgeLevel.LOW: 0.6,
            KnowledgeLevel.PROMPT_ONLY: 0.7
        }
        
        base_confidence = (document_weight * 0.6 + prompt_weight * 0.4)
        return base_confidence * level_multipliers[knowledge_level]
    
    def _identify_available_sources(self, document_count: int, 
                                  prompt_quality_score: float) -> List[str]:
        """Identify available knowledge sources"""
        sources = []
        
        if document_count > 0:
            sources.append("document")
        
        if prompt_quality_score > 0.3:
            sources.append("prompt")
        
        # Market data is always available (with Grok service)
        sources.append("market")
        
        return sources
    
    def _identify_knowledge_gaps(self, knowledge_level: KnowledgeLevel, 
                               available_sources: List[str]) -> List[str]:
        """Identify knowledge gaps based on level and sources"""
        gaps = []
        
        if knowledge_level == KnowledgeLevel.LOW:
            gaps.extend([
                "Limited company information",
                "Insufficient product details",
                "Weak value propositions"
            ])
        
        if knowledge_level == KnowledgeLevel.PROMPT_ONLY:
            gaps.extend([
                "No document-based knowledge",
                "Reliance on prompt interpretation",
                "Limited historical context"
            ])
        
        if "document" not in available_sources:
            gaps.append("No document knowledge available")
        
        if "prompt" not in available_sources:
            gaps.append("Poor prompt quality")
        
        return gaps
    
    def _select_primary_strategy(self, knowledge_level: KnowledgeLevel, 
                               task_type: str) -> AdaptationStrategy:
        """Select primary adaptation strategy"""
        strategy_map = {
            KnowledgeLevel.HIGH: AdaptationStrategy.DOCUMENT_FIRST,
            KnowledgeLevel.MEDIUM: AdaptationStrategy.HYBRID,
            KnowledgeLevel.LOW: AdaptationStrategy.PROMPT_ENHANCED,
            KnowledgeLevel.PROMPT_ONLY: AdaptationStrategy.MARKET_DRIVEN
        }
        
        # Override based on task type
        if task_type in ["market_analysis", "trend_analysis"]:
            return AdaptationStrategy.MARKET_DRIVEN
        elif task_type in ["quick_task", "simple_query"]:
            return AdaptationStrategy.PROMPT_ENHANCED
        
        return strategy_map[knowledge_level]
    
    def _get_fallback_strategies(self, primary_strategy: AdaptationStrategy) -> List[AdaptationStrategy]:
        """Get fallback strategies for primary strategy"""
        fallback_map = {
            AdaptationStrategy.DOCUMENT_FIRST: [
                AdaptationStrategy.HYBRID,
                AdaptationStrategy.PROMPT_ENHANCED
            ],
            AdaptationStrategy.HYBRID: [
                AdaptationStrategy.PROMPT_ENHANCED,
                AdaptationStrategy.MARKET_DRIVEN
            ],
            AdaptationStrategy.PROMPT_ENHANCED: [
                AdaptationStrategy.MARKET_DRIVEN
            ],
            AdaptationStrategy.MARKET_DRIVEN: [
                AdaptationStrategy.PROMPT_ENHANCED
            ]
        }
        
        return fallback_map.get(primary_strategy, [])
    
    def _get_confidence_threshold(self, strategy: AdaptationStrategy) -> float:
        """Get confidence threshold for strategy"""
        thresholds = {
            AdaptationStrategy.DOCUMENT_FIRST: 0.8,
            AdaptationStrategy.HYBRID: 0.7,
            AdaptationStrategy.PROMPT_ENHANCED: 0.6,
            AdaptationStrategy.MARKET_DRIVEN: 0.5
        }
        
        return thresholds.get(strategy, 0.6)
    
    def _get_required_services(self, strategy: AdaptationStrategy) -> List[str]:
        """Get required services for strategy"""
        service_map = {
            AdaptationStrategy.DOCUMENT_FIRST: [
                "knowledge_fusion", "quality_service"
            ],
            AdaptationStrategy.HYBRID: [
                "knowledge_fusion", "prompt_processor", "grok_service"
            ],
            AdaptationStrategy.PROMPT_ENHANCED: [
                "prompt_processor", "grok_service"
            ],
            AdaptationStrategy.MARKET_DRIVEN: [
                "grok_service", "prompt_processor"
            ]
        }
        
        return service_map.get(strategy, [])
    
    def _get_execution_priority(self, strategy: AdaptationStrategy) -> List[str]:
        """Get execution priority for strategy"""
        priority_map = {
            AdaptationStrategy.DOCUMENT_FIRST: [
                "document_knowledge", "prompt_analysis", "market_context"
            ],
            AdaptationStrategy.HYBRID: [
                "prompt_analysis", "document_knowledge", "market_context", "knowledge_fusion"
            ],
            AdaptationStrategy.PROMPT_ENHANCED: [
                "prompt_analysis", "market_context", "knowledge_generation"
            ],
            AdaptationStrategy.MARKET_DRIVEN: [
                "market_analysis", "prompt_analysis", "context_generation"
            ]
        }
        
        return priority_map.get(strategy, [])
    
    def _execute_document_first(self, prompt: str, context: Dict[str, Any], 
                              tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Execute with document-first strategy"""
        logger.info("Executing document-first strategy")
        
        # Get document knowledge (simplified - in real implementation, query database)
        document_knowledge = self._get_document_knowledge(tenant_id, user_id)
        
        # Analyze prompt
        prompt_analysis = self.prompt_processor.analyze_detailed_prompt(prompt)
        
        # Get market context
        market_context = self._get_market_context(prompt, context)
        
        # Fuse knowledge sources
        fused_knowledge = self.knowledge_fusion.combine_knowledge_sources(
            document_knowledge=document_knowledge,
            prompt_knowledge=prompt_analysis.get("business_context"),
            market_data=market_context
        )
        
        return {
            "success": True,
            "knowledge": fused_knowledge,
            "strategy": "document_first",
            "sources_used": ["document", "prompt", "market"]
        }
    
    def _execute_hybrid(self, prompt: str, context: Dict[str, Any], 
                       tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Execute with hybrid strategy"""
        logger.info("Executing hybrid strategy")
        
        # Get available knowledge sources
        document_knowledge = self._get_document_knowledge(tenant_id, user_id)
        prompt_analysis = self.prompt_processor.analyze_detailed_prompt(prompt)
        market_context = self._get_market_context(prompt, context)
        
        # Generate adaptive knowledge if needed
        if not document_knowledge:
            adaptive_knowledge = self.prompt_processor.generate_adaptive_knowledge(
                prompt_analysis.get("business_context", {})
            )
        else:
            adaptive_knowledge = None
        
        # Fuse all available sources
        fused_knowledge = self.knowledge_fusion.combine_knowledge_sources(
            document_knowledge=document_knowledge,
            prompt_knowledge=prompt_analysis.get("business_context"),
            market_data=market_context
        )
        
        # Add adaptive knowledge if generated
        if adaptive_knowledge:
            fused_knowledge["adaptive_knowledge"] = adaptive_knowledge
        
        return {
            "success": True,
            "knowledge": fused_knowledge,
            "strategy": "hybrid",
            "sources_used": ["document", "prompt", "market", "adaptive"]
        }
    
    def _execute_prompt_enhanced(self, prompt: str, context: Dict[str, Any], 
                               tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Execute with prompt-enhanced strategy"""
        logger.info("Executing prompt-enhanced strategy")
        
        # Enhanced prompt analysis
        prompt_analysis = self.prompt_processor.analyze_detailed_prompt(prompt)
        
        # Generate comprehensive knowledge from prompt
        adaptive_knowledge = self.prompt_processor.generate_adaptive_knowledge(
            prompt_analysis.get("business_context", {})
        )
        
        # Get market context for enhancement
        market_context = self._get_market_context(prompt, context)
        
        # Combine prompt-generated knowledge with market data
        enhanced_knowledge = self.knowledge_fusion.combine_knowledge_sources(
            prompt_knowledge=prompt_analysis.get("business_context"),
            market_data=market_context
        )
        
        # Add adaptive knowledge
        enhanced_knowledge["adaptive_knowledge"] = adaptive_knowledge
        
        return {
            "success": True,
            "knowledge": enhanced_knowledge,
            "strategy": "prompt_enhanced",
            "sources_used": ["prompt", "market", "adaptive"]
        }
    
    def _execute_market_driven(self, prompt: str, context: Dict[str, Any], 
                             tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Execute with market-driven strategy"""
        logger.info("Executing market-driven strategy")
        
        # Analyze prompt for market context
        prompt_analysis = self.prompt_processor.analyze_detailed_prompt(prompt)
        
        # Get comprehensive market data
        market_context = self._get_market_context(prompt, context)
        
        # Generate market-informed knowledge
        business_context = prompt_analysis.get("business_context", {})
        industry = business_context.get("company_info", {}).get("industry", "Technology")
        
        # Get industry trends and competitive intelligence
        industry_trends = self.grok_service.get_industry_trends(industry)
        competitive_intel = self.grok_service.get_competitive_intelligence(
            business_context.get("company_info", {}).get("company_name", "Company"),
            business_context.get("competitive_advantages", [])
        )
        
        # Combine market data
        market_driven_knowledge = {
            "market_context": market_context,
            "industry_trends": industry_trends,
            "competitive_intelligence": competitive_intel,
            "prompt_context": business_context
        }
        
        return {
            "success": True,
            "knowledge": market_driven_knowledge,
            "strategy": "market_driven",
            "sources_used": ["market", "prompt", "trends", "competitive"]
        }
    
    def _execute_fallback(self, failed_strategy: AdaptationStrategy, prompt: str, 
                        context: Dict[str, Any], tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Execute fallback strategy when primary fails"""
        logger.warning(f"Executing fallback for failed strategy: {failed_strategy.value}")
        
        # Get fallback strategies
        fallback_strategies = self._get_fallback_strategies(failed_strategy)
        
        # Try first fallback strategy
        if fallback_strategies:
            fallback_strategy = fallback_strategies[0]
            return self.execute_with_strategy(
                fallback_strategy, prompt, context, tenant_id, user_id
            )
        
        # Ultimate fallback - basic prompt processing
        return self._execute_basic_fallback(prompt, context)
    
    def _execute_basic_fallback(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute basic fallback when all strategies fail"""
        logger.warning("Executing basic fallback strategy")
        
        try:
            # Basic prompt analysis
            prompt_analysis = self.prompt_processor.analyze_detailed_prompt(prompt)
            
            return {
                "success": True,
                "knowledge": prompt_analysis.get("business_context", {}),
                "strategy": "basic_fallback",
                "sources_used": ["prompt"],
                "warning": "Limited functionality due to fallback mode"
            }
        except Exception as e:
            logger.error(f"Basic fallback failed: {e}")
            return {
                "success": False,
                "error": "All strategies failed",
                "strategy": "failed",
                "sources_used": []
            }
    
    def _get_document_count(self, tenant_id: str, user_id: str) -> int:
        """Get document count for user (simplified implementation)"""
        # In real implementation, query database
        # For now, return mock data
        return 2  # Mock: user has 2 documents
    
    def _get_document_knowledge(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Get document knowledge for user (simplified implementation)"""
        # In real implementation, query database and extract knowledge
        # For now, return mock data
        return {
            "company_info": {
                "company_name": "Example Corp",
                "industry": "Technology"
            },
            "products": ["Product A", "Product B"],
            "value_propositions": ["Efficiency", "Innovation"]
        }
    
    def _get_market_context(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get market context for prompt"""
        try:
            # Extract industry from prompt or context
            industry = context.get("industry", "Technology")
            
            # Get market sentiment
            keywords = context.get("keywords", ["technology", "innovation"])
            market_sentiment = self.grok_service.get_market_sentiment(industry, keywords)
            
            return {
                "market_sentiment": market_sentiment,
                "industry": industry,
                "keywords": keywords
            }
        except Exception as e:
            logger.warning(f"Failed to get market context: {e}")
            return {"market_sentiment": {"sentiment": "neutral", "confidence": 0.5}}
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptation strategies"""
        return {
            "available_strategies": [strategy.value for strategy in AdaptationStrategy],
            "knowledge_levels": [level.value for level in KnowledgeLevel],
            "strategy_configs": {
                strategy.value: config for strategy, config in self.strategy_configs.items()
            },
            "service_version": "1.0",
            "last_updated": datetime.now().isoformat()
        }
