#!/usr/bin/env python3
"""
Quick script to extract knowledge from existing uploaded documents.
Run this to process documents that were uploaded before knowledge extraction was added.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.knowledge_extraction_agent import KnowledgeExtractionAgent
from services.supabase_service import SupabaseService
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def extract_knowledge_for_user(user_id: str, tenant_id: str):
    """Extract knowledge from all uploaded documents for a user"""
    
    supabase = SupabaseService()
    agent = KnowledgeExtractionAgent()
    
    logger.info(f"🔍 Finding documents for user {user_id}...")
    
    # Get all documents for this user
    response = supabase.client.from_('training_documents').select('*').eq('tenant_id', tenant_id).eq('user_id', user_id).execute()
    
    documents = response.data or []
    logger.info(f"📄 Found {len(documents)} documents")
    
    if not documents:
        logger.warning(f"⚠️  No documents found for user {user_id}")
        return
    
    for doc in documents:
        logger.info(f"\n📝 Processing: {doc['filename']} (Type: {doc['document_type']})")
        
        file_path = doc['file_path']
        
        # Check if file exists
        if not Path(file_path).exists():
            logger.error(f"❌ File not found: {file_path}")
            continue
        
        try:
            # Extract knowledge
            logger.info(f"🤖 Extracting knowledge with Claude...")
            result = agent.extract_knowledge_from_files(
                [file_path], 
                document_type=doc['document_type']
            )
            
            if result.get('success'):
                extracted_knowledge = result.get('extracted_knowledge', {})
                logger.info(f"✅ Knowledge extracted successfully!")
                logger.info(f"   - Company: {extracted_knowledge.get('company_info', {}).get('company_name', 'N/A')}")
                logger.info(f"   - Products: {len(extracted_knowledge.get('products', []))}")
                logger.info(f"   - Value Props: {len(extracted_knowledge.get('value_propositions', []))}")
                
                # Save to user_knowledge table (correct schema)
                import json
                knowledge_record = {
                    'tenant_id': tenant_id,
                    'user_id': user_id,
                    'subject': doc['filename'],
                    'content': json.dumps(extracted_knowledge),  # Save full structure as JSON
                    'source_type': 'extracted',
                    'source_id': doc['id'],
                    'confidence_score': 0.8,
                    'tags': [doc['document_type']]
                }
                
                supabase.client.from_('user_knowledge').insert(knowledge_record).execute()
                logger.info(f"💾 Saved to user_knowledge table")
                
            else:
                logger.error(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"❌ Error processing {doc['filename']}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"\n✅ Knowledge extraction complete for user {user_id}!")

if __name__ == "__main__":
    # Demo user credentials
    USER_ID = "89985897-54af-436b-8ff5-61c5fa30f434"
    TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
    
    logger.info("🚀 Starting knowledge extraction for existing documents...")
    logger.info(f"👤 User ID: {USER_ID}")
    logger.info(f"🏢 Tenant ID: {TENANT_ID}\n")
    
    asyncio.run(extract_knowledge_for_user(USER_ID, TENANT_ID))

