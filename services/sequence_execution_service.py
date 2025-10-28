"""
Sequence Execution Service
Handles timestamp-based execution of email sequences
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from services.supabase_service import supabase_service
from integrations.google_oauth_service import GoogleOAuthService
from integrations.email_service import EmailService

logger = logging.getLogger(__name__)

class SequenceExecutionService:
    """Service for executing sequence steps based on timestamps"""
    
    def __init__(self):
        self.google_service = GoogleOAuthService()
        self.email_service = EmailService()
    
    async def process_all_sequences(self):
        """Main entry point: Process all sequences ready for execution"""
        try:
            logger.info("🔄 Processing sequences...")
            
            # Step 1: Activate scheduled sequences whose time has come
            activated_count = await self.activate_scheduled_sequences()
            
            # Step 2: Execute active leads ready for next action
            executed_count = await self.execute_ready_steps()
            
            logger.info(f"✅ Processed {activated_count} scheduled → active, {executed_count} steps executed")
            
            return {
                "activated": activated_count,
                "executed": executed_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing sequences: {e}")
            return {
                "activated": 0,
                "executed": 0,
                "error": str(e)
            }
    
    async def activate_scheduled_sequences(self) -> int:
        """Convert scheduled enrollments to active if time has arrived"""
        try:
            # Find enrollments that are scheduled and ready to start
            result = supabase_service.client.table('sequence_enrollments').select('*').eq('status', 'scheduled').lte('next_action_at', datetime.now(timezone.utc).isoformat()).execute()
            
            count = 0
            for enrollment in result.data:
                try:
                    # Update to active and set started_at
                    supabase_service.client.table('sequence_enrollments').update({
                        'status': 'active',
                        'started_at': datetime.now(timezone.utc).isoformat()
                    }).eq('id', enrollment['id']).execute()
                    
                    count += 1
                    logger.info(f"✅ Activated enrollment {enrollment['id']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error activating enrollment {enrollment['id']}: {e}")
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error activating scheduled sequences: {e}")
            return 0
    
    async def execute_ready_steps(self) -> int:
        """Execute all steps that are ready based on next_action_at timestamp"""
        try:
            # Find active enrollments ready for next action
            result = supabase_service.client.table('sequence_enrollments').select('*, leads(*), sequences(*)').eq('status', 'active').lte('next_action_at', datetime.now(timezone.utc).isoformat()).execute()
            
            count = 0
            for enrollment in result.data:
                try:
                    # Get current step details
                    step_result = supabase_service.client.table('sequence_steps').select('*').eq('sequence_id', enrollment['sequence_id']).eq('step_order', enrollment['current_step']).execute()
                    
                    if not step_result.data:
                        logger.warning(f"⚠️ No step found for enrollment {enrollment['id']} at step {enrollment['current_step']}")
                        # Mark as completed - no more steps
                        await self._complete_enrollment(enrollment['id'], 'completed')
                        continue
                    
                    step = step_result.data[0]
                    
                    # Execute the step based on type
                    await self.execute_step(enrollment, step)
                    count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error executing step for enrollment {enrollment['id']}: {e}")
                    # Log the error but continue processing other enrollments
                    await self._log_step_execution(
                        enrollment['id'],
                        step.get('id') if 'step' in locals() else None,
                        'failed',
                        error_message=str(e)
                    )
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error executing ready steps: {e}")
            return 0
    
    async def execute_step(self, enrollment: Dict, step: Dict):
        """Execute a single step based on its type"""
        step_type = step['step_type']
        
        logger.info(f"🔄 Executing {step_type} step for enrollment {enrollment['id']}")
        
        if step_type == 'email':
            await self._execute_email_step(enrollment, step)
        elif step_type == 'delay':
            await self._execute_delay_step(enrollment, step)
        elif step_type == 'condition':
            await self._execute_condition_step(enrollment, step)
        elif step_type == 'action':
            await self._execute_action_step(enrollment, step)
        else:
            logger.warning(f"⚠️ Unknown step type: {step_type}")
            # Move to next step
            await self._move_to_next_step(enrollment['id'], enrollment['current_step'])
    
    async def _execute_email_step(self, enrollment: Dict, step: Dict):
        """Execute an email step - send email via Gmail"""
        try:
            lead = enrollment['leads']
            sequence = enrollment['sequences']
            
            # Personalize email content
            subject = self._personalize_content(step['subject_line'], lead, sequence)
            body = self._personalize_content(step['body_text'], lead, sequence)
            
            # Send email via Gmail API
            success = await self._send_email(
                tenant_id=enrollment['tenant_id'],
                to_email=lead['email'],
                to_name=lead['name'],
                subject=subject,
                body=body
            )
            
            # Log execution
            await self._log_step_execution(
                enrollment['id'],
                step['id'],
                'sent' if success else 'failed',
                email_sent=success
            )
            
            # Move to next step immediately
            await self._move_to_next_step(enrollment['id'], enrollment['current_step'], immediate=True)
            
            logger.info(f"✅ Email sent to {lead['email']}")
            
        except Exception as e:
            logger.error(f"❌ Error executing email step: {e}")
            await self._log_step_execution(
                enrollment['id'],
                step['id'],
                'failed',
                error_message=str(e)
            )
            raise
    
    async def _execute_delay_step(self, enrollment: Dict, step: Dict):
        """Execute a delay step - calculate next_action_at timestamp"""
        try:
            # Calculate delay duration
            delay_seconds = (step.get('delay_days', 0) * 86400) + (step.get('delay_hours', 0) * 3600)
            next_action_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            
            # Move to next step with calculated timestamp
            await self._move_to_next_step(
                enrollment['id'],
                enrollment['current_step'],
                next_action_at=next_action_at
            )
            
            logger.info(f"✅ Delay set: next action at {next_action_at}")
            
        except Exception as e:
            logger.error(f"❌ Error executing delay step: {e}")
            raise
    
    async def _execute_condition_step(self, enrollment: Dict, step: Dict):
        """Execute a condition step - check reply status"""
        try:
            condition_type = step.get('condition_type')
            lead = enrollment['leads']
            
            if condition_type == 'if_not_replied':
                # Check if lead has replied
                has_replied = await self._check_if_replied(lead['email'], enrollment['tenant_id'])
                
                if has_replied:
                    # Exit sequence - lead replied
                    await self._complete_enrollment(enrollment['id'], 'replied')
                    logger.info(f"✅ Lead {lead['email']} replied - exiting sequence")
                else:
                    # Continue to next step
                    await self._move_to_next_step(enrollment['id'], enrollment['current_step'], immediate=True)
                    logger.info(f"✅ Lead {lead['email']} has not replied - continuing")
            
            elif condition_type == 'if_opened':
                # Check if email was opened (would need email tracking)
                # For now, just continue
                await self._move_to_next_step(enrollment['id'], enrollment['current_step'], immediate=True)
            
            else:
                logger.warning(f"⚠️ Unknown condition type: {condition_type}")
                await self._move_to_next_step(enrollment['id'], enrollment['current_step'], immediate=True)
            
        except Exception as e:
            logger.error(f"❌ Error executing condition step: {e}")
            raise
    
    async def _execute_action_step(self, enrollment: Dict, step: Dict):
        """Execute an action step (future: LinkedIn, SMS, etc.)"""
        try:
            action_type = step.get('action_type')
            logger.info(f"⚠️ Action step '{action_type}' not yet implemented")
            
            # For now, just move to next step
            await self._move_to_next_step(enrollment['id'], enrollment['current_step'], immediate=True)
            
        except Exception as e:
            logger.error(f"❌ Error executing action step: {e}")
            raise
    
    async def _move_to_next_step(
        self,
        enrollment_id: str,
        current_step: int,
        immediate: bool = False,
        next_action_at: Optional[datetime] = None
    ):
        """Move enrollment to next step"""
        try:
            update_data = {
                'current_step': current_step + 1
            }
            
            if next_action_at:
                # Delay step - use calculated timestamp
                update_data['next_action_at'] = next_action_at.isoformat()
            elif immediate:
                # Execute next step immediately
                update_data['next_action_at'] = datetime.now(timezone.utc).isoformat()
            
            supabase_service.client.table('sequence_enrollments').update(update_data).eq('id', enrollment_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Error moving to next step: {e}")
            raise
    
    async def _complete_enrollment(self, enrollment_id: str, exit_reason: str):
        """Mark enrollment as completed"""
        try:
            supabase_service.client.table('sequence_enrollments').update({
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'exit_reason': exit_reason
            }).eq('id', enrollment_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Error completing enrollment: {e}")
            raise
    
    async def _send_email(
        self,
        tenant_id: str,
        to_email: str,
        to_name: str,
        subject: str,
        body: str
    ) -> bool:
        """Send email via Gmail API using user's OAuth token"""
        try:
            # Get user's Gmail credentials from google_auth table
            google_auth = supabase_service.client.table('google_auth').select('*').eq('tenant_id', tenant_id).execute()
            
            if not google_auth.data:
                logger.warning(f"⚠️ No Gmail credentials found for tenant {tenant_id}")
                return False
            
            auth_data = google_auth.data[0]
            access_token = auth_data.get('access_token')
            refresh_token = auth_data.get('refresh_token')
            
            if not access_token:
                logger.warning(f"⚠️ No access token found for tenant {tenant_id}")
                return False
            
            # Send email via Gmail API
            result = self.google_service.send_email_via_gmail(
                access_token=access_token,
                refresh_token=refresh_token,
                to_email=to_email,
                subject=subject,
                body=body
            )
            
            if result.get('success'):
                logger.info(f"✅ Email sent via Gmail API to {to_email}")
                return True
            else:
                logger.error(f"❌ Failed to send email: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    async def _check_if_replied(self, email: str, tenant_id: str) -> bool:
        """Check if a lead has replied to any sequence emails"""
        try:
            # This would check Gmail API for replies
            # For now, return False (not implemented yet)
            # TODO: Implement reply detection via Gmail API
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking replies: {e}")
            return False
    
    async def _log_step_execution(
        self,
        enrollment_id: str,
        step_id: Optional[str],
        status: str,
        email_sent: bool = False,
        error_message: Optional[str] = None
    ):
        """Log step execution for tracking"""
        try:
            if not step_id:
                return
            
            # Get tenant_id from enrollment
            enrollment = supabase_service.client.table('sequence_enrollments').select('tenant_id').eq('id', enrollment_id).execute()
            
            if not enrollment.data:
                return
            
            supabase_service.client.table('sequence_step_executions').insert({
                'tenant_id': enrollment.data[0]['tenant_id'],
                'enrollment_id': enrollment_id,
                'step_id': step_id,
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'status': status,
                'email_sent': email_sent,
                'error_message': error_message
            }).execute()
            
        except Exception as e:
            logger.error(f"❌ Error logging step execution: {e}")
    
    def _personalize_content(self, content: str, lead: Dict, sequence: Dict) -> str:
        """Replace variables in email content with lead data"""
        if not content:
            return ""
        
        # Replace common variables
        personalized = content
        personalized = personalized.replace('{{name}}', lead.get('name', ''))
        personalized = personalized.replace('{{company}}', lead.get('company', ''))
        personalized = personalized.replace('{{title}}', lead.get('title', ''))
        personalized = personalized.replace('{{industry}}', lead.get('industry', ''))
        personalized = personalized.replace('{{location}}', lead.get('location', ''))
        
        # Add sender name (would come from user profile)
        personalized = personalized.replace('{{sender_name}}', 'Your Sales Team')
        
        return personalized


# Global instance
sequence_execution_service = SequenceExecutionService()

