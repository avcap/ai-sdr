import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import re
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    from_email: str
    sent_at: Optional[datetime] = None
    message_id: Optional[str] = None

@dataclass
class EmailResponse:
    from_email: str
    subject: str
    body: str
    received_at: datetime
    message_id: str
    in_reply_to: Optional[str] = None

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("Email credentials not configured")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return all([self.smtp_username, self.smtp_password])
    
    def send_email(self, to_email: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """Send an email message"""
        try:
            # Use configured email as sender if not provided
            if not from_email:
                from_email = self.smtp_username
                
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            
            return {
                "success": True,
                "message_id": msg['Message-ID'],
                "sent_at": datetime.now().isoformat(),
                "recipient": to_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }
    
    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Send multiple emails"""
        results = []
        
        for message in messages:
            result = self.send_email(message)
            results.append(result)
            
            # Add delay between emails to avoid rate limiting
            import time
            time.sleep(1)
        
        return results
    
    def check_for_responses(self, sent_message_ids: List[str]) -> List[EmailResponse]:
        """Check for email responses"""
        responses = []
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.smtp_username, self.smtp_password)
            mail.select('inbox')
            
            # Search for emails
            for message_id in sent_message_ids:
                # Search for replies
                search_criteria = f'HEADER "In-Reply-To" "{message_id}"'
                status, messages = mail.search(None, search_criteria)
                
                if status == 'OK':
                    for msg_id in messages[0].split():
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')
                        
                        if status == 'OK':
                            email_body = msg_data[0][1]
                            email_message = email.message_from_bytes(email_body)
                            
                            response = EmailResponse(
                                from_email=email_message['From'],
                                subject=email_message['Subject'],
                                body=self._extract_email_body(email_message),
                                received_at=datetime.now(),
                                message_id=email_message['Message-ID'],
                                in_reply_to=email_message['In-Reply-To']
                            )
                            responses.append(response)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error checking for responses: {e}")
        
        return responses
    
    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        
        return body
    
    def parse_email_content(self, content: str) -> Dict[str, Any]:
        """Parse email content to extract meeting requests, responses, etc."""
        parsed = {
            "is_meeting_request": False,
            "is_positive_response": False,
            "is_negative_response": False,
            "is_out_of_office": False,
            "meeting_times": [],
            "sentiment": "neutral"
        }
        
        content_lower = content.lower()
        
        # Check for meeting requests
        meeting_keywords = [
            "schedule a meeting", "book a call", "set up a call",
            "meeting", "call", "demo", "presentation"
        ]
        
        if any(keyword in content_lower for keyword in meeting_keywords):
            parsed["is_meeting_request"] = True
        
        # Check for positive responses
        positive_keywords = [
            "interested", "yes", "sounds good", "let's do it",
            "schedule", "book", "meeting", "call"
        ]
        
        if any(keyword in content_lower for keyword in positive_keywords):
            parsed["is_positive_response"] = True
        
        # Check for negative responses
        negative_keywords = [
            "not interested", "no thanks", "not a good fit",
            "not right now", "busy", "decline"
        ]
        
        if any(keyword in content_lower for keyword in negative_keywords):
            parsed["is_negative_response"] = True
        
        # Check for out of office
        ooo_keywords = [
            "out of office", "vacation", "away", "unavailable"
        ]
        
        if any(keyword in content_lower for keyword in ooo_keywords):
            parsed["is_out_of_office"] = True
        
        # Extract meeting times
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(?:am|pm)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, content_lower)
            parsed["meeting_times"].extend(matches)
        
        # Determine sentiment
        if parsed["is_positive_response"]:
            parsed["sentiment"] = "positive"
        elif parsed["is_negative_response"]:
            parsed["sentiment"] = "negative"
        
        return parsed
    
    def create_follow_up_sequence(self, lead_data: Dict[str, Any], campaign_data: Dict[str, Any]) -> List[EmailMessage]:
        """Create a follow-up email sequence"""
        messages = []
        
        # Initial message
        initial_message = EmailMessage(
            to=lead_data["email"],
            subject=f"Quick question about {lead_data['company']}",
            body=f"""
Hi {lead_data['name']},

I hope this email finds you well. I noticed you're {lead_data['title']} at {lead_data['company']}.

{campaign_data['value_proposition']}

Would you be open to a brief 15-minute conversation this week to discuss how this might apply to {lead_data['company']}?

{campaign_data['call_to_action']}

Best regards,
[Your Name]
            """.strip(),
            from_email=self.smtp_username
        )
        messages.append(initial_message)
        
        # Follow-up 1 (3 days later)
        follow_up_1 = EmailMessage(
            to=lead_data["email"],
            subject=f"Following up - {lead_data['company']}",
            body=f"""
Hi {lead_data['name']},

I wanted to follow up on my previous email about {campaign_data['name']}.

I understand you're busy, but I believe this could be valuable for {lead_data['company']}.

Would you have 10 minutes for a quick call this week?

Best regards,
[Your Name]
            """.strip(),
            from_email=self.smtp_username
        )
        messages.append(follow_up_1)
        
        # Follow-up 2 (1 week later)
        follow_up_2 = EmailMessage(
            to=lead_data["email"],
            subject=f"Last attempt - {lead_data['company']}",
            body=f"""
Hi {lead_data['name']},

This is my final follow-up regarding {campaign_data['name']}.

If you're not interested, no worries at all. If you'd like to learn more, I'm here to help.

Best regards,
[Your Name]
            """.strip(),
            from_email=self.smtp_username
        )
        messages.append(follow_up_2)
        
        return messages
    
    def validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_email_metrics(self, sent_messages: List[Dict[str, Any]], responses: List[EmailResponse]) -> Dict[str, Any]:
        """Calculate email campaign metrics"""
        total_sent = len(sent_messages)
        successful_sends = len([msg for msg in sent_messages if msg.get("success", False)])
        total_responses = len(responses)
        
        # Categorize responses
        positive_responses = len([r for r in responses if self.parse_email_content(r.body)["is_positive_response"]])
        negative_responses = len([r for r in responses if self.parse_email_content(r.body)["is_negative_response"]])
        meeting_requests = len([r for r in responses if self.parse_email_content(r.body)["is_meeting_request"]])
        
        return {
            "total_sent": total_sent,
            "successful_sends": successful_sends,
            "delivery_rate": (successful_sends / total_sent * 100) if total_sent > 0 else 0,
            "total_responses": total_responses,
            "response_rate": (total_responses / successful_sends * 100) if successful_sends > 0 else 0,
            "positive_responses": positive_responses,
            "negative_responses": negative_responses,
            "meeting_requests": meeting_requests,
            "positive_response_rate": (positive_responses / total_responses * 100) if total_responses > 0 else 0,
            "meeting_rate": (meeting_requests / total_responses * 100) if total_responses > 0 else 0
        }
