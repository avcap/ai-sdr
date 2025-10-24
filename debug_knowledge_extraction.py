#!/usr/bin/env python3
"""
Debug script for knowledge extraction
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('/Users/zoecapital/ai-sdr')

from agents.knowledge_extraction_agent import KnowledgeExtractionAgent

def test_knowledge_extraction():
    print("🧪 Testing Knowledge Extraction Agent")
    print("=" * 50)
    
    # Test with the uploaded file
    file_path = "/Users/zoecapital/ai-sdr/uploads/training/demo_user_sample_company_doc.txt"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Testing with file: {file_path}")
    
    # Initialize the agent
    try:
        agent = KnowledgeExtractionAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test file reading
    try:
        content = agent._read_document(file_path)
        if content:
            print(f"✅ File read successfully ({len(content)} characters)")
            print(f"📄 First 200 characters: {content[:200]}...")
        else:
            print("❌ Failed to read file content")
            return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Test knowledge extraction
    try:
        print("\n🧠 Testing knowledge extraction...")
        result = agent.extract_knowledge_from_files([file_path])
        
        if result["success"]:
            print("✅ Knowledge extraction successful!")
            knowledge = result["knowledge"]
            
            print("\n📊 Extracted Knowledge:")
            print(f"🏢 Company: {knowledge.get('company_info', {}).get('company_name', 'N/A')}")
            print(f"🏭 Industry: {knowledge.get('company_info', {}).get('industry', 'N/A')}")
            print(f"📦 Products: {len(knowledge.get('products', []))}")
            print(f"💬 Key Messages: {len(knowledge.get('key_messages', []))}")
            
            if knowledge.get('key_messages'):
                print("Sample key messages:")
                for i, msg in enumerate(knowledge['key_messages'][:3], 1):
                    print(f"  {i}. {msg}")
        else:
            print(f"❌ Knowledge extraction failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during knowledge extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_extraction()
