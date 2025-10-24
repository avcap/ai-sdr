#!/usr/bin/env python3
"""
Test the Train Your Team functionality with a demo tenant and user
"""
import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_train_your_team():
    """Test the complete Train Your Team workflow"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        client = create_client(url, key)
        
        print("🧪 Testing Train Your Team functionality...")
        
        # Test 1: Create a demo tenant
        print("\n1. Creating demo tenant...")
        tenant_data = {
            "name": "Demo Company",
            "slug": "demo-company",
            "plan": "free",
            "status": "active"
        }
        
        try:
            tenant_result = client.table('tenants').insert(tenant_data).execute()
            tenant_id = tenant_result.data[0]['id']
            print(f"✅ Demo tenant created: {tenant_id}")
        except Exception as e:
            print(f"⚠️  Tenant creation: {e}")
            # Try to get existing tenant
            existing_tenant = client.table('tenants').select('id').eq('slug', 'demo-company').execute()
            if existing_tenant.data:
                tenant_id = existing_tenant.data[0]['id']
                print(f"✅ Using existing tenant: {tenant_id}")
            else:
                print("❌ Could not create or find tenant")
                return False
        
        # Test 2: Create a demo user
        print("\n2. Creating demo user...")
        user_data = {
            "tenant_id": tenant_id,
            "email": "demo@example.com",
            "name": "Demo User",
            "role": "admin"
        }
        
        try:
            user_result = client.table('users').insert(user_data).execute()
            user_id = user_result.data[0]['id']
            print(f"✅ Demo user created: {user_id}")
        except Exception as e:
            print(f"⚠️  User creation: {e}")
            # Try to get existing user
            existing_user = client.table('users').select('id').eq('email', 'demo@example.com').execute()
            if existing_user.data:
                user_id = existing_user.data[0]['id']
                print(f"✅ Using existing user: {user_id}")
            else:
                print("❌ Could not create or find user")
                return False
        
        # Test 3: Test file upload via backend
        print("\n3. Testing file upload...")
        
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
        
        with open('/Users/zoecapital/ai-sdr/test_company_doc.txt', 'w') as f:
            f.write(test_content)
        
        # Test upload to backend
        backend_url = "http://localhost:8000"
        
        try:
            with open('/Users/zoecapital/ai-sdr/test_company_doc.txt', 'rb') as f:
                files = {'files': f}
                data = {'subject': 'Company Overview'}
                
                # Add authentication header (we'll use a simple approach for testing)
                headers = {'Authorization': f'Bearer demo-token'}
                
                response = requests.post(f"{backend_url}/train-your-team/upload", 
                                       files=files, data=data, headers=headers)
                
                print(f"Upload response: {response.status_code}")
                print(f"Upload result: {response.text[:200]}")
                
                if response.status_code == 200:
                    print("✅ File upload successful!")
                else:
                    print(f"⚠️  Upload response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Upload test failed: {e}")
        
        # Clean up test file
        if os.path.exists('/Users/zoecapital/ai-sdr/test_company_doc.txt'):
            os.remove('/Users/zoecapital/ai-sdr/test_company_doc.txt')
        
        print("\n🎯 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_train_your_team()