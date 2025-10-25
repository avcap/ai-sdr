#!/usr/bin/env python3
"""
Test script to verify document type detection and knowledge extraction.
"""

import os
import json
import logging
from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
from services.knowledge_service import KnowledgeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_type_detection():
    """Test document type detection with different types of documents"""
    
    print("🧪 TESTING DOCUMENT TYPE DETECTION")
    print("=" * 50)
    
    # Set up environment variables
    os.environ['ANTHROPIC_API_KEY'] = "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"
    
    # Initialize the knowledge extraction agent
    agent = KnowledgeExtractionAgent()
    
    # Test 1: Sales Training Document
    print("\n1️⃣ TESTING SALES TRAINING DOCUMENT")
    print("-" * 30)
    
    sales_training_content = """
    How to Be the Best AI SDR
    
    Introduction:
    Being an AI SDR requires a unique combination of technical knowledge and sales skills. 
    This guide will help you master the art of AI-powered sales development.
    
    Key Sales Methodologies:
    1. SPIN Selling - Focus on Situation, Problem, Implication, Need-payoff
    2. Challenger Sale - Teach, tailor, take control
    3. Consultative Selling - Understand customer needs first
    
    Target Audience Insights:
    - Decision makers: CTOs, VPs of Engineering, IT Directors
    - Common pain points: Manual processes, inefficiency, cost overruns
    - Decision making process: Technical evaluation, ROI analysis, security review
    
    Best Practices:
    - Always research the prospect's company before outreach
    - Use data-driven insights to personalize messages
    - Follow up consistently but not aggressively
    - Focus on value proposition over features
    
    Industry Context:
    - SaaS companies are growing rapidly
    - AI adoption is accelerating across industries
    - Security and compliance are top concerns
    
    Practical Advice:
    - Use LinkedIn for research and connection
    - Send personalized video messages
    - Leverage social proof and case studies
    - Always ask for referrals
    """
    
    # Create a temporary file
    with open('/tmp/sales_training_test.txt', 'w') as f:
        f.write(sales_training_content)
    
    # Extract knowledge
    result = agent.extract_knowledge_from_files(['/tmp/sales_training_test.txt'])
    
    if result['success']:
        knowledge = result['knowledge']
        print(f"✅ Document type detected: {knowledge.get('document_type', 'Unknown')}")
        print(f"📊 Knowledge keys: {list(knowledge.keys())}")
        
        if knowledge.get('document_type') == 'sales_training':
            print("✅ Correctly identified as sales training document")
            print(f"📚 Sales methodologies: {knowledge.get('sales_methodologies', [])}")
            print(f"🎯 Target audience insights: {knowledge.get('target_audience_insights', {})}")
        else:
            print(f"❌ Expected 'sales_training', got '{knowledge.get('document_type')}'")
    else:
        print(f"❌ Extraction failed: {result.get('error')}")
    
    # Test 2: Company Info Document
    print("\n2️⃣ TESTING COMPANY INFO DOCUMENT")
    print("-" * 30)
    
    company_info_content = """
    TechCorp Solutions - Company Overview
    
    Company Information:
    TechCorp Solutions is a leading provider of AI-powered business automation solutions.
    Founded in 2018, we serve mid-market and enterprise clients across various industries.
    
    Mission Statement:
    To empower businesses with intelligent automation solutions that drive efficiency, 
    reduce costs, and accelerate growth.
    
    Core Values:
    - Innovation
    - Customer Success
    - Integrity
    - Collaboration
    
    Products and Services:
    TechCorp AI Assistant - Our flagship product that helps companies automate routine tasks,
    analyze data, and make informed decisions. Key features include natural language processing,
    automated workflow creation, and real-time data insights.
    
    Target Market:
    - Mid-market companies (100-1000 employees)
    - Enterprise clients (1000+ employees)
    - Industries: Healthcare, Financial Services, Manufacturing, Retail
    
    Value Propositions:
    - Reduce operational costs by 30-50%
    - Increase team productivity by 40%
    - Faster decision-making with real-time insights
    - Seamless integration with existing tools
    
    Competitive Advantages:
    - Industry-leading AI accuracy (99.2% accuracy rate)
    - Fastest implementation time (average 2 weeks)
    - Most comprehensive integration ecosystem
    - Dedicated customer success team
    """
    
    # Create a temporary file
    with open('/tmp/company_info_test.txt', 'w') as f:
        f.write(company_info_content)
    
    # Extract knowledge
    result = agent.extract_knowledge_from_files(['/tmp/company_info_test.txt'])
    
    if result['success']:
        knowledge = result['knowledge']
        print(f"✅ Document type detected: {knowledge.get('document_type', 'Unknown')}")
        print(f"📊 Knowledge keys: {list(knowledge.keys())}")
        
        if knowledge.get('document_type') == 'company_info':
            print("✅ Correctly identified as company info document")
            company_info = knowledge.get('company_info', {})
            print(f"🏢 Company name: {company_info.get('company_name', 'Unknown')}")
            print(f"🏭 Industry: {company_info.get('industry', 'Unknown')}")
            print(f"📈 Products: {len(knowledge.get('products', []))}")
        else:
            print(f"❌ Expected 'company_info', got '{knowledge.get('document_type')}'")
    else:
        print(f"❌ Extraction failed: {result.get('error')}")
    
    # Test 3: Knowledge Service Normalization
    print("\n3️⃣ TESTING KNOWLEDGE SERVICE NORMALIZATION")
    print("-" * 30)
    
    knowledge_service = KnowledgeService()
    
    # Test with sales training knowledge
    sales_training_knowledge = {
        "document_type": "sales_training",
        "sales_methodologies": ["SPIN Selling", "Challenger Sale", "Consultative Selling"],
        "target_audience_insights": {
            "buyer_personas": ["CTOs", "VPs of Engineering", "IT Directors"],
            "pain_points": ["Manual processes", "Inefficiency", "Cost overruns"]
        },
        "sales_philosophy": "Data-driven, consultative approach",
        "key_messages": ["Focus on value proposition", "Use social proof"],
        "practical_advice": ["Research prospects", "Personalize messages", "Follow up consistently"]
    }
    
    normalized = knowledge_service._normalize_sales_training_knowledge(sales_training_knowledge)
    print(f"✅ Normalized document type: {normalized.get('document_type')}")
    print(f"📚 Sales approach: {normalized.get('sales_approach', '')[:100]}...")
    print(f"🎯 Target audience: {normalized.get('target_audience', {})}")
    print(f"💡 Key messages: {len(normalized.get('key_messages', []))}")
    
    # Test 4: Prompt Enhancement
    print("\n4️⃣ TESTING PROMPT ENHANCEMENT")
    print("-" * 30)
    
    # Mock knowledge record for testing
    mock_knowledge_record = {
        'content': json.dumps(sales_training_knowledge)
    }
    
    # Test formatting
    formatted_context = knowledge_service._format_knowledge_for_prompts(normalized)
    print("✅ Formatted context:")
    print(formatted_context[:200] + "..." if len(formatted_context) > 200 else formatted_context)
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 50)
    
    # Clean up temporary files
    try:
        os.remove('/tmp/sales_training_test.txt')
        os.remove('/tmp/company_info_test.txt')
        print("🧹 Cleaned up temporary files")
    except:
        pass

if __name__ == "__main__":
    test_document_type_detection()

