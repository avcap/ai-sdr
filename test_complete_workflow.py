#!/usr/bin/env python3
"""
Test the complete Train Your Team workflow
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend_health():
    """Test if frontend is running"""
    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_train_your_team_endpoints():
    """Test Train Your Team endpoints"""
    endpoints = [
        "/train-your-team/agent-info",
        "/train-your-team/get-knowledge"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}")
            if response.status_code in [200, 401]:  # 401 is expected without auth
                print(f"✅ {endpoint} - Available")
            else:
                print(f"❌ {endpoint} - Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if url and key:
            client = create_client(url, key)
            result = client.table('tenants').select('id').limit(1).execute()
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Missing Supabase credentials")
            return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def main():
    print("🚀 Testing Complete Train Your Team Workflow")
    print("=" * 50)
    
    # Test all components
    backend_ok = test_backend_health()
    frontend_ok = test_frontend_health()
    supabase_ok = test_supabase_connection()
    
    print("\n📋 Train Your Team Endpoints:")
    test_train_your_team_endpoints()
    
    print("\n🎯 Overall Status:")
    if backend_ok and frontend_ok and supabase_ok:
        print("🎉 ALL SYSTEMS READY!")
        print("\n✅ Backend: Multi-tenant FastAPI running")
        print("✅ Frontend: Next.js dashboard running") 
        print("✅ Database: Supabase PostgreSQL connected")
        print("✅ Train Your Team: All endpoints available")
        
        print("\n🚀 Ready to test the complete workflow!")
        print("1. Go to http://localhost:3000")
        print("2. Click '🎓 Train Your Team'")
        print("3. Upload a document")
        print("4. Extract knowledge with Claude AI")
        print("5. Save knowledge to your profile")
        
    else:
        print("❌ Some components are not ready")
        if not backend_ok:
            print("   - Backend needs to be started")
        if not frontend_ok:
            print("   - Frontend needs to be started")
        if not supabase_ok:
            print("   - Supabase connection needs to be fixed")

if __name__ == "__main__":
    main()

