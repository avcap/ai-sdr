import os
from dotenv import load_dotenv
from services.sales_playbook_service import SalesPlaybookService
from services.campaign_intelligence_service import CampaignIntelligenceService

load_dotenv()

def test_adaptive_playbook():
    """Test the adaptive sales playbook system"""
    
    print("🧪 Testing Adaptive Sales Playbook System\n")
    
    # Test 1: Framework Selection
    print("Test 1: LLM Framework Selection")
    playbook_service = SalesPlaybookService()
    
    test_context = {
        'company_name': 'Enterprise Solutions Inc',
        'industry': 'B2B SaaS',
        'products': ['Enterprise CRM', 'Sales Analytics Platform'],
        'target_audience': {
            'roles': ['VP Sales', 'CRO', 'Sales Director'],
            'company_sizes': ['500-5000 employees'],
            'industries': ['Technology', 'Financial Services']
        },
        'tenant_id': '550e8400-e29b-41d4-a716-446655440000',
        'user_id': '89985897-54af-436b-8ff5-61c5fa30f434'
    }
    
    strategies = playbook_service.get_adaptive_strategies(
        test_context['tenant_id'],
        test_context['user_id'],
        test_context
    )
    
    print(f"✅ Strategy Source: {strategies.get('source')}")
    print(f"✅ Confidence: {strategies.get('confidence'):.0%}")
    print(f"✅ Reasoning: {strategies.get('reasoning')}\n")
    
    # Test 2: Campaign Suggestions with Adaptive Strategies
    print("Test 2: Generating Campaign Suggestions with Adaptive Strategies")
    intelligence_service = CampaignIntelligenceService()
    
    insights = intelligence_service.analyze_documents_for_campaigns(
        test_context['tenant_id'],
        test_context['user_id']
    )
    
    if insights.get('success'):
        suggestions = insights.get('suggestions', [])
        print(f"✅ Generated {len(suggestions)} suggestions")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\nSuggestion {i}:")
            print(f"  Title: {suggestion.get('title')}")
            print(f"  Strategy Applied: {suggestion.get('framework_application', 'N/A')}")
            print(f"  Confidence: {suggestion.get('confidence', 0):.0%}")
    else:
        print(f"❌ Failed to generate suggestions: {insights.get('error')}")
    
    print("\n✅ All tests completed!")

if __name__ == '__main__':
    test_adaptive_playbook()

