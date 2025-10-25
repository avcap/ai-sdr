import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"

class ModelType(Enum):
    """Available model types"""
    CLAUDE_HAIKU = "claude-haiku"
    CLAUDE_SONNET = "claude-sonnet"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GROK = "grok"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    model_type: ModelType
    max_tokens: int
    cost_per_1k_tokens: float
    speed_rating: float  # 1-10 scale
    quality_rating: float  # 1-10 scale
    best_for: List[str]
    limitations: List[str]

class LLMSelectorService:
    """
    Intelligent model selection service that chooses the optimal LLM based on task complexity,
    input size, cost considerations, and performance requirements.
    """
    
    def __init__(self):
        self.model_configs = self._initialize_model_configs()
        self.usage_stats = {}  # Track usage for optimization
        
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations with performance and cost data"""
        return {
            "claude-haiku": ModelConfig(
                name="Claude 3 Haiku",
                model_type=ModelType.CLAUDE_HAIKU,
                max_tokens=200000,
                cost_per_1k_tokens=0.00025,  # $0.25 per 1M tokens
                speed_rating=9.0,
                quality_rating=7.0,
                best_for=[
                    "fast extraction",
                    "summaries",
                    "simple analysis",
                    "quick tasks",
                    "large document processing"
                ],
                limitations=[
                    "complex reasoning",
                    "creative writing",
                    "advanced personalization"
                ]
            ),
            "claude-sonnet": ModelConfig(
                name="Claude 3 Sonnet",
                model_type=ModelType.CLAUDE_SONNET,
                max_tokens=200000,
                cost_per_1k_tokens=0.003,  # $3 per 1M tokens
                speed_rating=7.0,
                quality_rating=9.0,
                best_for=[
                    "complex reasoning",
                    "large documents",
                    "detailed analysis",
                    "knowledge extraction",
                    "structured output"
                ],
                limitations=[
                    "real-time data",
                    "market analysis",
                    "very fast tasks"
                ]
            ),
            "gpt-3.5-turbo": ModelConfig(
                name="GPT-3.5 Turbo",
                model_type=ModelType.GPT_35_TURBO,
                max_tokens=16384,
                cost_per_1k_tokens=0.0005,  # $0.50 per 1M tokens
                speed_rating=8.0,
                quality_rating=6.5,
                best_for=[
                    "quick generation",
                    "simple tasks",
                    "cost-effective processing",
                    "basic personalization"
                ],
                limitations=[
                    "complex reasoning",
                    "large context",
                    "advanced analysis"
                ]
            ),
            "gpt-4": ModelConfig(
                name="GPT-4",
                model_type=ModelType.GPT_4,
                max_tokens=128000,
                cost_per_1k_tokens=0.03,  # $30 per 1M tokens
                speed_rating=5.0,
                quality_rating=10.0,
                best_for=[
                    "advanced personalization",
                    "creative content",
                    "complex reasoning",
                    "high-quality output",
                    "sophisticated analysis"
                ],
                limitations=[
                    "cost",
                    "speed",
                    "real-time data"
                ]
            ),
            "grok": ModelConfig(
                name="Grok",
                model_type=ModelType.GROK,
                max_tokens=32768,
                cost_per_1k_tokens=0.001,  # $1 per 1M tokens (estimated)
                speed_rating=8.5,
                quality_rating=8.0,
                best_for=[
                    "real-time data",
                    "market analysis",
                    "trend analysis",
                    "current events",
                    "competitive intelligence"
                ],
                limitations=[
                    "structured output",
                    "complex reasoning",
                    "document analysis"
                ]
            )
        }
    
    def assess_task_complexity(self, task_type: str, input_data: Dict[str, Any]) -> TaskComplexity:
        """
        Assess the complexity of a task based on type and input characteristics.
        
        Args:
            task_type: Type of task (extraction, personalization, analysis, etc.)
            input_data: Input data characteristics
            
        Returns:
            TaskComplexity level
        """
        logger.info(f"Assessing task complexity for: {task_type}")
        
        complexity_score = 0
        
        # Base complexity by task type
        task_complexity_map = {
            "knowledge_extraction": 3,
            "document_analysis": 4,
            "personalization": 5,
            "campaign_creation": 6,
            "market_analysis": 4,
            "lead_generation": 3,
            "content_generation": 4,
            "competitive_analysis": 5,
            "trend_analysis": 3,
            "simple_query": 1,
            "summarization": 2
        }
        
        complexity_score += task_complexity_map.get(task_type, 3)
        
        # Adjust based on input characteristics
        input_size = input_data.get("input_size", 0)
        if input_size > 100000:  # Large documents
            complexity_score += 2
        elif input_size > 50000:
            complexity_score += 1
        
        # Multiple documents increase complexity
        num_documents = input_data.get("num_documents", 1)
        if num_documents > 5:
            complexity_score += 2
        elif num_documents > 2:
            complexity_score += 1
        
        # Real-time requirements
        if input_data.get("real_time_required", False):
            complexity_score -= 1  # Prefer faster models
        
        # Quality requirements
        if input_data.get("high_quality_required", False):
            complexity_score += 1
        
        # Determine complexity level
        if complexity_score <= 2:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 4:
            return TaskComplexity.MODERATE
        elif complexity_score <= 6:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ADVANCED
    
    def select_optimal_model(self, complexity_score: TaskComplexity, requirements: Dict[str, Any] = None) -> Tuple[str, ModelConfig]:
        """
        Select the optimal model based on complexity and requirements.
        
        Args:
            complexity_score: Assessed task complexity
            requirements: Additional requirements (speed, cost, quality)
            
        Returns:
            Tuple of (model_name, model_config)
        """
        logger.info(f"Selecting optimal model for complexity: {complexity_score.value}")
        
        requirements = requirements or {}
        
        # Filter models based on requirements
        available_models = self._filter_models_by_requirements(requirements)
        
        # Score each available model
        model_scores = {}
        for model_name, config in available_models.items():
            score = self._calculate_model_score(config, complexity_score, requirements)
            model_scores[model_name] = score
        
        # Select best model
        if not model_scores:
            logger.warning("No models available, returning default model")
            return "gpt-3.5-turbo", self.model_configs.get("gpt-3.5-turbo", self.model_configs["claude-haiku"])
        
        best_model = max(model_scores.items(), key=lambda x: x[1])
        selected_model = best_model[0]
        selected_config = available_models[selected_model]
        
        logger.info(f"Selected model: {selected_model} (score: {best_model[1]:.2f})")
        
        # Track usage for optimization
        self._track_model_usage(selected_model, complexity_score)
        
        return selected_model, selected_config
    
    def _filter_models_by_requirements(self, requirements: Dict[str, Any]) -> Dict[str, ModelConfig]:
        """Filter available models based on requirements"""
        filtered_models = {}
        
        for model_name, config in self.model_configs.items():
            # Check API key availability
            if not self._is_model_available(model_name):
                continue
            
            # Check speed requirements
            if requirements.get("speed_priority", False):
                if config.speed_rating < 7.0:
                    continue
            
            # Check quality requirements
            if requirements.get("quality_priority", False):
                if config.quality_rating < 8.0:
                    continue
            
            # Check cost constraints
            max_cost = requirements.get("max_cost_per_1k", float('inf'))
            if config.cost_per_1k_tokens > max_cost:
                continue
            
            # Check token limits
            max_tokens_needed = requirements.get("max_tokens_needed", 0)
            if config.max_tokens < max_tokens_needed:
                continue
            
            filtered_models[model_name] = config
        
        return filtered_models
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if model API key is available"""
        api_keys = {
            "claude-haiku": os.getenv("ANTHROPIC_API_KEY"),
            "claude-sonnet": os.getenv("ANTHROPIC_API_KEY"),
            "gpt-3.5-turbo": os.getenv("OPENAI_API_KEY"),
            "gpt-4": os.getenv("OPENAI_API_KEY"),
            "grok": os.getenv("GROK_API_KEY")
        }
        
        return bool(api_keys.get(model_name))
    
    def _calculate_model_score(self, config: ModelConfig, complexity: TaskComplexity, requirements: Dict[str, Any]) -> float:
        """Calculate suitability score for a model"""
        score = 0.0
        
        # Base score from complexity matching
        complexity_scores = {
            TaskComplexity.SIMPLE: {
                "claude-haiku": 9.0,
                "gpt-3.5-turbo": 8.0,
                "grok": 7.0,
                "claude-sonnet": 6.0,
                "gpt-4": 4.0
            },
            TaskComplexity.MODERATE: {
                "claude-sonnet": 9.0,
                "claude-haiku": 7.0,
                "gpt-3.5-turbo": 6.0,
                "grok": 7.0,
                "gpt-4": 5.0
            },
            TaskComplexity.COMPLEX: {
                "claude-sonnet": 9.0,
                "gpt-4": 8.0,
                "grok": 6.0,
                "claude-haiku": 4.0,
                "gpt-3.5-turbo": 3.0
            },
            TaskComplexity.ADVANCED: {
                "gpt-4": 10.0,
                "claude-sonnet": 8.0,
                "grok": 5.0,
                "claude-haiku": 2.0,
                "gpt-3.5-turbo": 2.0
            }
        }
        
        score += complexity_scores[complexity].get(config.model_type.value, 5.0)
        
        # Adjust for requirements
        if requirements.get("speed_priority", False):
            score += config.speed_rating * 0.5
        
        if requirements.get("quality_priority", False):
            score += config.quality_rating * 0.5
        
        if requirements.get("cost_priority", False):
            # Lower cost = higher score
            cost_score = max(0, 10 - (config.cost_per_1k_tokens * 1000))
            score += cost_score * 0.3
        
        # Adjust for real-time requirements
        if requirements.get("real_time_required", False):
            if config.model_type == ModelType.GROK:
                score += 2.0
            elif config.speed_rating >= 8.0:
                score += 1.0
        
        # Adjust for market analysis requirements
        if requirements.get("market_analysis", False):
            if config.model_type == ModelType.GROK:
                score += 3.0
        
        return score
    
    def _track_model_usage(self, model_name: str, complexity: TaskComplexity):
        """Track model usage for optimization"""
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = {
                "total_usage": 0,
                "complexity_usage": {},
                "last_used": None
            }
        
        self.usage_stats[model_name]["total_usage"] += 1
        self.usage_stats[model_name]["complexity_usage"][complexity.value] = \
            self.usage_stats[model_name]["complexity_usage"].get(complexity.value, 0) + 1
        self.usage_stats[model_name]["last_used"] = time.time()
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.model_configs.get(model_name)
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for all models"""
        return {
            "model_stats": self.usage_stats,
            "total_models": len(self.model_configs),
            "available_models": [name for name, config in self.model_configs.items() 
                               if self._is_model_available(name)]
        }
    
    def get_model_details(self, model_name: str) -> Optional[ModelConfig]:
        """Returns details for a specific model."""
        return self.model_configs.get(model_name)

    def recommend_model_for_task(self, task_description: str, input_size: int = 0, 
                                requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Provide model recommendation with reasoning for a specific task.
        
        Args:
            task_description: Description of the task
            input_size: Size of input data
            requirements: Additional requirements
            
        Returns:
            Dict with recommendation and reasoning
        """
        logger.info(f"Providing model recommendation for: {task_description}")
        
        requirements = requirements or {}
        requirements["input_size"] = input_size
        
        # Assess complexity
        complexity = self.assess_task_complexity("custom_task", requirements)
        
        # Select optimal model
        selected_model, config = self.select_optimal_model(complexity, requirements)
        
        # Generate reasoning
        reasoning = self._generate_recommendation_reasoning(selected_model, config, complexity, requirements)
        
        # Get alternatives
        alternatives = self._get_alternative_models(complexity, requirements, selected_model)
        
        return {
            "recommended_model": selected_model,
            "model_config": {
                "name": config.name,
                "max_tokens": config.max_tokens,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "speed_rating": config.speed_rating,
                "quality_rating": config.quality_rating
            },
            "complexity_level": complexity.value,
            "reasoning": reasoning,
            "alternatives": alternatives,
            "estimated_cost": self._estimate_cost(config, input_size),
            "estimated_time": self._estimate_time(config, input_size)
        }
    
    def _generate_recommendation_reasoning(self, model_name: str, config: ModelConfig, 
                                         complexity: TaskComplexity, requirements: Dict[str, Any]) -> List[str]:
        """Generate reasoning for model recommendation"""
        reasoning = []
        
        # Complexity-based reasoning
        if complexity == TaskComplexity.SIMPLE:
            reasoning.append(f"{config.name} is optimal for simple tasks due to its speed and cost-effectiveness")
        elif complexity == TaskComplexity.MODERATE:
            reasoning.append(f"{config.name} provides good balance of speed, quality, and cost for moderate complexity")
        elif complexity == TaskComplexity.COMPLEX:
            reasoning.append(f"{config.name} excels at complex reasoning and detailed analysis")
        else:
            reasoning.append(f"{config.name} is the best choice for advanced tasks requiring high-quality output")
        
        # Requirement-based reasoning
        if requirements.get("speed_priority", False):
            reasoning.append(f"Speed priority: {config.name} has speed rating of {config.speed_rating}/10")
        
        if requirements.get("quality_priority", False):
            reasoning.append(f"Quality priority: {config.name} has quality rating of {config.quality_rating}/10")
        
        if requirements.get("cost_priority", False):
            reasoning.append(f"Cost-effective: ${config.cost_per_1k_tokens:.4f} per 1K tokens")
        
        if requirements.get("real_time_required", False):
            reasoning.append("Real-time data access capabilities")
        
        if requirements.get("market_analysis", False):
            reasoning.append("Specialized for market analysis and current events")
        
        return reasoning
    
    def _get_alternative_models(self, complexity: TaskComplexity, requirements: Dict[str, Any], 
                               selected_model: str) -> List[Dict[str, Any]]:
        """Get alternative model recommendations"""
        alternatives = []
        
        # Get all available models except the selected one
        available_models = self._filter_models_by_requirements(requirements)
        available_models.pop(selected_model, None)
        
        # Score alternatives
        for model_name, config in available_models.items():
            score = self._calculate_model_score(config, complexity, requirements)
            alternatives.append({
                "model": model_name,
                "name": config.name,
                "score": score,
                "reason": f"Alternative with {config.speed_rating}/10 speed, {config.quality_rating}/10 quality"
            })
        
        # Sort by score and return top 2
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        return alternatives[:2]
    
    def _estimate_cost(self, config: ModelConfig, input_size: int) -> float:
        """Estimate cost for processing input"""
        # Rough estimation: assume 1 token per 4 characters
        estimated_tokens = input_size / 4
        return (estimated_tokens / 1000) * config.cost_per_1k_tokens
    
    def _estimate_time(self, config: ModelConfig, input_size: int) -> float:
        """Estimate processing time in seconds"""
        # Rough estimation based on speed rating
        base_time = input_size / 10000  # Base time for 10k characters
        speed_factor = 10 - config.speed_rating  # Slower models take longer
        return base_time * (1 + speed_factor * 0.1)
    
    def optimize_model_selection(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize model selection based on historical performance data.
        
        Args:
            performance_data: List of performance records with model, task, and results
            
        Returns:
            Optimization recommendations
        """
        logger.info("Optimizing model selection based on performance data")
        
        # Analyze performance by model and task type
        model_performance = {}
        
        for record in performance_data:
            model = record.get("model")
            task_type = record.get("task_type")
            success = record.get("success", False)
            quality_score = record.get("quality_score", 0)
            processing_time = record.get("processing_time", 0)
            
            if model not in model_performance:
                model_performance[model] = {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "avg_quality": 0,
                    "avg_time": 0,
                    "task_types": {}
                }
            
            model_performance[model]["total_tasks"] += 1
            if success:
                model_performance[model]["successful_tasks"] += 1
            
            # Update averages
            current_avg_quality = model_performance[model]["avg_quality"]
            current_avg_time = model_performance[model]["avg_time"]
            total_tasks = model_performance[model]["total_tasks"]
            
            model_performance[model]["avg_quality"] = (
                (current_avg_quality * (total_tasks - 1) + quality_score) / total_tasks
            )
            model_performance[model]["avg_time"] = (
                (current_avg_time * (total_tasks - 1) + processing_time) / total_tasks
            )
            
            # Track by task type
            if task_type not in model_performance[model]["task_types"]:
                model_performance[model]["task_types"][task_type] = {
                    "count": 0,
                    "success_rate": 0,
                    "avg_quality": 0
                }
            
            task_stats = model_performance[model]["task_types"][task_type]
            task_stats["count"] += 1
            if success:
                task_stats["success_rate"] = (
                    (task_stats["success_rate"] * (task_stats["count"] - 1) + 1) / task_stats["count"]
                )
            else:
                task_stats["success_rate"] = (
                    (task_stats["success_rate"] * (task_stats["count"] - 1)) / task_stats["count"]
                )
            
            task_stats["avg_quality"] = (
                (task_stats["avg_quality"] * (task_stats["count"] - 1) + quality_score) / task_stats["count"]
            )
        
        # Generate recommendations
        recommendations = []
        for model, stats in model_performance.items():
            success_rate = stats["successful_tasks"] / stats["total_tasks"]
            recommendations.append({
                "model": model,
                "success_rate": success_rate,
                "avg_quality": stats["avg_quality"],
                "avg_time": stats["avg_time"],
                "recommendation": "excellent" if success_rate > 0.9 else "good" if success_rate > 0.7 else "needs_improvement"
            })
        
        return {
            "model_performance": model_performance,
            "recommendations": sorted(recommendations, key=lambda x: x["success_rate"], reverse=True),
            "optimization_timestamp": time.time()
        }
