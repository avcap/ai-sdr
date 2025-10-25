#!/usr/bin/env python3
"""
Test script to verify sales training knowledge is being used correctly by AI agents.
"""

import os
import json
import logging
from services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sales_training_knowledge_usage():
    """Test that sales training knowledge is properly normalized and used"""
    
    print("🧪 TESTING SALES TRAINING KNOWLEDGE USAGE")
    print("=" * 50)
    
    # Set up environment variables
    os.environ['SUPABASE_URL'] = "https://nxzxdllhjdazcfjvlkyy.supabase.co"
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im54enhkbGxoamRhemNmanZsa3l5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI1MjI1MSwiZXhwIjoyMDc2ODI4MjUxfQ.sYKbZK1JtFgoIpm1QbWF1XmVxpndmycJsvzh6ufugmw"
    
    # Initialize the knowledge service
    knowledge_service = KnowledgeService()
    
    # Test with demo user
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    user_id = "89985897-54af-436b-8ff5-61c5fa30f434"
    
    print("\n1️⃣ TESTING KNOWLEDGE RETRIEVAL")
    print("-" * 30)
    
    # Get user knowledge
    knowledge = knowledge_service.get_user_knowledge(tenant_id, user_id)
    print(f"✅ Knowledge retrieved")
    print(f"📊 Document type: {knowledge.get('document_type', 'Unknown')}")
    print(f"📋 Knowledge keys: {list(knowledge.keys())}")
    
    if knowledge.get('document_type') == 'sales_training':
        print("✅ Correctly identified as sales training knowledge")
    else:
        print(f"❌ Expected 'sales_training', got '{knowledge.get('document_type')}'")
    
    print("\n2️⃣ TESTING KNOWLEDGE NORMALIZATION")
    print("-" * 30)
    
    # Test normalization
    company_info = knowledge.get('company_info', {})
    sales_approach = knowledge.get('sales_approach', '')
    target_audience = knowledge.get('target_audience', {})
    key_messages = knowledge.get('key_messages', [])
    
    print(f"🏢 Company name: {company_info.get('company_name', 'Unknown')}")
    print(f"🏭 Industry: {company_info.get('industry', 'Unknown')}")
    print(f"📚 Sales approach: {sales_approach[:100]}..." if len(sales_approach) > 100 else f"📚 Sales approach: {sales_approach}")
    print(f"🎯 Target audience: {target_audience}")
    print(f"💡 Key messages: {len(key_messages)} messages")
    
    print("\n3️⃣ TESTING PROMPT ENHANCEMENT")
    print("-" * 30)
    
    # Test prompt enhancement
    enhanced_prompt = knowledge_service.build_knowledge_enhanced_prompt(
        "Find me 3 CTOs in healthcare companies", 
        tenant_id, 
        user_id
    )
    
    print("✅ Enhanced prompt created")
    print(f"📏 Prompt length: {len(enhanced_prompt)} characters")
    
    # Check if sales training context is included
    if "SALES TRAINING KNOWLEDGE" in enhanced_prompt:
        print("✅ Sales training context included in prompt")
    else:
        print("❌ Sales training context missing from prompt")
    
    # Check for specific sales training elements
    sales_elements = [
        "SPIN Selling",
        "Challenger Sale", 
        "Consultative Selling",
        "CTOs",
        "VPs of Engineering",
        "IT Directors"
    ]
    
    found_elements = [elem for elem in sales_elements if elem in enhanced_prompt]
    print(f"📋 Found sales elements: {found_elements}")
    
    print("\n4️⃣ TESTING COMPANY CONTEXT FORMATTING")
    print("-" * 30)
    
    # Test company context formatting
    company_context = knowledge_service.get_company_context(tenant_id, user_id)
    print("✅ Company context formatted")
    print(f"📏 Context length: {len(company_context)} characters")
    
    # Show first 300 characters
    print(f"📄 Context preview: {company_context[:300]}...")
    
    print("\n5️⃣ TESTING SPECIFIC KNOWLEDGE COMPONENTS")
    print("-" * 30)
    
    # Test specific components
    target_audience = knowledge_service.get_target_audience(tenant_id, user_id)
    value_propositions = knowledge_service.get_value_propositions(tenant_id, user_id)
    sales_approach = knowledge_service.get_sales_approach(tenant_id, user_id)
    competitive_advantages = knowledge_service.get_competitive_advantages(tenant_id, user_id)
    
    print(f"🎯 Target audience: {target_audience}")
    print(f"💎 Value propositions: {len(value_propositions)} items")
    print(f"📚 Sales approach: {sales_approach[:100]}..." if len(sales_approach) > 100 else f"📚 Sales approach: {sales_approach}")
    print(f"🏆 Competitive advantages: {len(competitive_advantages)} items")
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 50)
    
    # Summary
    print("\n📝 SUMMARY:")
    print(f"   Document Type: {knowledge.get('document_type', 'Unknown')}")
    print(f"   Company: {company_info.get('company_name', 'Unknown')}")
    print(f"   Industry: {company_info.get('industry', 'Unknown')}")
    print(f"   Sales Approach: {'✅ Present' if sales_approach else '❌ Missing'}")
    print(f"   Target Audience: {'✅ Present' if target_audience else '❌ Missing'}")
    print(f"   Key Messages: {len(key_messages)} items")
    print(f"   Value Propositions: {len(value_propositions)} items")
    print(f"   Competitive Advantages: {len(competitive_advantages)} items")

if __name__ == "__main__":
    test_sales_training_knowledge_usage()

