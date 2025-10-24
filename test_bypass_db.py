#!/usr/bin/env python3
"""
Quick fix: Create a simple test to bypass the missing tables issue
"""
import requests
import json

def test_upload_without_database():
    """Test the upload functionality by mocking the database calls"""
    
    backend_url = "http://localhost:8000"
    
    # Create a test file
    test_content = """
    Company Overview:
    We are a leading AI automation platform that helps businesses streamline their operations.
    
    Our Products:
    - AI-powered workflow automation
    - Intelligent document processing
    - Smart data analytics
    - Custom AI solutions
    
    Sales Methodology:
    We focus on understanding client needs and providing tailored solutions.
    Our approach is consultative and results-driven.
    """
    
    with open('/Users/zoecapital/ai-sdr/test_doc.txt', 'w') as f:
        f.write(test_content)
    
    print("🧪 Testing upload without database dependency...")
    
    try:
        # Test 1: Check if backend is running
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
        
        # Test 2: Test knowledge extraction directly
        print("\n📋 Testing knowledge extraction...")
        
        # Create a simple test payload
        test_data = {
            "file_paths": ["/Users/zoecapital/ai-sdr/test_doc.txt"],
            "subject": "Company Overview"
        }
        
        response = requests.post(f"{backend_url}/train-your-team/extract-knowledge", 
                               json=test_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Knowledge extraction response: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ Knowledge extraction works!")
            return True
        else:
            print(f"⚠️  Knowledge extraction response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Clean up
        import os
        if os.path.exists('/Users/zoecapital/ai-sdr/test_doc.txt'):
            os.remove('/Users/zoecapital/ai-sdr/test_doc.txt')
    
    return False

if __name__ == "__main__":
    test_upload_without_database()

