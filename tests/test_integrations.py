import pytest
from integrations.email_service import EmailService, EmailMessage, EmailResponse
from integrations.linkedin_service import LinkedInService, LinkedInProfile, LinkedInMessage
from integrations.google_sheets_service import GoogleSheetsService
from datetime import datetime

def test_email_message_creation():
    """Test EmailMessage dataclass"""
    message = EmailMessage(
        to="test@example.com",
        subject="Test Subject",
        body="Test Body",
        from_email="sender@example.com"
    )
    
    assert message.to == "test@example.com"
    assert message.subject == "Test Subject"
    assert message.body == "Test Body"
    assert message.from_email == "sender@example.com"

def test_email_response_creation():
    """Test EmailResponse dataclass"""
    response = EmailResponse(
        from_email="test@example.com",
        subject="Re: Test Subject",
        body="Test Response",
        received_at=datetime.now(),
        message_id="msg123"
    )
    
    assert response.from_email == "test@example.com"
    assert response.subject == "Re: Test Subject"
    assert response.message_id == "msg123"

def test_email_service_initialization():
    """Test EmailService initialization"""
    service = EmailService()
    assert service.smtp_server == "smtp.gmail.com"
    assert service.smtp_port == 587
    assert service.imap_server == "imap.gmail.com"
    assert service.imap_port == 993

def test_email_validation():
    """Test email address validation"""
    service = EmailService()
    
    # Valid emails
    assert service.validate_email_address("test@example.com") == True
    assert service.validate_email_address("user.name@domain.co.uk") == True
    
    # Invalid emails
    assert service.validate_email_address("invalid-email") == False
    assert service.validate_email_address("@example.com") == False
    assert service.validate_email_address("test@") == False

def test_email_content_parsing():
    """Test email content parsing"""
    service = EmailService()
    
    # Positive response
    positive_content = "Hi, I'm interested in learning more about your product. Let's schedule a meeting."
    parsed = service.parse_email_content(positive_content)
    assert parsed["is_positive_response"] == True
    assert parsed["is_meeting_request"] == True
    assert parsed["sentiment"] == "positive"
    
    # Negative response
    negative_content = "Thanks for reaching out, but we're not interested at this time."
    parsed = service.parse_email_content(negative_content)
    assert parsed["is_negative_response"] == True
    assert parsed["sentiment"] == "negative"
    
    # Out of office
    ooo_content = "I'm currently out of office and will return next week."
    parsed = service.parse_email_content(ooo_content)
    assert parsed["is_out_of_office"] == True

def test_linkedin_profile_creation():
    """Test LinkedInProfile dataclass"""
    profile = LinkedInProfile(
        id="12345",
        first_name="John",
        last_name="Doe",
        headline="VP of Engineering",
        company="Test Company",
        position="VP of Engineering",
        location="San Francisco, CA",
        profile_url="https://linkedin.com/in/johndoe"
    )
    
    assert profile.id == "12345"
    assert profile.first_name == "John"
    assert profile.last_name == "Doe"
    assert profile.headline == "VP of Engineering"

def test_linkedin_message_creation():
    """Test LinkedInMessage dataclass"""
    message = LinkedInMessage(
        to_profile_id="12345",
        subject="Test Subject",
        body="Test Message Body"
    )
    
    assert message.to_profile_id == "12345"
    assert message.subject == "Test Subject"
    assert message.body == "Test Message Body"

def test_linkedin_service_initialization():
    """Test LinkedInService initialization"""
    service = LinkedInService()
    assert service.base_url == "https://api.linkedin.com/v2"

def test_linkedin_url_extraction():
    """Test LinkedIn URL extraction"""
    service = LinkedInService()
    
    text_with_url = "Check out my LinkedIn: https://www.linkedin.com/in/johndoe"
    url = service.extract_linkedin_url(text_with_url)
    assert url == "https://www.linkedin.com/in/johndoe"
    
    text_without_url = "No LinkedIn URL here"
    url = service.extract_linkedin_url(text_without_url)
    assert url is None

