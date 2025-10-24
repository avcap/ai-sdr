#!/usr/bin/env python3
"""
Google Integration Demo Script

This script demonstrates how the AI SDR system works with Google OAuth integration.
It shows the complete workflow from user authentication to campaign execution.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.google_workflow import AISDRWorkflow, CampaignData, LeadData
from integrations.google_oauth_service import GoogleOAuthService

def demo_google_integration():
    """Demonstrate the Google-integrated AI SDR workflow"""
    
    print("🚀 AI SDR Google Integration Demo")
    print("=" * 50)
    
    # Check if Google OAuth is configured
    google_oauth = GoogleOAuthService()
    
    if not google_oauth.client_id or not google_oauth.client_secret:
        print("❌ Google OAuth not configured!")
        print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file")
        print("See GOOGLE_INTEGRATION_GUIDE.md for setup instructions")
        return
    
    print("✅ Google OAuth configured")
    
    # Demo data
    sample_leads = [
        {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "title": "VP of Engineering",
            "email": "john@techcorp.com",
            "industry": "Technology",
            "company_size": "100-500",
            "location": "San Francisco, CA"
        },
        {
            "name": "Sarah Johnson",
            "company": "DataFlow Systems",
            "title": "CTO",
            "email": "sarah@dataflow.com",
            "industry": "Data Analytics",
            "company_size": "50-100",
            "location": "Austin, TX"
        },
        {
            "name": "Mike Chen",
            "company": "StartupXYZ",
            "title": "Founder",
            "email": "mike@startupxyz.com",
            "industry": "Fintech",
            "company_size": "10-50",
            "location": "New York, NY"
        }
    ]
    
    sample_campaign = CampaignData(
        campaign_id="demo_campaign_001",
        name="AI Automation Outreach",
        description="Demo campaign for AI automation services",
        target_audience="Engineering leaders at mid-size tech companies",
        value_proposition="Our AI automation platform can reduce your engineering team's manual work by 40% while improving code quality.",
        call_to_action="Would you be open to a 15-minute call to discuss how this could work for your team?",
        created_at=datetime.now(),
        status="draft"
    )
    
    print(f"\n📋 Campaign: {sample_campaign.name}")
    print(f"🎯 Target: {sample_campaign.target_audience}")
    print(f"💡 Value Prop: {sample_campaign.value_proposition}")
    print(f"📞 CTA: {sample_campaign.call_to_action}")
    
    print(f"\n👥 Leads: {len(sample_leads)}")
    for lead in sample_leads:
        print(f"  - {lead['name']} ({lead['title']} at {lead['company']})")
    
    # Simulate user access token (in real app, this comes from OAuth flow)
    print(f"\n🔐 Google OAuth Flow:")
    print("1. User clicks 'Connect Google' button")
    print("2. Redirected to Google OAuth consent screen")
    print("3. User authorizes access to Gmail, Sheets, Drive")
    print("4. System receives access token")
    print("5. Token stored securely for user")
    
    # Demo workflow creation
    print(f"\n🤖 Creating AI SDR Workflow...")
    workflow = AISDRWorkflow()
    
    # Simulate access token (in real app, this comes from database)
    demo_access_token = "demo_token_12345"
    
    try:
        # Create crew with user's access token
        crew_info = workflow.create_crew(
            campaign_id=sample_campaign.campaign_id,
            leads_data=sample_leads,
            campaign=sample_campaign,
            user_access_token=demo_access_token
        )
        
        print(f"✅ Workflow created successfully")
        print(f"   - Campaign ID: {crew_info['campaign_id']}")
        print(f"   - Leads Count: {crew_info['leads_count']}")
        print(f"   - Tools Created: {', '.join(crew_info['tools_created'])}")
        print(f"   - Status: {crew_info['status']}")
        
    except Exception as e:
        print(f"❌ Workflow creation failed: {e}")
        print("This is expected in demo mode without real Google access")
    
    # Demo campaign execution
    print(f"\n🚀 Executing Campaign...")
    print("AI Agents will:")
    print("1. 📊 Prospecting Agent: Validate and process lead data")
    print("2. ✍️  Personalization Agent: Generate personalized messages using OpenAI")
    print("3. 📧 Outreach Agent: Send emails via user's Gmail account")
    print("4. 📈 Coordinator Agent: Create Google Sheets for tracking")
    
    try:
        results = workflow.execute_campaign(
            campaign_id=sample_campaign.campaign_id,
            leads_data=sample_leads,
            campaign=sample_campaign,
            user_access_token=demo_access_token
        )
        
        print(f"\n📊 Campaign Results:")
        print(f"   - Status: {results.get('status', 'Unknown')}")
        print(f"   - Leads Processed: {results.get('leads_processed', 0)}")
        print(f"   - Messages Sent: {results.get('messages_sent', 0)}")
        print(f"   - Execution Time: {results.get('execution_time', 0):.1f} seconds")
        print(f"   - Spreadsheet Created: {results.get('spreadsheet_created', False)}")
        
        if results.get('details'):
            print(f"\n📝 Message Details:")
            for detail in results['details'][:3]:  # Show first 3
                print(f"   - {detail['lead']} ({detail['company']}): {detail['status']}")
        
    except Exception as e:
        print(f"❌ Campaign execution failed: {e}")
        print("This is expected in demo mode without real Google access")
    
    # Demo features
    print(f"\n🎯 Key Features Demonstrated:")
    print("✅ Per-user Google account integration")
    print("✅ AI-powered message personalization")
    print("✅ Gmail API email sending")
    print("✅ Google Sheets campaign tracking")
    print("✅ Google Drive CSV file access")
    print("✅ Secure token management")
    print("✅ Automatic token refresh")
    
    # Next steps
    print(f"\n🚀 Next Steps:")
    print("1. Set up Google OAuth credentials (see GOOGLE_INTEGRATION_GUIDE.md)")
    print("2. Configure environment variables")
    print("3. Start the application: python backend/main.py")
    print("4. Open frontend: cd frontend && npm run dev")
    print("5. Connect your Google account and test!")
    
    print(f"\n📚 Documentation:")
    print("- GOOGLE_INTEGRATION_GUIDE.md - Complete setup guide")
    print("- GOOGLE_OAUTH_SETUP.md - OAuth configuration details")
    print("- README.md - General application documentation")
    
    print(f"\n🎉 Demo completed!")
    print("The AI SDR system is ready for Google integration!")

if __name__ == "__main__":
    demo_google_integration()


