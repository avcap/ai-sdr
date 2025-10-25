import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import re
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class QualityMetric:
    """Represents a quality metric with score and details"""
    name: str
    score: float
    max_score: float
    details: Dict[str, Any]
    recommendations: List[str]

@dataclass
class QualityReport:
    """Comprehensive quality report for knowledge"""
    overall_score: float
    metrics: List[QualityMetric]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    timestamp: str

class KnowledgeQualityService:
    """
    Comprehensive knowledge quality assessment service that validates and scores
    extracted knowledge for completeness, specificity, consistency, and actionability.
    """
    
    def __init__(self):
        # Quality criteria weights
        self.quality_weights = {
            "completeness": 0.25,
            "specificity": 0.25,
            "consistency": 0.20,
            "actionability": 0.20,
            "relevance": 0.10
        }
        
        # Required fields for different knowledge types
        self.required_fields = {
            "company_info": ["company_name", "industry"],
            "products": [],
            "value_propositions": [],
            "target_audience": ["roles"],
            "sales_approach": [],
            "competitive_advantages": []
        }
        
        # Generic terms that indicate low specificity
        self.generic_terms = [
            "not specified", "unknown", "various", "multiple", "several", 
            "some", "general", "typical", "common", "standard"
        ]
        
        # Actionable keywords that indicate high actionability
        self.actionable_keywords = [
            "increase", "reduce", "save", "improve", "boost", "enhance",
            "streamline", "automate", "optimize", "accelerate", "maximize",
            "minimize", "eliminate", "achieve", "deliver", "provide"
        ]
    
    def assess_knowledge_quality(self, 
                                 knowledge: Dict[str, Any], 
                                 document_type: Optional[str] = None,
                                 source_type: str = "document") -> Dict[str, Any]:
        """
        Assesses the overall quality of a given knowledge dictionary.
        This is an alias for score_extracted_knowledge for compatibility.
        """
        quality_report = self.score_extracted_knowledge(knowledge)
        
        return {
            "overall_score": quality_report.overall_score,
            "quality_rating": self._get_quality_rating(quality_report.overall_score),
            "metrics": {metric.name: metric for metric in quality_report.metrics},
            "recommendations": quality_report.recommendations,
            "timestamp": quality_report.timestamp
        }

    def score_extracted_knowledge(self, knowledge_data: Dict[str, Any]) -> QualityReport:
        """
        Score extracted knowledge and generate comprehensive quality report.
        
        Args:
            knowledge_data: Knowledge structure to assess
            
        Returns:
            Comprehensive quality report
        """
        logger.info("Starting knowledge quality assessment")
        
        # Calculate individual quality metrics
        completeness_metric = self.validate_completeness(knowledge_data)
        specificity_metric = self.assess_specificity(knowledge_data)
        consistency_metric = self.assess_consistency(knowledge_data)
        actionability_metric = self.assess_actionability(knowledge_data)
        relevance_metric = self.assess_relevance(knowledge_data)
        
        # Collect all metrics
        metrics = [
            completeness_metric,
            specificity_metric,
            consistency_metric,
            actionability_metric,
            relevance_metric
        ]
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        
        # Generate insights
        strengths = self._identify_strengths(metrics)
        weaknesses = self._identify_weaknesses(metrics)
        recommendations = self._generate_recommendations(metrics, knowledge_data)
        
        # Create quality report
        report = QualityReport(
            overall_score=overall_score,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Quality assessment completed - Overall score: {overall_score:.2f}")
        return report
    
    def validate_completeness(self, knowledge_data: Dict[str, Any]) -> QualityMetric:
        """Validate completeness of knowledge structure"""
        logger.debug("Assessing knowledge completeness")
        
        total_fields = 0
        completed_fields = 0
        field_details = {}
        
        # Check each required section
        for section, required_fields in self.required_fields.items():
            section_score = 0
            section_total = 0
            
            if section in knowledge_data and knowledge_data[section]:
                section_total += 1
                
                if required_fields:
                    # Check specific required fields
                    for field in required_fields:
                        section_total += 1
                        if field in knowledge_data[section]:
                            field_value = knowledge_data[section][field]
                            if field_value and field_value != "Not specified":
                                completed_fields += 1
                                section_score += 1
                            else:
                                field_details[f"{section}.{field}"] = "Missing or generic"
                        else:
                            field_details[f"{section}.{field}"] = "Field not found"
                else:
                    # Section exists and has content
                    completed_fields += 1
                    section_score += 1
            else:
                section_total += 1
                field_details[section] = "Section missing"
            
            total_fields += section_total
            field_details[f"{section}_score"] = section_score / max(section_total, 1)
        
        completeness_score = completed_fields / max(total_fields, 1)
        
        # Generate recommendations
        recommendations = []
        if completeness_score < 0.7:
            recommendations.append("Add missing company information (name, industry)")
        if completeness_score < 0.5:
            recommendations.append("Define target audience roles and characteristics")
        if completeness_score < 0.3:
            recommendations.append("Provide value propositions and competitive advantages")
        
        return QualityMetric(
            name="completeness",
            score=completeness_score,
            max_score=1.0,
            details=field_details,
            recommendations=recommendations
        )
    
    def assess_specificity(self, knowledge_data: Dict[str, Any]) -> QualityMetric:
        """Assess specificity vs generic nature of knowledge"""
        logger.debug("Assessing knowledge specificity")
        
        specificity_scores = {}
        total_score = 0
        total_weight = 0
        
        # Assess each section
        sections_to_assess = [
            "company_info", "products", "value_propositions", 
            "target_audience", "sales_approach", "competitive_advantages"
        ]
        
        for section in sections_to_assess:
            if section in knowledge_data:
                section_score = self._assess_section_specificity(
                    section, knowledge_data[section]
                )
                specificity_scores[section] = section_score
                total_score += section_score
                total_weight += 1
        
        overall_specificity = total_score / max(total_weight, 1)
        
        # Generate recommendations
        recommendations = []
        if overall_specificity < 0.6:
            recommendations.append("Replace generic terms with specific details")
        if overall_specificity < 0.4:
            recommendations.append("Add concrete examples and specific metrics")
        if overall_specificity < 0.2:
            recommendations.append("Provide detailed company and product information")
        
        return QualityMetric(
            name="specificity",
            score=overall_specificity,
            max_score=1.0,
            details=specificity_scores,
            recommendations=recommendations
        )
    
    def _assess_section_specificity(self, section: str, section_data: Any) -> float:
        """Assess specificity of a specific section"""
        if not section_data:
            return 0.0
        
        if isinstance(section_data, dict):
            # Count specific vs generic fields
            specific_fields = 0
            total_fields = 0
            
            for key, value in section_data.items():
                if isinstance(value, str):
                    total_fields += 1
                    if not any(term in value.lower() for term in self.generic_terms):
                        specific_fields += 1
            
            return specific_fields / max(total_fields, 1)
        
        elif isinstance(section_data, list):
            # Count specific vs generic items
            specific_items = 0
            total_items = len(section_data)
            
            for item in section_data:
                if isinstance(item, str):
                    if not any(term in item.lower() for term in self.generic_terms):
                        specific_items += 1
            
            return specific_items / max(total_items, 1)
        
        elif isinstance(section_data, str):
            # Single string value
            if any(term in section_data.lower() for term in self.generic_terms):
                return 0.0
            else:
                return 1.0
        
        return 0.5  # Default for unknown types
    
    def assess_consistency(self, knowledge_data: Dict[str, Any]) -> QualityMetric:
        """Assess internal consistency of knowledge"""
        logger.debug("Assessing knowledge consistency")
        
        consistency_issues = []
        consistency_score = 1.0
        
        # Check for contradictory information
        consistency_score -= self._check_company_info_consistency(knowledge_data, consistency_issues)
        consistency_score -= self._check_target_audience_consistency(knowledge_data, consistency_issues)
        consistency_score -= self._check_value_proposition_consistency(knowledge_data, consistency_issues)
        consistency_score -= self._check_sales_approach_consistency(knowledge_data, consistency_issues)
        
        consistency_score = max(consistency_score, 0.0)
        
        # Generate recommendations
        recommendations = []
        if consistency_score < 0.8:
            recommendations.append("Review and resolve contradictory information")
        if consistency_score < 0.6:
            recommendations.append("Ensure company information is consistent across all sections")
        if consistency_score < 0.4:
            recommendations.append("Standardize terminology and messaging")
        
        return QualityMetric(
            name="consistency",
            score=consistency_score,
            max_score=1.0,
            details={"issues": consistency_issues},
            recommendations=recommendations
        )
    
    def _check_company_info_consistency(self, knowledge_data: Dict[str, Any], issues: List[str]) -> float:
        """Check consistency in company information"""
        penalty = 0.0
        
        company_info = knowledge_data.get("company_info", {})
        if not isinstance(company_info, dict):
            return penalty
        
        # Check for conflicting company sizes
        size_indicators = ["startup", "small", "medium", "large", "enterprise"]
        size_values = [str(v).lower() for v in company_info.values()]
        
        conflicting_sizes = []
        for size in size_indicators:
            if sum(1 for val in size_values if size in val) > 1:
                conflicting_sizes.append(size)
        
        if conflicting_sizes:
            issues.append(f"Conflicting company size indicators: {conflicting_sizes}")
            penalty += 0.2
        
        # Check for conflicting industry information
        industry_info = str(company_info).lower()
        tech_terms = ["tech", "software", "saas", "ai", "technology"]
        non_tech_terms = ["healthcare", "finance", "retail", "manufacturing"]
        
        has_tech = any(term in industry_info for term in tech_terms)
        has_non_tech = any(term in industry_info for term in non_tech_terms)
        
        if has_tech and has_non_tech:
            issues.append("Conflicting industry information (tech vs non-tech)")
            penalty += 0.1
        
        return penalty
    
    def _check_target_audience_consistency(self, knowledge_data: Dict[str, Any], issues: List[str]) -> float:
        """Check consistency in target audience information"""
        penalty = 0.0
        
        target_audience = knowledge_data.get("target_audience", {})
        if not isinstance(target_audience, dict):
            return penalty
        
        # Check for conflicting company sizes in target audience
        company_sizes = target_audience.get("company_sizes", [])
        if isinstance(company_sizes, list):
            size_categories = []
            for size in company_sizes:
                if "startup" in size.lower():
                    size_categories.append("startup")
                elif "small" in size.lower():
                    size_categories.append("small")
                elif "enterprise" in size.lower():
                    size_categories.append("enterprise")
            
            if len(set(size_categories)) > 2:  # Too many different size categories
                issues.append("Target audience spans too many company size categories")
                penalty += 0.1
        
        return penalty
    
    def _check_value_proposition_consistency(self, knowledge_data: Dict[str, Any], issues: List[str]) -> float:
        """Check consistency in value propositions"""
        penalty = 0.0
        
        value_props = knowledge_data.get("value_propositions", [])
        if not isinstance(value_props, list):
            return penalty
        
        # Check for contradictory value propositions
        contradictory_pairs = [
            ("increase", "decrease"),
            ("reduce", "increase"),
            ("save", "cost"),
            ("fast", "slow"),
            ("simple", "complex")
        ]
        
        for i, vp1 in enumerate(value_props):
            for j, vp2 in enumerate(value_props):
                if i != j and isinstance(vp1, str) and isinstance(vp2, str):
                    for pos_word, neg_word in contradictory_pairs:
                        if pos_word in vp1.lower() and neg_word in vp2.lower():
                            issues.append(f"Contradictory value propositions: '{vp1}' vs '{vp2}'")
                            penalty += 0.1
        
        return penalty
    
    def _check_sales_approach_consistency(self, knowledge_data: Dict[str, Any], issues: List[str]) -> float:
        """Check consistency in sales approach"""
        penalty = 0.0
        
        sales_approach = knowledge_data.get("sales_approach", "")
        if not isinstance(sales_approach, str):
            return penalty
        
        # Check for conflicting methodologies
        methodologies = ["consultative", "transactional", "relationship", "solution"]
        mentioned_methodologies = []
        
        for method in methodologies:
            if method in sales_approach.lower():
                mentioned_methodologies.append(method)
        
        if len(mentioned_methodologies) > 2:
            issues.append("Multiple conflicting sales methodologies mentioned")
            penalty += 0.1
        
        return penalty
    
    def assess_actionability(self, knowledge_data: Dict[str, Any]) -> QualityMetric:
        """Assess actionability of knowledge for sales activities"""
        logger.debug("Assessing knowledge actionability")
        
        actionability_scores = {}
        total_score = 0
        total_weight = 0
        
        # Assess value propositions actionability
        value_props = knowledge_data.get("value_propositions", [])
        if value_props:
            vp_score = self._assess_value_proposition_actionability(value_props)
            actionability_scores["value_propositions"] = vp_score
            total_score += vp_score
            total_weight += 1
        
        # Assess target audience actionability
        target_audience = knowledge_data.get("target_audience", {})
        if target_audience:
            ta_score = self._assess_target_audience_actionability(target_audience)
            actionability_scores["target_audience"] = ta_score
            total_score += ta_score
            total_weight += 1
        
        # Assess competitive advantages actionability
        competitive_advantages = knowledge_data.get("competitive_advantages", [])
        if competitive_advantages:
            ca_score = self._assess_competitive_advantages_actionability(competitive_advantages)
            actionability_scores["competitive_advantages"] = ca_score
            total_score += ca_score
            total_weight += 1
        
        overall_actionability = total_score / max(total_weight, 1)
        
        # Generate recommendations
        recommendations = []
        if overall_actionability < 0.6:
            recommendations.append("Add specific metrics and outcomes to value propositions")
        if overall_actionability < 0.4:
            recommendations.append("Define specific target roles and pain points")
        if overall_actionability < 0.2:
            recommendations.append("Provide concrete competitive differentiators")
        
        return QualityMetric(
            name="actionability",
            score=overall_actionability,
            max_score=1.0,
            details=actionability_scores,
            recommendations=recommendations
        )
    
    def _assess_value_proposition_actionability(self, value_props: List[str]) -> float:
        """Assess actionability of value propositions"""
        actionable_count = 0
        total_count = len(value_props)
        
        for vp in value_props:
            if isinstance(vp, str):
                # Check for actionable language
                if any(keyword in vp.lower() for keyword in self.actionable_keywords):
                    actionable_count += 1
                # Check for specific metrics
                elif re.search(r'\d+%|\$\d+|\d+x|\d+\s*(times|fold)', vp):
                    actionable_count += 1
        
        return actionable_count / max(total_count, 1)
    
    def _assess_target_audience_actionability(self, target_audience: Dict[str, Any]) -> float:
        """Assess actionability of target audience information"""
        score = 0.0
        
        # Check for specific roles
        roles = target_audience.get("roles", [])
        if isinstance(roles, list) and roles:
            specific_roles = [role for role in roles if len(role.split()) > 1]
            score += min(len(specific_roles) / 3, 1.0) * 0.4
        
        # Check for specific industries
        industries = target_audience.get("industries", [])
        if isinstance(industries, list) and industries:
            specific_industries = [ind for ind in industries if len(ind.split()) > 1]
            score += min(len(specific_industries) / 3, 1.0) * 0.3
        
        # Check for pain points
        pain_points = target_audience.get("pain_points", [])
        if isinstance(pain_points, list) and pain_points:
            score += min(len(pain_points) / 2, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _assess_competitive_advantages_actionability(self, competitive_advantages: List[str]) -> float:
        """Assess actionability of competitive advantages"""
        actionable_count = 0
        total_count = len(competitive_advantages)
        
        for advantage in competitive_advantages:
            if isinstance(advantage, str):
                # Check for specificity (more than 3 words)
                if len(advantage.split()) > 3:
                    actionable_count += 1
                # Check for concrete differentiators
                elif any(word in advantage.lower() for word in ["only", "unique", "exclusive", "patented"]):
                    actionable_count += 1
        
        return actionable_count / max(total_count, 1)
    
    def assess_relevance(self, knowledge_data: Dict[str, Any]) -> QualityMetric:
        """Assess relevance of knowledge for sales activities"""
        logger.debug("Assessing knowledge relevance")
        
        relevance_score = 0.0
        relevance_details = {}
        
        # Check sales-relevant content
        sales_keywords = [
            "customer", "prospect", "lead", "deal", "pipeline", "close",
            "revenue", "growth", "market", "competition", "value", "benefit"
        ]
        
        content_text = str(knowledge_data).lower()
        sales_relevance = sum(1 for keyword in sales_keywords if keyword in content_text)
        sales_relevance_score = min(sales_relevance / len(sales_keywords), 1.0)
        
        relevance_details["sales_relevance"] = sales_relevance_score
        relevance_score += sales_relevance_score * 0.6
        
        # Check business relevance
        business_keywords = [
            "company", "business", "organization", "product", "service",
            "solution", "industry", "market", "strategy", "goal"
        ]
        
        business_relevance = sum(1 for keyword in business_keywords if keyword in content_text)
        business_relevance_score = min(business_relevance / len(business_keywords), 1.0)
        
        relevance_details["business_relevance"] = business_relevance_score
        relevance_score += business_relevance_score * 0.4
        
        # Generate recommendations
        recommendations = []
        if relevance_score < 0.6:
            recommendations.append("Add more sales-focused content and terminology")
        if relevance_score < 0.4:
            recommendations.append("Include customer pain points and business outcomes")
        if relevance_score < 0.2:
            recommendations.append("Focus on business value and competitive positioning")
        
        return QualityMetric(
            name="relevance",
            score=min(relevance_score, 1.0),
            max_score=1.0,
            details=relevance_details,
            recommendations=recommendations
        )
    
    def _get_quality_rating(self, score: float) -> str:
        """Returns a human-readable quality rating based on the score."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Acceptable"
        elif score >= 0.3:
            return "Poor"
        else:
            return "Very Poor"

    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate overall quality score from individual metrics"""
        total_score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weight = self.quality_weights.get(metric.name, 0.2)
            total_score += metric.score * weight
            total_weight += weight
        
        return total_score / max(total_weight, 1.0)
    
    def _identify_strengths(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify strengths based on high-scoring metrics"""
        strengths = []
        
        for metric in metrics:
            if metric.score >= 0.8:
                strengths.append(f"Strong {metric.name} (score: {metric.score:.2f})")
            elif metric.score >= 0.6:
                strengths.append(f"Good {metric.name} (score: {metric.score:.2f})")
        
        return strengths
    
    def _identify_weaknesses(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify weaknesses based on low-scoring metrics"""
        weaknesses = []
        
        for metric in metrics:
            if metric.score < 0.4:
                weaknesses.append(f"Poor {metric.name} (score: {metric.score:.2f})")
            elif metric.score < 0.6:
                weaknesses.append(f"Weak {metric.name} (score: {metric.score:.2f})")
        
        return weaknesses
    
    def _generate_recommendations(self, metrics: List[QualityMetric], 
                                knowledge_data: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations for improvement"""
        recommendations = []
        
        # Collect recommendations from all metrics
        for metric in metrics:
            recommendations.extend(metric.recommendations)
        
        # Add overall recommendations based on overall score
        overall_score = self._calculate_overall_score(metrics)
        
        if overall_score < 0.5:
            recommendations.append("Consider providing more detailed company and product information")
            recommendations.append("Add specific examples and case studies")
        
        if overall_score < 0.3:
            recommendations.append("Review and improve knowledge extraction process")
            recommendations.append("Consider using multiple document sources")
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(recommendations))
        
        # Prioritize by frequency and importance
        priority_keywords = ["missing", "add", "provide", "include", "define"]
        prioritized = []
        
        for rec in unique_recommendations:
            if any(keyword in rec.lower() for keyword in priority_keywords):
                prioritized.insert(0, rec)
            else:
                prioritized.append(rec)
        
        return prioritized[:10]  # Return top 10 recommendations
    
    def generate_quality_report(self, scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a formatted quality report"""
        return {
            "quality_assessment": {
                "overall_score": scores.get("overall_score", 0.0),
                "grade": self._score_to_grade(scores.get("overall_score", 0.0)),
                "timestamp": datetime.now().isoformat()
            },
            "detailed_scores": scores.get("detailed_scores", {}),
            "recommendations": scores.get("recommendations", []),
            "next_steps": self._generate_next_steps(scores)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_next_steps(self, scores: Dict[str, Any]) -> List[str]:
        """Generate next steps based on quality scores"""
        next_steps = []
        overall_score = scores.get("overall_score", 0.0)
        
        if overall_score < 0.5:
            next_steps.append("Review and improve knowledge extraction process")
            next_steps.append("Add more comprehensive document sources")
        elif overall_score < 0.7:
            next_steps.append("Address specific quality issues identified")
            next_steps.append("Consider additional validation steps")
        else:
            next_steps.append("Knowledge quality is good - proceed with confidence")
            next_steps.append("Monitor quality metrics over time")
        
        return next_steps
    
    def get_quality_benchmarks(self) -> Dict[str, Any]:
        """Get quality benchmarks and thresholds"""
        return {
            "thresholds": {
                "excellent": 0.9,
                "good": 0.7,
                "acceptable": 0.5,
                "poor": 0.3
            },
            "weights": self.quality_weights,
            "required_fields": self.required_fields,
            "generic_terms": self.generic_terms,
            "actionable_keywords": self.actionable_keywords
        }