def test_linkedin_url_validation():
    """Test LinkedIn URL validation"""
    service = LinkedInService()
    
    # Valid URLs
    assert service.validate_linkedin_url("https://www.linkedin.com/in/johndoe") == True
    assert service.validate_linkedin_url("https://linkedin.com/in/johndoe") == True
    
    # Invalid URLs
    assert service.validate_linkedin_url("https://facebook.com/johndoe") == False
    assert service.validate_linkedin_url("not-a-url") == False

def test_linkedin_profile_id_extraction():
    """Test profile ID extraction from URL"""
    service = LinkedInService()
    
    profile_id = service.get_profile_id_from_url("https://www.linkedin.com/in/johndoe")
    assert profile_id == "johndoe"
    
    profile_id = service.get_profile_id_from_url("https://linkedin.com/in/jane-smith")
    assert profile_id == "jane-smith"

def test_linkedin_personalized_message():
    """Test personalized message creation"""
    service = LinkedInService()
    
    lead_data = {
        "name": "John Doe",
        "company": "Test Company",
        "title": "VP of Engineering",
        "linkedin_profile_id": "johndoe"
    }
    
    campaign_data = {
        "name": "AI Automation Campaign",
        "value_proposition": "Our AI platform reduces manual work by 40%",
        "call_to_action": "Would you be open to a brief conversation?"
    }
    
    message = service.create_personalized_message(lead_data, campaign_data)
    
    assert message.to_profile_id == "johndoe"
    assert "John Doe" in message.body
    assert "Test Company" in message.body
    assert "VP of Engineering" in message.body

def test_google_sheets_service_initialization():
    """Test GoogleSheetsService initialization"""
    service = GoogleSheetsService()
    assert service.scopes is not None
    assert len(service.scopes) > 0

def test_email_metrics_calculation():
    """Test email metrics calculation"""
    service = EmailService()
    
    sent_messages = [
        {"success": True, "recipient": "test1@example.com"},
        {"success": True, "recipient": "test2@example.com"},
        {"success": False, "recipient": "test3@example.com"}
    ]
    
    responses = [
        EmailResponse(
            from_email="test1@example.com",
            subject="Re: Test",
            body="I'm interested in learning more",
            received_at=datetime.now(),
            message_id="msg1"
        )
    ]
    
    metrics = service.get_email_metrics(sent_messages, responses)
    
    assert metrics["total_sent"] == 3
    assert metrics["successful_sends"] == 2
    assert metrics["delivery_rate"] == (2/3 * 100)
    assert metrics["total_responses"] == 1
    assert metrics["response_rate"] == (1/2 * 100)

def test_linkedin_messaging_metrics():
    """Test LinkedIn messaging metrics"""
    service = LinkedInService()
    
    sent_messages = [
        {"success": True, "recipient": "profile1"},
        {"success": True, "recipient": "profile2"},
        {"success": False, "recipient": "profile3"}
    ]
    
    metrics = service.get_messaging_metrics(sent_messages)
    
    assert metrics["total_sent"] == 3
    assert metrics["successful_sends"] == 2
    assert metrics["delivery_rate"] == (2/3 * 100)
    assert metrics["platform"] == "linkedin"

def test_follow_up_sequence_creation():
    """Test follow-up email sequence creation"""
    service = EmailService()
    
    lead_data = {
        "name": "John Doe",
        "company": "Test Company",
        "title": "VP of Engineering",
        "email": "john@test.com"
    }
    
    campaign_data = {
        "name": "AI Automation Campaign",
        "value_proposition": "Our AI platform reduces manual work by 40%",
        "call_to_action": "Would you be open to a brief conversation?"
    }
    
    messages = service.create_follow_up_sequence(lead_data, campaign_data)
    
    assert len(messages) == 3  # Initial + 2 follow-ups
    assert all(isinstance(msg, EmailMessage) for msg in messages)
    assert all(msg.to == "john@test.com" for msg in messages)
    
    # Check that messages are personalized
    assert "John Doe" in messages[0].body
    assert "Test Company" in messages[0].body
    assert "VP of Engineering" in messages[0].body

if __name__ == "__main__":
    pytest.main([__file__])
