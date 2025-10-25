#!/usr/bin/env python3
"""
Phase 3 Comprehensive Test Suite
Tests all Phase 3 adaptive AI features including:
- Adaptive AI Agent framework
- Knowledge fusion service
- LLM selector service
- Market monitoring service
- Predictive analytics service
- Grok integration
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_adaptive_ai_agent():
    """Test the Adaptive AI Agent framework"""
    logger.info("🧠 Testing Adaptive AI Agent...")
    
    try:
        from agents.adaptive_ai_agent import AdaptiveAIAgent, KnowledgeLevel, AdaptationStrategy
        
        agent = AdaptiveAIAgent()
        
        # Test knowledge assessment
        tenant_id = "test_tenant"
        user_id = "test_user"
        sample_prompt = "Generate leads for our SaaS product targeting CTOs in mid-market companies"
        
        assessment = agent.assess_knowledge_level(tenant_id, user_id, sample_prompt)
        logger.info(f"✅ Knowledge assessment completed: {assessment.level.value}")
        
        # Test strategy selection
        strategy_plan = agent.select_adaptation_strategy(assessment.level, "campaign_orchestration")
        logger.info(f"✅ Strategy selected: {strategy_plan.strategy.value}")
        
        # Test execution with strategy
        execution_result = agent.execute_with_strategy(
            strategy_plan.strategy,
            sample_prompt,
            {"task_type": "campaign_orchestration", "industry": "SaaS"},
            tenant_id,
            user_id
        )
        logger.info(f"✅ Strategy execution completed with confidence: {execution_result.get('strategy_metadata', {}).get('fused_overall_score', 0.0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive AI Agent test failed: {e}")
        return False

def test_knowledge_fusion_service():
    """Test the Knowledge Fusion Service"""
    logger.info("🔗 Testing Knowledge Fusion Service...")
    
    try:
        from services.knowledge_fusion_service import KnowledgeFusionService
        
        fusion_service = KnowledgeFusionService()
        
        # Sample knowledge sources
        document_knowledge = {
            "company_info": {"company_name": "TestCorp", "industry": "SaaS"},
            "products": [{"name": "TestProduct", "description": "A test product"}],
            "value_propositions": ["Efficiency", "Cost savings"]
        }
        
        prompt_knowledge = {
            "company_info": {"company_name": "TestCorp", "industry": "Technology"},
            "target_audience": {"roles": ["CTO", "VP Engineering"]},
            "key_messages": ["Innovation", "Scalability"]
        }
        
        market_knowledge = {
            "market_sentiment": {"sentiment": "bullish", "confidence": 0.8},
            "industry_trends": {"trends": ["AI adoption", "Cloud migration"]},
            "competitive_intelligence": {"competitors": ["Competitor A", "Competitor B"]}
        }
        
        # Test knowledge fusion
        fused_knowledge = fusion_service.fuse_knowledge(
            document_knowledge,
            prompt_knowledge,
            market_knowledge
        )
        
        logger.info(f"✅ Knowledge fusion completed. Fused keys: {list(fused_knowledge.keys())}")
        
        # Test conflict resolution
        conflict_resolution = fusion_service.resolve_conflicts(
            "company_info",
            [{"source": "document", "value": document_knowledge["company_info"], "confidence": 0.9}, 
             {"source": "prompt", "value": prompt_knowledge["company_info"], "confidence": 0.7}],
            [{"field": "company_info", "sources": ["document", "prompt"], "values": [document_knowledge["company_info"], prompt_knowledge["company_info"]]}]
        )
        logger.info(f"✅ Conflict resolution completed. Resolved conflicts: {len(conflict_resolution) if isinstance(conflict_resolution, list) else 1}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Knowledge Fusion Service test failed: {e}")
        return False

def test_llm_selector_service():
    """Test the LLM Selector Service"""
    logger.info("🤖 Testing LLM Selector Service...")
    
    try:
        from services.llm_selector_service import LLMSelectorService, TaskComplexity
        
        selector = LLMSelectorService()
        
        # Test model recommendation for different tasks
        tasks = [
            ("extraction", 1000, {"quality_priority": True}),
            ("personalization", 500, {"cost_priority": True}),
            ("market_analysis", 2000, {"speed_priority": True}),
            ("quick_chat", 100, {})
        ]
        
        for task_type, prompt_length, preferences in tasks:
            recommendation = selector.recommend_model_for_task(task_type, prompt_length, preferences)
            logger.info(f"✅ Task '{task_type}': {recommendation['recommended_model']} ({recommendation['reasoning']})")
        
        # Test model details
        model_details = selector.get_model_details("gpt-4")
        if model_details:
            logger.info(f"✅ Model details retrieved for GPT-4: {model_details.max_tokens} max tokens")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM Selector Service test failed: {e}")
        return False

def test_grok_service():
    """Test the Grok Service integration"""
    logger.info("📊 Testing Grok Service...")
    
    try:
        from integrations.grok_service import GrokService
        
        grok_service = GrokService()
        
        # Test market sentiment
        sentiment = grok_service.get_market_sentiment("SaaS", ["growth", "innovation"])
        logger.info(f"✅ Market sentiment: {sentiment.get('sentiment', 'unknown')}")
        
        # Test industry trends
        trends = grok_service.get_industry_trends("SaaS", "current")
        logger.info(f"✅ Industry trends: {len(trends.get('trends', []))} trends found")
        
        # Test competitive intelligence
        competitive = grok_service.get_competitive_intelligence("CRM software", ["pricing", "features"])
        logger.info(f"✅ Competitive intelligence: {len(competitive.get('competitors', []))} competitors found")
        
        # Test lead enrichment
        lead_data = {"email": "test@example.com", "company": "TestCorp"}
        enriched = grok_service.enrich_lead_data(lead_data)
        logger.info(f"✅ Lead enrichment completed for {lead_data['email']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Grok Service test failed: {e}")
        return False

def test_market_monitoring_service():
    """Test the Market Monitoring Service"""
    logger.info("📈 Testing Market Monitoring Service...")
    
    try:
        from services.market_monitoring_service import MarketMonitoringService
        
        monitoring_service = MarketMonitoringService()
        
        # Test real-time market trends
        trends = monitoring_service.get_real_time_market_trends("SaaS", depth=5)
        logger.info(f"✅ Market trends: {len(trends.get('trends', []))} trends retrieved")
        
        # Test market opportunities
        opportunities = monitoring_service.detect_market_opportunities("SaaS")
        logger.info(f"✅ Market opportunities: {len(opportunities)} opportunities detected")
        
        # Test market alerts
        alerts = monitoring_service.get_market_alerts("SaaS")
        logger.info(f"✅ Market alerts: {len(alerts)} alerts generated")
        
        # Test competitor tracking
        competitor_activity = monitoring_service.track_competitor_activity("Salesforce")
        logger.info(f"✅ Competitor tracking: {len(competitor_activity)} activities tracked")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Market Monitoring Service test failed: {e}")
        return False

def test_predictive_analytics_service():
    """Test the Predictive Analytics Service"""
    logger.info("🔮 Testing Predictive Analytics Service...")
    
    try:
        from services.predictive_analytics_service import PredictiveAnalyticsService
        
        analytics_service = PredictiveAnalyticsService()
        
        # Sample campaign and lead data
        campaign_data = {
            "campaign_id": "test_campaign_001",
            "name": "Test Campaign",
            "industry": "SaaS",
            "target_audience": {
                "roles": ["CTO"],
                "size": "medium",
                "quality_score": 0.8,
                "industry_match": 0.9,
                "pain_point_match": 0.7
            },
            "message_type": "cold_email",
            "content": {
                "quality_score": 0.8,
                "personalization_level": 0.7,
                "value_proposition_clarity": 0.9
            }
        }
        
        lead_data = [
            {"name": "John Doe", "title": "CTO", "company": "TestCorp", "industry": "SaaS"},
            {"name": "Jane Smith", "title": "VP Engineering", "company": "TestInc", "industry": "Technology"}
        ]
        
        # Test campaign performance prediction
        prediction = analytics_service.predict_campaign_performance(campaign_data, lead_data)
        logger.info(f"✅ Campaign prediction: {prediction.predicted_response_rate:.2%} response rate")
        
        # Test targeting optimization
        historical_data = {
            "audience_metrics": {
                "CTOs": {"email_open_rate": 0.3, "email_click_rate": 0.08, "response_rate": 0.03, "conversion_rate": 0.02},
                "VP Engineering": {"email_open_rate": 0.25, "email_click_rate": 0.06, "response_rate": 0.025, "conversion_rate": 0.015}
            }
        }
        current_targets = ["CTOs", "VP Engineering"]
        optimization = analytics_service.optimize_targeting(historical_data, current_targets)
        logger.info(f"✅ Targeting optimization: {len(optimization)} optimizations found")
        
        # Test timing recommendation
        market_data = {
            "market_sentiment": "positive",
            "positive_trends": 2,
            "market_outlook": "growing"
        }
        historical_timing = {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["10:00 AM", "2:00 PM", "3:00 PM"],
            "performance_by_day": {
                "Monday": 0.8, "Tuesday": 1.2, "Wednesday": 1.1, "Thursday": 1.0, "Friday": 0.9
            }
        }
        timing = analytics_service.recommend_best_timing(market_data, historical_timing)
        logger.info(f"✅ Timing recommendation: {timing.optimal_time} on {timing.optimal_day}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Predictive Analytics Service test failed: {e}")
        return False

def test_knowledge_quality_service():
    """Test the Knowledge Quality Service"""
    logger.info("📊 Testing Knowledge Quality Service...")
    
    try:
        from services.knowledge_quality_service import KnowledgeQualityService
        
        quality_service = KnowledgeQualityService()
        
        # Sample knowledge to assess
        sample_knowledge = {
            "company_info": {
                "company_name": "TestCorp",
                "industry": "SaaS",
                "company_size": "50-200 employees"
            },
            "products": [
                {"name": "TestProduct", "description": "A comprehensive SaaS solution"}
            ],
            "value_propositions": [
                "Increases efficiency by 50%",
                "Reduces operational costs by 30%"
            ],
            "target_audience": {
                "roles": ["CTO", "VP Engineering"],
                "industries": ["SaaS", "Technology"],
                "pain_points": ["Manual processes", "Scaling challenges"]
            },
            "competitive_advantages": [
                "AI-powered automation",
                "Enterprise-grade security"
            ]
        }
        
        # Test quality assessment
        quality_report = quality_service.assess_knowledge_quality(
            sample_knowledge,
            document_type="company_info",
            source_type="document"
        )
        
        logger.info(f"✅ Quality assessment: {quality_report['overall_score']:.2f} overall score")
        logger.info(f"✅ Quality rating: {quality_report['quality_rating']}")
        logger.info(f"✅ Recommendations: {len(quality_report['recommendations'])} recommendations")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Knowledge Quality Service test failed: {e}")
        return False

def test_adaptive_prompt_processor():
    """Test the Adaptive Prompt Processor"""
    logger.info("📝 Testing Adaptive Prompt Processor...")
    
    try:
        from agents.adaptive_prompt_processor import AdaptivePromptProcessor
        
        processor = AdaptivePromptProcessor()
        
        # Test detailed prompt analysis
        detailed_prompt = """
        We are TechCorp, a SaaS company specializing in AI-powered CRM solutions. 
        We target CTOs and VP Engineering at mid-market companies (50-500 employees) 
        in the technology and fintech industries. Our main product is SmartCRM, 
        which helps companies increase sales efficiency by 40% and reduce customer 
        acquisition costs by 25%. We want to run a campaign to generate qualified 
        leads for our product demo. Our key value propositions are AI automation, 
        seamless integration, and enterprise security. We prefer a professional 
        yet innovative tone in our messaging.
        """
        
        analysis = processor.analyze_detailed_prompt(detailed_prompt)
        logger.info(f"✅ Prompt analysis completed: {analysis['confidence_scores'].get('overall', 0.0):.2f} confidence score")
        logger.info(f"✅ Business context extracted: {analysis['business_context'].get('company_name', 'Unknown')}")
        logger.info(f"✅ Extraction method: {analysis['extraction_method']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive Prompt Processor test failed: {e}")
        return False

def test_integrated_workflow():
    """Test the integrated Phase 3 workflow"""
    logger.info("🔄 Testing Integrated Phase 3 Workflow...")
    
    try:
        from agents.smart_campaign_orchestrator import SmartCampaignOrchestrator
        
        orchestrator = SmartCampaignOrchestrator()
        
        # Test adaptive campaign execution
        prompt = "Generate leads for our AI-powered CRM targeting CTOs in SaaS companies with 50-200 employees"
        tenant_id = "test_tenant"
        user_id = "test_user"
        
        result = orchestrator.execute_adaptive_campaign(prompt, tenant_id, user_id)
        
        if result["success"]:
            logger.info(f"✅ Adaptive campaign executed successfully")
            logger.info(f"✅ Strategy used: {result.get('strategy_used', 'unknown')}")
            logger.info(f"✅ Knowledge level: {result.get('knowledge_level', 'unknown')}")
            logger.info(f"✅ Confidence score: {result.get('confidence_score', 0.0):.2f}")
            
            if "market_intelligence" in result:
                logger.info(f"✅ Market intelligence applied")
            
            if "adaptive_metadata" in result:
                logger.info(f"✅ Adaptive metadata generated")
        else:
            logger.error(f"❌ Adaptive campaign failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated workflow test failed: {e}")
        return False

def main():
    """Run all Phase 3 tests"""
    logger.info("🚀 Starting Phase 3 Comprehensive Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Adaptive AI Agent", test_adaptive_ai_agent),
        ("Knowledge Fusion Service", test_knowledge_fusion_service),
        ("LLM Selector Service", test_llm_selector_service),
        ("Grok Service", test_grok_service),
        ("Market Monitoring Service", test_market_monitoring_service),
        ("Predictive Analytics Service", test_predictive_analytics_service),
        ("Knowledge Quality Service", test_knowledge_quality_service),
        ("Adaptive Prompt Processor", test_adaptive_prompt_processor),
        ("Integrated Workflow", test_integrated_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Phase 3 Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All Phase 3 tests passed! The adaptive AI system is ready.")
        return True
    else:
        logger.error(f"⚠️ {total-passed} tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
