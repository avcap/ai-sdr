#!/usr/bin/env python3
"""
Test file upload to Train Your Team without authentication
"""
import requests
import os

def test_file_upload():
    """Test uploading a file to the Train Your Team endpoint"""
    
    # Create a simple test file
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
    
    # Save test file
    with open('/Users/zoecapital/ai-sdr/test_company_doc.txt', 'w') as f:
        f.write(test_content)
    
    # Test upload
    backend_url = "http://localhost:8000"
    
    try:
        # Test 1: Check if endpoint exists
        print("🔍 Testing Train Your Team endpoints...")
        
        # Test agent info endpoint
        response = requests.get(f"{backend_url}/train-your-team/agent-info")
        print(f"Agent Info: {response.status_code} - {response.text[:100]}")
        
        # Test upload endpoint (this will fail without auth, but we can see the error)
        files = {'files': open('/Users/zoecapital/ai-sdr/test_company_doc.txt', 'rb')}
        response = requests.post(f"{backend_url}/train-your-team/upload", files=files)
        print(f"Upload Test: {response.status_code} - {response.text[:100]}")
        
        # Test knowledge extraction
        data = {
            "file_paths": ["/Users/zoecapital/ai-sdr/test_company_doc.txt"],
            "subject": "Company Overview"
        }
        response = requests.post(f"{backend_url}/train-your-team/extract-knowledge", json=data)
        print(f"Knowledge Extraction: {response.status_code} - {response.text[:100]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists('/Users/zoecapital/ai-sdr/test_company_doc.txt'):
            os.remove('/Users/zoecapital/ai-sdr/test_company_doc.txt')

if __name__ == "__main__":
    test_file_upload()

