#!/usr/bin/env python3
"""
Test Smart Campaign Suggestions Implementation
Tests the complete flow from document analysis to suggestion generation and learning.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_campaign_intelligence_service():
    """Test the Campaign Intelligence Service"""
    logger.info("🧠 Testing Campaign Intelligence Service...")
    
    try:
        from services.campaign_intelligence_service import CampaignIntelligenceService
        
        service = CampaignIntelligenceService()
        
        # Test with mock knowledge data
        mock_knowledge = {
            'company_info': {
                'company_name': 'Avius LLC',
                'industry': 'Technology',
                'sales_approach': 'Consultative selling focused on AI solutions'
            },
            'products': [
                {'name': 'AI Agent Platform'},
                {'name': 'Smart Automation Tools'}
            ],
            'target_audience': {
                'buyer_personas': ['CTOs', 'VPs of Engineering'],
                'company_sizes': ['50-200', '200-500'],
                'industries': ['SaaS', 'Technology'],
                'pain_points': ['Manual processes', 'Inefficiency']
            },
            'competitive_advantages': ['AI expertise', 'Scalable solutions'],
            'value_propositions': ['Reduce manual work', 'Increase efficiency'],
            'source_count': 3
        }
        
        # Test suggestion generation
        suggestions = service.generate_prompt_suggestions(mock_knowledge, count=3)
        
        assert len(suggestions) == 3, f"Expected 3 suggestions, got {len(suggestions)}"
        
        for suggestion in suggestions:
            assert 'title' in suggestion, "Suggestion missing title"
            assert 'prompt' in suggestion, "Suggestion missing prompt"
            assert 'confidence' in suggestion, "Suggestion missing confidence"
            assert 'category' in suggestion, "Suggestion missing category"
            assert 0 <= suggestion['confidence'] <= 1, f"Invalid confidence score: {suggestion['confidence']}"
        
        logger.info("✅ Campaign Intelligence Service test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Campaign Intelligence Service test failed: {e}")
        return False

def test_campaign_learning_service():
    """Test the Campaign Learning Service"""
    logger.info("📊 Testing Campaign Learning Service...")
    
    try:
        from services.campaign_learning_service import CampaignLearningService
        
        service = CampaignLearningService()
        
        # Test success metrics calculation
        mock_results = {
            'lead_count': 15,
            'high_quality_leads': 8,
            'campaign_success': True,
            'responses': 3,
            'opens': 12,
            'clicks': 5,
            'replies': 2
        }
        
        metrics = service.calculate_success_metrics(mock_results)
        
        assert 'overall_score' in metrics, "Missing overall_score"
        assert 'quality_score' in metrics, "Missing quality_score"
        assert 'response_rate' in metrics, "Missing response_rate"
        assert 'engagement_score' in metrics, "Missing engagement_score"
        assert 0 <= metrics['overall_score'] <= 1, f"Invalid overall score: {metrics['overall_score']}"
        
        # Test pattern analysis
        mock_executions = [
            {
                'original_prompt': 'Find me CTOs at SaaS companies',
                'quality_score': 0.8,
                'executed_at': datetime.now().isoformat()
            },
            {
                'original_prompt': 'Find me VPs at tech companies',
                'quality_score': 0.9,
                'executed_at': datetime.now().isoformat()
            }
        ]
        
        patterns = service._analyze_patterns(mock_executions)
        assert isinstance(patterns, list), "Patterns should be a list"
        
        logger.info("✅ Campaign Learning Service test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Campaign Learning Service test failed: {e}")
        return False

def test_supabase_methods():
    """Test the new Supabase methods"""
    logger.info("🗄️ Testing Supabase Methods...")
    
    try:
        from services.supabase_service import SupabaseService
        
        service = SupabaseService()
        
        # Test that methods exist
        assert hasattr(service, 'save_campaign_suggestion'), "Missing save_campaign_suggestion method"
        assert hasattr(service, 'get_campaign_suggestions'), "Missing get_campaign_suggestions method"
        assert hasattr(service, 'save_campaign_execution'), "Missing save_campaign_execution method"
        assert hasattr(service, 'get_campaign_execution_history'), "Missing get_campaign_execution_history method"
        assert hasattr(service, 'update_suggestion_metrics'), "Missing update_suggestion_metrics method"
        assert hasattr(service, 'save_prompt_pattern'), "Missing save_prompt_pattern method"
        assert hasattr(service, 'get_successful_patterns'), "Missing get_successful_patterns method"
        
        logger.info("✅ Supabase Methods test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase Methods test failed: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints exist and are properly structured"""
    logger.info("🌐 Testing API Endpoints...")
    
    try:
        # Check if backend file has the new endpoints
        with open('backend/main_supabase.py', 'r') as f:
            backend_content = f.read()
        
        required_endpoints = [
            '/campaign-intelligence/suggestions',
            '/campaign-intelligence/generate',
            '/campaign-intelligence/record-execution',
            '/campaign-intelligence/insights'
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in backend_content, f"Missing endpoint: {endpoint}"
        
        # Check if frontend API routes exist
        api_routes = [
            'frontend/pages/api/campaign-intelligence/suggestions.js',
            'frontend/pages/api/campaign-intelligence/generate.js',
            'frontend/pages/api/campaign-intelligence/record-execution.js'
        ]
        
        for route in api_routes:
            assert os.path.exists(route), f"Missing API route: {route}"
        
        logger.info("✅ API Endpoints test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API Endpoints test failed: {e}")
        return False

def test_frontend_integration():
    """Test the frontend integration"""
    logger.info("🎨 Testing Frontend Integration...")
    
    try:
        # Check if SmartCampaign component has suggestion features
        with open('frontend/components/SmartCampaign.js', 'r') as f:
            smart_campaign_content = f.read()
        
        required_features = [
            'suggestedPrompts',
            'isLoadingSuggestions',
            'selectedSuggestion',
            'getCampaignSuggestions',
            'handlePromptSuggestion',
            'recordCampaignExecution',
            'Smart Suggestions'
        ]
        
        for feature in required_features:
            assert feature in smart_campaign_content, f"Missing feature: {feature}"
        
        # Check if Knowledge Bank has regeneration trigger
        with open('frontend/pages/knowledge-bank.js', 'r') as f:
            knowledge_bank_content = f.read()
        
        assert 'regenerateCampaignSuggestions' in knowledge_bank_content, "Missing suggestion regeneration"
        assert 'campaign-intelligence/generate' in knowledge_bank_content, "Missing API call"
        
        logger.info("✅ Frontend Integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Frontend Integration test failed: {e}")
        return False

def test_database_schema():
    """Test the database schema migration"""
    logger.info("🗃️ Testing Database Schema...")
    
    try:
        # Check if migration file exists
        migration_file = 'supabase_migrations/create_smart_campaign_tables.sql'
        assert os.path.exists(migration_file), f"Missing migration file: {migration_file}"
        
        # Check migration content
        with open(migration_file, 'r') as f:
            migration_content = f.read()
        
        required_tables = [
            'campaign_suggestions',
            'campaign_executions',
            'prompt_patterns'
        ]
        
        for table in required_tables:
            assert f'CREATE TABLE.*{table}' in migration_content or f'{table}' in migration_content, f"Missing table: {table}"
        
        # Check for indexes and policies
        assert 'CREATE INDEX' in migration_content, "Missing indexes"
        assert 'ROW LEVEL SECURITY' in migration_content, "Missing RLS policies"
        
        logger.info("✅ Database Schema test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database Schema test failed: {e}")
        return False

def test_end_to_end_flow():
    """Test the complete end-to-end flow"""
    logger.info("🔄 Testing End-to-End Flow...")
    
    try:
        from services.campaign_intelligence_service import CampaignIntelligenceService
        from services.campaign_learning_service import CampaignLearningService
        
        # Simulate complete flow
        intelligence_service = CampaignIntelligenceService()
        learning_service = CampaignLearningService()
        
        # 1. Analyze documents (simulated)
        mock_knowledge = {
            'company_info': {'company_name': 'Test Company', 'industry': 'Technology'},
            'products': [{'name': 'Test Product'}],
            'target_audience': {'buyer_personas': ['CTOs']},
            'source_count': 1
        }
        
        # 2. Generate suggestions
        suggestions = intelligence_service.generate_prompt_suggestions(mock_knowledge)
        assert len(suggestions) > 0, "No suggestions generated"
        
        # 3. Simulate campaign execution
        prompt_data = {
            'original_prompt': suggestions[0]['prompt'],
            'suggested_prompt_id': suggestions[0]['id']
        }
        
        results = {
            'lead_count': 10,
            'campaign_success': True,
            'quality_score': 0.8
        }
        
        # 4. Record execution (this would normally save to DB)
        execution_record = learning_service.record_campaign_execution(
            'test_tenant', 'test_user', prompt_data, results
        )
        
        # 5. Analyze patterns
        patterns = learning_service.analyze_successful_patterns('test_tenant', 'test_user')
        
        logger.info("✅ End-to-End Flow test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-End Flow test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Smart Campaign Suggestions Tests...")
    
    tests = [
        test_database_schema,
        test_campaign_intelligence_service,
        test_campaign_learning_service,
        test_supabase_methods,
        test_api_endpoints,
        test_frontend_integration,
        test_end_to_end_flow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Smart Campaign Suggestions implementation is ready.")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
