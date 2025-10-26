"""
Supabase Multi-Tenant Service
Handles all database operations with tenant isolation
"""

import os
import logging
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized")
    
    # ==============================================
    # TENANT MANAGEMENT
    # ==============================================
    
    def create_tenant(self, name: str, slug: str, plan: str = "free") -> Dict[str, Any]:
        """Create a new tenant"""
        try:
            tenant_data = {
                "name": name,
                "slug": slug,
                "plan": plan,
                "status": "active"
            }
            
            result = self.client.table("tenants").insert(tenant_data).execute()
            tenant = result.data[0] if result.data else None
            
            if tenant:
                logger.info(f"Created tenant: {tenant['id']}")
                return tenant
            else:
                raise Exception("Failed to create tenant")
                
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            raise
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        try:
            result = self.client.table("tenants").select("*").eq("id", tenant_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting tenant: {e}")
            return None
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get tenant by slug"""
        try:
            result = self.client.table("tenants").select("*").eq("slug", slug).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting tenant by slug: {e}")
            return None
    
    # ==============================================
    # USER MANAGEMENT
    # ==============================================
    
    def create_user(self, tenant_id: str, email: str, name: str, role: str = "user") -> Dict[str, Any]:
        """Create a new user"""
        try:
            user_data = {
                "tenant_id": tenant_id,
                "email": email,
                "name": name,
                "role": role
            }
            
            result = self.client.table("users").insert(user_data).execute()
            user = result.data[0] if result.data else None
            
            if user:
                logger.info(f"Created user: {user['id']}")
                return user
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_tenant_users(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all users for a tenant"""
        try:
            result = self.client.table("users").select("*").eq("tenant_id", tenant_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting tenant users: {e}")
            return []
    
    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            result = self.client.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating user last login: {e}")
            return False
    
    # ==============================================
    # KNOWLEDGE MANAGEMENT
    # ==============================================
    
    def save_user_knowledge(self, tenant_id: str, user_id: str, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update user knowledge"""
        try:
            # Convert the knowledge data to match our table structure
            import json
            
            # Extract meaningful subject from knowledge data
            subject = "Company Knowledge"  # Default
            if isinstance(knowledge_data, dict):
                if 'company_info' in knowledge_data and knowledge_data['company_info']:
                    company_name = knowledge_data['company_info'].get('company_name', '')
                    if company_name and company_name != 'Not specified':
                        subject = f"{company_name} Knowledge"
                    elif knowledge_data.get('document_type'):
                        subject = f"{knowledge_data['document_type'].replace('_', ' ').title()} Knowledge"
                elif knowledge_data.get('document_type'):
                    subject = f"{knowledge_data['document_type'].replace('_', ' ').title()} Knowledge"
            
            # Determine confidence based on content quality
            confidence_score = 0.8  # Default
            if isinstance(knowledge_data, dict):
                # Higher confidence if we have more structured data
                structured_fields = ['company_info', 'products', 'value_propositions', 'sales_approach']
                filled_fields = sum(1 for field in structured_fields if knowledge_data.get(field))
                if filled_fields >= 3:
                    confidence_score = 0.9
                elif filled_fields >= 2:
                    confidence_score = 0.8
                else:
                    confidence_score = 0.7
            
            # Generate tags based on content
            tags = ["company", "sales", "products"]  # Default
            if isinstance(knowledge_data, dict):
                content_tags = []
                if knowledge_data.get('company_info'):
                    content_tags.append("company")
                if knowledge_data.get('products'):
                    content_tags.append("products")
                if knowledge_data.get('sales_approach') or knowledge_data.get('sales_methodologies'):
                    content_tags.append("sales")
                if knowledge_data.get('document_type') == 'sales_training':
                    content_tags.append("training")
                if knowledge_data.get('document_type') == 'industry_knowledge':
                    content_tags.append("industry")
                if content_tags:
                    tags = content_tags
            
            # Preserve the original knowledge structure instead of converting to old format
            knowledge_record = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "subject": subject,
                "content": json.dumps(knowledge_data, indent=2),  # Save the full knowledge structure
                "source_type": "extracted",
                "source_id": None,
                "confidence_score": confidence_score,
                "tags": tags
            }
            
            # Insert new knowledge record
            result = self.client.table("user_knowledge").insert(knowledge_record).execute()
            
            knowledge = result.data[0] if result.data else None
            
            if knowledge:
                logger.info(f"Saved knowledge for user: {user_id}")
                return knowledge
            else:
                raise Exception("Failed to save knowledge")
                
        except Exception as e:
            logger.error(f"Error saving knowledge: {e}")
            raise
    
    def get_user_knowledge(self, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user knowledge (most recent article only - for backward compatibility)"""
        try:
            result = self.client.table("user_knowledge").select("*").eq("tenant_id", tenant_id).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user knowledge: {e}")
            return None
    
    def get_all_user_knowledge(self, tenant_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all user knowledge articles"""
        try:
            result = self.client.table("user_knowledge").select("*").eq("tenant_id", tenant_id).eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting all user knowledge: {e}")
            return []
    
    def get_user_knowledge_by_types(self, tenant_id: str, user_id: str, document_types: List[str]) -> List[Dict[str, Any]]:
        """Get user knowledge articles filtered by document types"""
        try:
            query = self.client.table("user_knowledge").select("*").eq("tenant_id", tenant_id).eq("user_id", user_id)
            
            # Filter by document types if provided
            if document_types:
                # Note: This assumes document_type is stored in the content JSON
                # We'll filter after retrieval for now, but could optimize with a proper query later
                result = query.order("created_at", desc=True).execute()
                filtered_data = []
                
                for article in result.data:
                    try:
                        import json
                        content = json.loads(article.get('content', '{}'))
                        doc_type = content.get('document_type', 'company_info')
                        if doc_type in document_types:
                            filtered_data.append(article)
                    except (json.JSONDecodeError, KeyError):
                        # If we can't parse, include it as company_info
                        if 'company_info' in document_types:
                            filtered_data.append(article)
                
                return filtered_data
            else:
                # Return all articles if no types specified
                result = query.order("created_at", desc=True).execute()
                return result.data if result.data else []
                
        except Exception as e:
            logger.error(f"Error getting user knowledge by types: {e}")
            return []
    
    def save_training_document(self, tenant_id: str, user_id: str, filename: str, file_path: str, file_size: int, file_type: str) -> Dict[str, Any]:
        """Save training document record"""
        try:
            document_data = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "status": "uploaded"
            }
            
            result = self.client.table("training_documents").insert(document_data).execute()
            document = result.data[0] if result.data else None
            
            if document:
                logger.info(f"Saved training document: {document['id']}")
                return document
            else:
                raise Exception("Failed to save training document")
                
        except Exception as e:
            logger.error(f"Error saving training document: {e}")
            raise
    
    def get_user_training_documents(self, tenant_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get user's training documents"""
        try:
            result = self.client.table("training_documents").select("*").eq("tenant_id", tenant_id).eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting training documents: {e}")
            return []
    
    # ==============================================
    # CAMPAIGN MANAGEMENT
    # ==============================================
    
    def create_campaign(self, tenant_id: str, user_id: str, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new campaign"""
        try:
            campaign_data = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "status": "draft"
            }
            
            result = self.client.table("campaigns").insert(campaign_data).execute()
            campaign = result.data[0] if result.data else None
            
            if campaign:
                logger.info(f"Created campaign: {campaign['id']}")
                return campaign
            else:
                raise Exception("Failed to create campaign")
                
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
    
    def get_tenant_campaigns(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all campaigns for a tenant"""
        try:
            result = self.client.table("campaigns").select("*").eq("tenant_id", tenant_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting tenant campaigns: {e}")
            return []
    
    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> bool:
        """Update campaign"""
        try:
            result = self.client.table("campaigns").update(updates).eq("id", campaign_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return False
    
    def save_leads(self, tenant_id: str, campaign_id: str, leads_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save leads for a campaign"""
        try:
            leads_records = []
            for lead in leads_data:
                lead_record = {
                    "tenant_id": tenant_id,
                    "campaign_id": campaign_id,
                    "name": lead.get("name"),
                    "email": lead.get("email"),
                    "company": lead.get("company"),
                    "title": lead.get("title"),
                    "linkedin_url": lead.get("linkedin_url"),
                    "phone": lead.get("phone"),
                    "status": "new",
                    "score": lead.get("score", 0),
                    "data": lead.get("data", {})
                }
                leads_records.append(lead_record)
            
            result = self.client.table("leads").insert(leads_records).execute()
            leads = result.data or []
            
            logger.info(f"Saved {len(leads)} leads for campaign: {campaign_id}")
            return leads
            
        except Exception as e:
            logger.error(f"Error saving leads: {e}")
            raise
    
    def get_campaign_leads(self, tenant_id: str, campaign_id: str) -> List[Dict[str, Any]]:
        """Get leads for a campaign"""
        try:
            result = self.client.table("leads").select("*").eq("tenant_id", tenant_id).eq("campaign_id", campaign_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting campaign leads: {e}")
            return []
    
    # ==============================================
    # AGENT RESULTS
    # ==============================================
    
    def save_agent_result(self, tenant_id: str, user_id: str, campaign_id: str, agent_type: str, input_data: Dict[str, Any], output_data: Dict[str, Any], status: str = "completed") -> Dict[str, Any]:
        """Save agent result"""
        try:
            result_data = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "campaign_id": campaign_id,
                "agent_type": agent_type,
                "input_data": input_data,
                "output_data": output_data,
                "status": status
            }
            
            result = self.client.table("agent_results").insert(result_data).execute()
            agent_result = result.data[0] if result.data else None
            
            if agent_result:
                logger.info(f"Saved agent result: {agent_result['id']}")
                return agent_result
            else:
                raise Exception("Failed to save agent result")
                
        except Exception as e:
            logger.error(f"Error saving agent result: {e}")
            raise
    
    def get_agent_results(self, tenant_id: str, campaign_id: str = None, agent_type: str = None) -> List[Dict[str, Any]]:
        """Get agent results"""
        try:
            query = self.client.table("agent_results").select("*").eq("tenant_id", tenant_id)
            
            if campaign_id:
                query = query.eq("campaign_id", campaign_id)
            
            if agent_type:
                query = query.eq("agent_type", agent_type)
            
            result = query.order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting agent results: {e}")
            return []
    
    # ==============================================
    # AUDIT LOGGING
    # ==============================================
    
    def log_audit_event(self, tenant_id: str, user_id: str, action: str, resource_type: str, resource_id: str = None, details: Dict[str, Any] = None) -> bool:
        """Log audit event"""
        try:
            audit_data = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {}
            }
            
            result = self.client.table("audit_logs").insert(audit_data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return False
    
    # ==============================================
    # DASHBOARD STATS
    # ==============================================
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant dashboard statistics"""
        try:
            # Get basic counts
            campaigns_result = self.client.table("campaigns").select("id,status").eq("tenant_id", tenant_id).execute()
            leads_result = self.client.table("leads").select("id").eq("tenant_id", tenant_id).execute()
            users_result = self.client.table("users").select("id").eq("tenant_id", tenant_id).execute()
            
            campaigns = campaigns_result.data or []
            leads = leads_result.data or []
            users = users_result.data or []
            
            active_campaigns = len([c for c in campaigns if c.get("status") == "active"])
            
            stats = {
                "user_count": len(users),
                "campaign_count": len(campaigns),
                "lead_count": len(leads),
                "active_campaigns": active_campaigns
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tenant stats: {e}")
            return {
                "user_count": 0,
                "campaign_count": 0,
                "lead_count": 0,
                "active_campaigns": 0
            }
    
    # ==============================================
    # DOCUMENT MANAGEMENT
    # ==============================================
    
    def get_user_documents(self, tenant_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all uploaded documents for a user.
        
        Args:
            tenant_id: User's tenant ID
            user_id: User's ID
            
        Returns:
            List of document records with id, filename, document_type, file_path, created_at
        """
        try:
            response = (
                self.client
                .from_('uploaded_documents')
                .select('id, filename, document_type, file_path, created_at, extracted_content')
                .eq('tenant_id', tenant_id)
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .execute()
            )
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} documents for user {user_id}")
                return response.data
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving user documents: {e}")
            return []
    
    # ==============================================
    # UTILITY METHODS
    # ==============================================
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            result = self.client.table("tenants").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information"""
        try:
            result = self.client.table(table_name).select("*").limit(1).execute()
            return {
                "table_name": table_name,
                "has_data": len(result.data) > 0,
                "sample_record": result.data[0] if result.data else None
            }
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"table_name": table_name, "error": str(e)}
    
    # ==============================================
    # CAMPAIGN INTELLIGENCE & LEARNING
    # ==============================================
    
    def save_campaign_suggestion(self, tenant_id: str, user_id: str, suggestion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save campaign suggestion to database"""
        try:
            suggestion_record = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "title": suggestion_data.get("title", ""),
                "prompt_text": suggestion_data.get("prompt", ""),
                "reasoning": suggestion_data.get("reasoning", ""),
                "confidence_score": suggestion_data.get("confidence", 0.7),
                "category": suggestion_data.get("category", "general"),
                "source_documents": json.dumps(suggestion_data.get("source_documents", [])),
                "usage_count": 0,
                "success_rate": 0.0
            }
            
            result = self.client.table("campaign_suggestions").insert(suggestion_record).execute()
            suggestion = result.data[0] if result.data else None
            
            if suggestion:
                logger.info(f"Saved campaign suggestion: {suggestion['id']}")
                return suggestion
            else:
                raise Exception("Failed to save campaign suggestion")
                
        except Exception as e:
            logger.error(f"Error saving campaign suggestion: {e}")
            raise
    
    def get_campaign_suggestions(self, tenant_id: str, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get campaign suggestions for user"""
        try:
            result = self.client.table("campaign_suggestions")\
                .select("*")\
                .eq("tenant_id", tenant_id)\
                .eq("user_id", user_id)\
                .order("confidence_score", desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting campaign suggestions: {e}")
            return []
    
    def save_campaign_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save campaign execution record"""
        try:
            result = self.client.table("campaign_executions").insert(execution_data).execute()
            execution = result.data[0] if result.data else None
            
            if execution:
                logger.info(f"Saved campaign execution: {execution['id']}")
                return execution
            else:
                raise Exception("Failed to save campaign execution")
                
        except Exception as e:
            logger.error(f"Error saving campaign execution: {e}")
            raise
    
    def get_campaign_execution_history(self, tenant_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get campaign execution history for user"""
        try:
            result = self.client.table("campaign_executions")\
                .select("*")\
                .eq("tenant_id", tenant_id)\
                .eq("user_id", user_id)\
                .order("executed_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting campaign execution history: {e}")
            return []
    
    def update_suggestion_metrics(self, suggestion_id: str, metrics: Dict[str, Any]) -> bool:
        """Update suggestion performance metrics"""
        try:
            result = self.client.table("campaign_suggestions")\
                .update(metrics)\
                .eq("id", suggestion_id)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating suggestion metrics: {e}")
            return False
    
    def save_prompt_pattern(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save successful prompt pattern"""
        try:
            result = self.client.table("prompt_patterns").insert(pattern_data).execute()
            pattern = result.data[0] if result.data else None
            
            if pattern:
                logger.info(f"Saved prompt pattern: {pattern['id']}")
                return pattern
            else:
                raise Exception("Failed to save prompt pattern")
                
        except Exception as e:
            logger.error(f"Error saving prompt pattern: {e}")
            raise
    
    def get_successful_patterns(self, tenant_id: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get successful prompt patterns"""
        try:
            query = self.client.table("prompt_patterns")\
                .select("*")\
                .eq("tenant_id", tenant_id)\
                .order("success_count", desc=True)
            
            # Apply filters if provided
            if filters:
                if filters.get("pattern_type"):
                    query = query.eq("pattern_type", filters["pattern_type"])
                if filters.get("industry"):
                    query = query.eq("industry", filters["industry"])
                if filters.get("target_role"):
                    query = query.eq("target_role", filters["target_role"])
            
            result = query.limit(20).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting successful patterns: {e}")
            return []

