#!/usr/bin/env python3
"""
Test script to verify knowledge normalization logic.
"""

import os
import json
import logging
from services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_knowledge_normalization():
    """Test knowledge normalization logic"""
    
    print("🧪 TESTING KNOWLEDGE NORMALIZATION")
    print("=" * 50)
    
    # Set up environment variables
    os.environ['SUPABASE_URL'] = "https://nxzxdllhjdazcfjvlkyy.supabase.co"
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im54enhkbGxoamRhemNmanZsa3l5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI1MjI1MSwiZXhwIjoyMDc2ODI4MjUxfQ.sYKbZK1JtFgoIpm1QbWF1XmVxpndmycJsvzh6ufugmw"
    
    # Initialize the knowledge service
    knowledge_service = KnowledgeService()
    
    print("\n1️⃣ TESTING SALES TRAINING NORMALIZATION")
    print("-" * 30)
    
    # Test with sales training knowledge structure
    sales_training_knowledge = {
        "document_type": "company_info",  # This is wrong, but should be inferred
        "sales_methodologies": ["SPIN Selling", "Challenger Sale"],
        "target_audience_insights": {
            "buyer_personas": ["CTOs", "VPs of Engineering"],
            "pain_points": ["Manual processes", "Inefficiency"]
        },
        "sales_philosophy": "Data-driven approach",
        "practical_advice": ["Research prospects", "Personalize messages"]
    }
    
    normalized = knowledge_service._normalize_knowledge_by_type(sales_training_knowledge)
    print(f"✅ Normalized document type: {normalized.get('document_type')}")
    print(f"📚 Sales approach: {normalized.get('sales_approach', '')[:100]}...")
    print(f"🎯 Target audience: {normalized.get('target_audience', {})}")
    
    print("\n2️⃣ TESTING COMPANY INFO NORMALIZATION")
    print("-" * 30)
    
    # Test with company info knowledge structure
    company_info_knowledge = {
        "document_type": "company_info",
        "company_info": {
            "company_name": "TechCorp",
            "industry": "Technology"
        },
        "sales_approach": "Consultative selling",
        "products": [{"name": "Product A", "description": "Description"}]
    }
    
    normalized = knowledge_service._normalize_knowledge_by_type(company_info_knowledge)
    print(f"✅ Normalized document type: {normalized.get('document_type')}")
    print(f"🏢 Company name: {normalized.get('company_info', {}).get('company_name')}")
    print(f"📈 Products: {len(normalized.get('products', []))}")
    
    print("\n3️⃣ TESTING INFERENCE LOGIC")
    print("-" * 30)
    
    # Test inference when document_type is wrong but content suggests sales training
    mixed_knowledge = {
        "document_type": "company_info",  # Wrong type
        "company_info": None,  # No company info
        "sales_methodologies": ["SPIN Selling"],
        "target_audience_insights": {"buyer_personas": ["CTOs"]},
        "practical_advice": ["Research prospects"]
    }
    
    normalized = knowledge_service._normalize_knowledge_by_type(mixed_knowledge)
    print(f"✅ Inferred document type: {normalized.get('document_type')}")
    print(f"📚 Sales approach: {normalized.get('sales_approach', '')[:100]}...")
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 50)

if __name__ == "__main__":
    test_knowledge_normalization()

