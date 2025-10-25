#!/usr/bin/env python3
"""
SQLite to Supabase Data Migration Script
Migrates existing data from SQLite to Supabase
"""

import sqlite3
import json
import uuid
from datetime import datetime
from services.supabase_service import SupabaseService
import os

def migrate_data():
    print("🔄 Starting SQLite to Supabase migration...")
    
    # Initialize Supabase service
    supabase = SupabaseService()
    
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect('ai_sdr.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        # Migrate campaigns
        print("📊 Migrating campaigns...")
        cursor.execute("SELECT * FROM campaigns")
        campaigns = cursor.fetchall()
        
        for campaign in campaigns:
            try:
                result = supabase.create_campaign(
                    tenant_id="550e8400-e29b-41d4-a716-446655440000",
                    user_id="89985897-54af-436b-8ff5-61c5fa30f434",
                    name=campaign["name"],
                    description=campaign["description"] or ""
                )
                print(f"  ✅ Migrated campaign: {campaign['name']}")
                
            except Exception as e:
                print(f"  ❌ Error migrating campaign {campaign['name']}: {e}")
        
        # Migrate leads (group by campaign)
        print("👥 Migrating leads...")
        cursor.execute("SELECT * FROM leads")
        leads = cursor.fetchall()
        
        # Group leads by campaign_id
        leads_by_campaign = {}
        for lead in leads:
            campaign_id = lead["campaign_id"]
            if campaign_id not in leads_by_campaign:
                leads_by_campaign[campaign_id] = []
            
            lead_data = {
                "name": lead["name"],
                "email": lead["email"] or "",
                "company": lead["company"],
                "title": lead["title"],
                "linkedin_url": lead["linkedin_url"] or "",
                "phone": lead["phone"] or "",
                "status": lead["status"] or "new",
                "notes": f"Industry: {lead['industry'] if lead['industry'] else ''}, Size: {lead['company_size'] if lead['company_size'] else ''}, Location: {lead['location'] if lead['location'] else ''}"
            }
            leads_by_campaign[campaign_id].append(lead_data)
        
        # Save leads for each campaign
        for campaign_id, campaign_leads in leads_by_campaign.items():
            try:
                # Find the corresponding Supabase campaign ID
                # For now, we'll use the first campaign we created
                campaigns = supabase.get_tenant_campaigns("550e8400-e29b-41d4-a716-446655440000")
                if campaigns:
                    supabase_campaign_id = campaigns[0]["id"]
                    result = supabase.save_leads(
                        tenant_id="550e8400-e29b-41d4-a716-446655440000",
                        campaign_id=supabase_campaign_id,
                        leads_data=campaign_leads
                    )
                    print(f"  ✅ Migrated {len(campaign_leads)} leads for campaign {campaign_id}")
                else:
                    print(f"  ⚠️  No campaigns found, skipping leads for campaign {campaign_id}")
                    
            except Exception as e:
                print(f"  ❌ Error migrating leads for campaign {campaign_id}: {e}")
        
        # Migrate user knowledge
        print("🧠 Migrating user knowledge...")
        cursor.execute("SELECT * FROM user_knowledge")
        knowledge_records = cursor.fetchall()
        
        for knowledge in knowledge_records:
            try:
                # Combine all knowledge fields into structured content
                content = {
                    "company_info": knowledge["company_info"] if knowledge["company_info"] else "",
                    "sales_approach": knowledge["sales_approach"] if knowledge["sales_approach"] else "",
                    "products": knowledge["products"] if knowledge["products"] else "",
                    "key_messages": knowledge["key_messages"] if knowledge["key_messages"] else "",
                    "value_propositions": knowledge["value_propositions"] if knowledge["value_propositions"] else "",
                    "target_audience": knowledge["target_audience"] if knowledge["target_audience"] else "",
                    "competitive_advantages": knowledge["competitive_advantages"] if knowledge["competitive_advantages"] else ""
                }
                
                result = supabase.save_user_knowledge(
                    tenant_id="550e8400-e29b-41d4-a716-446655440000",
                    user_id="89985897-54af-436b-8ff5-61c5fa30f434",
                    knowledge_data={
                        "subject": "Company Knowledge Base",
                        "content": content,
                        "source_type": "manual",
                        "confidence_score": 0.9
                    }
                )
                print(f"  ✅ Migrated knowledge: Company Knowledge Base")
                
            except Exception as e:
                print(f"  ❌ Error migrating knowledge: {e}")
        
        # Migrate Google accounts
        print("🔗 Migrating Google accounts...")
        cursor.execute("SELECT * FROM user_google_accounts")
        google_accounts = cursor.fetchall()
        
        for account in google_accounts:
            try:
                # Note: This would need to be implemented in SupabaseService
                print(f"  ⚠️  Google account migration not implemented: {account['email']}")
                
            except Exception as e:
                print(f"  ❌ Error migrating Google account: {e}")
        
        print("\n✅ Migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data()
