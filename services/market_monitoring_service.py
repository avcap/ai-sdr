import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import time
from collections import defaultdict

from integrations.grok_service import GrokService

logger = logging.getLogger(__name__)

@dataclass
class MarketTrend:
    """Represents a market trend with metadata"""
    name: str
    impact: str  # "high", "medium", "low"
    timeline: str
    confidence: float
    source: str
    timestamp: str
    description: str

@dataclass
class CompetitorActivity:
    """Represents competitor activity"""
    competitor: str
    activity_type: str
    description: str
    impact_level: str
    timestamp: str
    source: str

@dataclass
class MarketOpportunity:
    """Represents a market opportunity"""
    title: str
    description: str
    industry: str
    opportunity_type: str
    confidence: float
    potential_value: str
    timeline: str
    requirements: List[str]

@dataclass
class MarketAlert:
    """Represents a market alert"""
    alert_id: str
    alert_type: str
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    industry: str
    timestamp: str
    source: str
    actionable: bool
    recommendations: List[str]

class MarketMonitoringService:
    """
    Continuous market intelligence service that monitors industry trends,
    competitor activities, and detects market opportunities in real-time.
    """
    
    def __init__(self):
        self.grok_service = GrokService()
        self.cache_expiry_minutes = 30
        self.cache = {}
        
        # Monitoring configuration
        self.monitoring_config = {
            "trend_check_interval": 3600,  # 1 hour
            "competitor_check_interval": 1800,  # 30 minutes
            "opportunity_check_interval": 7200,  # 2 hours
            "alert_threshold": 0.7,
            "max_trends_per_industry": 10,
            "max_competitors_per_company": 5
        }
        
        # Active monitoring sessions
        self.active_monitors = {}
        self.trend_cache = {}
        self.competitor_cache = {}
        self.opportunity_cache = {}
        
        # Alert preferences
        self.alert_preferences = {
            "trend_alerts": True,
            "competitor_alerts": True,
            "opportunity_alerts": True,
            "critical_threshold": 0.8
        }
        
        # Historical data storage
        self.historical_trends = defaultdict(list)
        self.historical_competitors = defaultdict(list)
        self.historical_opportunities = defaultdict(list)
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves data from cache if not expired."""
        entry = self.cache.get(key)
        if entry and (datetime.now() - entry["timestamp"]) < timedelta(minutes=self.cache_expiry_minutes):
            logger.debug(f"Cache hit for {key}")
            return entry["data"]
        logger.debug(f"Cache miss or expired for {key}")
        return None
        
    def _set_to_cache(self, key: str, data: Dict[str, Any]):
        """Stores data in cache with a timestamp."""
        self.cache[key] = {"data": data, "timestamp": datetime.now()}
        logger.debug(f"Cached data for {key}")

    def monitor_industry_trends(self, industries: List[str], 
                              timeframe: str = "6months") -> Dict[str, List[MarketTrend]]:
        """
        Monitor trends for specified industries.
        
        Args:
            industries: List of industries to monitor
            timeframe: Analysis timeframe
            
        Returns:
            Dict mapping industries to their trends
        """
        logger.info(f"Monitoring trends for industries: {industries}")
        
        industry_trends = {}
        
        for industry in industries:
            try:
                # Get trends from Grok service
                trends_data = self.grok_service.get_industry_trends(industry, timeframe)
                
                # Convert to MarketTrend objects
                trends = []
                for trend_info in trends_data.get("trends", []):
                    trend = MarketTrend(
                        name=trend_info.get("name", "Unknown Trend"),
                        impact=trend_info.get("impact", "medium"),
                        timeline=trend_info.get("timeline", "Unknown"),
                        confidence=0.8,  # Default confidence
                        source="grok_api",
                        timestamp=datetime.now().isoformat(),
                        description=f"Trend in {industry}: {trend_info.get('name', '')}"
                    )
                    trends.append(trend)
                
                # Cache trends
                self.trend_cache[industry] = {
                    "trends": trends,
                    "last_updated": datetime.now().isoformat(),
                    "timeframe": timeframe
                }
                
                # Store in historical data
                self.historical_trends[industry].extend(trends)
                
                # Limit historical data
                if len(self.historical_trends[industry]) > 50:
                    self.historical_trends[industry] = self.historical_trends[industry][-50:]
                
                industry_trends[industry] = trends
                
                logger.info(f"Found {len(trends)} trends for {industry}")
                
            except Exception as e:
                logger.error(f"Error monitoring trends for {industry}: {e}")
                industry_trends[industry] = []
        
        return industry_trends
    
    def track_competitor_activities(self, companies: List[str], 
                                  industries: List[str] = None) -> Dict[str, List[CompetitorActivity]]:
        """
        Track activities of competitor companies.
        
        Args:
            companies: List of competitor company names
            industries: Optional industries for context
            
        Returns:
            Dict mapping companies to their activities
        """
        logger.info(f"Tracking competitor activities for: {companies}")
        
        competitor_activities = {}
        
        for company in companies:
            try:
                # Get competitive intelligence
                competitive_data = self.grok_service.get_competitive_intelligence(company)
                
                # Convert to CompetitorActivity objects
                activities = []
                
                # Extract activities from competitive data
                competitors = competitive_data.get("competitors", [])
                for competitor_info in competitors:
                    activity = CompetitorActivity(
                        competitor=competitor_info.get("name", "Unknown Competitor"),
                        activity_type="market_position",
                        description=f"Market position: {competitor_info.get('strength', 'Unknown')}",
                        impact_level="medium",
                        timestamp=datetime.now().isoformat(),
                        source="grok_api"
                    )
                    activities.append(activity)
                
                # Add market gaps as opportunities
                market_gaps = competitive_data.get("market_gaps", [])
                for gap in market_gaps:
                    activity = CompetitorActivity(
                        competitor=company,
                        activity_type="market_gap",
                        description=f"Market gap identified: {gap}",
                        impact_level="high",
                        timestamp=datetime.now().isoformat(),
                        source="grok_api"
                    )
                    activities.append(activity)
                
                # Cache activities
                self.competitor_cache[company] = {
                    "activities": activities,
                    "last_updated": datetime.now().isoformat()
                }
                
                # Store in historical data
                self.historical_competitors[company].extend(activities)
                
                # Limit historical data
                if len(self.historical_competitors[company]) > 30:
                    self.historical_competitors[company] = self.historical_competitors[company][-30:]
                
                competitor_activities[company] = activities
                
                logger.info(f"Found {len(activities)} activities for {company}")
                
            except Exception as e:
                logger.error(f"Error tracking competitor {company}: {e}")
                competitor_activities[company] = []
        
        return competitor_activities
    
    def get_real_time_market_trends(self, industry: str, depth: int = 3) -> Dict[str, Any]:
        """
        Fetches real-time market trends for a given industry.
        
        Args:
            industry: The industry to monitor (e.g., "SaaS", "Fintech").
            depth: How many top trends to retrieve.
            
        Returns:
            A dictionary containing current trends and market outlook.
        """
        cache_key = f"trends_{industry}_{depth}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        logger.info(f"Fetching real-time market trends for industry: {industry}")
        try:
            grok_response = self.grok_service.get_industry_trends(industry, time_frame="real-time")
            
            trends = grok_response.get("trends", [])[:depth]
            market_outlook = grok_response.get("market_outlook", "stable")
            
            result = {
                "industry": industry,
                "trends": trends,
                "market_outlook": market_outlook,
                "timestamp": datetime.now().isoformat()
            }
            
            self._set_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching market trends: {e}")
            return {
                "industry": industry,
                "trends": [],
                "market_outlook": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def detect_market_opportunities(self, industry: str) -> List[MarketOpportunity]:
        """
        Detect market opportunities based on industry.
        
        Args:
            industry: Industry to detect opportunities for
            
        Returns:
            List of detected market opportunities
        """
        logger.info(f"Detecting market opportunities for industry: {industry}")
        
        opportunities = []
        keywords = ["innovation", "growth"]
        
        try:
            # Get market sentiment for opportunity detection
            sentiment_data = self.grok_service.get_market_sentiment(industry, keywords)
            
            # Get industry trends
            trends_data = self.grok_service.get_industry_trends(industry)
            
            # Generate opportunities based on trends and sentiment
            trend_opportunities = self._generate_opportunities_from_trends(
                industry, trends_data, sentiment_data
            )
            
            opportunities.extend(trend_opportunities)
            
            # Cache opportunities
            cache_key = f"{industry}_{'_'.join(keywords)}"
            self.opportunity_cache[cache_key] = {
                "opportunities": trend_opportunities,
                "last_updated": datetime.now().isoformat(),
                "industry": industry
            }
            
            # Store in historical data
            self.historical_opportunities[industry].extend(trend_opportunities)
            
            # Limit historical data
            if len(self.historical_opportunities[industry]) > 20:
                self.historical_opportunities[industry] = self.historical_opportunities[industry][-20:]
            
        except Exception as e:
            logger.error(f"Error detecting opportunities for {industry}: {e}")
        
        return opportunities
    
    def _generate_opportunities_from_trends(self, industry: str, trends_data: Dict[str, Any], 
                                          sentiment_data: Dict[str, Any]) -> List[MarketOpportunity]:
        """Generate opportunities from trend and sentiment data"""
        opportunities = []
        
        trends = trends_data.get("trends", [])
        sentiment = sentiment_data.get("sentiment", "neutral")
        confidence = sentiment_data.get("confidence", 0.5)
        
        for trend in trends[:3]:  # Top 3 trends
            opportunity = MarketOpportunity(
                title=f"{trend['name']} Opportunity in {industry}",
                description=f"Capitalize on the {trend['name']} trend in {industry}",
                industry=industry,
                opportunity_type="trend_based",
                confidence=confidence,
                potential_value="High" if trend.get("impact") == "high" else "Medium",
                timeline=trend.get("timeline", "6-12 months"),
                requirements=[
                    f"Understanding of {trend['name']}",
                    f"Industry expertise in {industry}",
                    "Market research capabilities"
                ]
            )
            opportunities.append(opportunity)
        
        # Add sentiment-based opportunities
        if sentiment == "positive" and confidence > 0.7:
            opportunity = MarketOpportunity(
                title=f"Market Growth Opportunity in {industry}",
                description=f"Positive market sentiment indicates growth opportunities in {industry}",
                industry=industry,
                opportunity_type="sentiment_based",
                confidence=confidence,
                potential_value="High",
                timeline="3-6 months",
                requirements=[
                    f"Market entry strategy for {industry}",
                    "Competitive analysis",
                    "Growth planning"
                ]
            )
            opportunities.append(opportunity)
        
        return opportunities
    
    def get_market_alerts(self, industry: str) -> List[MarketAlert]:
        """
        Get market alerts for a specific industry.
        """
        logger.info(f"Getting market alerts for industry: {industry}")
        
        # Generate sample alerts based on industry
        alerts = []
        
        if industry.lower() == "saas":
            alerts = [
                MarketAlert(
                    alert_id=f"saas_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="trend",
                    title="AI Integration Trend",
                    description="Growing demand for AI-powered features in SaaS platforms",
                    severity="medium",
                    industry="SaaS",
                    timestamp=datetime.now().isoformat(),
                    source="market_monitoring",
                    actionable=True,
                    recommendations=["Consider adding AI features to your product roadmap"]
                )
            ]
        elif industry.lower() == "fintech":
            alerts = [
                MarketAlert(
                    alert_id=f"fintech_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="regulation",
                    title="New Compliance Requirements",
                    description="Updated regulations affecting fintech companies",
                    severity="high",
                    industry="Fintech",
                    timestamp=datetime.now().isoformat(),
                    source="market_monitoring",
                    actionable=True,
                    recommendations=["Review compliance procedures", "Update security measures"]
                )
            ]
        else:
            alerts = [
                MarketAlert(
                    alert_id=f"general_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="general",
                    title="Market Update",
                    description=f"General market update for {industry} industry",
                    severity="low",
                    industry=industry,
                    timestamp=datetime.now().isoformat(),
                    source="market_monitoring",
                    actionable=False,
                    recommendations=[]
                )
            ]
        
        return alerts

    def track_competitor_activity(self, industry: str) -> List[CompetitorActivity]:
        """
        Track competitor activities for a specific industry.
        
        Args:
            industry: Industry to track competitors for
            
        Returns:
            List of competitor activities
        """
        logger.info(f"Tracking competitor activity for industry: {industry}")
        
        activities = []
        
        try:
            # Get competitive intelligence from Grok
            competitive_data = self.grok_service.get_competitive_intelligence(industry)
            
            # Process competitor data
            competitors = competitive_data.get("competitors", [])
            for competitor in competitors:
                activity = CompetitorActivity(
                    competitor=competitor.get("name", "Unknown Competitor"),
                    activity_type="market_position",
                    description=f"Market position: {competitor.get('strength', 'Unknown')}",
                    impact_level="medium",
                    timestamp=datetime.now().isoformat(),
                    source="grok_api"
                )
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error tracking competitor activity: {e}")
            return []

    def generate_market_alerts(self, user_preferences: Dict[str, Any]) -> List[MarketAlert]:
        """
        Generate market alerts based on user preferences and monitoring data.
        
        Args:
            user_preferences: User's alert preferences and thresholds
            
        Returns:
            List of generated market alerts
        """
        logger.info("Generating market alerts based on user preferences")
        
        alerts = []
        
        # Check for trend alerts
        if user_preferences.get("trend_alerts", True):
            trend_alerts = self._generate_trend_alerts(user_preferences)
            alerts.extend(trend_alerts)
        
        # Check for competitor alerts
        if user_preferences.get("competitor_alerts", True):
            competitor_alerts = self._generate_competitor_alerts(user_preferences)
            alerts.extend(competitor_alerts)
        
        # Check for opportunity alerts
        if user_preferences.get("opportunity_alerts", True):
            opportunity_alerts = self._generate_opportunity_alerts(user_preferences)
            alerts.extend(opportunity_alerts)
        
        # Sort alerts by severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        alerts.sort(key=lambda x: severity_order.get(x.severity, 0), reverse=True)
        
        return alerts
    
    def _generate_trend_alerts(self, preferences: Dict[str, Any]) -> List[MarketAlert]:
        """Generate alerts based on trend analysis"""
        alerts = []
        threshold = preferences.get("critical_threshold", 0.8)
        
        for industry, trends in self.trend_cache.items():
            for trend in trends.get("trends", []):
                if trend.confidence >= threshold and trend.impact == "high":
                    alert = MarketAlert(
                        alert_type="trend",
                        severity="critical" if trend.confidence >= 0.9 else "high",
                        title=f"High-Impact Trend: {trend.name}",
                        description=f"High-confidence trend detected in {industry}: {trend.description}",
                        affected_industries=[industry],
                        timestamp=datetime.now().isoformat(),
                        action_required=True,
                        recommendations=[
                            f"Analyze impact of {trend.name} on your business",
                            f"Consider strategic adjustments for {industry}",
                            "Monitor trend development closely"
                        ]
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _generate_competitor_alerts(self, preferences: Dict[str, Any]) -> List[MarketAlert]:
        """Generate alerts based on competitor activities"""
        alerts = []
        
        for company, activities in self.competitor_cache.items():
            for activity in activities.get("activities", []):
                if activity.impact_level == "high":
                    alert = MarketAlert(
                        alert_type="competitor",
                        severity="high",
                        title=f"Competitor Activity: {activity.competitor}",
                        description=f"High-impact activity detected: {activity.description}",
                        affected_industries=["Multiple"],
                        timestamp=datetime.now().isoformat(),
                        action_required=True,
                        recommendations=[
                            f"Analyze competitive response to {activity.competitor}",
                            "Review market positioning strategy",
                            "Consider competitive countermeasures"
                        ]
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _generate_opportunity_alerts(self, preferences: Dict[str, Any]) -> List[MarketAlert]:
        """Generate alerts based on market opportunities"""
        alerts = []
        threshold = preferences.get("opportunity_threshold", 0.7)
        
        for industry, opportunities in self.historical_opportunities.items():
            recent_opportunities = [
                opp for opp in opportunities 
                if datetime.fromisoformat(opp.timestamp) > datetime.now() - timedelta(days=7)
            ]
            
            for opportunity in recent_opportunities:
                if opportunity.confidence >= threshold:
                    alert = MarketAlert(
                        alert_type="opportunity",
                        severity="medium",
                        title=f"Market Opportunity: {opportunity.title}",
                        description=f"High-confidence opportunity detected: {opportunity.description}",
                        affected_industries=[opportunity.industry],
                        timestamp=datetime.now().isoformat(),
                        action_required=False,
                        recommendations=[
                            f"Evaluate {opportunity.title}",
                            f"Assess requirements: {', '.join(opportunity.requirements)}",
                            f"Timeline: {opportunity.timeline}"
                        ]
                    )
                    alerts.append(alert)
        
        return alerts
    
    def start_continuous_monitoring(self, industries: List[str], companies: List[str], 
                                  user_preferences: Dict[str, Any]) -> str:
        """
        Start continuous monitoring for specified industries and companies.
        
        Args:
            industries: Industries to monitor
            companies: Competitor companies to track
            user_preferences: User's monitoring preferences
            
        Returns:
            Monitoring session ID
        """
        session_id = f"monitor_{int(time.time())}"
        
        logger.info(f"Starting continuous monitoring session: {session_id}")
        
        # Store monitoring configuration
        self.active_monitors[session_id] = {
            "industries": industries,
            "companies": companies,
            "preferences": user_preferences,
            "started_at": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Start background monitoring task
        asyncio.create_task(self._continuous_monitoring_loop(session_id))
        
        return session_id
    
    async def _continuous_monitoring_loop(self, session_id: str):
        """Background loop for continuous monitoring"""
        while session_id in self.active_monitors:
            try:
                monitor_config = self.active_monitors[session_id]
                
                # Check trends
                if monitor_config["preferences"].get("trend_alerts", True):
                    await self._check_trends_async(monitor_config["industries"])
                
                # Check competitors
                if monitor_config["preferences"].get("competitor_alerts", True):
                    await self._check_competitors_async(monitor_config["companies"])
                
                # Update last check time
                self.active_monitors[session_id]["last_check"] = datetime.now().isoformat()
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_config["trend_check_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop for {session_id}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _check_trends_async(self, industries: List[str]):
        """Asynchronously check for new trends"""
        try:
            for industry in industries:
                trends_data = self.grok_service.get_industry_trends(industry)
                # Process trends asynchronously
                await asyncio.sleep(0.1)  # Small delay to avoid rate limiting
        except Exception as e:
            logger.error(f"Error checking trends: {e}")
    
    async def _check_competitors_async(self, companies: List[str]):
        """Asynchronously check competitor activities"""
        try:
            for company in companies:
                competitive_data = self.grok_service.get_competitive_intelligence(company)
                # Process competitor data asynchronously
                await asyncio.sleep(0.1)  # Small delay to avoid rate limiting
        except Exception as e:
            logger.error(f"Error checking competitors: {e}")
    
    def stop_monitoring(self, session_id: str) -> bool:
        """
        Stop continuous monitoring session.
        
        Args:
            session_id: Monitoring session ID
            
        Returns:
            True if stopped successfully
        """
        if session_id in self.active_monitors:
            del self.active_monitors[session_id]
            logger.info(f"Stopped monitoring session: {session_id}")
            return True
        return False
    
    def get_monitoring_status(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get status of monitoring sessions.
        
        Args:
            session_id: Specific session ID, or None for all sessions
            
        Returns:
            Monitoring status information
        """
        if session_id:
            return self.active_monitors.get(session_id, {})
        
        return {
            "active_sessions": len(self.active_monitors),
            "sessions": list(self.active_monitors.keys()),
            "cache_status": {
                "trends_cached": len(self.trend_cache),
                "competitors_cached": len(self.competitor_cache),
                "opportunities_cached": len(self.opportunity_cache)
            },
            "historical_data": {
                "trends": sum(len(trends) for trends in self.historical_trends.values()),
                "competitors": sum(len(activities) for activities in self.historical_competitors.values()),
                "opportunities": sum(len(opps) for opps in self.historical_opportunities.values())
            }
        }
    
    def get_market_summary(self, industries: List[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive market summary for specified industries.
        
        Args:
            industries: Industries to summarize, or None for all
            
        Returns:
            Market summary with trends, opportunities, and alerts
        """
        logger.info(f"Generating market summary for industries: {industries}")
        
        if not industries:
            industries = list(self.trend_cache.keys())
        
        summary = {
            "summary_timestamp": datetime.now().isoformat(),
            "industries_analyzed": industries,
            "trends": {},
            "opportunities": {},
            "alerts": [],
            "market_sentiment": {}
        }
        
        for industry in industries:
            # Get trends
            if industry in self.trend_cache:
                summary["trends"][industry] = [
                    {
                        "name": trend.name,
                        "impact": trend.impact,
                        "timeline": trend.timeline,
                        "confidence": trend.confidence
                    }
                    for trend in self.trend_cache[industry]["trends"]
                ]
            
            # Get opportunities
            if industry in self.historical_opportunities:
                summary["opportunities"][industry] = [
                    {
                        "title": opp.title,
                        "type": opp.opportunity_type,
                        "confidence": opp.confidence,
                        "timeline": opp.timeline
                    }
                    for opp in self.historical_opportunities[industry][-5:]  # Last 5
                ]
            
            # Get market sentiment
            try:
                sentiment_data = self.grok_service.get_market_sentiment(industry, ["growth", "innovation"])
                summary["market_sentiment"][industry] = {
                    "sentiment": sentiment_data.get("sentiment", "neutral"),
                    "confidence": sentiment_data.get("confidence", 0.5)
                }
            except Exception as e:
                logger.warning(f"Could not get sentiment for {industry}: {e}")
                summary["market_sentiment"][industry] = {
                    "sentiment": "neutral",
                    "confidence": 0.5
                }
        
        # Generate alerts
        summary["alerts"] = self.generate_market_alerts(self.alert_preferences)
        
        return summary
    
    def export_monitoring_data(self, session_id: str = None, 
                              format: str = "json") -> Dict[str, Any]:
        """
        Export monitoring data for analysis.
        
        Args:
            session_id: Specific session to export, or None for all
            format: Export format ("json", "csv")
            
        Returns:
            Exported monitoring data
        """
        logger.info(f"Exporting monitoring data for session: {session_id}")
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "format": format,
            "monitoring_config": self.monitoring_config,
            "alert_preferences": self.alert_preferences
        }
        
        if session_id and session_id in self.active_monitors:
            export_data["session_data"] = self.active_monitors[session_id]
        else:
            export_data["all_sessions"] = self.active_monitors
        
        export_data["trend_cache"] = self.trend_cache
        export_data["competitor_cache"] = self.competitor_cache
        export_data["opportunity_cache"] = self.opportunity_cache
        
        export_data["historical_data"] = {
            "trends": dict(self.historical_trends),
            "competitors": dict(self.historical_competitors),
            "opportunities": dict(self.historical_opportunities)
        }
        
        return export_data
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return {
            "service_name": "Market Monitoring Service",
            "version": "1.0",
            "active_monitors": len(self.active_monitors),
            "cache_status": {
                "trends": len(self.trend_cache),
                "competitors": len(self.competitor_cache),
                "opportunities": len(self.opportunity_cache)
            },
            "historical_data_counts": {
                "trends": sum(len(trends) for trends in self.historical_trends.values()),
                "competitors": sum(len(activities) for activities in self.historical_competitors.values()),
                "opportunities": sum(len(opps) for opps in self.historical_opportunities.values())
            },
            "monitoring_config": self.monitoring_config,
            "last_updated": datetime.now().isoformat()
        }
