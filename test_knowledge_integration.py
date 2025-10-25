#!/usr/bin/env python3
"""
Test script to verify AI agents are using company knowledge
This tests the knowledge integration without requiring OpenAI API calls
"""

import sys
import os
sys.path.append('/Users/zoecapital/ai-sdr')

from services.knowledge_service import KnowledgeService
from agents.prospector_agent import ProspectorAgent
from agents.smart_campaign_orchestrator import SmartCampaignOrchestrator
from agents.copywriter_agent import CopywriterAgent
from agents.smart_outreach_agent import SmartOutreachAgent

def test_knowledge_integration():
    """Test that agents properly integrate company knowledge"""
    
    print("🧪 TESTING AI AGENT KNOWLEDGE INTEGRATION")
    print("=" * 50)
    
    # Test data
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    user_id = "89985897-54af-436b-8ff5-61c5fa30f434"
    
    # Initialize knowledge service
    ks = KnowledgeService()
    
    # Test 1: Knowledge Retrieval
    print("\n1️⃣ TESTING KNOWLEDGE RETRIEVAL")
    print("-" * 30)
    
    knowledge = ks.get_user_knowledge(tenant_id, user_id)
    if knowledge:
        print("✅ Knowledge retrieved successfully")
        print(f"   Company: {knowledge.get('company_info', {}).get('company_name', 'N/A')}")
        print(f"   Industry: {knowledge.get('company_info', {}).get('industry', 'N/A')}")
        print(f"   Products: {len(knowledge.get('products', []))}")
        print(f"   Value Props: {len(knowledge.get('value_propositions', []))}")
    else:
        print("❌ Failed to retrieve knowledge")
        return False
    
    # Test 2: ProspectorAgent Knowledge Integration
    print("\n2️⃣ TESTING PROSPECTOR AGENT")
    print("-" * 30)
    
    try:
        prospector = ProspectorAgent()
        # Test that the agent has knowledge service
        if hasattr(prospector, 'knowledge_service'):
            print("✅ ProspectorAgent has knowledge service")
        else:
            print("❌ ProspectorAgent missing knowledge service")
            return False
            
        # Test that parse_prompt accepts tenant_id and user_id
        try:
            criteria = prospector.tool.parse_prompt(
                "Find healthcare CTOs", 
                tenant_id=tenant_id, 
                user_id=user_id
            )
            print("✅ ProspectorAgent parse_prompt accepts knowledge parameters")
        except Exception as e:
            print(f"❌ ProspectorAgent parse_prompt failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ProspectorAgent test failed: {e}")
        return False
    
    # Test 3: SmartCampaignOrchestrator Knowledge Integration
    print("\n3️⃣ TESTING SMART CAMPAIGN ORCHESTRATOR")
    print("-" * 30)
    
    try:
        orchestrator = SmartCampaignOrchestrator()
        if hasattr(orchestrator, 'knowledge_service'):
            print("✅ SmartCampaignOrchestrator has knowledge service")
        else:
            print("❌ SmartCampaignOrchestrator missing knowledge service")
            return False
            
        # Test analyze_prompt with knowledge
        try:
            analysis = orchestrator.analyze_prompt(
                "Create healthcare campaign", 
                tenant_id=tenant_id, 
                user_id=user_id
            )
            print("✅ SmartCampaignOrchestrator analyze_prompt accepts knowledge parameters")
        except Exception as e:
            print(f"❌ SmartCampaignOrchestrator analyze_prompt failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ SmartCampaignOrchestrator test failed: {e}")
        return False
    
    # Test 4: CopywriterAgent Knowledge Integration
    print("\n4️⃣ TESTING COPYWRITER AGENT")
    print("-" * 30)
    
    try:
        copywriter = CopywriterAgent()
        if hasattr(copywriter, 'knowledge_service'):
            print("✅ CopywriterAgent has knowledge service")
        else:
            print("❌ CopywriterAgent missing knowledge service")
            return False
            
        # Test personalize_message with knowledge
        try:
            result = copywriter.personalize_message(
                {"name": "John", "title": "CTO", "company": "HealthTech"},
                tenant_id=tenant_id,
                user_id=user_id
            )
            print("✅ CopywriterAgent personalize_message accepts knowledge parameters")
        except Exception as e:
            print(f"❌ CopywriterAgent personalize_message failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ CopywriterAgent test failed: {e}")
        return False
    
    # Test 5: SmartOutreachAgent Knowledge Integration
    print("\n5️⃣ TESTING SMART OUTREACH AGENT")
    print("-" * 30)
    
    try:
        outreach = SmartOutreachAgent()
        if hasattr(outreach, 'knowledge_service'):
            print("✅ SmartOutreachAgent has knowledge service")
        else:
            print("❌ SmartOutreachAgent missing knowledge service")
            return False
            
        # Test create_smart_outreach_plan with knowledge
        try:
            result = outreach.create_smart_outreach_plan(
                [{"name": "John", "title": "CTO"}],
                tenant_id=tenant_id,
                user_id=user_id
            )
            print("✅ SmartOutreachAgent create_smart_outreach_plan accepts knowledge parameters")
        except Exception as e:
            print(f"❌ SmartOutreachAgent create_smart_outreach_plan failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ SmartOutreachAgent test failed: {e}")
        return False
    
    # Test 6: Prompt Enhancement
    print("\n6️⃣ TESTING PROMPT ENHANCEMENT")
    print("-" * 30)
    
    base_prompt = "Generate leads for healthcare companies"
    enhanced_prompt = ks.build_knowledge_enhanced_prompt(base_prompt, tenant_id, user_id)
    
    if len(enhanced_prompt) > len(base_prompt):
        print("✅ Prompt enhancement working")
        print(f"   Base prompt length: {len(base_prompt)}")
        print(f"   Enhanced prompt length: {len(enhanced_prompt)}")
        print(f"   Enhancement ratio: {len(enhanced_prompt) / len(base_prompt):.1f}x")
    else:
        print("❌ Prompt enhancement failed")
        return False
    
    # Test 7: Knowledge Components
    print("\n7️⃣ TESTING KNOWLEDGE COMPONENTS")
    print("-" * 30)
    
    components = {
        'target_audience': ks.get_target_audience(tenant_id, user_id),
        'value_propositions': ks.get_value_propositions(tenant_id, user_id),
        'products': ks.get_products(tenant_id, user_id),
        'sales_approach': ks.get_sales_approach(tenant_id, user_id),
        'competitive_advantages': ks.get_competitive_advantages(tenant_id, user_id)
    }
    
    all_components_found = True
    for name, component in components.items():
        if component:
            print(f"✅ {name}: Found")
        else:
            print(f"❌ {name}: Missing")
            all_components_found = False
    
    if not all_components_found:
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 50)
    print("✅ Knowledge integration is working correctly")
    print("✅ All AI agents can access company knowledge")
    print("✅ Prompt enhancement is functioning")
    print("✅ Knowledge components are properly structured")
    print("\n📝 SUMMARY:")
    print(f"   Company: {knowledge.get('company_info', {}).get('company_name', 'N/A')}")
    print(f"   Industry: {knowledge.get('company_info', {}).get('industry', 'N/A')}")
    print(f"   Products: {len(knowledge.get('products', []))}")
    print(f"   Value Props: {len(knowledge.get('value_propositions', []))}")
    print(f"   Target Audience: {knowledge.get('target_audience', {}).get('primary_customers', 'N/A')}")
    
    return True

if __name__ == "__main__":
    success = test_knowledge_integration()
    sys.exit(0 if success else 1)

