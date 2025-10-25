import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
from collections import defaultdict
import numpy as np

from services.market_monitoring_service import MarketMonitoringService
from services.knowledge_quality_service import KnowledgeQualityService

logger = logging.getLogger(__name__)

@dataclass
class CampaignPrediction:
    """Campaign performance prediction"""
    campaign_id: str
    predicted_open_rate: float
    predicted_click_rate: float
    predicted_response_rate: float
    predicted_conversion_rate: float
    confidence_score: float
    risk_factors: List[str]
    success_probability: float
    recommended_optimizations: List[str]

@dataclass
class TargetingOptimization:
    """Targeting optimization recommendations"""
    target_audience: str
    optimization_type: str
    current_performance: float
    predicted_improvement: float
    confidence: float
    recommendations: List[str]
    expected_roi: float

@dataclass
class TimingRecommendation:
    """Timing optimization recommendations"""
    optimal_time: str
    optimal_day: str
    optimal_frequency: str
    reasoning: str
    expected_improvement: float
    confidence: float
    market_factors: List[str]

@dataclass
class MessageImprovement:
    """Message improvement suggestions"""
    message_type: str
    current_score: float
    suggested_improvements: List[str]
    expected_impact: float
    confidence: float
    a_b_test_recommendations: List[str]

class PredictiveAnalyticsService:
    """
    ML-powered campaign optimization service that predicts performance,
    optimizes targeting, recommends timing, and suggests message improvements.
    """
    
    def __init__(self):
        self.market_monitoring = MarketMonitoringService()
        self.quality_service = KnowledgeQualityService()
        
        # Analytics configuration
        self.analytics_config = {
            "prediction_horizon_days": 30,
            "min_data_points": 10,
            "confidence_threshold": 0.6,
            "optimization_threshold": 0.1,  # 10% improvement threshold
            "max_recommendations": 5
        }
        
        # Historical performance data
        self.campaign_history = defaultdict(list)
        self.audience_performance = defaultdict(list)
        self.timing_performance = defaultdict(list)
        self.message_performance = defaultdict(list)
        
        # Performance baselines
        self.performance_baselines = {
            "email_open_rate": 0.25,  # 25%
            "email_click_rate": 0.05,  # 5%
            "response_rate": 0.02,  # 2%
            "conversion_rate": 0.01,  # 1%
            "engagement_rate": 0.15  # 15%
        }
        
        # Market impact factors
        self.market_impact_factors = {
            "high_sentiment": 1.2,
            "positive_trends": 1.15,
            "competitive_advantage": 1.1,
            "market_gaps": 1.25,
            "seasonal_factors": 1.05
        }
    
    def predict_campaign_performance(self, campaign_data: Dict[str, Any], lead_data: List[Dict[str, Any]] = None) -> CampaignPrediction:
        """
        Predict campaign performance based on historical data and market conditions.
        
        Args:
            campaign_data: Campaign configuration and targeting information
            
        Returns:
            Campaign performance prediction with confidence scores
        """
        logger.info(f"Predicting performance for campaign: {campaign_data.get('campaign_id', 'unknown')}")
        
        campaign_id = campaign_data.get("campaign_id", f"campaign_{int(datetime.now().timestamp())}")
        
        # Analyze campaign components
        audience_analysis = self._analyze_target_audience(campaign_data)
        content_analysis = self._analyze_campaign_content(campaign_data)
        timing_analysis = self._analyze_campaign_timing(campaign_data)
        market_analysis = self._analyze_market_conditions(campaign_data)
        
        # Calculate base predictions
        base_predictions = self._calculate_base_predictions(audience_analysis, content_analysis)
        
        # Apply market adjustments
        market_adjusted_predictions = self._apply_market_adjustments(
            base_predictions, market_analysis
        )
        
        # Calculate confidence and risk factors
        confidence_score = self._calculate_prediction_confidence(
            audience_analysis, content_analysis, timing_analysis, market_analysis
        )
        
        risk_factors = self._identify_risk_factors(campaign_data, market_analysis)
        
        # Generate optimization recommendations
        optimizations = self._generate_optimization_recommendations(
            campaign_data, market_adjusted_predictions, risk_factors
        )
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            market_adjusted_predictions, confidence_score, risk_factors
        )
        
        return CampaignPrediction(
            campaign_id=campaign_id,
            predicted_open_rate=market_adjusted_predictions["email_open_rate"],
            predicted_click_rate=market_adjusted_predictions["email_click_rate"],
            predicted_response_rate=market_adjusted_predictions["response_rate"],
            predicted_conversion_rate=market_adjusted_predictions["conversion_rate"],
            confidence_score=confidence_score,
            risk_factors=risk_factors,
            success_probability=success_probability,
            recommended_optimizations=optimizations
        )
    
    def optimize_targeting(self, historical_data: Dict[str, Any], 
                          current_targets: List[str]) -> List[TargetingOptimization]:
        """
        Optimize targeting based on historical performance data.
        
        Args:
            historical_data: Historical campaign and audience performance
            current_targets: Current target audience segments
            
        Returns:
            List of targeting optimization recommendations
        """
        logger.info("Optimizing targeting based on historical data")
        
        optimizations = []
        
        # Analyze audience performance
        audience_performance = self._analyze_audience_performance(historical_data)
        
        # Generate targeting recommendations
        for target in current_targets:
            optimization = self._generate_targeting_optimization(
                target, audience_performance, historical_data
            )
            if optimization:
                optimizations.append(optimization)
        
        # Add new audience recommendations
        new_audience_recommendations = self._recommend_new_audiences(
            audience_performance, historical_data
        )
        optimizations.extend(new_audience_recommendations)
        
        # Sort by expected improvement
        optimizations.sort(key=lambda x: x.predicted_improvement, reverse=True)
        
        return optimizations[:self.analytics_config["max_recommendations"]]
    
    def recommend_best_timing(self, market_data: Dict[str, Any], 
                            historical_timing: Dict[str, Any] = None) -> TimingRecommendation:
        """
        Recommend optimal timing for campaigns based on market conditions.
        
        Args:
            market_data: Current market conditions and trends
            historical_timing: Historical timing performance data
            
        Returns:
            Timing optimization recommendations
        """
        logger.info("Generating timing recommendations based on market data")
        
        # Analyze market timing factors
        market_timing_factors = self._analyze_market_timing_factors(market_data)
        
        # Analyze historical timing patterns
        historical_patterns = self._analyze_historical_timing_patterns(historical_timing)
        
        # Determine optimal timing
        optimal_timing = self._determine_optimal_timing(
            market_timing_factors, historical_patterns
        )
        
        # Calculate expected improvement
        expected_improvement = self._calculate_timing_improvement(
            optimal_timing, historical_patterns
        )
        
        # Generate reasoning
        reasoning = self._generate_timing_reasoning(
            optimal_timing, market_timing_factors, historical_patterns
        )
        
        return TimingRecommendation(
            optimal_time=optimal_timing["time"],
            optimal_day=optimal_timing["day"],
            optimal_frequency=optimal_timing["frequency"],
            reasoning=reasoning,
            expected_improvement=expected_improvement,
            confidence=optimal_timing["confidence"],
            market_factors=market_timing_factors["key_factors"]
        )
    
    def suggest_message_improvements(self, engagement_data: Dict[str, Any], 
                                   current_messages: List[Dict[str, Any]]) -> List[MessageImprovement]:
        """
        Suggest message improvements based on engagement data.
        
        Args:
            engagement_data: Historical engagement metrics
            current_messages: Current message content and performance
            
        Returns:
            List of message improvement suggestions
        """
        logger.info("Analyzing message performance and generating improvements")
        
        improvements = []
        
        # Analyze message performance patterns
        performance_patterns = self._analyze_message_performance_patterns(engagement_data)
        
        # Generate improvements for each message type
        for message in current_messages:
            improvement = self._generate_message_improvement(
                message, performance_patterns, engagement_data
            )
            if improvement:
                improvements.append(improvement)
        
        # Generate A/B test recommendations
        ab_test_recommendations = self._generate_ab_test_recommendations(
            current_messages, performance_patterns
        )
        
        # Add A/B test recommendations to improvements
        for improvement in improvements:
            improvement.a_b_test_recommendations.extend(ab_test_recommendations)
        
        return improvements
    
    def _analyze_target_audience(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze target audience characteristics"""
        audience_data = campaign_data.get("target_audience", {})
        
        analysis = {
            "audience_size": audience_data.get("size", "unknown"),
            "audience_quality": "high" if audience_data.get("quality_score", 0) > 0.7 else "medium",
            "audience_specificity": len(audience_data.get("roles", [])),
            "industry_alignment": audience_data.get("industry_match", 0.5),
            "pain_point_alignment": audience_data.get("pain_point_match", 0.5)
        }
        
        return analysis
    
    def _analyze_campaign_content(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze campaign content quality and relevance"""
        content_data = campaign_data.get("content", {})
        
        analysis = {
            "content_quality": content_data.get("quality_score", 0.5),
            "personalization_level": content_data.get("personalization_score", 0.5),
            "value_proposition_clarity": content_data.get("value_prop_score", 0.5),
            "call_to_action_strength": content_data.get("cta_score", 0.5),
            "message_length": content_data.get("length", "medium")
        }
        
        return analysis
    
    def _analyze_campaign_timing(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze campaign timing factors"""
        timing_data = campaign_data.get("timing", {})
        
        analysis = {
            "day_of_week": timing_data.get("day", "Tuesday"),
            "time_of_day": timing_data.get("time", "10:00"),
            "frequency": timing_data.get("frequency", "weekly"),
            "seasonality": timing_data.get("seasonal_factor", 1.0),
            "market_timing": timing_data.get("market_alignment", 0.5)
        }
        
        return analysis
    
    def _analyze_market_conditions(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market conditions"""
        industry = campaign_data.get("industry", "Technology")
        
        try:
            # Get market sentiment
            market_sentiment = self.market_monitoring.grok_service.get_market_sentiment(
                industry, ["growth", "innovation", "competition"]
            )
            
            # Get industry trends
            industry_trends = self.market_monitoring.grok_service.get_industry_trends(industry)
            
            analysis = {
                "market_sentiment": market_sentiment.get("sentiment", "neutral"),
                "sentiment_confidence": market_sentiment.get("confidence", 0.5),
                "trend_count": len(industry_trends.get("trends", [])),
                "positive_trends": len([t for t in industry_trends.get("trends", []) 
                                      if t.get("impact") == "high"]),
                "market_outlook": industry_trends.get("market_outlook", "stable")
            }
            
        except Exception as e:
            logger.warning(f"Could not analyze market conditions: {e}")
            analysis = {
                "market_sentiment": "neutral",
                "sentiment_confidence": 0.5,
                "trend_count": 0,
                "positive_trends": 0,
                "market_outlook": "stable"
            }
        
        return analysis
    
    def _calculate_base_predictions(self, audience_analysis: Dict[str, Any], 
                                  content_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate base performance predictions"""
        # Start with baselines
        predictions = self.performance_baselines.copy()
        
        # Adjust based on audience quality
        audience_quality_multiplier = 1.0
        if audience_analysis["audience_quality"] == "high":
            audience_quality_multiplier = 1.2
        elif audience_analysis["audience_quality"] == "medium":
            audience_quality_multiplier = 1.0
        else:
            audience_quality_multiplier = 0.8
        
        # Adjust based on content quality
        content_quality_multiplier = (
            content_analysis["content_quality"] * 0.3 +
            content_analysis["personalization_level"] * 0.3 +
            content_analysis["value_proposition_clarity"] * 0.2 +
            content_analysis["call_to_action_strength"] * 0.2
        )
        
        # Apply adjustments
        predictions["email_open_rate"] *= audience_quality_multiplier * content_quality_multiplier
        predictions["email_click_rate"] *= audience_quality_multiplier * content_quality_multiplier
        predictions["response_rate"] *= audience_quality_multiplier * content_quality_multiplier
        predictions["conversion_rate"] *= audience_quality_multiplier * content_quality_multiplier
        
        return predictions
    
    def _apply_market_adjustments(self, base_predictions: Dict[str, float], 
                                market_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Apply market condition adjustments to predictions"""
        adjusted_predictions = base_predictions.copy()
        
        # Market sentiment adjustment
        sentiment_multiplier = 1.0
        if market_analysis["market_sentiment"] == "positive":
            sentiment_multiplier = self.market_impact_factors["high_sentiment"]
        elif market_analysis["market_sentiment"] == "negative":
            sentiment_multiplier = 0.8
        
        # Trend adjustment
        trend_multiplier = 1.0
        if market_analysis["positive_trends"] > 0:
            trend_multiplier = self.market_impact_factors["positive_trends"]
        
        # Market outlook adjustment
        outlook_multiplier = 1.0
        if market_analysis["market_outlook"] == "growing":
            outlook_multiplier = 1.1
        elif market_analysis["market_outlook"] == "declining":
            outlook_multiplier = 0.9
        
        # Apply all adjustments
        total_multiplier = sentiment_multiplier * trend_multiplier * outlook_multiplier
        
        for metric in adjusted_predictions:
            adjusted_predictions[metric] *= total_multiplier
        
        return adjusted_predictions
    
    def _calculate_prediction_confidence(self, audience_analysis: Dict[str, Any],
                                      content_analysis: Dict[str, Any],
                                      timing_analysis: Dict[str, Any],
                                      market_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for predictions"""
        confidence_factors = []
        
        # Audience confidence
        audience_confidence = min(audience_analysis["audience_specificity"] / 5, 1.0)
        confidence_factors.append(audience_confidence)
        
        # Content confidence
        content_confidence = (
            content_analysis["content_quality"] +
            content_analysis["personalization_level"] +
            content_analysis["value_proposition_clarity"]
        ) / 3
        confidence_factors.append(content_confidence)
        
        # Market confidence
        market_confidence = market_analysis["sentiment_confidence"]
        confidence_factors.append(market_confidence)
        
        # Timing confidence
        timing_confidence = timing_analysis["market_timing"]
        confidence_factors.append(timing_confidence)
        
        return statistics.mean(confidence_factors)
    
    def _identify_risk_factors(self, campaign_data: Dict[str, Any], 
                             market_analysis: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors for the campaign"""
        risk_factors = []
        
        # Market risks
        if market_analysis["market_sentiment"] == "negative":
            risk_factors.append("Negative market sentiment")
        
        if market_analysis["positive_trends"] == 0:
            risk_factors.append("No positive industry trends")
        
        if market_analysis["market_outlook"] == "declining":
            risk_factors.append("Declining market outlook")
        
        # Campaign risks
        audience_data = campaign_data.get("target_audience", {})
        if audience_data.get("quality_score", 0) < 0.5:
            risk_factors.append("Low audience quality")
        
        content_data = campaign_data.get("content", {})
        if content_data.get("quality_score", 0) < 0.5:
            risk_factors.append("Low content quality")
        
        return risk_factors
    
    def _generate_optimization_recommendations(self, campaign_data: Dict[str, Any],
                                             predictions: Dict[str, float],
                                             risk_factors: List[str]) -> List[str]:
        """Generate optimization recommendations based on predictions and risks"""
        recommendations = []
        
        # Address risk factors
        for risk in risk_factors:
            if "market sentiment" in risk.lower():
                recommendations.append("Consider delaying campaign until market sentiment improves")
            elif "audience quality" in risk.lower():
                recommendations.append("Refine target audience criteria for better quality")
            elif "content quality" in risk.lower():
                recommendations.append("Improve content quality and personalization")
        
        # Performance-based recommendations
        if predictions["email_open_rate"] < self.performance_baselines["email_open_rate"]:
            recommendations.append("Improve subject line and sender reputation")
        
        if predictions["email_click_rate"] < self.performance_baselines["email_click_rate"]:
            recommendations.append("Enhance call-to-action and content relevance")
        
        if predictions["response_rate"] < self.performance_baselines["response_rate"]:
            recommendations.append("Increase personalization and value proposition clarity")
        
        return recommendations[:self.analytics_config["max_recommendations"]]
    
    def _calculate_success_probability(self, predictions: Dict[str, float],
                                     confidence_score: float,
                                     risk_factors: List[str]) -> float:
        """Calculate overall success probability"""
        # Base probability from predictions
        avg_performance = statistics.mean([
            predictions["email_open_rate"],
            predictions["email_click_rate"],
            predictions["response_rate"],
            predictions["conversion_rate"]
        ])
        
        # Adjust for confidence
        confidence_adjusted = avg_performance * confidence_score
        
        # Adjust for risk factors
        risk_penalty = len(risk_factors) * 0.05  # 5% penalty per risk factor
        
        success_probability = max(confidence_adjusted - risk_penalty, 0.0)
        
        return min(success_probability, 1.0)
    
    def _analyze_audience_performance(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical audience performance"""
        audience_performance = {}
        
        # Extract audience performance data
        for audience, metrics in historical_data.get("audience_metrics", {}).items():
            audience_performance[audience] = {
                "avg_open_rate": metrics.get("email_open_rate", 0.25),
                "avg_click_rate": metrics.get("email_click_rate", 0.05),
                "avg_response_rate": metrics.get("response_rate", 0.02),
                "avg_conversion_rate": metrics.get("conversion_rate", 0.01),
                "performance_score": self._calculate_audience_score(metrics)
            }
        
        return audience_performance
    
    def _calculate_audience_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall audience performance score"""
        weights = {
            "email_open_rate": 0.2,
            "email_click_rate": 0.3,
            "response_rate": 0.3,
            "conversion_rate": 0.2
        }
        
        score = 0.0
        for metric, weight in weights.items():
            score += metrics.get(metric, 0) * weight
        
        return score
    
    def _generate_targeting_optimization(self, target: str, audience_performance: Dict[str, Any],
                                       historical_data: Dict[str, Any]) -> Optional[TargetingOptimization]:
        """Generate targeting optimization for a specific audience"""
        if target not in audience_performance:
            return None
        
        performance = audience_performance[target]
        current_score = performance["performance_score"]
        
        # Calculate potential improvements
        improvements = []
        expected_improvement = 0.0
        
        if performance["avg_open_rate"] < self.performance_baselines["email_open_rate"]:
            improvements.append("Improve subject line targeting")
            expected_improvement += 0.05
        
        if performance["avg_click_rate"] < self.performance_baselines["email_click_rate"]:
            improvements.append("Enhance content relevance")
            expected_improvement += 0.03
        
        if performance["avg_response_rate"] < self.performance_baselines["response_rate"]:
            improvements.append("Increase personalization")
            expected_improvement += 0.02
        
        if expected_improvement < self.analytics_config["optimization_threshold"]:
            return None
        
        return TargetingOptimization(
            target_audience=target,
            optimization_type="performance_improvement",
            current_performance=current_score,
            predicted_improvement=expected_improvement,
            confidence=0.7,  # Default confidence
            recommendations=improvements,
            expected_roi=expected_improvement * 10  # Estimated ROI multiplier
        )
    
    def _recommend_new_audiences(self, audience_performance: Dict[str, Any],
                               historical_data: Dict[str, Any]) -> List[TargetingOptimization]:
        """Recommend new audience segments based on performance patterns"""
        recommendations = []
        
        # Analyze high-performing audiences
        high_performers = [
            audience for audience, perf in audience_performance.items()
            if perf["performance_score"] > 0.7
        ]
        
        # Generate recommendations for similar audiences
        for performer in high_performers:
            recommendation = TargetingOptimization(
                target_audience=f"Similar to {performer}",
                optimization_type="audience_expansion",
                current_performance=0.0,
                predicted_improvement=0.15,
                confidence=0.6,
                recommendations=[
                    f"Expand targeting to audiences similar to {performer}",
                    "Test with adjacent market segments",
                    "Leverage successful messaging patterns"
                ],
                expected_roi=1.5
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_market_timing_factors(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market timing factors"""
        factors = {
            "key_factors": [],
            "optimal_conditions": [],
            "avoid_conditions": []
        }
        
        # Analyze market sentiment timing
        sentiment = market_data.get("sentiment", "neutral")
        if sentiment == "positive":
            factors["key_factors"].append("Positive market sentiment")
            factors["optimal_conditions"].append("High market confidence")
        elif sentiment == "negative":
            factors["key_factors"].append("Negative market sentiment")
            factors["avoid_conditions"].append("Low market confidence")
        
        # Analyze trend timing
        trends = market_data.get("trends", [])
        if trends:
            factors["key_factors"].append(f"{len(trends)} active trends")
            factors["optimal_conditions"].append("Trending topics alignment")
        
        return factors
    
    def _analyze_historical_timing_patterns(self, historical_timing: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical timing performance patterns"""
        if not historical_timing:
            return {"patterns": {}, "best_performing": {}}
        
        patterns = {
            "day_performance": historical_timing.get("day_performance", {}),
            "time_performance": historical_timing.get("time_performance", {}),
            "frequency_performance": historical_timing.get("frequency_performance", {})
        }
        
        # Find best performing patterns
        best_performing = {
            "day": max(patterns["day_performance"].items(), key=lambda x: x[1], default=("Tuesday", 0.25))[0],
            "time": max(patterns["time_performance"].items(), key=lambda x: x[1], default=("10:00", 0.25))[0],
            "frequency": max(patterns["frequency_performance"].items(), key=lambda x: x[1], default=("weekly", 0.25))[0]
        }
        
        return {
            "patterns": patterns,
            "best_performing": best_performing
        }
    
    def _determine_optimal_timing(self, market_factors: Dict[str, Any],
                                historical_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal timing based on market and historical factors"""
        # Use historical patterns as base
        optimal = historical_patterns["best_performing"].copy()
        
        # Adjust based on market factors
        confidence = 0.7  # Base confidence
        
        if market_factors["key_factors"]:
            confidence += 0.1
        
        if market_factors["optimal_conditions"]:
            confidence += 0.1
        
        optimal["confidence"] = min(confidence, 1.0)
        
        return optimal
    
    def _calculate_timing_improvement(self, optimal_timing: Dict[str, Any],
                                    historical_patterns: Dict[str, Any]) -> float:
        """Calculate expected improvement from optimal timing"""
        # Calculate improvement over average performance
        avg_performance = 0.25  # Default average
        
        if historical_patterns["patterns"]["day_performance"]:
            avg_performance = statistics.mean(historical_patterns["patterns"]["day_performance"].values())
        
        optimal_performance = 0.3  # Estimated optimal performance
        
        improvement = (optimal_performance - avg_performance) / avg_performance
        
        return max(improvement, 0.0)
    
    def _generate_timing_reasoning(self, optimal_timing: Dict[str, Any],
                                 market_factors: Dict[str, Any],
                                 historical_patterns: Dict[str, Any]) -> str:
        """Generate reasoning for timing recommendations"""
        reasoning_parts = []
        
        # Historical performance reasoning
        reasoning_parts.append(f"Historical data shows {optimal_timing['day']} at {optimal_timing['time']} performs best")
        
        # Market factors reasoning
        if market_factors["key_factors"]:
            reasoning_parts.append(f"Market conditions favor timing: {', '.join(market_factors['key_factors'])}")
        
        # Confidence reasoning
        if optimal_timing["confidence"] > 0.8:
            reasoning_parts.append("High confidence recommendation based on strong data patterns")
        elif optimal_timing["confidence"] > 0.6:
            reasoning_parts.append("Moderate confidence recommendation based on available data")
        else:
            reasoning_parts.append("Lower confidence recommendation - consider testing")
        
        return ". ".join(reasoning_parts) + "."
    
    def _analyze_message_performance_patterns(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze message performance patterns"""
        patterns = {
            "high_performing_subjects": [],
            "high_performing_content": [],
            "low_performing_patterns": [],
            "engagement_drivers": []
        }
        
        # Extract patterns from engagement data
        messages = engagement_data.get("messages", [])
        
        for message in messages:
            performance = message.get("performance", {})
            
            if performance.get("email_open_rate", 0) > 0.3:  # High open rate
                patterns["high_performing_subjects"].append(message.get("subject", ""))
            
            if performance.get("email_click_rate", 0) > 0.08:  # High click rate
                patterns["high_performing_content"].append(message.get("content_type", ""))
            
            if performance.get("response_rate", 0) < 0.01:  # Low response rate
                patterns["low_performing_patterns"].append(message.get("content_type", ""))
        
        return patterns
    
    def _generate_message_improvement(self, message: Dict[str, Any],
                                   performance_patterns: Dict[str, Any],
                                   engagement_data: Dict[str, Any]) -> Optional[MessageImprovement]:
        """Generate improvement suggestions for a specific message"""
        message_type = message.get("type", "email")
        current_score = message.get("performance_score", 0.5)
        
        improvements = []
        expected_impact = 0.0
        
        # Subject line improvements
        if message.get("subject_score", 0.5) < 0.7:
            improvements.append("Improve subject line clarity and urgency")
            expected_impact += 0.05
        
        # Content improvements
        if message.get("content_score", 0.5) < 0.7:
            improvements.append("Enhance content relevance and value proposition")
            expected_impact += 0.03
        
        # Personalization improvements
        if message.get("personalization_score", 0.5) < 0.7:
            improvements.append("Increase personalization and targeting")
            expected_impact += 0.04
        
        if expected_impact < self.analytics_config["optimization_threshold"]:
            return None
        
        return MessageImprovement(
            message_type=message_type,
            current_score=current_score,
            suggested_improvements=improvements,
            expected_impact=expected_impact,
            confidence=0.7,
            a_b_test_recommendations=[]
        )
    
    def _generate_ab_test_recommendations(self, current_messages: List[Dict[str, Any]],
                                        performance_patterns: Dict[str, Any]) -> List[str]:
        """Generate A/B test recommendations"""
        recommendations = []
        
        # Subject line A/B tests
        recommendations.append("Test subject line variations: direct vs. curiosity-driven")
        
        # Content A/B tests
        recommendations.append("Test content length: short vs. detailed")
        
        # Timing A/B tests
        recommendations.append("Test send times: morning vs. afternoon")
        
        # Personalization A/B tests
        recommendations.append("Test personalization level: basic vs. advanced")
        
        return recommendations
    
    def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        return {
            "service_name": "Predictive Analytics Service",
            "version": "1.0",
            "performance_baselines": self.performance_baselines,
            "analytics_config": self.analytics_config,
            "market_impact_factors": self.market_impact_factors,
            "historical_data_counts": {
                "campaigns": sum(len(campaigns) for campaigns in self.campaign_history.values()),
                "audiences": sum(len(audiences) for audiences in self.audience_performance.values()),
                "timing_data": sum(len(timing) for timing in self.timing_performance.values()),
                "messages": sum(len(messages) for messages in self.message_performance.values())
            },
            "last_updated": datetime.now().isoformat()
        }
