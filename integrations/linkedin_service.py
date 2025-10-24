import requests
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LinkedInProfile:
    id: str
    first_name: str
    last_name: str
    headline: str
    company: str
    position: str
    location: str
    profile_url: str
    email: Optional[str] = None

@dataclass
class LinkedInMessage:
    to_profile_id: str
    subject: str
    body: str
    sent_at: Optional[datetime] = None
    message_id: Optional[str] = None

@dataclass
class LinkedInConnection:
    profile_id: str
    status: str  # pending, accepted, declined
    sent_at: datetime
    message: Optional[str] = None

class LinkedInService:
    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:3000/auth/linkedin/callback")
        self.access_token = None
        self.base_url = "https://api.linkedin.com/v2"
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("LinkedIn API credentials not configured")
    
    def get_auth_url(self) -> str:
        """Generate LinkedIn OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": "random_state_string",
            "scope": "r_liteprofile r_emailaddress w_messaging"
        }
        
        auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + "&".join([f"{k}={v}" for k, v in params.items()])
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            return token_data
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise e
    
    def get_profile(self, profile_id: str = "me") -> LinkedInProfile:
        """Get LinkedIn profile information"""
        if not self.access_token:
            raise ValueError("Access token not set")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get basic profile info
        profile_url = f"{self.base_url}/people/{profile_id}"
        params = {
            "projection": "(id,firstName,lastName,headline,location,profilePicture(displayImage~:playableStreams))"
        }
        
        try:
            response = requests.get(profile_url, headers=headers, params=params)
            response.raise_for_status()
            
            profile_data = response.json()
            
            # Get email if available
            email_url = f"{self.base_url}/emailAddress?q=members&projection=(elements*(handle~))"
            email_response = requests.get(email_url, headers=headers)
            
            email = None
            if email_response.status_code == 200:
                email_data = email_response.json()
                if email_data.get("elements"):
                    email = email_data["elements"][0]["handle~"]["emailAddress"]
            
            return LinkedInProfile(
                id=profile_data["id"],
                first_name=profile_data["firstName"]["localized"]["en_US"],
                last_name=profile_data["lastName"]["localized"]["en_US"],
                headline=profile_data.get("headline", {}).get("localized", {}).get("en_US", ""),
                company="",  # Would need additional API call
                position="",  # Would need additional API call
                location=profile_data.get("location", {}).get("name", ""),
                profile_url=f"https://www.linkedin.com/in/{profile_data['id']}",
                email=email
            )
            
        except Exception as e:
            logger.error(f"Error getting LinkedIn profile: {e}")
            raise e
    
    def search_profiles(self, keywords: str, limit: int = 10) -> List[LinkedInProfile]:
        """Search for LinkedIn profiles (Note: Limited by LinkedIn API)"""
        if not self.access_token:
            raise ValueError("Access token not set")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # LinkedIn People Search API (requires special access)
        search_url = f"{self.base_url}/peopleSearch"
        params = {
            "keywords": keywords,
            "count": limit
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            search_data = response.json()
            profiles = []
            
            for person in search_data.get("elements", []):
                profile = LinkedInProfile(
                    id=person["id"],
                    first_name=person.get("firstName", ""),
                    last_name=person.get("lastName", ""),
                    headline=person.get("headline", ""),
                    company=person.get("company", ""),
                    position=person.get("position", ""),
                    location=person.get("location", ""),
                    profile_url=f"https://www.linkedin.com/in/{person['id']}"
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn profiles: {e}")
            # Return empty list if search fails
            return []
    
    def send_message(self, message: LinkedInMessage) -> Dict[str, Any]:
        """Send a LinkedIn message"""
        if not self.access_token:
            raise ValueError("Access token not set")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # LinkedIn Messaging API
        message_url = f"{self.base_url}/messaging/conversations"
        
        payload = {
            "recipients": [message.to_profile_id],
            "subject": message.subject,
            "body": message.body
        }
        
        try:
            response = requests.post(message_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"LinkedIn message sent successfully to {message.to_profile_id}")
            
            return {
                "success": True,
                "message_id": result.get("id"),
                "sent_at": datetime.now().isoformat(),
                "recipient": message.to_profile_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send LinkedIn message: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": message.to_profile_id
            }
    
    def send_connection_request(self, connection: LinkedInConnection) -> Dict[str, Any]:
        """Send a LinkedIn connection request"""
        if not self.access_token:
            raise ValueError("Access token not set")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # LinkedIn Connection API
        connection_url = f"{self.base_url}/people/{connection.profile_id}/relation-to-viewer"
        
        payload = {
            "person": connection.profile_id,
            "message": connection.message or "Hi, I'd like to connect with you."
        }
        
        try:
            response = requests.post(connection_url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"LinkedIn connection request sent to {connection.profile_id}")
            
            return {
                "success": True,
                "sent_at": datetime.now().isoformat(),
                "recipient": connection.profile_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send LinkedIn connection request: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": connection.profile_id
            }
    
    def get_connection_status(self, profile_id: str) -> Dict[str, Any]:
        """Get connection status with a profile"""
        if not self.access_token:
            raise ValueError("Access token not set")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        connection_url = f"{self.base_url}/people/{profile_id}/relation-to-viewer"
        
        try:
            response = requests.get(connection_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def extract_linkedin_url(self, text: str) -> Optional[str]:
        """Extract LinkedIn profile URL from text"""
        import re
        
        patterns = [
            r'https://www\.linkedin\.com/in/[a-zA-Z0-9-]+/?',
            r'https://linkedin\.com/in/[a-zA-Z0-9-]+/?',
            r'linkedin\.com/in/[a-zA-Z0-9-]+/?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return None
    
    def get_profile_id_from_url(self, profile_url: str) -> Optional[str]:
        """Extract profile ID from LinkedIn URL"""
        import re
        
        pattern = r'linkedin\.com/in/([a-zA-Z0-9-]+)'
        match = re.search(pattern, profile_url)
        
        if match:
            return match.group(1)
        
        return None
    
    def create_personalized_message(self, lead_data: Dict[str, Any], campaign_data: Dict[str, Any]) -> LinkedInMessage:
        """Create a personalized LinkedIn message"""
        message_body = f"""
Hi {lead_data['name']},

I noticed you're {lead_data['title']} at {lead_data['company']}. 

{campaign_data['value_proposition']}

Would you be open to a brief conversation about how this might apply to {lead_data['company']}?

{campaign_data['call_to_action']}

Best regards,
[Your Name]
        """.strip()
        
        return LinkedInMessage(
            to_profile_id=lead_data.get("linkedin_profile_id", ""),
            subject=f"Quick question about {lead_data['company']}",
            body=message_body
        )
    
    def get_messaging_metrics(self, sent_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate LinkedIn messaging metrics"""
        total_sent = len(sent_messages)
        successful_sends = len([msg for msg in sent_messages if msg.get("success", False)])
        
        return {
            "total_sent": total_sent,
            "successful_sends": successful_sends,
            "delivery_rate": (successful_sends / total_sent * 100) if total_sent > 0 else 0,
            "platform": "linkedin"
        }
    
    def validate_linkedin_url(self, url: str) -> bool:
        """Validate LinkedIn profile URL format"""
        import re
        
        pattern = r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?$'
        return re.match(pattern, url) is not None
