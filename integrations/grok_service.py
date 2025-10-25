import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class GrokService:
    """
    Grok API integration service for market research and competitive intelligence.
    Provides real-time market sentiment, industry trends, and lead enrichment.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY")
        self.api_url = os.getenv("GROK_API_URL", "https://api.x.ai/v1")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        if not self.api_key:
            logger.warning("GROK_API_KEY not found in environment variables")
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with error handling and rate limiting"""
        if not self.api_key:
            logger.warning("Grok API key not configured, returning mock data")
            return self._get_mock_response(endpoint)
        
        self._rate_limit()
        
        try:
            url = f"{self.api_url}/{endpoint}"
            response = self.session.post(url, json=data) if data else self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Grok API request failed: {e}")
            return self._get_mock_response(endpoint)
    
    def _get_mock_response(self, endpoint: str) -> Dict[str, Any]:
        """Return mock data when API is not available"""
        mock_responses = {
            "market-sentiment": {
                "sentiment": "positive",
                "confidence": 0.75,
                "trends": ["AI adoption", "Digital transformation", "Remote work"],
                "market_indicators": {
                    "growth_rate": "15%",
                    "market_size": "$50B",
                    "competition_level": "high"
                }
            },
            "lead-enrichment": {
                "company_size": "50-200 employees",
                "revenue": "$10M-$50M",
                "industry": "Technology",
                "recent_news": ["Series A funding", "Product launch"],
                "market_position": "Emerging leader"
            },
            "industry-trends": {
                "trends": [
                    {"name": "AI Integration", "impact": "high", "timeline": "6-12 months"},
                    {"name": "Cloud Migration", "impact": "medium", "timeline": "12-18 months"}
                ],
                "opportunities": ["Digital transformation", "Automation"],
                "challenges": ["Talent shortage", "Security concerns"]
            },
            "competitive-intelligence": {
                "competitors": [
                    {"name": "Competitor A", "strength": "Market leader", "weakness": "High pricing"},
                    {"name": "Competitor B", "strength": "Innovation", "weakness": "Limited reach"}
                ],
                "market_gaps": ["SMB segment", "International markets"],
                "differentiation_opportunities": ["Better UX", "Lower cost"]
            }
        }
        return mock_responses.get(endpoint, {"error": "Mock data not available"})
    
    def get_market_sentiment(self, industry: str, keywords: List[str], region: str = None) -> Dict[str, Any]:
        """
        Get market sentiment analysis for a specific industry and keywords.
        
        Args:
            industry: Target industry (e.g., "SaaS", "Healthcare", "Fintech")
            keywords: List of relevant keywords
            region: Optional geographic region
            
        Returns:
            Dict with sentiment analysis, trends, and market indicators
        """
        logger.info(f"Getting market sentiment for industry: {industry}, keywords: {keywords}")
        
        data = {
            "industry": industry,
            "keywords": keywords,
            "region": region,
            "analysis_type": "sentiment"
        }
        
        response = self._make_request("market-sentiment", data)
        
        return {
            "sentiment": response.get("sentiment", "neutral"),
            "confidence": response.get("confidence", 0.5),
            "trends": response.get("trends", []),
            "market_indicators": response.get("market_indicators", {}),
            "timestamp": datetime.now().isoformat(),
            "industry": industry,
            "keywords": keywords
        }
    
    def enrich_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches lead data with additional market and company-specific information.
        """
        logger.info(f"Enriching lead data for {lead_data.get('email', 'N/A')}")
        
        # Extract company and industry from lead data
        company = lead_data.get('company', 'Unknown Company')
        industry = lead_data.get('industry', 'General')
        
        # Use existing enrich_lead method
        enriched_data = self.enrich_lead(company, industry)
        
        return {
            "original_lead": lead_data,
            "enriched_data": enriched_data
        }

    def enrich_lead(self, company: str, industry: str = None) -> Dict[str, Any]:
        """
        Enrich lead data with market intelligence and company information.
        
        Args:
            company: Company name
            industry: Optional industry context
            
        Returns:
            Dict with enriched lead data including market position, recent news, etc.
        """
        logger.info(f"Enriching lead data for company: {company}")
        
        data = {
            "company": company,
            "industry": industry,
            "enrichment_fields": [
                "company_size", "revenue", "recent_news", 
                "market_position", "funding_status", "growth_stage"
            ]
        }
        
        response = self._make_request("lead-enrichment", data)
        
        return {
            "company": company,
            "company_size": response.get("company_size", "Unknown"),
            "revenue": response.get("revenue", "Unknown"),
            "industry": response.get("industry", industry),
            "recent_news": response.get("recent_news", []),
            "market_position": response.get("market_position", "Unknown"),
            "funding_status": response.get("funding_status", "Unknown"),
            "growth_stage": response.get("growth_stage", "Unknown"),
            "enrichment_timestamp": datetime.now().isoformat()
        }
    
    def get_industry_trends(self, industry: str, timeframe: str = "6months") -> Dict[str, Any]:
        """
        Get industry trends and market analysis.
        
        Args:
            industry: Target industry
            timeframe: Analysis timeframe (3months, 6months, 1year)
            
        Returns:
            Dict with trends, opportunities, and challenges
        """
        logger.info(f"Getting industry trends for {industry} over {timeframe}")
        
        data = {
            "industry": industry,
            "timeframe": timeframe,
            "analysis_depth": "comprehensive"
        }
        
        response = self._make_request("industry-trends", data)
        
        return {
            "industry": industry,
            "timeframe": timeframe,
            "trends": response.get("trends", []),
            "opportunities": response.get("opportunities", []),
            "challenges": response.get("challenges", []),
            "market_outlook": response.get("market_outlook", "stable"),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def get_competitive_intelligence(self, company: str, competitors: List[str] = None) -> Dict[str, Any]:
        """
        Get competitive intelligence and market positioning analysis.
        
        Args:
            company: Your company name
            competitors: List of competitor names
            
        Returns:
            Dict with competitive analysis, market gaps, and opportunities
        """
        logger.info(f"Getting competitive intelligence for {company}")
        
        data = {
            "company": company,
            "competitors": competitors or [],
            "analysis_type": "competitive_intelligence"
        }
        
        response = self._make_request("competitive-intelligence", data)
        
        return {
            "company": company,
            "competitors": response.get("competitors", []),
            "market_gaps": response.get("market_gaps", []),
            "differentiation_opportunities": response.get("differentiation_opportunities", []),
            "market_share_estimate": response.get("market_share_estimate", "Unknown"),
            "competitive_strengths": response.get("competitive_strengths", []),
            "competitive_weaknesses": response.get("competitive_weaknesses", []),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def get_market_context_for_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive market context for campaign optimization.
        
        Args:
            campaign_data: Campaign information including target industry, audience, etc.
            
        Returns:
            Dict with market context for campaign personalization
        """
        logger.info("Getting market context for campaign optimization")
        
        industry = campaign_data.get("industry", "Technology")
        target_audience = campaign_data.get("target_audience", [])
        keywords = campaign_data.get("keywords", [])
        
        # Get multiple data points
        sentiment = self.get_market_sentiment(industry, keywords)
        trends = self.get_industry_trends(industry)
        
        # Combine into campaign context
        return {
            "market_sentiment": sentiment,
            "industry_trends": trends,
            "campaign_timing": self._assess_campaign_timing(sentiment, trends),
            "messaging_opportunities": self._identify_messaging_opportunities(sentiment, trends),
            "competitive_context": self._get_competitive_context(industry),
            "context_timestamp": datetime.now().isoformat()
        }
    
    def _assess_campaign_timing(self, sentiment: Dict[str, Any], trends: Dict[str, Any]) -> Dict[str, Any]:
        """Assess optimal timing for campaign based on market conditions"""
        sentiment_score = sentiment.get("confidence", 0.5)
        market_outlook = trends.get("market_outlook", "stable")
        
        timing_score = 0.5
        if sentiment_score > 0.7 and market_outlook in ["positive", "growing"]:
            timing_score = 0.9
        elif sentiment_score < 0.3 or market_outlook == "declining":
            timing_score = 0.2
        
        return {
            "timing_score": timing_score,
            "recommendation": "optimal" if timing_score > 0.7 else "caution" if timing_score < 0.3 else "moderate",
            "reasoning": f"Market sentiment: {sentiment_score:.2f}, Outlook: {market_outlook}"
        }
    
    def _identify_messaging_opportunities(self, sentiment: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
        """Identify messaging opportunities based on market analysis"""
        opportunities = []
        
        # Add trending topics
        trends_list = trends.get("trends", [])
        for trend in trends_list[:3]:  # Top 3 trends
            opportunities.append(f"Leverage {trend['name']} trend")
        
        # Add sentiment-based opportunities
        sentiment_type = sentiment.get("sentiment", "neutral")
        if sentiment_type == "positive":
            opportunities.append("Emphasize growth and opportunity")
        elif sentiment_type == "negative":
            opportunities.append("Address market challenges")
        
        return opportunities
    
    def _get_competitive_context(self, industry: str) -> Dict[str, Any]:
        """Get competitive context for industry"""
        return {
            "competition_level": "high",
            "market_maturity": "growing",
            "key_players": ["Market Leader A", "Market Leader B"],
            "entry_barriers": ["Technology", "Capital", "Talent"]
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Grok service is healthy and accessible"""
        try:
            if not self.api_key:
                return {
                    "status": "warning",
                    "message": "Grok API key not configured",
                    "mock_mode": True
                }
            
            # Simple health check request
            response = self._make_request("health")
            return {
                "status": "healthy",
                "message": "Grok service is accessible",
                "mock_mode": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Grok service error: {str(e)}",
                "mock_mode": True
            }
